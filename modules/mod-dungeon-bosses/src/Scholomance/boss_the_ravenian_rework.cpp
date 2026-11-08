/*
 * mod-dungeon-bosses, Scholomance S8: The Ravenian (10507) and Master Corvane (300542), normal and heroic, their
 * Graduate Examiner mode and the Vault of the Ravenian's solo lesson. Build spec: SC 2193-2259 (build spec), SC
 * 2052-2192 (design: pitch A "The Leash"), RV1-RV11; handoff section 3.4 rows RV, section 3.5 row S8, section 3.6
 * (normal 160k / 50k, heroic 210k / 65k, examiners 60k / 20k), section 3.7, section 3.8 and the user ruling of
 * 2026-11-08 (Corvane's phase 1 seat is kRavenianUserSpot, right behind the Ravenian; landing (128, -1)). Replaces
 * SmartAI 10507 (WP-S8's SQL rev drops the five rows: Cleave 20691, Trample 15550 and Knock Away 10101 retired,
 * Sundering Cleave 25174 copied for one target, the death's SetData(1,1) replaced by the boss state). Bound by
 * apps/dbc-tools source/npcs/scholomance/the_ravenian.py (the Ravenian's columns, Corvane 300542, the spells).
 *
 *   The leash        Corvane stands on his seat behind the Ravenian, unselectable, a beam from his hands to its back
 *                    (206270, a channel his other casts do not break).
 *   RV1-RV4 Orders   Corvane's 2 s cast and yell (Trample, Sweep, Smash; never the same twice in a row), then the
 *                    Ravenian's own 2 s marker: Trample a 4 yd line from the Ravenian through a random non-tank to the
 *                    vault's wall (35% / 50%), Sweep a 120 degree 12 yd frontal toward his tank (45% / 60%), Smash a
 *                    6 yd ring on a random non-tank (30% / 40% and Weakened). Phase 1 first at 8 s, every 12 s
 *                    (heroic: in pairs, the second called as the first's marker appears); phase 2 every 15 s.
 *   RV5 Transition   at 50%: Mend Construct from the seat (cannot be stopped; heals 10% / 15%), yell 4, then the
 *                    teleport to his landing (128, -1) (at least 15 yd from the Ravenian) and he is attackable.
 *   RV6 Unbound      phase 2: a kicked order makes the Ravenian do the move on Corvane (8% of his health) and stand 2 s
 *                    (the leash snaps and comes back).
 *   RV7 Driven       heroic phase 2: an order nobody kicks gives the Ravenian +10% damage for the fight (uncapped).
 *   RV8 Mend         phase 2: a 3 s kickable heal, 10 s after landing then every 20 s, 6% / 10% (the must-kick).
 *   RV9 Shadow Bolt  Corvane's filler between orders and heals, 15% / 20% Shadow.
 *   RV10 Bereaved    whichever falls first enrages the other: +10% damage every 5 s, uncapped; the unleashed Ravenian
 *                    does a random order on his own every 10 s. The encounter ends when both are dead.
 *   RV11 Cleave      Sundering Cleave on the tank only (a copy of 25174 with one target), the stock timers.
 *   Arena            RavenianArena() with LeashOptions (no grips). The vault's gate is the instance's door data.
 *
 * Who owns what. The Ravenian is the BossAI on BOSS_RAVENIAN and the registry encounter's owner; his AI runs the
 * fight (RavenianFight) and commands Corvane, his summon (outside BossAI's summon list, so the Ravenian's death does
 * not despawn him). Corvane's AI only reports his casts and his death back.
 *
 * The Ravenian never dies first (user ruling 1, 2026-11-08; RavenianLogic.h Pair). Lethal damage while Corvane stands
 * leaves him at 1 HP, collapsed: inert, not selectable, not attackable, his registry encounter re-described with
 * Corvane as the only target. Corvane fights on alone (his bolts, his Bereaved stacks); his death kills the collapsed
 * Ravenian for real on the Ravenian's next tick (Corvane's killer, else the loot recipient, as the killer), so the
 * credit, the loot, the Passing Grades and DONE land together. A wipe while he is collapsed (Corvane alone finds nobody
 * left), or Corvane gone without a death, makes the Ravenian evade: both reset, nothing respawns. A forced death (a GM
 * kill past the collapse) ends the encounter as it stands and sends Corvane away.
 *
 * Examiner mode (S13, the Graduate Exam): npc_sc_examiner_ravenian (300551, 60k) runs the same fight at heroic values
 * on any map and summons its own examiner Corvane npc_sc_examiner_corvane (300552, 20k); no boss state, no Passing
 * Grade, no text; the same collapse, and its registry encounter ends at its evade and death. Registered once wave C
 * binds (kWaveCBound).
 *
 * Solo lesson (S11's detention, SoloLesson.h): RavenianVaultLesson, registered for Classroom::RavenianVault. The echo
 * (300545, S11's entry; summoned by the lesson when its template exists) calls 3 orders on the student, each a 2 s bar
 * then a 2 s marker; any hit fails it (15% / 25% plus Weakened).
 *
 * Every timer runs on the AI's own clock (RavenianLogic.h Timeline), never on BossAI's scheduler that a cast bar
 * pauses; Corvane's cast results are queued and handled on the Ravenian's next tick (never inside the cast's own
 * callback). Every firing logs one INFO line "scholo ravenian <mechanic> ..." (module.dungeonbosses); `.dbtest scholo
 * ravenian <mechanic>` fires one.
 */

#include "ArenaGuard.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "RavenianLogic.h"
#include "Random.h"
#include "ScholomanceKit.h"
#include "ScholomanceRework.h"
#include "ScholomanceTestCommand.h"
#include "ScriptedCreature.h"
#include "SoloLesson.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <list>
#include <memory>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;
using namespace ScholoRavenian;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;

namespace
{
    char const* const kBossLogName = "ravenian";
    char const* const kExaminerLogName = "ravenian-examiner";
    char const* const kLessonLogName = "detention-ravenian-vault";
    int32 constexpr kGuidRavenian = 0x52560001;         // Corvane's SetGUID id: his Ravenian ("RV")
    uint32 constexpr kTestLessonOwnerEntry = 12999;     // stock World Invisible Trigger: the `.dbtest` lesson's owner
    uint32 constexpr kTestLessonOwnerMs = 20000;
    uint32 constexpr kOrphanMs = 2000;                  // Corvane with no Ravenian this long: he leaves too

    bool IsCorvaneEntry(uint32 entry)
    {
        return entry == NPC_SC_MASTER_CORVANE || entry == NPC_SC_EXAMINER_CORVANE;
    }

    // Corvane's guard (used once he stands alone): only the no-target leash. He never moves (rooted, passive), so
    // nothing to hold, switch or pull back.
    DungeonKit::ArenaGuardOptions CorvaneLeash(bool examiner)
    {
        DungeonKit::ArenaGuardOptions o = LeashOptions(examiner ? "corvane-examiner" : "corvane");
        o.holdWhileVictimOff = false;
        o.switchWhenVictimOff = false;
        o.evadeWhenBossOff = false;
        return o;
    }

    bool IsExaminerEntry(uint32 entry)
    {
        return entry == NPC_SC_EXAMINER_RAVENIAN || entry == NPC_SC_EXAMINER_CORVANE;
    }

    // Heroic values for this unit: a heroic map, or an examiner anywhere.
    bool HeroicFor(Unit const* unit)
    {
        return unit && HeroicValues(DungeonKit::IsHeroicMap(unit), IsExaminerEntry(unit->GetEntry()));
    }

    Position ToPos(Point4 const& p)
    {
        return Position(p.x, p.y, p.z, p.o);
    }

    // The vault's walls for Trample (RavenianLogic.h VaultWalls), built once.
    Arena const& Walls()
    {
        static Arena const walls = VaultWalls();
        return walls;
    }

    // Driven and Bereaved: the damage factor of `unit`'s stacks (multiplied, as the engine does on his melee).
    float StackScale(Unit const* unit)
    {
        return StackedDamageScale(DungeonKit::Stacks(unit, SPELL_RV_DRIVEN),
            DungeonKit::Stacks(unit, SPELL_RV_BEREAVED));
    }

    void SetCreatureHealth(Creature* me, uint32 health)
    {
        // Create health is the base the engine rebuilds max health from (the Deadmines hard mode's SetBossHealth).
        me->SetCreateHealth(health);
        me->SetStatFlatModifier(UNIT_MOD_HEALTH, BASE_VALUE, static_cast<float>(health));
        me->UpdateMaxHealth();
        me->SetHealth(me->GetMaxHealth());
    }

    // The point `dist` yd from `from` along `bearing` (absolute), stopped at the first wall.
    Position ReachablePoint(Unit* from, float bearing, float dist)
    {
        Position at = from->GetFirstCollisionPosition(dist, bearing - from->GetOrientation());
        at.SetOrientation(bearing);
        return at;
    }

