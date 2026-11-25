/*
 * mod-dungeon-bosses, Ragefire Chasm: the hard mode item effects of Taragaman the Hungerer, Starving (after the Scarlet
 * Monastery precedent ScarletMonasteryHardModeItemsLogic.h). The ids mirror
 * apps/dbc-tools/source/items/ragefire_chasm_hard_mode_effects.py (the `ragefire_chasm_items` reservation: spells
 * 213500-213539). The engine glue is hard_mode_items.cpp.
 *
 * Pure: no engine headers (the generated ItemSpellCopies.h is pure too), so the host test
 * (tests/ragefire_chasm_hard_mode_items_test.cpp) includes it.
 *
 * Every number a tooltip shows lives in the spell data, not here: the bite's and the spin's damage are potency, the
 * Heart's health threshold and share are 213503's amounts, the Felstorm's reach is 213507's radius; the chances and
 * internal cooldowns are spell_proc rows. Only when the Fang leaps, how the leap's landing is watched and the
 * one-roll-per-cast bookkeeping are script numbers.
 */

#ifndef MOD_DUNGEON_BOSSES_RAGEFIRE_CHASM_HARD_MODE_ITEMS_LOGIC_H
#define MOD_DUNGEON_BOSSES_RAGEFIRE_CHASM_HARD_MODE_ITEMS_LOGIC_H

#include "ItemSpellCopies.h"
#include <cstdint>

namespace RagefireChasmHardModeItems
{
    struct IdSlice
    {
        std::uint32_t first;
        std::uint32_t last;

        constexpr bool Contains(std::uint32_t id) const { return id >= first && id <= last; }
    };

    // ids.yaml reservation `ragefire_chasm_items` (the Ragefire Chasm gear stage); the copies of the scaled effects
    // mint from the `item_spell_copy` block, never from here.
    IdSlice constexpr kSpellsRagefireChasmItems{ 213500, 213539 };
    IdSlice constexpr kSpellsDeclared{ 213500, 213507 };

    // A Ragefire Chasm hard mode item spell: a declared one (the reservation) or one of their tier copies (minted in
    // the item spell copy block, so only ItemSpellCopies knows their base). The bite and the spin are melee class, so
    // the Haunted set's Haunting Mark must skip them (the Scarlet Monastery gear review's m2).
    constexpr bool IsItemSpell(std::uint32_t id)
    {
        if (kSpellsRagefireChasmItems.Contains(id))
            return true;
        for (ItemSpellCopies::Copy const& copy : ItemSpellCopies::kCopies)
            if (copy.copy == id)
                return kSpellsRagefireChasmItems.Contains(copy.base);
        return false;
    }

    enum RagefireChasmHardModeItemSpells : std::uint32_t
    {
        SPELL_TARAGAMANS_FANG               = 213500,   // Taragaman's Fang, Use: the leap (spell_rfc_taragamans_fang)
        SPELL_HUNGERING_BITE                = 213501,   // the bite (potency, scaled per tier; spell_rfc_hungering_bite)
        SPELL_FEED                          = 213502,   // the heal for the damage dealt (one spell for every tier)
        SPELL_HEART_OF_THE_STARVING         = 213503,   // Heart of the Starving, Equip: the heal proc aura
                                                        // (spell_rfc_heart_of_the_starving; its share grows per tier)
        SPELL_BLOODWARD                     = 213504,   // the absorb on the healed target (one spell for every tier)
        SPELL_FELSTORM_GREATBLADE           = 213505,   // Felstorm Greatblade, Equip: PROC_TRIGGER_SPELL into 213506
                                                        // (spell_rfc_one_roll_per_cast)
        SPELL_FELSTORM                      = 213506,   // the 3 sec spin on the wearer (data only)
        SPELL_FELSTORM_SPIN                 = 213507,   // one second of it (potency, scaled per tier; data only)
        // 213508-213539 spare
    };

