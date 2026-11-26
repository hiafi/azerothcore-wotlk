/*
 * mod-dungeon-bosses, Zul'Farrak D4b:
 * boss_sezzziz_rework (7275), boss_nekrum_rework (7796).
 * STUB written by WP-S0 (the Zul'Farrak skeleton); WP-D4b owns this file from now on. Bound by the DT file and the S0
 * rev.
 *
 * What the stub does: a melee placeholder for each unit (the pull line OnBossPull, the arena leash with LeashOptions:
 * no grips, ZulFarrak::NoAssist every tick), a death log line.
 *
 * TODO(WP-D4b):
 * - SP 1101-1432 (Build spec 1346; PY12-PY15); handoff section 3.5 row D4b, sections 3.6, 3.8, 3.10, 3.12; the kick and
 *   dispel table. Health and every room point and arena are in ZulFarrakRework.h.
 * - They are stage 3 of the Pyramid (the Altar), summoned by the stage 3 director (pyramid_stair_rework.cpp) from
 *   kWaveSpawns; not BossAIs: the instance writes slot 5 and wins the stage when both are dead. The stubs send
 *   SetData(DATA_PYRAMID_START, 3) at their pull (the restart after a wipe; refused while it runs).
 * - Mechanics: PY12 Blood Offering (through CR's BlyCrew.h on a crew member, else a player), PY13 Psychic Scream, PY14
 *   the adds at kSezzzizAddPoints (capped at 4), PY15; Nekrum's Gutchew (heroic). DamageModifier 2.4 / 3.0 (section 7
 *   #44 A) is in pyramid_stair.py already.
 * - Add scripts (registered here by WP-D4b, in the change that declares the creature): none here (the specialists are
 *   pyramid_stair_rework.cpp's).
 * - Host-testable logic in SezzzizLogic.h (spell ids in kSpellsStair, 213990-214029 (shared with
 *   pyramid_stair_rework.cpp)), tests/zf_stair_test.cpp, one `.dbtest zf stair <mechanic>` subcommand per mechanic, the
 *   descriptor (Mechanic::Describe), texts 7275 group 0. Own SQL rev:
 *   data/sql/updates/pending_db_world/rev_stair_zul_farrak.sql (the stock SmartAI is dropped by S0's
 *   rev_skeleton_zul_farrak.sql).
 * - Rules (handoff section 3.5 rules 1-36, RB-1..RB-22, LESSONS L1-L9): ZulFarrak::NoAssist(me) first in UpdateAI (rule
 *   27, host-tested); loot and hard mode bits are the instance's, never in JustDied; emotes type 41; custom damage
 *   spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS (script hits NO_REDIRECTION | NO_REFLECTION too); percent hits via
 *   DungeonKit::RefFlat / RefFlatOn with the boss as the owner; no summoned unit in ObjectData; _visuals.py constants
 *   only; every bot shape `.Within(PlazaFloorBounds())`; kickable casts and bars by the kick table (rule 24, LESSONS
 *   L2), dispels by rule 25; cleanup on reset, evade and death; mechanics include the tank; one log line per firing
 *   (DungeonKit::LogMechanic(kLogDungeon, ...)) and the pull line (OnBossPull, already here); every number a static
 *   constexpr in the Logic header's Tune (rule 32), health from ZulFarrakRework.h Health; the DC contract in the
 *   report.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "InstanceScript.h"
#include "ScriptedCreature.h"
#include "SezzzizLogic.h"
#include "ZulFarrakKit.h"
#include "ZulFarrakRework.h"
#include "ZulFarrakTestCommand.h"

using namespace Acore::ChatCommands;
using namespace ZulFarrakRework;

// Shadowpriest Sezz'ziz 7275
struct boss_sezzziz_rework : public ScriptedAI
{
    explicit boss_sezzziz_rework(Creature* creature)
        : ScriptedAI(creature), _arena(PlazaArena(), LeashOptions("stair")) { }

    void Reset() override
    {
        _arena.Reset();
    }

    void JustEngagedWith(Unit* who) override
    {
        ScriptedAI::JustEngagedWith(who);

        OnBossPull(me, "stair");
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_PYRAMID;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);
        if (InstanceScript* instance = me->GetInstanceScript())
            instance->SetData(DATA_PYRAMID_START, PYRAMID_STAGE_ALTAR);     // refused unless it is the stage in play
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        _arena.Reset();
        ScriptedAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* /*killer*/) override
    {
        _arena.Reset();
        DungeonKit::LogMechanic(kLogDungeon, "stair", "death", "boss_sezzziz_rework");
    }

    void UpdateAI(uint32 diff) override
    {
        ZulFarrak::NoAssist(me);        // rule 27, LESSONS L1: every tick, before UpdateVictim
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        scheduler.Update(diff);
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

private:
    DungeonKit::ArenaGuard _arena;
};

// Nekrum Gutchewer 7796
struct boss_nekrum_rework : public ScriptedAI
{
    explicit boss_nekrum_rework(Creature* creature)
        : ScriptedAI(creature), _arena(PlazaArena(), LeashOptions("stair")) { }

    void Reset() override
    {
        _arena.Reset();
    }

    void JustEngagedWith(Unit* who) override
    {
        ScriptedAI::JustEngagedWith(who);

        OnBossPull(me, "stair");
        _arena.Engage(me);
        if (InstanceScript* instance = me->GetInstanceScript())
            instance->SetData(DATA_PYRAMID_START, PYRAMID_STAGE_ALTAR);     // refused unless it is the stage in play
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        _arena.Reset();
        ScriptedAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* /*killer*/) override
    {
        _arena.Reset();
        DungeonKit::LogMechanic(kLogDungeon, "stair", "death", "boss_nekrum_rework");
    }

    void UpdateAI(uint32 diff) override
    {
        ZulFarrak::NoAssist(me);        // rule 27, LESSONS L1: every tick, before UpdateVictim
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        scheduler.Update(diff);
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

private:
    DungeonKit::ArenaGuard _arena;
};

void AddSC_boss_sezzziz_rework()
{
    RegisterDungeonReworkCreatureAI(boss_sezzziz_rework, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(boss_nekrum_rework, ZulFarrakRework::kInstanceScriptName);
}
