/*
 * mod-dungeon-bosses, Stratholme S1:
 * The Unforgiven (10516).
 * STUB written by WP-S0 (the Stratholme skeleton); WP-S1 owns this file from now on. Wave 2 (the Main Gate):
 * registered but bound to nothing until wave 2 flips kWave2Bound / BIND_WAVE_2.
 *
 * What the stub does:
 * - a melee BossAI on BOSS_UNFORGIVEN (the instance's boss state: doors, ziggurats, the save);
 * - the registry encounter (Mechanic::BeginEncounter with bossStateId);
 * - the arena leash (UnforgivenArena, LeashOptions: no grips);
 * - an engage / death log line and `.dbtest strat unforgiven info`.
 *
 * TODO(WP-S1):
 * - ST 616-676; handoff section 3.5 row S1, section 3.6 (normal 185k, heroic 250k; the
 *   normal HealthModifier is set by the dbc-tools stub, heroic is WP-H's overrides).
 * - Wave 2 (unbound while kWave2Bound is false: his stock SmartAI runs, the instance sets his state on death).
 *   Mechanics: the marching ranks on the two lanes (kUnforgivenLaneMarketRow, kUnforgivenLanePassage; the
 *   heroic crossing rank 1.5 s after the first, the stratholme-followups drill row at t 0), the Cordon
 *   (KT-2 LethalWall on X4's .Lethal(); the pull grip arms the walls 2 s later, section 10), house fires
 *   (300601, kUnforgivenFireSpots), the Accused, Freed in the Light, phantoms 10387 (6k, 9k heroic), the
 *   Last Soul. Footman 300600 (display 30978, unattackable).
 * - Data: drop SmartAI 10516 x8, 10387 x1. Arena: the plaza polygon closed by two cordons; the pull grip on
 *   top of LeashOptions (gripOnPull, landing inside the plaza). The DamageModifier below is the live value
 *   (no sniff row); state your own.
 * - Host-testable logic in UnforgivenLogic.h (spell ids in kSpellsUnforgiven), one
 *   `.dbtest strat unforgiven <mechanic>` subcommand per mechanic, the descriptor (Mechanic::Describe), the
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
#include "UnforgivenLogic.h"
#include "ScriptedCreature.h"
#include "StratholmeKit.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"

using namespace Acore::ChatCommands;
using namespace StratholmeRework;

namespace
{
    char const* const kBossLogName = "unforgiven";
}

struct boss_the_unforgiven_rework : public BossAI
{
    explicit boss_the_unforgiven_rework(Creature* creature)
        : BossAI(creature, BOSS_UNFORGIVEN), _arena(UnforgivenArena(), LeashOptions(kBossLogName)) { }

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
        options.bossStateId = BOSS_UNFORGIVEN;
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
        return StratTest::ShowBossInfo(handler, NPC_UNFORGIVEN, BOSS_UNFORGIVEN);
    }

    ChatCommandTable const& UnforgivenTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_the_unforgiven_rework()
{
    RegisterDungeonReworkCreatureAI(boss_the_unforgiven_rework, StratholmeRework::kInstanceScriptName);
    StratTest::RegisterBoss("unforgiven", UnforgivenTestCommands());
}
