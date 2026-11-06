/*
 * mod-dungeon-bosses, Deadmines: the shared kit's engine glue (DeadminesKit.h).
 */

#include "DeadminesKit.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "Map.h"
#include "SpellAuras.h"
#include "Unit.h"

namespace DeadminesKit
{
    uint32 RefFlat(Unit const* owner, float pct, bool tank)
    {
        // mod-boss-mechanics' own helper (WP-X): the registry's content key, reference row and rounding.
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
        if (linger.slow)
            ref.Rider(DeadminesRework::SPELL_DM_STANDING_IN_IT);
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

    BossMechanics::RoomFrame DeckFrame()
    {
        BossMechanics::RoomFrame frame;
        frame.origin = ToPosition(DeadminesRework::kDeckOrigin, DeadminesRework::kDeckZ, DeadminesRework::kDeckAngle);
        frame.angle = DeadminesRework::kDeckAngle;
        frame.sizeX = DeadminesRework::kDeckLength;
        frame.sizeY = DeadminesRework::kDeckWidth;
        return frame;
    }
}
