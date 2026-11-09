/*
 * mod-dungeon-bosses, Stratholme S14:
 * Baron Rivendare (10440).
 * STUB written by WP-S0 (the Stratholme skeleton); WP-S14 owns this file from now on. Wave 1 (the Service Entrance).
 *
 * What the stub does:
 * - a melee BossAI on BOSS_BARON (the instance's boss state: doors, ziggurats, the save);
 * - the registry encounter (Mechanic::BeginEncounter with bossStateId);
 * - the arena leash (BaronArena, LeashOptions: no grips);
 * - an engage / death log line and `.dbtest strat baron info`.
 *
 * TODO(WP-S14):
 * - ST 3842-3906; handoff section 3.5 row S14, section 3.6 (normal 250k, heroic 300k; the
 *   normal HealthModifier is set by the dbc-tools stub, heroic is WP-H's overrides).
 * - Mechanics: BR1 Raise Dead (3 Mindless Skeletons 11197 at 6k per wave at kRaiseDeadPoints, alternating
 *   north and south; 6 alive at most on normal, no cap on heroic), BR2 bone piles (GO 301207, displays
 *   6328 / 6329), BR3 Death and Decay (FollowThenLand, X2's drop spot with the piles as avoid points; rot
 *   stalker 300588), BR4 Unholy Aura (a 100 yd copy of 17467), BR5 the stock tank kit (Shadow Bolt 17393,
 *   Mortal Strike 15708, Cleave 15284 at its live 10%). Death Pact 17471 and Raise Dead 17473 / 17475-17480
 *   retired. Casts never overlap (CastQueue).
 * - S15 hooks: BaronFight.h (the Scholomance RasFight.h pattern): read DATA_ULTIMATUM at the pull (yell 11,
 *   mounted display 10718, 500k by script, back to heroic on reset). The instance clears the flag on his
 *   death, records BOSS_ULTIMATUM, sets the loot bit while it is lit and opens the exit gate 176424 when
 *   Ysida is dead.
 * - Data: drop SmartAI 10440 x20, 11197 x3. Immunity: the stock -419 stays (section 7 #3). His door 175796
 *   is the instance's (closed while BOSS_BARON is IN_PROGRESS, open once the Black Guards died). The stock
 *   leash (21 yd from 175405, 4 yd from his door) is yours. Texts per BaronTexts (0-8 stock, 9-15 new).
 * - Host-testable logic in BaronLogic.h (spell ids in kSpellsBaron), one
 *   `.dbtest strat baron <mechanic>` subcommand per mechanic, the descriptor (Mechanic::Describe), the
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
#include "BaronLogic.h"
#include "ScriptedCreature.h"
#include "StratholmeKit.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"

using namespace Acore::ChatCommands;
using namespace StratholmeRework;

namespace
{
    char const* const kBossLogName = "baron";
}

struct boss_baron_rivendare_rework : public BossAI
{
    explicit boss_baron_rivendare_rework(Creature* creature)
        : BossAI(creature, BOSS_BARON), _arena(BaronArena(), LeashOptions(kBossLogName)) { }

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
        options.bossStateId = BOSS_BARON;
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
        return StratTest::ShowBossInfo(handler, NPC_BARON, BOSS_BARON);
    }

    ChatCommandTable const& BaronTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_baron_rivendare_rework()
{
    RegisterDungeonReworkCreatureAI(boss_baron_rivendare_rework, StratholmeRework::kInstanceScriptName);
    StratTest::RegisterBoss("baron", BaronTestCommands());
}
