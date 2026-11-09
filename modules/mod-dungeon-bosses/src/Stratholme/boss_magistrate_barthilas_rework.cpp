/*
 * mod-dungeon-bosses, Stratholme S9:
 * Magistrate Barthilas (10435).
 * STUB written by WP-S0 (the Stratholme skeleton); WP-S9 owns this file from now on. Wave 1 (the Service Entrance).
 *
 * What the stub does:
 * - a melee BossAI on BOSS_BARTHILAS (the instance's boss state: doors, ziggurats, the save);
 * - the registry encounter (Mechanic::BeginEncounter with bossStateId);
 * - the arena leash (BarthilasArena, LeashOptions: no grips);
 * - an engage / death log line and `.dbtest strat barthilas info`.
 *
 * TODO(WP-S9):
 * - ST 2355-2407; handoff section 3.5 row S9, section 3.6 (normal 180k, heroic 235k; the
 *   normal HealthModifier is set by the dbc-tools stub, heroic is WP-H's overrides).
 * - Mechanics: BT1 the cough (RunOut from every carrier, the tank included), BT3 Quarantine Stacks by the
 *   Infected aura, BT4 grain piles, BT5 cough puddles, BT6 the wards (the ward line from the floor,
 *   PickFloorSpot; kBarthilasWardAnchor 12 yd west fits every bearing, at his spawn only north-south), BT7
 *   Fever, heroic BT8 two patients and BT9 Bedlam, BT11 the stock tank kit (Mighty Blow 14099, Draining Blow
 *   16793). Section 7 #17: the heroic cough is Weakened too. Route avoidance of carriers is X1's.
 * - Data: drop SmartAI 10435 x19 (the run, the path, Furious Anger, Crowd Pummel go); keep the
 *   Transformation 16794 look (on spawn and death) in C++. His portcullises 175377 / 175372 are the
 *   instance's door data on BOSS_BARTHILAS (closed while he fights): do not move them into this file. The
 *   Service Entrance Gate is open from the start (the instance); the Key to the City stays. Drop the GO
 *   175368 SmartAI row (type 1, the run). Texts per StratholmeRework.h BarthilasTexts (group 0 stock, now on
 *   aggro). Kit units: grain pile / cough puddle 300580, ward 300581.
 * - Host-testable logic in BarthilasLogic.h (spell ids in kSpellsBarthilas), one
 *   `.dbtest strat barthilas <mechanic>` subcommand per mechanic, the descriptor (Mechanic::Describe), the
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
#include "BarthilasLogic.h"
#include "ScriptedCreature.h"
#include "StratholmeKit.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"

using namespace Acore::ChatCommands;
using namespace StratholmeRework;

namespace
{
    char const* const kBossLogName = "barthilas";
}

struct boss_magistrate_barthilas_rework : public BossAI
{
    explicit boss_magistrate_barthilas_rework(Creature* creature)
        : BossAI(creature, BOSS_BARTHILAS), _arena(BarthilasArena(), LeashOptions(kBossLogName)) { }

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
        options.bossStateId = BOSS_BARTHILAS;
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
        return StratTest::ShowBossInfo(handler, NPC_BARTHILAS, BOSS_BARTHILAS);
    }

    ChatCommandTable const& BarthilasTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_magistrate_barthilas_rework()
{
    RegisterDungeonReworkCreatureAI(boss_magistrate_barthilas_rework, StratholmeRework::kInstanceScriptName);
    StratTest::RegisterBoss("barthilas", BarthilasTestCommands());
}
