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

// Custom: Class Advancement window bridge (classless-ui U2, .agents/plans/classless-ui/classless-ui.PLAN.md section 5).
//
// The client's talent window (patch-X) reads and learns talents through addon messages under the "CTAL" prefix
// instead of the stock talent Lua API, which only knows the player's own class (the Hero class will need every tab).
//
// Client -> server: SendAddonMessage("CTAL", body, "WHISPER", UnitName("player")). The whisper to self is caught in
// OnPlayerCanUseChat and swallowed, so it never reaches real chat.
// Server -> client: a LANG_ADDON whisper from the player to the player, "CTAL\t<body>", read from CHAT_MSG_ADDON.
//
//   C->S HELLO                                   -> CFG then ST
//   C->S GET                                     -> ST
//   C->S LEARN;<part>/<parts>;<talentId>:<rank>,...
//                                                -> (after the last part) LR, then SMSG_TALENTS_INFO, then ST
//   S->C CFG;<classes>;<rowGate>;<group>/<groups>
//   S->C ST;<part>/<parts>;<talentId>:<rank>,...  learned talents of the active group, rank 1-based
//   S->C LR;<code>;<talentId>;<learnedCount>
//
// LR codes: 0 OK, 1 not enough points, 2 other class's tree, 3 row gate, 4 DependsOn not met, 5 unknown talent or
// rank (also a refusal LearnTalent made that the checks here did not predict, e.g. a script veto), 6 busy or rate
// limited, 7 malformed, 8 every entry was already at or above its rank (nothing to do).
//
// LEARN entries run in the order sent and stop at the first failure; Player::LearnTalent stays the authority, the
// checks before it only pick the error code. HELLO, GET and the first part of a LEARN share one 200 ms rate limit per
// player; the later parts of a LEARN are not limited (the client sends them in one burst) but must arrive in order.
//
// All of this runs on the world thread: CMSG_MESSAGECHAT is PROCESS_THREADUNSAFE, and so are commands and logout.

#include "Chat.h"
#include "ChatCommand.h"
#include "Config.h"
#include "DBCStores.h"
#include "Log.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellMgr.h"
#include "StringConvert.h"
#include "StringFormat.h"
#include "Tokenize.h"
#include "WorldPacket.h"
#include "WorldSession.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <map>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;

namespace
{
    std::string const TalentPrefix = "CTAL";

    // The 3.3.5 client caps an addon message near 255 bytes including the prefix and the tab.
    std::size_t constexpr MaxBodySize = 240;

    // A LEARN plan holds at most this many entries over all its parts, in at most this many parts.
    std::size_t constexpr MaxPlanEntries = 255;
    uint32 constexpr MaxPlanParts = 32;

    std::chrono::milliseconds constexpr MinRequestInterval{ 200 };

    enum LearnResult : uint32
    {
        LEARN_RESULT_OK              = 0,
        LEARN_RESULT_NO_POINTS       = 1,
        LEARN_RESULT_OTHER_CLASS     = 2,
        LEARN_RESULT_ROW_GATE        = 3,
        LEARN_RESULT_DEPENDS_ON      = 4,
        LEARN_RESULT_UNKNOWN         = 5,
        LEARN_RESULT_BUSY            = 6,
        LEARN_RESULT_MALFORMED       = 7,
        LEARN_RESULT_ALREADY_KNOWN   = 8
    };

    // Client class tokens in the order CFG lists them with the GM toggle on.
    std::array<std::pair<uint8, char const*>, 10> constexpr ClassTokens =
    { {
        { CLASS_WARRIOR,      "WARRIOR"     },
        { CLASS_PALADIN,      "PALADIN"     },
        { CLASS_HUNTER,       "HUNTER"      },
        { CLASS_ROGUE,        "ROGUE"       },
        { CLASS_PRIEST,       "PRIEST"      },
        { CLASS_DEATH_KNIGHT, "DEATHKNIGHT" },
        { CLASS_SHAMAN,       "SHAMAN"      },
        { CLASS_MAGE,         "MAGE"        },
        { CLASS_WARLOCK,      "WARLOCK"     },
        { CLASS_DRUID,        "DRUID"       },
    } };

