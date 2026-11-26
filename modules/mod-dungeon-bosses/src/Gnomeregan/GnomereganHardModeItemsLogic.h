/*
 * mod-dungeon-bosses, Gnomeregan: the hard mode item effects of Mekgineer Thermaplugg, the Whole Workshop (after the
 * Zul'Farrak precedent ZulFarrakHardModeItemsLogic.h). The ids mirror
 * apps/dbc-tools/source/items/gnomeregan_hard_mode_effects.py and source/npcs/gnomeregan/hard_mode_items.py (the
 * `gnomeregan_items` reservation: spells 214240-214279, creatures 301100-301104). The engine glue is
 * hard_mode_items.cpp. The dungeon build adds its own files to this folder later: every name here carries the item
 * (REACTOR_CORE, BOMB_LAUNCHER, PUNCH_CARD), never a boss mechanic's name.
 *
 * Pure: no engine headers (the generated ItemSpellCopies.h is pure too), so the host test
 * (tests/gnomeregan_hard_mode_items_test.cpp) includes it.
 *
 * Every number a tooltip shows lives in the spell data, not here: Meltdown's percents and pulse, the blast's damage and
 * reach, the bomb's life and fuse, the punches Clearance needs, the card's lock and Clearance's ratings. Only the event
 * rules, the one-roll-per-cast bookkeeping, the card's memory and the bomb's launch spot are script numbers.
 */

#ifndef MOD_DUNGEON_BOSSES_GNOMEREGAN_HARD_MODE_ITEMS_LOGIC_H
#define MOD_DUNGEON_BOSSES_GNOMEREGAN_HARD_MODE_ITEMS_LOGIC_H

#include "ItemSpellCopies.h"
#include <array>
#include <cstdint>

namespace GnomereganHardModeItems
{
    struct IdSlice
    {
        std::uint32_t first;
        std::uint32_t last;

        constexpr bool Contains(std::uint32_t id) const { return id >= first && id <= last; }
    };

    // ids.yaml reservation `gnomeregan_items` (the Gnomeregan gear stage); the copies of the scaled effects mint from
    // the `item_spell_copy` block, never from here.
    IdSlice constexpr kSpellsGnomereganItems{ 214240, 214279 };
    IdSlice constexpr kSpellsDeclared{ 214240, 214247 };
    IdSlice constexpr kCreaturesGnomereganItems{ 301100, 301104 };

    enum GnomereganHardModeItemSpells : std::uint32_t
    {
        SPELL_REACTOR_CORE_MELTDOWN     = 214240,   // Leaking Reactor Core, Use: the 15 sec aura (data only; its
                                                    // damage bonus and pulse grow per tier)
        SPELL_REACTOR_CORE_PULSE        = 214241,   // one pulse (potency, scaled per tier;
                                                    // spell_gnomer_item_meltdown_pulse)
        SPELL_BOMB_LAUNCHER             = 214242,   // Walking Bomb Launcher, Equip: the proc aura
                                                    // (spell_gnomer_item_walking_bomb_launcher)
        SPELL_BOMB_LAUNCHER_MARK        = 214243,   // the mark on the bomb's target (copied per tier so it casts its
                                                    // tier's blast; spell_gnomer_item_walking_bomb)
        SPELL_BOMB_LAUNCHER_BLAST       = 214244,   // the blast (potency, scaled per tier;
                                                    // spell_gnomer_item_walking_bomb_blast)
        SPELL_PUNCH_CARD                = 214245,   // Master Punch Card, Equip: the proc aura
                                                    // (spell_gnomer_item_master_punch_card)
        SPELL_PUNCH_CARD_PUNCHED        = 214246,   // the punches on the wearer (one spell for every tier)
        SPELL_PUNCH_CARD_CLEARANCE      = 214247,   // Clearance: PRISMATIC (ratings, scaled per tier)
        // 214248-214279 spare
    };

    enum GnomereganHardModeItemCreatures : std::uint32_t
    {
        NPC_LAUNCHER_WALKING_BOMB       = 301100,   // Launched Walking Bomb, the Launcher's bomb, look only;
                                                    // 301101-301104 spare
    };

