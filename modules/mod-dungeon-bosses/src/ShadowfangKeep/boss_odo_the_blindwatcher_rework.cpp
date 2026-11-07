/*
 * mod-dungeon-bosses, Shadowfang Keep: Odo the Blindwatcher (WP-S5). Build spec: SK 904-952 (build spec), SK 816-903
 * (design), OD1-OD6; handoff section 3.5 rows OD and section 3.6 row S5.
 *
 * STUB from WP-K (the SFK layer): a plain melee BossAI on boss state BOSS_ODO that begins the registry encounter, bound
 * by apps/dbc-tools source/npcs/shadowfang_keep/odo_the_blindwatcher.py (ScriptName, AIName '', normal health,
 * immunities 1972), plus `.sfktest odo info`. WP-S5 owns this file, OdoLogic.h, tests/sfk_odo_test.cpp, the DT file and
 * its own SQL rev; shared files (ShadowfangKeepRework.h, the instance, the loader, _common.py, tests/run.sh) are
 * WP-K's: ask the orchestrator in the report.
 *
 * TODO(WP-S5), handoff section 3.6 row S5:
 *   - OD1 The Hunt: fixate + DungeonKit::SetRunSpeedPct (80% normal / 95% heroic) + Circle(odo,
 *     3).AnchorOn(odo).Persistent(10s, 250ms).Eligible({carriers = {hunted}}). Share it as Hunt.h (S3's Echo of Odo
 *     reuses it). Sign-off waits on WP-GD's sfk-hunt drill (handoff section 3.9, section 7 #5).
 *   - OD2 Maul: on catch, stun 3 s + RefFlat(35%) over 3 s.
 *   - OD3 Ring the bell: DungeonKit::Pickups (1 body, dwell 1 s, Eligibility non-tank and not the hunted), only during
 *     a Hunt; the GO is also clickable (go_sfk_alarm_bell below). OD4 Bell landing: Circle(bell, 6,
 *     2s).Damage(35).Weakened() as Odo jumps there (DungeonKit::JumpTo). Bell toll SoundEntries 9154.
 *   - Howling Rage (stock 7481 / 7483 / 7484 at 70 / 50 / 30%) kept in C++. Heroic Relentless Hunt, Silenced Bells,
 *     Blood Frenzy (EMOTE_ODO_FRENZY).
 *   - SQL rev: drop SmartAI 4279 (Call for Help gone); spawn the three bells (GO 301101, template in WP-K's rev, size
 *     0.55) at kBellSpots, spawnMask 3; creature_text 0-2.
 *   - DT odo_the_blindwatcher.py: spells 205990-206009 only.
 *   - ArenaGuard on OdoArena(); tests in tests/sfk_odo_test.cpp.
 *
 * Pilot lessons (handoff section 4): custom damage spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS and hit through
 * LaunchTarget + SetEffectValue; visuals and timers never ride a scheduler the cast bar pauses; SaveToDB after a
 * saved data change; mechanic emotes are type 41; every hit has a visible impact; filled circles only for real
 * threats (a range cue is an outline, NoFillTimer); telegraph shapes match the room; the boss cannot be kited off
 * its arena (DungeonKit::ArenaGuard on OdoArena()). Log each firing with DungeonKit::LogMechanic("sfk",
 * "odo", "<mechanic>", ...).
 */

#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "GameObjectAI.h"
#include "OdoLogic.h"
#include "ScriptedCreature.h"
#include "ShadowfangKeepRework.h"
#include "ShadowfangKeepTestCommand.h"
#include <string>

using namespace Acore::ChatCommands;
using namespace ShadowfangKeepRework;

// Odo the Blindwatcher 4279
struct boss_odo_the_blindwatcher_rework : public BossAI
{
    explicit boss_odo_the_blindwatcher_rework(Creature* creature) : BossAI(creature, BOSS_ODO) { }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_ODO;
        Mechanic::BeginEncounter(me, options);
        DungeonKit::LogMechanic(kLogDungeon, "odo", "engage",
            std::string("heroic=") + (DungeonKit::IsHeroicMap(me) ? "1" : "0"));
    }
};

// The Alarm Bell 301101 (go_sfk_alarm_bell): clickable as well as a pickup (OD3). STUB from WP-K.
struct go_sfk_alarm_bell : public GameObjectAI
{
    explicit go_sfk_alarm_bell(GameObject* go) : GameObjectAI(go) { }
};

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return SfkTest::ShowBossInfo(handler, NPC_ODO, BOSS_ODO);
    }

    ChatCommandTable const& OdoTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_odo_the_blindwatcher_rework()
{
    RegisterDungeonReworkCreatureAI(boss_odo_the_blindwatcher_rework, ShadowfangKeepRework::kInstanceScriptName);
    RegisterDungeonReworkGameObjectAI(go_sfk_alarm_bell, ShadowfangKeepRework::kInstanceScriptName);
    SfkTest::RegisterBoss("odo", OdoTestCommands());
}
