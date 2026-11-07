/*
 * mod-dungeon-bosses, the shared dungeon kit (DungeonKit.h). RefFlat, IsHeroicMap, Linger, ImpactThenLinger, CastBar,
 * ShortenAura and ToPosition are the Deadmines Pilot's DeadminesKit code, moved here unchanged.
 */

#include "DungeonKit.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "MotionMaster.h"
#include "MovementTypedefs.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptMgr.h"
#include "SpellAuras.h"
#include "TemporarySummon.h"
#include "Unit.h"
#include <algorithm>

static_assert(DungeonKit::State::NotStarted == NOT_STARTED && DungeonKit::State::InProgress == IN_PROGRESS
    && DungeonKit::State::Fail == FAIL && DungeonKit::State::Done == DONE
    && DungeonKit::State::Special == SPECIAL && DungeonKit::State::ToBeDecided == TO_BE_DECIDED,
    "DungeonKitState.h mirrors InstanceScript.h's EncounterState");

namespace DungeonKit
{
    uint32 RefFlat(Unit const* owner, float pct, bool tank)
    {
        // mod-boss-mechanics' own helper: the registry's content key, reference row and rounding.
        return Mechanic::RefFlat(owner, pct, tank);
    }

    bool IsHeroicMap(WorldObject const* me)
    {
        Map const* map = me ? me->FindMap() : nullptr;
        return map && map->IsHeroic();
    }

    BossMechanics::MechanicRef Linger(Unit* owner, BossMechanics::ZoneSpec const& shape, LingerSpec const& linger)
    {
        if (!owner)
            return {};
        BossMechanics::MechanicRef ref = Mechanic::Zone(owner, shape, linger.tick);
        ref.Persistent(linger.duration, linger.tick).Damage(linger.pct).School(linger.school).NoFillTimer();
        if (linger.spellId)
            ref.Spell(linger.spellId);
        if (linger.slow && linger.slowSpell)
            ref.Rider(linger.slowSpell);
        if (linger.color)
            ref.Color(*linger.color);
        if (linger.tag)
            ref.Tag(linger.tag);
        return ref;
    }

    BossMechanics::MechanicRef ImpactThenLinger(Unit* owner, ImpactSpec const& impact, LingerSpec const& linger)
    {
        if (!owner)
            return {};
        BossMechanics::MechanicRef ref = Mechanic::Zone(owner, impact.shape, impact.warn);
        ref.Damage(impact.pct).School(impact.school);
        if (impact.tankPct >= 0.f)
            ref.TankDamage(impact.tankPct);
        if (impact.spellId)
            ref.Spell(impact.spellId);
        if (impact.weakened)
            ref.Weakened();
        if (impact.tag)
            ref.Tag(impact.tag);

        // Capture the map and guid only (a lambda kept by the registry must not hold a Unit*; STAGE-M5-R-REPORT m-4).
        // The registry calls OnResolve only while the owner is present, and Add from a callback is safe.
        Map* map = owner->GetMap();
        ObjectGuid const ownerGuid = owner->GetGUID();
        BossMechanics::ZoneSpec const lingerShape = linger.shape ? *linger.shape : impact.shape;
        LingerSpec const lingerCopy = linger;
        ref.OnResolve([map, ownerGuid, lingerShape, lingerCopy](BossMechanics::ResolveResult const& result)
        {
            if (result.fizzled || !map)
                return;
            if (Creature* source = map->GetCreature(ownerGuid))
                Linger(source, lingerShape, lingerCopy);
        });
        return ref;
    }

    void CastBar(Creature* caster, uint32 spellId, Unit* target, std::optional<uint8> textGroup,
        WorldObject const* textTarget)
    {
        if (!caster)
            return;
        caster->CastSpell(target ? target : caster, spellId, false);
        if (textGroup && caster->IsAIEnabled && caster->AI())
            caster->AI()->Talk(*textGroup, textTarget);
    }