    // Every spell this file declares, a base id or one of its tier copies (the generated table).
    constexpr bool IsItemSpell(std::uint32_t spellId)
    {
        if (kSpellsDeclared.Contains(spellId))
            return true;
        for (ItemSpellCopies::Copy const& copy : ItemSpellCopies::kCopies)
            if (copy.copy == spellId)
                return kSpellsDeclared.Contains(copy.base);
        return false;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // One roll per cast (Systems.md section 5, "A cast rolls once"; the Scholomance Bonechill Blade's guard): an area
    // spell reaches a proc check once per target it hits, all with the same Spell object, so the object's address
    // groups the hits; it never identifies a cast alone, because the allocator reuses a freed Spell's address and
    // triggered spells all carry cast count 0. `moment` pins the cast in time: a delayed (traveling) spell's launch
    // moment (Spell::GetDelayStart, the same for every target it reaches later), else the game time of the update the
    // immediate spell hits in (all its targets land in that one update). A later cast that reuses the address has
    // another moment, so it rolls.
    struct CastStamp
    {
        void const* spell = nullptr;
        std::uint32_t spellId = 0;
        std::uint8_t castCount = 0;
        std::uint64_t moment = 0;
    };

    // The `moment` of a cast: the delayed spell's launch moment when it has one, else the current game time.
    constexpr std::uint64_t CastMoment(std::uint64_t delayStart, std::uint64_t nowMs)
    {
        return delayStart != 0 ? delayStart : nowMs;
    }

    // True when `now` is the cast that already rolled. An event without a spell has a null `spell` and never matches.
    constexpr bool SameCast(CastStamp const& last, CastStamp const& now)
    {
        return now.spell != nullptr && last.spell == now.spell && last.spellId == now.spellId
            && last.castCount == now.castCount && last.moment == now.moment;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Walking Bomb Launcher

    // SpellMgr.h ProcFlags, the events 214242's spell_proc row passes (the host test keeps this header free of
    // SpellMgr.h; the .cpp asserts the values): ranged auto attacks (Auto Shot, Shoot, Throw) and ranged-class
    // abilities.
    std::uint32_t constexpr kRangedHitFlags = 0x40u | 0x100u;

    // What the mark does on a tick. The bomb falls apart when there is nothing to blow up for (the target is dead or
    // gone), nobody to blow it (the wearer is dead or left the map, so the blast has no caster; a dead hunter's bomb
    // not blowing is by design) or no bomb (it timed out or was removed); it blows when it is within the fuse of its
    // target; else it keeps running (it follows the target, MoveFollow, and stops at its own reach, inside the fuse).
    enum class BombStep : std::uint8_t
    {
        Walk,
        Blast,
        FallApart,
    };

    constexpr BombStep StepBomb(bool targetAlive, bool wearerHere, bool bombHere, bool withinFuse)
    {
        if (!targetAlive || !wearerHere || !bombHere)
            return BombStep::FallApart;
        return withinFuse ? BombStep::Blast : BombStep::Walk;
    }

    // The bomb's launch spot: this far from the wearer, toward the target (look only). From there it runs at 8 yd per
    // sec (its speed_run), so a target at 40 yd is reached in about 5 sec, inside the 8 sec mark.
    float constexpr kBombLaunchDistance = 2.0f;
    // The bomb's own despawn timer is the mark's duration plus this tail: the mark sends it away, the timer only
    // catches a mark that never ended on its map (the target left it). The Launcher's internal cooldown (10 sec, the
    // spell_proc row) outlasts both, so a wearer has one bomb at most.
    std::uint32_t constexpr kBombTailMs = 1000;

    // ----------------------------------------------------------------------------------------------------------------
    // Master Punch Card

    // SpellMgr.h ProcFlags, the cast phase events 214245's spell_proc row passes: melee, ranged, magic and none class
    // spells, helpful or harmful (no auto attack).
    std::uint32_t constexpr kOwnCastFlags = 0x10u | 0x100u | 0x400u | 0x1000u | 0x4000u | 0x10000u;

    // A cast that can punch: the wearer cast it themselves, from the spell book or an action bar. Not triggered (the
    // cast phase event already skips those), not an item's Use (trinkets, potions, the Card's neighbors), not an auto
    // repeat (Auto Shot, Shoot, Throw: an auto attack in all but name), not passive.
    constexpr bool CountsAsPunch(bool triggered, bool fromItem, bool autoRepeat, bool passive)
    {
        return !triggered && !fromItem && !autoRepeat && !passive;
    }

    // The card's memory: which spells (by first rank) punched it since it last cleared. The punch count Clearance
    // needs comes from the data (effect 1's amount); the card holds at most this many.
    std::uint32_t constexpr kMaxPunches = 8;

    struct PunchCard
    {
        std::array<std::uint32_t, kMaxPunches> spells{};
        std::uint32_t count = 0;
    };

    constexpr bool IsPunched(PunchCard const& card, std::uint32_t firstRankId)
    {
        for (std::uint32_t i = 0; i < card.count && i < kMaxPunches; ++i)
            if (card.spells[i] == firstRankId)
                return true;
        return false;
    }

    constexpr void ClearCard(PunchCard& card)
    {
        card = PunchCard{};
    }

    // The visible stacks are the card's face: fewer stacks than punches (the wearer died, the stacks were canceled)
    // means the card was cleared, so the memory clears too.
    constexpr void SyncCard(PunchCard& card, std::uint32_t visibleStacks)
    {
        if (visibleStacks < card.count)
            ClearCard(card);
    }

    enum class PunchResult : std::uint8_t
    {
        None,       // nothing happens: locked, already punched, or no data
        Punched,    // one more punch (a stack)
        Clearance,  // the last punch: the card clears and Clearance starts
    };

    // A punch by `firstRankId` at `nowMs`. The card is locked until `readyAtMs` (Clearance's lock); a spell that
    // already punched it does nothing; the punch that reaches `needed` (capped at kMaxPunches) clears the card.
    constexpr PunchResult Punch(PunchCard& card, std::uint32_t firstRankId, std::uint32_t needed, std::uint64_t nowMs,
        std::uint64_t readyAtMs)
    {
        if (needed == 0 || firstRankId == 0 || nowMs < readyAtMs || IsPunched(card, firstRankId))
            return PunchResult::None;
        std::uint32_t const full = needed < kMaxPunches ? needed : kMaxPunches;
        card.spells[card.count] = firstRankId;
        ++card.count;
        if (card.count >= full)
        {
            ClearCard(card);
            return PunchResult::Clearance;
        }
        return PunchResult::Punched;
    }
}

#endif
