/*
 * mod-dungeon-bosses, Scholomance S1:
 * Jandice Barov (10503).
 * STUB written by WP-KS (the Scholomance kit); WP-S1 owns this file from now on.
 *
 * What the stub does:
 * - a melee BossAI on BOSS_JANDICE (the instance's boss state: doors, Gandling's reveal, the save);
 * - the registry encounter (Mechanic::BeginEncounter with bossStateId);
 * - the arena leash (JandiceArena, LeashOptions: no grips);
 * - an engage / death log line and `.dbtest scholo jandice info`.
 *
 * TODO(WP-S1):
 * - SC 546-601; handoff section 3.5 row S1, section 3.6 (normal 175k, heroic 265k; the normal HealthModifier is set by
 *   the dbc-tools stub, heroic is WP-H's overrides).
 * - Mechanics: JB1 Blood Sigil, JB2 The Shell Game, JB3 Shatter, JB4 Unmasked, JB5 Failed game, JB6 Bloodlines, JB7
 *   Shuffle (H), JB8 Blood Price (H), JB9 Curse of Blood.
 * - Data: drop SmartAI 10503 x8 (keep the death emote, text group 0, and the journal spell 26096 in C++); creature_text
 *   per ScholomanceRework.h's text enum (your SQL rev); your own DamageModifier (the live value is a mod-progression
 *   leftover, handoff section 2.3).
 * - Adds: Reflection 300530 (two creature_equip_template sets: id 1 journal 12866, id 2 empty); the Shell Game copy
 *   reuses the stock Illusion of Jandice Barov 11439 (give it an AI and the copy flags).
 * - Heroic: the decoy sigil and lane need BM Decoy() (WP-X); shuffle, Blood Price, 15 copies, two finds.
 * - Frame kJandiceAisle (21 yd wide: 3 lanes across, 7 along the body; handoff section 7 #12) and the heroic sigil grid
 *   kJandiceSigilGrid are in ScholomanceRework.h.
 * - Arena: JandiceArena() with LeashOptions (no grips; hold at the edge, evade after 10 s with nobody inside). Tighten
 *   it in your own file if the room needs it.
 * - Host-testable logic in JandiceLogic.h (spell ids in kSpellsJandice), one `.dbtest scholo jandice <mechanic>`
 *   subcommand per mechanic, the descriptor (Mechanic::Describe), the registry calls of handoff section 3.4.
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
#include "JandiceLogic.h"
#include "ScholomanceRework.h"
#include "ScholomanceKit.h"
#include "ScholomanceTestCommand.h"
#include "ScriptedCreature.h"
#include "StringFormat.h"

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;

namespace
{
    char const* const kBossLogName = "jandice";
}

struct boss_jandice_barov_rework : public BossAI
{
    explicit boss_jandice_barov_rework(Creature* creature)
        : BossAI(creature, BOSS_JANDICE), _arena(JandiceArena(), LeashOptions(kBossLogName)) { }

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
        options.bossStateId = BOSS_JANDICE;
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
        return ScholoTest::ShowBossInfo(handler, NPC_JANDICE, BOSS_JANDICE);
    }

    ChatCommandTable const& JandiceTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_jandice_barov_rework()
{
    RegisterDungeonReworkCreatureAI(boss_jandice_barov_rework, ScholomanceRework::kInstanceScriptName);
    ScholoTest::RegisterBoss("jandice", JandiceTestCommands());
}