    // One order's marker (RV1-RV3), under `owner`'s encounter. `source` is where the move starts (the Ravenian, or
    // the lesson's echo spot) and faces where the move goes; `sourceUnit` (may be null) anchors the Sweep so it turns
    // with him and spares his tank (the fight); without it the Sweep is a fixed cone that spares nobody (the lesson).
    // `target` is the Trample's and the Smash's player. `weakenedAll`: every move costs Weakened (the lesson's rule),
    // else only the Smash (ruling 21).
    MechanicHandle PlaceOrder(Unit* owner, Unit* sourceUnit, Position const& source, Order o, Unit* target, float pct,
        bool weakenedAll)
    {
        Milliseconds const warn(kOrderMarkerMs);
        switch (o)
        {
            case Order::Trample:
            {
                if (!target)
                    return {};
                DungeonKit::LineStrikeSpec spec;
                spec.width = kTrampleWidth;
                spec.overrun = kTrampleOverrun;
                spec.warn = warn;
                spec.pct = pct;
                spec.spellId = SPELL_RV_TRAMPLE;
                spec.weakened = weakenedAll;
                spec.tag = TAG_TRAMPLE;
                spec.clip = &Walls();
                return DungeonKit::LineStrike(owner, source, target->GetPosition(), spec).handle;
            }
            case Order::Sweep:
            {
                MechanicRef ref = sourceUnit
                    ? Mechanic::Cone(owner, sourceUnit, kSweepAngle, kSweepLength, warn, BossMechanics::TankExempt::Yes)
                    : Mechanic::Zone(owner, BossMechanics::Shapes::Cone(source, kSweepAngle, kSweepLength), warn);
                ref.Damage(pct).Spell(SPELL_RV_SWEEP).Tag(TAG_SWEEP);
                if (weakenedAll)
                    ref.Weakened();
                return ref.Handle();
            }
            case Order::Smash:
            {
                if (!target)
                    return {};
                MechanicRef ref = Mechanic::Circle(owner, target->GetPosition(), kSmashRadius, warn);
                ref.Damage(pct).Spell(SPELL_RV_SMASH).Weakened().Tag(TAG_SMASH);
                return ref.Handle();
            }
        }
        return {};
    }

    std::optional<Order> OrderByName(std::string_view name)
    {
        for (std::size_t i = 0; i < kOrderCount; ++i)
            if (name == OrderName(Order(i)))
                return Order(i);
        return std::nullopt;
    }
}

class RavenianFight;

// What Corvane's AI talks to: the Ravenian's AI (the boss or his examiner).
class RavenianDirector
{
public:
    virtual ~RavenianDirector() = default;
    virtual RavenianFight& Fight() = 0;
};

namespace
{
    RavenianDirector* DirectorOf(Creature* ravenian)
    {
        return ravenian && ravenian->IsAIEnabled ? dynamic_cast<RavenianDirector*>(ravenian->AI()) : nullptr;
    }
}

struct npc_sc_master_corvane;

// ---- The fight, run by the Ravenian's AI (the boss or his examiner) -------------------------------------------------

class RavenianFight
{
public:
    explicit RavenianFight(bool examiner) : _examiner(examiner) { }

    bool Examiner() const { return _examiner; }
    bool Heroic() const { return _heroic; }
    bool Engaged() const { return _engaged; }
    bool Standing() const { return _standMs > 0; }
    Stage GetStage() const { return _stage; }
    uint32 CorvaneEntry() const { return _examiner ? uint32(NPC_SC_EXAMINER_CORVANE) : uint32(NPC_SC_MASTER_CORVANE); }
    char const* LogName() const { return _examiner ? kExaminerLogName : kBossLogName; }

    Creature* Corvane(Creature const* rav) const
    {
        return rav && !_corvane.IsEmpty() ? ObjectAccessor::GetCreature(*rav, _corvane) : nullptr;
    }

    // Out of combat, every tick: Corvane on his seat (a fresh one after a wipe), the leash up.
    void Idle(Creature* rav, uint32 diff)
    {
        _idleMs += diff;
        if (_idleMs < kLeashCheckMs)
            return;
        _idleMs = 0;
        Creature* corv = Corvane(rav);
        if (!corv || !corv->IsAlive())
            corv = SummonCorvane(rav);
        if (corv)
            KeepLeash(rav, corv);
    }

    void DespawnCorvane(Creature* rav)
    {
        if (Creature* corv = Corvane(rav))
            corv->DespawnOrUnsummon();
        _corvane.Clear();
    }

    void Engage(Creature* rav)
    {
        ClearState(rav);
        ResetPair();
        _heroic = HeroicValues(DungeonKit::IsHeroicMap(rav), _examiner);
        _engaged = true;
        _stage = Stage::Leash;
        _timeline.Start(urand(kCleaveFirstMinMs, kCleaveFirstMaxMs));
        Creature* corv = Corvane(rav);
        if (!corv || !corv->IsAlive())
            corv = SummonCorvane(rav);
        if (corv)
        {
            Mechanic::TrackUnit(rav, corv);
            Say(corv, YELL_CORVANE_AGGRO);
            KeepLeash(rav, corv);
        }
        Describe(rav);
        DungeonKit::LogMechanic(kLogDungeon, LogName(), "engage", Acore::StringFormat("heroic={} corvane={}",
            _heroic ? 1 : 0, corv ? 1 : 0));
    }

    // After UpdateVictim and the arena: the fight's clock, Corvane's reports, the beats.
    void Update(Creature* rav, uint32 diff)
    {
        if (!_engaged)
            return;
        _timeline.Advance(diff);
        UpdateStand(rav, diff);

        Creature* corv = Corvane(rav);
        if (corv && !corv->IsAlive())
            corv = nullptr;
        if (!_corvaneDead && !corv)
            CorvaneGone(rav, "gone");
        HandleReports(rav, corv);

        if (_timeline.Due(Beat::Leash))
        {
            _timeline.Set(Beat::Leash, kLeashCheckMs);
            if (corv)
                KeepLeash(rav, corv);
        }

        switch (_stage)
        {
            case Stage::Leash:
                if (TransitionDue(_stage, rav->GetHealthPct()))
                {
                    if (corv && !Busy(corv))
                        BeginTransition(rav, corv);
                }
                else if (_pairDue && corv && !Busy(corv))
                    CallOrder(corv, true);
                else if (_timeline.Due(Beat::Order) && corv && !Busy(corv))
                    CallOrder(corv, false);
                break;
            case Stage::Transition:
                if (_landDue || _timeline.now >= _transitionAt + kTransitionFallbackMs)
                    Land(rav, corv, _landDue ? "mended" : "fallback");
                break;
            case Stage::Hand:
                if (corv && !Busy(corv))
                {
                    if (_timeline.Due(Beat::Order))
                        CallOrder(corv, false);
                    else if (_timeline.Due(Beat::Mend))
                        CallMend(rav, corv);
                    else if (_timeline.Due(Beat::Bolt))
                        CallBolt(rav, corv);
                }
                break;
            case Stage::Bereaved:
                if (_timeline.Due(Beat::Bereaved))
                {
                    _timeline.Set(Beat::Bereaved, kBereavedEveryMs);
                    uint32 const stacks = DungeonKit::AddStacks(rav, SPELL_RV_BEREAVED, 1, rav);
                    DungeonKit::LogMechanic(kLogDungeon, LogName(), "bereaved", Acore::StringFormat("unit=ravenian "
                        "stacks={}", stacks));
                }
                if (_timeline.Due(Beat::Order) && !Standing())
                    UnleashedOrder(rav, nullptr);
                break;
        }

        if (_timeline.Due(Beat::Cleave))
            Cleave(rav);
    }

    // Reset, evade: every marker cancelled, the stand and the stacks off, a collapse undone (full health again).
    // Corvane stays (the caller decides).
    void Cleanup(Creature* rav)
    {
        ClearState(rav);
        if (rav)
        {
            if (_pair == Pair::Collapsed)
                Uncollapse(rav, true);
            RemoveStacks(rav);
        }
        ResetPair();
    }

    bool Collapsed() const { return _pair == Pair::Collapsed; }

    // Every hit on the Ravenian (his AI's DamageTaken): what lands. Lethal while Corvane stands collapses him.
    uint32 RavenianDamage(Creature* rav, uint32 damage)
    {
        if (_pair == Pair::Both && !_engaged)
            return damage;      // out of the fight (a `.dbtest`, a GM): stock rules
        Creature* corv = Corvane(rav);
        bool const corvaneStanding = corv && corv->IsAlive() && !_corvaneDead;
        RavenianHit const hit = ScholoRavenian::RavenianDamage(_pair, rav->GetHealth(), damage, corvaneStanding);
        if (hit.collapse)
        {
            // The state now (every later hit lands nothing); the rest on his next tick, off the damage's own call.
            _pair = Pair::Collapsed;
            _collapseDue = true;
        }
        return hit.damage;
    }

    // The collapsed Ravenian's tick (his AI, in place of the fight): the collapse itself first, then Hold, Kill
    // (KillCollapsed) or Reset (his evade).
    CollapsedStep UpdateCollapsed(Creature* rav)
    {
        if (_collapseDue)
        {
            _collapseDue = false;
            Collapse(rav);
        }
        Creature* corv = Corvane(rav);
        bool const died = _corvaneDead || (corv && !corv->IsAlive());
        return NextCollapsedStep(died, _wipeDue, corv != nullptr);
    }

    // Corvane alone found nobody left (his wipe): the Ravenian resets both on his next tick.
    void RequestReset()
    {
        _wipeDue = true;
    }

