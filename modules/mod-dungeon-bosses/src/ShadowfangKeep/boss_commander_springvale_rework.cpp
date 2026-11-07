/*
 * mod-dungeon-bosses, Shadowfang Keep: Commander Springvale (WP-S4). Build spec: SK 754-812 (build spec), SK 625-753
 * (design), SP1-SP8; handoff section 3.5 rows SP and section 3.6 row S4.
 *
 * STUB from WP-K (the SFK layer): a plain melee BossAI on boss state BOSS_SPRINGVALE that begins the registry
 * encounter, bound by apps/dbc-tools source/npcs/shadowfang_keep/commander_springvale.py (ScriptName, AIName '', normal
 * health, immunities 1972), plus `.sfktest springvale info`. WP-S4 owns this file, SpringvaleLogic.h,
 * tests/sfk_springvale_test.cpp, the DT file and its own SQL rev; shared files (ShadowfangKeepRework.h, the instance,
 * the loader, _common.py, tests/run.sh) are WP-K's: ask the orchestrator in the report.
 *
 * TODO(WP-S4), handoff section 3.6 row S4:
 *   - SP1 Hammer of Judgement: RunOut(target, 8, 3s).Damage(25).Weakened().Rider(stun 1.5 s); the marked player's own
 *     10% via RefFlat (no Weakened). SP2 heroic Ricochet (one bounce, off a live Consecration).
 *   - SP3 Consecration: DungeonKit::Linger(Circle(pos, 8), 10 s normal / 40 s heroic, 1 s, 5%, Holy, no slow).
 *   - SP4 Holy Light / SP5 heroic Searing Light: real interruptible casts (copies), heal 5%; on success heroic
 *     RefFlat(15%) to every player. Descriptor interrupt list.
 *   - SP6-SP7 Unbreakable Oath: user ruling (handoff section 10, section 7 #20): damage taken -90%, no immunity;
 *     guardsmen npc_sfk_risen_guardsman 300506-300508 rise at kGuardsmanRisePoints (display 3226), each death cracks
 *     it. SP8 heroic Wrath of God: 30 s uninterruptible cast, kills all on finish; kill order by entry.
 *   - SQL rev: drop SmartAI 4278 (5588, 1026, 33581); creature_text 2-5 (0-1 stock, kept in C++).
 *   - DT commander_springvale.py: spells 205965-205989 only; creatures 300506-300508.
 *   - Heroic (WP-H): each hostile kit add's full creature_template() row sets `difficulty_entry_1` to its id in
 *     source/world/heroic_ids.lock (generate.py --check prints it; STAGE-H report):
 *     300506 -> 310061, 300507 -> 310062, 300508 -> 310063.
 *   - ArenaGuard on SpringvaleArena(); tests in tests/sfk_springvale_test.cpp.
 *
 * Pilot lessons (handoff section 4): custom damage spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS and hit through
 * LaunchTarget + SetEffectValue; visuals and timers never ride a scheduler the cast bar pauses; SaveToDB after a
 * saved data change; mechanic emotes are type 41; every hit has a visible impact; filled circles only for real
 * threats (a range cue is an outline, NoFillTimer); telegraph shapes match the room; the boss cannot be kited off
 * its arena (DungeonKit::ArenaGuard on SpringvaleArena()). Log each firing with DungeonKit::LogMechanic("sfk",
 * "springvale", "<mechanic>", ...).
 */

#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "SpringvaleLogic.h"
#include "ScriptedCreature.h"
#include "ShadowfangKeepRework.h"
#include "ShadowfangKeepTestCommand.h"
#include <string>

using namespace Acore::ChatCommands;
using namespace ShadowfangKeepRework;

// Commander Springvale 4278
struct boss_commander_springvale_rework : public BossAI
{
    explicit boss_commander_springvale_rework(Creature* creature) : BossAI(creature, BOSS_SPRINGVALE) { }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_SPRINGVALE;
        Mechanic::BeginEncounter(me, options);
        DungeonKit::LogMechanic(kLogDungeon, "springvale", "engage",
            std::string("heroic=") + (DungeonKit::IsHeroicMap(me) ? "1" : "0"));
    }
};

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return SfkTest::ShowBossInfo(handler, NPC_SPRINGVALE, BOSS_SPRINGVALE);
    }

    ChatCommandTable const& SpringvaleTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_commander_springvale_rework()
{
    RegisterDungeonReworkCreatureAI(boss_commander_springvale_rework, ShadowfangKeepRework::kInstanceScriptName);
    SfkTest::RegisterBoss("springvale", SpringvaleTestCommands());
}
