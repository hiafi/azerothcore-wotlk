/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

// Custom: free gathering and professions at the cap (crafting rework C2,
// .agents/plans/crafting-rework/crafting-rework.PLAN.md).
//
// Every character (bots too) knows Herbalism, Mining and Skinning, and every profession it knows (the eight crafting
// ones, the three gathering ones, Cooking, Fishing and First Aid) sits at value = max = Custom.Professions.SkillCap.
// There is no skill leveling. The cap is raised by hand on a phase change (300 at level 60, later 375 / 450).
//
// - On login: learn the missing gathering skills, raise every known profession to the cap, remove the stripped
//   gathering perks (Toughness, Master of Anatomy, Lifeblood) if known.
// - On learning a profession rank (trainer, book, GM): raise that profession to the cap on the player's next update.
// - Trainers show the rank spells above the cap as unavailable, so a level-60 player cannot buy Master, and no other
//   route (recipe book, quest, GM command) can teach a rank above the cap either.
//
// Raising walks the profession's rank chain (spell_ranks: Apprentice 75, Journeyman 150, Expert 225, Artisan 300,
// Master 375, Grand Master 450): each rank whose max is <= the cap is learned in order, which is what a trainer
// purchase does (Player::_addSpell sets the step and max from the rank's SpellLearnSkillNode, and an older rank of a
// non-stackable chain stays known but inactive, so the trainer lists it as known). Then SetSkill puts value and max
// at the cap with the step of the last rank learned. Pure values only: racial bonuses (Tauren Herbalism, Gnome
// Engineering, ...) stay on top as before. A skill already at or above the cap is never lowered.
//
// Data half (apps/dbc-tools/source/world/crafting.py): the three gathering skills are SkillLine category 9
// (secondary), so they do not use a MaxPrimaryTradeSkill point and cannot be unlearned; the perks' SkillLineAbility
// rows are AcquireMethod 0, so Player::learnSkillRewardedSpells no longer teaches them.
//
// Professions page feed (C2-UI, client/ui-overrides ProfessionsFrame.lua): the client cannot count known recipes
// without opening each trade skill window, so the server sends them as an addon message to the player himself
// (SMSG_MESSAGECHAT, CHAT_MSG_WHISPER + LANG_ADDON, read by the client as CHAT_MSG_ADDON):
//
//     prefix "CPROF", body "1;<skill>,<recipes>,<rank>;<skill>,<recipes>,<rank>;..."
//
// "1" is the format version. One entry per known profession of the 14 above. <rank> is the gathering rank (C3,
// custom_gathering_ranks.cpp): the best rank across the skill's materials for Herbalism, Mining and Skinning, empty
// for the others (the client then shows no rank line). A recipe is a known spell whose SkillLineAbility skill is
// that profession, minus passives and the profession's tools: the rank spells (SPELL_EFFECT_SKILL), the trade
// window openers (SPELL_EFFECT_TRADE_SKILL: the main spell, Smelting), Disenchant / Prospecting / Milling and the
// tracking spells (SPELL_AURA_TRACK_RESOURCES: Find Herbs / Minerals / Fish). That is what the trade skill window
// lists. Sent on login, after a recipe or profession rank is learned, after a recipe is removed or a profession is
// unlearned, on a gathering rank-up, and when the client asks (body "REQ" whispered to himself; swallowed here).
// Several changes in one update coalesce into one message. Players without a client (bots) get nothing.
// On login and on "REQ" the Gathering Ranks window's material list ("G1" bodies, custom_gathering_ranks.cpp) follows
// the feed under the same prefix.

#include "Chat.h"
#include "Config.h"
#include "custom_crafting.h"
#include "DataMap.h"
#include "Log.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "StringFormat.h"
#include "Trainer.h"
#include "WorldPacket.h"
#include "WorldSession.h"
#include <algorithm>
#include <array>
#include <string>

namespace
{
    struct ProfessionChain
    {
        uint16 skillId;
        uint32 firstRankSpell; // Apprentice rank, first spell of the spell_ranks chain
    };

