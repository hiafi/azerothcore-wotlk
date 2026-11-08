/*
 * mod-dungeon-bosses, Shadowfang Keep: Wolf Master Nandos (WP-S8), the pure, host-testable part (no engine headers):
 * spell ids, per-difficulty tuning numbers, timers, the pack roster, Pack Bond, the Mark the Prey split and the
 * Alpha's Inheritance bookkeeping. Build spec: SK 1338-1390 (build spec), SK 1238-1337 (design), NA1-NA9.
 *
 * Conventions (ShadowfangKeepRework.h): spell ids only inside the slice below (apps/dbc-tools
 * source/npcs/shadowfang_keep/wolf_master_nandos.py declares the same ids); tuning numbers as
 * `inline constexpr DungeonKit::NH<T> kName{ normal, heroic };` where they differ. The damage percents are the same on
 * both difficulties: the reference row (normal 1,300 / heroic 4,120) makes the difference.
 */

#ifndef MOD_DUNGEON_BOSSES_SFK_NANDOS_LOGIC_H
#define MOD_DUNGEON_BOSSES_SFK_NANDOS_LOGIC_H

#include "DungeonKitLogic.h"
#include "DungeonKitMath.h"
#include "ShadowfangKeepRework.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>
#include <vector>

namespace Nandos
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // This boss's spell slice (handoff section 3.4).
    inline constexpr ShadowfangKeepRework::IdSlice kSlice = ShadowfangKeepRework::kSpellsNandos;

    // ----------------------------------------------------------------------------------------------------------------
    // Spells (wolf_master_nandos.py declares the same ids; 206051-206059 spare)
    // ----------------------------------------------------------------------------------------------------------------
    enum NandosSpells : std::uint32_t
    {
        SPELL_NANDOS_ACID_SLAVER_BAR        = 206040,   // NA4 2 s cast bar (Acid Breath SV 2619)
        SPELL_NANDOS_ACID_SLAVER            = 206041,   // NA4 the registry's resolve copy, Nature
        SPELL_NANDOS_GUARDIAN_HOWL          = 206042,   // NA5 normal: 2 s interruptible, heals the pack 5%
        SPELL_NANDOS_GUARDIAN_HOWL_HEROIC   = 206043,   // NA5 heroic: heals 5% and +15% damage done for 10 s
        SPELL_NANDOS_PACK_BOND              = 206044,   // NA7 on Nandos: damage taken -10% per living wolf
        SPELL_NANDOS_PACK_BOND_LINK         = 206045,   // NA7 the beam each living wolf holds on Nandos (look only)
        SPELL_NANDOS_MARKED_PREY            = 206046,   // NA6 the prey's 4 s head marker (Hunter's Mark SV 3239)
        SPELL_NANDOS_MARK_THE_PREY          = 206047,   // NA6 a wolf's lunge hit, Physical (one split share)
        SPELL_NANDOS_WAVERING_WILL          = 206048,   // NA1 inherited (heroic): stacking Shadow DoT, Magic
        SPELL_NANDOS_LUPINE_TERROR          = 206049,   // NA3 (heroic): the 2 s fear rider
        SPELL_NANDOS_LUPINE_TERROR_HIT      = 206050,   // NA3 the fear spot's resolve copy (no damage)
    };

    inline constexpr std::array<std::uint32_t, 11> kAllSpells{ {
        SPELL_NANDOS_ACID_SLAVER_BAR, SPELL_NANDOS_ACID_SLAVER, SPELL_NANDOS_GUARDIAN_HOWL,
        SPELL_NANDOS_GUARDIAN_HOWL_HEROIC, SPELL_NANDOS_PACK_BOND, SPELL_NANDOS_PACK_BOND_LINK,
        SPELL_NANDOS_MARKED_PREY, SPELL_NANDOS_MARK_THE_PREY, SPELL_NANDOS_WAVERING_WILL, SPELL_NANDOS_LUPINE_TERROR,
        SPELL_NANDOS_LUPINE_TERROR_HIT } };

    // Stock spells the pack keeps (DD scales them on heroic).
    using ShadowfangKeepRework::SPELL_SUMMON_LUPINE_DELUSIONS;
    using ShadowfangKeepRework::SPELL_WAVERING_WILL;

    // Registry tags (log and `.mech` ledger).
    enum NandosTags : std::uint32_t
    {
        TAG_NANDOS_ACID_SLAVER          = 0x4E410401,   // NA4, a Slavering Worg's 8 yd cone
        TAG_NANDOS_ACID_SLAVER_ALPHA    = 0x4E410402,   // NA4, Nandos's inherited 20 yd cone
        TAG_NANDOS_MARK_THE_PREY        = 0x4E410601,   // NA6
        TAG_NANDOS_LUPINE_TERROR        = 0x4E410301,   // NA3
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The pack (boss kit 300509-300512 on spawns 16238-16241)
    // ----------------------------------------------------------------------------------------------------------------
    enum class Wolf : std::uint8_t
    {
        Bleak = 0,          // Wavering Will (NA1)
        Lupine = 1,         // Lupine Delusions (NA2, heroic NA3)
        Slavering = 2,      // Acid Slaver (NA4)
        Wolfguard = 3,      // Guardian Howl (NA5)
    };

    inline constexpr std::size_t kWolfCount = 4;

    inline constexpr std::array<std::uint32_t, kWolfCount> kPackEntries{ {
        ShadowfangKeepRework::NPC_SFK_PACK_BLEAK_WORG, ShadowfangKeepRework::NPC_SFK_PACK_LUPINE_HORROR,
        ShadowfangKeepRework::NPC_SFK_PACK_SLAVERING_WORG, ShadowfangKeepRework::NPC_SFK_PACK_WOLFGUARD_WORG } };

    // Each copy's stock entry (the spawn's entry before the SQL rev), display, and spawn guid (DB-FACTS s3), in Wolf
    // order.
    inline constexpr std::array<std::uint32_t, kWolfCount> kStockEntries{ {
        ShadowfangKeepRework::NPC_BLEAK_WORG, ShadowfangKeepRework::NPC_LUPINE_HORROR,
        ShadowfangKeepRework::NPC_SLAVERING_WORG, ShadowfangKeepRework::NPC_WOLFGUARD_WORG } };
    inline constexpr std::array<std::uint32_t, kWolfCount> kDisplays{ { 801, 2446, 11421, 246 } };
    inline constexpr std::array<std::uint32_t, kWolfCount> kPackSpawnGuids{ { 16239, 16238, 16240, 16241 } };

    constexpr std::size_t Index(Wolf w)
    {
        return static_cast<std::size_t>(w);
    }

    constexpr std::uint32_t EntryOf(Wolf w)
    {
        return kPackEntries[Index(w)];
    }

    constexpr std::optional<Wolf> WolfOf(std::uint32_t entry)
    {
        for (std::size_t i = 0; i < kWolfCount; ++i)
            if (kPackEntries[i] == entry)
                return static_cast<Wolf>(i);
        return std::nullopt;
    }

    constexpr char const* WolfName(Wolf w)
    {
        switch (w)
        {
            case Wolf::Bleak:
                return "bleak";
            case Wolf::Lupine:
                return "lupine";
            case Wolf::Slavering:
                return "slavering";
            case Wolf::Wolfguard:
                return "wolfguard";
        }
        return "?";
    }

    // `.sfktest nandos inherit <name>`: the wolf by its short name.
    constexpr std::optional<Wolf> WolfByName(std::string_view name)
    {
        for (std::size_t i = 0; i < kWolfCount; ++i)
            if (name == WolfName(static_cast<Wolf>(i)))
                return static_cast<Wolf>(i);
        return std::nullopt;
    }

    // Boss data kill order (SK 1368, approved): Wolfguard, Slavering, Bleak, Lupine, then Nandos (priority 0). The
    // delusions die to one hit (cleave fodder): above every wolf, AoE allowed.
    constexpr std::int8_t KillPriority(Wolf w)
    {
        switch (w)
        {
            case Wolf::Wolfguard:
                return 4;
            case Wolf::Slavering:
                return 3;
            case Wolf::Bleak:
                return 2;
            case Wolf::Lupine:
                return 1;
        }
        return 0;
    }
    inline constexpr std::int8_t kDelusionPriority = 5;

    // The pack search from Nandos (the farthest wolf stands 28.5 yd from him).
    inline constexpr float kPackSearchYd = 60.f;

    // ----------------------------------------------------------------------------------------------------------------
    // NA7 Pack Bond: damage taken -40% while all four wolves live, 10% less per wolf killed (one aura whose amount the
    // script sets: additive steps, not four multiplied auras)
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::int32_t kPackBondPctPerWolf = 10;

    constexpr std::uint32_t ClampWolves(std::uint32_t alive)
    {
        return alive > kWolfCount ? static_cast<std::uint32_t>(kWolfCount) : alive;
    }

    // The Pack Bond aura's amount (MOD_DAMAGE_PERCENT_TAKEN) with `alive` wolves: -10 per wolf, 0 with none.
    constexpr std::int32_t PackBondAmount(std::uint32_t alive)
    {
        return -kPackBondPctPerWolf * static_cast<std::int32_t>(ClampWolves(alive));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // NA6 Mark the Prey: a 6 yd Stack on a random non-tank; 4 s later every living wolf lunges: 25% of reference
    // health per wolf, split among the players inside, at most 75% to one player. Physical, no Weakened.
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kPreyFirstMs = 10000;
    inline constexpr std::uint32_t kPreyEveryMs = 18000;
    inline constexpr std::uint32_t kPreyWarnMs = 4000;
    inline constexpr float kPreyRadiusYd = 6.f;
    inline constexpr float kPreyPctPerWolf = 25.f;
    inline constexpr float kPreyCapPct = 75.f;
    inline constexpr float kPreyPickRangeYd = 60.f;

    constexpr float PreyTotalPct(std::uint32_t alive)
    {
        return kPreyPctPerWolf * static_cast<float>(ClampWolves(alive));
    }

    // Mark the Prey runs while a wolf lives ("killing wolves shrinks the lunge; with no wolves left it stops").
    constexpr bool PreyActive(std::uint32_t alive)
    {
        return alive > 0;
    }

    // Each player's share with `alive` wolves and `inside` players, from the reference non-tank row `refNonTank`: the
    // pure form of DungeonKit::SplitShares(nandos, inside, PreyTotalPct(alive), kPreyCapPct).
    inline std::vector<std::uint32_t> PreyShares(std::uint32_t refNonTank, std::uint32_t alive, std::uint32_t inside)
    {
        std::uint32_t const total = DungeonKit::RefFlatValue(refNonTank, refNonTank, PreyTotalPct(alive), false);
        std::uint32_t const cap = DungeonKit::RefFlatValue(refNonTank, refNonTank, kPreyCapPct, false);
        return DungeonKit::SplitDamage(total, inside, cap);
    }

    // The lunge: share `share` is dealt by wolf `share % wolves` (every wolf lunges; the hits spread over them).
    constexpr std::size_t LungeWolfFor(std::size_t share, std::size_t wolves)
    {
        return wolves ? share % wolves : 0;
    }

    // Where a lunging wolf lands: `offset` yd short of the prey on the line from the wolf (it stays put when it is
    // that close already).
    inline Vec2 LungeLanding(Vec2 wolf, Vec2 prey, float offset)
    {
        float const d = DungeonKit::Distance(wolf, prey);
        if (d <= offset)
            return wolf;
        return DungeonKit::Advance(prey, DungeonKit::BearingTo(prey, wolf), offset);
    }
    inline constexpr float kLungeOffsetYd = 1.5f;
    inline constexpr float kLungeSpeedXY = 25.f;
    inline constexpr float kLungeMinSpeedZ = 6.f;

    // ----------------------------------------------------------------------------------------------------------------
    // NA4 Acid Slaver: 2 s cast bar, then a 90 degree Frontal (the caster's target exempt), 35% Nature + 1 Weakened
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr float kSlaverAngleDeg = 90.f;
    inline constexpr float kSlaverWolfYd = 8.f;     // the Slavering Worg's
    inline constexpr float kSlaverAlphaYd = 20.f;   // inherited (heroic, Nandos)
    inline constexpr float kSlaverPct = 35.f;
    inline constexpr std::uint32_t kSlaverWarnMs = 2000;
    inline constexpr std::uint32_t kSlaverFirstMs = 6000;
    inline constexpr std::uint32_t kSlaverEveryMs = 15000;

    constexpr float SlaverLength(bool inherited)
    {
        return inherited ? kSlaverAlphaYd : kSlaverWolfYd;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // NA5 Guardian Howl: a real 2 s interruptible cast; heals Nandos and every living wolf 5% of their health, heroic
    // also +15% damage done for 10 s
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kHowlCastMs = 2000;
    inline constexpr std::uint32_t kHowlFirstMs = 8000;
    inline constexpr std::uint32_t kHowlEveryMs = 20000;
    inline constexpr std::uint32_t kHowlHealPct = 5;
    inline constexpr std::uint32_t kHowlDamagePct = 15;
    inline constexpr std::uint32_t kHowlBuffMs = 10000;
    inline constexpr float kHowlRadiusYd = 50.f;    // the room is 33 x 35 yd; the spell script keeps the pack only
    inline constexpr NH<std::uint32_t> kHowlSpell{ SPELL_NANDOS_GUARDIAN_HOWL, SPELL_NANDOS_GUARDIAN_HOWL_HEROIC };

    // Who Guardian Howl touches: Nandos and the pack copies, never another Shadowfang creature in range.
    constexpr bool HowlTouches(std::uint32_t entry)
    {
        return entry == ShadowfangKeepRework::NPC_NANDOS || WolfOf(entry).has_value();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // NA1 Wavering Will (stock 7127 from the Bleak Worg: 2-10 s, then every 15-20 s, on its target)
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kWillFirstMinMs = 2000;
    inline constexpr std::uint32_t kWillFirstMaxMs = 10000;
    inline constexpr std::uint32_t kWillEveryMinMs = 15000;
    inline constexpr std::uint32_t kWillEveryMaxMs = 20000;
    // Inherited (heroic): Nandos puts the stock slows and one stack of a Shadow DoT on his tank every 15 s; each stack
    // deals 2% of reference health every 2 s, up to 5 stacks, 60 s, Magic (one dispel of the DoT clears every stack
    // and the slows with it).
    inline constexpr std::uint32_t kAlphaWillEveryMs = 15000;
    inline constexpr float kAlphaWillPctPerStack = 2.f;
    inline constexpr std::uint32_t kAlphaWillTickMs = 2000;
    inline constexpr std::uint32_t kAlphaWillMaxStacks = 5;
    inline constexpr std::uint32_t kAlphaWillMs = 60000;

    // ----------------------------------------------------------------------------------------------------------------
    // NA2 Lupine Delusions (stock 7132 from the Lupine Horror: 4-12 s, then every 60 s), NA3 the heroic fear
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kDelusionsFirstMinMs = 4000;
    inline constexpr std::uint32_t kDelusionsFirstMaxMs = 12000;
    inline constexpr std::uint32_t kDelusionsEveryMs = 60000;
    inline constexpr std::uint32_t kAlphaDelusionsEveryMs = 20000;  // inherited (heroic)
    // NA3: 2 s after one of Nandos's own delusions vanishes, a 2 s fear on anyone within 5 yd of the spot (the marker
    // shows for those 2 s). The Lupine Horror's own delusions never leave one.
    inline constexpr float kTerrorRadiusYd = 5.f;
    inline constexpr std::uint32_t kTerrorWarnMs = 2000;
    inline constexpr std::uint32_t kTerrorFearMs = 2000;

    // A delusion leaving the world vanished because it was hit (dead, or below full health: its stock SmartAI
    // despawns it below 99%), not because the fight ended (despawned at full health).
    constexpr bool VanishedByHit(bool alive, std::uint32_t health, std::uint32_t maxHealth)
    {
        return !alive || health < maxHealth;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // NA8 The Alpha's Inheritance (heroic): each wolf's death hands Nandos its ability, on the inherited cadence
    // ----------------------------------------------------------------------------------------------------------------
    // The first inherited cast comes this long after the wolf's death, then every InheritedEveryMs (the build spec
    // gives only the cooldowns).
    inline constexpr std::uint32_t kInheritFirstMs = 5000;

    constexpr std::uint32_t InheritedEveryMs(Wolf w)
    {
        switch (w)
        {
            case Wolf::Bleak:
                return kAlphaWillEveryMs;
            case Wolf::Lupine:
                return kAlphaDelusionsEveryMs;
            case Wolf::Slavering:
                return kSlaverEveryMs;
            case Wolf::Wolfguard:
                return kHowlEveryMs;
        }
        return 0;
    }

    // The inherited set, one bit per wolf.
    class Inheritance
    {
    public:
        // True when `w` was not held yet (schedule its ability).
        bool Take(Wolf w)
        {
            std::uint8_t const bit = Bit(w);
            if (_mask & bit)
                return false;
            _mask = static_cast<std::uint8_t>(_mask | bit);
            return true;
        }

        bool Has(Wolf w) const { return (_mask & Bit(w)) != 0; }
        std::uint8_t Mask() const { return _mask; }
        std::uint32_t Count() const
        {
            std::uint32_t n = 0;
            for (std::size_t i = 0; i < kWolfCount; ++i)
                n += (_mask >> i) & 1u;
            return n;
        }
        void Clear() { _mask = 0; }

    private:
        static constexpr std::uint8_t Bit(Wolf w) { return static_cast<std::uint8_t>(1u << Index(w)); }

        std::uint8_t _mask = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Timing and the arena
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kBusyRetryMs = 500;

    // ArenaGuard landing (handoff section 3.8: the room's most open point, clearance 9.4 yd): a player gripped back
    // lands up to kGripLandYd from the open point toward where they were.
    inline constexpr float kGripLandYd = 4.f;
    // Never grip a unit farther than this from Nandos (the room is 33 x 35 yd; ArenaGuard's default is 120).
    inline constexpr float kGripMaxYd = 60.f;

    inline Vec2 GripLanding(Vec2 from)
    {
        Vec2 const open = ShadowfangKeepRework::kNandosOpenPoint.XY();
        float const d = DungeonKit::Distance(open, from);
        if (d < 0.01f)
            return open;
        return DungeonKit::Advance(open, DungeonKit::BearingTo(open, from), d < kGripLandYd ? d : kGripLandYd);
    }
}

#endif
