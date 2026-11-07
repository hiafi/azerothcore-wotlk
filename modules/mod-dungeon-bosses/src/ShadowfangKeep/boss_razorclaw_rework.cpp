/*
 * mod-dungeon-bosses, Shadowfang Keep: Razorclaw the Butcher (WP-S2). Build spec: SK 444-479 (build spec), SK 357-443
 * (design), RC1-RC4; handoff section 3.5 rows RC and section 3.6 row S2.
 *
 * STUB from WP-K (the SFK layer): a plain melee BossAI on boss state BOSS_RAZORCLAW that begins the registry encounter,
 * bound by apps/dbc-tools source/npcs/shadowfang_keep/razorclaw.py (ScriptName, AIName '', normal health, immunities
 * 1972), plus `.sfktest razorclaw info`. WP-S2 owns this file, RazorclawLogic.h, tests/sfk_razorclaw_test.cpp, the DT
 * file and its own SQL rev; shared files (ShadowfangKeepRework.h, the instance, the loader, _common.py, tests/run.sh)
 * are WP-K's: ask the orchestrator in the report.
 *
 * TODO(WP-S2), handoff section 3.6 row S2:
 *   - RC1 Meat Hook: DungeonKit::LineStrike (width 3, overrun 5, exclude 4, warn 2 s, 35%, Weakened, clip
 *     RazorclawArena), OnHit -> DungeonKit::JumpTo the boss's front; Scourge Hook SV 11055. Share it as MeatHook.h
 *     (S3's Echo of Razorclaw reuses it). Heroic Twin Hooks (two distinct targets, one hit per player per cast) and
 *     Hung to Bleed (RefFlat 20% over 8 s).
 *   - RC2 Tenderize / RC3 Butcher's Cut: DungeonKit::AddStacks on each melee hit; at 3: CastBar 2 s, Cone(90, 10,
 *     TankExempt).Damage(40).Weakened(); the tank's hit is a 250% weapon spell (InFrontalCone).
 *   - RC4 heroic Offal Slick: DungeonKit::ImpactThenLinger (the Cut's cone, Persistent 30 s / 1 s, 5% + the kit's
 *     205201 slow).
 *   - Normal columns: DamageModifier 2.0 (add it to this file's creature_template_columns call).
 *   - SQL rev: drop SmartAI 3886 (Butcher Drain); creature_text 0-2.
 *   - DT razorclaw.py: spells 205930-205944 only.
 *   - ArenaGuard on RazorclawArena(); tests in tests/sfk_razorclaw_test.cpp.
 *
 * Pilot lessons (handoff section 4): custom damage spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS and hit through
 * LaunchTarget + SetEffectValue; visuals and timers never ride a scheduler the cast bar pauses; SaveToDB after a
 * saved data change; mechanic emotes are type 41; every hit has a visible impact; filled circles only for real
 * threats (a range cue is an outline, NoFillTimer); telegraph shapes match the room; the boss cannot be kited off
 * its arena (DungeonKit::ArenaGuard on RazorclawArena()). Log each firing with DungeonKit::LogMechanic("sfk",
 * "razorclaw", "<mechanic>", ...).
 */

#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "RazorclawLogic.h"
#include "ScriptedCreature.h"
#include "ShadowfangKeepRework.h"
#include "ShadowfangKeepTestCommand.h"
#include <string>

using namespace Acore::ChatCommands;
using namespace ShadowfangKeepRework;

// Razorclaw the Butcher 3886
struct boss_razorclaw_rework : public BossAI
{
    explicit boss_razorclaw_rework(Creature* creature) : BossAI(creature, BOSS_RAZORCLAW) { }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_RAZORCLAW;
        Mechanic::BeginEncounter(me, options);
        DungeonKit::LogMechanic(kLogDungeon, "razorclaw", "engage",
            std::string("heroic=") + (DungeonKit::IsHeroicMap(me) ? "1" : "0"));
    }
};

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return SfkTest::ShowBossInfo(handler, NPC_RAZORCLAW, BOSS_RAZORCLAW);
    }

    ChatCommandTable const& RazorclawTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_razorclaw_rework()
{
    RegisterDungeonReworkCreatureAI(boss_razorclaw_rework, ShadowfangKeepRework::kInstanceScriptName);
    SfkTest::RegisterBoss("razorclaw", RazorclawTestCommands());
}
