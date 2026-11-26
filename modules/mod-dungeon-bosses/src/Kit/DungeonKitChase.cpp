/*
 * mod-dungeon-bosses, the shared dungeon kit: the Blackrock Spire wave 1 movers (DungeonKitChase.h, WP-KT-B1).
 */

#include "DungeonKitChase.h"
#include "Creature.h"
#include "DungeonKitFields.h"
#include "Map.h"
#include "MechanicRegistry.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "TemporarySummon.h"
#include "ThreatManager.h"
#include "Unit.h"
#include <algorithm>

namespace DungeonKit
{
    namespace
    {
        uint32 constexpr kChasePointId = 0x43485345;    // "CHSE": the chaser's re-aimed MovePoint
        uint32 constexpr kCrawlPointId = 0x43524C57;    // "CRLW": a crawl's MovePoint fallback

        uint32 Ms(Milliseconds d)
        {
            return static_cast<uint32>(std::max<int64>(0, d.count()));
        }

        // A script (spell id 0) immunity of this op and type is already on the unit.
        bool HasScriptImmunity(Unit const* unit, uint32 op, uint32 type)
        {
            auto const bounds = unit->m_spellImmune[op].equal_range(type);
            for (auto itr = bounds.first; itr != bounds.second; ++itr)
                if (!itr->second)
                    return true;
            return false;
        }

        bool ChaseTargetValid(Creature const* chaser, Unit const* target)
        {
            if (!target || !target->IsInWorld() || !target->IsAlive() || target->GetMap() != chaser->GetMap())
                return false;
            if (Player const* p = target->ToPlayer())
                if (p->IsGameMaster())
                    return false;
            return true;
        }

        // Tossed (a knockback or a jump: the controlled slot's effect movement) or stunned, feared, confused.
        bool ChaserControlled(Creature* chaser)
        {
            return chaser->HasUnitState(UNIT_STATE_LOST_CONTROL)
                || chaser->GetMotionMaster()->GetMotionSlotType(MOTION_SLOT_CONTROLLED) == EFFECT_MOTION_TYPE;
        }

