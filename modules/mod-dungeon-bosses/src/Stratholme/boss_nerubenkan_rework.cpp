/*
 * mod-dungeon-bosses, Stratholme S11:
 * Nerub'enkan (10437).
 * STUB written by WP-S0 (the Stratholme skeleton); WP-S11 owns this file from now on. Wave 1 (the Service Entrance).
 *
 * What the stub does:
 * - a melee BossAI on BOSS_NERUBENKAN (the instance's boss state: doors, ziggurats, the save);
 * - the registry encounter (Mechanic::BeginEncounter with bossStateId);
 * - the arena leash (NerubenkanArena, LeashOptions: no grips);
 * - an engage / death log line and `.dbtest strat nerubenkan info`.
 *
 * TODO(WP-S11):
 * - ST 2859-2911; handoff section 3.5 row S11, section 3.6 (normal 170k, heroic 200k; the
 *   normal HealthModifier is set by the dbc-tools stub, heroic is WP-H's overrides).
 * - Mechanics: NE1 the web spit (FollowThenLand, the drop spot rule X2 onto an existing patch), the web
 *   patches (PuddleField with the merge rule, the farthest patch within 30 yd), NE4 Web Cocoon (HoldInUnit),
 *   NE6 Skitter (JumpTo), the scarabs 10876 at 2k (Poison Proc 13299 kept), heroic NE7 Brood Call, 7 yd
 *   webs, 12k cocoon at 6 s. Stock Encasing Webs 6016 per the build spec.
 * - Data: drop SmartAI 10437 x5 and 10876's out-of-combat attack row (keep Poison Proc's reset cast in C++
 *   or keep row 0). Texts per NerubenkanTexts (none stock). Kit units: Web Cocoon 300582 (display 16213),
 *   web patch 300583. His ziggurat (DATA_ZIGGURAT2) opens on his death by the instance.
 * - Host-testable logic in NerubenkanLogic.h (spell ids in kSpellsNerubenkan), one
 *   `.dbtest strat nerubenkan <mechanic>` subcommand per mechanic, the descriptor (Mechanic::Describe), the
 *   registry calls of handoff section 3.4.
 * - Pilot lessons (handoff section 3.5): custom damage spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS and hit
 *   through LaunchTarget + SetEffectValue (tank hits too); every custom damage spell uses DungeonKit::RefFlat
 *   (DD never scales ids >= 200000); emotes are type 41; SaveToDB after a saved data change; no summoned unit in
 *   ObjectData; visuals and timers that must run during a cast never ride BossAI's paused scheduler; every hit
 *   has a visible impact; filled circles only for real threats; telegraph shapes match the room; spells that
 *   must clear on leaving carry CHANGE_MAP interrupt flags; one log category (DungeonKit::LogMechanic(
 *   kLogDungeon, ...)).
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "NerubenkanLogic.h"
#include "ScriptedCreature.h"
#include "StratholmeKit.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"

using namespace Acore::ChatCommands;
using namespace StratholmeRework;

namespace
{
    char const* const kBossLogName = "nerubenkan";
}

struct boss_nerubenkan_rework : public BossAI
{
    explicit boss_nerubenkan_rework(Creature* creature)
        : BossAI(creature, BOSS_NERUBENKAN), _arena(NerubenkanArena(), LeashOptions(kBossLogName)) { }

    void Reset() override
    {
        _Reset();
        _arena.Reset();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_NERUBENKAN;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f})", DungeonKit::IsHeroicMap(me) ? 1 : 0,
                me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        _arena.Reset();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        _arena.Reset();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death");
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        events.Update(diff);
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

private:
    DungeonKit::ArenaGuard _arena;
};

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return StratTest::ShowBossInfo(handler, NPC_NERUBENKAN, BOSS_NERUBENKAN);
    }

    ChatCommandTable const& NerubenkanTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_nerubenkan_rework()
{
    RegisterDungeonReworkCreatureAI(boss_nerubenkan_rework, StratholmeRework::kInstanceScriptName);
    StratTest::RegisterBoss("nerubenkan", NerubenkanTestCommands());
}