    struct PlanEntry
    {
        uint32 talentId;
        uint32 rank; // 1-based target rank
    };

    struct TalentUIState
    {
        std::chrono::steady_clock::time_point lastRequest{};
        bool allClasses = false;    // GM toggle: CFG lists all ten classes
        bool learning = false;      // a LEARN is executing
        uint32 planParts = 0;       // parts of the buffered plan, 0 = no plan buffered
        uint32 nextPart = 0;        // next part expected
        uint32 discardParts = 0;    // remaining parts of a dropped plan, swallowed silently
        std::vector<PlanEntry> plan;

        void ResetPlan()
        {
            planParts = 0;
            nextPart = 0;
            plan.clear();
            plan.shrink_to_fit();
        }
    };

    struct
    {
        bool enabled = true;
    } Settings;

    std::unordered_map<ObjectGuid, TalentUIState> States;

    void SendTalentMessage(Player* player, std::string const& body)
    {
        WorldSession* session = player->GetSession();
        if (!session || session->IsSocketClosed())
            return;

        WorldPacket data;
        ChatHandler::BuildChatPacket(data, CHAT_MSG_WHISPER, LANG_ADDON, player, player, TalentPrefix + '\t' + body);
        player->SendDirectMessage(&data);
    }

    void SendLearnResult(Player* player, uint32 code, uint32 talentId, uint32 learnedCount)
    {
        SendTalentMessage(player, Acore::StringFormat("LR;{};{};{}", code, talentId, learnedCount));
    }

    bool AcceptRequest(TalentUIState& state)
    {
        auto const now = std::chrono::steady_clock::now();
        if (state.lastRequest.time_since_epoch().count() && now - state.lastRequest < MinRequestInterval)
            return false;

        state.lastRequest = now;
        return true;
    }

    char const* ClassToken(uint8 classId)
    {
        for (auto const& [id, token] : ClassTokens)
            if (id == classId)
                return token;
        return nullptr;
    }

    std::string BuildCfgBody(Player* player, bool allClasses)
    {
        std::string classes;
        if (allClasses)
        {
            for (auto const& [id, token] : ClassTokens)
            {
                if (!classes.empty())
                    classes += ',';
                classes += token;
            }
        }
        else if (char const* token = ClassToken(player->getClass()))
            classes = token;

        return Acore::StringFormat("CFG;{};{};{}/{}", classes, MAX_TALENT_RANK, uint32(player->GetActiveSpec()) + 1,
            uint32(player->GetSpecsCount()));
    }

    // Learned talents of the active group, the way Player::BuildPlayerTalentsInfoData walks the talent map. Keyed by
    // talent id, highest rank kept, so each talent appears once and in id order.
    std::map<uint32, uint32> CollectActiveTalents(Player* player)
    {
        std::map<uint32, uint32> talents;
        uint8 const spec = player->GetActiveSpec();
        for (auto const& [spellId, talent] : player->GetTalentMap())
        {
            if (!talent || talent->State == PLAYERSPELL_REMOVED || !talent->IsInSpec(spec))
                continue;

            TalentSpellPos const* talentPos = GetTalentSpellPos(spellId);
            if (!talentPos)
                continue;

            uint32& rank = talents[talentPos->talent_id];
            rank = std::max<uint32>(rank, uint32(talentPos->rank) + 1);
        }
        return talents;
    }

    std::vector<std::string> BuildStBodies(Player* player)
    {
        // "ST;" + "<part>/<parts>;" with up to three digits each.
        std::size_t constexpr HeaderReserve = 3 + 3 + 1 + 3 + 1;

        std::vector<std::string> payloads(1);
        for (auto const& [talentId, rank] : CollectActiveTalents(player))
        {
            std::string const item = Acore::StringFormat("{}:{}", talentId, rank);
            std::string& current = payloads.back();
            if (!current.empty() && HeaderReserve + current.size() + 1 + item.size() > MaxBodySize)
                payloads.emplace_back(item);
            else
            {
                if (!current.empty())
                    current += ',';
                current += item;
            }
        }

        std::vector<std::string> bodies;
        bodies.reserve(payloads.size());
        for (std::size_t i = 0; i < payloads.size(); ++i)
            bodies.push_back(Acore::StringFormat("ST;{}/{};{}", i + 1, payloads.size(), payloads[i]));
        return bodies;
    }