    std::array<ProfessionChain, 14> constexpr Professions =
    { {
        { SKILL_ALCHEMY,        2259  },
        { SKILL_BLACKSMITHING,  2018  },
        { SKILL_ENCHANTING,     7411  },
        { SKILL_ENGINEERING,    4036  },
        { SKILL_INSCRIPTION,    45357 },
        { SKILL_JEWELCRAFTING,  25229 },
        { SKILL_LEATHERWORKING, 2108  },
        { SKILL_TAILORING,      3908  },
        { SKILL_HERBALISM,      2366  },
        { SKILL_MINING,         2575  },
        { SKILL_SKINNING,       8613  },
        { SKILL_COOKING,        2550  },
        { SKILL_FIRST_AID,      3273  },
        { SKILL_FISHING,        7620  },
    } };

    // Granted to everyone on login.
    std::array<uint16, 3> constexpr GatheringSkills = { SKILL_HERBALISM, SKILL_MINING, SKILL_SKINNING };

    // The stripped gathering perks: Toughness (Mining), Master of Anatomy (Skinning), Lifeblood (Herbalism), every
    // rank. Their SkillLineAbility rows no longer teach them; this removes them from characters who know them.
    std::array<uint32, 18> constexpr GatheringPerkSpells =
    {
        53120, 53121, 53122, 53123, 53124, 53040, // Toughness
        53125, 53662, 53663, 53664, 53665, 53666, // Master of Anatomy
        55428, 55480, 55500, 55501, 55502, 55503, // Lifeblood
    };

    uint16 constexpr MinSkillCap = 75;  // Apprentice
    uint16 constexpr MaxSkillCap = 450; // Grand Master

    struct ProfessionSettings
    {
        bool enabled = true;
        uint16 skillCap = 300;
    };

    ProfessionSettings Settings;

    // Set while RaiseToCap teaches rank spells, so the OnPlayerLearnSpell those fire does not schedule another raise.
    thread_local bool RaisingSkill = false;

    ProfessionChain const* FindProfession(uint32 skillId)
    {
        auto itr = std::find_if(Professions.begin(), Professions.end(), [skillId](ProfessionChain const& chain)
        {
            return chain.skillId == skillId;
        });
        return itr != Professions.end() ? &(*itr) : nullptr;
    }

    // The profession a rank spell belongs to (SPELL_EFFECT_SKILL of a managed skill), or nullptr.
    ProfessionChain const* FindProfessionOfRank(uint32 spellId)
    {
        SpellLearnSkillNode const* node = sSpellMgr->GetSpellLearnSkill(spellId);
        return node ? FindProfession(node->skill) : nullptr;
    }

    // Teaches the ranks of `chain` up to the cap and sets value = max = cap. Learns the first rank when the player
    // lacks the skill only if `grantMissing` (the gathering grant); otherwise an unknown profession is left alone.
    void RaiseToCap(Player* player, ProfessionChain const& chain, bool grantMissing)
    {
        if (!player->HasSkill(chain.skillId) && !grantMissing)
            return;

        uint16 const cap = Settings.skillCap;
        if (player->HasSkill(chain.skillId) && player->GetPureSkillValue(chain.skillId) >= cap &&
            player->GetPureMaxSkillValue(chain.skillId) >= cap)
            return;

        RaisingSkill = true;
        uint16 step = 0;
        for (uint32 rankSpell = chain.firstRankSpell; rankSpell; rankSpell = sSpellMgr->GetNextSpellInChain(rankSpell))
        {
            SpellLearnSkillNode const* node = sSpellMgr->GetSpellLearnSkill(rankSpell);
            if (!node || node->skill != chain.skillId || node->maxvalue > cap)
                break;

            if (!player->HasSpell(rankSpell))
                player->learnSpell(rankSpell);

            step = node->step;
        }
        RaisingSkill = false;

        if (!step || !player->HasSkill(chain.skillId))
        {
            LOG_WARN("scripts.custom", "custom_professions: {} could not learn skill {} (no free skill slot, or the "
                "first rank {} was refused)", player->GetGUID().ToString(), chain.skillId, chain.firstRankSpell);
            return;
        }

        // Never lower: a character above the cap (cap lowered by hand, or trained before the cap existed) keeps it.
        uint16 const value = std::max(player->GetPureSkillValue(chain.skillId), cap);
        uint16 const max = std::max(player->GetPureMaxSkillValue(chain.skillId), cap);
        player->SetSkill(chain.skillId, std::max(player->GetSkillStep(chain.skillId), step), value, max);
    }

