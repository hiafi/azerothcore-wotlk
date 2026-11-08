/*
 * mod-dungeon-bosses, Scholomance S7: Lorekeeper Polkelt (10901), "Chain Reaction". Build spec SC 1979-2036
 * (docs/dungeons/scholomance-rework.md), handoff section 3.4 rows PK and 3.5 row S7. Replaces stock SmartAI 10901
 * (Volatile Infection 18149 kept here; Corrosive Acid 8245 and Noxious Catalyst 18151 retired: WP-S7's SQL rev drops
 * the rows); bound by apps/dbc-tools source/npcs/scholomance/lorekeeper_polkelt.py. Pure rules: PolkeltLogic.h.
 *
 *   PK1  Raise Specimens   10 s, then every 15 s (emote line 0): 2 walking + 1 rooted (heroic 3 + 3) Unstable (300540)
 *                          and Rooted (300541) Specimens at floor points 8+ yd from every player (heroic rooted 13+ yd
 *                          apart; the measured spots are the fallback). Walkers fight on threat; rooted ones melee only
 *                          what stands in reach
 *   PK2  Fuse and burst    a lethal hit drops a specimen at 1 health: a 2 s fuse (206255), then a 6 yd ring, 30% / 40%
 *                          Nature + Weakened (206250). A specimen inside the ring lights a 1 s chained fuse (206256,
 *                          ruling 18) at any health. Every ring is its own registry circle: overlaps stack
 *   PK3  Catalyst Reaction a kill or chained ring that holds him: 1.5% of his health (206259) and a Corroded stack
 *                          (206260: +5% damage taken, 20 s, refreshes, 10). Rings carry Park() for the bot tank
 *   PK4  Ripe              30 s after its raise (the Ripening clock 206264, a visible swell to 150%), a specimen
 *                          burns a 3 s fuse (206257), then a 12 yd ring, 40% / 55% (206251), lights every specimen in
 *                          it, never reacts with him, and leaves a pool
 *   PK5  Acid Pool         6 yd, 60 s, 8% / 12% per second with the kit's slow (206252; the floor look 206253); at most
 *                          6 / 8 (the user's ruling), the oldest dries up
 *   PK6  Hardened (H)      rooted specimens take 90% less damage (206262): only a burst sets them off
 *   PK7  Noxious Catalyst  heroic: every 10 s each player in the fight carries one more stack (206263, 0.3% per second
 *        (H)               per stack, undispellable, uncapped): the soft enrage
 *   PK8  Volatile Infection stock 18149 on his victim: 7-15 s, then every 40 s (a Disease: the dispel list)
 *   Arena                  ScholomanceRework::LeashOptions on PolkeltArena() (no grips; holds at the edge). The Hall of
 *                          Secrets gate is the instance's door data on BOSS_POLKELT
 *   Detention              the Hall of Secrets solo lesson (HallOfSecretsLesson, registered for S11): 3 / 4 specimens
 *                          walk at the student and burst on reaching them or on death
 *   Examiner (S13)         bind this ScriptName on the Graduate Examiner 300550: the same AI in examiner mode (80k,
 *                          heroic values for both mechanics, no enrage, texts, grades or boss state)
 *
 * The specimens' chain is the SpecimenLab below, one per fight (the boss, the examiner, a detention lesson): it runs
 * on its owner's own clock, never on BossAI's scheduler (a cast bar pauses that one), and owns every specimen, ring
 * and pool it made. Every firing logs one INFO line "scholo polkelt <mechanic> ..." (module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DynamicObject.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "PolkeltLogic.h"
#include "Random.h"
#include "ScholomanceKit.h"
#include "ScholomanceRework.h"
#include "ScholomanceTestCommand.h"
#include "ScriptedCreature.h"
#include "SoloLesson.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <cmath>
#include <memory>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;
using namespace ScholoPolkelt;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kLogBoss = "polkelt";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    float Rand01()
    {
        return std::min(0.9999f, static_cast<float>(rand_norm()));
    }

    char const* KindName(BurstKind kind)
    {
        switch (kind)
        {
            case BurstKind::Kill:    return "kill";
            case BurstKind::Chained: return "chained";
            case BurstKind::Ripe:    return "ripe";
        }
        return "?";
    }

    // The Hall of Secrets floor under `p` (z 85; not the stair or the gate corridor at z 89), else nullopt.
    std::optional<float> FloorZ(WorldObject const* ref, Vec2 p)
    {
        float const z = ref->GetMapHeight(p.x, p.y, kHallFloorZ + 3.f);
        if (z <= INVALID_HEIGHT + 1.f || std::fabs(z - kHallFloorZ) > kHallFloorZBand)
            return std::nullopt;
        return z;
    }

    bool CountsAsPlayer(Player const* p)
    {
        return p && p->IsInWorld() && p->IsAlive() && !p->IsGameMaster();
    }

    // Every living player of the map (not a GM) on the map plane.
    std::vector<Vec2> PlayerSpots(Map* map)
    {
        std::vector<Vec2> spots;
        for (auto const& ref : map->GetPlayers())
            if (Player* p = ref.GetSource(); CountsAsPlayer(p))
                spots.push_back(DungeonKit::PlaneOf(p));
        return spots;
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// The specimens (300540 walking, 300541 rooted). A lethal hit never kills one: it drops it at 1 health and marks it
// collapsed; its owner's SpecimenLab sees that on its next update and lights the fuse (freezing it). Frozen, it takes
// no damage, cannot be attacked and stands still until it bursts and despawns.
// ---------------------------------------------------------------------------------------------------------------------
struct npc_sc_polkelt_specimen : public ScriptedAI
{
    explicit npc_sc_polkelt_specimen(Creature* creature) : ScriptedAI(creature) { }

    bool Rooted() const { return me->GetEntry() == NPC_SC_ROOTED_SPECIMEN; }

    void Reset() override { }

    void AttackStart(Unit* who) override
    {
        if (_frozen || !who)
            return;
        if (Rooted())
            me->Attack(who, true);      // melee only, never chases
        else
            ScriptedAI::AttackStart(who);
    }

    void MoveInLineOfSight(Unit* /*who*/) override { }

    // A specimen that loses its target stays where it is (no run home, no heal): the lab owns its end.
    void EnterEvadeMode(EvadeReason /*why*/) override
    {
        me->AttackStop();
        if (!Rooted())
        {
            me->StopMoving();
            me->GetMotionMaster()->Clear();
            me->GetMotionMaster()->MoveIdle();
        }
    }

    void DamageTaken(Unit* /*attacker*/, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*school*/) override
    {
        if (_frozen)
        {
            damage = 0;
            return;
        }
        if (damage < me->GetHealth())
            return;
        damage = me->GetHealth() > 1 ? me->GetHealth() - 1 : 0;
        _collapsed = true;
        Freeze();
    }

    uint32 GetData(uint32 id) const override
    {
        return id == DATA_SPECIMEN_COLLAPSED && _collapsed ? 1 : 0;
    }

    void SetData(uint32 id, uint32 value) override
    {
        if (!value)
            return;
        if (id == DATA_SPECIMEN_COLLAPSED && !_frozen)
            _collapsed = true;      // `.dbtest scholo polkelt kill`: as if a lethal hit dropped it
        if (id == DATA_SPECIMEN_FROZEN || id == DATA_SPECIMEN_COLLAPSED)
            Freeze();
    }

    void UpdateAI(uint32 /*diff*/) override
    {
        if (_frozen)
            return;
        if (Rooted())
        {
            // Rooted: hit whatever stands in reach (its victim first), never move, never evade.
            Unit* victim = me->GetVictim();
            if (!victim || !victim->IsAlive() || !me->IsWithinMeleeRange(victim))
            {
                victim = nullptr;
                for (auto const& ref : me->GetMap()->GetPlayers())
                {
                    Player* p = ref.GetSource();
                    if (CountsAsPlayer(p) && me->IsWithinMeleeRange(p) && me->IsValidAttackTarget(p))
                    {
                        victim = p;
                        break;
                    }
                }
                if (!victim)
                {
                    if (me->GetVictim())
                        me->AttackStop();
                    return;
                }
                me->Attack(victim, true);
            }
            DoMeleeAttackIfReady();
            return;
        }
        if (!UpdateVictim())
            return;
        DoMeleeAttackIfReady();
    }