    bool ShortenAura(Unit* target, uint32 spellId, ObjectGuid caster, Milliseconds duration)
    {
        if (!target)
            return false;
        Aura* aura = target->GetAura(spellId, caster);
        if (!aura)
            return false;
        int32 const ms = static_cast<int32>(duration.count());
        aura->SetMaxDuration(ms);
        aura->SetDuration(ms);
        return true;
    }

    Position ToPosition(Vec2 p, float z, float orientation)
    {
        return Position(p.x, p.y, z, orientation);
    }

    Vec2 PlaneOf(WorldObject const* o)
    {
        return { o->GetPositionX(), o->GetPositionY() };
    }

    BossMechanics::RoomFrame ToRoomFrame(FrameRect const& frame, float z)
    {
        BossMechanics::RoomFrame out;
        out.origin = ToPosition(frame.origin, z, frame.angle);
        out.angle = frame.angle;
        out.sizeX = frame.sizeX;
        out.sizeY = frame.sizeY;
        return out;
    }

    void JumpTo(Unit* unit, Position const& dest, float speedXY, float minSpeedZ, uint32 lookSpell, Unit* lookCaster)
    {
        if (!unit || speedXY <= 0.f)
            return;
        // Mirrors Spell::EffectPullTowards (AzerothCore): a jump whose arc lands at the destination.
        float const dist = Distance(PlaneOf(unit), { dest.GetPositionX(), dest.GetPositionY() });
        float const speedZ = std::max(minSpeedZ, static_cast<float>(dist / speedXY * 0.5 * Movement::gravity));
        if (lookSpell && lookCaster)
            lookCaster->CastSpell(unit, lookSpell, true);
        unit->GetMotionMaster()->MoveJump(dest.GetPositionX(), dest.GetPositionY(), dest.GetPositionZ(), speedXY,
            speedZ);
        if (Player* player = unit->ToPlayer())
            sScriptMgr->AnticheatSetUnderACKmount(player);
    }

    void SetRunSpeedPct(Creature* creature, float pctOfPlayerRun)
    {
        if (creature)
            creature->SetSpeed(MOVE_RUN, SpeedFor(pctOfPlayerRun));
    }

    namespace
    {
        // The players on `me`'s threat list, as pick candidates (parallel to `players`).
        void PickCandidates(Creature* me, std::vector<Player*>& players, std::vector<PickCandidate>& candidates)
        {
            Unit const* victim = me->GetVictim();
            for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
            {
                Unit* unit = ref->GetVictim();
                Player* player = unit ? unit->ToPlayer() : nullptr;
                if (!player || !player->IsInWorld() || !player->IsAlive() || player->IsGameMaster()
                    || !player->IsInMap(me))
                    continue;
                PickCandidate c;
                c.id = player->GetGUID().GetRawValue();
                c.distance = me->GetExactDist2d(player);
                c.tank = player == victim;
                c.inLos = me->IsWithinLOSInMap(player);
                players.push_back(player);
                candidates.push_back(c);
            }
        }

        uint32 RandomBelow(uint32 n)
        {
            return n ? urand(0, n - 1) : 0;
        }
    }

    Player* PickPlayer(Creature* me, PickRule const& rule)
    {
        if (!me)
            return nullptr;
        std::vector<Player*> players;
        std::vector<PickCandidate> candidates;
        PickCandidates(me, players, candidates);
        std::optional<std::size_t> const pick = PickFrom(candidates, rule, RandomBelow);
        return pick ? players[*pick] : nullptr;
    }

    std::vector<Player*> PickPlayers(Creature* me, PickRule const& rule, uint32 count)
    {
        std::vector<Player*> out;
        if (!me)
            return out;
        std::vector<Player*> players;
        std::vector<PickCandidate> candidates;
        PickCandidates(me, players, candidates);
        for (std::size_t const i : PickDistinctFrom(candidates, rule, count, RandomBelow))
            out.push_back(players[i]);
        return out;
    }

    void ExcludeGuids(PickRule& rule, GuidSet const& guids)
    {
        for (ObjectGuid const& guid : guids)
            rule.exclude.push_back(guid.GetRawValue());
    }

