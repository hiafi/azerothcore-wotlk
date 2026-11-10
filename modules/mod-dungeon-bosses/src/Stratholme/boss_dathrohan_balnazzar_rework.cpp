/*
 * mod-dungeon-bosses, Stratholme S7:
 * Grand Crusader Dathrohan and Balnazzar (10812, 10813).
 * STUB written by WP-S0 (the Stratholme skeleton); WP-S7 owns this file from now on. Wave 2 (the Main Gate):
 * registered but bound to nothing until wave 2 flips kWave2Bound / BIND_WAVE_2.
 *
 * What the stub does:
 * - a melee BossAI on BOSS_BALNAZZAR (the instance's boss state: doors, ziggurats, the save);
 * - the registry encounter (Mechanic::BeginEncounter with bossStateId);
 * - the arena leash (DathrohanArena, LeashOptions: no grips);
 * - an engage / death log line and `.dbtest strat balnazzar info`.
 *
 * TODO(WP-S7):
 * - ST 2077-2166; handoff section 3.5 row S7, section 3.6 (normal 250k / 220k, heroic 340k / 300k; the
 *   normal HealthModifier is set by the dbc-tools stub, heroic is WP-H's overrides).
 * - Wave 2 (unbound while kWave2Bound is false). One script on both entries: Dathrohan 10812, then
 *   Balnazzar 10813 after the transform (UpdateEntry; the script talks with the new entry's groups,
 *   section 7 #14). Balnazzar's own columns: HealthModifier 84.942 (220k) on the same base.
 *   Mechanics: DB1 the true and lying calls (Decoy() markers), DB2 the Judgments (split shares), the half-room
 *   cleave on kDathrohanHalves, Carrion Swarm, the meteor, Infernals 300608 (12k, 18k heroic), Sleep (an
 *   interrupt and a dispel on heroic), heroic two cones (the drill row at t 20), drifting timers.
 * - S8 hooks (the Grand Lie): a hard mode start out of combat on the Letter (DATA_GRAND_LIE, read at the
 *   pull: 600k by script, act 1). The instance records BOSS_GRAND_LIE and the loot bit.
 * - Data: drop SmartAI 10812 x18; the death skeletons (summon group) stay. The DamageModifier below is the
 *   live value; state your own (Balnazzar's live value is 9).
 * - Host-testable logic in DathrohanLogic.h (spell ids in kSpellsDathrohan), one
 *   `.dbtest strat balnazzar <mechanic>` subcommand per mechanic, the descriptor (Mechanic::Describe), the
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
#include "DathrohanLogic.h"
#include "ScriptedCreature.h"
#include "StratholmeKit.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"

using namespace Acore::ChatCommands;
using namespace StratholmeRework;

namespace
{
    char const* const kBossLogName = "balnazzar";
}

struct boss_dathrohan_balnazzar_rework : public BossAI
{
    explicit boss_dathrohan_balnazzar_rework(Creature* creature)
        : BossAI(creature, BOSS_BALNAZZAR), _arena(DathrohanArena(), LeashOptions(kBossLogName)) { }

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
        options.bossStateId = BOSS_BALNAZZAR;
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
        return StratTest::ShowBossInfo(handler, NPC_DATHROHAN, BOSS_BALNAZZAR);
    }

    ChatCommandTable const& DathrohanTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_dathrohan_balnazzar_rework()
{
    RegisterDungeonReworkCreatureAI(boss_dathrohan_balnazzar_rework, StratholmeRework::kInstanceScriptName);
    StratTest::RegisterBoss("balnazzar", DathrohanTestCommands());
}
