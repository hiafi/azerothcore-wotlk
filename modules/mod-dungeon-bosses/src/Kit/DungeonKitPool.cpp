/*
 * mod-dungeon-bosses, the shared dungeon kit: a health pool shared by several units (DungeonKitPool.h, Blackrock
 * Depths WP-KT-D2).
 */

#include "DungeonKitPool.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "GameTime.h"
#include "Map.h"
#include "MapReference.h"
#include "ObjectAccessor.h"
#include "Player.h"
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

        PoolHitKind KindOf(DamageEffectType type)
        {
            switch (type)
            {
                case DIRECT_DAMAGE:
                    return PoolHitKind::Melee;
                case SPELL_DIRECT_DAMAGE:
                    return PoolHitKind::Spell;
                case DOT:
                    return PoolHitKind::Periodic;
                default:
                    return PoolHitKind::Other;
            }
        }

        // The amount that takes `member` from its health to `target` (0 at or under it: SetHealth raises it).
        uint32 ToTarget(Creature* member, uint32 target)
        {
            uint32 const health = member->GetHealth();
            if (health > target)
                return health - target;
            if (health < target)
                member->SetHealth(target);
            return 0;
        }
    }

    SharedHealthPool::SharedHealthPool(SharedHealthPoolSpec spec)
        : _spec(std::move(spec)), _pool(_spec.maxHealth, _spec.castWindowMs)
    {
    }

    void SharedHealthPool::Add(Creature* member)
    {
        if (member)
            Add(member->GetGUID());
    }

    void SharedHealthPool::Add(ObjectGuid member)
    {
        if (member && !Contains(member))
            _members.push_back(member);
    }

    bool SharedHealthPool::Contains(ObjectGuid member) const
    {
        return std::find(_members.begin(), _members.end(), member) != _members.end();
    }

    void SharedHealthPool::ClearMembers()
    {
        _members.clear();
        Reset();
    }

    void SharedHealthPool::Engage(Creature* any)
    {
        if (!any)
            return;
        uint32 max = _spec.maxHealth;
        if (!max)
            max = any->GetMaxHealth();
        _pool.Start(max);
        _killer.Clear();
        _engaged = true;
        for (ObjectGuid const& guid : _members)
        {
            Creature* member = guid == any->GetGUID() ? any : ObjectAccessor::GetCreature(*any, guid);
            if (!member || !member->IsAlive())
                continue;
            member->SetHealth(member->GetMaxHealth());
            // The mirror lowers a member's health without player damage: drop the requirement or a kill gives nothing.
            member->LowerPlayerDamageReq(member->GetMaxHealth());
        }
        LogMechanic(_spec.dungeon, _spec.boss, "pool-engage", "max=" + std::to_string(_pool.Max()) + " members="
            + std::to_string(_members.size()));
    }

    void SharedHealthPool::MirrorAll(Creature* any, ObjectGuid skip)
    {
        for (ObjectGuid const& guid : _members)
        {
            if (guid == skip)
                continue;
            Creature* member = guid == any->GetGUID() ? any : ObjectAccessor::GetCreature(*any, guid);
            if (!member || !member->IsAlive())
                continue;
            uint32 const target = _pool.Mirror(member->GetMaxHealth());
            if (member->GetHealth() != target)
                member->SetHealth(target);
        }
    }

    bool SharedHealthPool::DamageTaken(Creature* me, Unit* attacker, uint32& damage, DamageEffectType type)
    {
        if (!me || !_engaged || !me->IsAlive() || !Contains(me->GetGUID()))
            return false;
        uint32 const before = damage;
        if (_pool.Emptied())
        {
            // Held at 1 health until the death tick.
            damage = ToTarget(me, 1);
            return damage != before;
        }

        PoolHit hit;
        hit.attacker = attacker && attacker != me ? attacker->GetGUID().GetRawValue() : 0;
        hit.kind = KindOf(type);
        hit.member = me->GetGUID().GetRawValue();
        hit.amount = damage;
        hit.atMs = NowMs();
        HealthPool::Result const r = _pool.Damage(hit);

        damage = ToTarget(me, _pool.Mirror(me->GetMaxHealth()));
        if (_spec.keepThreat && attacker && attacker != me && before > damage && me->IsHostileTo(attacker))
            me->AddThreat(attacker, static_cast<float>(before - damage));
        MirrorAll(me, me->GetGUID());

        if (r.emptied)
        {
            _killer = attacker ? attacker->GetGUID() : ObjectGuid::Empty;
            LogMechanic(_spec.dungeon, _spec.boss, "pool-empty", "unit=" + me->GetName() + " hit="
                + std::to_string(before));
            if (_spec.onEmpty)
                _spec.onEmpty(me, attacker);
        }
        return damage != before;
    }

    bool SharedHealthPool::HealReceived(Creature* me, Unit* healer, uint32& heal)
    {
        if (!me || !_engaged || !me->IsAlive() || !Contains(me->GetGUID()))
            return false;
        uint32 const before = heal;
        if (_pool.Emptied())
        {
            heal = 0;
            return before != 0;
        }

        PoolHit hit;
        hit.attacker = healer ? healer->GetGUID().GetRawValue() : 0;
        hit.kind = PoolHitKind::Heal;
        hit.member = me->GetGUID().GetRawValue();
        hit.amount = heal;
        hit.atMs = NowMs();
        _pool.Heal(hit);

        uint32 const target = _pool.Mirror(me->GetMaxHealth());
        uint32 const health = me->GetHealth();
        heal = target > health ? target - health : 0;
        if (health > target)
            me->SetHealth(target);
        MirrorAll(me, me->GetGUID());
        return heal != before;
    }

    uint32 SharedHealthPool::Restore(Creature* any, uint32 amount)
    {
        if (!any || !_engaged)
            return 0;
        uint32 const gain = _pool.Restore(amount);
        if (gain)
            MirrorAll(any);
        return gain;
    }

    uint32 SharedHealthPool::RestorePct(Creature* any, float pct)
    {
        if (!any || !_engaged)
            return 0;
        uint32 const gain = _pool.RestorePct(pct);
        if (gain)
            MirrorAll(any);
        return gain;
    }

    // R-2-FW MIN-1 / R-2-B MN-1: never a self-kill while a player can take the credit (ChoosePoolKiller).
    Unit* SharedHealthPool::ResolveKiller(Creature* any, char const*& source) const
    {
        Unit* recorded = _killer ? ObjectAccessor::GetUnit(*any, _killer) : nullptr;
        if (recorded && !recorded->IsInMap(any))
            recorded = nullptr;
        Player* recipient = nullptr;
        for (ObjectGuid const& guid : _members)
        {
            Creature* member = guid == any->GetGUID() ? any : ObjectAccessor::GetCreature(*any, guid);
            if (Player* p = member ? member->GetLootRecipient() : nullptr; p && p->IsInMap(any))
            {
                recipient = p;
                break;
            }
        }
        Player* mapPlayer = nullptr;
        if (!recorded && !recipient)
            for (MapReference const& ref : any->GetMap()->GetPlayers())
                if (Player* p = ref.GetSource(); p && p->IsAlive() && !p->IsGameMaster())
                {
                    mapPlayer = p;
                    break;
                }
        switch (ChoosePoolKiller(recorded != nullptr, recipient != nullptr, mapPlayer != nullptr))
        {
            case PoolKiller::Recorded:
                source = "recorded";
                return recorded;
            case PoolKiller::LootRecipient:
                source = "loot-recipient";
                return recipient;
            case PoolKiller::MapPlayer:
                source = "map-player";
                return mapPlayer;
            default:
                source = "self";
                return nullptr;
        }
    }

    void SharedHealthPool::KillAll(Creature* any)
    {
        char const* source = "self";
        Unit* killer = ResolveKiller(any, source);
        std::vector<ObjectGuid> const members = _members;   // a JustDied may touch the pool
        uint32 killed = 0;
        for (ObjectGuid const& guid : members)
        {
            Creature* member = guid == any->GetGUID() ? any : ObjectAccessor::GetCreature(*any, guid);
            if (!member || !member->IsAlive())
                continue;
            Unit::Kill(killer && killer->IsInMap(member) ? killer : member, member);
            ++killed;
        }
        LogMechanic(_spec.dungeon, _spec.boss, "pool-death", "killed=" + std::to_string(killed) + " killer="
            + source);
    }

    void SharedHealthPool::Update(Creature* me)
    {
        if (!me || !_engaged || !Contains(me->GetGUID()))
            return;
        if (_pool.TakeDeathTick())
        {
            KillAll(me);
            return;
        }
        if (_pool.Emptied() || !me->IsAlive())
            return;
        uint32 const target = _pool.Mirror(me->GetMaxHealth());
        if (me->GetHealth() != target)
            me->SetHealth(target);
    }

    void SharedHealthPool::Reset()
    {
        _engaged = false;
        _killer.Clear();
        _pool.Start(_spec.maxHealth);
    }
}
