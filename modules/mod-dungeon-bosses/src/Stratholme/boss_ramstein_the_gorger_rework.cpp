/*
 * mod-dungeon-bosses, Stratholme S13:
 * Ramstein the Gorger (10439).
 * STUB written by WP-S0 (the Stratholme skeleton); WP-S13 owns this file from now on. Wave 1 (the Service Entrance).
 *
 * What the stub does:
 * - a melee BossAI on BOSS_RAMSTEIN (the instance's boss state: doors, ziggurats, the save);
 * - the registry encounter (Mechanic::BeginEncounter with bossStateId);
 * - the arena leash (RamsteinArena, LeashOptions: no grips);
 * - an engage / death log line and `.dbtest strat ramstein info`.
 *
 * TODO(WP-S13):
 * - ST 3432-3483; handoff section 3.5 row S13, section 3.6 (normal 210k, heroic 230k; the
 *   normal HealthModifier is set by the dbc-tools stub, heroic is WP-H's overrides).
 * - He is summoned by the instance's slaughter event at kRamsteinSummon (stock SlaughterPos) once the
 *   abominations die; his death goes straight to the Black Guards (the instance: no Mindless Undead stage,
 *   ST 3395-3400; 20 s, then the Baron's door). Take over his stock walk-in (actionlist 1043900: home
 *   position kRamsteinStop, door 175405, line 0, attack start).
 *   Mechanics: RG1 the meat (Mindless Undead 11030 at 4k, summoned by this script at kMindlessUndeadSpawn
 *   along the 91 yd straight path; capped at 33 on normal, uncapped heroic waves of 5; the instance never
 *   counts them), RG2 Gorge, RG3 the gut puddle (300587, SV 90342 / 90343), crawlers (Half-Digested Corpse
 *   300586), heroic Cannibalize, crawlers walk back. Stock Knockout 15088 per the build spec. Open the side
 *   gate 175358 at the first meat wave (the instance opens it again on his death).
 * - Data: drop SmartAI 10439 x4 + actionlist 1043900 x8, 11030 x1. Immunity 1972 (stun; ST asked -273,
 *   section 8 #5). Texts per RamsteinTexts (group 0 stock). Keep him out of his 5-6 yd passage (scale 4.4-5
 *   at 8-10 Gorged stacks).
 * - Host-testable logic in RamsteinLogic.h (spell ids in kSpellsRamstein), one
 *   `.dbtest strat ramstein <mechanic>` subcommand per mechanic, the descriptor (Mechanic::Describe), the
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
#include "RamsteinLogic.h"
#include "ScriptedCreature.h"
#include "StratholmeKit.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"

using namespace Acore::ChatCommands;
using namespace StratholmeRework;

namespace
{
    char const* const kBossLogName = "ramstein";
}

struct boss_ramstein_the_gorger_rework : public BossAI
{
    explicit boss_ramstein_the_gorger_rework(Creature* creature)
        : BossAI(creature, BOSS_RAMSTEIN), _arena(RamsteinArena(), LeashOptions(kBossLogName)) { }

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
        options.bossStateId = BOSS_RAMSTEIN;
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
        return StratTest::ShowBossInfo(handler, NPC_RAMSTEIN, BOSS_RAMSTEIN);
    }

    ChatCommandTable const& RamsteinTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_ramstein_the_gorger_rework()
{
    RegisterDungeonReworkCreatureAI(boss_ramstein_the_gorger_rework, StratholmeRework::kInstanceScriptName);
    StratTest::RegisterBoss("ramstein", RamsteinTestCommands());
}
