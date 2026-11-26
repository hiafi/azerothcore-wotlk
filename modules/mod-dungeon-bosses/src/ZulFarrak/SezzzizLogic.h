/*
 * mod-dungeon-bosses, Zul'Farrak D4b: the Altar (stage 3 of the Pyramid) with Shadowpriest Sezz'ziz (7275) and Nekrum
 * Gutchewer (7796), the pure, host-testable part (no engine headers). The spell ids of the Altar's half of the Stair's
 * slice (from ZfStair::kAltarSpellBase), the registry tags, the text, the tuning (`namespace Tune`, handoff section 3.5
 * rule 32), the add sets and their cap, the Blood Offering's picks and numbers, the Altar's arena (the plaza, the
 * ramp's foot and the stair) and the test actions. Build spec: SP 1346-1432 (PY12-PY16), design SP 1180-1281 (rulings
 * 21-23, 46); handoff section 3.5 row D4b and its kick table, sections 3.6, 3.8 (the plaza), section 7 #11 A, #20 A,
 * #44 A. Tested by tests/zf_stair_test.cpp. Health is ZulFarrakRework.h Health: never restated here.
 *
 * Mirrored stock code (AGENTS.md credit rule): Sezz'ziz's four add sets cycled in order and their two points are
 * npc_shadowpriest_sezziz's (zulfarrak.cpp; the points as df82d1be9 jrad7 <106174524+jrad7@users.noreply.github.com>
 * corrected them, #26183; the script 048025ceb UltraNix <80540499+UltraNix@users.noreply.github.com>), re-implemented
 * with the specialists in place of the Zealots and Acolytes and a cap of four alive (SP "Sezz'ziz: adds").
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_SEZZZIZ_LOGIC_H
#define MOD_DUNGEON_BOSSES_ZF_SEZZZIZ_LOGIC_H

#include "DungeonKitMath.h"
#include "StairLogic.h"
#include "ZulFarrakRework.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>

namespace ZfAltar
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using ZulFarrakRework::Point3;

    // Every spell of this WP sits in this slice (ZulFarrakRework.h; ids.yaml reservation `zul_farrak`), shared with
    // StairLogic.h: the Altar's ids start at ZfStair::kAltarSpellBase.
    inline constexpr ZulFarrakRework::IdSlice kSpellSlice = ZulFarrakRework::kSpellsStair;

    // Declared in apps/dbc-tools source/npcs/zul_farrak/pyramid_stair.py (same ids).
    enum AltarSpells : std::uint32_t
    {
        SPELL_BLOOD_OFFERING        = ZfStair::kAltarSpellBase + 0,     // PY12 normal: the 3 s cast (Fire, kickable)
        SPELL_BLOOD_OFFERING_H      = ZfStair::kAltarSpellBase + 1,     // PY12 heroic: the 2 s cast
        SPELL_BLOOD_OFFERING_HIT    = ZfStair::kAltarSpellBase + 2,     // PY12 a player offered: resolve copy (Shadow)
        SPELL_BLOOD_FRENZY          = ZfStair::kAltarSpellBase + 3,     // PY12 normal: +50% damage done, 15 s
        SPELL_BLOOD_FRENZY_H        = ZfStair::kAltarSpellBase + 4,     // PY12 heroic: +50% a stack, no end, no cap
        SPELL_SCREAM_BAR            = ZfStair::kAltarSpellBase + 5,     // PY13 the 2 s bar (Physical, not kickable)
        SPELL_SCREAM_FEAR           = ZfStair::kAltarSpellBase + 6,     // PY13 the rider: a 2 s fear (Magic)
        SPELL_BLOOD_OFFERING_BEAM   = ZfStair::kAltarSpellBase + 7,     // PY12 the red beam (SV 7270): a channel
                                                                        // field on him while the bar runs, never cast
        // ZfStair::kAltarSpellBase + 8 .. kSpellSlice.last: spare
    };
    static_assert(kSpellSlice.Contains(SPELL_BLOOD_OFFERING) && kSpellSlice.Contains(SPELL_BLOOD_OFFERING_BEAM),
        "the Altar's spells sit in the slice");

    // Stock spells cast as they are (SP "Stock kit": Keep).
    std::uint32_t constexpr SPELL_SHADOW_BOLT = 15537;      // Sezz'ziz (Shadow, kickable: a kick's reward)
    std::uint32_t constexpr SPELL_HAMSTRING = 26141;        // Nekrum
    std::uint32_t constexpr SPELL_BERSERKER_CHARGE = 19471; // Nekrum, on aggro

    // Registry tags (the build spec's PY numbers).
    enum AltarTags : std::uint32_t
    {
        TAG_OFFERING_HIT    = 12,   // PY12 a player offered (the kit's RegistryHit)
        TAG_SCREAM          = 13,   // PY13 the 8 yd circle
    };

    // Texts (creature_text 7275, new: the SQL rev): the emote as Blood Offering starts.
    enum AltarTexts : std::uint8_t
    {
        EMOTE_BLOOD_OFFERING = 0,   // "%s offers $n's blood to the loa!" (type 41)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SP Build spec 1346-1432 PY12-PY15 and "Tuning starting points"; section 7 #44 A; rule 32)
    // ----------------------------------------------------------------------------------------------------------------
    namespace Tune
    {
        // PY12 Blood Offering: first at 6 s, then every 15 to 18 s; a 3 s cast (heroic 2 s) on a surviving crew
        // fighter, else a random player (tank included). Landed on the crew: that member dies (CR's KillCrew). On a
        // player: 25% Shadow (the tank row on the tank). Either way he heals 15% (heroic 25%) of his health and gains
        // Blood Frenzy: normal +50% damage done for 15 s; heroic +50% a stack, no end, no cap (ruling 46; the
        // "+100% 15 s" of the old tuning table is stale, handoff section 8 #9).
        std::uint32_t constexpr kOfferingFirstMs = 6000;
        std::uint32_t constexpr kOfferingMinMs = 15000;
        std::uint32_t constexpr kOfferingMaxMs = 18000;
        inline constexpr NH<std::uint32_t> kOfferingCastMs{ 3000, 2000 };
        static_assert(kOfferingCastMs.heroic >= ZulFarrakRework::kWarningFloorMs, "the Offering meets the floor");
        float constexpr kOfferingRangeYd = 40.f;
        float constexpr kOfferingPlayerPct = 25.f;
        inline constexpr NH<float> kOfferingHealPct{ 15.f, 25.f };
        std::int32_t constexpr kFrenzyPct = 50;
        std::uint32_t constexpr kFrenzyMs = 15000;
        std::uint32_t constexpr kFrenzyStackLimit = 255;

        // PY13 Psychic Scream: first at 10 s, then every 22 to 30 s; a 2 s bar (Physical school: his kickable Shadow
        // Bolt locks Shadow, rule 24) with the 8 yd circle drawn on him; a 2 s fear (Magic) on everyone inside.
        std::uint32_t constexpr kScreamFirstMs = 10000;
        std::uint32_t constexpr kScreamMinMs = 22000;
        std::uint32_t constexpr kScreamMaxMs = 30000;
        std::uint32_t constexpr kScreamCastMs = 2000;
        static_assert(kScreamCastMs >= ZulFarrakRework::kWarningFloorMs, "the Scream meets the warning floor");
        float constexpr kScreamRadiusYd = 8.f;
        std::uint32_t constexpr kFearMs = 2000;

        // PY14 his adds: first at 12 s, then every 10 to 14 s, the stock four sets in turn, at most 4 alive.
        std::uint32_t constexpr kAddsFirstMs = 12000;
        std::uint32_t constexpr kAddsMinMs = 10000;
        std::uint32_t constexpr kAddsMaxMs = 14000;
        std::uint32_t constexpr kAddsCap = 4;

        // PY15 Sezz'ziz: Shadow Bolt 15537 (3 s cast) every 3 to 4 s, first at 1 to 3 s, cast from kCasterRangeYd (the
        // stock AttackStartCaster(40), kept inside the spell's own range).
        std::uint32_t constexpr kBoltFirstMinMs = 1000;
        std::uint32_t constexpr kBoltFirstMaxMs = 3000;
        std::uint32_t constexpr kBoltMinMs = 3000;
        std::uint32_t constexpr kBoltMaxMs = 4000;
        float constexpr kCasterRangeYd = 30.f;

        // PY15 Nekrum: Berserker Charge 19471 on aggro; Hamstring 26141 first at 0 to 16 s, then every 12 to 20 s;
        // heroic Gutchew every 15 s: his bite leaves Grievous Wound on his target (PyramidFight.h).
        std::uint32_t constexpr kHamstringFirstMaxMs = 16000;
        std::uint32_t constexpr kHamstringMinMs = 12000;
        std::uint32_t constexpr kHamstringMaxMs = 20000;
        std::uint32_t constexpr kGutchewEveryMs = 15000;

        // The Altar's director: every kLinkPollMs an Altar unit out of combat joins any of its fellows that fights
        // (Sezz'ziz's stock CallAssistance, the whole Altar as one pull).
        std::uint32_t constexpr kLinkPollMs = 500;
        float constexpr kLinkRangeYd = 80.f;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // PY14 Sezz'ziz's adds: the stock npc_shadowpriest_sezziz sets in turn (Zealot -> Berserker, Acolyte ->
    // Hexmaster), at kSezzzizAddPoints[0] (A, 1874.12, 1198.90) or [1] (B, 1895.26, 1199.09).
    // ----------------------------------------------------------------------------------------------------------------
    struct AddSlot
    {
        std::uint32_t entry = 0;
        std::uint8_t point = 0;     // index in kSezzzizAddPoints
    };

    struct AddSet
    {
        std::array<AddSlot, 4> slots{};
        std::uint8_t size = 0;
    };

    inline constexpr std::array<AddSet, 4> kAddSets{ {
        { { { { ZulFarrakRework::NPC_ZF_SANDFURY_BERSERKER, 0 }, { ZulFarrakRework::NPC_ZF_SANDFURY_HEXMASTER, 0 },
            {}, {} } }, 2 },
        { { { { ZulFarrakRework::NPC_ZF_SANDFURY_HEXMASTER, 1 }, { ZulFarrakRework::NPC_ZF_SANDFURY_HEXMASTER, 1 },
            {}, {} } }, 2 },
        { { { { ZulFarrakRework::NPC_ZF_SANDFURY_BERSERKER, 0 }, { ZulFarrakRework::NPC_ZF_SANDFURY_HEXMASTER, 1 },
            { ZulFarrakRework::NPC_ZF_SANDFURY_HEXMASTER, 1 }, {} } }, 3 },
        { { { { ZulFarrakRework::NPC_ZF_SANDFURY_BERSERKER, 1 }, { ZulFarrakRework::NPC_ZF_SANDFURY_BERSERKER, 0 },
            { ZulFarrakRework::NPC_ZF_SANDFURY_HEXMASTER, 0 }, { ZulFarrakRework::NPC_ZF_SANDFURY_HEXMASTER, 1 } } },
            4 },
    } };

    constexpr AddSet const& AddSetFor(std::uint32_t call)
    {
        return kAddSets[call % kAddSets.size()];
    }

    // How many of a set of `setSize` come now with `alive` of his adds still alive (at most kAddsCap alive).
    constexpr std::uint32_t AddsToSummon(std::uint32_t setSize, std::uint32_t alive)
    {
        if (alive >= Tune::kAddsCap)
            return 0;
        return std::min(setSize, Tune::kAddsCap - alive);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // PY12 Blood Offering
    // ----------------------------------------------------------------------------------------------------------------

    // The crew member offered: one of `candidates` (CrewMember bits: alive, an Ally fighter, in reach; never Weegli,
    // whom CR refuses), `roll` a uniform random number. nullopt: none (he offers a player instead).
    constexpr std::optional<std::uint32_t> PickOfferingCrew(std::uint32_t candidates, std::uint32_t roll)
    {
        candidates &= ZulFarrakRework::kCrewFighters;
        std::uint32_t count = 0;
        for (std::uint32_t m = 0; m < ZulFarrakRework::kCrewCount; ++m)
            if (candidates & ZulFarrakRework::CrewBit(m))
                ++count;
        if (!count)
            return std::nullopt;
        std::uint32_t pick = roll % count;
        for (std::uint32_t m = 0; m < ZulFarrakRework::kCrewCount; ++m)
            if (candidates & ZulFarrakRework::CrewBit(m))
            {
                if (!pick)
                    return m;
                --pick;
            }
        return std::nullopt;
    }

    // The health a landed Offering gives back (of his maximum, rounded down).
    constexpr std::uint32_t OfferingHeal(std::uint32_t maxHealth, bool heroic)
    {
        return std::uint32_t(float(maxHealth) * Tune::kOfferingHealPct.Get(heroic) / 100.f);
    }

    // Heroic Blood Frenzy: the damage done of `stacks` stacks (no cap; the aura shows at most kFrenzyStackLimit).
    constexpr std::int32_t FrenzyDamagePct(std::uint32_t stacks)
    {
        return std::int32_t(stacks) * Tune::kFrenzyPct;
    }

    constexpr std::uint32_t FrenzyShownStacks(std::uint32_t stacks)
    {
        return std::min(stacks, Tune::kFrenzyStackLimit);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Altar's arena: the plaza (PlazaArena), the ramp's foot between the plaza's cut and the stair's z band (x
    // 1872-1904, y 1219-1230: three wave 3 trolls and the crew's descent points stand there) and the stair itself, so
    // the fight may spill up the stair as far as its lip without a leash firing.
    // ----------------------------------------------------------------------------------------------------------------
    inline std::array<Vec2, 4> constexpr kRampFootPolygon{ {
        { 1872.f, 1219.f }, { 1904.f, 1219.f }, { 1904.f, 1230.f }, { 1872.f, 1230.f },
    } };
    float constexpr kRampFootZMin = 6.5f;
    float constexpr kRampFootZMax = 20.f;

    inline DungeonKit::Arena AltarArena()
    {
        DungeonKit::Arena arena = ZulFarrakRework::PlazaArena();
        arena.Add(ZulFarrakRework::PolygonRegion(kRampFootPolygon, kRampFootZMin, kRampFootZMax));
        arena.Add(ZulFarrakRework::PolygonRegion(ZulFarrakRework::kStairPolygon, ZulFarrakRework::kStairZMin,
            ZulFarrakRework::kStairZMax));
        return arena;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest zf stair` (pyramid_stair_rework.cpp) reaches Sezz'ziz's and Nekrum's AIs through DoAction / GetData.
    // ----------------------------------------------------------------------------------------------------------------
    enum AltarTestActions : std::int32_t
    {
        ACTION_TEST_OFFERING    = 20951,    // Sezz'ziz: a Blood Offering now
        ACTION_TEST_SCREAM      = 20952,    // Sezz'ziz: a Psychic Scream now
        ACTION_TEST_ADDS        = 20953,    // Sezz'ziz: the next add set now
        ACTION_TEST_GUTCHEW     = 20954,    // Nekrum: Gutchew now (heroic)
    };

    enum AltarTestData : std::uint32_t
    {
        DATA_TEST_ENGAGED   = 20961,    // 1 in combat
        DATA_TEST_ADDS      = 20962,    // his adds alive
        DATA_TEST_FRENZY    = 20963,    // Blood Frenzy stacks (heroic total; normal 0 / 1)
        DATA_TEST_OFFERINGS = 20964,    // Offerings landed this pull
        DATA_TEST_CALLS     = 20965,    // add calls this pull
    };
}

#endif
