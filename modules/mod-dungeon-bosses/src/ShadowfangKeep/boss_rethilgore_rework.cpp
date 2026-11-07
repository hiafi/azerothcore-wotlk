/*
 * mod-dungeon-bosses, Shadowfang Keep: Rethilgore (WP-S1). Build spec: SK 310-353 (normal and heroic), SK 191-309
 * (design), RG1-RG6; handoff section 3.5 rows RG and section 3.6 row S1.
 *
 * STUB from WP-K (the SFK layer): a plain melee BossAI on boss state BOSS_RETHILGORE that begins the registry
 * encounter, bound by apps/dbc-tools source/npcs/shadowfang_keep/rethilgore.py (ScriptName, AIName '', normal health,
 * immunities 1972), plus `.sfktest rethilgore info`. WP-S1 owns this file, RethilgoreLogic.h,
 * tests/sfk_rethilgore_test.cpp, the DT file and its own SQL rev; shared files (ShadowfangKeepRework.h, the instance,
 * the loader, _common.py, tests/run.sh) are WP-K's: ask the orchestrator in the report.
 *
 * TODO(WP-S1), handoff section 3.6 row S1:
 *   - RG1 Lock-Up: emote (EMOTE_RETHILGORE_LOCK_UP), DungeonKit::JumpTo him to the target, then the target into a cell
 *     (kCellLandings), that door closed (GO_STATE_READY), a stand-in spawned; waits while anyone is jailed. Confinement
 *     (Kit/ArenaGuard.h) holds jailed units in (CellArena) and keeps others out (InFrontOfCell): server movement
 *     ignores closed doors (handoff section 3.2 #1b, section 7 #6).
 *   - RG2 Cell Door: npc_sfk_cell_door (300500, invisible display 11686) derived from DungeonKit::BreakableDoorAI,
 *     DungeonKit::SpawnBreakableDoor (720 / 12,000 health); descriptor TargetEntry(300500, 2). LoS through door display
 *     411: check with `.sfktest cells los` (WP-K) before sign-off.
 *   - RG3 Cell Key: DungeonKit::Pickups where the key lands (kKeyLandings, along the corridor; GO 301100 is the look, a
 *     goEntry), then a carrier-only pickup at the closed occupied door (Eligibility.carriers).
 *   - RG4 Soul Drain: the channel on the cell prisoner (SV 680; a real channel), tick = RefFlat(5%); share it as
 *     SoulDrain.h (S3's Echo of Rethilgore reuses it).
 *   - RG5 Soul Fragment: npc_sfk_soul_fragment (300501, wisp display 1825), Pickups 1 body, life 6 s, onExpire heals
 *     him 5% (kFragmentPointsS/M/N, at least 2 yd apart).
 *   - RG6 heroic Tainted Fragment (300502, display 24465): Mechanic::Mine(pos, 1.5, 500ms,
 *     0).Lifetime(40s).Damage(25).Weakened(); never in the corridor's narrow WNW third (cell N).
 *   - On his death: tell the prisoners (stock SmartAI 3914 rows 1-2: SetData(1, 1) on Ashcrombe, SetData(1, 2) on
 *     Adamant; the instance's GetCreature(DATA_ASHCROMBE_GUID / DATA_ADAMANT_GUID)). The instance opens all three cell
 *     doors on DONE and locks the levers while he is IN_PROGRESS; open any door Lock-Up closed on evade / reset.
 *   - SQL rev: drop SmartAI 3914; cell levers 18900 / 18901 / 101811 action 9 -> 118 (open only, handoff section 2.5);
 *     creature_text 0-2 + Adamant 5, Ashcrombe 5, Landen 0.
 *   - DT rethilgore.py: spells 205910-205929 only; creatures 300500-300502.
 *   - Heroic (WP-H): each hostile kit add's full creature_template() row sets `difficulty_entry_1` to its id in
 *     source/world/heroic_ids.lock (generate.py --check prints it; STAGE-H report):
 *     300500 -> 310057 (300501 / 300502 are triggers: no heroic
 *     template).
 *   - ArenaGuard on RethilgoreArena(); tests in tests/sfk_rethilgore_test.cpp.
 *
 * Pilot lessons (handoff section 4): custom damage spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS and hit through
 * LaunchTarget + SetEffectValue; visuals and timers never ride a scheduler the cast bar pauses; SaveToDB after a
 * saved data change; mechanic emotes are type 41; every hit has a visible impact; filled circles only for real
 * threats (a range cue is an outline, NoFillTimer); telegraph shapes match the room; the boss cannot be kited off
 * its arena (DungeonKit::ArenaGuard on RethilgoreArena()). Log each firing with DungeonKit::LogMechanic("sfk",
 * "rethilgore", "<mechanic>", ...).
 */

#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "RethilgoreLogic.h"
#include "ScriptedCreature.h"
#include "ShadowfangKeepRework.h"
#include "ShadowfangKeepTestCommand.h"
#include <string>

using namespace Acore::ChatCommands;
using namespace ShadowfangKeepRework;

// Rethilgore 3914
struct boss_rethilgore_rework : public BossAI
{
    explicit boss_rethilgore_rework(Creature* creature) : BossAI(creature, BOSS_RETHILGORE) { }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_RETHILGORE;
        Mechanic::BeginEncounter(me, options);
        DungeonKit::LogMechanic(kLogDungeon, "rethilgore", "engage",
            std::string("heroic=") + (DungeonKit::IsHeroicMap(me) ? "1" : "0"));
    }
};

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return SfkTest::ShowBossInfo(handler, NPC_RETHILGORE, BOSS_RETHILGORE);
    }

    ChatCommandTable const& RethilgoreTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_rethilgore_rework()
{
    RegisterDungeonReworkCreatureAI(boss_rethilgore_rework, ShadowfangKeepRework::kInstanceScriptName);
    SfkTest::RegisterBoss("rethilgore", RethilgoreTestCommands());
}
