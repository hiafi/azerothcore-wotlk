/*
 * mod-dungeon-bosses, Shadowfang Keep: Archmage Arugal (WP-S9). Build spec: SK 1576-1646 (build spec), SK 1394-1575
 * (design), AR1-AR9; handoff section 3.5 rows AR and section 3.6 row S9.
 *
 * STUB from WP-K (the SFK layer): a plain melee BossAI on boss state BOSS_ARUGAL that begins the registry encounter,
 * bound by apps/dbc-tools source/npcs/shadowfang_keep/archmage_arugal.py (ScriptName, AIName '', normal health,
 * immunities 1972), plus `.sfktest arugal info`. WP-S9 owns this file, ArugalLogic.h, tests/sfk_arugal_test.cpp, the DT
 * file and its own SQL rev; shared files (ShadowfangKeepRework.h, the instance, the loader, _common.py, tests/run.sh)
 * are WP-K's: ask the orchestrator in the report.
 *
 * TODO(WP-S9), handoff section 3.6 row S9:
 *   - User rulings (handoff section 10): he keeps his stock ledge and Shadow Port spots (kShadowPortSpots; 7587 is off
 *     the mesh, ArugalArena() includes its ledge); every level of the room stays reachable by melee with well-timed
 *     jumps, bots that cannot jump path via the stairs; the wards are placed for the level he is on
 *     (kLowerFloorWardPoints on the lower floor). All turned = the turned players die and the fight resets (section 7
 *     #22).
 *   - AR1 Worgen's Curse (+ heroic Feral Power): DungeonKit::AddStacks meter, seep +1 / 3 s; never dispellable. AR2
 *     Thundershock: CastBar 2 s + Circle(me, 8).AnchorOn(me).Damage(30).Rider(stun 1.5 s), OnHit +15 stacks. AR3 Void
 *     Bolt: a real 3 s interruptible copy, RefFlat(15% / 25%), +3 stacks. AR4 Arugal's Curse: +10 stacks on a random
 *     non-tank. AR5 Shadow Port: 1 s flicker, NearTeleportTo a spot, rooted 10 s.
 *   - AR6 Turned: 100 stacks -> charm + transform (display 202); needs WP-F1 (FORK attack / heal filters and the BM
 *     descriptor field). AR7 Ashcrombe's Ward: Stack(wardPos, 5, 1s).Persistent(10s, 250ms).Eligible({auraSpell =
 *     CURSE, minStacks = 20}); -10 stacks pulses. AR9 heroic Moonrise at 30%.
 *   - The lair prisoner npc_sfk_lair_prisoner (below): 300513 Ashcrombe / 300514 Adamant, declared by WP-K in
 *     archmage_arugal.py; the instance summons it at kLairPrisonerWait on Nandos's DONE (DATA_LAIR_PRISONER_GUID); S9
 *     moves it to the gallery (kLairPrisonerGallery) and gives it the wards and its gossip menu (heroic option: S10).
 *     Ward stalker 300515.
 *   - SQL rev: drop SmartAI 4275 (all rows); prisoner action lists 384900 / 385000: the farewell line -> group 8 and
 *     one added row SetData(DATA_PRISONER = 21, 1 Ashcrombe / 2 Adamant); creature_text 4-5 + prisoners 6-8; the lair
 *     prisoners' gossip menus.
 *   - DT archmage_arugal.py: spells 206060-206084 only (206085-206089 are S10's); creature 300515.
 *   - ArenaGuard on ArugalArena(); tests in tests/sfk_arugal_test.cpp.
 *
 * Pilot lessons (handoff section 4): custom damage spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS and hit through
 * LaunchTarget + SetEffectValue; visuals and timers never ride a scheduler the cast bar pauses; SaveToDB after a
 * saved data change; mechanic emotes are type 41; every hit has a visible impact; filled circles only for real
 * threats (a range cue is an outline, NoFillTimer); telegraph shapes match the room; the boss cannot be kited off
 * its arena (DungeonKit::ArenaGuard on ArugalArena()). Log each firing with DungeonKit::LogMechanic("sfk",
 * "arugal", "<mechanic>", ...).
 */

#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "ArugalLogic.h"
#include "ScriptedCreature.h"
#include "ShadowfangKeepRework.h"
#include "ShadowfangKeepTestCommand.h"
#include <string>

using namespace Acore::ChatCommands;
using namespace ShadowfangKeepRework;

// Archmage Arugal 4275
struct boss_archmage_arugal_rework : public BossAI
{
    explicit boss_archmage_arugal_rework(Creature* creature) : BossAI(creature, BOSS_ARUGAL) { }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_ARUGAL;
        Mechanic::BeginEncounter(me, options);
        DungeonKit::LogMechanic(kLogDungeon, "arugal", "engage",
            std::string("heroic=") + (DungeonKit::IsHeroicMap(me) ? "1" : "0"));
    }
};

// The lair prisoner (300513 Ashcrombe / 300514 Adamant, npc_sfk_lair_prisoner): the instance summons it at the lair
// door on Nandos's DONE. STUB from WP-K: passive; S9 gives it the wards, S10 its heroic gossip option.
struct npc_sfk_lair_prisoner : public ScriptedAI
{
    explicit npc_sfk_lair_prisoner(Creature* creature) : ScriptedAI(creature)
    {
        me->SetReactState(REACT_PASSIVE);
    }
};

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return SfkTest::ShowBossInfo(handler, NPC_ARUGAL, BOSS_ARUGAL);
    }

    ChatCommandTable const& ArugalTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_archmage_arugal_rework()
{
    RegisterDungeonReworkCreatureAI(boss_archmage_arugal_rework, ShadowfangKeepRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sfk_lair_prisoner, ShadowfangKeepRework::kInstanceScriptName);
    SfkTest::RegisterBoss("arugal", ArugalTestCommands());
}
