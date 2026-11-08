/*
 * mod-dungeon-bosses, Shadowfang Keep: Arugal's hard mode "Face Him Alone" (WP-S10), the pure, host-testable part.
 * Build spec: SK 1491-1511 and the gossip line SK 1524 / 1645 (docs/dungeons/shadowfang-keep-rework.md); handoff
 * section 3.6 row S10.
 *
 * The hard mode is a choice, not a mechanic: on heroic (empowered heroic runs on the heroic difficulty too) the lair
 * prisoner's gossip offers "Stay behind. We will face Arugal alone." Choosing it lights DATA_HARD_MODE (the instance
 * saves it; only an instance reset clears it), the prisoner says its line 7 and leaves (LairPrisoner.h), and Arugal
 * fights on his heroic numbers with no wards (S9's PlaceWard skips every ward kind while the flag is lit, the
 * Moonrise ward included). The instance adds LOOT_MODE_HARD_MODE_1 to Arugal while the flag is lit, so his kill rolls
 * group 2 of his heroic lootid (WP-L), and his DONE with the flag lit sets BOSS_FACE_HIM_ALONE (the kill flag).
 *
 * This header holds:
 *   - the choice rule (`CanChoose`): heroic only, once, and only while his encounter is open (not fighting, not dead);
 *   - the gossip's texts and ids;
 *   - the loot ids the instance and WP-L agree on (apps/dbc-tools lib/test_shadowfang_keep_face_him_alone.py checks
 *     them against the declarations) and the loot-mode bit arithmetic;
 *   - the build spec's hard mode budget on Arugal's real numbers (ArugalLogic.h), so a retune that breaks SK's
 *     arithmetic (the seep at the moon, the tank's Void Bolt budget, the moon window against the burn) fails the host
 *     test.
 *
 * Spells: none. The slice 206085-206089 (the last five of Arugal's) stays reserved for this WP and unused: the flag
 * needs no aura (the prisoner's line and its leaving are the cue, the missing wards the effect), and apps/dbc-tools
 * source/npcs/shadowfang_keep/face_him_alone.py declares nothing.
 */

#ifndef MOD_DUNGEON_BOSSES_SFK_FACE_HIM_ALONE_LOGIC_H
#define MOD_DUNGEON_BOSSES_SFK_FACE_HIM_ALONE_LOGIC_H

#include "ArugalLogic.h"
#include "ShadowfangKeepRework.h"
#include <chrono>
#include <cstdint>

namespace FaceHimAlone
{
    using Ms = std::chrono::milliseconds;

    // Reserved for this WP, unused (see the header comment).
    inline constexpr ShadowfangKeepRework::IdSlice kSlice = ShadowfangKeepRework::kSpellsFaceHimAlone;

    // ----------------------------------------------------------------------------------------------------------------
    // The gossip: a C++ option on the prisoner's menu (SfkLairPrisoner::SetGossipHooks), no gossip_menu_option rows
    // ----------------------------------------------------------------------------------------------------------------
    char constexpr kOptionText[] = "Stay behind. We will face Arugal alone.";       // SK 1524
    char constexpr kConfirmText[] = "Face Archmage Arugal without the prisoner's wards? The choice holds until the "
        "instance resets.";
    // The option's sender and action: GOSSIP_SENDER_MAIN (1) and GOSSIP_ACTION_INFO_DEF (1000) + 22 (DATA_HARD_MODE),
    // pinned against the engine's values in face_him_alone.cpp. The prisoner's menu has no DB option to collide with.
    std::uint32_t constexpr kOptionSender = 1;
    std::uint32_t constexpr kOptionAction = 1000 + ShadowfangKeepRework::DATA_HARD_MODE;

    // ----------------------------------------------------------------------------------------------------------------
    // The loot (WP-L: source/items/shadowfang_keep_loot.py; the instance's ApplyHardModeLoot)
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kArugalHeroicEntry = 310051;    // WP-H: heroic_ids.lock; its lootid is its own entry
    std::uint32_t constexpr kHardModeLootGroup = 2;         // group 2 of 310051: the three hard mode items
    std::uint16_t constexpr kLootModeDefault = 1;           // LOOT_MODE_DEFAULT (pinned in face_him_alone.cpp)
    std::uint16_t constexpr kLootModeHardMode = 2;          // LOOT_MODE_HARD_MODE_1 (pinned in face_him_alone.cpp)

    // The loot mode his kill rolls with: the default bit, plus the hard mode bit while the flag is lit and he is not
    // DONE yet (the instance's ApplyHardModeLoot; Unit::Kill fills the loot before JustDied and the DONE state).
    constexpr std::uint16_t KillLootMode(bool hardMode, bool arugalDone)
    {
        return hardMode && !arugalDone ? std::uint16_t(kLootModeDefault | kLootModeHardMode) : kLootModeDefault;
    }