private:
    void Freeze()
    {
        if (_frozen)
            return;
        _frozen = true;
        me->SetReactState(REACT_PASSIVE);
        me->AttackStop();
        me->InterruptNonMeleeSpells(false);
        me->StopMoving();
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MoveIdle();
        me->SetControlled(true, UNIT_STATE_ROOT);
        me->SetUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
    }

    bool _collapsed = false;
    bool _frozen = false;
};

namespace ScholoPolkelt
{
    // -----------------------------------------------------------------------------------------------------------------
    // SpecimenLab: one fight's specimens, rings and pools (PK1-PK6), owned by the boss, the examiner or a detention
    // lesson
    // -----------------------------------------------------------------------------------------------------------------
    struct LabConfig
    {
        bool heroic = false;
        bool hardened = false;          // PK6 on rooted specimens
        bool catalyst = true;           // PK3: rings react with the owner (the boss and the examiner)
        bool park = true;               // the kill / chained rings carry Park() (the owner is the parked unit)
        bool pools = true;              // PK5 (only ripe bursts leave one)
        uint32 poolCap = 6;
        float burstPct = 30.f;          // a kill / chained ring's hit
        uint32 burstTag = TAG_KILL_BURST;
        ObjectGuid fixate;              // the lesson's student: specimens walk at them and burst on reaching them
        ChainTuning chain;

        static LabConfig Fight(FightProfile const& p)
        {
            LabConfig c;
            c.heroic = p.heroic;
            c.hardened = p.hardened;
            c.poolCap = p.poolCap;
            c.burstPct = kBurstPct(p.heroic);
            return c;
        }

        static LabConfig Lesson(bool heroic, ObjectGuid student)
        {
            LabConfig c;
            c.heroic = heroic;
            c.catalyst = false;
            c.park = false;
            c.pools = false;
            c.burstPct = LessonFailurePct(heroic);
            c.burstTag = TAG_LESSON_BURST;
            c.fixate = student;
            c.chain = LessonChain();
            return c;
        }
    };

    class SpecimenLab
    {
    public:
        void Start(Creature* owner, LabConfig const& config)
        {
            Clear();
            _map = owner ? owner->GetMap() : nullptr;
            _owner = owner ? owner->GetGUID() : ObjectGuid::Empty;
            _cfg = config;
            _chain.Reset(config.chain);
            _clockMs = 0;
            _bursts = 0;
            _reactions = 0;
        }