    // --- Professions page feed ---

    std::string const FeedPrefix = "CPROF";
    std::string const FeedRequest = "REQ";
    char constexpr FeedVersion = '1';
    std::string const FeedStateKey = "Custom_Professions.Feed";

    // A feed message is queued for the player's next update (coalesces several learns in one update).
    struct FeedState : public DataMap::Base
    {
        bool pending = false;
        bool materials = false; // also send the Gathering Ranks window's list
    };

    // Spells of a profession that are not recipes (rank spells, window openers, Disenchant / Prospecting / Milling,
    // Find Herbs / Minerals / Fish): the trade window shows none of them.
    bool IsProfessionTool(SpellInfo const* spellInfo)
    {
        return spellInfo->IsPassive() || spellInfo->HasEffect(SPELL_EFFECT_SKILL) ||
            spellInfo->HasEffect(SPELL_EFFECT_TRADE_SKILL) || spellInfo->HasEffect(SPELL_EFFECT_DISENCHANT) ||
            spellInfo->HasEffect(SPELL_EFFECT_PROSPECTING) || spellInfo->HasEffect(SPELL_EFFECT_MILLING) ||
            spellInfo->HasAura(SPELL_AURA_TRACK_RESOURCES); // Find Herbs / Minerals / Fish
    }

    // The managed profession a spell belongs to through SkillLineAbility, or nullptr.
    ProfessionChain const* FindProfessionOfAbility(uint32 spellId)
    {
        SkillLineAbilityMapBounds bounds = sSpellMgr->GetSkillLineAbilityMapBounds(spellId);
        for (auto itr = bounds.first; itr != bounds.second; ++itr)
            if (ProfessionChain const* chain = FindProfession(itr->second->SkillLine))
                return chain;
        return nullptr;
    }

    std::string BuildFeed(Player const* player)
    {
        std::array<uint32, Professions.size()> recipes = { };
        for (auto const& [spellId, playerSpell] : player->GetSpellMap())
        {
            if (playerSpell->State == PLAYERSPELL_REMOVED)
                continue;

            ProfessionChain const* chain = FindProfessionOfAbility(spellId);
            if (!chain)
                continue;

            SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(spellId);
            if (!spellInfo || IsProfessionTool(spellInfo))
                continue;

            ++recipes[chain - Professions.data()];
        }

        std::string body(1, FeedVersion);
        for (std::size_t i = 0; i < Professions.size(); ++i)
        {
            if (!player->HasSkill(Professions[i].skillId))
                continue;

            // Third field: gathering rank (crafting rework C3), gathering skills only.
            body += Acore::StringFormat(";{},{},", Professions[i].skillId, recipes[i]);
            uint16 const skillId = Professions[i].skillId;
            if (std::find(GatheringSkills.begin(), GatheringSkills.end(), skillId) != GatheringSkills.end())
                body += std::to_string(CustomGathering::GetBestRank(player, skillId));
        }
        return body;
    }

    void SendFeed(Player* player)
    {
        CustomProfessions::SendAddonMessage(player, BuildFeed(player));
    }

