/*
 * mod-dungeon-bosses, Stratholme S10:
 * Baroness Anastari (10436).
 * STUB written by WP-S0 (the Stratholme skeleton); WP-S10 owns this file from now on. Wave 1 (the Service Entrance).
 *
 * What the stub does:
 * - a melee BossAI on BOSS_BARONESS (the instance's boss state: doors, ziggurats, the save);
 * - the registry encounter (Mechanic::BeginEncounter with bossStateId);
 * - the arena leash (BaronessArena, LeashOptions: no grips);
 * - an engage / death log line and `.dbtest strat baroness info`.
 *
 * TODO(WP-S10):
 * - ST 2630-2677; handoff section 3.5 row S10, section 3.6 (normal 170k, heroic 220k; the
 *   normal HealthModifier is set by the dbc-tools stub, heroic is WP-H's overrides).
 * - Mechanics: BA1 the Keening (the isolation pick), BA4 Banshee Wail ring then the 8 / 60 donut (the
 *   stratholme-followups drill row at t 13 gates her heroic sign-off), BA5, BA6 the Veil, Death Knell (the
 *   stack-weighted split, KT-1), heroic BA7 Lament, the Wail echo, two Visage cones, the 5 s keen, 100% Knell.
 *   Stock Banshee Wail 16565 kept (DD scales it on heroic).
 * - Data: the stock C++ boss_baroness_anastari stays registered and is unbound by data (no SQL needed for
 *   it). Texts per BaronessTexts (none stock). Her ziggurat (DATA_ZIGGURAT1) opens on her death by the
 *   instance (boss state DONE): no SetData here.
 * - Host-testable logic in BaronessLogic.h (spell ids in kSpellsBaroness), one
 *   `.dbtest strat baroness <mechanic>` subcommand per mechanic, the descriptor (Mechanic::Describe), the
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
#include "BaronessLogic.h"
#include "ScriptedCreature.h"
#include "StratholmeKit.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"

using namespace Acore::ChatCommands;
using namespace StratholmeRework;

namespace
{
    char const* const kBossLogName = "baroness";
}

struct boss_baroness_anastari_rework : public BossAI
{
    explicit boss_baroness_anastari_rework(Creature* creature)
        : BossAI(creature, BOSS_BARONESS), _arena(BaronessArena(), LeashOptions(kBossLogName)) { }

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
        options.bossStateId = BOSS_BARONESS;
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
        return StratTest::ShowBossInfo(handler, NPC_BARONESS, BOSS_BARONESS);
    }

    ChatCommandTable const& BaronessTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_baroness_anastari_rework()
{
    RegisterDungeonReworkCreatureAI(boss_baroness_anastari_rework, StratholmeRework::kInstanceScriptName);
    StratTest::RegisterBoss("baroness", BaronessTestCommands());
}