        void StopPointMove(Unit* unit)
        {
            if (unit->GetMotionMaster()->GetCurrentMovementGeneratorType() == POINT_MOTION_TYPE)
            {
                unit->GetMotionMaster()->Clear(false);
                unit->StopMoving();
            }
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Chaser
    // ----------------------------------------------------------------------------------------------------------------

    bool Chaser::Start(Creature* chaser, Unit* target, ChaserSpec spec, Creature* picker)
    {
        if (!chaser || !chaser->IsInWorld() || !chaser->IsAlive() || !ChaseTargetValid(chaser, target))
            return false;
        if (_active)
            Stop(chaser);

        _spec = std::move(spec);
        ChaseTuning tuning;
        tuning.pauseMs = Ms(_spec.pauseOnControl);
        tuning.retargetEveryMs = Ms(_spec.retargetEvery);
        tuning.lifeMs = Ms(_spec.life);
        tuning.reach = _spec.reach;
        tuning.endOnArrive = _spec.endOnArrive;
        _clock = ChaseClock(tuning);
        _target = target->GetGUID();
        _picker = picker ? picker->GetGUID() : ObjectGuid::Empty;
        _repathMs = 0;

        _prevCombatMovement = chaser->IsCombatMovementAllowed();
        chaser->SetCombatMovement(false);
        // A spell-0 immunity exists once per type (Unit::ApplySpellImmune): only the ones this chase adds are
        // removed at its end, so an immunity a script set before the chase survives it (R-1-KIT K-n2).
        _setTauntImmune = _spec.tauntImmune && !HasScriptImmunity(chaser, IMMUNITY_STATE, SPELL_AURA_MOD_TAUNT);
        _setAttackMeImmune = _spec.tauntImmune && !HasScriptImmunity(chaser, IMMUNITY_EFFECT, SPELL_EFFECT_ATTACK_ME);
        if (_setTauntImmune)
            chaser->ApplySpellImmune(0, IMMUNITY_STATE, SPELL_AURA_MOD_TAUNT, true);
        if (_setAttackMeImmune)
            chaser->ApplySpellImmune(0, IMMUNITY_EFFECT, SPELL_EFFECT_ATTACK_ME, true);
        if (_spec.fixate)
        {
            chaser->GetThreatMgr().AddThreat(target, 0.f, nullptr, true, true);
            chaser->GetThreatMgr().FixateTarget(target);
        }
        chaser->SetWalk(false);
        _active = true;
        ApplySpeed(chaser);
        Aim(chaser, target);
        return true;
    }

    void Chaser::ApplySpeed(Creature* chaser) const
    {
        if (_spec.speed <= 0.f)
            return;
        float rate = _spec.speed / kPlayerRunYdPerSec;
        if (_spec.honorSlows)
            if (int32 const slow = chaser->GetMaxNegativeAuraModifier(SPELL_AURA_MOD_DECREASE_SPEED))
                rate *= std::max(0.f, 100.f + static_cast<float>(slow)) / 100.f;
        chaser->SetSpeed(MOVE_RUN, rate);
    }

    void Chaser::Aim(Creature* chaser, Unit* target)
    {
        _repathMs = 0;
        chaser->GetMotionMaster()->MovePoint(kChasePointId, target->GetPosition());
    }

    bool Chaser::Retarget(Creature* chaser)
    {
        Creature* picker = _picker ? ObjectAccessor::GetCreature(*chaser, _picker) : chaser;
        if (!picker || !picker->IsInWorld() || !picker->IsAlive() || picker->GetMap() != chaser->GetMap())
            picker = chaser;

        PickRule other = _spec.pick;
        if (_target)
            other.exclude.push_back(_target.GetRawValue());
        Player* pick = PickPlayer(picker, other);
        if (!pick)
            pick = PickPlayer(picker, _spec.pick);     // nobody else: the old target again, if it still qualifies
        if (!pick)
            return false;

        _clock.Retargeted();
        bool const changed = pick->GetGUID() != _target;
        _target = pick->GetGUID();
        if (changed && _spec.fixate)
        {
            chaser->GetThreatMgr().AddThreat(pick, 0.f, nullptr, true, true);
            chaser->GetThreatMgr().FixateTarget(pick);
        }
        Aim(chaser, pick);
        if (changed && _spec.onTarget)
        {
            auto const onTarget = _spec.onTarget;   // a copy: the callback may restart the chase
            onTarget(chaser, pick);
        }
        return true;
    }

    void Chaser::Update(Creature* chaser, uint32 diff)
    {
        if (!_active)
            return;
        if (!chaser || !chaser->IsInWorld() || !chaser->IsAlive())
        {
            Finish(chaser, ChaseEnd::Stopped, nullptr);
            return;
        }

        Unit* target = ObjectAccessor::GetUnit(*chaser, _target);
        bool const valid = ChaseTargetValid(chaser, target);
        bool const controlled = ChaserControlled(chaser);
        float const dist = valid ? chaser->GetExactDist2d(target) : 0.f;

        switch (_clock.Update(diff, controlled, valid, dist))
        {
            case ChaseStep::Expire:
                Finish(chaser, ChaseEnd::Expired, valid ? target : nullptr);
                return;
            case ChaseStep::Hold:
                // Under the control the motion master is the toss's or the stun's; in the pause after it, stand.
                if (!controlled)
                    StopPointMove(chaser);
                _repathMs = Ms(_spec.repath);   // re-aim at once when the hold ends
                return;
            case ChaseStep::Retarget:
                if (!Retarget(chaser))
                {
                    if (valid)
                    {
                        // The period ran out and nobody qualifies, not even the old target: keep after it.
                        _clock.Retargeted();
                        Aim(chaser, target);
                    }
                    else
                        Finish(chaser, ChaseEnd::NoTarget, nullptr);
                }
                return;
            case ChaseStep::Arrive:
                if (_spec.endOnArrive)
                {
                    Finish(chaser, ChaseEnd::Arrived, target);
                    return;
                }
                if (_spec.onArrive)
                {
                    auto const onArrive = _spec.onArrive;
                    onArrive(chaser, target);
                    if (!_active)
                        return;
                }
                break;
            case ChaseStep::Move:
                break;
        }

        _repathMs += diff;
        if (_repathMs >= Ms(_spec.repath) || chaser->GetMotionMaster()->GetCurrentMovementGeneratorType()
            != POINT_MOTION_TYPE)
        {
            ApplySpeed(chaser);
            Aim(chaser, target);
        }
    }

    void Chaser::Stop(Creature* chaser)
    {
        if (_active)
            Finish(chaser, ChaseEnd::Stopped, nullptr);
    }

    void Chaser::Finish(Creature* chaser, ChaseEnd why, Unit* target)
    {
        _active = false;
        // Copies: a callback may start a new chase on this object.
        auto const onArrive = _spec.onArrive;
        auto const onEnd = _spec.onEnd;
        bool const setTaunt = _setTauntImmune;
        bool const setAttackMe = _setAttackMeImmune;
        bool const fixate = _spec.fixate;
        bool const ownSpeed = _spec.speed > 0.f;
        _setTauntImmune = false;
        _setAttackMeImmune = false;

        if (chaser && chaser->IsInWorld())
        {
            if (setTaunt)
                chaser->ApplySpellImmune(0, IMMUNITY_STATE, SPELL_AURA_MOD_TAUNT, false);
            if (setAttackMe)
                chaser->ApplySpellImmune(0, IMMUNITY_EFFECT, SPELL_EFFECT_ATTACK_ME, false);
            if (chaser->IsAlive())
            {
                if (fixate)
                    chaser->GetThreatMgr().ClearFixate();
                if (ownSpeed)
                    chaser->UpdateSpeed(MOVE_RUN, false);   // the template's run speed and its auras again
                StopPointMove(chaser);
                chaser->SetCombatMovement(_prevCombatMovement);
                if (chaser->IsCombatMovementAllowed())
                    if (Unit* victim = chaser->GetVictim())
                        chaser->GetMotionMaster()->MoveChase(victim);
            }
        }

        if (!chaser)
            return;
        if (why == ChaseEnd::Arrived && onArrive)
            onArrive(chaser, target);
        else if ((why == ChaseEnd::Expired || why == ChaseEnd::NoTarget) && onEnd)
            onEnd(chaser, why);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // CrawlPickups
    // ----------------------------------------------------------------------------------------------------------------

    uint32 CrawlPickups::Add(Creature* owner, Position const& at, CrawlPickupSpec spec, CrawlGoal goal)
    {
        if (!owner || !owner->IsInWorld() || !spec.entry || spec.radius <= 0.f)
            return 0;
        TempSummon* unit = owner->SummonCreature(spec.entry, at, TEMPSUMMON_MANUAL_DESPAWN);
        if (!unit)
            return 0;
        unit->SetReactState(REACT_PASSIVE);

        Entry e;
        e.id = _nextId++;
        e.unit = unit->GetGUID();
        e.goal = std::move(goal);
        e.clock = CrawlClock(Ms(spec.wait), Ms(spec.life), spec.reach, spec.crawl);
        e.dwell = DwellTracker(Ms(spec.dwell));
        e.last = at;
        if (spec.onlyWhileCarriers)
            spec.who.carriers = _carriers;
        e.spec = std::move(spec);
        RegisterSoak(owner, e, unit);
        _pickups.push_back(std::move(e));
        return _pickups.back().id;
    }

    // Telegraph only: the Soak shows the pickup to the bots and never posts a failure (the arrival is the cost). A
    // pickup with a life is cancelled before its warning ends; one without lasts the whole fight. A dormant pickup
    // (onlyWhileCarriers, nobody to take it) has none.
    void CrawlPickups::RegisterSoak(Creature* owner, Entry& e, Creature* unit)
    {
        if (e.soak)
            Mechanic::Cancel(owner, e.soak);
        e.soak = {};
        if (e.spec.onlyWhileCarriers && e.spec.who.carriers.empty())
            return;
        if (!unit)
            unit = e.unit ? owner->GetMap()->GetCreature(e.unit) : nullptr;
        if (!unit)
            return;
        uint32 const lifeMs = Ms(e.spec.life);
        uint32 const ageMs = e.clock.AgeMs();
        Milliseconds const warn = lifeMs > 0 ? Milliseconds(lifeMs > ageMs ? lifeMs - ageMs : 0) + Milliseconds(5000)
            : kWholeFight;
        BossMechanics::MechanicRef ref = Mechanic::Soak(owner, unit, e.spec.radius, std::max<uint8>(1, e.spec.count),
            warn);
        ref.MissedSoak(BossMechanics::MissedSoakMode::Never).Eligible(e.spec.who).NoFillTimer();
        if (e.spec.order)
            ref.Order(*e.spec.order);
        if (e.spec.oneClaimPerBot)
            ref.OneClaimPerBot();
        if (e.spec.color)
            ref.Color(*e.spec.color);
        if (e.spec.tag)
            ref.Tag(e.spec.tag);
        e.soak = ref.Handle();
    }

    void CrawlPickups::SetCarriers(Creature* owner, GuidSet carriers)
    {
        if (carriers == _carriers)
            return;
        _carriers = std::move(carriers);
        for (Entry& e : _pickups)
        {
            if (!e.spec.onlyWhileCarriers)
                continue;
            e.spec.who.carriers = _carriers;
            e.dwell.Clear();
            if (owner && owner->IsInWorld())
                RegisterSoak(owner, e);
        }
    }

    bool CrawlPickups::Dormant(uint32 id) const
    {
        for (Entry const& e : _pickups)
            if (e.id == id)
                return e.spec.onlyWhileCarriers && e.spec.who.carriers.empty();
        return false;
    }

    void CrawlPickups::SetGoal(CrawlGoal goal)
    {
        for (Entry& e : _pickups)
        {
            e.goal = goal;
            e.moving = false;       // re-path at the next poll
        }
    }

    bool CrawlPickups::GoalPosition(Map* map, CrawlGoal const& goal, Position& out) const
    {
        if (goal.unit)
        {
            Unit* u = nullptr;
            if (goal.unit.IsPlayer())
                u = ObjectAccessor::GetPlayer(map, goal.unit);
            else
                u = map->GetCreature(goal.unit);
            if (u && u->IsInWorld() && u->IsAlive())
            {
                out = u->GetPosition();
                return true;
            }
        }
        if (goal.point)
        {
            out = *goal.point;
            return true;
        }
        return false;
    }

    void CrawlPickups::Remove(Creature* owner, Entry& e)
    {
        Mechanic::Cancel(owner, e.soak);
        if (Creature* unit = e.unit ? owner->GetMap()->GetCreature(e.unit) : nullptr)
            unit->DespawnOrUnsummon();
    }

    void CrawlPickups::Update(Creature* owner, uint32 diff)
    {
        if (!owner || !owner->IsInWorld() || _pickups.empty())
            return;
        _pollMs += diff;
        if (_pollMs < kPollMs)
            return;
        uint32 const elapsed = _pollMs;
        _pollMs = 0;

        Map* map = owner->GetMap();
        BossMechanics::Registry const* reg = BossMechanics::Registry::Get(map);
        for (uint32 const id : Ids())
        {
            auto it = std::find_if(_pickups.begin(), _pickups.end(), [id](Entry const& e) { return e.id == id; });
            if (it == _pickups.end())
                continue;
            Creature* unit = map->GetCreature(it->unit);
            if (!unit || !unit->IsInWorld() || !unit->IsAlive())
            {
                // Gone from under us (despawned elsewhere): the pickup goes quietly.
                Entry e = std::move(*it);
                _pickups.erase(it);
                Remove(owner, e);
                continue;
            }
            Position const pos = unit->GetPosition();
            it->last = pos;

            // The Soak's own eligibility: the rule the bots follow (Pickups::Update's check, on the moving unit).
            BossMechanics::ActiveMechanic const* soak = reg ? reg->Find(it->soak.id) : nullptr;
            std::vector<uint64> inside;
            std::vector<Player*> players;
            bool const dormant = it->spec.onlyWhileCarriers && it->spec.who.carriers.empty();
            for (auto const& ref : map->GetPlayers())
            {
                if (dormant)
                    break;      // nobody may take it now (an empty who would mean everyone)
                Player* player = ref.GetSource();
                if (!player || !player->IsAlive() || player->IsGameMaster())
                    continue;
                if (!InPickupRange(player->GetExactDist2d(pos), player->GetPositionZ() - pos.GetPositionZ(),
                        it->spec.radius, it->spec.zBand))
                    continue;
                if (soak)
                {
                    if (!reg->IsEligible(*soak, player))
                        continue;
                }
                else
                {
                    if (!it->spec.who.carriers.empty() && !it->spec.who.carriers.count(player->GetGUID()))
                        continue;
                    if (it->spec.who.auraSpell)
                    {
                        uint32 const stacks = Stacks(player, it->spec.who.auraSpell);
                        if (stacks < it->spec.who.minStacks || stacks > it->spec.who.maxStacks)
                            continue;
                    }
                }
                inside.push_back(player->GetGUID().GetRawValue());
                players.push_back(player);
            }
            if (uint64 const taker = it->dwell.Update(inside, elapsed))
            {
                Player* player = nullptr;
                for (Player* p : players)
                    if (p->GetGUID().GetRawValue() == taker)
                        player = p;
                Entry e = std::move(*it);
                _pickups.erase(it);
                Remove(owner, e);
                if (e.spec.onPick && player)
                    e.spec.onPick(player, pos);
                continue;
            }

            Position goal;
            bool const hasGoal = GoalPosition(map, it->goal, goal);
            float const dist = hasGoal ? unit->GetExactDist2d(goal.GetPositionX(), goal.GetPositionY()) : 0.f;
            switch (it->clock.Update(elapsed, hasGoal, dist))
            {
                case CrawlStep::Reach:
                {
                    Entry e = std::move(*it);
                    _pickups.erase(it);
                    Remove(owner, e);
                    if (e.spec.onReach)
                        e.spec.onReach(e.goal.unit, pos);
                    break;
                }
                case CrawlStep::Expire:
                {
                    Entry e = std::move(*it);
                    _pickups.erase(it);
                    Remove(owner, e);
                    if (e.spec.onExpire)
                        e.spec.onExpire(pos);
                    break;
                }
                case CrawlStep::Crawl:
                {
                    it->repathMs += elapsed;
                    if (it->moving && it->repathMs < Ms(it->spec.repath))
                        break;
                    it->repathMs = 0;
                    it->moving = true;
                    std::vector<FloorPathPoint> const path = FloorPathOnMap(unit, PlaneOf(unit),
                        Vec2{ goal.GetPositionX(), goal.GetPositionY() }, unit->GetPositionZ());
                    if (!MoveAlongFloor(unit, path, it->spec.crawlSpeed))
                        unit->GetMotionMaster()->MovePoint(kCrawlPointId, goal, FORCED_MOVEMENT_NONE,
                            it->spec.crawlSpeed);
                    break;
                }
                case CrawlStep::Wait:
                    if (it->moving)
                    {
                        // The goal went: lie still where it is.
                        it->moving = false;
                        unit->GetMotionMaster()->Clear(false);
                        unit->StopMoving();
                    }
                    break;
            }
        }
    }

    void CrawlPickups::Cancel(Creature* owner, uint32 id)
    {
        auto it = std::find_if(_pickups.begin(), _pickups.end(), [id](Entry const& e) { return e.id == id; });
        if (it == _pickups.end())
            return;
        Entry e = std::move(*it);
        _pickups.erase(it);
        if (owner && owner->IsInWorld())
            Remove(owner, e);
    }

    void CrawlPickups::Clear(Creature* owner)
    {
        std::vector<Entry> all = std::move(_pickups);
        _pickups.clear();
        _pollMs = 0;
        if (owner && owner->IsInWorld())
            for (Entry& e : all)
                Remove(owner, e);
    }

    ObjectGuid CrawlPickups::UnitOf(uint32 id) const
    {
        for (Entry const& e : _pickups)
            if (e.id == id)
                return e.unit;
        return ObjectGuid::Empty;
    }

    std::vector<uint32> CrawlPickups::Ids() const
    {
        std::vector<uint32> ids;
        ids.reserve(_pickups.size());
        for (Entry const& e : _pickups)
            ids.push_back(e.id);
        return ids;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // FallWatch
    // ----------------------------------------------------------------------------------------------------------------

    void FallWatch::Arm(FallWatchSpec spec)
    {
        _spec = std::move(spec);
        _book = FallCatchBook(Ms(_spec.grace));
        _armed = true;
        _pollMs = 0;
    }

    void FallWatch::Disarm()
    {
        _armed = false;
        _book.Clear();
        _pollMs = 0;
    }

    bool FallWatch::Watch(Unit* unit, uint64 nowMs)
    {
        float const z = unit->GetPositionZ();
        bool const inRegion = _spec.region.Empty() || _spec.region.Contains(PlaneOf(unit), z);
        if (!_book.Check(unit->GetGUID().GetRawValue(), z, inRegion, _spec.deckZ, _spec.below, nowMs))
            return false;
        // The fall so far no longer counts: the jump back lands higher than this, so no fall damage.
        if (Player* player = unit->ToPlayer())
            player->SetFallInformation(0, z);
        if (_spec.onCatch)
        {
            auto const onCatch = _spec.onCatch;     // a copy: the callback may re-arm or disarm the watch
            onCatch(unit);
        }
        return true;
    }

    uint32 FallWatch::Update(WorldObject* ref, uint32 diff)
    {
        if (!_armed || !ref || !ref->IsInWorld())
            return 0;
        _clockMs += diff;
        _pollMs += diff;
        if (_pollMs < kPollMs)
            return 0;
        _pollMs = 0;
        _book.Prune(_clockMs);

        // Guids first: a catch callback may move, kill or dismiss what it catches.
        Map* map = ref->GetMap();
        std::vector<ObjectGuid> watched;
        for (auto const& itr : map->GetPlayers())
        {
            Player* player = itr.GetSource();
            if (!player || !player->IsInWorld() || !player->IsAlive() || player->IsGameMaster())
                continue;
            watched.push_back(player->GetGUID());
            if (_spec.pets)
                for (Unit* controlled : player->m_Controlled)
                    if (controlled && controlled->IsInWorld() && controlled->IsAlive() && WatchesControlled(
                        controlled->IsPet(), controlled->IsGuardian(), controlled->IsTotem(), controlled->IsCharmed()))
                        watched.push_back(controlled->GetGUID());
        }

        uint32 caught = 0;
        for (ObjectGuid const& guid : watched)
        {
            if (!_armed)
                break;
            Unit* unit = ObjectAccessor::GetUnit(*ref, guid);
            if (!unit || !unit->IsInWorld() || !unit->IsAlive() || unit->GetMap() != map)
                continue;
            if (Watch(unit, _clockMs))
                ++caught;
        }
        return caught;
    }
}
