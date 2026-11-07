/*
 * mod-dungeon-bosses, Shadowfang Keep: Baron Silverlaine (WP-S3). Build spec: SK 578-621 (build spec), SK 483-577
 * (design), BS1-BS7; handoff section 3.5 rows BS and section 3.6 row S3.
 *
 * STUB from WP-K (the SFK layer): a plain melee BossAI on boss state BOSS_SILVERLAINE that begins the registry
 * encounter, bound by apps/dbc-tools source/npcs/shadowfang_keep/baron_silverlaine.py (ScriptName, AIName '', normal
 * health, immunities 1972), plus `.sfktest silverlaine info`. WP-S3 owns this file, SilverlaineLogic.h,
 * tests/sfk_silverlaine_test.cpp, the DT file and its own SQL rev; shared files (ShadowfangKeepRework.h, the instance,
 * the loader, _common.py, tests/run.sh) are WP-K's: ask the orchestrator in the report.
 *
 * TODO(WP-S3), handoff section 3.6 row S3:
 *   - BS1-BS5 Echoes: npc_sfk_echo on 300503 (Rethilgore, SoulDrain.h from S1), 300504 (Razorclaw, MeatHook.h from S2),
 *     300505 (Odo, Hunt.h from S5: 8 s, 1.5 s stun Maul, RefFlat 20%); spectral look (Ghost Visual 9617 / SV 886). User
 *     ruling (handoff section 10, section 7 #21): on timers, not health % (first at 15 s, then every 25 s, in kill
 *     order); one alive at a time on normal.
 *   - BS6 Accursed Veil: a real 1.5 s interruptible cast; the curse aura (DoT RefFlat 3% / 2 s, healing -50%, Curse);
 *     every 2 s a fresh Spread(4).Targets(cursed) with a 2 s warn, OnHit copies the curse (section 7 #18).
 *   - BS7 heroic The Night Ends: at 10% every echo not alive returns (YELL_SILVERLAINE_NIGHT_ENDS).
 *   - SQL rev: drop SmartAI 3887 (aggro yell kept in C++); creature_text 1-4.
 *   - DT baron_silverlaine.py: spells 205945-205964 only; creatures 300503-300505.
 *   - Heroic (WP-H): each hostile kit add's full creature_template() row sets `difficulty_entry_1` to its id in
 *     source/world/heroic_ids.lock (generate.py --check prints it; STAGE-H report):
 *     300503 -> 310058, 300504 -> 310059, 300505 -> 310060.
 *   - ArenaGuard on SilverlaineArena() (alcove + hall); tests in tests/sfk_silverlaine_test.cpp.
 *
 * Pilot lessons (handoff section 4): custom damage spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS and hit through
 * LaunchTarget + SetEffectValue; visuals and timers never ride a scheduler the cast bar pauses; SaveToDB after a
 * saved data change; mechanic emotes are type 41; every hit has a visible impact; filled circles only for real
 * threats (a range cue is an outline, NoFillTimer); telegraph shapes match the room; the boss cannot be kited off
 * its arena (DungeonKit::ArenaGuard on SilverlaineArena()). Log each firing with DungeonKit::LogMechanic("sfk",
 * "silverlaine", "<mechanic>", ...).
 */

#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "SilverlaineLogic.h"
#include "ScriptedCreature.h"
#include "ShadowfangKeepRework.h"
#include "ShadowfangKeepTestCommand.h"
#include <string>

using namespace Acore::ChatCommands;
using namespace ShadowfangKeepRework;

// Baron Silverlaine 3887
struct boss_baron_silverlaine_rework : public BossAI
{
    explicit boss_baron_silverlaine_rework(Creature* creature) : BossAI(creature, BOSS_SILVERLAINE) { }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_SILVERLAINE;
        Mechanic::BeginEncounter(me, options);
        DungeonKit::LogMechanic(kLogDungeon, "silverlaine", "engage",
            std::string("heroic=") + (DungeonKit::IsHeroicMap(me) ? "1" : "0"));
    }
};

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return SfkTest::ShowBossInfo(handler, NPC_SILVERLAINE, BOSS_SILVERLAINE);
    }

    ChatCommandTable const& SilverlaineTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_baron_silverlaine_rework()
{
    RegisterDungeonReworkCreatureAI(boss_baron_silverlaine_rework, ShadowfangKeepRework::kInstanceScriptName);
    SfkTest::RegisterBoss("silverlaine", SilverlaineTestCommands());
}