    LineStrikeResult LineStrike(Unit* owner, Position const& from, Position const& target, LineStrikeSpec const& spec)
    {
        LineStrikeResult out;
        if (!owner)
            return out;
        LinePath const path = LineStrikePath({ from.GetPositionX(), from.GetPositionY() },
            { target.GetPositionX(), target.GetPositionY() }, spec.overrun, from.GetOrientation(), spec.clip,
            from.GetPositionZ(), spec.inset);
        out.end = ToPosition(path.end, target.GetPositionZ(), path.facing);
        out.length = path.length;
        out.clipped = path.clipped;
        if (path.length <= 0.f)
            return out;

        Position const start = ToPosition(path.from, from.GetPositionZ(), path.facing);
        BossMechanics::MechanicRef ref = Mechanic::Line(owner, start, path.facing, path.length, spec.width, spec.warn);
        ref.Damage(spec.pct).School(spec.school);
        if (spec.tankPct >= 0.f)
            ref.TankDamage(spec.tankPct);
        if (spec.spellId)
            ref.Spell(spec.spellId);
        if (spec.weakened)
            ref.Weakened();
        if (spec.rider)
            ref.Rider(spec.rider);
        if (spec.excludeSourceEnd > 0.f)
            ref.ExcludeSourceEnd(spec.excludeSourceEnd);
        if (spec.color)
            ref.Color(*spec.color);
        if (spec.tag)
            ref.Tag(spec.tag);
        if (spec.onHit)
            ref.OnHit(spec.onHit);
        out.handle = ref.Handle();
        return out;     // the ref commits here
    }

    LineStrikeResult LineStrike(Unit* owner, Unit const* from, Unit const* target, LineStrikeSpec const& spec)
    {
        if (!from || !target)
            return {};
        return LineStrike(owner, from->GetPosition(), target->GetPosition(), spec);
    }

    bool LethalGuard::Intercept(Unit* unit, uint32& damage, std::function<void()> const& onZero)
    {
        if (!_armed)
            return false;
        bool fired = _fired;
        bool const clamped = InterceptLethal(unit, damage, fired, onZero);
        _fired = fired;
        return clamped;
    }

    bool InterceptLethal(Unit* unit, uint32& damage, bool& fired, std::function<void()> const& onZero)
    {
        if (!unit)
            return false;
        uint32 const health = unit->GetHealth();
        if (damage < health)
            return false;
        damage = ClampLethal(health, damage);
        if (!fired)
        {
            fired = true;
            if (onZero)
                onZero();
        }
        return true;
    }

    std::vector<std::pair<ObjectGuid, uint32>> SplitShares(Unit const* owner, std::vector<Unit*> const& inside,
        float totalPct, float capPct)
    {
        std::vector<std::pair<ObjectGuid, uint32>> out;
        if (!owner || inside.empty())
            return out;
        uint32 const total = RefFlat(owner, totalPct);
        uint32 const cap = capPct > 0.f ? RefFlat(owner, capPct) : 0;
        std::vector<uint32> const shares = SplitDamage(total, static_cast<uint32>(inside.size()), cap);
        for (std::size_t i = 0; i < inside.size(); ++i)
            if (inside[i])
                out.emplace_back(inside[i]->GetGUID(), shares[i]);
        return out;
    }

    uint32 AddStacks(Unit* target, uint32 spellId, int32 delta, Unit* caster, uint32 max)
    {
        if (!target)
            return 0;
        Unit* source = caster ? caster : target;
        Aura* aura = target->GetAura(spellId, source->GetGUID());
        uint32 const current = aura ? aura->GetStackAmount() : 0;
        uint32 const want = ClampStacks(current, delta, max);
        if (!want)
        {
            if (aura)
                target->RemoveAura(aura);
            return 0;
        }
        if (!aura)
        {
            aura = source->AddAura(spellId, target);
            if (!aura)
                return 0;
        }
        if (aura->GetStackAmount() != want)
            aura->SetStackAmount(static_cast<uint8>(std::min<uint32>(want, 255)));
        aura->RefreshDuration();
        return aura->GetStackAmount();
    }