    // Corvane is dead: the collapsed Ravenian dies for real. The killer: Corvane's (a pet's owner), else the
    // Ravenian's loot recipient, else any living player on the map; the kill carries the credit, the loot and DONE.
    void KillCollapsed(Creature* rav)
    {
        Unit* killer = _corvaneKiller.IsEmpty() ? nullptr : ObjectAccessor::GetUnit(*rav, _corvaneKiller);
        Player* player = killer ? killer->GetCharmerOrOwnerPlayerOrPlayerItself() : nullptr;
        if (!player || !player->IsInMap(rav))
            player = rav->GetLootRecipient();
        if (!player || !player->IsInMap(rav))
        {
            player = nullptr;
            for (auto const& ref : rav->GetMap()->GetPlayers())
                if (Player* p = ref.GetSource())
                    if (p->IsAlive() && !p->IsGameMaster())
                    {
                        player = p;
                        break;
                    }
        }
        DungeonKit::LogMechanic(kLogDungeon, LogName(), "ravenian-kill", Acore::StringFormat("killer={}",
            player ? player->GetName() : "-"));
        Uncollapse(rav, false);
        _pair = Pair::Over;
        Unit::Kill(player ? static_cast<Unit*>(player) : static_cast<Unit*>(rav), rav);
    }

    // ---- reports from Corvane's AI (queued: handled on the Ravenian's next tick) ------------------------------------

    void CorvaneCast(uint32 spellId, bool completed)
    {
        if (!_engaged || _selfCancel)
            return;
        if (spellId == SPELL_RV_LEASH || spellId == SPELL_RV_TELEPORT || spellId == SPELL_RV_SHADOW_BOLT)
            return;
        _reports.push_back({ spellId, completed });
    }

    // Corvane died (`killer` may be null). Collapsed Ravenian: he dies for real on his next tick (KillCollapsed).
    // Both standing: RV10 on the Ravenian.
    void CorvaneDied(Creature* rav, Unit* killer)
    {
        if (_corvaneDead)
            return;
        if (_pair == Pair::Collapsed)
        {
            _corvaneDead = true;
            _corvaneKiller = killer ? killer->GetGUID() : ObjectGuid::Empty;
            DungeonKit::LogMechanic(kLogDungeon, LogName(), "corvane-death", "last=1 ravenian=collapsed");
            return;
        }
        if (!rav || !rav->IsAlive())
        {
            _corvaneDead = true;
            DungeonKit::LogMechanic(kLogDungeon, LogName(), "corvane-death", "last=1");
            return;
        }
        CorvaneGone(rav, "died");
    }

    // The Ravenian died: the collapse's kill (Corvane already dead), Corvane dead first (RV10), or a forced death past
    // the collapse (a GM kill), which ends the encounter as it stands: Corvane leaves.
    void RavenianDied(Creature* rav)
    {
        Creature* corv = Corvane(rav);
        if (corv && corv->IsAlive() && !_corvaneDead)
        {
            DungeonKit::LogMechanic(kLogDungeon, LogName(), "ravenian-death", "forced=1 corvane=sent-away");
            DespawnCorvane(rav);
        }
        ClearState(rav);
        _pair = Pair::Over;
    }

    // ---- `.dbtest` hooks --------------------------------------------------------------------------------------------

    // An order now: Corvane calls it (in combat, alive), else the Ravenian does it at once on `forced`.
    bool ForceOrder(Creature* rav, Order o, Player* forced)
    {
        if (_pair != Pair::Both)
            return false;       // collapsed or dead: no moves
        Creature* corv = Corvane(rav);
        if (_engaged && corv && corv->IsAlive() && !Busy(corv) && (_stage == Stage::Leash || _stage == Stage::Hand))
            return StartOrder(corv, o, false);
        PerformOrder(rav, o, forced, "test");
        return true;
    }

    bool ForceTransition(Creature* rav)
    {
        Creature* corv = Corvane(rav);
        if (!_engaged || _stage != Stage::Leash || !corv || Busy(corv))
            return false;
        BeginTransition(rav, corv);
        return true;
    }

    bool ForceMend(Creature* rav)
    {
        Creature* corv = Corvane(rav);
        if (!_engaged || _stage != Stage::Hand || !corv || Busy(corv))
            return false;
        CallMend(rav, corv);
        return true;
    }

    bool ForceUnbound(Creature* rav)
    {
        Creature* corv = Corvane(rav);
        if (!_engaged || _stage != Stage::Hand || !corv)
            return false;
        Unbound(rav, corv, _lastOrder.value_or(Order::Smash));
        return true;
    }

    std::string State(Creature const* rav) const
    {
        static char const* const stages[] = { "?", "leash", "transition", "hand", "bereaved" };
        return Acore::StringFormat("engaged={} heroic={} examiner={} stage={} t={}ms next order/mend/bolt/cleave/"
            "bereaved={}/{}/{}/{}/{} last={} pair={} stand={}ms corvane={} dead={} driven={} bereaved={} live={} "
            "collapse={}",
            _engaged ? 1 : 0, _heroic ? 1 : 0, _examiner ? 1 : 0, stages[std::size_t(_stage)], _timeline.now,
            Next(Beat::Order), Next(Beat::Mend), Next(Beat::Bolt), Next(Beat::Cleave), Next(Beat::Bereaved),
            _lastOrder ? OrderName(*_lastOrder) : "-", _pairDue ? 1 : 0, _standMs, Corvane(rav) ? 1 : 0,
            _corvaneDead ? 1 : 0, rav ? DungeonKit::Stacks(rav, SPELL_RV_DRIVEN) : 0,
            rav ? DungeonKit::Stacks(rav, SPELL_RV_BEREAVED) : 0, _live.size(), uint32(_pair));
    }

private:
    struct Report
    {
        uint32 spellId = 0;
        bool completed = false;
    };

    int64 Next(Beat b) const
    {
        return _timeline.At(b) == kNever ? -1 : int64(_timeline.At(b)) - int64(_timeline.now);
    }

    void ClearState(Creature* rav)
    {
        CancelLive(rav);
        if (_standMs && rav)
            rav->SetControlled(false, UNIT_STATE_ROOT);
        _standMs = 0;
        _timeline = Timeline{};
        _engaged = false;
        _stage = Stage::Leash;
        _lastOrder.reset();
        _pendingOrder.reset();
        _pairPending = false;
        _pairDue = false;
        _landDue = false;
        _corvaneDead = false;
        _transitionAt = 0;
        _reports.clear();
    }

    void ResetPair()
    {
        _pair = Pair::Both;
        _wipeDue = false;
        _collapseDue = false;
        _corvaneKiller.Clear();
    }

    static void RemoveStacks(Creature* rav)
    {
        rav->RemoveAurasDueToSpell(SPELL_RV_DRIVEN);
        rav->RemoveAurasDueToSpell(SPELL_RV_BEREAVED);
        rav->RemoveAurasDueToSpell(SPELL_RV_UNBOUND);
    }

    // Lethal damage while Corvane stands (user ruling 1): the Ravenian lies at 1 HP, inert, not selectable, not
    // attackable; Corvane lands if he had not yet and fights on alone (Bereaved); the registry encounter stays (the
    // boss state stays IN_PROGRESS, the gate shut) with Corvane as the only target.
    void Collapse(Creature* rav)
    {
        Creature* corv = Corvane(rav);
        bool const reported = _corvaneDead;                                     // he may have died the same moment
        bool const corvaneDead = reported || !corv || !corv->IsAlive();
        CancelLive(rav);
        if (!corvaneDead)
        {
            Say(corv, YELL_CORVANE_RAVENIAN_DIES);
            _selfCancel = true;
            corv->InterruptNonMeleeSpells(true);
            _selfCancel = false;
            if (_stage == Stage::Leash || _stage == Stage::Transition)
                Land(rav, corv, "ravenian-collapsed");
        }
        ClearState(rav);
        _corvaneDead = reported || (corv && !corv->IsAlive());     // ClearState forgot it; a corpse counts too
        RemoveStacks(rav);

        rav->InterruptNonMeleeSpells(false);
        rav->AttackStop();
        rav->SetReactState(REACT_PASSIVE);
        rav->StopMoving();
        rav->GetMotionMaster()->Clear();
        rav->GetMotionMaster()->MoveIdle();
        rav->SetControlled(true, UNIT_STATE_ROOT);
        rav->SetUnitFlag(UnitFlags(UNIT_FLAG_NOT_SELECTABLE | UNIT_FLAG_NON_ATTACKABLE));
        rav->SetStandState(UNIT_STAND_STATE_DEAD);
        rav->SetRegeneratingHealth(false);
        rav->RemoveEvadeAuras();        // nothing ticks on a body that cannot be hit
        Describe(rav);
        if (!corvaneDead)
            BecomeAlone(corv);
        DungeonKit::LogMechanic(kLogDungeon, LogName(), "ravenian-collapse", Acore::StringFormat("health={} "
            "corvane={}", rav->GetHealth(), corvaneDead ? "dead" : "alone"));
    }

