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

// Custom: featured quests, the "golden path" (.agents/plans/featured-quests/, stage FQ1).
//
// The world table custom_featured_quest sorts quests into two tiers; every other quest keeps stock behavior.
// - Featured (Tier 1): the quest giver's "!" stays yellow however far the player outlevels the quest, and its XP
//   ignores the grey-quest penalty and partly grows with the player: the QuestXP.dbc value at
//   max(quest level, player level - 5) for the quest's XP difficulty, times the quest rate and quest XP auras.
// - Filler (Tier 2): the "!" is reported as low level even at the player's level, so the client hides it unless
//   Minimap tracking > Low Level Quests is on. The quest stays acceptable and its XP is stock.
//
// The status goes through OnPlayerGetQuestDialogStatus (a custom hook in Player::GetQuestDialogStatus, quests the
// player has not taken yet); the XP through OnPlayerQuestComputeXP, which covers the reward and the XP shown in the
// quest windows.

#include "Config.h"
#include "DBCStores.h"
#include "DatabaseEnv.h"
#include "Log.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "QueryResult.h"
#include "QuestDef.h"
#include "ScriptMgr.h"
#include <algorithm>
#include <iterator>
#include <unordered_map>

namespace
{
    enum class FeaturedQuestTier : uint8
    {
        Featured = 1,
        Filler   = 2
    };

    // How far below the player's level a featured quest's XP level may sit.
    constexpr int32 FeaturedXPLevelLag = 5;

    struct FeaturedQuestSettings
    {
        bool enabled = true;
    };

    FeaturedQuestSettings Settings;
    std::unordered_map<uint32, FeaturedQuestTier> QuestTiers;

    FeaturedQuestTier const* GetTier(uint32 questId)
    {
        auto itr = QuestTiers.find(questId);
        return itr != QuestTiers.end() ? &itr->second : nullptr;
    }

    // The quest-XP level a featured quest pays at: the quest's own level, but never more than FeaturedXPLevelLag
    // below the player, clamped to [1, maxXPLevel]. questLevel -1 (scales with the player) is the player's level.
    uint32 FeaturedXPLevel(int32 questLevel, uint32 playerLevel, uint32 maxXPLevel)
    {
        int32 const level = questLevel == -1 ? int32(playerLevel) : questLevel;
        int32 const effective = std::max(level, int32(playerLevel) - FeaturedXPLevelLag);
        return uint32(std::clamp<int32>(effective, 1, int32(maxXPLevel)));
    }

    // The small-value rounding of Quest::XPValue.
    uint32 RoundQuestXP(uint32 xp)
    {
        if (xp <= 100)
            return 5 * ((xp + 2) / 5);
        if (xp <= 500)
            return 10 * ((xp + 5) / 10);
        if (xp <= 1000)
            return 25 * ((xp + 12) / 25);
        return 50 * ((xp + 25) / 50);
    }

    // Featured quest XP before rates: Quest::XPValue without the diff-factor (grey-quest) penalty, read at
    // FeaturedXPLevel. 0 when QuestXP.dbc has no row or the quest's XP difficulty is out of range.
    uint32 FeaturedQuestBaseXP(Quest const* quest, uint8 playerLevel)
    {
        if (sQuestXPStore.GetNumRows() < 2)
            return 0;

        uint32 const level = FeaturedXPLevel(quest->GetQuestLevel(), playerLevel, sQuestXPStore.GetNumRows() - 1);
        QuestXPEntry const* entry = sQuestXPStore.LookupEntry(level);
        uint32 const difficulty = quest->GetXPId();
        if (!entry || difficulty >= std::size(entry->Exp))
            return 0;

        return RoundQuestXP(entry->Exp[difficulty]);
    }

    void LoadFeaturedQuests()
    {
        QuestTiers.clear();

        QueryResult result = WorldDatabase.Query("SELECT QuestId, Tier FROM custom_featured_quest");
        if (!result)
        {
            LOG_INFO("server.loading", ">> Featured quests: 0 featured, 0 filler (custom_featured_quest is empty)");
            return;
        }

        uint32 featured = 0;
        uint32 filler = 0;
        do
        {
            Field* fields = result->Fetch();
            uint32 const questId = fields[0].Get<uint32>();
            uint8 const tier = fields[1].Get<uint8>();

            if (!sObjectMgr->GetQuestTemplate(questId))
            {
                LOG_ERROR("sql.sql", "Table `custom_featured_quest` has quest {} which does not exist, skipped",
                    questId);
                continue;
            }

            switch (FeaturedQuestTier(tier))
            {
                case FeaturedQuestTier::Featured:
                    ++featured;
                    break;
                case FeaturedQuestTier::Filler:
                    ++filler;
                    break;
                default:
                    LOG_ERROR("sql.sql", "Table `custom_featured_quest` has quest {} with unknown Tier {}, skipped",
                        questId, tier);
                    continue;
            }

            QuestTiers[questId] = FeaturedQuestTier(tier);
        } while (result->NextRow());

        LOG_INFO("server.loading", ">> Featured quests: {} featured, {} filler", featured, filler);
    }
}