    uint32 Stacks(Unit const* target, uint32 spellId, ObjectGuid caster)
    {
        if (!target)
            return 0;
        Aura const* aura = target->GetAura(spellId, caster);
        return aura ? aura->GetStackAmount() : 0;
    }

    uint32 RollOnce(InstanceScript* instance, uint32 dataId, uint32 presentChancePct)
    {
        if (!instance)
            return Roll::Unrolled;
        uint32 roll = SanitizeLoadedRoll(instance->GetData(dataId));
        if (roll == Roll::Unrolled)
        {
            roll = ResolveRoll(urand(0, 99), presentChancePct);
            instance->SetData(dataId, roll);
        }
        return roll;
    }

    void SetHardModeLoot(Creature* boss, bool lit)
    {
        if (!boss)
            return;
        if (lit)
            boss->AddLootMode(LOOT_MODE_HARD_MODE_1);
        else
            boss->RemoveLootMode(LOOT_MODE_HARD_MODE_1);
    }

    Creature* SpawnBreakableDoor(WorldObject* owner, GameObject* door, uint32 standInEntry, uint32 health)
    {
        if (!owner || !door || !standInEntry)
            return nullptr;
        TempSummon* standIn = owner->SummonCreature(standInEntry, door->GetPosition(), TEMPSUMMON_MANUAL_DESPAWN);
        if (!standIn)
            return nullptr;
        if (health)
        {
            standIn->SetMaxHealth(health);
            standIn->SetHealth(health);
        }
        if (standIn->IsAIEnabled && standIn->AI())
            standIn->AI()->SetGUID(door->GetGUID(), BreakableDoorAI::kSetDoorGuid);
        return standIn;
    }

    BreakableDoorAI::BreakableDoorAI(Creature* creature) : ScriptedAI(creature)
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void BreakableDoorAI::Reset()
    {
        me->SetReactState(REACT_PASSIVE);
        me->SetControlled(true, UNIT_STATE_ROOT);
    }

    void BreakableDoorAI::SetGUID(ObjectGuid const& guid, int32 id)
    {
        if (id == kSetDoorGuid)
            _door = guid;
    }

    void BreakableDoorAI::JustDied(Unit* /*killer*/)
    {
        if (GameObject* door = _door ? me->GetMap()->GetGameObject(_door) : nullptr)
        {
            door->SetGoState(GO_STATE_ACTIVE);
            OnDoorOpened(door);
        }
        me->DespawnOrUnsummon(Milliseconds(1000));
    }

    void BreakableDoorAI::OnDoorOpened(GameObject* door)
    {
        LOG_INFO(kLogCategory, "dungeon-kit breakable door {} opened by stand-in {}", door->GetEntry(),
            me->GetEntry());
    }

    uint32 Pickups::Add(Creature* owner, Position const& at, PickupSpec spec)
    {
        if (!owner || !owner->IsInWorld() || spec.radius <= 0.f)
            return 0;
        Entry e;
        e.id = _nextId++;
        e.at = at;
        e.dwell = DwellTracker(static_cast<uint32>(spec.dwell.count()));
        // The Soak never resolves: Update cancels it at `life`, a poll before its warn ends (no MissedSoak).
        Milliseconds const warn = spec.life + Milliseconds(kPollMs * 4);
        {
            BossMechanics::MechanicRef ref = Mechanic::Soak(owner, at, spec.radius, std::max<uint8>(1, spec.count),
                warn);
            ref.Eligible(spec.who).NoFillTimer();
            if (spec.color)
                ref.Color(*spec.color);
            if (spec.tag)
                ref.Tag(spec.tag);
            e.soak = ref.Handle();
        }
        if (spec.visualEntry)
            if (TempSummon* look = owner->SummonCreature(spec.visualEntry, at, TEMPSUMMON_TIMED_DESPAWN,
                    static_cast<uint32>(spec.life.count()) + 1000))
            {
                look->SetReactState(REACT_PASSIVE);
                e.visual = look->GetGUID();
            }
        if (spec.goEntry)
            if (GameObject* go = owner->SummonGameObject(spec.goEntry, at.GetPositionX(), at.GetPositionY(),
                    at.GetPositionZ(), at.GetOrientation(), 0.f, 0.f, 0.f, 0.f,
                    static_cast<uint32>(spec.life.count() / 1000) + 1))
                e.object = go->GetGUID();
        e.spec = std::move(spec);
        _pickups.push_back(std::move(e));
        return _pickups.back().id;
    }