    void SendTalentState(Player* player)
    {
        for (std::string const& body : BuildStBodies(player))
            SendTalentMessage(player, body);
    }

    uint32 CurrentTalentRank(Player* player, TalentEntry const* talentInfo)
    {
        for (uint8 rank = 0; rank < MAX_TALENT_RANK; ++rank)
            if (talentInfo->RankID[rank] && player->HasTalent(talentInfo->RankID[rank], player->GetActiveSpec()))
                return rank + 1;
        return 0;
    }

    // The reason Player::LearnTalent would refuse this entry, in the order the handoff ranks them, or OK. Mirrors its
    // checks only to pick an error code.
    uint32 DiagnoseLearn(Player* player, TalentEntry const* talentInfo, uint32 rank, uint32 currentRank)
    {
        if (!talentInfo || rank < 1 || rank > MAX_TALENT_RANK)
            return LEARN_RESULT_UNKNOWN;

        uint32 const spellId = talentInfo->RankID[rank - 1];
        if (!spellId || !sSpellMgr->GetSpellInfo(spellId))
            return LEARN_RESULT_UNKNOWN;

        TalentTabEntry const* talentTabInfo = sTalentTabStore.LookupEntry(talentInfo->TalentTab);
        if (!talentTabInfo)
            return LEARN_RESULT_UNKNOWN;

        if ((player->getClassMask() & talentTabInfo->ClassMask) == 0)
            return LEARN_RESULT_OTHER_CLASS;

        if (player->GetFreeTalentPoints() < rank - currentRank)
            return LEARN_RESULT_NO_POINTS;

        if (talentInfo->DependsOn > 0)
        {
            if (TalentEntry const* depTalentInfo = sTalentStore.LookupEntry(talentInfo->DependsOn))
            {
                bool hasEnoughRank = false;
                for (uint8 depRank = talentInfo->DependsOnRank; depRank < MAX_TALENT_RANK; ++depRank)
                {
                    if (depTalentInfo->RankID[depRank] &&
                        player->HasTalent(depTalentInfo->RankID[depRank], player->GetActiveSpec()))
                    {
                        hasEnoughRank = true;
                        break;
                    }
                }

                if (!hasEnoughRank)
                    return LEARN_RESULT_DEPENDS_ON;
            }
        }

        if (talentInfo->Row > 0)
        {
            uint32 spentPoints = 0;
            uint8 const spec = player->GetActiveSpec();
            for (auto const& [spellIdInMap, talent] : player->GetTalentMap())
            {
                if (!talent || talent->State == PLAYERSPELL_REMOVED || !talent->IsInSpec(spec))
                    continue;

                if (TalentSpellPos const* talentPos = GetTalentSpellPos(spellIdInMap))
                    if (TalentEntry const* itrTalentInfo = sTalentStore.LookupEntry(talentPos->talent_id))
                        if (itrTalentInfo->TalentTab == talentInfo->TalentTab)
                            spentPoints += talentPos->rank + 1;
            }

            if (spentPoints < talentInfo->Row * MAX_TALENT_RANK)
                return LEARN_RESULT_ROW_GATE;
        }

        return LEARN_RESULT_OK;
    }

