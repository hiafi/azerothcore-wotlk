/*
 * mod-dungeon-bosses, Blackrock Spire B14:
 * General Drakkisath (10363).
 * STUB written by WP-S0 (the Blackrock Spire skeleton); WP-B14 owns this file from now on.
 * Wave 2 (Upper Blackrock Spire):
 * the AI registers only once wave 2 flips kWave2Bound / BIND_WAVE_2 (an unbound registered name
 * logs "not assigned" at boot); its `.dbtest brs` table registers now.
 *
 * What the stub does:
 * - a melee BossAI on BOSS_DRAKKISATH (the instance's boss state);
 * - the flex pull (BlackrockSpireRework::OnBossPull: the held count, the scaled health, the flex loot bits, the
 *   "brs <boss> pull" line) and the registry encounter (Mechanic::BeginEncounter with bossStateId);
 * - the arena leash (DrakkisathArena, LeashOptions: no grips);
 * - a death log line and `.dbtest brs drakkisath info`.
 *
 * TODO(WP-B14):
 * - SP 3939-4082; handoff section 3.4 rows, section 3.5 row B14, section 3.6 (normal 260k,
 *   heroic 310k (hard mode 240k phase 2); the normal HealthModifier is set by the dbc-tools stub, heroic is WP-H's
 *   overrides), section 3.8 (his room; the arena below is the stub's leash frame).
 * - Wave 2 (unbound while kWave2Bound is false). The Elite Guards 10814 are his minions (instance minion
 *   data); his gates 175946 / 175947 are door data (passage on his DONE).
 * - Mechanics: DR1 the opening (Guards kill order), DR2 Searing Brand, DR3 Collapsing Brand, DR5
 *   Thunderclap, DR6 Flamestrike (interrupt on heroic), DR7 Blackblade Sweep (facing locked at cast start),
 *   DR9 Seared Flesh at 10 players (the TS swap at 3). Stock Rage 16789, Mortal Strike 15708 kept.
 * - B15 hooks: DrakkisathFight.h: read DATA_GENERALS_ARMY at the pull; the instance clears it when the
 *   attempt ends, records BOSS_GENERALS_ARMY on an armed kill and sets the hard mode loot bit.
 * - Host-testable logic in DrakkisathLogic.h (spell ids in kSpellsDrakkisath), one
 *   `.dbtest brs drakkisath <mechanic>` subcommand per mechanic, the descriptor (Mechanic::Describe), the
 *   registry calls of handoff section 3.4.
 * - Pilot lessons (handoff section 3.5): custom damage spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS and hit
 *   through LaunchTarget + SetEffectValue (tank hits too); every custom damage spell uses DungeonKit::RefFlat (DD
 *   never scales ids >= 200000); emotes are type 41; SaveToDB after a saved data change; no summoned unit in
 *   ObjectData; visuals and timers that must run during a cast never ride BossAI's paused scheduler; every hit has
 *   a visible impact; filled circles only for real threats; telegraph shapes match the room; arena polygons stop 2
 *   yd short of any lethal wall; a must-play cast bar uses a school the interruptible casts do not use; MissedSoak
 *   chosen per persistent Soak; one log line per firing (DungeonKit::LogMechanic(kLogDungeon, ...)).
 * - Flex: read the count once at the pull (OnBossPull, already in the stub), target counts from FlexAB pairs in the
 *   Logic header (DungeonKit::Flex::TargetCount), the taunt swap entry only when DungeonKit::Flex::TankSwapOn(n)
 *   (the user ruling: a tank taunts once its own stacks are gone; size the debuff so it falls off in time),
 *   script-set health through DungeonKit::Flex::SetHealth, the hard mode bit through SetFlexLoot at the pull.
 */

#include "ArenaGuard.h"
#include "BlackrockSpireKit.h"
#include "BlackrockSpireRework.h"
#include "BlackrockSpireTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DrakkisathLogic.h"
#include "ScriptedCreature.h"

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;

namespace
{
    char const* const kBossLogName = "drakkisath";
}

struct boss_drakkisath_rework : public BossAI
{
    explicit boss_drakkisath_rework(Creature* creature)
        : BossAI(creature, BOSS_DRAKKISATH),
          _arena(DrakkisathArena(), LeashOptions(kBossLogName)) { }

    void Reset() override
    {
        _Reset();
        _arena.Reset();
        _players = 0;
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        _players = OnBossPull(me, kBossLogName);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_DRAKKISATH;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);
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
    uint8 _players = 0;     // the flex count held at the pull (5..10)
};

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return BrsTest::ShowBossInfo(handler, NPC_DRAKKISATH, BOSS_DRAKKISATH);
    }

    ChatCommandTable const& DrakkisathTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_drakkisath_rework()
{
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_drakkisath_rework, BlackrockSpireRework::kInstanceScriptName);
    BrsTest::RegisterBoss("drakkisath", DrakkisathTestCommands());
}
