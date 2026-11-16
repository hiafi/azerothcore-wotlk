/*
 * mod-dungeon-bosses, the shared dungeon kit: the ring wall (Blackrock Spire WP-KT-B2, handoff section 3.11 #6), the
 * circle form of LethalWall (DungeonKitWalls.h) for Drakkisath's Champion's Challenge (SP DR17-DR18): a ring of fire
 * closes round the boss and his challenger, everyone else inside is pushed out (knockback, no damage), and for its
 * life the band kills whoever stands in it or crosses it, as the arena walls do (user ruling F-2: an outright kill).
 * The pure rules are DungeonKitRingLogic.h.
 *
 *   LethalRing    registers the ring: a telegraph-only persistent Donut, `.Lethal()` (bots never plan a way across,
 *                 inside or out; `.SparesPets()` with pets = false), armed `armAfter` after the close; pushes out at
 *                 the close and, on every tick, anyone not kept in who got inside the disc; strikes every player (and
 *                 pet, unless pets = false) in the band and every one whose step crossed it (pushed units fly over it
 *                 under a grace)
 *   RingInside    the hard bounds that keep a bot inside (the challenger): SpotBounds().Circle inside the band, for
 *                 the bot's Within(...) on the challenge's Zones
 *   LethalRings   the rings one AI raised (and their carriers): Add, Clear (Reset / JustDied / EnterEvadeMode)
 *
 * Lambdas kept by the registry capture the map and guids only, never a Unit*.
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_RING_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_RING_H

#include "BossMechanics.h"
#include "DungeonKit.h"
#include "DungeonKitRingLogic.h"
#include "DungeonKitWallLogic.h"
#include "Duration.h"
#include "ObjectGuid.h"
#include "Position.h"
#include <functional>
#include <optional>
#include <vector>

class Unit;

namespace DungeonKit
{
    struct LethalRingSpec
    {
        Position center;                                // the ring's centre on the floor (z: the floor there)
        float radius = kRingDefaultRadiusYd;            // the band's middle (SP DR17: 12 yd)
        float width = kRingDefaultWidthYd;              // the band: the hitbox and the marker
        // The strike (an INSTAKILL spell bound to spell_dungeon_lethal_strike), cast for its look; a victim still
        // standing is killed outright (FinishLethalStrike). 0: Unit::Kill only.
        uint32 killSpell = 0;
        Milliseconds armAfter{ kRingArmMs };            // the close to the first kill (the push lands first)
        Milliseconds lifetime{ kRingLifeMs };           // armed for this long (SP DR17: 12 s)
        Milliseconds tick{ kWallTickMs };
        float zBand = 6.f;                              // units this far above or below the centre's z count
        float zTolerance = 0.f;                         // > 0: the registry hitbox's ZTolerance
        // false: pets and guardians are never struck (pushed out), and the ring says so to the bots (SparesPets).
        bool pets = true;                               // pets and guardians die in the band too
        bool crossings = true;                          // a step across the band between ticks kills
        // The units it closes round (the challenger; the boss is a creature and never counts): never pushed. Their
        // pets are pushed unless listed.
        std::vector<ObjectGuid> keepIn;
        bool spareKeepIn = false;                       // true: the kept-in units are never struck (they may leave)
        bool pushOut = true;
        float pushClearYd = kRingPushClearYd;           // a pushed unit lands this far past the band
        float pushSpeedZ = kRingPushSpeedZ;
        bool pushDuringLife = true;                     // also push anyone not kept in found inside the disc later
        std::optional<BossMechanics::Color> color;      // default: the encounter's get-out color
        uint32 tag = 0;
        // A unit that carries the ring's look (SP: "Challenge ring, invisible trigger", 300741): summoned on the
        // centre for armAfter + lifetime (timed despawn), `carrierAura` cast on itself. 0: none.
        uint32 carrierEntry = 0;
        uint32 carrierAura = 0;
        std::vector<ObjectGuid> strikers;               // as LethalWallSpec::strikers (empty: the owner strikes)
        char const* dungeon = "kit";                    // LogMechanic: "<dungeon> <boss> lethal-ring ..."
        char const* boss = "ring";
        std::function<void(Unit* victim)> onStrike;     // after each strike (capture guids only)
        std::function<void(Unit* pushed)> onPush;       // after each push (capture guids only)
    };

    // The pure ring of a spec.
    inline RingWall RingWallOf(LethalRingSpec const& spec)
    {
        return { { spec.center.GetPositionX(), spec.center.GetPositionY() }, spec.radius, spec.width };
    }

    // Registers (and, at the end of the calling statement, commits) one ring, pushing out at once everyone not kept in
    // inside the band's outer edge. A telegraph-only persistent Donut (inner, outer edge of the band), warn armAfter,
    // ticking every `tick` for `lifetime`, NoFillTimer, Lethal, no Eligible and no TankExempt. Further options may be
    // chained on the returned ref (Color, Within); do not replace its OnResolve, and do not add Damage, Weakened or
    // OnHit. Spawns the carrier when the spec names one: use LethalRings to have it despawned on Clear (else it goes
    // with its timer). Returns an invalid ref when refused (no owner, no map, radius or width <= 0, a band wider
    // than the radius).
    BossMechanics::MechanicRef LethalRing(Unit* owner, LethalRingSpec const& spec, ObjectGuid* carrier = nullptr);

    // Hard bounds for a bot kept inside the ring (the challenger): the disc `marginYd` inside the band.
    BossMechanics::SpotBounds RingInside(LethalRingSpec const& spec, float marginYd = 1.f);

    // The rings one boss AI raised. Clear from Reset / JustDied / EnterEvadeMode: it cancels the rings and despawns
    // their carriers (the registry also ends an owner's mechanics on death, evade and despawn).
    //
    //     DungeonKit::LethalRings _rings;
    //     LethalRingSpec ring;
    //     ring.center = me->GetPosition();                     // or between him and the challenger
    //     ring.keepIn = { challenger->GetGUID() };
    //     ring.killSpell = SPELL_DR_RING_STRIKE;
    //     ring.carrierEntry = NPC_CHALLENGE_RING; ring.carrierAura = SPELL_DR_RING_VISUAL;
    //     _rings.Add(me, ring);
    //     ... Mechanic::Zone(...).Within(DungeonKit::RingInside(ring))   // the challenge's blows: the bot stays in
    //     void JustDied(Unit*) override { _rings.Clear(me); ... }
    class LethalRings
    {
    public:
        BossMechanics::MechanicHandle Add(Unit* owner, LethalRingSpec const& spec);
        void Clear(Unit* owner);
        // Forget rings whose registry entry is gone (expired) and despawn their carriers; true if any is still live.
        bool Prune(Unit* owner);

        // A unit stands in the band of any live ring now (the registry's hitbox).
        bool Contains(Unit* owner, Unit const* who) const;
        std::size_t Count() const { return _rings.size(); }

    private:
        struct Live
        {
            BossMechanics::MechanicHandle handle;
            ObjectGuid carrier;
        };

        std::vector<Live> _rings;
    };
}

#endif