    void ExecutePlan(Player* player, std::vector<PlanEntry> const& plan)
    {
        uint32 learnedCount = 0;
        uint32 skippedCount = 0;
        uint32 failCode = LEARN_RESULT_OK;
        uint32 failTalentId = 0;

        for (PlanEntry const& entry : plan)
        {
            TalentEntry const* talentInfo = sTalentStore.LookupEntry(entry.talentId);
            uint32 const currentRank = talentInfo ? CurrentTalentRank(player, talentInfo) : 0;

            // Already at or above the target: skipped, the plan goes on.
            if (talentInfo && entry.rank >= 1 && entry.rank <= MAX_TALENT_RANK && currentRank >= entry.rank)
            {
                ++skippedCount;
                continue;
            }

            uint32 code = DiagnoseLearn(player, talentInfo, entry.rank, currentRank);
            if (code == LEARN_RESULT_OK)
            {
                player->LearnTalent(entry.talentId, entry.rank - 1);
                if (CurrentTalentRank(player, talentInfo) != entry.rank)
                    code = LEARN_RESULT_UNKNOWN;
            }

            if (code != LEARN_RESULT_OK)
            {
                failCode = code;
                failTalentId = entry.talentId;
                break;
            }

            ++learnedCount;
        }

        if (failCode == LEARN_RESULT_OK)
        {
            uint32 const lastTalentId = plan.empty() ? 0 : plan.back().talentId;
            if (!learnedCount && skippedCount)
                SendLearnResult(player, LEARN_RESULT_ALREADY_KNOWN, lastTalentId, 0);
            else
                SendLearnResult(player, LEARN_RESULT_OK, lastTalentId, learnedCount);
        }
        else
            SendLearnResult(player, failCode, failTalentId, learnedCount);

        player->SendTalentsInfoData(false);
        SendTalentState(player);
    }

    // "<talentId>:<rank>,..." appended to `plan`. False on any bad entry or when the plan would exceed its cap.
    bool ParsePlanEntries(std::string_view text, std::vector<PlanEntry>& plan)
    {
        for (std::string_view item : Acore::Tokenize(text, ',', false))
        {
            std::vector<std::string_view> pair = Acore::Tokenize(item, ':', true);
            if (pair.size() != 2)
                return false;

            Optional<uint32> talentId = Acore::StringTo<uint32>(pair[0]);
            Optional<uint32> rank = Acore::StringTo<uint32>(pair[1]);
            if (!talentId || !rank || plan.size() >= MaxPlanEntries)
                return false;

            plan.push_back({ *talentId, *rank });
        }
        return true;
    }

    // "<part>/<parts>" with 1 <= part <= parts <= MaxPlanParts.
    bool ParsePart(std::string_view text, uint32& part, uint32& parts)
    {
        std::vector<std::string_view> pair = Acore::Tokenize(text, '/', true);
        if (pair.size() != 2)
            return false;

        Optional<uint32> partValue = Acore::StringTo<uint32>(pair[0]);
        Optional<uint32> partsValue = Acore::StringTo<uint32>(pair[1]);
        if (!partValue || !partsValue || *partValue < 1 || *partValue > *partsValue || *partsValue > MaxPlanParts)
            return false;

        part = *partValue;
        parts = *partsValue;
        return true;
    }

    void HandleLearn(Player* player, TalentUIState& state, std::vector<std::string_view> const& fields)
    {
        uint32 part = 0;
        uint32 parts = 0;
        bool const partOk = fields.size() == 3 && ParsePart(fields[1], part, parts);

        // A continuation of a plan already dropped (rate limited or malformed): swallowed, one LR per plan.
        if (partOk && part > 1 && !state.planParts && state.discardParts)
        {
            --state.discardParts;
            return;
        }

        if (!partOk)
        {
            LOG_DEBUG("scripts.custom", "CTAL: malformed LEARN header from {}", player->GetGUID().ToString());
            state.ResetPlan();
            state.discardParts = 0;
            SendLearnResult(player, LEARN_RESULT_MALFORMED, 0, 0);
            return;
        }

        if (part == 1)
        {
            state.ResetPlan();
            state.discardParts = 0;
            if (state.learning || !AcceptRequest(state))
            {
                state.discardParts = parts - 1;
                SendLearnResult(player, LEARN_RESULT_BUSY, 0, 0);
                return;
            }

            state.planParts = parts;
            state.nextPart = 1;
        }

        if (!state.planParts || parts != state.planParts || part != state.nextPart ||
            !ParsePlanEntries(fields[2], state.plan))
        {
            LOG_DEBUG("scripts.custom", "CTAL: malformed or out of order LEARN part {}/{} from {}", part, parts,
                player->GetGUID().ToString());
            state.ResetPlan();
            state.discardParts = parts - part;
            SendLearnResult(player, LEARN_RESULT_MALFORMED, 0, 0);
            return;
        }

        if (part < parts)
        {
            ++state.nextPart;
            return;
        }

        std::vector<PlanEntry> plan = std::move(state.plan);
        state.ResetPlan();

        state.learning = true;
        ExecutePlan(player, plan);

        // ExecutePlan cannot log the player out, but look the state up again rather than trust the reference.
        auto itr = States.find(player->GetGUID());
        if (itr != States.end())
            itr->second.learning = false;
    }

