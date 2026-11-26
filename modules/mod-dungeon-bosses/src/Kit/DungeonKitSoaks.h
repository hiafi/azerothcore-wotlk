/*
 * mod-dungeon-bosses, the shared dungeon kit (Zul'Farrak WP-KT, handoff section 3.11, F36; SP UK6): Soaks that must be
 * held. The registry's Soak is judged at its resolve and has no dwell; CrawlPickups has a dwell but lives on a summoned
 * unit. A held Soak sits on any unit (a sunk player) and is taken by the first eligible player who stands within its
 * radius for `dwell` without a break. The pure rules are DungeonKitSoakLogic.h (SoakAt).
 *
 *   DwellSoaks   held Soaks owned by one AI: a telegraph registry Soak on the anchor for the bots (MissedSoak Never:
 *                the cost of a missed rescue is the script's), a 250 ms poll with the dwell clock, onDone at the
 *                hold, onExpire at the life's end, onLost when the anchor dies or leaves. The anchors of every live
 *                held Soak (and anyone carrying `excludeAura`) never count and are never offered to the bots: two sunk
 *                players never rescue each other (heroic UK11 sinks everyone at once). Their carriers set follows the
 *                group and is re-registered when it changes.
 *
 * Call Update from UpdateAI (in combat), Clear from Reset, JustDied and EnterEvadeMode. Lambdas capture guids only.
 *
 *     DungeonKit::DwellSoaks _rescues;
 *     _rescues.Add(me, sunk, { .radius = 3.f, .dwell = 2000ms, .life = 8000ms, .excludeAura = SPELL_SUNK,
 *         .onDone = [guid](Player* rescuer, Unit* sunk) { Free(sunk); },
 *         .onExpire = [guid](ObjectGuid sunk) { StartExecute(sunk); }, .dungeon = "zf", .boss = "ukorz",
 *         .name = "rescue" });
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_SOAKS_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_SOAKS_H

#include "BossMechanics.h"
#include "DungeonKitSoakLogic.h"
#include "Duration.h"
#include "ObjectGuid.h"
#include <functional>
#include <optional>
#include <vector>

class Creature;
class Player;
class Unit;

namespace DungeonKit
{
    struct DwellSoakSpec
    {
        float radius = 3.f;                 // yd (2D) from the anchor
        float zBand = 6.f;                  // yd above or below the anchor that still count
        Milliseconds dwell{ 2000 };         // held this long without a break (0: on touch)
        Milliseconds life{ 0 };             // nobody held it by then: onExpire (0: until done or Cancel)
        uint8 count = 1;                    // bodies the bots send (the registry Soak's count)
        // The registry rule (roles, aura stacks). Its carriers: empty (the usual) is "every player on the map but the
        // anchors and the excluded", kept current; a set given here is used as it is (minus the anchors).
        BossMechanics::Eligibility who;
        uint32 excludeAura = 0;             // a player with this aura never holds one (the sunk)
        bool oneClaimPerBot = true;         // among this tag's live held Soaks, a bot claims one
        bool draw = true;                   // false: NoTelegraph
        std::optional<BossMechanics::Color> color;
        uint32 tag = 0;
        // Extra registry options on every registration. Capture guids only.
        std::function<void(BossMechanics::MechanicRef&)> configure;
        // Capture guids only. The held Soak is already gone when these run.
        std::function<void(Player* taker, Unit* anchor)> onDone;
        std::function<void(ObjectGuid anchor)> onExpire;
        std::function<void(ObjectGuid anchor)> onLost;  // the anchor died, left the map or is no longer found
        char const* dungeon = "kit";        // LogMechanic: "<dungeon> <boss> <name>-start|-done|-expire|-lost"
        char const* boss = "soak";
        char const* name = "held-soak";
    };

    class DwellSoaks
    {
    public:
        static uint32 constexpr kPollMs = 250;
        static Milliseconds constexpr kWholeFight{ 4 * 3600 * 1000 };  // a life-0 Soak's registry warning
        static Milliseconds constexpr kWarnSlack{ 5000 };              // a lived Soak is canceled before it resolves

        // Returns the held Soak's id (0: refused: no owner, no anchor or a dead one, radius <= 0, the anchor already
        // has one).
        uint32 Add(Creature* owner, Unit* anchor, DwellSoakSpec spec);
        void Update(Creature* owner, uint32 diff);
        void Cancel(Creature* owner, uint32 id);
        // The held Soak on `anchor`, if any (a rescue that frees by other means).
        void CancelOn(Creature* owner, ObjectGuid anchor);
        void Clear(Creature* owner);

        std::size_t Count() const { return _soaks.size(); }
        bool Has(ObjectGuid anchor) const;
        std::vector<uint32> Ids() const;
        ObjectGuid AnchorOf(uint32 id) const;
        // Milliseconds of life left (0: no life, or gone).
        uint32 LeftMs(uint32 id) const;
        BossMechanics::MechanicHandle SoakOf(uint32 id) const;

    private:
        struct Entry
        {
            uint32 id = 0;
            ObjectGuid anchor;
            DwellSoakSpec spec;
            SoakAt clock;
            BossMechanics::MechanicHandle soak;
            GuidSet carriers;    // the set the Soak was registered with
        };

        void Register(Creature* owner, Entry& e, GuidSet carriers);
        GuidSet CarriersFor(Creature* owner, Entry const& e) const;
        bool Excluded(Unit const* who) const;

        std::vector<Entry> _soaks;
        uint32 _nextId = 1;
        uint32 _pollMs = 0;
    };
}

#endif
