/*
 * mod-dungeon-bosses, Scarlet Monastery D2: Ironspine (6489), "Spare Parts in a rotting yard". Build spec GY 378-433
 * (docs/dungeons/scarlet-monastery-1-graveyard.md "Ironspine"), handoff section 3.5 row D2, sections 3.6, 3.8, 3.10 and
 * section 7 #24 A. Replaces stock SmartAI 6489 (the 90% despawn on AI init, Curse of Weakness 702, Poison Cloud 3815:
 * WP-S0's SQL rev drops the rows); bound by apps/dbc-tools source/npcs/scarlet_monastery/ironspine.py; his spawn (guid
 * 12164) moves to the open lawn in rev_ironspine_scarlet_monastery.sql. Pure rules: IronspineLogic.h.
 *
 * He always spawns now (a boss, hub ruling 11) and fights alone; the Unfettered Spirits stay trash.
 *
 *   IR1  Grave Rot   6 s, then every 14 s (2 s less per part killed for good, at least 8 s): a 1.5 s cast (emote line
 *                    0) and a 7 yd pool under him (a persistent registry zone, the kit's GrowingZone): 5% / 8% Nature a
 *                    second, no Weakened. Normal: it stays for the fight. Heroic: it grows to 10 yd over 30 s and fades
 *                    at 60 s. The tank drags him off it.
 *   IR2  Shatter     12 s, then every 22 s (heroic 20 s): emote line 1 and one part (heroic two) flies off in the order
 *                    Fist, Ribcage, Eye. A part that reaches him reattaches: he heals 10% / 15% and gains Reassembled
 *                    (+10% damage done; 3 at most on normal), and it goes to the back of the queue. A part killed is
 *                    gone for good: it crumbles into a pool where it dies and his rot comes faster. All three gone:
 *                    emote line 2.
 *   IR3  The Fist    lands 15-20 yd out, then knuckle-hops home 6 yd every 3 s (a jump arc: the model has no walk); a
 *                    5 yd marker at its next landing 2 s before it lands: 35% / 45% Physical + Weakened, the tank too.
 *   IR4  The Ribcage flies onto a random non-tank (heroic: and everyone within 6 yd of them, the tank too) and closes
 *                    (emote line 3; DungeonKit::HoldInUnit): rooted up to 12 s, every other action kept; the Crush
 *                    ticks every 2 s rising 1..6 to 50% / 120% by 12 s. Killing the cage frees them (the part dies for
 *                    good); a root break frees that player only. At 12 s it springs home and reattaches.
 *   IR5  The Eye     floats home at 1.5 yd/s; while it is loose each Grave Rot also drops a pool under 2 random players
 *                    (tank included) after a 2 s marker.
 *   IR6  Glare       heroic, while the Eye is loose: 6 s after it lands, then every 6 s, a 2 s cast (the Eye's line 0);
 *                    anyone facing the Eye within 40 yd is stunned 2 s (BM's Gaze kind: look away).
 *   Arena            ScarletMonasteryRework::LeashOptions on SmIronspine::FightArena() (the lawn disc, cut short of
 *                    the council; no grips).
 *
 * Every timer runs on the AI's own clock. Every firing logs one INFO line "sm ironspine <mechanic> ..."
 * (module.dungeonbosses); the pull line comes from OnBossPull.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "DungeonKitZones.h"
#include "IronspineLogic.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "Random.h"
#include "ScarletMonasteryKit.h"
#include "ScarletMonasteryRework.h"
#include "ScarletMonasteryTestCommand.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <optional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScarletMonasteryRework;
using namespace SmIronspine;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kLogBoss = "ironspine";

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(ms);
    }

    float Rand01()
    {
        return std::min(0.9999f, static_cast<float>(rand_norm()));
    }

    // The bots' planned spots on the lawn (the arena's cut disc, 2 yd in; MN-3: short of the council).
    BossMechanics::SpotBounds LawnBounds()
    {
        std::vector<Position> points;
        for (Vec2 const& p : YardPolygon(kBoundsRadiusYd, kYardNorthY - kBoundsNorthInsetYd))
            points.emplace_back(p.x, p.y, kHomeZ, 0.f);
        BossMechanics::SpotBounds bounds;
        bounds.Polygon(std::move(points), kArenaZMin, kArenaZMax);
        return bounds;
    }

    bool CountsAsPlayer(Player const* p)
    {
        return p && p->IsInWorld() && p->IsAlive() && !p->IsGameMaster();
    }
}

// Ironspine 6489
struct boss_ironspine_rework : public BossAI
{
    explicit boss_ironspine_rework(Creature* creature)
        : BossAI(creature, BOSS_IRONSPINE), _arena(FightArena(), LeashOptions(kLogBoss)) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

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

        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        OnBossPull(me, kLogBoss);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_IRONSPINE;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        uint32 const killed = _queue.KilledCount();
        uint32 const stacks = DungeonKit::Stacks(me, SPELL_IR_REASSEMBLED);
        BossAI::JustDied(killer);   // DONE, the summons despawn, the encounter ends
        Cleanup();
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "death",
            Acore::StringFormat("parts-killed={} reassembled={} clock={}s killer={}", killed, stacks,
                _deathClockMs / 1000, killer ? killer->GetName() : "none"));
    }

    // The parts fight (zoned into combat, BossAI's way); the pool stalkers are props.
    void JustSummoned(Creature* summon) override
    {
        if (PartOf(summon->GetEntry()))
        {
            BossAI::JustSummoned(summon);
            return;
        }
        summons.Summon(summon);
    }

    // IR2: a part killed is gone for good.
    void SummonedCreatureDies(Creature* summon, Unit* killer) override
    {
        std::optional<Part> const part = PartOf(summon->GetEntry());
        if (!part)
            return;
        PartState& s = State(*part);
        if (s.unit != summon->GetGUID() || s.phase == Phase::Dead)
            return;
        PartKilled(*part, summon, killer);
    }

    // A part that left the world some other way (a GM, a grid unload) is back at home; never counted as killed.
    void SummonedCreatureDespawn(Creature* summon) override
    {
        if (std::optional<Part> const part = PartOf(summon->GetEntry()))
        {
            PartState& s = State(*part);
            if (s.unit == summon->GetGUID() && s.phase != Phase::Dead && s.phase != Phase::Home)
            {
                ReleaseCage(s, "despawned");
                CancelPartMechanics(s);
                s = PartState{};
                _queue.Return(*part);
                DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "part-lost", PartName(*part));
            }
        }
        BossAI::SummonedCreatureDespawn(summon);
    }

    void UpdateAI(uint32 diff) override
    {
        _holds.Update(me, diff);    // a hold ends with its cage even out of combat
        if (!UpdateVictim())
            return;

        _clockMs += diff;
        _deathClockMs = _clockMs;
        bool const heroic = IsHeroicMap(me);
        _pools.Update(me, diff);
        UpdateParts(heroic);

        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        if (_clockMs >= _nextShatterAt)
            Shatter(heroic);
        if (_clockMs >= _nextRotAt && !me->HasUnitState(UNIT_STATE_CASTING))
            GraveRot(heroic);

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // IR1 Grave Rot (and IR5 the Eye's pools, IR2 the crumbled parts)
    // ----------------------------------------------------------------------------------------------------------------

    void GraveRot(bool heroic)
    {
        DungeonKit::CastBar(me, SPELL_IR_GRAVE_ROT_CAST, nullptr, EMOTE_IR_GRAVE_ROT);
        Position const at = me->GetPosition();
        uint32 const id = AddPool(at, heroic, kRotCastMs, TAG_IR_GRAVE_ROT, "grave-rot");
        uint32 eyePools = 0;
        if (State(Part::Eye).phase == Phase::Loose)
            eyePools = EyePools(heroic);
        _lastRotAt = _clockMs;
        _nextRotAt = _clockMs + RotEveryMs(_queue.KilledCount());
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "grave-rot",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}) zone={} eye-pools={} next={}s pools={}", heroic ? 1 : 0,
                at.GetPositionX(), at.GetPositionY(), id, eyePools, (_nextRotAt - _clockMs) / 1000, _pools.Count()));
    }

    // IR5: a pool under 2 random players (the tank included), each marked 2 s first. Never under a Ribcage prisoner:
    // a rooted player could not step out of it.
    uint32 EyePools(bool heroic)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        GuidSet held;
        for (Prisoner const& p : State(Part::Ribcage).prisoners)
            held.insert(p.guid);
        DungeonKit::ExcludeGuids(rule, held);
        uint32 n = 0;
        for (Player* p : DungeonKit::PickPlayers(me, rule, kEyePools))
        {
            me->CastSpell(p, SPELL_IR_EYE_SIGHT, true);
            if (AddPool(p->GetPosition(), heroic, kEyePoolWarnMs, TAG_IR_EYE_POOL, "eye-pool"))
                ++n;
        }
        return n;
    }

    // One rot pool at `at`: the persistent registry zone with its ground look (a stalker wearing the rung aura).
    uint32 AddPool(Position const& at, bool heroic, uint32 warnMs, uint32 tag, char const* name)
    {
        DungeonKit::GrowingZoneSpec spec;
        spec.anchor = BossMechanics::Anchor(at);
        spec.fromYd = kRotFromYd;
        spec.toYd = kRotToYd(heroic);
        if (heroic)
        {
            spec.overMs = kRotGrowOverMs;
            spec.stepMs = kRotGrowStepMs;
        }
        spec.lifeMs = kRotLifeMs(heroic);
        spec.warnMs = warnMs;
        spec.tickMs = kRotTickMs;
        spec.pct = kRotPct(heroic);
        spec.tankPct = kRotPct(heroic);
        spec.school = SPELL_SCHOOL_NATURE;
        spec.spellId = SPELL_IR_GRAVE_ROT;
        spec.tag = tag;
        for (RotRung const& rung : kRotRungs)
            spec.rungs.push_back({ rung.radiusYd, rung.spellId });
        spec.lookEntry = NPC_SM_STALKER;
        spec.configure = [](MechanicRef& ref)
        {
            ref.Within(LawnBounds());
        };
        spec.dungeon = kLogDungeon;
        spec.boss = kLogBoss;
        spec.name = name;
        uint32 const id = _pools.Add(me, std::move(spec));
        if (id)
            _poolSpots.push_back({ id, { at.GetPositionX(), at.GetPositionY() } });
        return id;
    }

    // The pools still on the ground, at their radius now (the landing pick avoids them).
    std::vector<Circle2> PoolCircles()
    {
        std::vector<Circle2> out;
        _poolSpots.erase(std::remove_if(_poolSpots.begin(), _poolSpots.end(), [this](PoolSpot const& p)
        {
            return !_pools.Get(p.id);
        }), _poolSpots.end());
        for (PoolSpot const& p : _poolSpots)
            if (DungeonKit::GrowingZone const* zone = _pools.Get(p.id))
                out.push_back({ p.at, zone->Radius() });
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // IR2 Shatter
    // ----------------------------------------------------------------------------------------------------------------

    enum class Phase : uint8
    {
        Home,       // part of him
        Flying,     // thrown out (a jump), lands at landAt
        Loose,      // on the floor: hopping (Fist), holding (Ribcage), floating (Eye)
        Springing,  // the Ribcage's jump home, reattaches at landAt
        Dead,       // killed for good
    };

    struct Prisoner
    {
        ObjectGuid guid;
        uint32 ticks = 0;
    };

    struct PartState
    {
        Phase phase = Phase::Home;
        ObjectGuid unit;
        uint64 landAt = 0;
        // IR3 the Fist
        uint64 markerAt = 0;
        uint64 nextMarkerAt = 0;
        uint64 hopJumpAt = 0;
        uint64 hopLandAt = 0;
        bool hopPending = false;
        bool hopJumped = false;
        Hop hop;
        float hopZ = 0.f;
        MechanicHandle hopZone;
        // IR4 the Ribcage
        ObjectGuid target;
        uint64 closedAt = 0;
        uint64 cageEndAt = 0;
        bool closed = false;
        std::vector<Prisoner> prisoners;
        // IR5 / IR6 the Eye
        uint64 nextRepathAt = 0;
        uint64 nextGlareAt = 0;
        MechanicHandle glare;
    };

    struct PoolSpot
    {
        uint32 id = 0;
        Vec2 at;
    };

    PartState& State(Part part)
    {
        return _parts[PartIndex(part)];
    }

    Creature* PartUnit(PartState const& s) const
    {
        return s.unit.IsEmpty() ? nullptr : me->GetMap()->GetCreature(s.unit);
    }

    void Shatter(bool heroic)
    {
        _nextShatterAt = _clockMs + kShatterEveryMs(heroic);
        std::vector<Part> const parts = _queue.Take(kPartsPerShatter(heroic));
        if (parts.empty())
        {
            DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "shatter-skipped",
                Acore::StringFormat("no part at home (killed={})", _queue.KilledCount()));
            return;
        }
        Talk(EMOTE_IR_SHATTER);
        me->CastSpell(me, SPELL_IR_SHATTER, true);
        std::vector<Vec2> taken = LooseSpots();
        std::string names;
        for (Part part : parts)
        {
            LaunchPart(part, heroic, taken);
            names += names.empty() ? PartName(part) : std::string(",") + PartName(part);
        }
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "shatter",
            Acore::StringFormat("heroic={} parts={} next={}s", heroic ? 1 : 0, names, kShatterEveryMs(heroic) / 1000));
    }

    std::vector<Vec2> LooseSpots() const
    {
        std::vector<Vec2> out;
        for (PartState const& s : _parts)
            if (s.phase == Phase::Loose || s.phase == Phase::Flying)
                if (Creature const* unit = PartUnit(s))
                    out.push_back(DungeonKit::PlaneOf(unit));
        return out;
    }

    // A part breaks off: summoned on him and thrown 15-20 yd to open floor (the Ribcage onto a non-tank).
    void LaunchPart(Part part, bool heroic, std::vector<Vec2>& taken)
    {
        Creature* unit = me->SummonCreature(PartEntry(part), me->GetPosition(), TEMPSUMMON_MANUAL_DESPAWN);
        if (!unit)
        {
            _queue.Return(part);
            DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "shatter-failed",
                Acore::StringFormat("{}: summon refused", PartName(part)));
            return;
        }
        Mechanic::TrackUnit(me, unit);
        PartState& s = State(part);
        s = PartState{};
        s.unit = unit->GetGUID();

        Position dest = me->GetPosition();
        Player* target = nullptr;
        if (part == Part::Ribcage)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.tankIfAlone = false;
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (target)
        {
            s.target = target->GetGUID();
            dest = target->GetPosition();
        }
        else
            dest = PickLanding(taken);
        taken.push_back({ dest.GetPositionX(), dest.GetPositionY() });

        float const dist = me->GetExactDist2d(&dest);
        DungeonKit::JumpTo(unit, dest, kFlySpeedYdPerSec, kFlyMinSpeedZ);
        s.phase = Phase::Flying;
        s.landAt = _clockMs + FlightMs(dist);
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "part-out",
            Acore::StringFormat("part={} heroic={} to=({:.1f}, {:.1f}) dist={:.1f} target={}", PartName(part),
                heroic ? 1 : 0, dest.GetPositionX(), dest.GetPositionY(), dist, target ? target->GetName() : "floor"));
    }

    // A landing 15-20 yd from him on the lawn, clear of pools and other parts where it can be; a wall in the way
    // shortens a throw, and a throw cut under 13 yd is refused.
    Position PickLanding(std::vector<Vec2> const& taken)
    {
        Vec2 const boss = DungeonKit::PlaneOf(me);
        Arena const arena = FightArena();
        std::vector<Vec2> const ring = LandingRing(boss, Rand01() * DungeonKit::kTwoPi, PoolCircles(), taken);
        for (Vec2 const& c : ring)
        {
            Position const pos = me->GetFirstCollisionPosition(me->GetPositionX(), me->GetPositionY(),
                me->GetPositionZ(), c.x, c.y);
            if (me->GetExactDist2d(&pos) < kLandShortestYd)
                continue;
            if (!arena.Contains({ pos.GetPositionX(), pos.GetPositionY() }, pos.GetPositionZ()))
                continue;
            return pos;
        }
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "landing-fallback", "no clear landing: lands beside him");
        return me->GetFirstCollisionPosition(kLandMinYd, Rand01() * DungeonKit::kTwoPi);
    }

    void UpdateParts(bool heroic)
    {
        for (Part part : kShatterOrder)
        {
            PartState& s = State(part);
            if (s.phase == Phase::Home || s.phase == Phase::Dead)
                continue;
            Creature* unit = PartUnit(s);
            if (!unit || !unit->IsAlive())
                continue;   // SummonedCreatureDies / SummonedCreatureDespawn settle it
            switch (s.phase)
            {
                case Phase::Flying:
                    if (_clockMs >= s.landAt)
                        Landed(part, unit, heroic);
                    break;
                case Phase::Springing:
                    if (_clockMs >= s.landAt)
                        Reattach(part, heroic, "sprang home");
                    break;
                case Phase::Loose:
                    switch (part)
                    {
                        case Part::Fist:
                            UpdateFist(s, unit, heroic);
                            break;
                        case Part::Ribcage:
                            UpdateCage(s, unit, heroic);
                            break;
                        case Part::Eye:
                            UpdateEye(s, unit, heroic);
                            break;
                    }
                    break;
                default:
                    break;
            }
        }
    }

    void Landed(Part part, Creature* unit, bool heroic)
    {
        PartState& s = State(part);
        s.phase = Phase::Loose;
        switch (part)
        {
            case Part::Fist:
                s.nextMarkerAt = _clockMs + kFistFirstMarkerMs;
                unit->CastSpell(unit, SPELL_IR_FIST_LANDING, true);
                break;
            case Part::Eye:
                s.nextRepathAt = _clockMs;
                s.nextGlareAt = _clockMs + kGlareFirstMs;
                break;
            case Part::Ribcage:
                CloseCage(s, unit, heroic);
                break;
        }
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "part-landed",
            Acore::StringFormat("part={} at=({:.1f}, {:.1f}) from-him={:.1f}", PartName(part), unit->GetPositionX(),
                unit->GetPositionY(), me->GetExactDist2d(unit)));
    }

    // A part reaches him: it is part of him again (heal, a Reassembled stack), back of the queue.
    void Reattach(Part part, bool heroic, char const* how)
    {
        PartState& s = State(part);
        Creature* unit = PartUnit(s);
        ReleaseCage(s, "reattached");
        CancelPartMechanics(s);
        s = PartState{};
        if (unit)
            unit->DespawnOrUnsummon();
        _queue.Return(part);
        if (!me->IsAlive())
            return;
        uint32 const heal = PctOfMax(me->GetMaxHealth(), kReattachHealPct(heroic));
        if (heal)
            me->CastCustomSpell(SPELL_IR_REASSEMBLE_HEAL, SPELLVALUE_BASE_POINT0, static_cast<int32>(heal), me, true);
        uint32 const before = DungeonKit::Stacks(me, SPELL_IR_REASSEMBLED);
        uint32 const after = ReassembledAfter(before, heroic);
        if (after != before)
            DungeonKit::AddStacks(me, SPELL_IR_REASSEMBLED, static_cast<int32>(after - before), me,
                ReassembledCap(heroic));
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "reattach",
            Acore::StringFormat("part={} how={} heal={} reassembled={}->{} health={}%", PartName(part), how, heal,
                before, after, uint32(me->GetHealthPct())));
    }

    // A part killed: gone for good, a pool where it fell, his rot faster.
    void PartKilled(Part part, Creature* unit, Unit* killer)
    {
        PartState& s = State(part);
        bool const heroic = IsHeroicMap(me);
        Position const at = unit->GetPosition();
        ReleaseCage(s, "cage-killed");
        CancelPartMechanics(s);
        s = PartState{};
        s.phase = Phase::Dead;
        _queue.Kill(part);
        unit->DespawnOrUnsummon(3s);

        uint32 pool = 0;
        if (me->IsAlive() && me->IsEngaged())
        {
            pool = AddPool(at, heroic, kCrumbleWarnMs, TAG_IR_CRUMBLE, "crumble");
            // The rot speeds up now: the next one comes at the new cadence from the last (never in the past).
            if (_lastRotAt)
            {
                uint64 const sooner = std::max<uint64>(_lastRotAt + RotEveryMs(_queue.KilledCount()), _clockMs);
                _nextRotAt = std::min(_nextRotAt, sooner);
            }
            if (_queue.AllKilled() && !_bareEmoted)
            {
                _bareEmoted = true;
                Talk(EMOTE_IR_BARE);
            }
        }
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "part-killed",
            Acore::StringFormat("part={} killer={} at=({:.1f}, {:.1f}) killed={} rot-every={}s pool={}", PartName(part),
                killer ? killer->GetName() : "none", at.GetPositionX(), at.GetPositionY(), _queue.KilledCount(),
                RotEveryMs(_queue.KilledCount()) / 1000, pool));
    }

    void CancelPartMechanics(PartState& s)
    {
        if (s.hopZone)
            Mechanic::Cancel(me, s.hopZone);
        if (s.glare)
            Mechanic::Cancel(me, s.glare);
        s.hopZone = {};
        s.glare = {};
    }

    // ----------------------------------------------------------------------------------------------------------------
    // IR3 the Fist
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateFist(PartState& s, Creature* fist, bool heroic)
    {
        if (!s.hopPending)
        {
            if (_clockMs >= s.nextMarkerAt)
                MarkHop(s, fist, heroic);
            return;
        }
        if (!s.hopJumped && _clockMs >= s.hopJumpAt)
        {
            s.hopJumped = true;
            float const dist = DungeonKit::Distance(DungeonKit::PlaneOf(fist), s.hop.to);
            if (dist > 0.5f)
                DungeonKit::JumpTo(fist, Position(s.hop.to.x, s.hop.to.y, s.hopZ, fist->GetOrientation()),
                    dist / (static_cast<float>(kFistJumpLeadMs) / 1000.f), 4.f);
        }
        if (_clockMs < s.hopLandAt)
            return;
        s.hopPending = false;
        s.hopZone = {};     // resolved (the registry prunes it)
        fist->CastSpell(fist, SPELL_IR_FIST_LANDING, true);
        float const dist = me->GetExactDist2d(fist);
        if (s.hop.last && Arrived(dist, me->GetCombatReach()))
        {
            Reattach(Part::Fist, heroic, "hopped home");
            return;
        }
        s.nextMarkerAt = s.markerAt + kFistHopEveryMs;
    }

    // The next hop's 5 yd marker, 2 s before the Fist lands on it.
    void MarkHop(PartState& s, Creature* fist, bool heroic)
    {
        Hop hop = NextHop(DungeonKit::PlaneOf(fist), DungeonKit::PlaneOf(me),
            me->GetCombatReach() + kFistStopBeyondReachYd);
        Position const to = fist->GetFirstCollisionPosition(fist->GetPositionX(), fist->GetPositionY(),
            fist->GetPositionZ(), hop.to.x, hop.to.y);
        hop.to = { to.GetPositionX(), to.GetPositionY() };
        float const pct = kFistPct(heroic);
        MechanicRef ref = Mechanic::Circle(me, to, kFistMarkerYd, Ms(kFistMarkerWarnMs));
        ref.Damage(pct).TankDamage(pct).Weakened().Spell(SPELL_IR_FIST_SLAM).Within(LawnBounds()).Tag(TAG_IR_FIST);
        s.hopZone = ref.Handle();
        s.hop = hop;
        s.hopZ = to.GetPositionZ();
        s.markerAt = _clockMs;
        s.hopJumpAt = _clockMs + kFistMarkerWarnMs - kFistJumpLeadMs;
        s.hopLandAt = _clockMs + kFistMarkerWarnMs;
        s.hopPending = true;
        s.hopJumped = false;
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "fist-hop",
            Acore::StringFormat("to=({:.1f}, {:.1f}) last={} pct={:.0f} to-him={:.1f}", hop.to.x, hop.to.y,
                hop.last ? 1 : 0, pct, DungeonKit::Distance(hop.to, DungeonKit::PlaneOf(me))));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // IR4 the Ribcage and the Crush
    // ----------------------------------------------------------------------------------------------------------------

    void CloseCage(PartState& s, Creature* cage, bool heroic)
    {
        s.closedAt = _clockMs;
        s.cageEndAt = _clockMs + kCageHoldMs;
        Player* target = s.target.IsEmpty() ? nullptr : ObjectAccessor::GetPlayer(*me, s.target);
        std::vector<Player*> inside;
        if (CountsAsPlayer(target) && target->IsInMap(me) && cage->GetExactDist2d(target) <= kCageCloseReachYd)
        {
            inside.push_back(target);
            float const nearby = kCageNearbyYd(heroic);
            if (nearby > 0.f)
                for (auto const& ref : me->GetMap()->GetPlayers())
                {
                    Player* p = ref.GetSource();
                    if (p != target && CountsAsPlayer(p) && p->GetExactDist2d(target) <= nearby)
                        inside.push_back(p);
                }
        }

        std::string names;
        for (Player* p : inside)
        {
            DungeonKit::HoldSpec spec;
            spec.holdSpell = SPELL_IR_CRUSH;
            spec.maxHold = Ms(kCageHoldMs + kCageHoldSlackMs);
            spec.onRelease = [](ObjectGuid holder, ObjectGuid held, DungeonKit::HoldEnd why)
            {
                DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "crush-end",
                    Acore::StringFormat("held={} cage={} why={}", held.ToString(), holder.ToString(),
                        DungeonKit::HoldEndName(why)));
            };
            if (!_holds.Hold(cage, p, std::move(spec)))
            {
                DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "cage-refused",
                    Acore::StringFormat("{} (root immune or already held)", p->GetName()));
                continue;
            }
            s.prisoners.push_back({ p->GetGUID(), 0 });
            names += names.empty() ? p->GetName() : "," + p->GetName();
        }
        if (!s.prisoners.empty())
        {
            s.closed = true;
            cage->CastSpell(cage, SPELL_IR_RIBCAGE_CLOSED, true);
            Talk(EMOTE_IR_RIBCAGE, target);
        }
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "ribcage",
            Acore::StringFormat("heroic={} target={} prisoners=[{}] crush={:.0f}%", heroic ? 1 : 0,
                target ? target->GetName() : "none", names, kCrushTotalPct(heroic)));
    }

    void UpdateCage(PartState& s, Creature* cage, bool heroic)
    {
        for (auto it = s.prisoners.begin(); it != s.prisoners.end();)
        {
            Player* p = ObjectAccessor::GetPlayer(*me, it->guid);
            if (!CountsAsPlayer(p) || !p->IsInMap(me) || !_holds.IsHeld(it->guid))
            {
                if (_holds.IsHeld(it->guid))
                    _holds.Release(me, it->guid);
                it = s.prisoners.erase(it);
                continue;
            }
            // A root break (Hand of Freedom, Escape Artist, a shapeshift) took the Crush off: that player is free.
            if (!p->HasAura(SPELL_IR_CRUSH))
            {
                _holds.Release(me, it->guid);
                DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "root-break",
                    Acore::StringFormat("{} after {} ticks", p->GetName(), it->ticks));
                it = s.prisoners.erase(it);
                continue;
            }
            while (it->ticks < kCrushTicks && _clockMs >= s.closedAt + uint64(kCrushTickMs) * (it->ticks + 1))
            {
                ++it->ticks;
                uint32 const amount = DungeonKit::RefFlatOn(me, p, CrushTickPct(heroic, it->ticks));
                if (amount)
                    cage->CastCustomSpell(SPELL_IR_CRUSH_TICK, SPELLVALUE_BASE_POINT0, static_cast<int32>(amount), p,
                        true);
            }
            ++it;
        }
        if (s.closed && s.prisoners.empty())
        {
            s.closed = false;
            cage->RemoveAurasDueToSpell(SPELL_IR_RIBCAGE_CLOSED);
        }
        if (_clockMs >= s.cageEndAt)
            SpringHome(s, cage);
    }

    // 12 s up: the cage lets go and springs home (it reattaches when it lands).
    void SpringHome(PartState& s, Creature* cage)
    {
        ReleaseCage(s, "timeout");
        Position const edge = BossEdgeFrom(cage);
        float const dist = cage->GetExactDist2d(&edge);
        DungeonKit::JumpTo(cage, edge, kFlySpeedYdPerSec, kFlyMinSpeedZ);
        s.phase = Phase::Springing;
        s.landAt = _clockMs + FlightMs(dist);
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "ribcage-springs", Acore::StringFormat("dist={:.1f}", dist));
    }

    void ReleaseCage(PartState& s, char const* why)
    {
        for (Prisoner const& p : s.prisoners)
            if (_holds.IsHeld(p.guid))
                _holds.Release(me, p.guid);
        if (!s.prisoners.empty())
            DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "cage-open",
                Acore::StringFormat("why={} prisoners={}", why, s.prisoners.size()));
        s.prisoners.clear();
        if (s.closed)
            if (Creature* cage = PartUnit(s))
                cage->RemoveAurasDueToSpell(SPELL_IR_RIBCAGE_CLOSED);
        s.closed = false;
    }

    // The point at his edge on the side of `unit` (a part's last stop).
    Position BossEdgeFrom(WorldObject const* unit) const
    {
        Vec2 const boss = DungeonKit::PlaneOf(me);
        Vec2 const edge = DungeonKit::Advance(boss, DungeonKit::BearingTo(boss, DungeonKit::PlaneOf(unit)),
            me->GetCombatReach() + kFistStopBeyondReachYd);
        return Position(edge.x, edge.y, me->GetPositionZ(), 0.f);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // IR5 / IR6 the Eye
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateEye(PartState& s, Creature* eye, bool heroic)
    {
        if (Arrived(me->GetExactDist2d(eye), me->GetCombatReach()) && !eye->HasUnitState(UNIT_STATE_CASTING))
        {
            Reattach(Part::Eye, heroic, "floated home");
            return;
        }
        if (heroic && _clockMs >= s.nextGlareAt)
        {
            s.nextGlareAt = _clockMs + kGlareEveryMs;
            Glare(s, eye);
        }
        if (_clockMs >= s.nextRepathAt && !eye->HasUnitState(UNIT_STATE_CASTING))
        {
            s.nextRepathAt = _clockMs + kEyeRepathMs;
            eye->GetMotionMaster()->MovePoint(POINT_IR_EYE_HOME, me->GetPosition(), FORCED_MOVEMENT_WALK,
                kEyeSpeedYdPerSec);
        }
    }

    // IR6 heroic: the Eye opens wide; anyone facing it within 40 yd when the cast ends is stunned 2 s.
    void Glare(PartState& s, Creature* eye)
    {
        if (s.glare)
            Mechanic::Cancel(me, s.glare);
        eye->StopMoving();
        DungeonKit::CastBar(eye, SPELL_IR_GLARE_CAST, nullptr, EMOTE_IR_EYE_GLARE);
        BossMechanics::GazeSpec glare(eye);
        glare.Range(kGlareRangeYd);
        MechanicRef ref = Mechanic::Gaze(me, glare, Ms(kGlareCastMs));
        ref.Rider(SPELL_IR_GLARE).Tag(TAG_IR_GLARE);
        ref.OnResolve([](BossMechanics::ResolveResult const& result)
        {
            if (!result.fizzled)
                DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "glare-lands",
                    Acore::StringFormat("caught={}", result.hits.size()));
        });
        s.glare = ref.Handle();
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "glare",
            Acore::StringFormat("eye=({:.1f}, {:.1f}) range={:.0f}", eye->GetPositionX(), eye->GetPositionY(),
                kGlareRangeYd));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (GY "Boss data"): kill order the Ribcage while it holds a player, then loose parts by distance to him,
    // then him; the tank keeps him (the parts at -1 for tanks); no interrupts, no dispels
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        using BossMechanics::Condition;
        using BossMechanics::TargetEntry;
        using BossMechanics::Who;
        BossMechanics::Descriptor d;
        d.targets.push_back(TargetEntry(NPC_SM_IRONSPINE_RIBCAGE, kCagePriority, Who::Dps,
            Condition::HasAura(SPELL_IR_RIBCAGE_CLOSED)).BreakOut());
        for (Part part : kShatterOrder)
        {
            for (NearTier const& tier : kNearTiers)
                d.targets.push_back(TargetEntry(PartEntry(part), tier.priority, Who::Dps,
                    Condition::NearUnit(NPC_IRONSPINE, tier.withinYd)).AoeOk());
            d.targets.push_back(TargetEntry(PartEntry(part), -1, Who::Tank));
        }
        d.targets.emplace_back(NPC_IRONSPINE, 0, Who::Any);
        d.ignores.emplace_back(NPC_SM_STALKER);
        // Neither cast is a kick (both are uninterruptible cast bars): priority 0 = never kick.
        d.interrupts.emplace_back(NPC_IRONSPINE, SPELL_IR_GRAVE_ROT_CAST, 0);
        d.interrupts.emplace_back(NPC_SM_IRONSPINE_EYE, SPELL_IR_GLARE_CAST, 0);
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest sm ironspine` entry points (`heroic` forces the heroic form on a normal map)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Rot,
        Shatter,
        Fist,
        Ribcage,
        Eye,
        Glare,
    };

    // An empty string when fired; otherwise why not.
    std::string TestFire(TestMechanic mechanic, bool heroic)
    {
        if (!me->IsEngaged())
            return "Ironspine must be in combat (the rot, the parts and the Glare run only in the fight).";
        auto launch = [this, heroic](Part part) -> std::string
        {
            if (!_queue.TakePart(part))
                return Acore::StringFormat("The {} is not at home (loose or killed).", PartName(part));
            Talk(EMOTE_IR_SHATTER);
            me->CastSpell(me, SPELL_IR_SHATTER, true);
            std::vector<Vec2> taken = LooseSpots();
            LaunchPart(part, heroic, taken);
            return {};
        };
        switch (mechanic)
        {
            case TestMechanic::Rot:
                GraveRot(heroic);
                return {};
            case TestMechanic::Shatter:
                Shatter(heroic);
                return {};
            case TestMechanic::Fist:
                return launch(Part::Fist);
            case TestMechanic::Ribcage:
                return launch(Part::Ribcage);
            case TestMechanic::Eye:
                return launch(Part::Eye);
            case TestMechanic::Glare:
            {
                PartState& s = State(Part::Eye);
                Creature* eye = PartUnit(s);
                if (s.phase != Phase::Loose || !eye)
                    return "The Eye must be loose (`.dbtest sm ironspine eye` first).";
                Glare(s, eye);
                return {};
            }
        }
        return {};
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    // Sets the Reassembled stacks (0 removes them), capped at the difficulty's.
    uint32 TestStacks(uint32 stacks)
    {
        bool const heroic = IsHeroicMap(me);
        uint32 const capped = std::min(stacks, ReassembledCap(heroic));
        uint32 const before = DungeonKit::Stacks(me, SPELL_IR_REASSEMBLED);
        if (capped != before)
            DungeonKit::AddStacks(me, SPELL_IR_REASSEMBLED, static_cast<int32>(capped) - static_cast<int32>(before), me,
                ReassembledCap(heroic));
        return capped;
    }

    std::string TestState()
    {
        auto phase = [](Phase p) -> char const*
        {
            switch (p)
            {
                case Phase::Home:      return "home";
                case Phase::Flying:    return "flying";
                case Phase::Loose:     return "loose";
                case Phase::Springing: return "springing";
                case Phase::Dead:      return "dead";
            }
            return "?";
        };
        std::string queue;
        for (Part part : _queue.Order())
            queue += queue.empty() ? PartName(part) : std::string(",") + PartName(part);
        PartState const& cage = State(Part::Ribcage);
        return Acore::StringFormat("clock={}s rot={}s shatter={}s rot-every={}s killed={} queue=[{}] fist={} "
            "ribcage={} (prisoners {}) eye={} pools={} holds={} reassembled={}", _clockMs / 1000, _nextRotAt / 1000,
            _nextShatterAt / 1000, RotEveryMs(_queue.KilledCount()) / 1000, _queue.KilledCount(), queue,
            phase(State(Part::Fist).phase), phase(cage.phase), cage.prisoners.size(), phase(State(Part::Eye).phase),
            _pools.Count(), _holds.Count(), DungeonKit::Stacks(me, SPELL_IR_REASSEMBLED));
    }

private:
    // The pull's state: no pools, no parts out, no holds, no stacks (Reset, evade, death, a new pull).
    void Cleanup()
    {
        for (PartState& s : _parts)
        {
            ReleaseCage(s, "cleanup");
            CancelPartMechanics(s);
            s = PartState{};
        }
        _holds.Clear(me);
        _pools.Clear(me);
        _poolSpots.clear();
        summons.DespawnAll();
        _queue.Reset();
        if (me->IsAlive())
            me->RemoveAurasDueToSpell(SPELL_IR_REASSEMBLED);
        _clockMs = 0;
        _lastRotAt = 0;
        _nextRotAt = kRotFirstMs;
        _nextShatterAt = kShatterFirstMs;
        _bareEmoted = false;
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::GrowingZones _pools;
    DungeonKit::HoldInUnit _holds;
    ShatterQueue _queue;
    std::array<PartState, kPartCount> _parts{};
    std::vector<PoolSpot> _poolSpots;
    uint64 _clockMs = 0;                        // ms since the pull: every timer of the fight
    uint64 _deathClockMs = 0;
    uint64 _lastRotAt = 0;
    uint64 _nextRotAt = kRotFirstMs;
    uint64 _nextShatterAt = kShatterFirstMs;
    bool _bareEmoted = false;
};

// Ironspine's Fist 300900, Ribcage 300901 and Eye 300902: props the boss throws, moves, reattaches and despawns. They
// never attack (NullCreatureAI is passive); damage lands on them (stun immune 1972, like him: only killing them stops
// them).
struct npc_sm_ironspine_part : public NullCreatureAI
{
    explicit npc_sm_ironspine_part(Creature* creature) : NullCreatureAI(creature) { }

    void InitializeAI() override
    {
        me->SetReactState(REACT_PASSIVE);
    }
};

namespace
{
    boss_ironspine_rework* FindIronspineAI(ChatHandler* handler)
    {
        Creature* boss = SmTest::FindBoss(handler, NPC_IRONSPINE);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_ironspine_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Ironspine is not running boss_ironspine_rework (check the ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_ironspine_rework::TestMechanic mechanic, Optional<uint32> heroic,
        char const* what)
    {
        boss_ironspine_rework* ai = FindIronspineAI(handler);
        if (!ai)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        std::string const error = ai->TestFire(mechanic, isHeroic);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Ironspine: {} fired ({}).", what, isHeroic ? "heroic" : "normal");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return SmTest::ShowBossInfo(handler, NPC_IRONSPINE, BOSS_IRONSPINE);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_ironspine_rework* ai = FindIronspineAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Ironspine: {}", ai->TestState());
        return true;
    }

    bool HandleRot(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_ironspine_rework::TestMechanic::Rot, heroic,
            "Grave Rot (IR1: the cast and a pool under him; IR5 pools while the Eye is loose)");
    }

    bool HandleShatter(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_ironspine_rework::TestMechanic::Shatter, heroic,
            "Shatter (IR2: the next part in the queue, heroic two)");
    }

    bool HandleFist(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_ironspine_rework::TestMechanic::Fist, heroic,
            "the Fist (IR3: lands, then hops home)");
    }

    bool HandleRibcage(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_ironspine_rework::TestMechanic::Ribcage, heroic,
            "the Ribcage (IR4: closes over a non-tank, the Crush)");
    }

    bool HandleEye(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_ironspine_rework::TestMechanic::Eye, heroic,
            "the Eye (IR5: floats home; heroic Glare every 6 s)");
    }

    bool HandleGlare(ChatHandler* handler)
    {
        return Fire(handler, boss_ironspine_rework::TestMechanic::Glare, 1u, "the Glare (IR6: look away)");
    }

    // `.dbtest sm ironspine stacks <n>`: sets his Reassembled stacks (0 removes them).
    bool HandleStacks(ChatHandler* handler, uint32 stacks)
    {
        boss_ironspine_rework* ai = FindIronspineAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Ironspine: Reassembled set to {}.", ai->TestStacks(stacks));
        return true;
    }

    // `.dbtest sm ironspine <sub> [1]`: the optional 1 forces the heroic form (0 forces normal); default: the map's.
    ChatCommandTable const& BossIronspineTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",    HandleInfo,    SEC_GAMEMASTER, Console::No },
            { "state",   HandleState,   SEC_GAMEMASTER, Console::No },
            { "rot",     HandleRot,     SEC_GAMEMASTER, Console::No },
            { "shatter", HandleShatter, SEC_GAMEMASTER, Console::No },
            { "fist",    HandleFist,    SEC_GAMEMASTER, Console::No },
            { "ribcage", HandleRibcage, SEC_GAMEMASTER, Console::No },
            { "eye",     HandleEye,     SEC_GAMEMASTER, Console::No },
            { "glare",   HandleGlare,   SEC_GAMEMASTER, Console::No },
            { "stacks",  HandleStacks,  SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_ironspine_rework()
{
    RegisterDungeonReworkCreatureAI(boss_ironspine_rework, ScarletMonasteryRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sm_ironspine_part, ScarletMonasteryRework::kInstanceScriptName);
    SmTest::RegisterBoss("ironspine", BossIronspineTestCommands());
}