    void Pickups::Remove(Creature* owner, Entry& e)
    {
        Mechanic::Cancel(owner, e.soak);
        Map* map = owner->GetMap();
        if (Creature* look = e.visual ? map->GetCreature(e.visual) : nullptr)
            look->DespawnOrUnsummon();
        if (GameObject* go = e.object ? map->GetGameObject(e.object) : nullptr)
            go->Delete();
    }

    void Pickups::Update(Creature* owner, uint32 diff)
    {
        if (!owner || _pickups.empty())
            return;
        _pollMs += diff;
        if (_pollMs < kPollMs)
            return;
        uint32 const elapsed = _pollMs;
        _pollMs = 0;

        // Work on a copy of the ids: a callback may add or cancel pickups.
        std::vector<uint32> ids;
        for (Entry const& e : _pickups)
            ids.push_back(e.id);
        Map* map = owner->GetMap();
        for (uint32 const id : ids)
        {
            auto it = std::find_if(_pickups.begin(), _pickups.end(), [id](Entry const& e) { return e.id == id; });
            if (it == _pickups.end())
                continue;
            it->ageMs += elapsed;

            std::vector<uint64> inside;
            std::vector<Player*> players;
            for (auto const& ref : map->GetPlayers())
            {
                Player* player = ref.GetSource();
                if (!player || !player->IsAlive() || player->IsGameMaster())
                    continue;
                if (player->GetExactDist2d(it->at) > it->spec.radius
                    || std::fabs(player->GetPositionZ() - it->at.GetPositionZ()) > 6.f)
                    continue;
                if (!it->spec.who.carriers.empty() && !it->spec.who.carriers.count(player->GetGUID()))
                    continue;
                if (it->spec.who.auraSpell)
                {
                    uint32 const stacks = Stacks(player, it->spec.who.auraSpell);
                    if (stacks < it->spec.who.minStacks || stacks > it->spec.who.maxStacks)
                        continue;
                }
                inside.push_back(player->GetGUID().GetRawValue());
                players.push_back(player);
            }

            uint64 const taker = it->dwell.Update(inside, elapsed);
            if (taker)
            {
                Player* player = nullptr;
                for (Player* p : players)
                    if (p->GetGUID().GetRawValue() == taker)
                        player = p;
                Entry e = std::move(*it);
                _pickups.erase(it);
                Remove(owner, e);
                if (e.spec.onPick && player)
                    e.spec.onPick(player);
                continue;
            }
            if (it->ageMs >= static_cast<uint32>(it->spec.life.count()))
            {
                Entry e = std::move(*it);
                _pickups.erase(it);
                Remove(owner, e);
                if (e.spec.onExpire)
                    e.spec.onExpire();
            }
        }
    }

    void Pickups::Cancel(Creature* owner, uint32 id)
    {
        auto it = std::find_if(_pickups.begin(), _pickups.end(), [id](Entry const& e) { return e.id == id; });
        if (it == _pickups.end())
            return;
        Entry e = std::move(*it);
        _pickups.erase(it);
        if (owner)
            Remove(owner, e);
    }

    void Pickups::Clear(Creature* owner)
    {
        std::vector<Entry> all = std::move(_pickups);
        _pickups.clear();
        _pollMs = 0;
        if (owner)
            for (Entry& e : all)
                Remove(owner, e);
    }

    void LogMechanic(char const* dungeon, char const* boss, char const* mechanic, std::string const& detail)
    {
        if (detail.empty())
            LOG_INFO(kLogCategory, "{} {} {}", dungeon, boss, mechanic);
        else
            LOG_INFO(kLogCategory, "{} {} {} {}", dungeon, boss, mechanic, detail);
    }
}
