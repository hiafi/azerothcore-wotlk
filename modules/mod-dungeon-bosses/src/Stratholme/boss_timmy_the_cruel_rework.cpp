/*
 * mod-dungeon-bosses, Stratholme S3:
 * Timmy the Cruel (10808).
 * STUB written by WP-S0 (the Stratholme skeleton); WP-S3 owns this file from now on. Wave 2 (the Main Gate):
 * registered but bound to nothing until wave 2 flips kWave2Bound / BIND_WAVE_2.
 *
 * What the stub does:
 * - a melee BossAI on BOSS_TIMMY (the instance's boss state: doors, ziggurats, the save);
 * - the registry encounter (Mechanic::BeginEncounter with bossStateId);
 * - the arena leash (TimmyArena, LeashOptions: no grips);
 * - an engage / death log line and `.dbtest strat timmy info`.
 *
 * TODO(WP-S3):
 * - ST 1035-1090; handoff section 3.5 row S3, section 3.6 (normal 170k, heroic 225k; the
 *   normal HealthModifier is set by the dbc-tools stub, heroic is WP-H's overrides).
 * - Wave 2 (unbound while kWave2Bound is false).
 *   Mechanics: the games (Tag, Patty Cake claps, Guess Who playmates 300604 at kTimmyBursts, Jump Rope on X3's
 *   Jump kind), heroic two games at once, 20% claps, 4 playmates at 7k. Stock Thrash 12787, Ravenous Claw
 *   17470, Enrage 8599 kept.
 * - Data: drop SmartAI 10808 x7 + actionlist 1080800 x6; keep the gate (conditions type 29 on 10418, 10419,
 *   10420, 10424 within 70 yd), the emerge and the path in C++. The DamageModifier below is the live value;
 *   state your own.
 * - Host-testable logic in TimmyLogic.h (spell ids in kSpellsTimmy), one
 *   `.dbtest strat timmy <mechanic>` subcommand per mechanic, the descriptor (Mechanic::Describe), the
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
#include "TimmyLogic.h"
#include "ScriptedCreature.h"
#include "StratholmeKit.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"

using namespace Acore::ChatCommands;
using namespace StratholmeRework;

namespace
{
    char const* const kBossLogName = "timmy";
}

struct boss_timmy_the_cruel_rework : public BossAI
{
    explicit boss_timmy_the_cruel_rework(Creature* creature)
        : BossAI(creature, BOSS_TIMMY), _arena(TimmyArena(), LeashOptions(kBossLogName)) { }

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
        options.bossStateId = BOSS_TIMMY;
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
        return StratTest::ShowBossInfo(handler, NPC_TIMMY, BOSS_TIMMY);
    }

    ChatCommandTable const& TimmyTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_timmy_the_cruel_rework()
{
    RegisterDungeonReworkCreatureAI(boss_timmy_the_cruel_rework, StratholmeRework::kInstanceScriptName);
    StratTest::RegisterBoss("timmy", TimmyTestCommands());
}
