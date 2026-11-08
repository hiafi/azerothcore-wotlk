/*
 * mod-dungeon-bosses, Scholomance S4:
 * Ras Frostwhisper (10508).
 * STUB written by WP-KS (the Scholomance kit); WP-S4 owns this file from now on.
 *
 * What the stub does:
 * - a melee BossAI on BOSS_RAS (the instance's boss state: doors, Gandling's reveal, the save);
 * - the registry encounter (Mechanic::BeginEncounter with bossStateId);
 * - the arena leash (RasArena, LeashOptions: no grips);
 * - an engage / death log line and `.dbtest scholo ras info`.
 *
 * TODO(WP-S4):
 * - SC 1171-1230; handoff section 3.5 row S4, section 3.6 (normal 195k, heroic 270k; the normal HealthModifier is set
 *   by the dbc-tools stub, heroic is WP-H's overrides).
 * - Mechanics: RF1 Chill, RF2 Warmth, RF3 Entombed, RF4 Thaw, RF5 Frost Mark, RF6 Blizzard, RF7 Frostbolt Volley, RF8
 *   Frost Armor (stock 18100).
 * - Data: drop SmartAI 10508 x5 (keep the quest Boon of Life: the stock spell_scholomance_boon_of_life_aura stays
 *   registered and drives the human form through AI()->Talk(0) and DATA_RAS_HUMAN); creature_text per
 *   ScholomanceRework.h's text enum (your SQL rev); your own DamageModifier (the live value is a mod-progression
 *   leftover, handoff section 2.3).
 * - Adds: Blizzard anchor 300534 (invisible; heroic drifts 1.5 yd/s). Patrol path 488500 stays out of combat
 *   (kRasPatrolPathId).
 * - Heroic: warm build 1 per 3 s, drifting Blizzards, the Volley adds Chill.
 * - S12 (the Torn Keepsake) fights on this AI: leave a hook for the hard mode (phase 2, the permanent tomb;
 *   GetData(DATA_RAS_HARD_MODE)); the loot bit is the instance's.
 * - Arena: RasArena() with LeashOptions (no grips; hold at the edge, evade after 10 s with nobody inside). Tighten it
 *   in your own file if the room needs it.
 * - Host-testable logic in RasLogic.h (spell ids in kSpellsRas), one `.dbtest scholo ras <mechanic>` subcommand per
 *   mechanic, the descriptor (Mechanic::Describe), the registry calls of handoff section 3.4.
 * - Pilot lessons (handoff section 2.2): custom damage spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS and hit through
 *   LaunchTarget + SetEffectValue (tank hits too, so defensives work); every custom damage spell uses
 *   DungeonKit::RefFlat (DD never scales ids >= 200000); emotes are type 41; SaveToDB after a saved data change; no
 *   summoned unit in ObjectData; visuals and timers that must run during a cast never ride BossAI's paused scheduler;
 *   every hit has a visible impact; filled circles only for real threats (a range cue is an outline, NoFillTimer);
 *   telegraph shapes match the room; one log category module.dungeonbosses (DungeonKit::LogMechanic(kLogDungeon, ...)).
 */

#include "ArenaGuard.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "RasLogic.h"
#include "ScholomanceRework.h"
#include "ScholomanceKit.h"
#include "ScholomanceTestCommand.h"
#include "ScriptedCreature.h"
#include "StringFormat.h"

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;

namespace
{
    char const* const kBossLogName = "ras";
}

struct boss_ras_frostwhisper_rework : public BossAI
{
    explicit boss_ras_frostwhisper_rework(Creature* creature)
        : BossAI(creature, BOSS_RAS), _arena(RasArena(), LeashOptions(kBossLogName)) { }

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
        options.bossStateId = BOSS_RAS;
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
        return ScholoTest::ShowBossInfo(handler, NPC_RAS, BOSS_RAS);
    }

    ChatCommandTable const& RasTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_ras_frostwhisper_rework()
{
    RegisterDungeonReworkCreatureAI(boss_ras_frostwhisper_rework, ScholomanceRework::kInstanceScriptName);
    ScholoTest::RegisterBoss("ras", RasTestCommands());
}
