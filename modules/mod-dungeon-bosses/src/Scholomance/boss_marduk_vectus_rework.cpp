/*
 * mod-dungeon-bosses, Scholomance S3:
 * Marduk Blackpool (10433) and Vectus (10432), one encounter on BOSS_MARDUK_VECTUS (shared health).
 * STUB written by WP-KS (the Scholomance kit); WP-S3 owns this file from now on.
 *
 * What the stub does:
 * - two melee BossAIs on BOSS_MARDUK_VECTUS; the encounter is DONE only when both are dead (the first death clears
 *   its own events and summons and leaves the state IN_PROGRESS); the pull of either brings the other in;
 * - the registry encounter (Mechanic::BeginEncounter with bossStateId) on each;
 * - the arena leash (ViewingRoomArena, LeashOptions: no grips) on each;
 * - an engage / death log line and `.dbtest scholo marduk info` (Marduk) / `vectus` (Vectus's info).
 *
 * TODO(WP-S3):
 * - SC 934-991; handoff section 3.5 row S3, section 3.6 (one shared pool: normal 300k, heroic 425k; both rows carry
 *   the pool's health, the dbc-tools stub sets the normal HealthModifiers; heroic is WP-H's overrides).
 * - Mechanics: MV1 Flamestrike Drill, MV2 Group Exercise (Stack + split damage, DungeonKit::SplitShares), MV3 Pop Quiz,
 *   MV4 Ebon Sweep (the tank's hit is its own spell, R2 S-1), MV5 Fireball, MV6 Whirlwind (H), MV7 Blast Wave (stock
 *   17277).
 * - Shared health (Twin Val'kyr UpdateSharedHealth pattern, handoff section 3.2 kit #7): one pool; then one encounter
 *   owner for the registry and the descriptor (one target priority for both).
 * - Data: drop SmartAI 10433 x9, 10432 x7 and the students' 10475 x7 (keep the idle lecture lines in C++: fix the stray
 *   type 16 row of Vectus's group 0 or Talk by id; keep Dawn's Gambit (quest 4771) and "We are betrayed!");
 *   creature_text per ScholomanceRework.h; your own DamageModifier.
 * - Adds: Graduate 300533; the students 10475 become props (unselectable except the quiz student; 8k / 12k). DC's
 *   pre-clear patch is WP-DC's (handoff section 3.12).
 * - Heroic: shuffled syllabus, double period, persistent Drill, Whirlwind.
 * - Host-testable logic in MardukVectusLogic.h (spell ids in kSpellsMardukVectus), `.dbtest scholo marduk <mechanic>`
 *   subcommands, the descriptor, the registry calls of handoff section 3.4. Pilot lessons: see any KS stub's list.
 */

#include "ArenaGuard.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "InstanceScript.h"
#include "MardukVectusLogic.h"
#include "ScholomanceKit.h"
#include "ScholomanceRework.h"
#include "ScholomanceTestCommand.h"
#include "ScriptedCreature.h"
#include "StringFormat.h"

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;

// Marduk Blackpool 10433 and Vectus 10432: the same AI, told apart by entry.
struct boss_marduk_vectus_rework_base : public BossAI
{
    boss_marduk_vectus_rework_base(Creature* creature, char const* logName, uint32 partnerGuidData)
        : BossAI(creature, BOSS_MARDUK_VECTUS), _logName(logName), _partnerGuidData(partnerGuidData),
        _arena(ViewingRoomArena(), LeashOptions(logName)) { }

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
        options.bossStateId = BOSS_MARDUK_VECTUS;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);
        // One encounter: the partner joins the pull.
        if (Creature* partner = Partner(); partner && partner->IsAlive() && !partner->IsInCombat() && who)
            partner->AI()->AttackStart(who);
        DungeonKit::LogMechanic(kLogDungeon, _logName, "engage",
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
        _arena.Reset();
        DungeonKit::LogMechanic(kLogDungeon, _logName, "death");
        // The encounter is DONE when the second one dies (S3's shared health makes them die together).
        if (Creature* partner = Partner(); partner && partner->IsAlive())
        {
            events.Reset();
            scheduler.CancelAll();
            summons.DespawnAll();
            return;
        }
        BossAI::JustDied(killer);
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off the Viewing Room, or nobody in it for 10 s: evading

        events.Update(diff);
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

protected:
    Creature* Partner() const
    {
        return instance ? instance->GetCreature(_partnerGuidData) : nullptr;
    }

    char const* _logName;
    uint32 _partnerGuidData;
    DungeonKit::ArenaGuard _arena;
};

struct boss_marduk_blackpool_rework : public boss_marduk_vectus_rework_base
{
    explicit boss_marduk_blackpool_rework(Creature* creature)
        : boss_marduk_vectus_rework_base(creature, "marduk", DATA_VECTUS_GUID) { }
};

struct boss_vectus_rework : public boss_marduk_vectus_rework_base
{
    explicit boss_vectus_rework(Creature* creature)
        : boss_marduk_vectus_rework_base(creature, "vectus", DATA_MARDUK_GUID) { }
};

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return ScholoTest::ShowBossInfo(handler, NPC_MARDUK, BOSS_MARDUK_VECTUS);
    }

    bool HandleInfoVectus(ChatHandler* handler)
    {
        return ScholoTest::ShowBossInfo(handler, NPC_VECTUS, BOSS_MARDUK_VECTUS);
    }

    ChatCommandTable const& MardukVectusTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",   HandleInfo,       SEC_GAMEMASTER, Console::No },
            { "vectus", HandleInfoVectus, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_marduk_vectus_rework()
{
    RegisterDungeonReworkCreatureAI(boss_marduk_blackpool_rework, ScholomanceRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(boss_vectus_rework, ScholomanceRework::kInstanceScriptName);
    ScholoTest::RegisterBoss("marduk", MardukVectusTestCommands());
}