    // A loot row of `rowLootMode` can roll for a creature of `creatureLootMode` (LootGroup::Roll's bit test).
    constexpr bool RowRolls(std::uint16_t rowLootMode, std::uint16_t creatureLootMode)
    {
        return (rowLootMode & creatureLootMode) != 0;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The choice
    // ----------------------------------------------------------------------------------------------------------------

    // Arugal's encounter state, with the engine's EncounterState values (pinned in face_him_alone.cpp).
    enum class Encounter : std::uint8_t
    {
        NotStarted  = 0,
        InProgress  = 1,
        Fail        = 2,
        Done        = 3,
        Special     = 4,
        ToBeDecided = 5,
    };

    struct ChoiceInputs
    {
        bool instance = false;          // an SFK instance script runs on the map
        bool heroic = false;            // heroic difficulty (empowered heroic included)
        bool lairPrisoner = false;      // the gossip is the lair prisoner's (300513 / 300514)
        bool prisonerWaiting = false;   // it waits by the lair door (its gossip flag is on: not stepping in, posted or
                                        // leaving)
        bool chosen = false;            // DATA_HARD_MODE is lit already
        Encounter arugal = Encounter::NotStarted;
        bool arugalFighting = false;    // Arugal found and in combat or evading
        bool playerAlive = true;
    };

    enum class Refusal : std::uint8_t
    {
        None,
        NoInstance,
        NotLairPrisoner,
        NotHeroic,
        AlreadyChosen,
        ArugalDead,
        ArugalFighting,
        PrisonerBusy,
        PlayerDead,
    };

    // The rule (SK 1494-1499, and the orchestrator's: once, and only before the fight). His encounter is open while it
    // is NOT_STARTED, FAIL or TO_BE_DECIDED (a fresh instance). A wipe puts it back to NOT_STARTED and the prisoner
    // back by the door, so the choice stays open before the next pull (the Deadmines keg's rule). Once chosen it is
    // never offered again; nothing but an instance reset (or `.sfktest instance hardmode 0`) clears it.
    constexpr Refusal CanChoose(ChoiceInputs const& in)
    {
        if (!in.instance)
            return Refusal::NoInstance;
        if (!in.lairPrisoner)
            return Refusal::NotLairPrisoner;
        if (!in.heroic)
            return Refusal::NotHeroic;
        if (in.chosen)
            return Refusal::AlreadyChosen;
        if (in.arugal == Encounter::Done)
            return Refusal::ArugalDead;
        if (in.arugalFighting || in.arugal == Encounter::InProgress || in.arugal == Encounter::Special)
            return Refusal::ArugalFighting;
        if (!in.prisonerWaiting)
            return Refusal::PrisonerBusy;
        if (!in.playerAlive)
            return Refusal::PlayerDead;
        return Refusal::None;
    }

    // The option shows exactly when it can be chosen (the select checks again: a stale menu does nothing).
    constexpr bool Offered(ChoiceInputs const& in)
    {
        return CanChoose(in) == Refusal::None;
    }

    // What the player is told when a stale menu's select is refused (empty: nothing).
    constexpr char const* Notice(Refusal r)
    {
        switch (r)
        {
            case Refusal::AlreadyChosen:
                return "You have already chosen to face Arugal alone.";
            case Refusal::ArugalDead:
                return "Arugal is already dead.";
            case Refusal::ArugalFighting:
                return "Not while Arugal is fighting.";
            case Refusal::NotHeroic:
                return "Only on heroic difficulty.";
            default:
                return "";
        }
    }

    constexpr char const* RefusalName(Refusal r)
    {
        switch (r)
        {
            case Refusal::None:
                return "none";
            case Refusal::NoInstance:
                return "no-instance";
            case Refusal::NotLairPrisoner:
                return "not-lair-prisoner";
            case Refusal::NotHeroic:
                return "not-heroic";
            case Refusal::AlreadyChosen:
                return "already-chosen";
            case Refusal::ArugalDead:
                return "arugal-dead";
            case Refusal::ArugalFighting:
                return "arugal-fighting";
            case Refusal::PrisonerBusy:
                return "prisoner-busy";
            case Refusal::PlayerDead:
                return "player-dead";
        }
        return "?";
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The build spec's hard mode budget (SK 1500-1509) on Arugal's heroic numbers (ArugalLogic.h). Every heroic number
    // holds on hard mode (Moonrise's +2 per second included); the only change is that no ward takes 10 stacks off.
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kArugalHeroicHealth = 405840;   // shadowfang_keep.py's heroic override (handoff s7 #7)

    // Health left when the moon rises (30%).
    constexpr std::uint32_t MoonHealth()
    {
        return static_cast<std::uint32_t>(static_cast<std::uint64_t>(kArugalHeroicHealth)
            * static_cast<std::uint64_t>(Arugal::kMoonrisePct) / 100u);
    }

    // Seconds the group needs for the first 70%, and for the burn, at `groupDps`.
    constexpr float SecondsToMoon(float groupDps)
    {
        return groupDps > 0.f ? static_cast<float>(kArugalHeroicHealth - MoonHealth()) / groupDps : 0.f;
    }

    constexpr float BurnSeconds(float groupDps)
    {
        return groupDps > 0.f ? static_cast<float>(MoonHealth()) / groupDps : 0.f;
    }

    // The seep's stacks after `elapsed` of the fight before the moon (+1 per whole 3 s; no ward removes any).
    constexpr std::uint32_t SeepBeforeMoon(Ms elapsed)
    {
        return elapsed.count() <= 0 ? 0u
            : static_cast<std::uint32_t>(elapsed.count() / Arugal::kSeepEvery.count()) * Arugal::kSeepStacks;
    }

    // The tank's budget: how many Void Bolts may land before the moon so the tank enters it at or under `enterCap`.
    constexpr std::uint32_t LandedVoidBoltBudget(std::uint32_t enterCap, std::uint32_t seepAtMoon)
    {
        return enterCap <= seepAtMoon ? 0u
            : (enterCap - seepAtMoon) / static_cast<std::uint32_t>(Arugal::kVoidBoltStacks);
    }

    // Seconds a player entering the moon at `stacks` has before turning (+2 every second).
    constexpr float MoonWindow(std::uint32_t stacks)
    {
        return Arugal::SecondsToTurn(stacks, Arugal::kMoonSeepStacks, Arugal::kMoonSeepEvery);
    }
}

#endif
