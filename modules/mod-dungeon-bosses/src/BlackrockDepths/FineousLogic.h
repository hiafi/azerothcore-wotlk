/*
 * mod-dungeon-bosses, Blackrock Depths D10:
 * Fineous Darkvire (9056) and the Guzzler rope, the pure, host-testable part (no engine headers). Build spec:
 * docs/dungeons/blackrock-depths-2-shadowforge-city.md "Fineous Darkvire" (FD1, FD2, the rope; rulings 46, 66, 67),
 * handoff sections 3.4 / 3.5 row D10, 3.6, 3.7 (the rope), 3.8 (the ramp), 3.10. Tested by tests/brd_fineous_test.cpp.
 *
 *   Spells        the WP's ids, inside kSpellsFineous (211120-211139), declared in apps/dbc-tools
 *                 source/npcs/blackrock_depths/fineous.py; the stock spells he keeps
 *   Tuning        NH<> values and the cadences, straight from the build spec
 *   Holy Light    FD2: once at 60% and once at 40% health, never repeated (an interrupted one is lost)
 *   Ramp          his leash frame (the whole patrol and the adds' side), the patrol's waypoints, and the two narrow
 *                 corners where FD1 never picks a player (no pillar circle there)
 *   Rope          the use spell's refusals, the drop and the hanging rope's visibility, the climb's destination
 *   FightClock    a repeating beat on the AI's own ms clock
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_FINEOUS_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_FINEOUS_LOGIC_H

#include "BlackrockDepthsRework.h"
#include <array>
#include <cstddef>
#include <cstdint>

namespace BrdFineous
{
    using BlackrockDepthsRework::Point3;
    using BlackrockDepthsRework::Point4;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsFineous;

    enum FineousSpells : std::uint32_t
    {
        SPELL_FD_SHODDY_COLLAPSE    = kSpellSlice.first + 0,    // 211120 FD1 the collapse's hit (resolve copy)
        SPELL_FD_HOLY_LIGHT         = kSpellSlice.first + 1,    // 211121 FD2 his 2.5 s self-heal, 4% of his health
        SPELL_FD_PILLAR_RISE        = kSpellSlice.first + 2,    // 211122 FD1 the earth spike as the pillar rises (look)
        SPELL_FD_COLLAPSE_DUST      = kSpellSlice.first + 3,    // 211123 FD1 the dust plume as it falls (look only)
        // 211124-211139 spare
    };
    static_assert(SPELL_FD_COLLAPSE_DUST <= kSpellSlice.last, "Fineous's spells must stay in his slice");

    // The stock spells he keeps (SmartAI 9056 rows 0-5, dropped by the S0 rev; Holy Light is the copy above).
    inline constexpr std::uint32_t SPELL_FD_DEVOTION_AURA = 8258;       // on the pull, self, once (+20 armor, 30 yd)
    inline constexpr std::uint32_t SPELL_FD_HOLY_STRIKE = 13953;        // the victim; weapon damage + holy
    inline constexpr std::uint32_t SPELL_FD_KICK = 11978;               // 2 damage + a 6 s interrupt lockout
    inline constexpr std::uint32_t SPELL_FD_SEAL_OF_RECKONING = 15346;  // at 20%, self, once (30 s, heals 24 a strike)

    // Registry tags (the build spec's mechanic numbers; the failure ledger and the playtest greps key on them).
    enum FineousTags : std::uint32_t
    {
        TAG_SHODDY_CONSTRUCTION = 1,    // FD1
    };

    // creature_text groups (data/sql/updates/pending_db_world/rev_fineous_blackrock_depths.sql): Franclorn's Spirit
    // 9542 (D7 owns its group 0, the Loregrain kill line); Fineous has no text of his own.
    inline constexpr std::uint8_t TEXT_FRANCLORN_IRONFEL = 1;

    // ----------------------------------------------------------------------------------------------------------------
    // The fight (build spec "Design", "Build spec" FD1, FD2)
    // ----------------------------------------------------------------------------------------------------------------

    // FD1 Shoddy Construction: every 15 s (heroic 12 s) a pillar goes in at a random player's spot; 3 s later it
    // collapses in a 6 yd circle: 25% (heroic 40%) + Weakened. The first one comes a little before the first beat
    // (the spec gives no first timer: designer question 1).
    inline constexpr NH<std::uint32_t> kShoddyFirstMs{ 8000, 6000 };
    inline constexpr NH<std::uint32_t> kShoddyEveryMs{ 15000, 12000 };
    inline constexpr NH<float> kShoddyPct{ 25.f, 40.f };
    inline constexpr std::uint32_t kShoddyWarnMs = 3000;
    inline constexpr float kShoddyRadiusYd = 6.f;
    // A pillar with no target to fall on (everyone on a corner, nobody in reach) tries again after this.
    inline constexpr std::uint32_t kShoddyRetryMs = 2000;
    // The pillar object is deleted at the collapse; this is its own backstop.
    inline constexpr std::uint32_t kShoddyObjectBackstopMs = kShoddyWarnMs + 2000;
    // Where the object and the dust stand: the floor under the player (a player in the air gets the floor within
    // this many yd below, else his own height).
    inline constexpr float kShoddyGroundSearchYd = 8.f;

    // The stock kit's cadences (SmartAI 9056, all flag 2: normal difficulty; heroic keeps them, DD scales the spells).
    inline constexpr std::uint32_t kHolyStrikeFirstMs = 3000;
    inline constexpr std::uint32_t kHolyStrikeMinMs = 6000;
    inline constexpr std::uint32_t kHolyStrikeMaxMs = 8500;
    inline constexpr std::uint32_t kKickFirstMs = 12000;
    inline constexpr std::uint32_t kKickEveryMs = 7000;
    inline constexpr float kKickRangeYd = 5.f;

    // FD2 Holy Light: 2.5 s, interruptible, 4% of his health (stock 467-541 on 13,734 = 3.4-3.9%, rescaled with his
    // health). Once at 60% and once at 40%; neither repeats, so an interrupted one is lost (the reward).
    inline constexpr float kHolyLightHealPct = 4.f;
    inline constexpr std::uint32_t kHolyLightCastMs = 2500;
    inline constexpr std::array<float, 2> kHolyLightAtPct{ 60.f, 40.f };
    inline constexpr float kSealAtPct = 20.f;

    // The Holy Light casts (bit i = threshold i started) due at this health.
    constexpr std::uint32_t HolyLightsDue(float healthPct, std::uint32_t doneMask)
    {
        std::uint32_t due = 0;
        for (std::size_t i = 0; i < kHolyLightAtPct.size(); ++i)
            if (healthPct <= kHolyLightAtPct[i] && !(doneMask & (1u << i)))
                due |= 1u << i;
        return due;
    }

    // The first due cast (the lower threshold waits for the first to finish), or -1.
    constexpr int NextHolyLight(float healthPct, std::uint32_t doneMask)
    {
        std::uint32_t const due = HolyLightsDue(healthPct, doneMask);
        for (std::size_t i = 0; i < kHolyLightAtPct.size(); ++i)
            if (due & (1u << i))
                return static_cast<int>(i);
        return -1;
    }

    constexpr bool SealDue(float healthPct, bool done)
    {
        return !done && healthPct <= kSealAtPct;
    }

    // The stock Kick: a player casting within 5 yd of him (the stock event, AREA_CASTING, 0 to 5 yd).
    constexpr bool KickTarget(bool casting, float distanceYd)
    {
        return casting && distanceYd >= 0.f && distanceYd <= kKickRangeYd;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The ramp
    // ----------------------------------------------------------------------------------------------------------------

    // The patrol (waypoint_data 476310, 18 points, there and back; [db] read 2026-11-17).
    inline constexpr std::array<Point3, 18> kPatrol{{
        { 963.267f, -343.735f, -71.739f }, { 981.865f, -362.260f, -66.055f }, { 983.254f, -374.384f, -66.288f },
        { 969.330f, -388.630f, -60.838f }, { 957.682f, -400.149f, -60.796f }, { 945.479f, -412.692f, -55.068f },
        { 933.462f, -413.572f, -55.387f }, { 919.726f, -400.435f, -49.580f }, { 901.371f, -379.424f, -49.936f },
        { 918.956f, -400.470f, -49.384f }, { 931.895f, -413.196f, -55.387f }, { 945.806f, -412.567f, -55.144f },
        { 957.165f, -400.344f, -60.642f }, { 969.142f, -387.739f, -60.838f }, { 982.107f, -375.658f, -66.287f },
        { 982.143f, -363.525f, -65.951f }, { 970.029f, -350.765f, -71.034f }, { 959.527f, -339.728f, -71.465f },
    }};

    // His leash frame: the whole ramp, the patrol's far end (901, -379) and the adds' side (the Doomforge Craftsmen
    // stand out to x 1002; the shared stub's box began at x 925 and cut the patrol), z from the causeway (-72) to the
    // top of the ramp (-49): a player who falls into the open middle is off it. [navmesh estimate]
    inline constexpr float kRampMinX = 888.f;
    inline constexpr float kRampMaxX = 1012.f;
    inline constexpr float kRampMinY = -424.f;
    inline constexpr float kRampMaxY = -322.f;
    inline constexpr float kRampMinZ = -80.f;
    inline constexpr float kRampMaxZ = -44.f;

    inline DungeonKit::Arena RampArena()
    {
        return DungeonKit::Arena(BlackrockDepthsRework::BoxRegion(kRampMinX, kRampMaxX, kRampMinY, kRampMaxY,
            kRampMinZ, kRampMaxZ));
    }

    // The two corners where the walkway narrows to 3-6 yd (the legs are 16-18 yd wide; NAVMESH 2.4, handoff 3.8): no
    // pillar circle there. A player standing inside one of these discs is never picked. [navmesh estimate]
    struct CornerDisc
    {
        Vec2 center;
        float radiusYd;
    };
    inline constexpr float kCornerRadiusYd = 9.f;
    inline constexpr std::array<CornerDisc, 2> kCorners{{
        { { 978.f, -370.f }, kCornerRadiusYd },
        { { 938.f, -408.f }, kCornerRadiusYd },
    }};

    inline bool OnCorner(Vec2 p)
    {
        for (CornerDisc const& c : kCorners)
            if (DungeonKit::Distance(p, c.center) <= c.radiusYd)
                return true;
        return false;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Guzzler rope (ruling 67; handoff 3.7; item 70622, use spell 211261 spell_brd_guzzler_rope, hanging rope GO
    // 301282 go_brd_hanging_rope)
    // ----------------------------------------------------------------------------------------------------------------

    // The use spell works only within this radius of the climb spot behind Lord Incendius (893.5, -267.1, -71.9, his
    // spawn): the Anvil's bulge is 22-24 yd wide (NAVMESH 2.5), so 12 yd is the whole bulge's disc and no more. The z
    // tolerance keeps the lava level (37 yd below) and the walkway above out. [navmesh estimate]
    inline constexpr float kRopeSpotRadiusYd = 12.f;
    inline constexpr float kRopeSpotZToleranceYd = 6.f;

    // The climb's destination: the floor past the Bar Door (the shared header's kRopeTop), turned toward the bar.
    inline constexpr Point4 kRopeLanding{ 878.5f, -222.5f, -49.8f, 2.17f };

    // The hanging rope object's spawn (a static spawn the script shows and hides): the climb spot.
    inline constexpr Point4 kRopeHang{ 893.5f, -267.1f, -71.9f, 2.0f };
    // A click carries a player this far at most from the rope (the client's own interact range is about 5 yd).
    inline constexpr float kRopeClickRangeYd = 8.f;

    enum class RopeRefusal : std::uint8_t
    {
        None = 0,
        NotInDungeon,       // not map 230, or no instance
        AlreadyHung,        // the instance's rope is up (one hanging rope per instance)
        NotAtTheSpot,       // not on the ledge behind Lord Incendius
    };

    // The use spell's checks, in the order the player is told. `distanceYd` = 2D distance to the climb spot, `dzYd` =
    // the height difference to it.
    constexpr RopeRefusal RopeUseRefusal(std::uint32_t mapId, bool hasInstance, std::uint32_t ropeState,
        float distanceYd, float dzYd)
    {
        if (mapId != BlackrockDepthsRework::kMapBlackrockDepths || !hasInstance)
            return RopeRefusal::NotInDungeon;
        if (ropeState >= BlackrockDepthsRework::ROPE_PLACED)
            return RopeRefusal::AlreadyHung;
        float const dz = dzYd < 0.f ? -dzYd : dzYd;
        if (distanceYd > kRopeSpotRadiusYd || dz > kRopeSpotZToleranceYd)
            return RopeRefusal::NotAtTheSpot;
        return RopeRefusal::None;
    }

    // The player-facing words of each refusal (a refused cast does not consume the rope).
    constexpr char const* RopeRefusalText(RopeRefusal why)
    {
        switch (why)
        {
            case RopeRefusal::NotInDungeon:
                return "The rope is only of use in Blackrock Depths.";
            case RopeRefusal::AlreadyHung:
                return "A rope already hangs from the ledge.";
            case RopeRefusal::NotAtTheSpot:
                return "Tie the rope off on the ledge behind Lord Incendius.";
            case RopeRefusal::None:
                break;
        }
        return "";
    }

    // Fineous drops the rope once per instance: while none has dropped or hung. Never again (a respawned Fineous after
    // his 12 h respawn, a rope already hanging).
    constexpr bool RopeDropAllowed(std::uint32_t ropeState)
    {
        return ropeState == BlackrockDepthsRework::ROPE_NONE;
    }

    // The hanging rope object is seen and clickable only once the rope is placed (saved, so it is back after a reload:
    // the object is a static spawn that reads the instance).
    constexpr bool RopeObjectShown(std::uint32_t ropeState)
    {
        return ropeState == BlackrockDepthsRework::ROPE_PLACED;
    }

    // The climb is a click within range of a shown rope.
    constexpr bool RopeClickAllowed(std::uint32_t ropeState, float distanceYd)
    {
        return RopeObjectShown(ropeState) && distanceYd <= kRopeClickRangeYd;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Franclorn's line on his death (S2 749): a copy of the spirit by the corpse for this long
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kFranclornLifeMs = 12000;
    inline constexpr float kFranclornOffsetYd = 2.f;

    // ----------------------------------------------------------------------------------------------------------------
    // FightClock: a repeating beat on the AI's own ms clock
    // ----------------------------------------------------------------------------------------------------------------

    class FightClock
    {
    public:
        // Starts (or restarts) the beat: due `afterMs` from `nowMs`.
        void Start(std::uint64_t nowMs, std::uint32_t afterMs)
        {
            _on = true;
            _dueMs = nowMs + afterMs;
        }

        void Stop() { _on = false; }
        bool On() const { return _on; }
        std::uint64_t DueMs() const { return _dueMs; }

        bool Due(std::uint64_t nowMs) const { return _on && nowMs >= _dueMs; }

        // It fired: the next one is `everyMs` after this one's due time (start to start), never in the past.
        void Fired(std::uint64_t nowMs, std::uint32_t everyMs)
        {
            _dueMs += everyMs;
            if (_dueMs <= nowMs)
                _dueMs = nowMs + everyMs;
        }

    private:
        bool _on = false;
        std::uint64_t _dueMs = 0;
    };
}

#endif
