/*
 * mod-dungeon-bosses, Stratholme S5:
 * Cannon Master Willey (10997).
 * STUB written by WP-S0 (the Stratholme skeleton); WP-S5 owns this file from now on. Wave 2 (the Main Gate):
 * registered but bound to nothing until wave 2 flips kWave2Bound / BIND_WAVE_2.
 *
 * What the stub does:
 * - a melee BossAI on BOSS_WILLEY (the instance's boss state: doors, ziggurats, the save);
 * - the registry encounter (Mechanic::BeginEncounter with bossStateId);
 * - the arena leash (WilleyArena, LeashOptions: no grips);
 * - an engage / death log line and `.dbtest strat willey info`.
 *
 * TODO(WP-S5):
 * - ST 1444-1502; handoff section 3.5 row S5, section 3.6 (normal 185k, heroic 230k; the
 *   normal HealthModifier is set by the dbc-tools stub, heroic is WP-H's overrides).
 * - Wave 2 (unbound while kWave2Bound is false).
 *   Mechanics: the riflemen ranks (11054 at 5k, 7k heroic; kWilleyRank3 / kWilleyRank4 at X 52 of
 *   kWilleyHall), Mercy (301200, east half) and Zeal (301201, west half) on the hall's halves, the dropped
 *   cannonball (301202, GO display 153; Pickups), heroic ranks of 4, the Barrage (five hidden lines on the
 *   halves, NoTelegraph, the order in a built boss emote; the drill row at t 25), 20% volleys. Stock Knock
 *   Away 10101, Pummel 15615, Shoot 17353 kept.
 * - Data: drop SmartAI 10997 x7, 11054 x4; the stock cannons 176216 / 176217 and the 5 Cannonball Stacks
 *   176215 go in the fight (spawn rows replaced by Mercy and Zeal). The DamageModifier below is the live
 *   value; state your own.
 * - Host-testable logic in WilleyLogic.h (spell ids in kSpellsWilley), one
 *   `.dbtest strat willey <mechanic>` subcommand per mechanic, the descriptor (Mechanic::Describe), the
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
#include "WilleyLogic.h"
#include "ScriptedCreature.h"
#include "StratholmeKit.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"

using namespace Acore::ChatCommands;
using namespace StratholmeRework;

namespace
{
    char const* const kBossLogName = "willey";
}

struct boss_cannon_master_willey_rework : public BossAI
{
    explicit boss_cannon_master_willey_rework(Creature* creature)
        : BossAI(creature, BOSS_WILLEY), _arena(WilleyArena(), LeashOptions(kBossLogName)) { }

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
        options.bossStateId = BOSS_WILLEY;
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
        return StratTest::ShowBossInfo(handler, NPC_WILLEY, BOSS_WILLEY);
    }

    ChatCommandTable const& WilleyTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_cannon_master_willey_rework()
{
    RegisterDungeonReworkCreatureAI(boss_cannon_master_willey_rework, StratholmeRework::kInstanceScriptName);
    StratTest::RegisterBoss("willey", WilleyTestCommands());
}