    // Taragaman's Fang: the leap moves the wearer only from outside melee range. Spell::CheckCast paths to the victim's
    // center and PathGenerator::ShortenPathUntilDist leaves that path whole when it starts inside the victim's combat
    // reach, so a leap from there would drag the wearer to the center (under a dragon, into Ragnaros' lava). From
    // outside it always ends at the victim's reach, on the wearer's side.
    constexpr bool LeapMoves(bool inMeleeRange, float distance, float victimReach)
    {
        return !inMeleeRange && distance > victimReach;
    }

    // The DUMMY hit arrives at distance / 42 (the spell's Speed), but the leap itself runs slower:
    // MoveSplineInit::Launch caps a ground spline at kLeapSplineSpeed (more only for a wearer whose run speed times 4
    // is higher). So the bite waits for the charge to end, looking every kLeapPollMs for at most kLeapWaitMs after the
    // hit (the longest path Spell::CheckCast accepts is 1.5 times the range plus the victim's reach: 2.1 sec at a reach
    // of 20 yd).
    float constexpr kLeapSplineSpeed = 28.0f;
    std::uint32_t constexpr kLeapPollMs = 50;
    std::uint32_t constexpr kLeapWaitMs = 2500;
    // The bite reaches this far past both combat reaches when the leap has ended, so a target that walked on during it
    // is still bitten and one the leap never got to (the charge was refused or broken off) is not.
    float constexpr kBiteReach = 10.0f;

    // The bite waits while the leap is still under way and the watch has not run out.
    constexpr bool WaitForLanding(bool charging, std::uint32_t waitedMs)
    {
        return charging && waitedMs < kLeapWaitMs;
    }

    // The bite's heal: the damage dealt (after armor, absorbs and the crit), never more than the health the victim had
    // left (the engine's own health leech leaves overkill out too).
    constexpr std::int32_t BiteHeal(std::int32_t damage, std::uint32_t victimHealthBefore)
    {
        if (damage <= 0)
            return 0;
        return std::uint32_t(damage) < victimHealthBefore ? damage : std::int32_t(victimHealthBefore);
    }

    // Heart of the Starving: the healed unit was strictly below `thresholdPct` percent of its maximum health before the
    // heal (the heal has landed when the proc runs: health now minus the effective heal). A unit at 0 before the heal
    // (dead) never qualifies.
    constexpr bool BelowThresholdBeforeHeal(std::uint32_t health, std::uint32_t effectiveHeal, std::uint32_t maxHealth,
        std::int32_t thresholdPct)
    {
        if (maxHealth == 0 || thresholdPct <= 0 || effectiveHeal >= health)
            return false;
        std::uint64_t const before = std::uint64_t(health - effectiveHeal);
        return before * 100u < std::uint64_t(maxHealth) * std::uint64_t(thresholdPct);
    }

    // Bloodward: `pct` percent of the heal's amount.
    constexpr std::int32_t BloodwardAmount(std::uint32_t heal, std::int32_t pct)
    {
        if (pct <= 0)
            return 0;
        std::uint64_t const amount = std::uint64_t(heal) * std::uint64_t(pct) / 100u;
        return amount < 0x7fffffffu ? std::int32_t(amount) : 0x7fffffff;
    }

    // Two healers' Bloodwards do not stack (one spell, another caster), so the newer one takes the older one's place:
    // it does so only when it absorbs at least what the older one, whoever cast it, has left.
    constexpr bool BloodwardReplaces(std::int32_t amount, std::int32_t remaining)
    {
        return amount >= remaining;
    }

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

    // True when `now` is the cast that already rolled (so it does not roll again). An event without a spell (an auto
    // attack) has a null `spell` and always rolls.
    constexpr bool SameCast(CastStamp const& last, CastStamp const& now)
    {
        return now.spell != nullptr && last.spell == now.spell && last.spellId == now.spellId
            && last.castCount == now.castCount && last.moment == now.moment;
    }
}

#endif
