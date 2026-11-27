/*
 * mod-dungeon-bosses, the shared dungeon kit (Gnomeregan WP-KT-G, handoff section 3.11, F42; SP MT5, MT14): two-ring
 * mines. The registry's Mine has one radius (trigger = blast); here a small ring sets the mine off and a larger ring
 * takes the blast. The pure rules are DungeonKitMineLogic.h (MineRings, InBlast, MineBook).
 *
 *   TwoRingMines  per mine: the registry Mine on the trigger ring (its own look: ring and fill while it arms, the
 *                 dashed ring once armed; a player inside for the grace, or anyone inside at the arming, sets it off;
 *                 players only, so bombs and puddles never do), telegraph-only itself, and a persistent telegraph-only
 *                 Zone on the blast ring (outline only, warned over the arming) that keeps the bots out of the whole
 *                 blast with path avoidance. When the mine goes off, the kit hits every player inside the blast ring
 *                 with RegistryHit (damage, Weakened, rider, ledger) on the next Update (never inside the registry's
 *                 own resolve callback, rule 11). Detonate / DetonateAll (the Remote Detonator) blow them up now.
 *                 A mine whose life runs out goes without a blast.
 *
 * Owned by one AI: Configure at the pull, Update from UpdateAI, Clear from Reset, JustDied and EnterEvadeMode. Never
 * call Add, Detonate or DetonateAll from a registry callback (OnResolve, OnHit): queue it. Lambdas capture guids only.
 *
 *     DungeonKit::TwoRingMines _mines;
 *     _mines.Configure({ .triggerYd = 3.f, .blastYd = 6.f, .arm = 3000ms, .grace = 500ms, .life = 45000ms,
 *         .pct = 40.f, .dungeon = "gnomer-build", .boss = "thermaplugg", .name = "mine" });
 *     _mines.Add(me, player->GetPosition());
 *     _mines.DetonateAll(me);                                     // MT14, armed mines only
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_MINES_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_MINES_H

#include "BossMechanics.h"
#include "DungeonKitMineLogic.h"
#include "Duration.h"
#include "ObjectGuid.h"
#include "Position.h"
#include <functional>
#include <memory>
#include <optional>
#include <vector>

class Creature;
class Unit;

namespace DungeonKit
{
    struct TwoRingMineSpec
    {
        float triggerYd = 3.f;
        float blastYd = 6.f;
        float zBand = 6.f;                      // the blast's height band (and both rings' ZTolerance)
        Milliseconds arm{ 3000 };
        Milliseconds grace{ 500 };              // inside the armed trigger ring this long sets it off
        Milliseconds life{ 45000 };             // then it goes without a blast (0: until Detonate, Remove or Clear)
        // The blast (RegistryHit on the players inside the blast ring).
        float pct = 40.f;                       // % of the reference non-tank row
        float tankPct = -1.f;                   // >= 0: the tank takes this % of tank health instead
        uint8 school = 0;
        uint32 spellId = 0;                     // a dungeon copy of the resolve spell (0: by school)
        bool weakened = true;
        uint32 rider = 0;
        // Looks: the trigger ring is the registry mine's; the blast ring an outline (false: NoTelegraph, bots only).
        bool drawBlast = true;
        std::optional<BossMechanics::Color> triggerColor;
        std::optional<BossMechanics::Color> blastColor;
        uint32 tag = 0;
        // Extra registry options on every trigger mine and every blast ring (Within, ZTolerance ...).
        std::function<void(BossMechanics::MechanicRef&)> configureTrigger;
        std::function<void(BossMechanics::MechanicRef&)> configureBlast;
        // A registry callback for each player the blast hits (Voltage +1 per player hit). Capture guids only.
        std::function<void(Unit* hit)> onHit;
        // After each blast, from Update / Detonate (not a registry callback): who was inside, and whether a player
        // set it off (false: Detonate). Capture guids only.
        std::function<void(Creature* owner, uint32 id, Position const& at, GuidSet const& hit, bool tripped)> onBlast;
        char const* dungeon = "kit";            // LogMechanic: "<dungeon> <boss> <name>-add|-blast|-fizzle"
        char const* boss = "mines";
        char const* name = "mine";
    };

    class TwoRingMines
    {
    public:
        static uint32 constexpr kForeverMs = 3600000;

        // The field's rules for every Add from now on (mines already down keep theirs).
        void Configure(TwoRingMineSpec spec);
        TwoRingMineSpec const& Spec() const { return _spec; }

        // Lays a mine at `at` (its z is the floor). Returns its id (0: refused: no owner, bad rings, or the registry
        // refused the trigger mine).
        uint32 Add(Creature* owner, Position const& at);
        // The tripped mines' blasts and the lives that ran out.
        void Update(Creature* owner, uint32 diff);
        // Blows mine `id` up now, armed or not. False when there is no such mine.
        bool Detonate(Creature* owner, uint32 id);
        // MT14: blows up the armed mines (every mine with armedOnly false) now; returns how many.
        uint32 DetonateAll(Creature* owner, bool armedOnly = true);
        // Mine `id` goes without a blast.
        void Remove(Creature* owner, uint32 id);
        void Clear(Creature* owner);

        std::size_t Count() const { return _mines.size(); }
        std::size_t ArmedCount() const { return _book.ArmedCount(_nowMs); }
        bool Armed(uint32 id) const { return _book.Armed(id, _nowMs); }
        std::vector<uint32> Ids() const { return _book.Ids(); }
        std::optional<Position> PositionOf(uint32 id) const;
        BossMechanics::MechanicHandle TriggerOf(uint32 id) const;
        BossMechanics::MechanicHandle BlastRingOf(uint32 id) const;

    private:
        struct Entry
        {
            uint32 id = 0;
            Position at;
            TwoRingMineSpec spec;
            BossMechanics::MechanicHandle trigger;
            BossMechanics::MechanicHandle ring;
        };

        void Blast(Creature* owner, uint32 id, bool tripped);
        void Drop(Creature* owner, uint32 id);

        TwoRingMineSpec _spec;
        MineBook _book;
        std::vector<Entry> _mines;
        // Ids the registry's mines reported set off (their OnResolve holds a weak_ptr to this queue).
        std::shared_ptr<std::vector<uint32>> _tripped = std::make_shared<std::vector<uint32>>();
        uint32 _nextId = 1;
        uint32 _nowMs = 0;
    };
}

#endif
