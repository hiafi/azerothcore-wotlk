/*
 * mod-dungeon-bosses, Zul'Farrak D4b: the Stair (stage 2 of the Pyramid), the pure, host-testable part (no engine
 * headers). The spell ids of the Stair's half of the slice, the registry tags, the tuning (`namespace Tune`, handoff
 * section 3.5 rule 32), the waves (the stock tables mapped to the three specialists, the send pace), the barrel lane
 * (the stair's true width, its slope, the drawn and the bot-only tiles), the bots' hold on the landing, the crew's
 * places on the Stair and the specialists' picks. Build spec: SP 1346-1432 (PY4-PY11, PY16), design SP 1180-1281
 * (rulings 21-23, 46); handoff section 3.5 row D4b, sections 3.6, 3.8 (the stair, the landing, the plaza), section 7
 * #11 A, #20 A, #31 A, #32 A, #44 A. Tested by tests/zf_stair_test.cpp. Health is ZulFarrakRework.h Health: never
 * restated here.
 *
 * Damage percentages are of the reference health row (209:46 = 2,655 non-tank / 2,717 tank, 209h:60 = 4,120 / 4,110,
 * section 7 #4 A).
 *
 * Mirrored stock behavior (AGENTS.md credit rule): the wave tables, the stair path 81553 and the gathering on the
 * plaza are the stock instance_zulfarrak.cpp's (c9315e3ec moostigre <moostigre@proton.me>, 048025ceb UltraNix
 * <80540499+UltraNix@users.noreply.github.com>), re-implemented; the stock pace (groups of 2, 3, 4 and up every 10 s)
 * is the spec's here (3, 4, 5, 6 and the rest every 8 s).
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_STAIR_LOGIC_H
#define MOD_DUNGEON_BOSSES_ZF_STAIR_LOGIC_H

#include "DungeonKitMath.h"
#include "ZulFarrakRework.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace ZfStair
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using ZulFarrakRework::Point3;

    // Every spell of this WP sits in this slice (ZulFarrakRework.h; ids.yaml reservation `zul_farrak`): the Stair's
    // ids from its first, the Altar's (SezzzizLogic.h) from kAltarSpellBase.
    inline constexpr ZulFarrakRework::IdSlice kSpellSlice = ZulFarrakRework::kSpellsStair;
    std::uint32_t constexpr kAltarSpellBase = kSpellSlice.first + 20;

    // Declared in apps/dbc-tools source/npcs/zul_farrak/pyramid_stair.py (same ids).
    enum StairSpells : std::uint32_t
    {
        SPELL_BARREL_HIT        = kSpellSlice.first + 0,    // PY4 a player on the lane: resolve copy (Fire)
        SPELL_KNOCKDOWN         = kSpellSlice.first + 1,    // PY4 the rider: a 2 s stun (SV 522)
        SPELL_BARREL_BLAST      = kSpellSlice.first + 2,    // PY4 the barrel goes off at the foot (look, SV 889)
        SPELL_BARREL_TROLL      = kSpellSlice.first + 3,    // PY4 a troll on the lane: the script's damage source
        SPELL_BERSERKER_BLEED   = kSpellSlice.first + 4,    // PY6 2% a second for 12 s (normal), Physical
        SPELL_BERSERKER_LOOK    = kSpellSlice.first + 5,    // PY6 the bleed opening (look, SV 372)
        SPELL_TRAMPLING         = kSpellSlice.first + 6,    // PY7 heroic: the charge path, resolve copy (Physical)
        SPELL_CURSE_OF_BLOOD    = kSpellSlice.first + 7,    // PY8 Curse: +10% Physical taken, 30 s
        SPELL_SANDFURY_HEX      = kSpellSlice.first + 8,    // PY9 heroic: Curse, a stack every 4 s, Hexed at 5
        SPELL_HEXED             = kSpellSlice.first + 9,    // PY9 heroic: Magic, a 2 s frog
        SPELL_LAVA_SPOUT        = kSpellSlice.first + 10,   // PY11 heroic: the totem's zone, resolve copy (Fire)
        SPELL_LAVA_TOTEM_BAR    = kSpellSlice.first + 11,   // PY11 heroic: the Witch Doctor's 1 s bar
        SPELL_LAVA_GLOW         = kSpellSlice.first + 12,   // PY11 heroic: the totem's 8 yd fire disc (look, 90508)
        // kSpellSlice.first + 13 .. 19: spare; 20 .. 39: the Altar (SezzzizLogic.h)
    };
    static_assert(SPELL_LAVA_GLOW < kAltarSpellBase, "the Stair's ids stay under the Altar's");
    static_assert(kSpellSlice.Contains(SPELL_BARREL_HIT) && kSpellSlice.Contains(kAltarSpellBase),
        "the Stair's spells sit in the slice");

    // Stock spells cast as they are (SP "Stock kit": Keep; the specialists keep their sources' kits, PY10).
    std::uint32_t constexpr SPELL_HEX_SHADOW_BOLT = 9613;       // the stock Acolyte's Shadow Bolt (Hexmaster)
    std::uint32_t constexpr SPELL_FLASH_HEAL = 17843;           // the stock Witch Doctor's (Holy, kickable: reward)
    std::uint32_t constexpr SPELL_HEALING_WARD = 11899;         // summons the Greater Healing Ward 8179
    std::uint32_t constexpr NPC_HEALING_WARD = 8179;
    std::uint32_t constexpr NPC_LAVA_SPOUT_TOTEM = 6017;        // V's PY_TOTEM_CREATURE (the stock totem's look)

    // Registry tags (the build spec's PY numbers; 10+ for the helpers).
    enum StairTags : std::uint32_t
    {
        TAG_BARREL          = 4,    // PY4 the lane's hit (the kit's RegistryHit)
        TAG_TRAMPLING       = 7,    // PY7 heroic
        TAG_TOTEM           = 11,   // PY11 heroic
        TAG_BARREL_TILE     = 14,   // PY4 the lane's tiles (telegraph only: the drawing and the bots' hazard)
        TAG_HOLD            = 15,   // the landing hold every climber carries (bots only)
    };

    // Texts: Weegli 7607 group 3 "Fire in the hole! Get off the stairs!" (CR's rev inserts it: BlyCrew.h
    // YELL_WEEGLI_BARRELS).

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SP Build spec 1346-1432, "Tuning starting points"; section 7 #31 A, #44 A; section 3.5 rule 32)
    // ----------------------------------------------------------------------------------------------------------------
    namespace Tune
    {
        // Waves 1 and 2 (SP "Waves: send pace", "Stages and pace"): groups of 3, 4, 5, 6 and the rest, one every
        // 8 s, the first at once; 10 s between a wave's last troll and the next wave.
        inline constexpr std::array<std::uint32_t, 4> kSendGroups{ { 3, 4, 5, 6 } };
        std::uint32_t constexpr kSendEveryMs = 8000;
        std::uint32_t constexpr kWaveGapMs = 10000;
        // The director's poll: sent climbers out of combat and standing (a knockback, an evade home, the path's end)
        // are sent on or set on the tank (rule 19); waiting trolls that start a stock SmartAI walk are stopped.
        std::uint32_t constexpr kPollMs = 500;
        // The wave trolls' corpses (their loot) stay this long.
        std::uint32_t constexpr kCorpseMs = 300000;

        // PY4 Weegli's Barrels: every 15 s normal, 12 s heroic, the first one period after the stage starts; the
        // lane is drawn for 3 s, then the barrel rolls. Players on it: 40% / 50% Fire (the tank row on the tank),
        // Weakened, a 2 s Knockdown (stun). Trolls on it: 50% of their health and knocked down the stair.
        inline constexpr NH<std::uint32_t> kBarrelEveryMs{ 15000, 12000 };
        std::uint32_t constexpr kBarrelWarnMs = 3000;
        static_assert(kBarrelWarnMs >= ZulFarrakRework::kWarningFloorMs, "the lane meets the warning floor");
        inline constexpr NH<float> kBarrelPct{ 40.f, 50.f };
        float constexpr kBarrelTrollPct = 50.f;
        std::uint32_t constexpr kKnockdownMs = 2000;
        // The troll's knock down the stair: away from kKnockSource, kTrollKnockXY yd/s across, kTrollKnockZ up.
        float constexpr kTrollKnockXY = 14.f;
        float constexpr kTrollKnockZ = 6.f;
        // The barrel slides from the lip to the foot at this speed (yd/s) once the lane resolves; gone after the
        // blast.
        float constexpr kBarrelSlideSpeed = 24.f;
        std::uint32_t constexpr kBarrelLifeMs = 10000;
        // The lane's judge: a point on the stair within this much of the stair's slope height.
        float constexpr kLaneZBandYd = 5.f;
        // The lane's tiles: kLaneTiles strips from y kStairLaneYMin to kStairLaneYMax at the stair's true width, each
        // a telegraph-only registry Line (the bots' hazard); four of them draw (section 7 #31 A: four strips up the
        // slope; one wide marker on a 39 degree slope breaks into floating slabs).
        std::size_t constexpr kLaneTiles = 11;
        inline constexpr std::array<std::size_t, 4> kDrawnTiles{ { 1, 4, 7, 10 } };
        float constexpr kTileZToleranceYd = 4.f;

        // The bots' hold (handoff appendix B "Landing hold"): every climber carries a hard-bounds Spot with no spots,
        // so while a climber fights a bot that bot keeps to the landing and the top (strict, every role).
        std::uint32_t constexpr kHoldCarrierMs = 600000;

        // PY6 Berserker: charges a random player 8 to 25 yd away (tank included), first at 4 s, then every 12 to
        // 16 s; normal: a bleed of 2% of the reference row a second for 12 s (the kit's refflat periodic, 200
        // hundredths); heroic: Grievous Wound instead (PyramidFight.h).
        float constexpr kChargeMinYd = 8.f;
        float constexpr kChargeMaxYd = 25.f;
        std::uint32_t constexpr kChargeFirstMs = 4000;
        std::uint32_t constexpr kChargeMinMs = 12000;
        std::uint32_t constexpr kChargeMaxMs = 16000;
        std::uint32_t constexpr kChargeRetryMs = 2000;
        float constexpr kChargeSpeed = 25.f;
        float constexpr kChargeHitYd = 6.f;         // the target this close on arrival takes the bleed / the wound
        std::uint32_t constexpr kChargeTimeoutMs = 3000;
        std::uint32_t constexpr kBleedTickHundredths = 200;
        std::uint32_t constexpr kBleedTickMs = 1000;
        std::uint32_t constexpr kBleedMs = 12000;
        // PY7 heroic Trampling Charge: the path drawn as a 4 yd line 1.5 s ahead; anyone on it but the target takes
        // 30% Physical plus Weakened.
        float constexpr kTramplingWidthYd = 4.f;
        std::uint32_t constexpr kTramplingWarnMs = 1500;
        static_assert(kTramplingWarnMs >= ZulFarrakRework::kWarningFloorMs, "the trample meets the warning floor");
        float constexpr kTramplingPct = 30.f;

        // PY8 Hexmaster: Curse of Blood on a random player (tank included), first at 6 s, then every 15 to 20 s:
        // +10% Physical damage taken for 30 s, a Curse (a reward to cure). Shadow Bolt 9613 as the stock Acolyte
        // (first 0 to 1 s, then every 3 to 4 s), from kCasterRangeYd.
        std::uint32_t constexpr kCurseFirstMs = 6000;
        std::uint32_t constexpr kCurseMinMs = 15000;
        std::uint32_t constexpr kCurseMaxMs = 20000;
        std::uint32_t constexpr kCurseMs = 30000;
        std::int32_t constexpr kCursePhysicalTakenPct = 10;
        float constexpr kCurseRangeYd = 40.f;
        std::uint32_t constexpr kBoltFirstMaxMs = 1000;
        std::uint32_t constexpr kBoltMinMs = 3000;
        std::uint32_t constexpr kBoltMaxMs = 4000;
        float constexpr kCasterRangeYd = 30.f;
        // A Hexmaster or Witch Doctor of waves 1 and 2 (a climber) casts from this close instead: from 30 yd it
        // stopped mid-lane, first in the kill order, where the landing hold keeps every melee bot from reaching it
        // (R-1-B MJ-1). The chase adds both hitboxes (about 3 yd), so it stands about 8 yd from its target: with the
        // target 4 yd or more inside the landing (the crew's spots, DC's hold at y 1271) it stops at the lane's top
        // or on the landing, in melee reach of the hold's mouth, and still in a barrel's reach while its target
        // holds the lip. Wave 3 and Sezz'ziz's adds keep kCasterRangeYd.
        float constexpr kClimberCasterRangeYd = 5.f;
        // PY9 heroic Sandfury Hex in place of the curse: a stack every 4 s; at 5 the player is Hexed (a 2 s frog,
        // Magic) and the curse clears.
        std::uint32_t constexpr kHexStackMs = 4000;
        std::uint32_t constexpr kHexMaxStacks = 5;
        std::uint32_t constexpr kHexedMs = 2000;

        // PY10 Witch Doctor: Flash Heal (stock 17843, 1.5 s) on a troll missing 1,500 or more within 40 yd, every 8
        // to 11 s (stock 5650); Healing Ward (stock 11899) first at 2 s, then every 30 s.
        std::uint32_t constexpr kFlashHealMissing = 1500;
        float constexpr kFlashHealRangeYd = 40.f;
        std::uint32_t constexpr kFlashHealMinMs = 8000;
        std::uint32_t constexpr kFlashHealMaxMs = 11000;
        std::uint32_t constexpr kWardFirstMs = 2000;
        std::uint32_t constexpr kWardEveryMs = 30000;
        // PY11 heroic Lava Spout Totem: first at 10 s, then every 20 s after a 1 s bar; the totem (the stock 6017's
        // look) stands 20 s on the landing; its 8 yd zone burns 6% Fire every 3 s once armed (1.5 s, the warning
        // floor).
        std::uint32_t constexpr kTotemFirstMs = 10000;
        std::uint32_t constexpr kTotemEveryMs = 20000;
        std::uint32_t constexpr kTotemBarMs = 1000;
        std::uint32_t constexpr kTotemLifeMs = 20000;
        std::uint32_t constexpr kTotemArmMs = 1500;
        std::uint32_t constexpr kTotemTickMs = 3000;
        float constexpr kTotemRadiusYd = 8.f;
        float constexpr kTotemPct = 6.f;
        static_assert(kTotemArmMs >= ZulFarrakRework::kWarningFloorMs, "the totem's zone meets the warning floor");
        static_assert(kTotemEveryMs >= kTotemLifeMs, "one totem per Witch Doctor at a time");

        // The crew on the Stair (PY5): kept off the plaza while stage 2 runs (back to their places when they chase
        // below this y).
        float constexpr kCrewLeashY = 1236.f;

        // A sent climber out of combat below the lip that comes no nearer the lip (kStuckProgressYd) for kStuckMs is
        // stuck (a barrel's knockback onto a ledge, a spawn under the ramp with no path out): the first time it goes
        // back to the path's first point and climbs again; the kStuckTries-th time it is removed, so its wave can
        // close (R-1-B MJ-2). The path is run at run speed (waypoint_data 81553 move_type 1): the whole climb takes
        // about 8 s.
        std::uint32_t constexpr kStuckMs = 15000;
        float constexpr kStuckProgressYd = 1.f;
        std::uint32_t constexpr kStuckTries = 2;
    }

    // The range a wave specialist casts from: a climber (waves 1 and 2) from close, every other one from 30 yd.
    constexpr float CasterRange(bool climber)
    {
        return climber ? Tune::kClimberCasterRangeYd : Tune::kCasterRangeYd;
    }

    // The specialists' AI data id: SetData(DATA_STAIR_CLIMBER, 1) marks a wave 1 or 2 troll (the Stair's director).
    std::uint32_t constexpr DATA_STAIR_CLIMBER = 20940;

    // ----------------------------------------------------------------------------------------------------------------
    // The waves (section 3.2 item 11, SP mechanic 4): the stock tables (ZulFarrakRework.h kWaveSpawns) with the
    // Cretins, Acolytes and Zealots replaced by the three specialists: Cretin -> Witch Doctor, Acolyte -> Hexmaster,
    // Zealot -> Berserker. Wave 1 has three Cretins: its Slave at (1883.50, 1218.25) (index 13) becomes the fourth
    // Witch Doctor, so waves 1 and 2 bring 4 + 4 + 4 specialists (SP "Per wave"), the rest fodder (11 and 12). Wave 3's
    // Acolyte is a Hexmaster ("wave 3 and the summons draw from the same three").
    // ----------------------------------------------------------------------------------------------------------------
    std::size_t constexpr kExtraDoctorIndex = 13;

    constexpr std::uint32_t WaveEntry(std::size_t index)
    {
        using namespace ZulFarrakRework;
        if (index >= kWaveSpawns.size())
            return 0;
        if (index == kExtraDoctorIndex)
            return NPC_ZF_SANDFURY_WITCH_DOCTOR;
        switch (kWaveSpawns[index].entry)
        {
            case NPC_SANDFURY_CRETIN:
                return NPC_ZF_SANDFURY_WITCH_DOCTOR;
            case NPC_SANDFURY_ACOLYTE:
                return NPC_ZF_SANDFURY_HEXMASTER;
            case NPC_SANDFURY_ZEALOT:
                return NPC_ZF_SANDFURY_BERSERKER;
            default:
                return kWaveSpawns[index].entry;
        }
    }

    // The indexes of kWaveSpawns that make wave `wave` (1, 2 or 3), in send order (the table's order).
    inline std::vector<std::size_t> WaveIndexes(std::uint32_t wave)
    {
        std::vector<std::size_t> out;
        for (std::size_t i = 0; i < ZulFarrakRework::kWaveSpawns.size(); ++i)
            if (ZulFarrakRework::kWaveSpawns[i].wave == wave)
                out.push_back(i);
        return out;
    }

    constexpr bool IsSpecialist(std::uint32_t entry)
    {
        return entry == ZulFarrakRework::NPC_ZF_SANDFURY_BERSERKER
            || entry == ZulFarrakRework::NPC_ZF_SANDFURY_HEXMASTER
            || entry == ZulFarrakRework::NPC_ZF_SANDFURY_WITCH_DOCTOR;
    }

    // The size of send `sendIndex` (0-based) with `left` trolls of the wave not yet sent: 3, 4, 5, 6, then the rest.
    constexpr std::uint32_t SendGroupSize(std::uint32_t sendIndex, std::uint32_t left)
    {
        if (sendIndex < Tune::kSendGroups.size())
            return std::min(Tune::kSendGroups[sendIndex], left);
        return left;
    }

    // How many sends are due `sinceWaveMs` after the wave began (the first at once, then one every kSendEveryMs).
    constexpr std::uint32_t SendsDue(std::uint32_t sinceWaveMs)
    {
        return sinceWaveMs / Tune::kSendEveryMs + 1;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The barrel lane (PY4, section 3.8, section 7 #31 A): the stair from y kStairLaneYMin (1227) to kStairLaneYMax
    // (1259) at its true width (kStairPolygon's two edges), on its slope (z 13.7 at y 1227 to 40.0 at y 1262); the
    // landing (y 1260 on) is never hit. The side ledges are off the stair's edges.
    // ----------------------------------------------------------------------------------------------------------------
    float constexpr kStairSlopeY0 = 1227.f;
    float constexpr kStairSlopeZ0 = 13.7f;
    float constexpr kStairSlopeY1 = 1262.f;
    float constexpr kStairSlopeZ1 = 40.0f;

    // The stair's floor height at `y` (linear on the run; clamped at both ends).
    constexpr float StairZAt(float y)
    {
        float const t = (std::clamp(y, kStairSlopeY0, kStairSlopeY1) - kStairSlopeY0) / (kStairSlopeY1 - kStairSlopeY0);
        return kStairSlopeZ0 + t * (kStairSlopeZ1 - kStairSlopeZ0);
    }

    // The stair's two edges at a height y (kStairPolygon in ZulFarrakRework.h: its first six points are the low-x
    // edge from the foot up, its last six the high-x edge from the lip down).
    struct StairEdges
    {
        float left;     // the smaller x
        float right;    // the larger x
    };

    constexpr float EdgeAt(std::array<Vec2, 6> const& edge, float y)
    {
        if (y <= edge.front().y)
            return edge.front().x;
        for (std::size_t i = 1; i < edge.size(); ++i)
            if (y <= edge[i].y)
            {
                float const t = (y - edge[i - 1].y) / (edge[i].y - edge[i - 1].y);
                return edge[i - 1].x + t * (edge[i].x - edge[i - 1].x);
            }
        return edge.back().x;
    }

    constexpr StairEdges StairEdgesAt(float y)
    {
        using ZulFarrakRework::kStairPolygon;
        std::array<Vec2, 6> left{};
        std::array<Vec2, 6> right{};
        for (std::size_t i = 0; i < 6; ++i)
        {
            left[i] = kStairPolygon[i];
            right[i] = kStairPolygon[kStairPolygon.size() - 1 - i];
        }
        return { EdgeAt(left, y), EdgeAt(right, y) };
    }

    // On the lane now: on the stair's run between the lane's ends, within its width, near its slope.
    constexpr bool InBarrelLane(float x, float y, float z)
    {
        if (y < ZulFarrakRework::kStairLaneYMin || y > ZulFarrakRework::kStairLaneYMax)
            return false;
        StairEdges const e = StairEdgesAt(y);
        if (x < e.left || x > e.right)
            return false;
        float const dz = z - StairZAt(y);
        return dz >= -Tune::kLaneZBandYd && dz <= Tune::kLaneZBandYd;
    }

    // One tile of the lane: a line along +y from `from` to `to` (each at the slope's height) of `width`, centered on
    // the stair at the tile's foot (the stair narrows going up, so the foot's width covers the whole tile).
    struct LaneTile
    {
        Point3 from;
        Point3 to;
        float width = 0.f;
        bool drawn = false;
    };

    inline std::array<LaneTile, Tune::kLaneTiles> LaneTiles()
    {
        std::array<LaneTile, Tune::kLaneTiles> tiles{};
        float const span = (ZulFarrakRework::kStairLaneYMax - ZulFarrakRework::kStairLaneYMin)
            / float(Tune::kLaneTiles);
        for (std::size_t i = 0; i < Tune::kLaneTiles; ++i)
        {
            float const y0 = ZulFarrakRework::kStairLaneYMin + span * float(i);
            float const y1 = y0 + span;
            StairEdges const e = StairEdgesAt(y0);
            float const cx = (e.left + e.right) / 2.f;
            tiles[i].from = { cx, y0, StairZAt(y0), 0.f };
            tiles[i].to = { cx, y1, StairZAt(y1), 0.f };
            tiles[i].width = e.right - e.left;
            tiles[i].drawn = std::find(Tune::kDrawnTiles.begin(), Tune::kDrawnTiles.end(), i)
                != Tune::kDrawnTiles.end();
        }
        return tiles;
    }

    // Where the barrel is lit (the lip, on the stair's axis) and where it goes off (the foot); bearing 270 (-y) is
    // down the stair.
    float constexpr kDownTheStair = 4.712f;
    Point3 constexpr kBarrelLit{ 1887.5f, 1260.5f, 40.0f, kDownTheStair };
    Point3 constexpr kBarrelFoot{ 1888.0f, 1226.5f, 13.4f, kDownTheStair };
    // The knockback's source for a troll on the lane: up the stair from the lip, so every troll flies downhill.
    Point3 constexpr kKnockSource{ 1887.5f, 1275.0f, 42.0f };
    // The lane stalker (D4a's 301019 entry): the Stair's registry owner and descriptor, at the lip.
    Point3 constexpr kLaneStalker{ 1887.5f, 1262.0f, 41.0f, kDownTheStair };

    constexpr float TrollBarrelDamage(float maxHealth)
    {
        return maxHealth * Tune::kBarrelTrollPct / 100.f;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The bots' hold (handoff appendix B "Landing hold"): the top and the landing (kPyramidTopPolygon) with the stair's
    // mouth pulled back to y 1261, so no hold point is on the lane (it ends at y 1259; the landing starts at y 1260).
    // ----------------------------------------------------------------------------------------------------------------
    float constexpr kHoldMouthY = 1261.f;

    inline std::array<Vec2, ZulFarrakRework::kPyramidTopPolygon.size()> HoldPolygon()
    {
        std::array<Vec2, ZulFarrakRework::kPyramidTopPolygon.size()> out = ZulFarrakRework::kPyramidTopPolygon;
        for (Vec2& p : out)
            if (p.y == 1260.f && p.x > 1880.f && p.x < 1894.f)     // the two mouth points (1880.5 / 1893.5, 1260)
                p.y = kHoldMouthY;
        return out;
    }

    inline DungeonKit::Arena HoldArena()
    {
        return DungeonKit::Arena(ZulFarrakRework::PolygonRegion(HoldPolygon(), ZulFarrakRework::kTopZMin,
            ZulFarrakRework::kTopZMax));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The crew on the Stair (PY5): Bly at the landing's lip (stock: he picks up the leakers), Raven, Oro and Murta back
    // on the landing's platform (SP "Raven, Oro and Murta on the platform"), Weegli at his stock spot by the lip (the
    // barrels are lit there). By CrewMember; nullopt: CR's stock point (kCrewStairPoints).
    // ----------------------------------------------------------------------------------------------------------------
    inline std::array<std::optional<Point3>, ZulFarrakRework::kCrewCount> constexpr kCrewStairSpots{ {
        std::nullopt,                                       // Bly: the stock stair point (1886.96, 1263.49)
        Point3{ 1880.0f, 1270.0f, 42.0f, kDownTheStair },   // Raven
        Point3{ 1885.5f, 1275.5f, 42.0f, kDownTheStair },   // Oro
        std::nullopt,                                       // Weegli: the stock stair point (1890, 1263)
        Point3{ 1891.0f, 1275.0f, 42.0f, kDownTheStair },   // Murta
    } };

    // ----------------------------------------------------------------------------------------------------------------
    // The wave's book-keeping (the stage director's): which trolls of the running wave are waiting, sent, gone.
    // ----------------------------------------------------------------------------------------------------------------
    enum class ClimberState : std::uint8_t
    {
        Waiting,    // on the plaza, not sent yet
        Sent,       // climbing (or fighting)
        Gone,       // dead or despawned
    };

    // The wave is over once none of its trolls is waiting or alive.
    inline bool WaveCleared(std::vector<ClimberState> const& climbers)
    {
        return std::all_of(climbers.begin(), climbers.end(), [](ClimberState s) { return s == ClimberState::Gone; });
    }

    // The trolls the next send takes: the first `n` still waiting, in table order.
    inline std::vector<std::size_t> NextSend(std::vector<ClimberState> const& climbers, std::uint32_t n)
    {
        std::vector<std::size_t> out;
        for (std::size_t i = 0; i < climbers.size() && out.size() < n; ++i)
            if (climbers[i] == ClimberState::Waiting)
                out.push_back(i);
        return out;
    }

    inline std::uint32_t CountWaiting(std::vector<ClimberState> const& climbers)
    {
        return std::uint32_t(std::count(climbers.begin(), climbers.end(), ClimberState::Waiting));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The stuck watch (R-1-B MJ-2): one per sent climber, judged at every poll while it is below the lip.
    // ----------------------------------------------------------------------------------------------------------------
    // The path's first point (waypoint_data 81553 point 1, the stair's foot) and the point "nearer the lip" is
    // measured to (its last point, on the landing; 2D).
    Point3 constexpr kWavePathStart{ 1884.87f, 1228.62f, 9.7f, 1.571f };
    Vec2 constexpr kWavePathEnd{ 1887.53f, 1263.f };

    struct ClimbWatch
    {
        float bestYd = -1.f;            // the nearest it came to the lip since the watch was last reset (-1: unset)
        std::uint32_t sinceMs = 0;      // when it last came nearer
        std::uint32_t strikes = 0;      // times it was found stuck
    };

    enum class ClimbVerdict : std::uint8_t
    {
        Climbing,   // fine (or fighting, or returning home from an evade)
        Return,     // stuck: back to the path's first point, climb again
        Remove,     // stuck again: gone, so its wave can close
    };

    // The watch starts over from where the climber stands now (a send, a return, a knockback).
    inline void ResetClimb(ClimbWatch& w)
    {
        w.bestYd = -1.f;
    }

    // `busy`: in combat, or walking home from an evade (the watch starts over). `distYd`: its 2D distance to
    // kWavePathEnd now.
    inline ClimbVerdict JudgeClimb(ClimbWatch& w, bool busy, float distYd, std::uint32_t nowMs)
    {
        if (busy || w.bestYd < 0.f || distYd < w.bestYd - Tune::kStuckProgressYd)
        {
            w.bestYd = distYd;
            w.sinceMs = nowMs;
            return ClimbVerdict::Climbing;
        }
        if (nowMs - w.sinceMs < Tune::kStuckMs)
            return ClimbVerdict::Climbing;
        ++w.strikes;
        ResetClimb(w);
        return w.strikes >= Tune::kStuckTries ? ClimbVerdict::Remove : ClimbVerdict::Return;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Picks
    // ----------------------------------------------------------------------------------------------------------------

    // PY6: a charge target's distance qualifies (8 to 25 yd).
    constexpr bool ChargeRange(float distance)
    {
        return distance >= Tune::kChargeMinYd && distance <= Tune::kChargeMaxYd;
    }

    // PY9: the Hex turns its carrier into a frog once it reaches its last stack.
    constexpr bool HexTurnsToFrog(std::uint32_t stacks)
    {
        return stacks >= Tune::kHexMaxStacks;
    }

    // PY11: where a Witch Doctor's totem stands on the Stair: at its feet on the landing or the top, else at the lip
    // (SP "drops a totem on the landing").
    Point3 constexpr kTotemLip{ 1887.0f, 1264.5f, 41.6f };
}

#endif