        // Raises one specimen at `at` (its floor height checked by the caller). Nullptr when the summon fails.
        Creature* Raise(Position const& at, bool rooted)
        {
            Creature* owner = Owner();
            if (!owner)
                return nullptr;
            Creature* c = owner->SummonCreature(rooted ? NPC_SC_ROOTED_SPECIMEN : NPC_SC_UNSTABLE_SPECIMEN,
                at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), at.GetOrientation(),
                TEMPSUMMON_MANUAL_DESPAWN);
            if (!c)
            {
                DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "raise-failed", "summon refused");
                return nullptr;
            }
            c->CastSpell(c, SPELL_PK_RAISE, true);
            if (rooted)
            {
                c->AddAura(SPELL_PK_ROOTED, c);
                if (_cfg.hardened)
                    c->AddAura(SPELL_PK_HARDENED, c);
            }
            if (_cfg.chain.ripens)
                c->AddAura(SPELL_PK_RIPENING, c);

            Rec rec;
            rec.guid = c->GetGUID();
            rec.id = _chain.Add(DungeonKit::PlaneOf(c), rooted, _clockMs);
            rec.baseScale = c->GetObjectScale();
            _recs.push_back(rec);

            if (Player* student = _cfg.fixate.IsEmpty() ? nullptr : ObjectAccessor::GetPlayer(c->GetMap(), _cfg.fixate))
            {
                c->AddThreat(student, 100000.f);
                c->AI()->AttackStart(student);
            }
            else
                c->SetInCombatWithZone();
            return c;
        }

        void Update(uint32 diff)
        {
            if (!_map)
                return;
            _clockMs += diff;
            Creature* owner = Owner();
            if (!owner)
                return;

            Player* student = _cfg.fixate.IsEmpty() ? nullptr : ObjectAccessor::GetPlayer(_map, _cfg.fixate);
            for (Rec& rec : _recs)
            {
                SpecimenChain::Specimen const* s = _chain.Find(rec.id);
                if (!s || s->phase != SpecimenPhase::Standing)
                    continue;
                Creature* c = _map->GetCreature(rec.guid);
                if (!c || !c->IsInWorld())
                {
                    _chain.Remove(rec.id);
                    continue;
                }
                _chain.SetPos(rec.id, DungeonKit::PlaneOf(c));
                bool const collapsed = !c->IsAlive() || (c->AI() && c->AI()->GetData(DATA_SPECIMEN_COLLAPSED));
                bool const reached = student && student->IsAlive()
                    && (c->IsWithinMeleeRange(student) || c->GetExactDist2d(student) <= kLessonReachYd);
                if (collapsed || reached)
                {
                    if (std::optional<FuseStart> f = _chain.Kill(rec.id, _clockMs))
                        StartFuse(owner, *f, reached && !collapsed ? "reached" : "collapsed");
                    continue;
                }
                if (_cfg.chain.ripens)
                {
                    // PK4: the swell over its 30 s, one step a second.
                    uint32 const second = static_cast<uint32>((_clockMs - s->risenMs) / 1000);
                    if (second != rec.scaleSecond)
                    {
                        rec.scaleSecond = second;
                        c->SetObjectScale(rec.baseScale * SwellScale(_clockMs - s->risenMs, _cfg.chain.ripeAfterMs));
                    }
                }
            }

            for (FuseStart const& f : _chain.TakeRipening(_clockMs))
                StartFuse(owner, f, "ripe");

            std::optional<Vec2> boss;
            if (_cfg.catalyst && owner->IsAlive())
                boss = DungeonKit::PlaneOf(owner);
            uint32 const generation = _generation;
            for (Burst const& b : _chain.TakeBursts(_clockMs, boss, owner->GetObjectSize()))
            {
                DoBurst(owner, b);
                if (generation != _generation)
                    return;     // the reaction killed him: his death cleared the lab
                for (FuseStart const& lit : b.lit)
                    StartFuse(owner, lit, "lit");
            }

            _chain.Compact();
            _recs.erase(std::remove_if(_recs.begin(), _recs.end(), [this](Rec const& r)
            {
                return !_chain.Find(r.id);
            }), _recs.end());
            _rings.erase(std::remove_if(_rings.begin(), _rings.end(), [this](Ring const& r)
            {
                return r.resolveMs + 1000 < _clockMs;
            }), _rings.end());
            _pools.Expire(_clockMs);
        }

        // Everything gone: specimens despawned, rings and pools cancelled, the pool looks removed.
        void Clear()
        {
            Creature* owner = Owner();
            if (_map)
                for (Rec const& rec : _recs)
                    if (Creature* c = _map->GetCreature(rec.guid))
                        c->DespawnOrUnsummon();
            if (owner)
            {
                for (Ring const& ring : _rings)
                    Mechanic::Cancel(owner, ring.handle);
                for (PoolQueue::Pool const& pool : _pools.All())
                    Mechanic::Cancel(owner, MechanicHandle{ pool.handle });
                owner->RemoveDynObject(SPELL_PK_ACID_POOL_LOOK);
            }
            _recs.clear();
            _rings.clear();
            _pools.Clear();
            _chain.Reset(_cfg.chain);
            ++_generation;
        }

        // PK3 alone (`.dbtest scholo polkelt catalyst`).
        void React(Creature* owner)
        {
            if (!owner || !owner->IsAlive())
                return;
            uint32 const before = DungeonKit::Stacks(owner, SPELL_PK_CORRODED);
            int32 const bp = CatalystBasePoints(owner->GetMaxHealth(), before);
            owner->CastCustomSpell(SPELL_PK_CATALYST_REACTION, SPELLVALUE_BASE_POINT0, bp, owner, true);
            uint32 const after = DungeonKit::AddStacks(owner, SPELL_PK_CORRODED, 1, owner, kCorrodedMaxStacks);
            ++_reactions;
            DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "catalyst-reaction",
                Acore::StringFormat("hit={} corroded={}->{} health={:.1f}%", bp, before, after, owner->GetHealthPct()));
        }

        // `.dbtest`: the nearest standing specimen to `ref` collapses (as if a lethal hit dropped it).
        bool CollapseNearest(WorldObject const* ref)
        {
            Creature* best = nullptr;
            for (Rec const& rec : _recs)
            {
                SpecimenChain::Specimen const* s = _chain.Find(rec.id);
                Creature* c = _map ? _map->GetCreature(rec.guid) : nullptr;
                if (s && c && s->phase == SpecimenPhase::Standing
                    && (!best || ref->GetExactDist2d(c) < ref->GetExactDist2d(best)))
                    best = c;
            }
            if (!best || !best->AI())
                return false;
            best->AI()->SetData(DATA_SPECIMEN_COLLAPSED, 1);
            return true;
        }

        // `.dbtest`: every standing specimen starts its ripe fuse now. Returns how many.
        uint32 RipenAll()
        {
            Creature* owner = Owner();
            if (!owner)
                return 0;
            uint32 n = 0;
            for (FuseStart const& f : _chain.RipenNow(_clockMs))
            {
                StartFuse(owner, f, "test");
                ++n;
            }
            return n;
        }

        std::size_t Live() const { return _chain.Live(); }
        std::size_t Standing() const { return _chain.Count(SpecimenPhase::Standing); }
        std::size_t Burning() const
        {
            return _chain.Count(SpecimenPhase::Fusing) + _chain.Count(SpecimenPhase::Ripening);
        }
        std::size_t Pools() const { return _pools.Size(); }
        uint32 Bursts() const { return _bursts; }
        uint32 Reactions() const { return _reactions; }
        uint64 ClockMs() const { return _clockMs; }
        LabConfig const& Config() const { return _cfg; }

        // The rooted specimens still standing and the live pools (a new batch keeps its distance from both).
        std::vector<Vec2> RootedSpots() const
        {
            std::vector<Vec2> out;
            for (SpecimenChain::Specimen const& s : _chain.All())
                if (s.rooted && s.phase != SpecimenPhase::Gone)
                    out.push_back(s.pos);
            return out;
        }

        std::vector<Vec2> PoolSpots() const
        {
            std::vector<Vec2> out;
            for (PoolQueue::Pool const& p : _pools.All())
                out.push_back(p.pos);
            return out;
        }

        std::vector<Vec2> SpecimenSpots() const
        {
            std::vector<Vec2> out;
            for (SpecimenChain::Specimen const& s : _chain.All())
                if (s.phase != SpecimenPhase::Gone)
                    out.push_back(s.pos);
            return out;
        }

    private:
        struct Rec
        {
            ObjectGuid guid;
            uint32 id = 0;
            float baseScale = 1.f;
            uint32 scaleSecond = 0;
        };

        struct Ring
        {
            MechanicHandle handle;
            uint64 resolveMs = 0;
        };

        Creature* Owner() const
        {
            return _map ? _map->GetCreature(_owner) : nullptr;
        }

        Creature* SpecimenOf(uint32 id) const
        {
            for (Rec const& rec : _recs)
                if (rec.id == id)
                    return _map ? _map->GetCreature(rec.guid) : nullptr;
            return nullptr;
        }

        void StartFuse(Creature* owner, FuseStart const& f, char const* why)
        {
            Creature* c = SpecimenOf(f.id);
            float const z = c ? c->GetPositionZ() : owner->GetPositionZ();
            Position const at(f.pos.x, f.pos.y, z, 0.f);
            if (c && c->IsAlive())
            {
                if (c->AI())
                    c->AI()->SetData(DATA_SPECIMEN_FROZEN, 1);
                uint32 const cast = f.kind == BurstKind::Kill ? SPELL_PK_FUSE
                    : f.kind == BurstKind::Chained ? SPELL_PK_CHAINED_FUSE : SPELL_PK_RIPE;
                c->CastSpell(c, cast, false);
            }

            MechanicRef ref = Mechanic::Circle(owner, at, f.radius, Ms(f.warnMs));
            if (f.kind == BurstKind::Ripe)
                ref.Damage(kRipePct(_cfg.heroic)).Spell(SPELL_PK_RIPE_BURST).Tag(TAG_RIPE_BURST);
            else
            {
                uint32 const tag = _cfg.burstTag != TAG_KILL_BURST ? _cfg.burstTag
                    : f.kind == BurstKind::Kill ? TAG_KILL_BURST : TAG_CHAINED_BURST;
                ref.Damage(_cfg.burstPct).Weakened().Spell(SPELL_PK_SPECIMEN_BURST).Tag(tag);
                if (_cfg.park)
                    ref.Park();
            }
            _rings.push_back({ ref.Handle(), _clockMs + f.warnMs });
            DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "fuse",
                Acore::StringFormat("kind={} why={} at=({:.1f}, {:.1f}) warn={}ms radius={:.0f}", KindName(f.kind), why,
                    f.pos.x, f.pos.y, f.warnMs, f.radius));
        }

        void DoBurst(Creature* owner, Burst const& b)
        {
            ++_bursts;
            Creature* c = SpecimenOf(b.id);
            float const z = c ? c->GetPositionZ() : owner->GetPositionZ();
            if (c)
            {
                c->CastSpell(c, SPELL_PK_BURST_LOOK, true);
                c->DespawnOrUnsummon(500ms);
            }
            DungeonKit::LogMechanic(kLogDungeon, kLogBoss, b.kind == BurstKind::Ripe ? "ripe-burst" : "burst",
                Acore::StringFormat("kind={} at=({:.1f}, {:.1f}) lit={} catalyst={}", KindName(b.kind), b.pos.x,
                    b.pos.y, b.lit.size(), b.catalyst && _cfg.catalyst ? 1 : 0));
            if (b.catalyst && _cfg.catalyst)
                React(owner);
            if (b.leavesPool && _cfg.pools)
                Pool(owner, b.pos, z);
        }

        // PK5: a pool where a ripe specimen burst; at the cap the oldest dries up (its zone and its look).
        void Pool(Creature* owner, Vec2 pos, float z)
        {
            Position const at(pos.x, pos.y, z, 0.f);
            DungeonKit::LingerSpec spec;
            spec.duration = Ms(kPoolMs);
            spec.tick = Ms(kPoolTickMs);
            spec.pct = kPoolPct(_cfg.heroic);
            spec.school = SPELL_SCHOOL_NATURE;
            spec.spellId = SPELL_PK_ACID_POOL;
            spec.tag = TAG_ACID_POOL;
            MechanicHandle const handle = DungeonKit::Linger(owner, BossMechanics::Shapes::Circle(at, kPoolRadius),
                spec);
            if (!handle)
                return;
            owner->CastSpell(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), SPELL_PK_ACID_POOL_LOOK, true);
            // A pool about to dry by itself is not the one a new pool pushes out (its look may already be gone).
            _pools.Expire(_clockMs + 250);
            std::vector<PoolQueue::Pool> const dried = _pools.Push(handle.id, pos, _clockMs, _cfg.poolCap);
            for (PoolQueue::Pool const& old : dried)
            {
                Mechanic::Cancel(owner, MechanicHandle{ old.handle });
                if (DynamicObject* look = owner->GetDynObject(SPELL_PK_ACID_POOL_LOOK))
                    look->Remove();         // the oldest look: the lab casts them in the queue's order
            }
            DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "acid-pool",
                Acore::StringFormat("at=({:.1f}, {:.1f}) pools={} cap={} dried={}", pos.x, pos.y, _pools.Size(),
                    _cfg.poolCap, dried.size()));
        }

        Map* _map = nullptr;
        ObjectGuid _owner;
        LabConfig _cfg;
        SpecimenChain _chain;
        PoolQueue _pools;
        std::vector<Rec> _recs;
        std::vector<Ring> _rings;
        uint64 _clockMs = 0;
        uint32 _bursts = 0;
        uint32 _reactions = 0;
        uint32 _generation = 0;         // +1 per Clear: an update that cleared itself (his death) stops
    };
}