    void HandleTalentMessage(Player* player, std::string_view body)
    {
        std::vector<std::string_view> fields = Acore::Tokenize(body, ';', true);
        if (fields.empty())
            return;

        TalentUIState& state = States[player->GetGUID()];
        std::string_view const command = fields[0];
        if (command == "HELLO")
        {
            if (!AcceptRequest(state))
                return;

            SendTalentMessage(player, BuildCfgBody(player, state.allClasses));
            SendTalentState(player);
        }
        else if (command == "GET")
        {
            if (AcceptRequest(state))
                SendTalentState(player);
        }
        else if (command == "LEARN")
            HandleLearn(player, state, fields);
        else
            LOG_DEBUG("scripts.custom", "CTAL: unknown message from {}", player->GetGUID().ToString());
    }
}

class Custom_TalentUIConfig : public WorldScript
{
public:
    Custom_TalentUIConfig() : WorldScript("Custom_TalentUIConfig", { WORLDHOOK_ON_AFTER_CONFIG_LOAD }) { }

    void OnAfterConfigLoad(bool /*reload*/) override
    {
        Settings.enabled = sConfigMgr->GetOption<bool>("Custom.TalentUI.Enable", true);
    }
};

class Custom_TalentUI : public PlayerScript
{
public:
    Custom_TalentUI() : PlayerScript("Custom_TalentUI",
        { PLAYERHOOK_CAN_PLAYER_USE_PRIVATE_CHAT, PLAYERHOOK_ON_LOGOUT }) { }

    using PlayerScript::OnPlayerCanUseChat;

    // Every whisper to self under the prefix is swallowed, whether the window is enabled or not.
    bool OnPlayerCanUseChat(Player* player, uint32 type, uint32 language, std::string& msg, Player* receiver) override
    {
        if (language != LANG_ADDON || type != CHAT_MSG_WHISPER || receiver != player ||
            msg.compare(0, TalentPrefix.size() + 1, TalentPrefix + '\t') != 0)
            return true;

        if (Settings.enabled)
            HandleTalentMessage(player, std::string_view(msg).substr(TalentPrefix.size() + 1));
        return false;
    }

    void OnPlayerLogout(Player* player) override
    {
        States.erase(player->GetGUID());
    }
};

class Custom_TalentUICommands : public CommandScript
{
public:
    Custom_TalentUICommands() : CommandScript("Custom_TalentUICommands") { }

    ChatCommandTable GetCommands() const override
    {
        static ChatCommandTable talentUITable =
        {
            { "allclasses", HandleAllClassesCommand, SEC_GAMEMASTER, Console::No }
        };

        static ChatCommandTable commandTable =
        {
            { "talentui", talentUITable }
        };

        return commandTable;
    }

    // Toggles (or sets) whether CFG lists all ten classes for the GM's own session. Not persisted; learning another
    // class's talents still fails with code 2.
    static bool HandleAllClassesCommand(ChatHandler* handler, Optional<bool> enable)
    {
        Player* player = handler->GetPlayer();
        if (!player)
            return false;

        TalentUIState& state = States[player->GetGUID()];
        state.allClasses = enable ? *enable : !state.allClasses;
        handler->PSendSysMessage("Talent window all classes: {}. Reopen the window to see the change.",
            state.allClasses ? "on" : "off");
        return true;
    }
};

void AddSC_custom_talent_ui()
{
    new Custom_TalentUIConfig();
    new Custom_TalentUI();
    new Custom_TalentUICommands();
}
