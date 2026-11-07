/*
 * mod-dungeon-bosses, Shadowfang Keep: Wolf Master Nandos (WP-S8). Build spec: SK 1338-1390 (build spec), SK 1238-1337
 * (design), NA1-NA8; handoff section 3.5 rows NA and section 3.6 row S8.
 *
 * STUB from WP-K (the SFK layer): a plain melee BossAI on boss state BOSS_NANDOS that begins the registry encounter,
 * bound by apps/dbc-tools source/npcs/shadowfang_keep/wolf_master_nandos.py (ScriptName, AIName '', normal health,
 * immunities 1972), plus `.sfktest nandos info`. WP-S8 owns this file, NandosLogic.h, tests/sfk_nandos_test.cpp, the DT
 * file and its own SQL rev; shared files (ShadowfangKeepRework.h, the instance, the loader, _common.py, tests/run.sh)
 * are WP-K's: ask the orchestrator in the report.
 *
 * TODO(WP-S8), handoff section 3.6 row S8:
 *   - The pack: npc_sfk_pack_wolf on 300509-300512 (copies of 3861, 3863, 3862, 5058; displays 801, 2446, 11421, 246);
 *     the SQL rev repoints spawns 16238-16241 (kPackSpawns) to them. Pulling any wolf pulls all five.
 *   - NA1 Wavering Will (stock 7127), NA2 Lupine Delusions (stock 7132, 5097), NA3 heroic fear (Circle(spot, 5,
 *     2s).Rider(fear 2 s)); inherited: DungeonKit::AddStacks DoT RefFlat(2%).
 *   - NA4 Acid Slaver: CastBar 2 s + Cone(wolf or me, 90, 8 / 20, TankExempt).Damage(35).Weakened() (Acid Breath SV
 *     2619). NA5 Guardian Howl: a real 2 s interruptible cast, heal 5%, heroic +15% damage 10 s.
 *   - NA6 Mark the Prey: Stack(prey, 6, 4s) (kNandosOpenPoint is the most open spot); OnResolve:
 *     DungeonKit::SplitShares of RefFlat(25%) x wolves alive, cap 75% (EMOTE_NANDOS_MARK_THE_PREY).
 *   - NA7 Pack Bond (-40%, -10% per wolf dead), NA8 heroic Alpha's Inheritance (each wolf's death adds its ability).
 *     YELL_NANDOS_PACK_DEAD on the last wolf. His DONE opens Arugal's Lair (door data) and summons the lair prisoner
 *     (the instance).
 *   - SQL rev: drop SmartAI 3927 (7489, 7487) and guid SmartAI -16238..-16241; spawns 16238-16241 -> the copies;
 *     creature_text 1.
 *   - DT wolf_master_nandos.py: spells 206040-206059 only; creatures 300509-300512.
 *   - Heroic (WP-H): each hostile kit add's full creature_template() row sets `difficulty_entry_1` to its id in
 *     source/world/heroic_ids.lock (generate.py --check prints it; STAGE-H report):
 *     300509 -> 310064, 300510 -> 310065, 300511 -> 310066, 300512 -> 310067.
 *   - ArenaGuard on NandosArena(); tests in tests/sfk_nandos_test.cpp.
 *
 * Pilot lessons (handoff section 4): custom damage spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS and hit through
 * LaunchTarget + SetEffectValue; visuals and timers never ride a scheduler the cast bar pauses; SaveToDB after a
 * saved data change; mechanic emotes are type 41; every hit has a visible impact; filled circles only for real
 * threats (a range cue is an outline, NoFillTimer); telegraph shapes match the room; the boss cannot be kited off
 * its arena (DungeonKit::ArenaGuard on NandosArena()). Log each firing with DungeonKit::LogMechanic("sfk",
 * "nandos", "<mechanic>", ...).
 */

#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "NandosLogic.h"
#include "ScriptedCreature.h"
#include "ShadowfangKeepRework.h"
#include "ShadowfangKeepTestCommand.h"
#include <string>

using namespace Acore::ChatCommands;
using namespace ShadowfangKeepRework;

// Wolf Master Nandos 3927
struct boss_wolf_master_nandos_rework : public BossAI
{
    explicit boss_wolf_master_nandos_rework(Creature* creature) : BossAI(creature, BOSS_NANDOS) { }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_NANDOS;
        Mechanic::BeginEncounter(me, options);
        DungeonKit::LogMechanic(kLogDungeon, "nandos", "engage",
            std::string("heroic=") + (DungeonKit::IsHeroicMap(me) ? "1" : "0"));
    }
};

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return SfkTest::ShowBossInfo(handler, NPC_NANDOS, BOSS_NANDOS);
    }

    ChatCommandTable const& NandosTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_wolf_master_nandos_rework()
{
    RegisterDungeonReworkCreatureAI(boss_wolf_master_nandos_rework, ShadowfangKeepRework::kInstanceScriptName);
    SfkTest::RegisterBoss("nandos", NandosTestCommands());
}