    // The collapse undone: before the real kill (`wipe` false: the body must be lootable and selectable), or on a
    // wipe (`wipe` true: full health, back on his feet; his evade takes him home).
    static void Uncollapse(Creature* rav, bool wipe)
    {
        rav->RemoveUnitFlag(UnitFlags(UNIT_FLAG_NOT_SELECTABLE | UNIT_FLAG_NON_ATTACKABLE));
        rav->SetStandState(UNIT_STAND_STATE_STAND);
        rav->SetControlled(false, UNIT_STATE_ROOT);
        rav->SetRegeneratingHealth(rav->GetCreatureTemplate()->RegenHealth);
        if (!wipe)
            return;
        rav->SetReactState(REACT_AGGRESSIVE);
        if (rav->IsAlive())
            rav->SetFullHealth();
    }

    void CancelLive(Creature* rav)
    {
        if (rav)
            for (MechanicHandle const& handle : _live)
                Mechanic::Cancel(rav, handle);
        _live.clear();
    }

    void Say(Creature* who, uint8 group, WorldObject const* target = nullptr)
    {
        if (!_examiner && who && who->IsAIEnabled && who->AI())
            who->AI()->Talk(group, target);
    }

    static bool Busy(Creature const* corv)
    {
        return corv->GetCurrentSpell(CURRENT_GENERIC_SPELL) != nullptr;
    }

    Creature* SummonCorvane(Creature* rav)
    {
        if (Creature* old = Corvane(rav))
            old->DespawnOrUnsummon();
        _corvane.Clear();
        // Never two: a Corvane left over from another Ravenian AI (a respawn) leaves first.
        std::list<Creature*> stale;
        rav->GetCreatureListWithEntryInGrid(stale, CorvaneEntry(), 80.f);
        for (Creature* old : stale)
            old->DespawnOrUnsummon();
        Creature* corv = rav->SummonCreature(CorvaneEntry(), ToPos(kCorvaneSeat), TEMPSUMMON_MANUAL_DESPAWN);
        if (!corv)
        {
            DungeonKit::LogMechanic(kLogDungeon, LogName(), "corvane-summon-failed");
            return nullptr;
        }
        _corvane = corv->GetGUID();
        if (corv->IsAIEnabled && corv->AI())
            corv->AI()->SetGUID(rav->GetGUID(), kGuidRavenian);
        DungeonKit::LogMechanic(kLogDungeon, LogName(), "corvane-seated", Acore::StringFormat("at=({:.1f}, {:.1f}, "
            "{:.1f})", corv->GetPositionX(), corv->GetPositionY(), corv->GetPositionZ()));
        return corv;
    }

    // The beam from Corvane to the Ravenian's back: a channel his casts do not break (ALLOW_ACTION_DURING_CHANNEL);
    // cast again whenever it is down (a teleport, the Unbound snap, its end).
    void KeepLeash(Creature* rav, Creature* corv)
    {
        if (!rav->IsAlive() || !corv->IsAlive() || Standing() || corv->GetCurrentSpell(CURRENT_CHANNELED_SPELL))
            return;
        corv->CastSpell(rav, SPELL_RV_LEASH, true);
    }

    void UpdateStand(Creature* rav, uint32 diff)
    {
        if (!_standMs)
            return;
        if (diff < _standMs)
        {
            _standMs -= diff;
            return;
        }
        _standMs = 0;
        rav->SetControlled(false, UNIT_STATE_ROOT);
    }

    // Boss data: phase 1 the Ravenian alone (Corvane ignored: unselectable anyway); phase 2 both, killed together,
    // with Mend Construct (must) and the orders (bonus; heroic counts them: Driven) on the interrupt list.
    void Describe(Creature* rav)
    {
        BossMechanics::Descriptor d;
        uint32 const corvane = CorvaneEntry();
        if (_pair == Pair::Collapsed)
        {
            // The collapsed Ravenian is no target; Corvane alone, nothing to kick (no Mend, no orders).
            d.phase = 3;
            d.targets.push_back(BossMechanics::TargetEntry(corvane, 1));
            d.ignores.emplace_back(rav->GetEntry());
        }
        else if (_stage == Stage::Leash || _stage == Stage::Transition)
        {
            d.phase = 1;
            d.ignores.emplace_back(corvane, BossMechanics::Condition::Phase(1));
        }
        else
        {
            d.phase = 2;
            d.targets.push_back(BossMechanics::TargetEntry(rav->GetEntry(), 1).KillTogether(corvane, kKillTogetherPct));
            d.targets.push_back(BossMechanics::TargetEntry(corvane, 1).KillTogether(rav->GetEntry(), kKillTogetherPct));
            if (_stage == Stage::Hand)
            {
                d.interrupts.emplace_back(corvane, SPELL_RV_MEND, 3, Milliseconds(kMendEveryMs));
                for (std::size_t i = 0; i < kOrderCount; ++i)
                    d.interrupts.emplace_back(corvane, OrderCastSpell(Order(i)), 2, Milliseconds(kHandOrderEveryMs));
            }
        }
        Mechanic::Describe(rav, std::move(d));
    }

    // RV4: Corvane calls the next order (never the last one again). `pairFollow`: the second of a heroic pair, off the
    // cadence.
    bool CallOrder(Creature* corv, bool pairFollow)
    {
        Order const o = NextOrder(_lastOrder, urand(0, 0xFFFF));
        return StartOrder(corv, o, pairFollow);
    }

    bool StartOrder(Creature* corv, Order o, bool pairFollow)
    {
        _pairDue = false;
        SpellCastResult const result = corv->CastSpell(corv, OrderCastSpell(o), false);
        if (result != SPELL_CAST_OK)
        {
            if (!pairFollow)
                _timeline.Retry(Beat::Order);
            DungeonKit::LogMechanic(kLogDungeon, LogName(), "order-call-failed", Acore::StringFormat("order={} "
                "result={}", OrderName(o), uint32(result)));
            return false;
        }
        _lastOrder = o;
        _pendingOrder = o;
        _orderStage = _stage;
        if (!pairFollow)
        {
            _timeline.Set(Beat::Order, _stage == Stage::Hand ? kHandOrderEveryMs : kLeashOrderEveryMs);
            _pairPending = _stage == Stage::Leash && kPairedOrders(_heroic);
        }
        else
            _pairPending = false;
        Say(corv, OrderYell(o));
        DungeonKit::LogMechanic(kLogDungeon, LogName(), "order-call", Acore::StringFormat("order={} stage={} pair={}",
            OrderName(o), uint32(_stage), pairFollow ? 2 : (_pairPending ? 1 : 0)));
        return true;
    }

    // Corvane's casts ended (queued by his AI; handled here, off the cast's own callback).
    void HandleReports(Creature* rav, Creature* corv)
    {
        if (_reports.empty())
            return;
        std::vector<Report> reports;
        reports.swap(_reports);
        for (Report const& r : reports)
        {
            if (std::optional<Order> const o = OrderOfCast(r.spellId))
                OrderEnded(rav, corv, *o, r.completed);
            else if (r.spellId == SPELL_RV_MEND_TRANSITION)
            {
                _landDue = true;
                DungeonKit::LogMechanic(kLogDungeon, LogName(), "transition-mend", r.completed ? "landed" : "lost");
            }
            else if (r.spellId == SPELL_RV_MEND)
                DungeonKit::LogMechanic(kLogDungeon, LogName(), "mend", Acore::StringFormat("{} pct={:.0f}",
                    r.completed ? "landed" : "interrupted", kMendPct(_heroic)));
        }
    }

    void OrderEnded(Creature* rav, Creature* corv, Order o, bool completed)
    {
        if (!_pendingOrder || *_pendingOrder != o)
            return;
        _pendingOrder.reset();
        switch (OrderResult(_orderStage, completed, _heroic))
        {
            case OrderOutcome::PerformedDriven:
            {
                PerformOrder(rav, o, nullptr, "order");
                uint32 const stacks = DungeonKit::AddStacks(rav, SPELL_RV_DRIVEN, 1, rav);
                DungeonKit::LogMechanic(kLogDungeon, LogName(), "driven", Acore::StringFormat("order={} stacks={}",
                    OrderName(o), stacks));
                break;
            }
            case OrderOutcome::Performed:
                PerformOrder(rav, o, nullptr, "order");
                break;
            case OrderOutcome::Unbound:
                if (corv)
                    Unbound(rav, corv, o);
                break;
            case OrderOutcome::Lost:
                DungeonKit::LogMechanic(kLogDungeon, LogName(), "order-lost", Acore::StringFormat("order={}",
                    OrderName(o)));
                break;
        }
        if (_pairPending && completed && _stage == Stage::Leash)
            _pairDue = true;
        _pairPending = false;
    }