class Custom_FeaturedQuestsWorld : public WorldScript
{
public:
    Custom_FeaturedQuestsWorld() : WorldScript("Custom_FeaturedQuestsWorld",
        { WORLDHOOK_ON_AFTER_CONFIG_LOAD, WORLDHOOK_ON_STARTUP }) { }

    void OnAfterConfigLoad(bool /*reload*/) override
    {
        Settings.enabled = sConfigMgr->GetOption<bool>("Custom.FeaturedQuests.Enable", true);
    }

    void OnStartup() override
    {
        LoadFeaturedQuests();
    }
};

class Custom_FeaturedQuestsPlayer : public PlayerScript
{
public:
    Custom_FeaturedQuestsPlayer() : PlayerScript("Custom_FeaturedQuestsPlayer",
        { PLAYERHOOK_ON_GET_QUEST_DIALOG_STATUS, PLAYERHOOK_ON_QUEST_COMPUTE_EXP }) { }

    void OnPlayerGetQuestDialogStatus(Player* /*player*/, Quest const* quest, QuestGiverStatus& status) override
    {
        if (!Settings.enabled || !quest)
            return;

        FeaturedQuestTier const* tier = GetTier(quest->GetQuestId());
        if (!tier)
            return;

        if (*tier == FeaturedQuestTier::Featured)
        {
            switch (status)
            {
                case DIALOG_STATUS_LOW_LEVEL_AVAILABLE:
                    status = DIALOG_STATUS_AVAILABLE;
                    break;
                case DIALOG_STATUS_LOW_LEVEL_AVAILABLE_REP:
                    status = DIALOG_STATUS_AVAILABLE_REP;
                    break;
                case DIALOG_STATUS_LOW_LEVEL_REWARD_REP:
                    status = DIALOG_STATUS_REWARD_REP;
                    break;
                default:
                    break;
            }
            return;
        }

        switch (status)
        {
            case DIALOG_STATUS_AVAILABLE:
                status = DIALOG_STATUS_LOW_LEVEL_AVAILABLE;
                break;
            case DIALOG_STATUS_AVAILABLE_REP:
                status = DIALOG_STATUS_LOW_LEVEL_AVAILABLE_REP;
                break;
            case DIALOG_STATUS_REWARD_REP:
                status = DIALOG_STATUS_LOW_LEVEL_REWARD_REP;
                break;
            default:
                break;
        }
    }

    void OnPlayerQuestComputeXP(Player* player, Quest const* quest, uint32& xpValue) override
    {
        if (!Settings.enabled || !player || !quest)
            return;

        // Core's zero-XP cases: money instead of XP, or a repeatable quest already rewarded (Player::RewardQuest).
        // Not keyed on xpValue == 0, since a grey quest's stock XP can round down to 0.
        if (sScriptMgr->OnPlayerShouldBeRewardedWithMoneyInsteadOfExp(player))
            return;

        if (player->IsQuestRewarded(quest->GetQuestId()) && !quest->IsDFQuest() &&
            !(quest->IsDaily() || quest->IsWeekly() || quest->IsMonthly()))
            return;

        FeaturedQuestTier const* tier = GetTier(quest->GetQuestId());
        if (!tier || *tier != FeaturedQuestTier::Featured)
            return;

        // As Player::CalculateQuestRewardXP.
        uint8 level = player->GetLevel();
        sScriptMgr->OnPlayerBeforeGetLevelForXPGain(player, level);

        uint32 const baseXP = FeaturedQuestBaseXP(quest, level);
        if (!baseXP)
            return;

        uint32 xp = uint32(baseXP * player->GetQuestRate(quest->IsDFQuest()));
        xp *= player->GetTotalAuraMultiplier(SPELL_AURA_MOD_XP_QUEST_PCT);
        xpValue = xp;
    }
};

void AddSC_custom_featured_quests()
{
    new Custom_FeaturedQuestsWorld();
    new Custom_FeaturedQuestsPlayer();
}
