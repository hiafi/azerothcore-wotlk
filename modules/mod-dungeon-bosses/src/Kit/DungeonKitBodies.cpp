/*
 * mod-dungeon-bosses, the shared dungeon kit: death spots and held bodies (DungeonKitBodies.h, Blackrock Depths
 * WP-KT-D1).
 */

#include "DungeonKitBodies.h"
#include "Creature.h"
#include "GameTime.h"
#include "MotionMaster.h"
#include "Random.h"
#include "Unit.h"
#include <algorithm>
#include <string>

namespace DungeonKit
{
    namespace
    {
        uint64 NowMs()
        {
            return static_cast<uint64>(GameTime::GetGameTimeMS().count());
        }

        DeathSpotAt ToEngine(DeathSpot const& s)
        {
            DeathSpotAt r;
            r.guid = ObjectGuid(s.id);
            r.entry = s.entry;
            r.at = Position(s.at.x, s.at.y, s.z, s.o);
            r.tag = s.tag;
            return r;
        }

        std::vector<DeathSpotAt> ToEngine(std::vector<DeathSpot> const& spots)
        {
            std::vector<DeathSpotAt> out;
            out.reserve(spots.size());
            for (DeathSpot const& s : spots)
                out.push_back(ToEngine(s));
            return out;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // DeathSpots
    // ----------------------------------------------------------------------------------------------------------------

    void DeathSpots::Record(Unit const* dead, uint32 tag)
    {
        if (!dead)
            return;
        Record(dead->GetGUID(), dead->IsPlayer() ? 0 : dead->GetEntry(), dead->GetPosition(), tag);
    }

    void DeathSpots::Record(ObjectGuid guid, uint32 entry, Position const& at, uint32 tag)
    {
        DeathSpot s;
        s.id = guid.GetRawValue();
        s.entry = entry;
        s.at = { at.GetPositionX(), at.GetPositionY() };
        s.z = at.GetPositionZ();
        s.o = at.GetOrientation();
        s.atMs = NowMs();
        s.tag = tag;
        _book.Record(s);
    }

    std::vector<DeathSpotAt> DeathSpots::TakeOldest(std::size_t n, DeathSpotFilter const& filter)
    {
        return ToEngine(_book.TakeOldest(n, filter));
    }

    std::vector<DeathSpotAt> DeathSpots::TakeRandom(std::size_t n, DeathSpotFilter const& filter)
    {
        return ToEngine(_book.TakeRandom(n, [](uint32 k) { return k ? urand(0, k - 1) : 0u; }, filter));
    }

    std::optional<DeathSpotAt> DeathSpots::Find(ObjectGuid guid) const
    {
        std::optional<DeathSpot> const s = _book.Find(guid.GetRawValue());
        if (!s)
            return std::nullopt;
        return ToEngine(*s);
    }

    std::optional<DeathSpotAt> DeathSpots::Nearest(Position const& p, float maxYd,
        DeathSpotFilter const& filter) const
    {
        std::optional<DeathSpot> const s = _book.Nearest({ p.GetPositionX(), p.GetPositionY() }, maxYd, filter);
        if (!s)
            return std::nullopt;
        return ToEngine(*s);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HeldBody
    // ----------------------------------------------------------------------------------------------------------------

    HeldBody::HeldBody(HeldBodySpec spec)
        : _spec(std::move(spec)),
          _latch(_spec.holds, static_cast<uint32>(std::max<int64>(0, _spec.holdLimit.count())))
    {
    }

    void HeldBody::LieDown(Creature* me)
    {
        _reactBefore = static_cast<uint8>(me->GetReactState());
        me->InterruptNonMeleeSpells(false);
        me->AttackStop();
        me->StopMoving();
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MoveIdle();
        me->SetReactState(REACT_PASSIVE);
        // Players and bots drop it (IsValidAttackTarget); friendly spells (a resurrection) still reach it.
        me->SetUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
        if (_spec.look)
        {
            me->SetStandState(UNIT_STAND_STATE_DEAD);
            me->SetDynamicFlag(UNIT_DYNFLAG_DEAD);
            me->SetUnitFlag2(UNIT_FLAG2_FEIGN_DEATH);
        }
        if (_spec.root)
            me->SetControlled(true, UNIT_STATE_ROOT);
        if (_spec.fallAura)
            me->CastSpell(me, _spec.fallAura, true);
        _lying = true;
    }

    void HeldBody::StandUp(Creature* me)
    {
        if (!_lying)
            return;
        _lying = false;
        if (_spec.fallAura)
            me->RemoveAurasDueToSpell(_spec.fallAura);
        if (_spec.root)
            me->SetControlled(false, UNIT_STATE_ROOT);
        if (_spec.look)
        {
            me->RemoveUnitFlag2(UNIT_FLAG2_FEIGN_DEATH);
            me->RemoveDynamicFlag(UNIT_DYNFLAG_DEAD);
            me->SetStandState(UNIT_STAND_STATE_STAND);
        }
        me->RemoveUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
        me->SetReactState(static_cast<ReactStates>(_reactBefore));
    }

    bool HeldBody::Intercept(Creature* me, uint32& damage)
    {
        if (!me || !me->IsAlive())
            return false;
        HeldBodyLatch::Result const r = _latch.Apply(me->GetHealth(), damage);
        if (!r.clamped)
            return false;
        damage = r.damage;
        if (r.fell)
        {
            _spot = me->GetPosition();
            LieDown(me);
            LogMechanic(_spec.dungeon, _spec.boss, "body-fall", "unit=" + me->GetName() + " fall="
                + std::to_string(_latch.Falls()));
            if (_spec.onFall)
                _spec.onFall(me);
        }
        return true;
    }

    bool HeldBody::Revive(Creature* me, float healthPct)
    {
        if (!me || !me->IsAlive() || !_latch.Revive())
            return false;
        StandUp(me);
        float const pct = healthPct < 0.f ? _spec.revivePct : healthPct;
        me->SetHealth(std::max<uint32>(1, me->CountPctFromMaxHealth(std::clamp(pct, 0.f, 100.f))));
        LogMechanic(_spec.dungeon, _spec.boss, "body-revive", "unit=" + me->GetName() + " pct="
            + std::to_string(static_cast<int>(pct + 0.5f)));
        if (_spec.onRevive)
            _spec.onRevive(me);
        return true;
    }

    bool HeldBody::Finish(Creature* me, Unit* killer)
    {
        if (!me || !me->IsAlive() || !_latch.Finish())
            return false;
        StandUp(me);
        LogMechanic(_spec.dungeon, _spec.boss, "body-finish", "unit=" + me->GetName());
        if (_spec.onFinish)
            _spec.onFinish(me);
        if (me->IsAlive())
            Unit::Kill(killer && killer->IsInMap(me) ? killer : me, me);
        return true;
    }

    void HeldBody::Update(Creature* me, uint32 diff)
    {
        if (me && _latch.Update(diff))
            Finish(me);
    }

    void HeldBody::Reset(Creature* me)
    {
        if (me)
            StandUp(me);
        _lying = false;
        _latch.Reset();
    }
}