    // RV1-RV3: the Ravenian does the move (on the group): his own 2 s marker, scaled by his Driven and Bereaved.
    void PerformOrder(Creature* rav, Order o, Player* forced, char const* why)
    {
        float const pct = OrderPct(o, _heroic || HeroicFor(rav)) * StackScale(rav);
        Player* target = forced;
        if (!target && o != Order::Sweep)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.tankIfAlone = true;        // a lone tank (a test) still gets the move
            target = DungeonKit::PickPlayer(rav, rule);
        }
        if (o != Order::Sweep && !target)
        {
            DungeonKit::LogMechanic(kLogDungeon, LogName(), "order-no-target", Acore::StringFormat("order={}",
                OrderName(o)));
            return;
        }
        MechanicHandle const handle = PlaceOrder(rav, rav, rav->GetPosition(), o, target, pct, false);
        if (handle.IsValid())
            _live.push_back(handle);
        PruneLive();
        DungeonKit::LogMechanic(kLogDungeon, LogName(), OrderName(o), Acore::StringFormat("{} target={} pct={:.1f} "
            "stage={}", why, target ? target->GetName() : "-", pct, uint32(_stage)));
    }

    // Handles of markers long resolved are only ids; keep the list short.
    void PruneLive()
    {
        if (_live.size() > 8)
            _live.erase(_live.begin(), _live.begin() + std::ptrdiff_t(_live.size() - 8));
    }

    // RV6: a kicked order: the move on Corvane (8% of his health) and the Ravenian stands 2 s; the leash snaps.
    void Unbound(Creature* rav, Creature* corv, Order o)
    {
        if (!rav->IsAlive() || !corv->IsAlive())
            return;
        rav->CastSpell(corv, SPELL_RV_UNBOUND_STRIKE, true);
        rav->CastSpell(rav, SPELL_RV_UNBOUND, true);
        _standMs = kUnboundStandMs;
        rav->StopMoving();
        rav->SetControlled(true, UNIT_STATE_ROOT);
        corv->InterruptSpell(CURRENT_CHANNELED_SPELL, false);
        DungeonKit::LogMechanic(kLogDungeon, LogName(), "unbound", Acore::StringFormat("order={} corvane={}/{}",
            OrderName(o), corv->GetHealth(), corv->GetMaxHealth()));
    }

    // RV5: Mend Construct from the seat (no interrupt flags; he is out of reach anyway), yell 4; Land follows.
    void BeginTransition(Creature* rav, Creature* corv)
    {
        _stage = Stage::Transition;
        _transitionAt = _timeline.now;
        _timeline.Stop(Beat::Order);
        _pairDue = false;
        _pairPending = false;
        Say(corv, YELL_CORVANE_TRANSITION);
        SpellCastResult const result = corv->CastSpell(rav, SPELL_RV_MEND_TRANSITION, false);
        if (result != SPELL_CAST_OK)
            _landDue = true;
        DungeonKit::LogMechanic(kLogDungeon, LogName(), "transition", Acore::StringFormat("health={:.1f} heal={:.0f} "
            "result={}", rav->GetHealthPct(), kTransitionHealPct(_heroic), uint32(result)));
    }

    // RV5: the teleport to the landing (at least 15 yd from the Ravenian), attackable, in combat; phase 2.
    void Land(Creature* rav, Creature* corv, char const* why);

    void CallMend(Creature* rav, Creature* corv)
    {
        SpellCastResult const result = corv->CastSpell(rav, SPELL_RV_MEND, false);
        if (result != SPELL_CAST_OK)
        {
            _timeline.Retry(Beat::Mend);
            return;
        }
        _timeline.Set(Beat::Mend, kMendEveryMs);
        Mechanic::NoteNextCastIn(corv, SPELL_RV_MEND, Milliseconds(kMendEveryMs));
        DungeonKit::LogMechanic(kLogDungeon, LogName(), "mend-cast", Acore::StringFormat("ravenian={:.1f}%",
            rav->GetHealthPct()));
    }

    // RV9: between orders and heals, a bolt at a random player in his range (the Ravenian's threat list).
    void CallBolt(Creature* rav, Creature* corv)
    {
        if (!BoltFits(_timeline.now, _timeline.At(Beat::Order), _timeline.At(Beat::Mend)))
        {
            _timeline.Retry(Beat::Bolt);
            return;
        }
        Player* target = BoltTarget(rav, corv);
        if (!target)
        {
            _timeline.Retry(Beat::Bolt);
            return;
        }
        if (corv->CastSpell(target, SPELL_RV_SHADOW_BOLT, false) == SPELL_CAST_OK)
            _timeline.Set(Beat::Bolt, kShadowBoltEveryMs);
        else
            _timeline.Retry(Beat::Bolt);
    }

    static Player* BoltTarget(Creature* picker, Creature* corv)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        std::vector<Player*> candidates = DungeonKit::PickPlayers(picker, rule, 10);
        candidates.erase(std::remove_if(candidates.begin(), candidates.end(), [corv](Player* p)
        {
            return !corv->IsWithinDistInMap(p, kShadowBoltRange) || !corv->IsWithinLOSInMap(p);
        }), candidates.end());
        if (candidates.empty())
            return nullptr;
        return candidates[urand(0, uint32(candidates.size()) - 1)];
    }

    // RV10: the unleashed Ravenian's own order, every 10 s (no cast; the marker is the warning).
    void UnleashedOrder(Creature* rav, Player* forced)
    {
        Order const o = NextOrder(_lastOrder, urand(0, 0xFFFF));
        _lastOrder = o;
        _timeline.Set(Beat::Order, kUnleashedOrderEveryMs);
        PerformOrder(rav, o, forced, "unleashed");
    }

    void Cleave(Creature* rav)
    {
        Unit* victim = rav->GetVictim();
        if (!victim || Standing() || !rav->IsWithinMeleeRange(victim))
        {
            _timeline.Retry(Beat::Cleave);
            return;
        }
        rav->CastSpell(victim, SPELL_RV_SUNDERING_CLEAVE, false);
        _timeline.Set(Beat::Cleave, urand(kCleaveEveryMinMs, kCleaveEveryMaxMs));
    }

    // Corvane died first (or was despawned): RV10 on the Ravenian. The emote, his stacks, his own orders.
    void CorvaneGone(Creature* rav, char const* why)
    {
        _corvaneDead = true;
        _pendingOrder.reset();
        _pairDue = false;
        _pairPending = false;
        _reports.clear();
        _stage = Stage::Bereaved;
        _timeline.Unleash();
        if (!_examiner && rav->IsAIEnabled && rav->AI())
            rav->AI()->Talk(EMOTE_RAVENIAN_TEARS_FREE);
        Describe(rav);
        DungeonKit::LogMechanic(kLogDungeon, LogName(), "bereaved-start", Acore::StringFormat("survivor=ravenian "
            "why={} health={:.1f}", why, rav->GetHealthPct()));
    }

    void BecomeAlone(Creature* corv);

    Timeline _timeline;
    ObjectGuid _corvane;
    std::vector<MechanicHandle> _live;
    std::vector<Report> _reports;
    std::optional<Order> _lastOrder;
    std::optional<Order> _pendingOrder;
    Stage _orderStage = Stage::Leash;
    Stage _stage = Stage::Leash;
    uint32 _idleMs = 0;
    uint32 _standMs = 0;
    uint32 _transitionAt = 0;
    bool _examiner;
    bool _heroic = false;
    bool _engaged = false;
    bool _pairPending = false;      // this order is the first of a heroic pair
    bool _pairDue = false;          // ... it was performed: call the second now
    bool _landDue = false;
    bool _corvaneDead = false;
    bool _selfCancel = false;
    Pair _pair = Pair::Both;
    bool _wipeDue = false;          // collapsed: Corvane alone wiped
    ObjectGuid _corvaneKiller;      // collapsed: who killed Corvane (the Ravenian's killer)
    bool _collapseDue = false;      // the lethal hit came: the collapse runs on his next tick
};

// ---- Master Corvane 300542 (and his examiner 300552) ----------------------------------------------------------------

struct npc_sc_master_corvane : public ScriptedAI
{
    explicit npc_sc_master_corvane(Creature* creature) : npc_sc_master_corvane(creature, false) { }

    npc_sc_master_corvane(Creature* creature, bool examiner)
        : ScriptedAI(creature), _arena(RavenianArena(), CorvaneLeash(examiner)), _examiner(examiner) { }

    void Reset() override
    {
        _alone = false;
        _landed = false;
        _wiping = false;
        _orphanMs = 0;
        _timeline = Timeline{};
        _arena.Reset();
        me->SetReactState(REACT_PASSIVE);
        Seat();
        if (_examiner)
            SetCreatureHealth(me, kExaminerCorvaneHealth);
    }

    void IsSummonedBy(WorldObject* summoner) override
    {
        if (Creature* rav = summoner ? summoner->ToCreature() : nullptr)
            _ravenian = rav->GetGUID();
    }

    void SetGUID(ObjectGuid const& guid, int32 id) override
    {
        if (id == kGuidRavenian)
            _ravenian = guid;
    }