namespace
{
    // `count` floor points by `rules` (PolkeltLogic.h PickSpots) with the engine's floor check, as positions.
    std::vector<Position> FloorPoints(WorldObject const* ref, SpotRules const& rules, uint32 count,
        std::vector<Vec2> const& players, std::vector<Vec2> const& apartFrom, std::vector<Vec2> const& avoid,
        std::vector<Vec2> const& fixed = {})
    {
        std::vector<Vec2> const picks = PickSpots(rules, count, players, apartFrom, avoid, Rand01,
            [ref](Vec2 p) { return FloorZ(ref, p).has_value(); }, fixed);
        std::vector<Position> out;
        Vec2 const center = rules.arenaCenter;
        for (Vec2 const& p : picks)
            out.emplace_back(p.x, p.y, FloorZ(ref, p).value_or(kHallFloorZ), DungeonKit::BearingTo(p, center));
        return out;
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// Lorekeeper Polkelt 10901 (and, in examiner mode, the Graduate Examiner 300550 that S13 binds to this ScriptName)
// ---------------------------------------------------------------------------------------------------------------------
struct boss_lorekeeper_polkelt_rework : public BossAI
{
    explicit boss_lorekeeper_polkelt_rework(Creature* creature)
        : BossAI(creature, BOSS_POLKELT), _arena(PolkeltArena(), LeashOptions(kLogBoss)) { }

    bool Examiner() const { return me->GetEntry() == NPC_SC_EXAMINER_POLKELT; }

    void Reset() override
    {
        if (Examiner())
        {
            summons.DespawnAll();
            ApplyExaminerHealth();
        }
        else
            _Reset();
        Cleanup();
        _grades.Reset();
    }

    void JustEngagedWith(Unit* who) override
    {
        if (_testLesson)
        {
            _testLesson->Abort();
            _testLesson.reset();
        }
        _profile = ProfileFor(IsHeroicMap(me), Examiner());
        if (_profile.bossState)
        {
            BossAI::JustEngagedWith(who);
            if (!me->IsEngaged())
                return;     // BossAI evaded
        }
        else
        {
            me->setActive(true);
            DoZoneInCombat();
        }

        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        BossMechanics::EncounterOptions options;
        if (_profile.bossState)
            options.bossStateId = BOSS_POLKELT;
        Mechanic::BeginEncounter(me, options);
        Describe();
        if (_profile.grades)
            _grades.Begin(me, Instructor::Polkelt);
        _arena.Engage(me);
        _lab.Start(me, LabConfig::Fight(_profile));
        _nextBatchMs = kFirstBatchMs;
        _nextNoxiousMs = _profile.noxious ? kNoxiousEveryMs : 0;
        _nextVolatileMs = InRange(kVolatileFirstMinMs, kVolatileFirstMaxMs, Rand01());
        if (_profile.talks)
            Talk(YELL_POLKELT_AGGRO);
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "engage",
            Acore::StringFormat("heroic={} examiner={} at=({:.1f}, {:.1f}, {:.1f}) health={}", _profile.heroic ? 1 : 0,
                Examiner() ? 1 : 0, me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), me->GetMaxHealth()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        _grades.Reset();
        if (Examiner())
            CreatureAI::EnterEvadeMode(why);
        else
            BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        if (_profile.grades)
            _grades.AwardAtDeath(me);
        if (_profile.talks)
            Talk(YELL_POLKELT_DEATH);
        Cleanup();
        if (Examiner())
            summons.DespawnAll();
        else
            BossAI::JustDied(killer);   // DONE (door data, Gandling's reveal), the summons despawn, the encounter ends
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "death",
            Acore::StringFormat("examiner={} bursts={} reactions={} killer={}", Examiner() ? 1 : 0, _lab.Bursts(),
                _lab.Reactions(), killer ? killer->GetName() : "none"));
    }

    // The specimens' combat is the lab's (walkers zoned in, rooted ones melee only in reach): never BossAI's zoning.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    uint32 GetData(uint32 id) const override
    {
        return id == DATA_EXAMINER_MODE && Examiner() ? 1 : 0;
    }

    void UpdateAI(uint32 diff) override
    {
        UpdateTestLesson(diff);
        if (!UpdateVictim())
            return;

        // The AI's own clock: nothing below waits for a cast bar.
        _clockMs += diff;
        _lab.Update(diff);
        if (!me->IsAlive() || !me->IsEngaged())
            return;     // a Catalyst Reaction killed him
        if (_clockMs >= _nextBatchMs)
        {
            _nextBatchMs += kBatchEveryMs;
            RaiseBatch();
        }
        if (_nextNoxiousMs && _clockMs >= _nextNoxiousMs)
        {
            _nextNoxiousMs += kNoxiousEveryMs;
            ApplyNoxious();
        }

        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (_clockMs >= _nextVolatileMs)
        {
            Unit* victim = me->GetVictim();
            if (victim && me->IsWithinMeleeRange(victim))
            {
                me->CastSpell(victim, SPELL_VOLATILE_INFECTION, false);
                _nextVolatileMs = _clockMs + kVolatileEveryMs;
                DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "volatile-infection", victim->GetName());
                return;
            }
            _nextVolatileMs = _clockMs + 1000;
        }
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // PK1 Raise Specimens
    // ----------------------------------------------------------------------------------------------------------------

    void RaiseBatch()
    {
        std::vector<Vec2> const players = PlayerSpots(me->GetMap());
        std::vector<Vec2> const pools = _lab.PoolSpots();
        std::vector<Position> const rooted = FloorPoints(me, RaiseRules(true), _profile.rooted, players,
            _lab.RootedSpots(), pools, RootedFallbackSpots());
        std::vector<Vec2> taken = _lab.SpecimenSpots();
        for (Position const& p : rooted)
            taken.push_back({ p.GetPositionX(), p.GetPositionY() });
        std::vector<Position> const walkers = FloorPoints(me, RaiseRules(false), _profile.walkers, players, taken,
            pools);
        uint32 raised = 0;
        for (Position const& p : rooted)
            raised += _lab.Raise(p, true) ? 1 : 0;
        for (Position const& p : walkers)
            raised += _lab.Raise(p, false) ? 1 : 0;
        if (_profile.talks)
            Talk(EMOTE_POLKELT_RAISE);
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "raise",
            Acore::StringFormat("heroic={} rooted={}/{} walkers={}/{} raised={} live={} pools={}",
                _profile.heroic ? 1 : 0, rooted.size(), _profile.rooted, walkers.size(), _profile.walkers, raised,
                _lab.Live(), _lab.Pools()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // PK7 Noxious Catalyst (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    void ApplyNoxious()
    {
        uint32 const want = NoxiousStacksAt(_clockMs);
        uint32 n = 0;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* p = ref.GetSource();
            if (!CountsAsPlayer(p) || !p->IsInCombatWith(me))
                continue;
            int32 const delta = static_cast<int32>(want) - static_cast<int32>(DungeonKit::Stacks(p,
                SPELL_PK_NOXIOUS_CATALYST, me->GetGUID()));
            DungeonKit::AddStacks(p, SPELL_PK_NOXIOUS_CATALYST, delta, me);
            ++n;
        }
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "noxious-catalyst",
            Acore::StringFormat("stacks={} players={} perSecond={:.1f}%", want, n, want * kNoxiousPctPerStack));
    }

    void RemoveNoxious()
    {
        for (auto const& ref : me->GetMap()->GetPlayers())
            if (Player* p = ref.GetSource())
                p->RemoveAurasDueToSpell(SPELL_PK_NOXIOUS_CATALYST, me->GetGUID());
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (SC): target priority, the walking (normal: and rooted) specimens above him once within 6 yd of him or
    // ripe in under 3 s, never otherwise; heroic rooted (Hardened) on the ignore list. Dispel: Volatile Infection.
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        using BossMechanics::Condition;
        using BossMechanics::Who;
        ObjectGuid const owner = me->GetGUID();
        auto ready = [owner](Unit const* unit)
        {
            if (!unit)
                return false;
            Creature const* boss = ObjectAccessor::GetCreature(*unit, owner);
            if (!boss || !boss->IsAlive())
                return false;
            uint64 msToRipe = UINT64_MAX;
            if (Aura const* clock = unit->GetAura(SPELL_PK_RIPENING))
                msToRipe = static_cast<uint64>(std::max(0, clock->GetDuration()));
            return IsKillTarget(unit->GetExactDist2d(boss), msToRipe);
        };
        BossMechanics::Descriptor d;
        d.dispels.emplace_back(SPELL_VOLATILE_INFECTION, 1);
        d.targets.emplace_back(NPC_SC_UNSTABLE_SPECIMEN, 2, Who::Dps, Condition::Custom(ready));
        if (_profile.hardened)
            d.ignores.emplace_back(NPC_SC_ROOTED_SPECIMEN);
        else
            d.targets.emplace_back(NPC_SC_ROOTED_SPECIMEN, 2, Who::Dps, Condition::Custom(ready));
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest scholo polkelt` entry points
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Raise,
        Collapse,
        Ripen,
        Catalyst,
        Noxious,
    };

    std::string TestFire(TestMechanic mechanic)
    {
        if (!me->IsEngaged())
            return "Polkelt must be in combat (the specimens, rings and pools belong to the fight).";
        switch (mechanic)
        {
            case TestMechanic::Raise:
                RaiseBatch();
                break;
            case TestMechanic::Collapse:
                if (!_lab.CollapseNearest(me))
                    return "No standing specimen.";
                break;
            case TestMechanic::Ripen:
                if (!_lab.RipenAll())
                    return "No standing specimen.";
                break;
            case TestMechanic::Catalyst:
                _lab.React(me);
                break;
            case TestMechanic::Noxious:
                ApplyNoxious();
                break;
        }
        return {};
    }

    std::string TestState() const
    {
        return Acore::StringFormat("examiner={} heroic={} clock={}s nextBatch={}s live={} (standing {}, burning {}) "
            "pools={}/{} bursts={} reactions={} corroded={} noxious={} lesson={}", Examiner() ? 1 : 0,
            _profile.heroic ? 1 : 0, _clockMs / 1000, _nextBatchMs / 1000, _lab.Live(), _lab.Standing(),
            _lab.Burning(), _lab.Pools(), _profile.poolCap, _lab.Bursts(), _lab.Reactions(),
            DungeonKit::Stacks(me, SPELL_PK_CORRODED), NoxiousStacksAt(_clockMs),
            _testLesson ? (_testLesson->Done() ? "done" : "running") : "none");
    }

    // A detention lesson run by Polkelt himself (out of combat): his AI ticks it, he owns its registry encounter.
    std::string TestLesson(Player* student, bool heroic)
    {
        if (me->IsEngaged() || !me->IsAlive())
            return "Polkelt must be alive and out of combat (he hosts the test lesson).";
        if (_testLesson)
        {
            _testLesson->Abort();
            _testLesson.reset();
        }
        _testLesson = CreateSoloLesson(Classroom::HallOfSecrets);
        if (!_testLesson)
            return "No Hall of Secrets lesson is registered.";
        _testLesson->Start(me, student, heroic);
        return {};
    }

private:
    void UpdateTestLesson(uint32 diff)
    {
        if (!_testLesson)
            return;
        _testLesson->Update(diff);
        if (_testLesson->Done())
            _testLesson.reset();
    }

    void ApplyExaminerHealth()
    {
        FightProfile const p = ProfileFor(true, true);
        if (!p.maxHealth || me->GetMaxHealth() == p.maxHealth)
            return;
        me->SetCreateHealth(p.maxHealth);
        me->SetStatFlatModifier(UNIT_MOD_HEALTH, BASE_VALUE, static_cast<float>(p.maxHealth));
        me->SetMaxHealth(p.maxHealth);
        me->SetFullHealth();
    }

    // The pull's state: nothing pending, no specimens or pools, no stacks (Reset, evade, death, a new pull).
    void Cleanup()
    {
        _lab.Clear();
        RemoveNoxious();
        me->RemoveAurasDueToSpell(SPELL_PK_CORRODED);
        _clockMs = 0;
        _nextBatchMs = kFirstBatchMs;
        _nextNoxiousMs = 0;
        _nextVolatileMs = 0;
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    GradeWatch _grades;
    SpecimenLab _lab;
    FightProfile _profile;
    std::unique_ptr<SoloLesson> _testLesson;
    uint64 _clockMs = 0;                        // ms since the pull: every timer of the fight
    uint64 _nextBatchMs = kFirstBatchMs;
    uint64 _nextNoxiousMs = 0;
    uint64 _nextVolatileMs = 0;
};

// ---------------------------------------------------------------------------------------------------------------------
// Detention: the Hall of Secrets (SC 2967; handoff section 3.7). 3 / 4 Unstable Specimens rise one every 2 s, 10-14 yd
// from the student, walk at them and burst on reaching them or on death (a 6 yd ring after a 2 s fuse; a burst lights
// any specimen in its ring, 1 s). Each ring that catches the student is a failure (15% / 25% + Weakened): pass = never
// in a burst. It ends early once every specimen has burst.
// ---------------------------------------------------------------------------------------------------------------------
class HallOfSecretsLesson final : public TimedSoloLesson
{
public:
    HallOfSecretsLesson() : TimedSoloLesson(Classroom::HallOfSecrets) { }

protected:
    void OnStart(Creature* owner, Player* student, bool heroic) override
    {
        _planned = kLessonSpecimens(heroic);
        _risen = 0;
        _elapsedMs = 0;
        _lab.Start(owner, LabConfig::Lesson(heroic, student->GetGUID()));
        SpawnDue(owner, student);
    }

    void OnUpdate(uint32 diff, Creature* owner, Player* student) override
    {
        _elapsedMs += diff;
        SpawnDue(owner, student);
        _lab.Update(diff);
        if (LessonCleared(_risen, _planned, _lab.Live()))
            FinishEarly();
    }

    void OnEnd(LessonEnd why, Creature* /*owner*/) override
    {
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "lesson-end",
            Acore::StringFormat("why={} risen={}/{} bursts={}", int(why), _risen, _planned, _lab.Bursts()));
        _lab.Clear();
    }

private:
    void SpawnDue(Creature* owner, Player* student)
    {
        if (!owner || !student)
            return;
        while (_risen < _planned && _elapsedMs >= LessonSpawnAtMs(_risen))
        {
            Vec2 const at = DungeonKit::PlaneOf(student);
            std::vector<Position> const spot = FloorPoints(student, LessonRules(at), 1, { at },
                _lab.SpecimenSpots(), {});
            ++_risen;
            if (spot.empty())
            {
                DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "lesson-raise-failed", "no floor point");
                continue;
            }
            _lab.Raise(spot.front(), false);
            DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "lesson-raise",
                Acore::StringFormat("{}/{} at=({:.1f}, {:.1f}) student={}", _risen, _planned,
                    spot.front().GetPositionX(), spot.front().GetPositionY(), student->GetName()));
        }
    }

    SpecimenLab _lab;
    uint32 _planned = 0;
    uint32 _risen = 0;
    uint32 _elapsedMs = 0;
};

// PK7 206263 Noxious Catalyst: each stack ticks 0.3% of the reference row per second (the aura multiplies the per-stack
// amount by its stacks); RefFlatOn: the tank row on the tank.
class spell_sc_polkelt_noxious_catalyst : public AuraScript
{
    PrepareAuraScript(spell_sc_polkelt_noxious_catalyst);

    void CalcAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        amount = static_cast<int32>(DungeonKit::RefFlatOn(GetCaster(), GetUnitOwner(), kNoxiousPctPerStack));
        canBeRecalculated = true;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_sc_polkelt_noxious_catalyst::CalcAmount, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE);
    }
};

namespace
{
    boss_lorekeeper_polkelt_rework* FindPolkeltAI(ChatHandler* handler)
    {
        Creature* boss = ScholoTest::FindBoss(handler, NPC_POLKELT);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_lorekeeper_polkelt_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}",
                "Lorekeeper Polkelt is not running boss_lorekeeper_polkelt_rework (check the ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_lorekeeper_polkelt_rework::TestMechanic mechanic, char const* what)
    {
        boss_lorekeeper_polkelt_rework* ai = FindPolkeltAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestFire(mechanic);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Lorekeeper Polkelt: {} fired.", what);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return ScholoTest::ShowBossInfo(handler, NPC_POLKELT, BOSS_POLKELT);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_lorekeeper_polkelt_rework* ai = FindPolkeltAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Lorekeeper Polkelt: {}", ai->TestState());
        return true;
    }

    bool HandleRaise(ChatHandler* handler)
    {
        return Fire(handler, boss_lorekeeper_polkelt_rework::TestMechanic::Raise, "a batch (PK1 Raise Specimens)");
    }

    bool HandleKill(ChatHandler* handler)
    {
        return Fire(handler, boss_lorekeeper_polkelt_rework::TestMechanic::Collapse,
            "the nearest specimen's kill fuse (PK2; the chain follows)");
    }

    bool HandleRipe(ChatHandler* handler)
    {
        return Fire(handler, boss_lorekeeper_polkelt_rework::TestMechanic::Ripen,
            "every standing specimen ripens (PK4, then PK5 pools)");
    }

    bool HandleCatalyst(ChatHandler* handler)
    {
        return Fire(handler, boss_lorekeeper_polkelt_rework::TestMechanic::Catalyst,
            "a Catalyst Reaction (PK3: 1.5% and a Corroded stack)");
    }

    bool HandleNoxious(ChatHandler* handler)
    {
        return Fire(handler, boss_lorekeeper_polkelt_rework::TestMechanic::Noxious,
            "Noxious Catalyst stacks set to the fight's count (PK7)");
    }

    // `.dbtest scholo polkelt lesson [1]`: the Hall of Secrets detention lesson on the selected player (else you),
    // hosted by Polkelt out of combat; 1 = the heroic lesson. Another living player must be in the instance, or the
    // lesson stops at once (the last-alive safety).
    bool HandleLesson(ChatHandler* handler, Optional<uint32> heroic)
    {
        boss_lorekeeper_polkelt_rework* ai = FindPolkeltAI(handler);
        if (!ai)
            return false;
        Player* student = handler->getSelectedPlayerOrSelf();
        if (!student)
            return false;
        bool const isHeroic = heroic && *heroic != 0;
        std::string const error = ai->TestLesson(student, isHeroic);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Hall of Secrets lesson started on {} ({}).", student->GetName(),
            isHeroic ? "heroic" : "normal");
        return true;
    }

    ChatCommandTable const& PolkeltTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",    HandleState,    SEC_GAMEMASTER, Console::No },
            { "raise",    HandleRaise,    SEC_GAMEMASTER, Console::No },
            { "kill",     HandleKill,     SEC_GAMEMASTER, Console::No },
            { "ripe",     HandleRipe,     SEC_GAMEMASTER, Console::No },
            { "catalyst", HandleCatalyst, SEC_GAMEMASTER, Console::No },
            { "noxious",  HandleNoxious,  SEC_GAMEMASTER, Console::No },
            { "lesson",   HandleLesson,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_lorekeeper_polkelt_rework()
{
    RegisterDungeonReworkCreatureAI(boss_lorekeeper_polkelt_rework, ScholomanceRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sc_polkelt_specimen, ScholomanceRework::kInstanceScriptName);
    RegisterSpellScript(spell_sc_polkelt_noxious_catalyst);
    RegisterSoloLesson(Classroom::HallOfSecrets, [] { return std::unique_ptr<SoloLesson>(new HallOfSecretsLesson()); });
    ScholoTest::RegisterBoss("polkelt", PolkeltTestCommands());
}
