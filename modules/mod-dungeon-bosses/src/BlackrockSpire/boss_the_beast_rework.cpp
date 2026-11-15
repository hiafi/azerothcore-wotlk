/*
 * mod-dungeon-bosses, Blackrock Spire B13:
 * The Beast (10430).
 * STUB written by WP-S0 (the Blackrock Spire skeleton); WP-B13 owns this file from now on.
 * Wave 2 (Upper Blackrock Spire):
 * the AI registers only once wave 2 flips kWave2Bound / BIND_WAVE_2 (an unbound registered name
 * logs "not assigned" at boot); its `.dbtest brs` table registers now.
 *
 * What the stub does:
 * - a melee BossAI on BOSS_BEAST (the instance's boss state);
 * - the flex pull (BlackrockSpireRework::OnBossPull: the held count, the scaled health, the flex loot bits, the
 *   "brs <boss> pull" line) and the registry encounter (Mechanic::BeginEncounter with bossStateId);
 * - the arena leash (BeastArena, LeashOptions: no grips);
 * - a death log line and `.dbtest brs beast info`.
 *
 * TODO(WP-B13):
 * - SP 3635-3697; handoff section 3.4 rows, section 3.5 row B13, section 3.6 (normal 220k,
 *   heroic 235k; the normal HealthModifier is set by the dbc-tools stub, heroic is WP-H's
 *   overrides), section 3.8 (his room; the arena below is the stub's leash frame).
 * - Wave 2 (unbound while kWave2Bound is false). Keep the stock protocols: area triggers 2066 / 2067 call his
 *   AI's SetData(1 | 2) through GetGuidData(BOSS_BEAST); the instance's skinning hook (Finkle) stays.
 * - Mechanics: BE2 Heat, BE3 Molten Blood pools (300735, PickFloorSpot), BE4 Molten Fury, BE5 Dread, BE6
 *   Magma Split, BE7 Eruption, BE8 Immolate (dispel). Stock Immolate 15570, Fire Blast 16144 kept.
 * - Host-testable logic in BeastLogic.h (spell ids in kSpellsBeast), one
 *   `.dbtest brs beast <mechanic>` subcommand per mechanic, the descriptor (Mechanic::Describe), the
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
#include "BeastLogic.h"
#include "ScriptedCreature.h"

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;

namespace
{
    char const* const kBossLogName = "beast";
}

struct boss_the_beast_rework : public BossAI
{
    explicit boss_the_beast_rework(Creature* creature)
        : BossAI(creature, BOSS_BEAST),
          _arena(BeastArena(), LeashOptions(kBossLogName)) { }

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
        options.bossStateId = BOSS_BEAST;
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
        return BrsTest::ShowBossInfo(handler, NPC_BEAST, BOSS_BEAST);
    }

    ChatCommandTable const& BeastTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_the_beast_rework()
{
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_the_beast_rework, BlackrockSpireRework::kInstanceScriptName);
    BrsTest::RegisterBoss("beast", BeastTestCommands());
}
