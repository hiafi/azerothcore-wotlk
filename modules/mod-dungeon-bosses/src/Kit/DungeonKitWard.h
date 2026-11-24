/*
 * mod-dungeon-bosses, the shared dungeon kit (Scarlet Monastery WP-KT-SM, handoff section 3.11 #5): Ward of the
 * Living (L38: a boss buff tied to living adds; Thalnos's Blood Pact, the Librarian's Reader's Ward, Fairbanks's
 * Inquisitor's Ward). The pure rule is DungeonKitWingLogic.h (WardRule).
 *
 * WardOfTheLiving, owned by the boss AI: the adds it counts are the ones linked by hand (Link, from the boss's
 * JustSummoned or the add's own pull) plus, with `addEntries`, every creature of those entries within searchYd of the
 * boss (by entry, never by position: RB-3). Every checkMs it counts the living ones and sets the boss's `aura` to one
 * stack per living add, held at the cap's count (WardRule::Stacks): an aura of -pctPerAdd % damage taken per stack
 * carries the reduction itself. With auraCarriesReduction = false the aura is a look only and the boss's DamageTaken
 * calls Mitigate. onLink / onUnlink run as an add joins or leaves the count (the tether look: capture guids only).
 *
 *     DungeonKit::WardOfTheLiving _ward;
 *     void JustEngagedWith(Unit*) override { _ward.Start(me, BloodPactSpec()); }
 *     void JustSummoned(Creature* s) override { BossAI::JustSummoned(s); if (IsRisen(s)) _ward.Link(me, s); }
 *     void UpdateAI(uint32 diff) override { _ward.Update(me, diff); ... }
 *     void Reset() / JustDied() / EnterEvadeMode(): _ward.Stop(me);
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_WARD_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_WARD_H

#include "DungeonKitWingLogic.h"
#include "ObjectGuid.h"
#include <functional>
#include <vector>

class Creature;

namespace DungeonKit
{
    struct WardSpec
    {
        uint32 aura = 0;                        // the stacking ward on the boss (0: no aura, Mitigate only)
        float pctPerAdd = 20.f;
        float capPct = 80.f;                    // never above 95 (WardRule::Cap)
        bool auraCarriesReduction = true;       // false: Mitigate does the reduction
        std::vector<uint32> addEntries;         // counted when within searchYd of the boss (empty: linked adds only)
        float searchYd = 100.f;
        uint32 checkMs = 500;
        std::function<void(Creature* boss, Creature* add)> onLink;
        std::function<void(Creature* boss, ObjectGuid add)> onUnlink;    // the add may be gone already
        char const* dungeon = "kit";            // LogMechanic: "<dungeon> <boss> ward living=N stacks=N"
        char const* boss = "ward";
    };

    class WardOfTheLiving
    {
    public:
        // Starts counting now (one count at once).
        void Start(Creature* boss, WardSpec spec);
        void Link(Creature* boss, Creature* add);
        void Update(Creature* boss, uint32 diff);
        // Removes the aura and forgets the adds (onUnlink for each still linked).
        void Stop(Creature* boss);

        // With auraCarriesReduction = false, from the boss's DamageTaken.
        void Mitigate(uint32& damage) const;

        bool Active() const { return _active; }
        uint32 Living() const { return static_cast<uint32>(_linked.size()); }
        float ReductionPct() const { return _rule.ReductionPct(Living()); }

    private:
        void Count(Creature* boss);

        WardSpec _spec;
        WardRule _rule;
        std::vector<ObjectGuid> _manual;        // linked by hand (kept until dead or gone)
        std::vector<ObjectGuid> _linked;        // counted living at the last check
        uint32 _checkMs = 0;
        uint32 _stacks = 0;
        bool _active = false;
    };
}

#endif