    // Sends the feed on the player's next update, once however often it is asked for in the meantime. `materials`
    // (login, client request) also sends the Gathering Ranks window's list (custom_gathering_ranks.cpp) after it.
    void ScheduleFeed(Player* player, Milliseconds delay = 0ms, bool materials = false)
    {
        if (!player->GetSession() || player->GetSession()->IsSocketClosed())
            return;

        FeedState* state = player->CustomData.GetDefault<FeedState>(FeedStateKey);
        state->materials = state->materials || materials;
        if (state->pending)
            return;

        state->pending = true;
        player->m_Events.AddEventAtOffset([player]()
        {
            FeedState* sending = player->CustomData.GetDefault<FeedState>(FeedStateKey);
            bool const withMaterials = sending->materials;
            sending->pending = false;
            sending->materials = false;
            if (!player->IsInWorld())
                return;

            SendFeed(player);
            if (withMaterials)
                CustomGathering::SendMaterialFeed(player);
        }, delay);
    }
}

void CustomProfessions::QueueFeed(Player* player)
{
    ScheduleFeed(player);
}

void CustomProfessions::SendAddonMessage(Player* player, std::string const& body)
{
    WorldSession* session = player->GetSession();
    if (!session || session->IsSocketClosed())
        return;

    std::string const message = FeedPrefix + '\t' + body;
    WorldPacket data;
    ChatHandler::BuildChatPacket(data, CHAT_MSG_WHISPER, LANG_ADDON, player, player, message);
    player->SendDirectMessage(&data);
}

class Custom_ProfessionsConfig : public WorldScript
{
public:
    Custom_ProfessionsConfig() : WorldScript("Custom_ProfessionsConfig", { WORLDHOOK_ON_AFTER_CONFIG_LOAD }) { }

    void OnAfterConfigLoad(bool /*reload*/) override
    {
        Settings.enabled = sConfigMgr->GetOption<bool>("Custom.Professions.Enable", true);
        uint32 const cap = sConfigMgr->GetOption<uint32>("Custom.Professions.SkillCap", 300);
        Settings.skillCap = uint16(std::clamp<uint32>(cap, MinSkillCap, MaxSkillCap));
        if (Settings.skillCap != cap)
            LOG_ERROR("server.loading", "Custom.Professions.SkillCap = {} is outside {}-{}, using {}", cap, MinSkillCap,
                MaxSkillCap, Settings.skillCap);
    }
};

class Custom_Professions : public PlayerScript
{
public:
    Custom_Professions() : PlayerScript("Custom_Professions",
        { PLAYERHOOK_ON_LOGIN, PLAYERHOOK_ON_LEARN_SPELL, PLAYERHOOK_ON_GET_TRAINER_SPELL_STATE,
          PLAYERHOOK_CAN_LEARN_SPELL, PLAYERHOOK_ON_SET_SKILL, PLAYERHOOK_CAN_PLAYER_USE_PRIVATE_CHAT,
          PLAYERHOOK_ON_FORGOT_SPELL }) { }

    using PlayerScript::OnPlayerCanUseChat;

    void OnPlayerLogin(Player* player) override
    {
        // The page feed goes out whatever Custom.Professions.Enable says: it only reports what the player knows. The
        // delay leaves the client time to finish loading its UI; the client also asks once it is in the world.
        ScheduleFeed(player, 2s, true);

        if (!Settings.enabled)
            return;

        // Grant only once the data half is live: while gathering is still a primary profession (no skillline_dbc
        // override), learnSpell does not check free profession points, so the grant would exceed the limit and the
        // Unlearn button would hand the slot back for a third crafting profession.
        if (!IsPrimaryProfessionSkill(SKILL_MINING))
            for (uint16 skillId : GatheringSkills)
                if (ProfessionChain const* chain = FindProfession(skillId))
                    RaiseToCap(player, *chain, true);

        for (ProfessionChain const& chain : Professions)
            RaiseToCap(player, chain, false);

        // Last, so a skill the raise above set cannot teach a perk back (it cannot once the data is live either).
        for (uint32 spellId : GatheringPerkSpells)
            if (player->HasSpell(spellId))
                player->removeSpell(spellId, SPEC_MASK_ALL, false);
    }

