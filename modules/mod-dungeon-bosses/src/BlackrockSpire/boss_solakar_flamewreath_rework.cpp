/*
 * mod-dungeon-bosses, Blackrock Spire B11:
 * Solakar Flamewreath (10264).
 * STUB written by WP-S0 (the Blackrock Spire skeleton); WP-B11 owns this file from now on.
 * Wave 2 (Upper Blackrock Spire):
 * the AI registers only once wave 2 flips kWave2Bound / BIND_WAVE_2 (an unbound registered name
 * logs "not assigned" at boot); its `.dbtest brs` table registers now.
 *
 * What the stub does:
 * - a melee BossAI on BOSS_SOLAKAR (the instance's boss state);
 * - the flex pull (BlackrockSpireRework::OnBossPull: the held count, the scaled health, the flex loot bits, the
 *   "brs <boss> pull" line) and the registry encounter (Mechanic::BeginEncounter with bossStateId);
 * - the arena leash (SolakarArena, LeashOptions: no grips);
 * - a death log line and `.dbtest brs solakar info`.
 *
 * TODO(WP-B11):
 * - SP 3037-3110; handoff section 3.4 rows, section 3.5 row B11, section 3.6 (normal 175k,
 *   heroic 220k; the normal HealthModifier is set by the dbc-tools stub, heroic is WP-H's
 *   overrides), section 3.8 (his room; the arena below is the stub's leash frame).
 * - Wave 2 (unbound while kWave2Bound is false). BossAI on BOSS_SOLAKAR (23), which persists now. The
 *   instance's Solakar event (DATA_SOLAKAR_EVENT, stock five waves, a FAIL now resets to NOT_STARTED) is
 *   rewritten with B11 (one pair, Solakar at 30 s): a shared-file request to the orchestrator.
 * - Mechanics: SK1-SK3 the opening (Guardian 10258 Ground Stomp, Hatcher 10683 the KT-B1 chaser), SK4 Father
 *   Flame and the held flame (DATA_SOLAKAR_FLAME), SK5 / SK6 the toss and catch (PS's Pass kind; item 13371
 *   on-use toss in DT items), SK7 floor flame, SK8 Reclaim, SK9 Hunt, SK10 War Stomp, heroic SK11 Spear
 *   Wound; flame whelp 300731.
 * - Data: rebind go_father_flame to go_brs_father_flame and npc_rookery_hatcher; drop SmartAI 10683 x2,
 *   edit 10258 (Ground Stomp).
 * - Host-testable logic in SolakarLogic.h (spell ids in kSpellsSolakar), one
 *   `.dbtest brs solakar <mechanic>` subcommand per mechanic, the descriptor (Mechanic::Describe), the
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
#include "SolakarLogic.h"
#include "ScriptedCreature.h"

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;

namespace
{
    char const* const kBossLogName = "solakar";
}

struct boss_solakar_flamewreath_rework : public BossAI
{
    explicit boss_solakar_flamewreath_rework(Creature* creature)
        : BossAI(creature, BOSS_SOLAKAR),
          _arena(SolakarArena(), LeashOptions(kBossLogName)) { }

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
        options.bossStateId = BOSS_SOLAKAR;
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
        return BrsTest::ShowBossInfo(handler, NPC_SOLAKAR, BOSS_SOLAKAR);
    }

    ChatCommandTable const& SolakarTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_solakar_flamewreath_rework()
{
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_solakar_flamewreath_rework, BlackrockSpireRework::kInstanceScriptName);
    BrsTest::RegisterBoss("solakar", SolakarTestCommands());
}
