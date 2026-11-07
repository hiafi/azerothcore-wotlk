/*
 * mod-dungeon-bosses, Shadowfang Keep: Fenrus the Devourer (WP-S7). Build spec: SK 1183-1234 (build spec), SK 1087-1182
 * (design), FN1-FN8; handoff section 3.5 rows FN and section 3.6 row S7.
 *
 * STUB from WP-K (the SFK layer): a plain melee BossAI on boss state BOSS_FENRUS that begins the registry encounter,
 * bound by apps/dbc-tools source/npcs/shadowfang_keep/fenrus_the_devourer.py (ScriptName, AIName '', normal health,
 * immunities 1972), plus `.sfktest fenrus info`. WP-S7 owns this file, FenrusLogic.h, tests/sfk_fenrus_test.cpp, the DT
 * file and its own SQL rev; shared files (ShadowfangKeepRework.h, the instance, the loader, _common.py, tests/run.sh)
 * are WP-K's: ask the orchestrator in the report.
 *
 * TODO(WP-S7), handoff section 3.6 row S7:
 *   - Arugal speaks from above: YELL_ARUGAL_FENRUS_PULL on the pull, YELL_ARUGAL_RELEASE_YOUR_RAGE on the first FN1,
 *     YELL_ARUGAL_AGGRO on FN5 (heroic); Arugal's Focus is DATA_ARUGALS_FOCUS_GUID.
 *   - FN1 Arugal's Lightning: Circle(edge point, 3, 2s).Damage(20).Weakened() at kFenrusStrikePoints (Lightning Cloud
 *     SV 986); OnResolve summons Arugal's Voidwalker 4627 there. FN2 voidwalkers: npc_sfk_voidwalker on 4627 (rebind it
 *     with creature_template_columns in this WP's DT file: ScriptName, AIName '', health 800 / 12,000); never summon
 *     4627 through ObjectData.
 *   - FN3 Void Pulse (+ heroic Rising Pulse): a real 1.5 s interruptible cast on the voidwalker, RefFlat(4% .. 10%) to
 *     every player; voidwalkers stay stunnable.
 *   - FN5 heroic Shadow Fenrus: DungeonKit::LethalGuard (fake death, handoff section 7 #15): 1 s still, health to 40%,
 *     Shadow melee; BOSS_FENRUS DONE (the Sorcerer's Gate, door data) only on the final death.
 *   - FN6-FN7 heroic Shadow Leap: Bait(me, BaitRule::FewestStacks(SCAR), 12,
 *     2s).Radius(6).Damage(25).Weakened().Rider(SCAR); the leap's x(1 + 2 x stacks) in the resolve copy's SpellScript;
 *     JumpTo. FN8 heroic Shadow Lightning: Circle(player, 3, 1s).Damage(15) (no Weakened).
 *   - SQL rev: drop SmartAI 4274, 4627, 4275's intro rows and action list 427500; creature_text Fenrus 0.
 *   - DT fenrus_the_devourer.py: spells 206020-206039 only; the 4627 columns.
 *   - ArenaGuard on FenrusArena(); tests in tests/sfk_fenrus_test.cpp.
 *
 * Pilot lessons (handoff section 4): custom damage spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS and hit through
 * LaunchTarget + SetEffectValue; visuals and timers never ride a scheduler the cast bar pauses; SaveToDB after a
 * saved data change; mechanic emotes are type 41; every hit has a visible impact; filled circles only for real
 * threats (a range cue is an outline, NoFillTimer); telegraph shapes match the room; the boss cannot be kited off
 * its arena (DungeonKit::ArenaGuard on FenrusArena()). Log each firing with DungeonKit::LogMechanic("sfk",
 * "fenrus", "<mechanic>", ...).
 */

#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "FenrusLogic.h"
#include "ScriptedCreature.h"
#include "ShadowfangKeepRework.h"
#include "ShadowfangKeepTestCommand.h"
#include <string>

using namespace Acore::ChatCommands;
using namespace ShadowfangKeepRework;

// Fenrus the Devourer 4274
struct boss_fenrus_the_devourer_rework : public BossAI
{
    explicit boss_fenrus_the_devourer_rework(Creature* creature) : BossAI(creature, BOSS_FENRUS) { }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_FENRUS;
        Mechanic::BeginEncounter(me, options);
        DungeonKit::LogMechanic(kLogDungeon, "fenrus", "engage",
            std::string("heroic=") + (DungeonKit::IsHeroicMap(me) ? "1" : "0"));
    }
};

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return SfkTest::ShowBossInfo(handler, NPC_FENRUS, BOSS_FENRUS);
    }

    ChatCommandTable const& FenrusTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_fenrus_the_devourer_rework()
{
    RegisterDungeonReworkCreatureAI(boss_fenrus_the_devourer_rework, ShadowfangKeepRework::kInstanceScriptName);
    SfkTest::RegisterBoss("fenrus", FenrusTestCommands());
}
