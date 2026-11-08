/*
 * mod-dungeon-bosses, Scholomance S2: Rattlegore (11622), "Spare Parts". Build spec SC 733-778
 * (docs/dungeons/scholomance-rework.md), handoff section 3.4 rows RG and 3.5 row S2. Replaces stock SmartAI 11622
 * (Knock Away 10101, Strike 18368, War Stomp 16727: WP-S2's SQL rev drops it); bound by apps/dbc-tools
 * source/npcs/scholomance/rattlegore.py. Pure rules: RattlegoreLogic.h.
 *
 *   RG1  Part lands       at 85, 70, 55, 40, 25 and 10% health (each once; a burst over two fires two): emote line 0,
 *                         a bone flung (206131) to 1 (heroic 2, opposite sides of him) floor points 20+ yd from him: a
 *                         registry circle 4 / 6 yd, 2 s, 30% / 40% Physical + 1 Weakened (206130)
 *   RG2  Loose part       each landing leaves a bone pile (300531): a registry Soak (1 body, non-tank, 3 yd) on the
 *                         moving pile; it waits 3 / 1 s, then crawls to him at 3 / 4 yd/s. Anyone on it holds it and
 *                         grinds it: 5% / 6% (206132) per second on it, ground down after 5 / 6 s (progress kept)
 *   RG3  Pile returns     a pile that reaches him bolts back on: heals him 8% / 10% (206133) and +5 Frenzy
 *   RG4  Ossuary Eruption 8 s, then every 20 s: a 2 s stomp (206135, emote line 1), then rings from where he stood,
 *                         0-6, 6-12, 12.06-18 yd, 1.5 s apart; heroic back inward, 1 s apart; 35% / 50% (206136)
 *   RG5  Salvage          from the second break, at most every 30 s: he walks to the nearest Unfinished Construct
 *                         (300532, 4 spawned on the pull) and channels 5 s (206137, emote line 2; on the interrupt
 *                         list). Broken by an interrupt or by 5% of his health in damage; else he heals 10% (206138),
 *                         and on heroic gains Reinforced (206139, +15% damage dealt, 4 stacks). Either way that
 *                         construct is spent
 *   RG6  Strike           stock 18368: 3-6 s, then every 7-12 s
 *   RG7  Knock Away       206140 (stock 10101 without its threat cut): 7-15 s, then every 15-25 s
 *   RG8  Frenzy           +1 stack (206134: +3% attack speed, +1% size) every 3 / 2 s from the pull, cap 100; each
 *                         break halves it, each pile home adds 5
 *   Arena                 ScholomanceRework::LeashOptions on RattlegoreArena() (no grips; holds at the edge)
 *
 * Every timer runs on the AI's own clock, never on BossAI's scheduler (a cast bar pauses that one): Frenzy, the
 * thresholds, the piles and the missiles keep running through the stomp's cast bar and the Salvage channel. Every
 * firing logs one INFO line "scholo rattlegore <mechanic> ..." (module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "Random.h"
#include "RattlegoreLogic.h"
#include "ScholomanceKit.h"
#include "ScholomanceRework.h"
#include "ScholomanceTestCommand.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <functional>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;
using namespace ScholoRattlegore;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kLogBoss = "rattlegore";

    uint32 constexpr POINT_SALVAGE = 1;
    uint32 constexpr POINT_PILE = 1;

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // The Ossuary floor under `p` (z 93-95; the stair and the hatchling floor above are not), else nullopt.
    std::optional<float> FloorZ(WorldObject const* ref, Vec2 p)
    {
        float const z = ref->GetMapHeight(p.x, p.y, kOssuaryFloorZ + 3.f);
        if (z <= INVALID_HEIGHT + 1.f || std::fabs(z - kOssuaryFloorZ) > 2.5f)
            return std::nullopt;
        return z;
    }

    BossMechanics::Eligibility NonTank()
    {
        BossMechanics::Eligibility e;
        e.roles = BossMechanics::Role::Healer | BossMechanics::Role::Damage;
        return e;
    }
}

// Rattlegore 11622
struct boss_rattlegore_rework : public BossAI
{
    explicit boss_rattlegore_rework(Creature* creature)
        : BossAI(creature, BOSS_RATTLEGORE), _arena(RattlegoreArena(), LeashOptions(kLogBoss)) { }

    void Reset() override
    {
        _Reset();
        Cleanup();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_RATTLEGORE;
        Mechanic::BeginEncounter(me, options);
        Describe();

        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        _arena.Engage(me);
        SpawnConstructs();
        bool const heroic = IsHeroicMap(me);
        _nextFrenzyMs = kFrenzyEveryMs(heroic);
        _nextEruptionMs = kEruptionFirstMs;
        _nextStrikeMs = InRange(kStrikeFirst, Rand01());
        _nextKnockMs = InRange(kKnockFirst, Rand01());
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "engage",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f}) constructs={}", heroic ? 1 : 0,
                me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), ConstructsStanding()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);   // DONE (door data, Gandling's count), the summons despawn, the encounter ends
        Cleanup();
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "death",
            Acore::StringFormat("breaks={} killer={}", _ladder.Breaks(), killer ? killer->GetName() : "none"));
    }

    // The piles and constructs are props: never zoned into combat (BossAI::JustSummoned would).
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    void DamageTaken(Unit* /*attacker*/, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*school*/) override
    {
        if (_salvage != SalvagePhase::Channeling || _salvageBreakSent)
            return;
        _salvageDamage += damage;
        if (!BreaksSalvage(_salvageDamage, me->GetMaxHealth()))
            return;
        _salvageBreakSent = true;
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "salvage-broken",
            Acore::StringFormat("damage={} of {}", _salvageDamage, SalvageBreakDamage(me->GetMaxHealth())));
        me->InterruptNonMeleeSpells(false);     // OnSpellFailed ends it
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (spell->Id != SPELL_RG_SALVAGE || _salvage != SalvagePhase::Channeling)
            return;
        if (!_salvageBreakSent)
            DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "salvage-interrupted");
        EndSalvage(false);
    }

    void OnChannelFinished(SpellInfo const* spell) override
    {
        if (spell->Id == SPELL_RG_SALVAGE && _salvage == SalvagePhase::Channeling)
            EndSalvage(true);
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type == POINT_MOTION_TYPE && id == POINT_SALVAGE && _salvage == SalvagePhase::Walking)
            BeginSalvageChannel();
    }

    void UpdateAI(uint32 diff) override
    {
        if (_salvage == SalvagePhase::None)
        {
            if (!UpdateVictim())
                return;
        }
        else if (!me->IsEngaged() || me->GetThreatMgr().IsThreatListEmpty())
        {
            // Walking or channeling (passive, no victim): a wipe still resets him.
            EnterEvadeMode(EVADE_REASON_NO_HOSTILES);
            return;
        }

        // The AI's own clock: nothing below waits for a cast bar or the channel.
        _clockMs += diff;
        UpdateFrenzy();
        CheckBreaks();
        UpdateLaunches();
        UpdatePiles(diff);

        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        if (_salvage != SalvagePhase::None)
        {
            if (_salvage == SalvagePhase::Walking && _clockMs >= _salvageWalkUntil)
                BeginSalvageChannel();      // a blocked path: channel where he stands
            return;
        }

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;

        bool const heroic = IsHeroicMap(me);
        if (_clockMs >= _nextEruptionMs)
        {
            _nextEruptionMs = _clockMs + kEruptionEveryMs;
            StartEruption(heroic);
            return;
        }
        if (SalvageMayStart(_ladder.Breaks(), ConstructsStanding(), _clockMs, _salvageNotBefore)
            && StartSalvage(heroic))
            return;
        if (_clockMs >= _nextKnockMs)
        {
            Unit* victim = me->GetVictim();
            if (victim && me->IsWithinMeleeRange(victim))
            {
                me->CastSpell(victim, SPELL_RG_KNOCK_AWAY, true);
                _nextKnockMs = _clockMs + InRange(kKnockEvery, Rand01());
                DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "knock-away", victim->GetName());
            }
            else
                _nextKnockMs = _clockMs + 1000;
        }
        if (_clockMs >= _nextStrikeMs)
        {
            Unit* victim = me->GetVictim();
            if (victim && me->IsWithinMeleeRange(victim))
            {
                me->CastSpell(victim, SPELL_STRIKE, true);
                _nextStrikeMs = _clockMs + InRange(kStrikeEvery, Rand01());
            }
            else
                _nextStrikeMs = _clockMs + 1000;
        }

        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RG8 Frenzy
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateFrenzy()
    {
        if (!_nextFrenzyMs || _clockMs < _nextFrenzyMs)
            return;
        uint32 const every = kFrenzyEveryMs(IsHeroicMap(me));
        while (_clockMs >= _nextFrenzyMs)
        {
            DungeonKit::AddStacks(me, SPELL_RG_FRENZY, 1, me, kFrenzyMaxStacks);
            _nextFrenzyMs += every;
        }
    }

    uint32 FrenzyStacks() const
    {
        return DungeonKit::Stacks(me, SPELL_RG_FRENZY);
    }

    void SetFrenzy(uint32 stacks)
    {
        int32 const delta = static_cast<int32>(stacks) - static_cast<int32>(FrenzyStacks());
        if (delta)
            DungeonKit::AddStacks(me, SPELL_RG_FRENZY, delta, me, kFrenzyMaxStacks);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RG1 Part lands
    // ----------------------------------------------------------------------------------------------------------------

    void CheckBreaks()
    {
        uint32 const crossed = _ladder.Take(me->GetHealthPct());
        for (uint32 i = 0; i < crossed; ++i)
            Break(IsHeroicMap(me), false);
    }

    void Break(bool heroic, bool forced)
    {
        if (forced)
            _ladder.AddForced();
        Talk(EMOTE_RATTLEGORE_PART_LOOSE);
        uint32 const before = FrenzyStacks();
        SetFrenzy(FrenzyAfterBreak(before));
        // Salvage opens with the second break (a burst over two thresholds counts both at once).
        if (_ladder.Breaks() >= kSalvageFromBreak && !_salvageOpen)
        {
            _salvageOpen = true;
            _salvageNotBefore = std::max<uint64>(_salvageNotBefore, _clockMs + kSalvageAfterBreakMs);
        }

        std::vector<Vec2> avoid = _pendingLandings;
        for (Pile const& pile : _piles)
            if (Creature* c = me->GetMap()->GetCreature(pile.guid))
                avoid.push_back(DungeonKit::PlaneOf(c));
        std::vector<Vec2> const points = PickLandings(LandingRules{}, DungeonKit::PlaneOf(me),
            kPilesPerBreak(heroic), avoid, Rand01, [this](Vec2 p) { return FloorZ(me, p).has_value(); });
        for (Vec2 const& p : points)
            RegisterLanding(p, heroic);
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "break",
            Acore::StringFormat("heroic={} forced={} breaks={} health={:.1f}% frenzy={}->{} landings={}",
                heroic ? 1 : 0, forced ? 1 : 0, _ladder.Breaks(), me->GetHealthPct(), before, FrenzyStacks(),
                points.size()));
    }

    void RegisterLanding(Vec2 p, bool heroic)
    {
        float const z = FloorZ(me, p).value_or(me->GetPositionZ());
        Position const at(p.x, p.y, z, 0.f);
        MechanicRef ref = Mechanic::Circle(me, at, kLandingRadius(heroic), Ms(kLandingWarnMs));
        ref.Damage(kLandingPct(heroic)).Weakened().Spell(SPELL_RG_PART_LANDS).Tag(TAG_PART_LANDS);
        ref.OnResolve(OnRattlegore([at, heroic, gen = _generation](boss_rattlegore_rework& ai,
            BossMechanics::ResolveResult const& result)
        {
            if (gen == ai._generation)
                ai.PartLanded(at, heroic, result.hits.size());
        }));
        Track(ref.Handle());
        _pendingLandings.push_back(p);
        uint32 const delay = LaunchDelayMs(kLandingWarnMs, me->GetExactDist2d(at.GetPositionX(), at.GetPositionY()));
        _launches.push_back({ at, _clockMs + delay });
    }

    // The bone missile, launched so it lands as the circle resolves (the visual only; the registry owns the hit).
    void UpdateLaunches()
    {
        for (auto it = _launches.begin(); it != _launches.end();)
        {
            if (_clockMs < it->dueMs)
            {
                ++it;
                continue;
            }
            me->CastSpell(it->at.GetPositionX(), it->at.GetPositionY(), it->at.GetPositionZ(), SPELL_RG_PART_FLUNG,
                true);
            it = _launches.erase(it);
        }
    }

    void PartLanded(Position const& at, bool heroic, std::size_t hits)
    {
        Vec2 const p{ at.GetPositionX(), at.GetPositionY() };
        _pendingLandings.erase(std::remove_if(_pendingLandings.begin(), _pendingLandings.end(), [p](Vec2 q)
        {
            return DungeonKit::Distance(p, q) < 0.01f;
        }), _pendingLandings.end());
        SpawnPile(at, heroic);
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "part-lands",
            Acore::StringFormat("at=({:.1f}, {:.1f}) hits={}", p.x, p.y, hits));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RG2 / RG3 Loose part
    // ----------------------------------------------------------------------------------------------------------------

    struct Pile
    {
        ObjectGuid guid;
        PileState state;
        MechanicHandle soak;
        uint32 repathMs = 0;
        bool heroic = false;
        bool moving = false;
    };

    void SpawnPile(Position const& at, bool heroic)
    {
        Creature* pile = me->SummonCreature(NPC_SC_LOOSE_PART, at.GetPositionX(), at.GetPositionY(),
            at.GetPositionZ(), me->GetAngle(&at) + DungeonKit::kPi, TEMPSUMMON_MANUAL_DESPAWN);
        if (!pile)
        {
            DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "pile-failed", "summon refused");
            return;
        }
        pile->SetReactState(REACT_PASSIVE);
        MechanicRef ref = Mechanic::Soak(me, pile, kPileSoakRadius, 1, Ms(kPileWaitMs(heroic)));
        ref.Persistent(Ms(kPileSoakLifeMs), Ms(kPileTickMs)).Eligible(NonTank()).Tag(TAG_LOOSE_PART);
        Pile entry;
        entry.guid = pile->GetGUID();
        entry.state = PileState(PileTuningFor(heroic));
        entry.soak = ref.Handle();
        entry.heroic = heroic;
        _piles.push_back(entry);
    }

    // The players standing on a pile (alive, not GMs, within the soak radius and z band).
    std::vector<Player*> PlayersOn(Creature const* pile) const
    {
        std::vector<Player*> on;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player || !player->IsAlive() || player->IsGameMaster())
                continue;
            if (pile->GetExactDist2d(player) <= kPileSoakRadius
                && std::fabs(player->GetPositionZ() - pile->GetPositionZ()) <= kPileSoakZBand)
                on.push_back(player);
        }
        return on;
    }

    void UpdatePiles(uint32 diff)
    {
        for (auto it = _piles.begin(); it != _piles.end();)
        {
            Pile& pile = *it;
            Creature* c = me->GetMap()->GetCreature(pile.guid);
            if (!c || !c->IsAlive())
            {
                Mechanic::Cancel(me, pile.soak);
                it = _piles.erase(it);
                continue;
            }
            std::vector<Player*> const on = PlayersOn(c);
            bool const atBoss = c->GetExactDist2d(me) <= me->GetCombatReach() + kPileHomeReach;
            PileState::Step const step = pile.state.Update(diff, !on.empty(), atBoss);
            for (uint32 t = 0; t < step.ticks; ++t)
                for (Player* player : on)
                    c->CastSpell(player, SPELL_RG_GRIND, true);
            if (step.ground)
            {
                c->StopMoving();
                c->GetMotionMaster()->Clear();
                c->CastSpell(c, SPELL_RG_GROUND_TO_DUST, true);
                c->DespawnOrUnsummon(1500ms);
                Mechanic::Cancel(me, pile.soak);
                DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "pile-ground",
                    Acore::StringFormat("ticks={} by={}", pile.state.TicksDone(), on.front()->GetName()));
                it = _piles.erase(it);
                continue;
            }
            if (step.home)
            {
                PileHome(c, pile);
                it = _piles.erase(it);
                continue;
            }
            if (step.held)
            {
                if (pile.moving)
                {
                    c->GetMotionMaster()->Clear();
                    c->StopMoving();
                    pile.moving = false;
                }
                pile.repathMs = 0;      // moves again at once when the soaker steps off
            }
            else if (step.move)
            {
                pile.repathMs = pile.repathMs > diff ? pile.repathMs - diff : 0;
                if (!pile.repathMs)
                {
                    c->GetMotionMaster()->MovePoint(POINT_PILE, me->GetPosition(), FORCED_MOVEMENT_WALK,
                        kPileCrawlYdPerSec(pile.heroic));
                    pile.repathMs = kPileRepathMs;
                    pile.moving = true;
                }
            }
            ++it;
        }
    }

    void PileHome(Creature* c, Pile const& pile)
    {
        int32 const heal = PctOfMax(me->GetMaxHealth(), kPileHomeHealPct(pile.heroic));
        me->CastCustomSpell(SPELL_RG_BOLTED_BACK_ON, SPELLVALUE_BASE_POINT0, heal, me, true);
        uint32 const before = FrenzyStacks();
        SetFrenzy(FrenzyAfterHome(before));
        Mechanic::Cancel(me, pile.soak);
        c->DespawnOrUnsummon();
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "pile-home",
            Acore::StringFormat("heal={} frenzy={}->{} groundPct={}", heal, before, FrenzyStacks(),
                pile.state.GrindPct()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RG4 Ossuary Eruption
    // ----------------------------------------------------------------------------------------------------------------

    void StartEruption(bool heroic)
    {
        Position const at = me->GetPosition();
        DungeonKit::CastBar(me, SPELL_RG_ERUPTION_CAST, nullptr, EMOTE_RATTLEGORE_ERUPTION);
        RegisterRing(at, 0, heroic);
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "eruption",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}) rings={}", heroic ? 1 : 0, at.GetPositionX(),
                at.GetPositionY(), EruptionRings(heroic).size()));
    }

    // Ring `index`, registered when the previous one resolves (one ring marker at a time; the chain stops with him).
    void RegisterRing(Position const& at, std::size_t index, bool heroic)
    {
        std::vector<EruptionRing> const rings = EruptionRings(heroic);
        if (index >= rings.size())
            return;
        EruptionRing const& ring = rings[index];
        MechanicRef ref = ring.inner <= 0.f
            ? Mechanic::Circle(me, at, ring.outer, Ms(ring.warnMs))
            : Mechanic::Donut(me, at, ring.inner, ring.outer, Ms(ring.warnMs));
        ref.Damage(kEruptionPct(heroic)).Spell(SPELL_RG_ERUPTION_HIT)
            .Tag(ring.inward ? TAG_ERUPTION_IN : TAG_ERUPTION_OUT);
        if (index + 1 < rings.size())
            ref.OnResolve(OnRattlegore([at, index, heroic, gen = _generation](boss_rattlegore_rework& ai,
                BossMechanics::ResolveResult const& /*result*/)
            {
                if (gen == ai._generation)
                    ai.RegisterRing(at, index + 1, heroic);
            }));
        Track(ref.Handle());
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RG5 Salvage
    // ----------------------------------------------------------------------------------------------------------------

    enum class SalvagePhase : uint8
    {
        None,
        Walking,
        Channeling,
    };

    void SpawnConstructs()
    {
        DespawnConstructs();
        Vec2 const center = RattlegoreArena().regions.front().center;
        for (std::size_t i = 0; i < kConstructSpots.size(); ++i)
        {
            Point3 const spot = kConstructSpots[i];
            float const z = FloorZ(me, spot.XY()).value_or(spot.z);
            Creature* c = me->SummonCreature(NPC_SC_UNFINISHED_CONSTRUCT, spot.x, spot.y, z,
                DungeonKit::BearingTo(spot.XY(), center), TEMPSUMMON_MANUAL_DESPAWN);
            _constructs[i] = c ? c->GetGUID() : ObjectGuid::Empty;
            _standing[i] = c != nullptr;
        }
    }

    void DespawnConstructs()
    {
        for (std::size_t i = 0; i < _constructs.size(); ++i)
        {
            if (Creature* c = _constructs[i].IsEmpty() ? nullptr : me->GetMap()->GetCreature(_constructs[i]))
                c->DespawnOrUnsummon();
            _constructs[i] = ObjectGuid::Empty;
            _standing[i] = false;
        }
    }

    uint32 ConstructsStanding() const
    {
        uint32 n = 0;
        for (bool s : _standing)
            n += s ? 1 : 0;
        return n;
    }

    // False when no construct is left.
    bool StartSalvage(bool heroic)
    {
        std::optional<std::size_t> const index = NearestConstruct(DungeonKit::PlaneOf(me), _standing);
        Creature* construct = index ? me->GetMap()->GetCreature(_constructs[*index]) : nullptr;
        if (!construct)
        {
            if (index)
                _standing[*index] = false;     // gone (a GM despawn): spent
            return false;
        }
        _salvage = SalvagePhase::Walking;
        _salvageIndex = *index;
        _salvageHeroic = heroic;
        _salvageWalkUntil = _clockMs + kSalvageWalkTimeoutMs;
        _salvageNotBefore = _clockMs + kSalvageEveryMs;
        Mechanic::NoteNextCastIn(me, SPELL_RG_SALVAGE, Ms(kSalvageEveryMs));
        Talk(EMOTE_RATTLEGORE_SALVAGE);
        me->InterruptNonMeleeSpells(false);
        me->AttackStop();
        me->SetReactState(REACT_PASSIVE);
        // A spot just short of the construct, on his side of it.
        Vec2 const from = DungeonKit::PlaneOf(construct);
        float const reach = me->GetCombatReach() + construct->GetCombatReach() + 1.f;
        Vec2 const spot = DungeonKit::Advance(from, DungeonKit::BearingTo(from, DungeonKit::PlaneOf(me)), reach);
        float const z = FloorZ(me, spot).value_or(construct->GetPositionZ());
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MovePoint(POINT_SALVAGE, Position(spot.x, spot.y, z, 0.f));
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "salvage-walk",
            Acore::StringFormat("heroic={} construct={} left={}", heroic ? 1 : 0, *index, ConstructsStanding()));
        return true;
    }

    void BeginSalvageChannel()
    {
        if (_salvage != SalvagePhase::Walking)
            return;
        me->GetMotionMaster()->Clear();
        me->StopMoving();
        if (Creature* construct = me->GetMap()->GetCreature(_constructs[_salvageIndex]))
            me->SetFacingToObject(construct);
        _salvageDamage = 0;
        _salvageBreakSent = false;
        _salvage = SalvagePhase::Channeling;    // before the cast: a failed start reports through OnSpellFailed
        SpellCastResult const result = me->CastSpell(me, SPELL_RG_SALVAGE, false);
        if (result != SPELL_CAST_OK)
        {
            if (_salvage == SalvagePhase::Channeling)
            {
                DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "salvage-failed",
                    Acore::StringFormat("cast result {}", int(result)));
                EndSalvage(false);
            }
            return;
        }
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "salvage-channel",
            Acore::StringFormat("construct={} breakAt={}", _salvageIndex, SalvageBreakDamage(me->GetMaxHealth())));
    }

    // The channel ended: `completed` = not stopped (he heals; heroic: Reinforced). Either way the construct is spent.
    void EndSalvage(bool completed)
    {
        if (_salvage == SalvagePhase::None)
            return;
        _salvage = SalvagePhase::None;
        _standing[_salvageIndex] = false;
        if (Creature* construct = me->GetMap()->GetCreature(_constructs[_salvageIndex]))
        {
            construct->CastSpell(construct, SPELL_RG_GROUND_TO_DUST, true);
            construct->DespawnOrUnsummon(1500ms);
        }
        uint32 reinforced = DungeonKit::Stacks(me, SPELL_RG_REINFORCED);
        int32 heal = 0;
        if (completed && me->IsAlive())
        {
            heal = PctOfMax(me->GetMaxHealth(), kSalvageHealPct);
            me->CastCustomSpell(SPELL_RG_SALVAGE_HEAL, SPELLVALUE_BASE_POINT0, heal, me, true);
            if (_salvageHeroic)
                reinforced = DungeonKit::AddStacks(me, SPELL_RG_REINFORCED, 1, me, kReinforcedMaxStacks);
        }
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, completed ? "salvage-completed" : "salvage-stopped",
            Acore::StringFormat("construct={} heal={} reinforced={} left={}", _salvageIndex, heal, reinforced,
                ConstructsStanding()));
        if (!me->IsAlive())
            return;
        me->SetReactState(REACT_AGGRESSIVE);
        if (Unit* victim = SelectTarget(SelectTargetMethod::MaxThreat, 0))
            AttackStart(victim);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (SC): target priority Rattlegore (no kill order); interrupt Salvage; no dispels
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        using BossMechanics::Who;
        BossMechanics::Descriptor d;
        d.interrupts.emplace_back(NPC_RATTLEGORE, SPELL_RG_SALVAGE, 2, Ms(kSalvageEveryMs));
        d.targets.emplace_back(NPC_RATTLEGORE, 1, Who::Any);
        d.ignores.emplace_back(NPC_SC_LOOSE_PART);
        d.ignores.emplace_back(NPC_SC_UNFINISHED_CONSTRUCT);
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest scholo rattlegore` entry points (`heroic` forces the heroic form on a normal map)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Break,
        Eruption,
        Salvage,
    };

    // An empty string when fired; otherwise why not.
    std::string TestFire(TestMechanic mechanic, bool heroic)
    {
        if (mechanic != TestMechanic::Eruption && !me->IsEngaged())
            return "Rattlegore must be in combat (the piles crawl and the constructs stand only in the fight).";
        if (me->HasUnitState(UNIT_STATE_CASTING) || _salvage != SalvagePhase::None)
            return "Rattlegore is casting or salvaging; try again in a moment.";
        switch (mechanic)
        {
            case TestMechanic::Break:
                Break(heroic, true);
                break;
            case TestMechanic::Eruption:
                StartEruption(heroic);
                break;
            case TestMechanic::Salvage:
                if (!StartSalvage(heroic))
                    return "No Unfinished Construct is left.";
                break;
        }
        return {};
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    void TestFrenzy(uint32 stacks)
    {
        SetFrenzy(std::min(stacks, kFrenzyMaxStacks));
    }

    std::string TestState() const
    {
        std::string piles;
        for (Pile const& pile : _piles)
            piles += Acore::StringFormat(" [phase={} ground={}%]", int(pile.state.GetPhase()), pile.state.GrindPct());
        return Acore::StringFormat("clock={}s breaks={} thresholds={}/6 frenzy={} reinforced={} constructs={} "
            "salvage={} salvageNotBefore={}s eruptionAt={}s piles={}{}", _clockMs / 1000, _ladder.Breaks(),
            _ladder.FiredCount(), FrenzyStacks(), DungeonKit::Stacks(me, SPELL_RG_REINFORCED), ConstructsStanding(),
            int(_salvage), _salvageNotBefore / 1000, _nextEruptionMs / 1000, _piles.size(), piles);
    }

private:
    static float Rand01()
    {
        return std::min(0.9999f, static_cast<float>(rand_norm()));
    }

    // Runs `fn(ai, result)` on this boss when a mechanic resolves, if he is still there. Captures the map and the guid
    // only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnRattlegore(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (result.fizzled || !map)
                return;
            Creature* boss = map->GetCreature(guid);
            if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_rattlegore_rework*>(boss->AI()))
                fn(*ai, result);
        };
    }

    void Track(MechanicHandle handle)
    {
        if (handle)
            _live.push_back(handle);
    }

    struct Launch
    {
        Position at;
        uint64 dueMs = 0;
    };

    // The pull's state: nothing pending, no piles, no constructs, no stacks (Reset, evade, death, a new pull).
    void Cleanup()
    {
        ++_generation;      // chained rings and landings of an older pull stop
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        for (Pile const& pile : _piles)
        {
            Mechanic::Cancel(me, pile.soak);
            if (Creature* c = me->GetMap()->GetCreature(pile.guid))
                c->DespawnOrUnsummon();
        }
        _piles.clear();
        _pendingLandings.clear();
        _launches.clear();
        DespawnConstructs();
        if (_salvage != SalvagePhase::None && me->IsAlive())
            me->SetReactState(REACT_AGGRESSIVE);
        _salvage = SalvagePhase::None;
        _salvageDamage = 0;
        _salvageBreakSent = false;
        _salvageNotBefore = 0;
        _salvageOpen = false;
        _ladder.Reset();
        me->RemoveAurasDueToSpell(SPELL_RG_FRENZY);
        me->RemoveAurasDueToSpell(SPELL_RG_REINFORCED);
        _clockMs = 0;
        _nextFrenzyMs = 0;
        _nextEruptionMs = kEruptionFirstMs;
        _nextStrikeMs = 0;
        _nextKnockMs = 0;
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    BreakLadder _ladder;
    uint64 _clockMs = 0;                        // ms since the pull: every timer of the fight
    uint64 _nextFrenzyMs = 0;
    uint64 _nextEruptionMs = 0;
    uint64 _nextStrikeMs = 0;
    uint64 _nextKnockMs = 0;
    uint32 _generation = 0;
    std::vector<Pile> _piles;
    std::vector<Vec2> _pendingLandings;
    std::vector<Launch> _launches;
    std::vector<MechanicHandle> _live;
    std::array<ObjectGuid, 4> _constructs{};
    std::array<bool, 4> _standing{};
    SalvagePhase _salvage = SalvagePhase::None;
    std::size_t _salvageIndex = 0;
    bool _salvageHeroic = false;
    bool _salvageBreakSent = false;
    bool _salvageOpen = false;                  // the second break has happened (the first Salvage is timed)
    uint64 _salvageDamage = 0;
    uint64 _salvageWalkUntil = 0;
    uint64 _salvageNotBefore = 0;
};

// The loose part (300531) and the Unfinished Construct (300532): props the boss moves and despawns. Never attack,
// never evade (NullCreatureAI); the pile's crawl is the boss's MovePoint.
struct npc_sc_loose_part : public NullCreatureAI
{
    explicit npc_sc_loose_part(Creature* creature) : NullCreatureAI(creature) { }
};

struct npc_sc_unfinished_construct : public NullCreatureAI
{
    explicit npc_sc_unfinished_construct(Creature* creature) : NullCreatureAI(creature) { }
};

// RG2 the grind tick 206132, cast by the pile on each player standing on it: 5% (heroic 6%) of the reference row, set
// at launch so the target's defensives count (the spell ignores caster modifiers).
class spell_sc_rattlegore_grind : public SpellScript
{
    PrepareSpellScript(spell_sc_rattlegore_grind);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;
        SetEffectValue(static_cast<int32>(DungeonKit::RefFlatOn(caster, GetHitUnit(),
            kPileTickPct(IsHeroicMap(caster)))));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_sc_rattlegore_grind::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

namespace
{
    boss_rattlegore_rework* FindRattlegoreAI(ChatHandler* handler)
    {
        Creature* boss = ScholoTest::FindBoss(handler, NPC_RATTLEGORE);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_rattlegore_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Rattlegore is not running boss_rattlegore_rework (check the ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_rattlegore_rework::TestMechanic mechanic, Optional<uint32> heroic,
        char const* what)
    {
        boss_rattlegore_rework* ai = FindRattlegoreAI(handler);
        if (!ai)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        std::string const error = ai->TestFire(mechanic, isHeroic);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Rattlegore: {} fired ({}).", what, isHeroic ? "heroic" : "normal");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return ScholoTest::ShowBossInfo(handler, NPC_RATTLEGORE, BOSS_RATTLEGORE);
    }

    bool HandleBreak(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_rattlegore_rework::TestMechanic::Break, heroic,
            "a break (RG1 Part lands, then RG2 piles; heroic: two)");
    }

    bool HandleEruption(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_rattlegore_rework::TestMechanic::Eruption, heroic,
            "Ossuary Eruption (RG4; heroic: out and back)");
    }

    bool HandleSalvage(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_rattlegore_rework::TestMechanic::Salvage, heroic,
            "Salvage (RG5; heroic: Reinforced when missed)");
    }

    // `.dbtest scholo rattlegore frenzy <n>`: sets his Frenzy stacks (RG8).
    bool HandleFrenzy(ChatHandler* handler, uint32 stacks)
    {
        boss_rattlegore_rework* ai = FindRattlegoreAI(handler);
        if (!ai)
            return false;
        ai->TestFrenzy(stacks);
        handler->PSendSysMessage("Rattlegore: Frenzy set to {} (cap {}).", std::min(stacks, kFrenzyMaxStacks),
            kFrenzyMaxStacks);
        return true;
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_rattlegore_rework* ai = FindRattlegoreAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Rattlegore: {}", ai->TestState());
        return true;
    }

    // `.dbtest scholo rattlegore <sub> [1]`: the optional 1 forces the heroic form (0 forces normal); default: the
    // map's.
    ChatCommandTable const& RattlegoreTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",    HandleState,    SEC_GAMEMASTER, Console::No },
            { "break",    HandleBreak,    SEC_GAMEMASTER, Console::No },
            { "eruption", HandleEruption, SEC_GAMEMASTER, Console::No },
            { "salvage",  HandleSalvage,  SEC_GAMEMASTER, Console::No },
            { "frenzy",   HandleFrenzy,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_rattlegore_rework()
{
    RegisterDungeonReworkCreatureAI(boss_rattlegore_rework, ScholomanceRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sc_loose_part, ScholomanceRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sc_unfinished_construct, ScholomanceRework::kInstanceScriptName);
    RegisterSpellScript(spell_sc_rattlegore_grind);
    ScholoTest::RegisterBoss("rattlegore", RattlegoreTestCommands());
}
