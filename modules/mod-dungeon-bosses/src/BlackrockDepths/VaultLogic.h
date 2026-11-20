/*
 * mod-dungeon-bosses, Blackrock Depths D9:
 * The Vault: Watchman Doomgrip (9476) and the four Vault Sentinels (300793), "Security Breach": the pure,
 * host-testable part (no engine headers). Build spec SP 640-687 (docs/dungeons/blackrock-depths-2-shadowforge-city.md,
 * "The Vault", rulings 42-45, 88), handoff section 3.4 row D9, 3.5 row D9, 3.6, 3.7 "The Vault", 3.8, 7 #17. Tested by
 * tests/brd_vault_test.cpp.
 *
 *   Spells         the WP's ids, inside kSpellsVault (211090-211119), declared in apps/dbc-tools
 *                  source/npcs/blackrock_depths/vault.py
 *   Tuning         NH<> constants: one number per difficulty, straight from the build spec (percents of the reference
 *                  row: N level 54, H level 60)
 *   Sentinels      VA2: the four wake one at a time (5 s, then every 20 s, heroic 15 s); with nothing awake left the
 *                  next one wakes at once
 *   Fields         VA3: 6 yd round each awake sentinel; heroic +1 yd every 10 s it lives, 9 yd at most
 *   Link           VA4: Doomgrip takes 25% less damage per awake sentinel, 75% at most
 *   Sweep          VA5: a 90 degree, 10 yd cone in front of him, locked at the warning's start (the tank too)
 *   Draught        VA7: at 60% and 30%, once each
 *   Loot clock     VA8: the seals (BlackrockDepthsRework.h kVaultSeal*) and what the Secret Safe holds at the end
 *   Lockdown       VA1: the room's doorway [navmesh estimate] and the corridor strip nobody may stand in
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_VAULT_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_VAULT_LOGIC_H

#include "BlackrockDepthsRework.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace BrdVault
{
    using BlackrockDepthsRework::VaultSafe;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsVault;

    enum VaultSpells : std::uint32_t
    {
        SPELL_VA_LOCKDOWN           = kSpellSlice.first + 0,    // 211090 VA1 the force field (a state on a stalker)
        SPELL_VA_SENTINEL_WAKES     = kSpellSlice.first + 1,    // 211091 VA2 the wake look (3 s, on the sentinel)
        SPELL_VA_FIELD_6            = kSpellSlice.first + 2,    // 211092 VA3 the field disc, 6 yd rung (on a stalker)
        SPELL_VA_FIELD_7            = kSpellSlice.first + 3,    // 211093 VA3 7 yd rung (heroic growth)
        SPELL_VA_FIELD_8            = kSpellSlice.first + 4,    // 211094 VA3 8 yd rung
        SPELL_VA_FIELD_9            = kSpellSlice.first + 5,    // 211095 VA3 9 yd rung
        SPELL_VA_FIELD_HIT          = kSpellSlice.first + 6,    // 211096 VA3 a field's tick (resolve copy, Arcane)
        SPELL_VA_LINK_BEAM          = kSpellSlice.first + 7,    // 211097 VA4 the beam (a channel, sentinel to Doomgrip)
        SPELL_VA_SECURITY_LINK      = kSpellSlice.first + 8,    // 211098 VA4 -25% damage taken a stack, 3 stacks
        SPELL_VA_SWEEP_CAST         = kSpellSlice.first + 9,    // 211099 VA5 the 2 s bar (Physical, not kickable)
        SPELL_VA_SWEEP_HIT          = kSpellSlice.first + 10,   // 211100 VA5 the cone's hit (resolve copy, Physical)
        SPELL_VA_SUNDER_ARMOR       = kSpellSlice.first + 11,   // 211101 VA6 -5% armor a stack, 5 stacks, 30 s
        SPELL_VA_WATCHMANS_DRAUGHT  = kSpellSlice.first + 12,   // 211102 VA7 heals 5%, +20% damage 15 s (Magic)
        SPELL_VA_STONED             = kSpellSlice.first + 13,   // 211103 the dormant look (Stoned 10255's visual)
        // 211104-211119 spare
    };
    static_assert(SPELL_VA_STONED <= kSpellSlice.last, "the D9 spells must stay in their slice");
    static_assert(SPELL_VA_STONED == BlackrockDepthsRework::kSpellVaultStoned, "the instance's freeze casts the same");

    // R-2-A MA-2: the dormant state is the sentinel's own (not selectable, set by the instance's freeze and the
    // script's Dormant, cleared only by its Wake), never an aura. Stock Stoned 10255 carries EffectMechanic FREEZE,
    // which the sentinel's immunity set 1972 drops, so its aura never lands; the look is now the copy above
    // (NO_IMMUNITIES, no mechanic) and is look only.
    //
    // Not awake, the Vault running, not stone and not walking home: the alarm woke it (stock), put it back to stone.
    constexpr bool SentinelNeedsStone(bool vaultInProgress, bool stone, bool evading)
    {
        return vaultInProgress && !stone && !evading;
    }

    // Awake but stone again: the instance froze it back (a reset); its field and beam go.
    constexpr bool SentinelReStoned(bool awake, bool stone)
    {
        return awake && stone;
    }

    // creature_text groups of 9476 (SP "Text"; kTextRanges 0-5 in BlackrockDepthsRework.h, 0 stock).
    enum DoomgripTexts : std::uint8_t
    {
        YELL_VA_ALARM           = 0,    // stock "What are you doing?  Intruders!!" (the lockdown, at his pull)
        EMOTE_VA_SENTINEL       = 1,    // "A Vault Sentinel grinds to life!" (boss emote, 41)
        EMOTE_VA_SEAL_BAG       = 2,    // 75 s
        EMOTE_VA_SEAL_GEAR      = 3,    // 90 s
        EMOTE_VA_SEAL_LAST_BAG  = 4,    // 110 s
        YELL_VA_DEATH           = 5,    // "The vault... is breached..."
    };

    // Registry tags (the failure ledger and the playtest greps key on them).
    enum VaultTags : std::uint32_t
    {
        TAG_VA_FIELD    = 1,    // VA3
        TAG_VA_SWEEP    = 2,    // VA5
    };

    // AI actions and data between the three scripts (the Secret Safe's controller, the sentinels, Doomgrip).
    enum VaultActions : std::int32_t
    {
        ACTION_SENTINEL_WAKE    = 1,    // the controller wakes one sentinel
        ACTION_SENTINEL_DORMANT = 2,    // the controller puts it (back) to stone
    };
    inline constexpr std::uint32_t DATA_SAFE_DOOMGRIP_GEAR = 1;    // GameObjectAI SetData on the Safe: his gear item

    // The instance's saved field for Doomgrip's gear item (F-1a: DATA_VAULT_DOOMGRIP_ITEM, saved while the Vault is
    // DONE), so the Safe still avoids it after a reload.
    inline constexpr std::uint32_t kDataVaultDoomgripItem = BlackrockDepthsRework::DATA_VAULT_DOOMGRIP_ITEM;
    static_assert(kDataVaultDoomgripItem == 67, "the instance's data id");

    // ----------------------------------------------------------------------------------------------------------------
    // VA2 The sentinels wake
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::size_t kSentinelCount = 4;
    inline constexpr std::uint32_t kWakeFirstMs = 5000;
    inline constexpr NH<std::uint32_t> kWakeEveryMs{ 20000, 15000 };
    inline constexpr float kAlarmZoneYd = 45.f;         // the room and its doorway: everyone who opened the coffer
    inline constexpr std::uint32_t kWakeLookMs = 3000;

    // When the sentinel woken `index`-th (0-based) is due, from the alarm: 5, 25, 45, 65 s (heroic 5, 20, 35, 50 s).
    constexpr std::uint32_t WakeDueMs(std::size_t index, bool heroic)
    {
        return kWakeFirstMs + static_cast<std::uint32_t>(index) * kWakeEveryMs(heroic);
    }

    // The next wake happens now: its time has come, or nothing awake is left to fight (Doomgrip dead and every woken
    // sentinel dead) once the first wake is due. Never past the fourth.
    constexpr bool WakeNow(std::size_t woken, std::uint64_t clockMs, bool heroic, bool anythingAwakeAlive)
    {
        if (woken >= kSentinelCount)
            return false;
        if (clockMs >= WakeDueMs(woken, heroic))
            return true;
        return !anythingAwakeAlive && clockMs >= kWakeFirstMs;
    }

    // The wake order: a permutation of the four, from a roll (each attempt its own).
    constexpr std::array<std::uint8_t, kSentinelCount> WakeOrder(std::uint32_t roll)
    {
        std::array<std::uint8_t, kSentinelCount> order{ { 0, 1, 2, 3 } };
        for (std::size_t i = kSentinelCount - 1; i > 0; --i)
        {
            std::size_t const j = roll % static_cast<std::uint32_t>(i + 1);
            roll /= static_cast<std::uint32_t>(i + 1);
            std::uint8_t const t = order[i];
            order[i] = order[j];
            order[j] = t;
        }
        return order;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VA3 Security field
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr NH<float> kFieldPct{ 5.f, 8.f };      // a second, the tank on its own row (ruling 88)
    inline constexpr std::uint32_t kFieldTickMs = 1000;
    inline constexpr std::uint32_t kFieldWarnMs = 1500;     // the wake look plays; then the first tick
    inline constexpr std::uint32_t kFieldLifeMs = 600000;   // the sentinel's life (cancelled at its death)
    inline constexpr float kFieldBaseYd = 6.f;
    inline constexpr float kFieldMaxYd = 9.f;
    inline constexpr std::uint32_t kFieldGrowEveryMs = 10000;   // heroic: +1 yd every 10 s the sentinel lives
    inline constexpr std::uint32_t kFieldOverlapMs = 1000;      // a grown field's warning; the old one ticks meanwhile
    // > 0 turns the field into a donut with a safe hole this wide round the sentinel (designer question 1: melee on a
    // sentinel otherwise stands in its field). 0 = the spec's circle.
    inline constexpr float kFieldHoleYd = 0.f;
    static_assert(kFieldHoleYd >= 0.f && kFieldHoleYd < kFieldBaseYd, "the hole stays inside the field");

    constexpr float FieldRadius(bool heroic, std::uint64_t aliveMs)
    {
        if (!heroic)
            return kFieldBaseYd;
        return std::min(kFieldMaxYd, kFieldBaseYd + static_cast<float>(aliveMs / kFieldGrowEveryMs));
    }

    // The field disc's look: the smallest minted rung at or above the radius (9 is the top; _visuals.py
    // security_field_rung).
    constexpr std::uint32_t FieldLookFor(float radius)
    {
        if (radius <= 6.f)
            return SPELL_VA_FIELD_6;
        if (radius <= 7.f)
            return SPELL_VA_FIELD_7;
        if (radius <= 8.f)
            return SPELL_VA_FIELD_8;
        return SPELL_VA_FIELD_9;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VA4 Security Link
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kLinkPctPerSentinel = 25;
    inline constexpr std::uint8_t kLinkMaxStacks = 3;
    inline constexpr std::uint32_t kLinkCheckMs = 500;
    inline constexpr std::uint32_t kBeamCheckMs = 2000;

    // R-1-B B1: a sentinel never moves. Fear is in its immunity set (1972); a grip or a knockback (effects) is undone:
    // once it has landed it is put back on its post (checked this often, past this slack).
    inline constexpr std::uint32_t kPostCheckMs = 500;
    inline constexpr float kPostSlackYd = 1.f;
    constexpr bool OffPost(float distFromPostYd)
    {
        return distFromPostYd > kPostSlackYd;
    }

    constexpr std::uint8_t LinkStacks(std::uint32_t awakeSentinels)
    {
        return static_cast<std::uint8_t>(std::min<std::uint32_t>(awakeSentinels, kLinkMaxStacks));
    }

    constexpr std::uint32_t LinkTakenReductionPct(std::uint8_t stacks)
    {
        return kLinkPctPerSentinel * std::min(stacks, kLinkMaxStacks);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VA5 Intruder Sweep
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kSweepFirstMs = 8000;
    inline constexpr NH<std::uint32_t> kSweepEveryMs{ 15000, 12000 };
    inline constexpr std::uint32_t kSweepWarnMs = 2000;
    inline constexpr float kSweepAngleDeg = 90.f;
    inline constexpr float kSweepLengthYd = 10.f;
    inline constexpr NH<float> kSweepPct{ 25.f, 40.f };

    // The start of the next beat on a fixed cadence (start to start): never earlier than 1 ms from now.
    constexpr std::uint64_t NextDue(std::uint64_t plannedMs, std::uint32_t everyMs, std::uint64_t nowMs)
    {
        return std::max<std::uint64_t>(plannedMs + everyMs, nowMs + 1);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VA6 Sunder Armor (the stock beat, the value made real)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kSunderFirstMs = 1000;
    inline constexpr std::uint32_t kSunderEveryMinMs = 6000;
    inline constexpr std::uint32_t kSunderEveryMaxMs = 8000;
    inline constexpr std::uint32_t kSunderArmorPct = 5;
    inline constexpr std::uint8_t kSunderMaxStacks = 5;
    inline constexpr std::uint32_t kSunderMs = 30000;
    inline constexpr std::uint32_t kRetryMs = 1000;

    // ----------------------------------------------------------------------------------------------------------------
    // VA7 Watchman's Draught
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::array<float, 2> kDraughtAtPct{ { 60.f, 30.f } };
    inline constexpr std::uint32_t kDraughtHealPct = 5;
    inline constexpr std::uint32_t kDraughtDamagePct = 20;
    inline constexpr std::uint32_t kDraughtMs = 15000;

    // The draught due at `healthPct` (the deepest threshold crossed and not drunk yet), as its bit in `drunkMask`.
    constexpr std::optional<std::uint8_t> DraughtDue(float healthPct, std::uint8_t drunkMask)
    {
        for (std::size_t i = kDraughtAtPct.size(); i-- > 0;)
            if (healthPct <= kDraughtAtPct[i] && !(drunkMask & (1u << i)))
                return static_cast<std::uint8_t>(i);
        return std::nullopt;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VA8 The loot clock (the seal times are the header's: kVaultSealFirstBagS, kVaultSealGearS, kVaultSealLastBagS)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::array<std::uint32_t, 3> kSealAtS{ {
        BlackrockDepthsRework::kVaultSealFirstBagS, BlackrockDepthsRework::kVaultSealGearS,
        BlackrockDepthsRework::kVaultSealLastBagS } };
    inline constexpr std::array<std::uint8_t, 3> kSealText{ { EMOTE_VA_SEAL_BAG, EMOTE_VA_SEAL_GEAR,
        EMOTE_VA_SEAL_LAST_BAG } };

    // The seals passed by `clockMs` (bit i = seal i).
    constexpr std::uint8_t SealsPassed(std::uint64_t clockMs)
    {
        std::uint8_t mask = 0;
        for (std::size_t i = 0; i < kSealAtS.size(); ++i)
            if (clockMs >= std::uint64_t(kSealAtS[i]) * 1000u)
                mask = static_cast<std::uint8_t>(mask | (1u << i));
        return mask;
    }

    // The finishing time the instance stores (DATA_VAULT_CLOCK, whole seconds, never 0: 0 means "not finished").
    constexpr std::uint32_t FinishedSeconds(std::uint64_t clockMs)
    {
        return static_cast<std::uint32_t>(std::max<std::uint64_t>(1, clockMs / 1000));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Secret Safe's contents (section 7 #17: the Cinder always, one gear item never Doomgrip's, bags by the clock)
    // ----------------------------------------------------------------------------------------------------------------

    // Doomgrip's list (SP "Loot"; apps/dbc-tools source/items/blackrock_depths.py, item_ids.lock): the Normal tier is
    // the stock id, the Heroic tier the minted one; the same index in both is the same item.
    inline constexpr std::array<std::uint32_t, 4> kGearNormal{ { 22205, 22254, 22255, 22256 } };
    inline constexpr std::array<std::uint32_t, 4> kGearHeroic{ { 72978, 72982, 72986, 72990 } };
    inline constexpr std::uint32_t kItemBagNormal = BlackrockDepthsRework::kItemVaultTreasureBag;   // 70620
    inline constexpr std::uint32_t kItemBagHeroic = 70623;      // STAGE-IT-REPORT: the two-gem heroic bag
    static_assert(kItemBagHeroic == BlackrockDepthsRework::kItemVaultTreasureBagHeroic, "the header's heroic bag");
    inline constexpr std::uint32_t kItemCinder = BlackrockDepthsRework::kItemCinderOfTheFirelord;    // 70621

    // The index of `item` in Doomgrip's list (either tier), if it is one of the four.
    constexpr std::optional<std::size_t> GearIndexOf(std::uint32_t item)
    {
        for (std::size_t i = 0; i < kGearNormal.size(); ++i)
            if (item == kGearNormal[i] || item == kGearHeroic[i])
                return i;
        return std::nullopt;
    }

    constexpr std::uint32_t BagFor(bool heroic)
    {
        return heroic ? kItemBagHeroic : kItemBagNormal;
    }

    // An item the Safe's script owns: anything of these the Safe's loot table rolled is replaced by the script's set.
    constexpr bool IsSafeManagedItem(std::uint32_t item)
    {
        return item == kItemCinder || item == kItemBagNormal || item == kItemBagHeroic
            || GearIndexOf(item).has_value();
    }

    // The Safe's gear item: one of the four of the difficulty's tier, never the one Doomgrip dropped
    // (`doomgripItem`, 0: unknown, any of the four), picked by `roll`.
    constexpr std::uint32_t PickSafeGear(bool heroic, std::uint32_t doomgripItem, std::uint32_t roll)
    {
        std::optional<std::size_t> const excluded = GearIndexOf(doomgripItem);
        std::size_t const choices = excluded ? kGearNormal.size() - 1 : kGearNormal.size();
        std::size_t pick = roll % choices;
        if (excluded && pick >= *excluded)
            ++pick;
        return heroic ? kGearHeroic[pick] : kGearNormal[pick];
    }

    // Every item the script puts in the Safe (the Cinder, then the gear, then the bags); none before the Vault is done.
    struct SafeItems
    {
        std::array<std::uint32_t, 4> items{};
        std::size_t count = 0;

        constexpr void Add(std::uint32_t item)
        {
            if (count < items.size())
                items[count++] = item;
        }
    };

    constexpr SafeItems SafeItemsFor(std::uint32_t finishedS, bool heroic, std::uint32_t doomgripItem,
        std::uint32_t roll)
    {
        SafeItems out;
        VaultSafe const safe = BlackrockDepthsRework::VaultSafeFor(finishedS);
        if (safe.cinder)
            out.Add(kItemCinder);
        if (safe.gear)
            out.Add(PickSafeGear(heroic, doomgripItem, roll));
        for (std::uint32_t i = 0; i < safe.bags; ++i)
            out.Add(BagFor(heroic));
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VA1 Lockdown: the room's one way out [navmesh estimate, 2026-11-17: the floor's rim by bearing from kVaultCenter
    // is closed from 0 to 30 and from 56 to 360 degrees; the gap between (828.5, -339.2) and (823.0, -333.7), about
    // 7.8 yd wide, 16.7 yd out, is the doorway north-east into the hall]
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr Vec2 kDoorwayA{ 828.5f, -339.2f };
    inline constexpr Vec2 kDoorwayB{ 823.0f, -333.7f };
    inline constexpr float kDoorwayZ = -50.1f;
    // Out of the room through the doorway (unit), and across it.
    inline constexpr Vec2 kDoorwayOut{ 0.7335f, 0.6796f };
    inline constexpr Vec2 kDoorwayAcross{ -0.6796f, 0.7335f };
    // The fence: the corridor strip past the doorway (along kDoorwayOut from kVaultCenter: 18 to 32 yd; across: 14 yd
    // each side). The room's floor never reaches 17.5 yd along it, so nobody inside is ever in it.
    inline constexpr float kFenceNearYd = 18.f;
    inline constexpr float kFenceFarYd = 32.f;
    inline constexpr float kFenceHalfWidthYd = 14.f;
    inline constexpr float kFenceZMin = -54.f;
    inline constexpr float kFenceZMax = -45.f;

    constexpr Vec2 DoorwayCenter()
    {
        return Vec2{ (kDoorwayA.x + kDoorwayB.x) / 2.f, (kDoorwayA.y + kDoorwayB.y) / 2.f };
    }

    constexpr Vec2 FencePoint(float along, float across)
    {
        Vec2 const c = BlackrockDepthsRework::kVaultCenter;
        return Vec2{ c.x + kDoorwayOut.x * along + kDoorwayAcross.x * across,
            c.y + kDoorwayOut.y * along + kDoorwayAcross.y * across };
    }

    inline std::vector<Vec2> FencePolygon()
    {
        return { FencePoint(kFenceNearYd, -kFenceHalfWidthYd), FencePoint(kFenceNearYd, kFenceHalfWidthYd),
            FencePoint(kFenceFarYd, kFenceHalfWidthYd), FencePoint(kFenceFarYd, -kFenceHalfWidthYd) };
    }

    // How far along the way out a point is, from the room's center.
    constexpr float AlongDoorway(Vec2 p)
    {
        Vec2 const c = BlackrockDepthsRework::kVaultCenter;
        return (p.x - c.x) * kDoorwayOut.x + (p.y - c.y) * kDoorwayOut.y;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The room, for the bots' planned spots: inside the rim's smallest radius (12.2 yd)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kRoomBoundsYd = 12.f;
    inline constexpr float kRoomZMin = -54.f;
    inline constexpr float kRoomZMax = -46.f;
    inline constexpr float kSentinelSearchYd = 40.f;
}

#endif