    // He never chases or swings: rooted on his seat, then on his landing, casting.
    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }

    void OnSpellCast(SpellInfo const* spell) override
    {
        Report(spell->Id, true);
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        // A kill interrupts the cast first (health 0, still alive): never an Unbound.
        if (me->IsAlive() && me->GetHealth() > 0)
            Report(spell->Id, false);
    }

    void JustDied(Unit* killer) override
    {
        _arena.Reset();
        if (!_examiner)
            Talk(YELL_CORVANE_DEATH);
        Creature* rav = Ravenian();
        if (RavenianDirector* director = DirectorOf(rav))
            director->Fight().CorvaneDied(rav, killer);
        DungeonKit::LogMechanic(kLogDungeon, LogTag(), "corvane-death", Acore::StringFormat("alone={}",
            _alone ? 1 : 0));
    }

    // While the Ravenian leads, his AI decides the fight's end (his evade despawns Corvane); alone (the Ravenian
    // collapsed), Corvane's wipe makes the Ravenian reset both.
    void EnterEvadeMode(EvadeReason why) override
    {
        if (!_alone)
            return;
        WipeAlone(uint32(why));
    }

    void UpdateAI(uint32 diff) override
    {
        UpdateOrphan(diff);
        if (!_alone || _wiping)
            return;
        if (!me->IsInCombat())
        {
            WipeAlone(uint32(EVADE_REASON_NO_HOSTILES));
            return;
        }
        if (!_arena.Update(me, diff))
            return;     // nobody on his arena for 10 s: evading (WipeAlone)

        _timeline.Advance(diff);
        if (_timeline.Due(Beat::Bereaved))
        {
            _timeline.Set(Beat::Bereaved, kBereavedEveryMs);
            uint32 const stacks = DungeonKit::AddStacks(me, SPELL_RV_BEREAVED, 1, me);
            DungeonKit::LogMechanic(kLogDungeon, LogTag(), "bereaved", Acore::StringFormat("unit=corvane stacks={}",
                stacks));
        }
        if (me->GetCurrentSpell(CURRENT_GENERIC_SPELL) || !_timeline.Due(Beat::Bolt))
            return;
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        rule.maxRange = kShadowBoltRange;
        rule.requireLos = true;
        Player* target = DungeonKit::PickPlayer(me, rule);
        if (target && me->CastSpell(target, SPELL_RV_SHADOW_BOLT, false) == SPELL_CAST_OK)
            _timeline.Set(Beat::Bolt, kShadowBoltEveryMs);
        else
            _timeline.Retry(Beat::Bolt);
    }

    // ---- the fight's calls ------------------------------------------------------------------------------------------

    // RV5: he is on the floor: attackable, in combat, his own leash guard (used once he stands alone).
    void Landed()
    {
        _landed = true;
        me->RemoveUnitFlag(UnitFlags(UNIT_FLAG_NOT_SELECTABLE | UNIT_FLAG_NON_ATTACKABLE));
        me->StopMoving();
        me->SetControlled(true, UNIT_STATE_ROOT);
        me->SetInCombatWithZone();
        _arena.Engage(me);
    }

    // The Ravenian collapsed: Corvane fights on alone (RV10), under the Ravenian's registry encounter (re-described
    // with Corvane as the only target).
    void BecomeAlone()
    {
        _alone = true;
        _timeline = Timeline{};
        _timeline.Set(Beat::Bolt, kRetryMs);
        _timeline.Set(Beat::Bereaved, kBereavedEveryMs);
        if (!_landed)
            Landed();
        me->SetInCombatWithZone();
    }

private:
    char const* LogTag() const { return _examiner ? kExaminerLogName : kBossLogName; }

    Creature* Ravenian() const
    {
        return _ravenian.IsEmpty() ? nullptr : ObjectAccessor::GetCreature(*me, _ravenian);
    }

    // Phase 1: on his seat behind the Ravenian, unselectable and not attackable (user ruling 2026-11-08).
    void Seat()
    {
        me->SetUnitFlag(UnitFlags(UNIT_FLAG_NOT_SELECTABLE | UNIT_FLAG_NON_ATTACKABLE));
    }

    void Report(uint32 spellId, bool completed)
    {
        if (_alone)
            return;
        if (RavenianDirector* director = DirectorOf(Ravenian()))
            director->Fight().CorvaneCast(spellId, completed);
    }

    // His Ravenian is gone from the map (an examiner the gauntlet despawned, a GM): he goes too.
    void UpdateOrphan(uint32 diff)
    {
        if (Ravenian())
        {
            _orphanMs = 0;
            return;
        }
        _orphanMs += diff;
        if (_orphanMs >= kOrphanMs)
            me->DespawnOrUnsummon();
    }

    // A wipe while he stood alone: the collapsed Ravenian resets both on his next tick (his evade: the boss state
    // NOT_STARTED, full health, this Corvane despawned and a fresh one seated). Nothing respawns.
    void WipeAlone(uint32 why)
    {
        if (_wiping)
            return;
        _wiping = true;
        _arena.Reset();
        DungeonKit::LogMechanic(kLogDungeon, LogTag(), "wipe-alone", Acore::StringFormat("reason={}", why));
        if (RavenianDirector* director = DirectorOf(Ravenian()))
            director->Fight().RequestReset();
        else
            me->DespawnOrUnsummon();    // no Ravenian AI to reset with (UpdateOrphan would send him away anyway)
    }

    DungeonKit::ArenaGuard _arena;
    Timeline _timeline;
    ObjectGuid _ravenian;
    uint32 _orphanMs = 0;
    bool _examiner;
    bool _alone = false;
    bool _landed = false;
    bool _wiping = false;
};

// The Graduate Examiner, Corvane (S13's gauntlet): 20k, heroic values, summoned by his examiner Ravenian.
struct npc_sc_examiner_corvane : public npc_sc_master_corvane
{
    explicit npc_sc_examiner_corvane(Creature* creature) : npc_sc_master_corvane(creature, true) { }
};

namespace
{
    npc_sc_master_corvane* CorvaneAI(Creature* corv)
    {
        return corv && corv->IsAIEnabled ? dynamic_cast<npc_sc_master_corvane*>(corv->AI()) : nullptr;
    }
}

void RavenianFight::Land(Creature* rav, Creature* corv, char const* why)
{
    _landDue = false;
    if (!corv || !corv->IsAlive())
    {
        if (_stage == Stage::Transition)
            _stage = Stage::Hand;
        return;
    }
    std::size_t const index = PickLanding(DungeonKit::PlaneOf(rav));
    Point3 const& spot = kCorvaneLandings[index];
    Vec2 const here{ spot.x, spot.y };
    float const facing = DungeonKit::BearingTo(here, DungeonKit::PlaneOf(rav));
    corv->CastSpell(corv, SPELL_RV_TELEPORT, true);
    corv->InterruptSpell(CURRENT_CHANNELED_SPELL, false);
    corv->NearTeleportTo(spot.x, spot.y, spot.z, facing);
    corv->CastSpell(corv, SPELL_RV_TELEPORT, true);
    if (npc_sc_master_corvane* ai = CorvaneAI(corv))
        ai->Landed();
    if (rav->IsAlive() && _pair != Pair::Collapsed)
    {
        _stage = Stage::Hand;
        _timeline.Land();
        Mechanic::TrackUnit(rav, corv);
        Mechanic::NoteNextCastIn(corv, SPELL_RV_MEND, Milliseconds(kMendFirstMs));
        Describe(rav);
        KeepLeash(rav, corv);
    }
    DungeonKit::LogMechanic(kLogDungeon, LogName(), "land", Acore::StringFormat("{} spot={} at=({:.1f}, {:.1f}) "
        "from-ravenian={:.1f}yd", why, index, spot.x, spot.y, DungeonKit::Distance(here, DungeonKit::PlaneOf(rav))));
}

void RavenianFight::BecomeAlone(Creature* corv)
{
    if (npc_sc_master_corvane* ai = CorvaneAI(corv))
        ai->BecomeAlone();
}

// ---- The Ravenian 10507 -------------------------------------------------------------------------------------------

struct boss_the_ravenian_rework : public BossAI, public RavenianDirector
{
    explicit boss_the_ravenian_rework(Creature* creature)
        : BossAI(creature, BOSS_RAVENIAN), _arena(RavenianArena(), LeashOptions(kBossLogName)), _fight(false) { }

    void Reset() override
    {
        _Reset();
        _fight.Cleanup(me);
        _arena.Reset();
        _grades.Reset();
    }

