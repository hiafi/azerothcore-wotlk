/*
 * mod-dungeon-bosses, Scholomance S2:
 * Rattlegore (11622).
 * STUB written by WP-KS (the Scholomance kit); WP-S2 owns this file from now on.
 *
 * What the stub does:
 * - a melee BossAI on BOSS_RATTLEGORE (the instance's boss state: doors, Gandling's reveal, the save);
 * - the registry encounter (Mechanic::BeginEncounter with bossStateId);
 * - the arena leash (RattlegoreArena, LeashOptions: no grips);
 * - an engage / death log line and `.dbtest scholo rattlegore info`.
 *
 * TODO(WP-S2):
 * - SC 733-778; handoff section 3.5 row S2, section 3.6 (normal 185k, heroic 280k; the normal HealthModifier is set by
 *   the dbc-tools stub, heroic is WP-H's overrides).
 * - Mechanics: RG1 Part lands, RG2 Loose part, RG3 Pile returns, RG4 Ossuary Eruption, RG5 Salvage, RG6 Strike, RG7
 *   Knock Away, RG8 Frenzy.
 * - Data: drop SmartAI 11622 x3; creature_text per ScholomanceRework.h's text enum (your SQL rev); your own
 *   DamageModifier (the live value is a mod-progression leftover, handoff section 2.3).
 * - Adds: the loose part 300531 (Bone Spider display 27976, scale about 0.4), Unfinished Construct 300532 at
 *   kConstructSpots (display 12074 + Permanent Feign Death 29266); Knock Away copy without the threat cut. Keep the
 *   Viewing Room Key 13873 drop (loot).
 * - Heroic: 2 piles, out-and-back rings, Reinforced.
 * - The arena caps z at 98: the north stair foot (kOssuaryStairFoot) is inside the circle.
 * - Arena: RattlegoreArena() with LeashOptions (no grips; hold at the edge, evade after 10 s with nobody inside).
 *   Tighten it in your own file if the room needs it.
 * - Host-testable logic in RattlegoreLogic.h (spell ids in kSpellsRattlegore), one `.dbtest scholo rattlegore
 *   <mechanic>` subcommand per mechanic, the descriptor (Mechanic::Describe), the registry calls of handoff section
 *   3.4.
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
#include "RattlegoreLogic.h"
#include "ScholomanceRework.h"
#include "ScholomanceKit.h"
#include "ScholomanceTestCommand.h"
#include "ScriptedCreature.h"
#include "StringFormat.h"

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;

namespace
{
    char const* const kBossLogName = "rattlegore";
}

struct boss_rattlegore_rework : public BossAI
{
    explicit boss_rattlegore_rework(Creature* creature)
        : BossAI(creature, BOSS_RATTLEGORE), _arena(RattlegoreArena(), LeashOptions(kBossLogName)) { }

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
        options.bossStateId = BOSS_RATTLEGORE;
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
        return ScholoTest::ShowBossInfo(handler, NPC_RATTLEGORE, BOSS_RATTLEGORE);
    }

    ChatCommandTable const& RattlegoreTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_rattlegore_rework()
{
    RegisterDungeonReworkCreatureAI(boss_rattlegore_rework, ScholomanceRework::kInstanceScriptName);
    ScholoTest::RegisterBoss("rattlegore", RattlegoreTestCommands());
}
