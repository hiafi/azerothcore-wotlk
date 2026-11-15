/*
 * mod-dungeon-bosses, Blackrock Spire B12:
 * Warchief Rend Blackhand (10429).
 * STUB written by WP-S0 (the Blackrock Spire skeleton); WP-B12 owns this file from now on.
 * Wave 2 (Upper Blackrock Spire):
 * the AI registers only once wave 2 flips kWave2Bound / BIND_WAVE_2 (an unbound registered name
 * logs "not assigned" at boot); its `.dbtest brs` table registers now.
 *
 * What the stub does:
 * - a melee BossAI on BOSS_REND (the instance's boss state);
 * - the flex pull (BlackrockSpireRework::OnBossPull: the held count, the scaled health, the flex loot bits, the
 *   "brs <boss> pull" line) and the registry encounter (Mechanic::BeginEncounter with bossStateId);
 * - the arena leash (RendGythArena, LeashOptions: no grips);
 * - a death log line and `.dbtest brs rend info`.
 *
 * TODO(WP-B12):
 * - SP 3349-3463; handoff section 3.4 rows, section 3.5 row B12, section 3.6 (normal 160k (Gyth 140k),
 *   heroic 210k (Gyth 200k); the normal HealthModifier is set by the dbc-tools stub, heroic is WP-H's
 *   overrides), section 3.8 (his room; the arena below is the stub's leash frame).
 * - Wave 2 (unbound while kWave2Bound is false). Keep the stock protocols: at_blackrock_stadium (2026)
 *   respawns a dead Rend while BOSS_REND is NOT_STARTED and calls his AI's SetData(1, 2026); the instance
 *   respawns him on a FAIL and has Nefarius say line 11; GetGuidData(BOSS_REND / BOSS_GYTH).
 * - Mechanics: RG1 act 1 and RG13 Handlers (through 175185), RG4 rounds, RG5 Dress Hunt (whelps the KT-B1
 *   chaser), RG6 Freezing Sweep (RF's rolling line; drill t 24 gates the heroic sign-off), RG7, heroic RG8
 *   Thumbs Down, RG9 Rend's Mark, RG10, RG11 Whirlwind, RG12 Banner 300733, RG16 / RG17 the taunt swaps at
 *   10. Nefarius's BRS copy 300732 (spawn 137967 rebound; BWL's 10162 untouched) with texts 0-19 and the
 *   insult (ReceiveEmote 77, 113, 89, 22 -> SetData(DATA_NEF_INSULTED, 1)). Gyth is boss_gyth_rework.
 * - Host-testable logic in RendGythLogic.h (spell ids in kSpellsRendGyth), one
 *   `.dbtest brs rend <mechanic>` subcommand per mechanic, the descriptor (Mechanic::Describe), the
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
#include "RendGythLogic.h"
#include "ScriptedCreature.h"

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;

namespace
{
    char const* const kBossLogName = "rend";
}

struct boss_rend_blackhand_rework : public BossAI
{
    explicit boss_rend_blackhand_rework(Creature* creature)
        : BossAI(creature, BOSS_REND),
          _arena(RendGythArena(), LeashOptions(kBossLogName)) { }

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
        options.bossStateId = BOSS_REND;
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
        return BrsTest::ShowBossInfo(handler, NPC_REND, BOSS_REND);
    }

    ChatCommandTable const& RendGythTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_rend_blackhand_rework()
{
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_rend_blackhand_rework, BlackrockSpireRework::kInstanceScriptName);
    BrsTest::RegisterBoss("rend", RendGythTestCommands());
}