    // Corvane is the fight's, not BossAI's summon list (its despawn at the Ravenian's death would take him along).
    void JustSummoned(Creature* summon) override
    {
        if (IsCorvaneEntry(summon->GetEntry()))
            return;
        BossAI::JustSummoned(summon);
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_RAVENIAN;
        Mechanic::BeginEncounter(me, options);
        _grades.Begin(me, Instructor::Ravenian);
        _arena.Engage(me);
        _fight.Engage(me);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "pull",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f})", DungeonKit::IsHeroicMap(me) ? 1 : 0,
                me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "evade", Acore::StringFormat("reason={}", uint32(why)));
        _fight.Cleanup(me);
        _fight.DespawnCorvane(me);      // a fresh one takes his seat (Idle)
        _arena.Reset();
        _grades.Reset();
        BossAI::EnterEvadeMode(why);
    }

    // He never dies first (the collapse); his death ends the encounter: DONE, saved, the Passing Grades (his
    // GradeWatch holds every failure, Corvane's alone phase included: it runs under his registry encounter).
    void JustDied(Unit* killer) override
    {
        _arena.Reset();
        _fight.RavenianDied(me);
        _grades.AwardAtDeath(me);
        BossAI::JustDied(killer);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death", Acore::StringFormat("killer={}",
            killer ? killer->GetName() : "-"));
    }

    void DamageTaken(Unit* /*attacker*/, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*mask*/) override
    {
        damage = _fight.RavenianDamage(me, damage);
    }

    RavenianFight& Fight() override { return _fight; }

    void UpdateAI(uint32 diff) override
    {
        UpdateTestLesson(diff);
        if (_fight.Collapsed())
        {
            UpdateCollapsed();
            return;
        }
        if (!me->IsEngaged())
            _fight.Idle(me, diff);

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        _fight.Update(me, diff);
        if (_fight.Standing() || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ---- `.dbtest scholo ravenian` entry points ---------------------------------------------------------------------

    Creature* Me() const { return me; }

    bool TestLesson(Creature* owner, Player* student, bool heroic)
    {
        if (_testLesson)
            _testLesson->Abort();
        _testLesson = CreateSoloLesson(Classroom::RavenianVault);
        if (!_testLesson || !owner || !student)
            return false;
        _testLesson->Start(owner, student, heroic);
        return true;
    }

    std::string TestState() const
    {
        return Acore::StringFormat("{} lesson={}", _fight.State(me), !_testLesson ? "none" : _testLesson->Done()
            ? (_testLesson->Passed() ? "passed" : _testLesson->Failed() ? "failed" : "ended") : "running");
    }

private:
    // Collapsed (user ruling 1): inert until Corvane dies (the real kill) or the group wipes (both reset).
    void UpdateCollapsed()
    {
        switch (_fight.UpdateCollapsed(me))
        {
            case CollapsedStep::Hold:
                break;
            case CollapsedStep::Kill:
                _fight.KillCollapsed(me);
                break;
            case CollapsedStep::Reset:
                EnterEvadeMode(EVADE_REASON_OTHER);
                break;
        }
    }

    void UpdateTestLesson(uint32 diff)
    {
        if (_testLesson && !_testLesson->Done())
            _testLesson->Update(diff);
    }

    DungeonKit::ArenaGuard _arena;
    GradeWatch _grades;
    RavenianFight _fight;
    std::unique_ptr<SoloLesson> _testLesson;
};

// The Graduate Examiner, the Ravenian (S13's gauntlet, heroic hard mode): the fight at heroic values, 60k, his own
// examiner Corvane (20k), no boss state, no Passing Grade, no text.
struct npc_sc_examiner_ravenian : public ScriptedAI, public RavenianDirector
{
    explicit npc_sc_examiner_ravenian(Creature* creature)
        : ScriptedAI(creature), _arena(RavenianArena(), LeashOptions(kExaminerLogName)), _fight(true) { }

    void Reset() override
    {
        _fight.Cleanup(me);
        _arena.Reset();
        SetCreatureHealth(me, kExaminerRavenianHealth);
    }

    void JustEngagedWith(Unit* /*who*/) override
    {
        Mechanic::BeginEncounter(me);
        _arena.Engage(me);
        _fight.Engage(me);
        DungeonKit::LogMechanic(kLogDungeon, kExaminerLogName, "pull", Acore::StringFormat("health={} at=({:.1f}, "
            "{:.1f}, {:.1f})", me->GetMaxHealth(), me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
    }

    // No boss state ends his registry encounter: the evade and the death do (Weakened comes off; RV-2).
    void EnterEvadeMode(EvadeReason why) override
    {
        _fight.Cleanup(me);
        _fight.DespawnCorvane(me);
        _arena.Reset();
        Mechanic::EndEncounter(me);
        ScriptedAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* /*killer*/) override
    {
        _arena.Reset();
        _fight.RavenianDied(me);
        Mechanic::EndEncounter(me);
        DungeonKit::LogMechanic(kLogDungeon, kExaminerLogName, "death", "last=1");
    }

    void DamageTaken(Unit* /*attacker*/, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*mask*/) override
    {
        damage = _fight.RavenianDamage(me, damage);
    }

    RavenianFight& Fight() override { return _fight; }

    void UpdateAI(uint32 diff) override
    {
        if (_fight.Collapsed())
        {
            switch (_fight.UpdateCollapsed(me))
            {
                case CollapsedStep::Hold:
                    break;
                case CollapsedStep::Kill:
                    _fight.KillCollapsed(me);
                    break;
                case CollapsedStep::Reset:
                    EnterEvadeMode(EVADE_REASON_OTHER);
                    break;
            }
            return;
        }
        if (!me->IsEngaged())
            _fight.Idle(me, diff);
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;
        _fight.Update(me, diff);
        if (_fight.Standing() || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

private:
    DungeonKit::ArenaGuard _arena;
    RavenianFight _fight;
};

// ---- Spell scripts --------------------------------------------------------------------------------------------------

// RV5 / RV8 Mend Construct 206277 / 206278: heals the Ravenian 10% / 15% (the transition) or 6% / 10% (phase 2) of
// his max health (set at launch; ignores caster modifiers; examiners: heroic values).
class spell_scholo_ravenian_mend : public SpellScript
{
    PrepareSpellScript(spell_scholo_ravenian_mend);

    void SetHeal(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;
        bool const heroic = HeroicFor(caster);
        float const pct = GetSpellInfo()->Id == SPELL_RV_MEND_TRANSITION ? kTransitionHealPct(heroic)
            : kMendPct(heroic);
        SetEffectValue(static_cast<int32>(CalculatePct(target->GetMaxHealth(), pct)));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_scholo_ravenian_mend::SetHeal, EFFECT_0, SPELL_EFFECT_HEAL);
    }
};

// RV9 Shadow Bolt 206283: 15% / 20% of the reference row (RefFlatOn at launch, so defensives count), raised by
// Corvane's Bereaved stacks.
class spell_scholo_corvane_shadow_bolt : public SpellScript
{
    PrepareSpellScript(spell_scholo_corvane_shadow_bolt);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        if (Unit* caster = GetCaster())
            SetEffectValue(static_cast<int32>(DungeonKit::RefFlatOn(caster, GetHitUnit(),
                kShadowBoltPct(HeroicFor(caster)) * StackScale(caster))));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_scholo_corvane_shadow_bolt::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

// RV6 Unbound 206280: the Ravenian does the kicked move on his maker: exactly 8% of Corvane's max health (a DUMMY that
// deals the damage itself, so his armor does not cut it), with the move's look on him.
class spell_scholo_ravenian_unbound_strike : public SpellScript
{
    PrepareSpellScript(spell_scholo_ravenian_unbound_strike);

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target || !target->IsAlive())
            return;
        SpellNonMeleeDamage damage(caster, target, GetSpellInfo(), SPELL_SCHOOL_MASK_NORMAL);
        damage.damage = CalculatePct(target->GetMaxHealth(), kUnboundPct);
        caster->SendSpellNonMeleeDamageLog(&damage);
        caster->DealSpellDamage(&damage, false);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_scholo_ravenian_unbound_strike::HandleDummy, EFFECT_0,
            SPELL_EFFECT_DUMMY);
    }
};

// ---- The Vault of the Ravenian's solo lesson (S11's detention; handoff section 3.7, SC 2960-2971) -------------------

// The Ravenian's echo carries out 3 orders on the lone student (each once, a random order): a 2 s order bar, then the
// 2 s marker (Trample through the student to the wall, Sweep from the echo's spot, Smash on the student); any hit fails
// the lesson (15% / 25% plus Weakened). The echo is S11's entry (300545, not attackable); the lesson summons it next to
// the student when its template exists, else the markers come from the same spot with no echo.
class RavenianVaultLesson : public TimedSoloLesson
{
public:
    RavenianVaultLesson() : TimedSoloLesson(Classroom::RavenianVault) { }

protected:
    void OnStart(Creature* owner, Player* student, bool heroic) override
    {
        _map = owner->GetMap();
        _plan = LessonOrders(urand(0, 0xFFFF), urand(0, 0xFFFF));
        _now = 0;
        _called = 0;
        _placed = 0;
        _pct = LessonPct(heroic);
        if (sObjectMgr->GetCreatureTemplate(NPC_SC_RAVENIANS_ECHO))
            if (Creature* echo = owner->SummonCreature(NPC_SC_RAVENIANS_ECHO, SourcePoint(owner, student),
                TEMPSUMMON_MANUAL_DESPAWN))
            {
                _echo = echo->GetGUID();
                echo->SetReactState(REACT_PASSIVE);
                echo->CastSpell(echo, kAuraGhostVisual, true);
            }
        DungeonKit::LogMechanic(kLogDungeon, kLessonLogName, "start", Acore::StringFormat("student={} heroic={} "
            "orders={},{},{} echo={}", student->GetName(), heroic ? 1 : 0, OrderName(_plan[0]), OrderName(_plan[1]),
            OrderName(_plan[2]), _echo.IsEmpty() ? 0 : 1));
    }

    void OnUpdate(uint32 diff, Creature* owner, Player* student) override
    {
        _now += diff;
        if (_called < kLessonOrders && _now >= kLessonCallAtMs[_called])
            Call(owner, student);
        if (_placed < _called && _now >= kLessonCallAtMs[_placed] + kLessonCallMs)
            Place(owner, student);
    }

    void OnEnd(LessonEnd why, Creature* owner) override
    {
        if (owner)
            for (MechanicHandle const& handle : _live)
                Mechanic::Cancel(owner, handle);
        _live.clear();
        if (Creature* echo = Echo())
            echo->DespawnOrUnsummon();
        _echo.Clear();
        DungeonKit::LogMechanic(kLogDungeon, kLessonLogName, "end", Acore::StringFormat("why={} placed={}",
            uint32(why), _placed));
    }

private:
    Creature* Echo() const
    {
        return _map && !_echo.IsEmpty() ? _map->GetCreature(_echo) : nullptr;
    }

    // kLessonSourceYd from the student, toward the echo (or the owner), stopped at walls; facing the student.
    Position SourcePoint(Creature* owner, Player* student) const
    {
        WorldObject const* from = Echo() ? static_cast<WorldObject const*>(Echo()) : owner;
        Vec2 const here = DungeonKit::PlaneOf(student);
        Vec2 const there = DungeonKit::PlaneOf(from);
        float const toward = DungeonKit::Distance(here, there) > 0.5f ? DungeonKit::BearingTo(here, there)
            : student->GetOrientation();
        Position at = ReachablePoint(student, toward, kLessonSourceYd);
        at.SetOrientation(DungeonKit::BearingTo(Vec2{ at.GetPositionX(), at.GetPositionY() }, here));
        return at;
    }

    // The order is called: the echo steps to its spot and shows the order's bar (2 s).
    void Call(Creature* owner, Player* student)
    {
        Order const o = _plan[_called];
        _sources[_called] = SourcePoint(owner, student);
        if (Creature* echo = Echo())
        {
            Position const& at = _sources[_called];
            echo->NearTeleportTo(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), at.GetOrientation());
            echo->CastSpell(echo, OrderCastSpell(o), false);     // not triggered: the bar shows
        }
        ++_called;
        DungeonKit::LogMechanic(kLogDungeon, kLessonLogName, "call", Acore::StringFormat("order={} n={}",
            OrderName(o), _called));
    }

    // Its 2 s marker: from the echo's spot, facing where the student stands now.
    void Place(Creature* owner, Player* student)
    {
        Order const o = _plan[_placed];
        Position source = _sources[_placed];
        Vec2 const from{ source.GetPositionX(), source.GetPositionY() };
        source.SetOrientation(DungeonKit::BearingTo(from, DungeonKit::PlaneOf(student)));
        MechanicHandle const handle = PlaceOrder(owner, nullptr, source, o, student, _pct, true);
        if (handle.IsValid())
            _live.push_back(handle);
        ++_placed;
        DungeonKit::LogMechanic(kLogDungeon, kLessonLogName, OrderName(o), Acore::StringFormat("n={} pct={:.0f}",
            _placed, _pct));
    }

    Map* _map = nullptr;
    std::array<Order, kLessonOrders> _plan{};
    std::array<Position, kLessonOrders> _sources{};
    std::vector<MechanicHandle> _live;
    ObjectGuid _echo;
    uint32 _now = 0;
    std::size_t _called = 0;
    std::size_t _placed = 0;
    float _pct = 15.f;
};

// ---- `.dbtest scholo ravenian` ------------------------------------------------------------------------------------

namespace
{
    boss_the_ravenian_rework* FindRavenianAI(ChatHandler* handler)
    {
        Creature* boss = ScholoTest::FindBoss(handler, NPC_RAVENIAN);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_the_ravenian_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "The Ravenian is not running boss_the_ravenian_rework (check the "
                "ScriptName).");
        return ai;
    }

    // The selected player, else the GM.
    Player* TestTarget(ChatHandler* handler)
    {
        if (Player* selected = handler->getSelectedPlayer())
            return selected;
        return handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return ScholoTest::ShowBossInfo(handler, NPC_RAVENIAN, BOSS_RAVENIAN);
    }

    // `.dbtest scholo ravenian state`: the stage, the clock, the beats, the stacks.
    bool HandleState(ChatHandler* handler)
    {
        boss_the_ravenian_rework* ai = FindRavenianAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Ravenian: {}", ai->TestState());
        return true;
    }

    // `.dbtest scholo ravenian order <trample|sweep|smash>`: in the fight, Corvane calls it now (RV1-RV3; a kick in
    // phase 2 unbinds); out of it, the Ravenian does the move at once on the selected player (or you).
    bool HandleOrder(ChatHandler* handler, std::string name)
    {
        boss_the_ravenian_rework* ai = FindRavenianAI(handler);
        std::optional<Order> const o = OrderByName(name);
        if (!ai || !o)
        {
            if (ai)
                handler->SendErrorMessage("{}", "Usage: order <trample|sweep|smash>");
            return false;
        }
        Player* target = TestTarget(handler);
        bool const ok = ai->Fight().ForceOrder(ai->Me(), *o, target);
        handler->PSendSysMessage("Ravenian: order {} {}.", OrderName(*o), ok ? "called" : "failed");
        return true;
    }

    // `.dbtest scholo ravenian transition`: the 50% transition now (phase 1, in the fight; RV5).
    bool HandleTransition(ChatHandler* handler)
    {
        boss_the_ravenian_rework* ai = FindRavenianAI(handler);
        if (!ai)
            return false;
        bool const ok = ai->Fight().ForceTransition(ai->Me());
        handler->PSendSysMessage("Ravenian: transition {}.", ok ? "started" : "needs phase 1 in combat, Corvane free");
        return true;
    }

    // `.dbtest scholo ravenian mend`: Corvane's Mend Construct now (phase 2; RV8: kick it).
    bool HandleMend(ChatHandler* handler)
    {
        boss_the_ravenian_rework* ai = FindRavenianAI(handler);
        if (!ai)
            return false;
        bool const ok = ai->Fight().ForceMend(ai->Me());
        handler->PSendSysMessage("Ravenian: Mend Construct {}.", ok ? "cast" : "needs phase 2, Corvane free");
        return true;
    }

    // `.dbtest scholo ravenian unbound`: the Ravenian does a move on Corvane as if an order were kicked (phase 2; RV6).
    bool HandleUnbound(ChatHandler* handler)
    {
        boss_the_ravenian_rework* ai = FindRavenianAI(handler);
        if (!ai)
            return false;
        bool const ok = ai->Fight().ForceUnbound(ai->Me());
        handler->PSendSysMessage("Ravenian: Unbound {}.", ok ? "done" : "needs phase 2");
        return true;
    }

    // `.dbtest scholo ravenian lesson [heroic 0|1]`: the Vault of the Ravenian lesson on the selected player (or you),
    // owned by a temporary trigger at their feet. Its safety rule ends it at once when nobody else (a living non-GM
    // player) is in the instance: select a bot, or `.gm off` with a second character.
    bool HandleLesson(ChatHandler* handler, Optional<uint32> heroic)
    {
        boss_the_ravenian_rework* ai = FindRavenianAI(handler);
        Player* student = TestTarget(handler);
        if (!ai || !student)
            return false;
        Creature* owner = student->SummonCreature(kTestLessonOwnerEntry, student->GetPosition(),
            TEMPSUMMON_TIMED_DESPAWN, kTestLessonOwnerMs);
        if (!owner)
        {
            handler->SendErrorMessage("{}", "Could not summon the lesson's owner.");
            return false;
        }
        bool const isHeroic = heroic ? *heroic != 0 : DungeonKit::IsHeroicMap(student);
        if (!ai->TestLesson(owner, student, isHeroic))
        {
            handler->SendErrorMessage("{}", "No Vault of the Ravenian lesson is registered.");
            return false;
        }
        handler->PSendSysMessage("Ravenian: the Vault of the Ravenian lesson ({}) on {}; `state` shows the verdict.",
            isHeroic ? "heroic" : "normal", student->GetName());
        return true;
    }

    ChatCommandTable const& RavenianTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,       SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,      SEC_GAMEMASTER, Console::No },
            { "order",      HandleOrder,      SEC_GAMEMASTER, Console::No },
            { "transition", HandleTransition, SEC_GAMEMASTER, Console::No },
            { "mend",       HandleMend,       SEC_GAMEMASTER, Console::No },
            { "unbound",    HandleUnbound,    SEC_GAMEMASTER, Console::No },
            { "lesson",     HandleLesson,     SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_the_ravenian_rework()
{
    RegisterDungeonReworkCreatureAI(boss_the_ravenian_rework, ScholomanceRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sc_master_corvane, ScholomanceRework::kInstanceScriptName);
    // The examiners' script names are RavenianLogic.h kExaminerRavenianScriptName / kExaminerCorvaneScriptName; S13
    // binds the entries in wave C.
    if (kWaveCBound)
    {
        RegisterDungeonReworkCreatureAI(npc_sc_examiner_ravenian, ScholomanceRework::kInstanceScriptName);
        RegisterDungeonReworkCreatureAI(npc_sc_examiner_corvane, ScholomanceRework::kInstanceScriptName);
    }
    RegisterSpellScript(spell_scholo_ravenian_mend);
    RegisterSpellScript(spell_scholo_corvane_shadow_bolt);
    RegisterSpellScript(spell_scholo_ravenian_unbound_strike);
    RegisterSoloLesson(Classroom::RavenianVault,
        [] { return std::unique_ptr<SoloLesson>(new RavenianVaultLesson()); });
    ScholoTest::RegisterBoss("ravenian", RavenianTestCommands());
}