    // A profession rank was learned (the first rank from a trainer, a book, a GM command). The raise waits for the
    // player's next update: from inside learnSpell it would send the higher ranks' SMSG_SUPERCEDED_SPELL before the
    // learn packet of the rank being learned, which learnSpell sends after this hook returns.
    // A recipe was learned: the page feed goes out on the next update.
    void OnPlayerLearnSpell(Player* player, uint32 spellId) override
    {
        if (RaisingSkill)
            return;

        ProfessionChain const* chain = FindProfessionOfRank(spellId);
        if (!chain || !Settings.enabled)
        {
            if (chain || FindProfessionOfAbility(spellId))
                ScheduleFeed(player);
            return;
        }

        uint16 const skillId = chain->skillId;
        player->m_Events.AddEventAtOffset([player, skillId]()
        {
            if (!Settings.enabled || !player->IsInWorld())
                return;

            if (ProfessionChain const* raised = FindProfession(skillId))
                RaiseToCap(player, *raised, false);

            // After the raise, so the feed lists the new profession with the recipes the ranks taught.
            ScheduleFeed(player);
        }, 0ms);
    }

    // A recipe was removed (GM .unlearn, or a profession's spells going with it): the count drops on the next feed.
    void OnPlayerForgotSpell(Player* player, uint32 spellId) override
    {
        if (FindProfessionOfAbility(spellId))
            ScheduleFeed(player);
    }

    // A profession was unlearned (Unlearn button, AbandonSkill): the page drops its card on the next feed.
    void OnPlayerSetSkill(Player* player, uint32 skillId, uint32 /*value*/, uint32 /*max*/, uint32 /*step*/,
        uint32 newValue) override
    {
        if (!newValue && FindProfession(skillId))
            ScheduleFeed(player);
    }

    // The client asks for the feed by whispering "REQ" to itself under the feed prefix. Every whisper to self under
    // that prefix is swallowed, so it never echoes back.
    bool OnPlayerCanUseChat(Player* player, uint32 type, uint32 language, std::string& msg, Player* receiver) override
    {
        if (language != LANG_ADDON || type != CHAT_MSG_WHISPER || receiver != player ||
            msg.compare(0, FeedPrefix.size() + 1, FeedPrefix + '\t') != 0)
            return true;

        if (msg.compare(FeedPrefix.size() + 1, std::string::npos, FeedRequest) == 0)
            ScheduleFeed(player, 0ms, true);
        return false;
    }

    // A profession rank above the cap cannot be learned by any route: trainer, recipe book (Master First Aid, Fishing
    // and Cooking books), quest reward or GM command all go through Player::learnSpell.
    bool OnPlayerCanLearnSpell(Player* /*player*/, uint32 spellId) override
    {
        if (!Settings.enabled)
            return true;

        SpellLearnSkillNode const* node = sSpellMgr->GetSpellLearnSkill(spellId);
        return !(node && FindProfession(node->skill) && node->maxvalue > Settings.skillCap);
    }

    // A trainer entry that teaches a profession rank above the cap (Master at a 300 cap) is unavailable, so it can be
    // neither shown as buyable nor bought (Trainer::CanTeachSpell refuses anything not Available).
    void OnPlayerGetTrainerSpellState(Player const* /*player*/, uint32 /*trainerId*/, uint32 spellId,
        Trainer::SpellState& state) override
    {
        if (!Settings.enabled || state != Trainer::SpellState::Available)
            return;

        SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(spellId);
        if (!spellInfo)
            return;

        auto aboveCap = [](uint32 rankSpell)
        {
            SpellLearnSkillNode const* node = sSpellMgr->GetSpellLearnSkill(rankSpell);
            return node && FindProfession(node->skill) && node->maxvalue > Settings.skillCap;
        };

        if (aboveCap(spellId))
        {
            state = Trainer::SpellState::Unavailable;
            return;
        }

        for (SpellEffectInfo const& effect : spellInfo->GetEffects())
        {
            if (effect.IsEffect(SPELL_EFFECT_LEARN_SPELL) && aboveCap(effect.TriggerSpell))
            {
                state = Trainer::SpellState::Unavailable;
                return;
            }
        }
    }
};

void AddSC_custom_professions()
{
    new Custom_ProfessionsConfig();
    new Custom_Professions();
}
