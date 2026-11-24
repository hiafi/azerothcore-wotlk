/*
 * mod-dungeon-bosses, Scarlet Monastery D6:
 * Ambrose Kell, the Antiquarian (300910), the pure, host-testable part (no engine headers). Build spec:
 * docs/dungeons/scarlet-monastery-2-library.md "Ambrose Kell, the Antiquarian" (AN1-AN5c, Build spec), handoff section
 * 3.5 row D6, 3.6, 3.8 (the long hall), 7 #25 A (the cases). Tested by tests/sm_kell_test.cpp.
 *
 *   Spells     the WP's ids, inside kSpellsKell (212570-212609), declared in apps/dbc-tools
 *              source/npcs/scarlet_monastery/kell.py
 *   Cases      AN1 the six cases (section 7 #25 A: three in the west bays, three on the east side), the nearest sealed
 *              one wakes; the cloud's center, the staff's three bearings
 *   Tuning     NH<> percents and cadences straight from the build spec (percents of the reference row: N level 34
 *              normal, H level 60 heroic)
 *   Rules      AN4 the skeleton cap (4 alive on normal, none on heroic); AN5 the Trophy Power of a relic type
 *   Beats      the fight's clock: first delay and cadence per mechanic and difficulty
 */

#ifndef MOD_DUNGEON_BOSSES_SM_KELL_LOGIC_H
#define MOD_DUNGEON_BOSSES_SM_KELL_LOGIC_H

#include "DungeonKitMath.h"
#include "ScarletMonasteryRework.h"
#include <array>
#include <cmath>
#include <cstdint>

namespace SmKell
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using ScarletMonasteryRework::Point3;

    // Every spell of this WP sits in this slice (ScarletMonasteryRework.h; ids.yaml reservation `scarlet_monastery`).
    inline constexpr ScarletMonasteryRework::IdSlice kSpellSlice = ScarletMonasteryRework::kSpellsKell;

    // The binding switch (S0): flipped with this WP's declaration of Kell 300910 (kell.py and its rev).
    inline constexpr bool kBound = true;

    enum KellSpells : std::uint32_t
    {
        SPELL_AN_UNSEAL_CAST = kSpellSlice.first + 0,  // 212570 AN1 the 2 s cast bar (Physical, not interruptible)
        SPELL_AN_UNSEAL_SHATTER = kSpellSlice.first + 1,  // 212571 AN1 the shatter's look on the case's trigger
        SPELL_AN_PLAGUE_CLOUD = kSpellSlice.first + 2,  // 212572 AN2 the cloud's tick (resolve copy, Nature)
        SPELL_AN_PLAGUE_CLOUD_LOOK = kSpellSlice.first + 3,  // 212573 AN2 the cloud's look (an aura on a trigger)
        SPELL_AN_ARCANE_LINE = kSpellSlice.first + 4,  // 212574 AN3 a staff line's hit (resolve copy, Arcane)
        SPELL_AN_ARCANE_LINE_LOOK = kSpellSlice.first + 5,  // 212575 AN3 the missile along a line (from the trigger)
        SPELL_AN_RAISE_SKELETON_LOOK = kSpellSlice.first + 6,  // 212576 AN4 the climb-out look on the trigger
        SPELL_AN_GILDED_CANE = kSpellSlice.first + 7,  // 212577 the tank hit (20% / 30%, Physical)
        SPELL_AN_PLAGUE_FLASK = kSpellSlice.first + 8,  // 212578 AN5a the landing's hit (resolve copy, Nature)
        SPELL_AN_PLAGUE_FLASK_POOL = kSpellSlice.first + 9,  // 212579 AN5a the pool's tick (resolve copy, Nature)
        SPELL_AN_PLAGUE_FLASK_THROW = kSpellSlice.first + 10,  // 212580 AN5a the vial's flight (a look at the spot)
        SPELL_AN_PLAGUE_FLASK_POOL_LOOK = kSpellSlice.first + 11,  // 212581 AN5a the pool's look (an aura on a trigger)
        SPELL_AN_ARCANE_TORRENT = kSpellSlice.first + 12,  // 212582 AN5b the interruptible 3 s cast, group damage
        SPELL_AN_BONE_CURSE = kSpellSlice.first + 13,  // 212583 AN5c the Magic debuff, 8 s
        SPELL_AN_BONE_BURST = kSpellSlice.first + 14,  // 212584 AN5c the burst on the cursed player
        SPELL_AN_TROPHY_CASK = kSpellSlice.first + 15,  // 212585 AN5 Kell's look after the first cask
        SPELL_AN_TROPHY_STAFF = kSpellSlice.first + 16,  // 212586 AN5 Kell's look after the first staff
        SPELL_AN_TROPHY_SKULL = kSpellSlice.first + 17,  // 212587 AN5 Kell's look after the first skull
        // 212588-212609 spare
    };
    static_assert(SPELL_AN_TROPHY_SKULL <= kSpellSlice.last, "Kell's spells must stay in his slice");

    // Registry tags (the build spec's mechanic numbers; the failure ledger and the playtest greps key on them).
    enum KellTags : std::uint32_t
    {
        TAG_AN_CLOUD        = 2,    // AN2 a Plague Cask cloud
        TAG_AN_STAFF_LINE   = 3,    // AN3 a Kirin Tor Staff line
        TAG_AN_FLASK        = 51,   // AN5a a Plague Flask landing
        TAG_AN_FLASK_POOL   = 52,   // AN5a a Plague Flask pool
    };

    // creature_text groups of 300910 (data/sql/updates/pending_db_world/rev_kell_scarlet_monastery.sql, LIB "Text").
    enum KellTexts : std::uint8_t
    {
        SAY_PULL            = 0,    // yell: "Hands off the collection!"
        EMOTE_UNSEAL_CASK   = 1,    // boss emote: "%s unseals the Plague Cask!"
        EMOTE_UNSEAL_STAFF  = 2,    // boss emote: "%s unseals the Kirin Tor Staff!"
        EMOTE_UNSEAL_SKULL  = 3,    // boss emote: "%s unseals the Necromancer's Skull!"
        SAY_TROPHY          = 4,    // yell (heroic, each Trophy Power): "Yes... I hear it now. Its power is mine!"
        EMOTE_TORRENT       = 5,    // boss emote (heroic): "%s begins to channel the staff's power!"
        SAY_DEATH           = 6,    // yell: "The collection... must be... preserved..."
    };

    // ----------------------------------------------------------------------------------------------------------------
    // AN1 the six cases (section 7 #25 A; the layout table of LIB "New mechanics" 1, NAVMESH floor z)
    // ----------------------------------------------------------------------------------------------------------------

    enum class Relic : std::uint8_t
    {
        Cask,
        Staff,
        Skull,
    };

    struct CaseSpot
    {
        Relic relic;
        Point3 spot;        // the pedestal's foot (the hall floor under it)
        bool west;          // the west bays (y about -311) face -y; the east side (y about -340) faces +y
    };

    inline constexpr std::uint32_t kCaseCount = 6;

    // West (y about -311), south to north: Cask, Staff, Skull; east (y about -340), south to north: Skull, Cask, Staff.
    // Compass follows the game's axes (+x north, +y west). The east north end (265, -340) is the 6 yd passage to the
    // reading hall: a staff case, nothing on the floor there (the staff's lines go out of it, the passage stays open).
    inline constexpr std::array<CaseSpot, kCaseCount> kCases{ {
        { Relic::Cask,  { 222.0f, -311.0f, 18.7f }, true },
        { Relic::Staff, { 243.0f, -311.0f, 20.8f }, true },
        { Relic::Skull, { 265.0f, -311.0f, 20.8f }, true },
        { Relic::Skull, { 221.8f, -340.3f, 19.3f }, false },
        { Relic::Cask,  { 243.0f, -340.0f, 18.7f }, false },
        { Relic::Staff, { 265.0f, -340.0f, 19.7f }, false },
    } };

    // Two of each type (the layout table): a second case of a type adds nothing to Kell's Trophy Powers.
    constexpr std::uint32_t CountOf(Relic relic)
    {
        std::uint32_t n = 0;
        for (CaseSpot const& c : kCases)
            n += c.relic == relic ? 1u : 0u;
        return n;
    }
    static_assert(CountOf(Relic::Cask) == 2 && CountOf(Relic::Staff) == 2 && CountOf(Relic::Skull) == 2,
        "two of each relic");

    // The relic on its pedestal sits on top of it (Battlemaster Pedestal GODI 7695, VR: 1.9 x 1.9 x 1.2 yd).
    inline constexpr float kPedestalHeightYd = 1.2f;

    // The objects (GO templates of rev_kell_scarlet_monastery.sql; the displays equal the template rows, tested and
    // re-applied at the summon: one C++ constant is the swap if a look is wrong in game).
    inline constexpr std::uint32_t kPedestalDisplay = 7695;     // BattlemasterPedestal (never Karazhan's 7273)
    inline constexpr std::uint32_t kCaskDisplay = 288;          // Barrel02
    inline constexpr std::uint32_t kStaffDisplay = 1708;        // BrambleStaff (alternate 2455 HumanStaff02)
    inline constexpr std::uint32_t kSkullDisplay = 217;         // BattleGladeSkullHumanDark (alternate 226)

    constexpr std::uint32_t RelicDisplay(Relic relic)
    {
        return relic == Relic::Cask ? kCaskDisplay : relic == Relic::Staff ? kStaffDisplay : kSkullDisplay;
    }

    // The facing of a case: west cases face the aisle (-y), east cases face it (+y).
    inline constexpr float kFaceWest = 4.71238898f;     // 3 pi / 2: towards -y
    inline constexpr float kFaceEast = 1.57079633f;     // pi / 2: towards +y

    constexpr float CaseFacing(CaseSpot const& c)
    {
        return c.west ? kFaceWest : kFaceEast;
    }

    // The aisle's middle line (NAVMESH: the aisle strip y -322 to -341, 15 to 21 yd wide).
    inline constexpr float kAisleY = -331.5f;

    // ----------------------------------------------------------------------------------------------------------------
    // Wake rules
    // ----------------------------------------------------------------------------------------------------------------

    // The sealed case nearest `from` (the plane), the lowest index on a tie; -1 when every case is awake.
    inline int NearestSealed(std::uint32_t wokenMask, Vec2 from)
    {
        int best = -1;
        float bestSq = 0.f;
        for (std::uint32_t i = 0; i < kCaseCount; ++i)
        {
            if (wokenMask & (1u << i))
                continue;
            float const dx = kCases[i].spot.x - from.x;
            float const dy = kCases[i].spot.y - from.y;
            float const sq = dx * dx + dy * dy;
            if (best < 0 || sq < bestSq - 1e-4f)
            {
                best = static_cast<int>(i);
                bestSq = sq;
            }
        }
        return best;
    }

    constexpr std::uint32_t AllWokenMask()
    {
        return (1u << kCaseCount) - 1u;
    }

    // The emote naming the relic (AN1).
    constexpr std::uint8_t UnsealEmote(Relic relic)
    {
        return relic == Relic::Cask ? EMOTE_UNSEAL_CASK : relic == Relic::Staff ? EMOTE_UNSEAL_STAFF
            : EMOTE_UNSEAL_SKULL;
    }

    // AN5: the Trophy Power aura of a relic type (Kell's look).
    constexpr std::uint32_t TrophySpell(Relic relic)
    {
        return relic == Relic::Cask ? SPELL_AN_TROPHY_CASK : relic == Relic::Staff ? SPELL_AN_TROPHY_STAFF
            : SPELL_AN_TROPHY_SKULL;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The beats (Build spec "First, cooldown", normal / heroic)
    // ----------------------------------------------------------------------------------------------------------------

    struct Beat
    {
        std::uint32_t firstMs;
        std::uint32_t everyMs;
    };

    inline constexpr NH<Beat> kUnsealBeat{ { 10000, 20000 }, { 8000, 15000 } };     // AN1 (about 4 woken on normal)
    inline constexpr NH<Beat> kStaffBeat{ { 2000, 8000 }, { 2000, 8000 } };         // AN3 after the staff's wake
    inline constexpr NH<Beat> kSkullBeat{ { 2000, 12000 }, { 2000, 12000 } };       // AN4 after the skull's wake
    inline constexpr NH<Beat> kCaneBeat{ { 5000, 10000 }, { 5000, 10000 } };        // Gilded Cane (the tank hit)
    inline constexpr std::uint32_t kFlaskEveryMs = 12000;       // AN5a from the first cask's wake (heroic)
    inline constexpr std::uint32_t kTorrentEveryMs = 15000;     // AN5b from the first staff's wake (heroic)
    inline constexpr std::uint32_t kTorrentRetryMs = 1000;      // AN5b after a refused cast (a silence, a lockout)
    inline constexpr std::uint32_t kCurseEveryMs = 15000;       // AN5c from the first skull's wake (heroic)

    // AN1 Unseal: a 2 s cast naming the relic; the case wakes when it ends.
    inline constexpr std::uint32_t kUnsealCastMs = 2000;

    // Case `i` (0-based) starts its Unseal at this ms into the fight if the cadence holds.
    constexpr std::uint32_t UnsealStartMs(std::uint32_t i, bool heroic)
    {
        Beat const b = kUnsealBeat(heroic);
        return b.firstMs + i * b.everyMs;
    }

    // Cases awake by `ms` into the fight (a wake lands kUnsealCastMs after its start).
    constexpr std::uint32_t CasesWokenBy(std::uint32_t ms, bool heroic)
    {
        std::uint32_t n = 0;
        while (n < kCaseCount && UnsealStartMs(n, heroic) + kUnsealCastMs <= ms)
            ++n;
        return n;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (Build spec "Mechanics"; percents of the reference row: N level 34, H level 60)
    // ----------------------------------------------------------------------------------------------------------------

    // AN2 Plague Cask: a poison cloud of 8 yd round the bay's mouth (the case spot moved 4 yd toward the aisle), a tick
    // a second to anyone in it, for the rest of the fight; lingering, no Weakened.
    inline constexpr float kCloudRadiusYd = 8.f;
    inline constexpr float kCloudOffsetYd = 4.f;
    inline constexpr std::uint32_t kCloudTickMs = 1000;
    inline constexpr std::uint32_t kCloudLifeMs = 20u * 60u * 1000u;    // longer than any fight; Cleanup cancels it
    inline constexpr NH<float> kCloudPct{ 6.f, 10.f };

    // AN3 Kirin Tor Staff: three lines of 4 yd by 40 yd from the case at random angles across the hall, a 2 s marker,
    // 35% (heroic 45%) Arcane and Weakened.
    inline constexpr std::uint32_t kLinesPerStaff = 3;
    inline constexpr float kLineWidthYd = 4.f;
    inline constexpr float kLineLengthYd = 40.f;
    inline constexpr std::uint32_t kLineWarnMs = 2000;
    inline constexpr NH<float> kLinePct{ 35.f, 45.f };
    // The bearings fan out of the case into the hall: within this many degrees of the inward direction, at least
    // kLineMinGapDeg apart.
    inline constexpr float kLineSpreadDeg = 70.f;
    inline constexpr float kLineMinGapDeg = 22.f;

    // AN4 Necromancer's Skull: a Gallery Skeleton every 12 s; normal holds at 4 alive (the skull waits), heroic never.
    inline constexpr NH<std::uint32_t> kSkeletonCap{ 4, 0 };    // 0 = no cap
    // The skeleton goes for the tank when it is this close to the case (rule 19: arrivals pick the tank first), else
    // for the nearest player.
    inline constexpr float kSkeletonTankSeekYd = 45.f;
    // The threat a skeleton puts on its first target before it attacks: everyone else is on its list at 0, so without
    // it the first threat update picks an arbitrary player (as Loksey's and Hollis Grey's adds).
    inline constexpr float kSkeletonOpeningThreat = 10.f;
    // The skull retries this long after a refusal at the cap.
    inline constexpr std::uint32_t kSkullRetryMs = 1000;
    // The summon's corpse lingers this long.
    inline constexpr std::uint32_t kSkeletonCorpseMs = 8000;

    // Gilded Cane: his swing on his victim, 20% (heroic 30%) of the tank row.
    inline constexpr NH<float> kCanePct{ 20.f, 30.f };

    // AN5a Plague Flask (heroic): a 4 yd marker at a random player's spot (the tank included), 2 s flight, 40% Nature
    // and Weakened; then a 15 s pool of 8% a second (lingering, no Weakened).
    inline constexpr float kFlaskRadiusYd = 4.f;
    inline constexpr std::uint32_t kFlaskFlightMs = 2000;
    inline constexpr float kFlaskPct = 40.f;
    inline constexpr std::uint32_t kPoolMs = 15000;
    inline constexpr std::uint32_t kPoolTickMs = 1000;
    inline constexpr float kPoolPct = 8.f;

    // AN5b Arcane Torrent (heroic): a 3 s interruptible cast; missed, 40% Arcane to every player (the spell's own
    // effect, kit percent script). The emote names it.
    inline constexpr std::uint32_t kTorrentCastMs = 3000;
    inline constexpr float kTorrentPct = 40.f;
    // The cast has not taken yet this long after the call (UpdateTorrent waits before calling it done).
    inline constexpr std::uint32_t kTorrentStartGraceMs = 250;

    // AN5c Bone Curse (heroic): a Magic debuff on a random player (the tank included) for 8 s; undispelled, a 25%
    // Physical burst on them and a Gallery Skeleton rises from them.
    inline constexpr std::uint32_t kCurseMs = 8000;
    inline constexpr float kBurstPct = 25.f;

    // The fight's length (Build spec "Tuning": effective group DPS 623 N / 3,145 H; the bots do about half of it).
    inline constexpr std::uint32_t kEffectiveDpsNormal = 623;
    inline constexpr std::uint32_t kEffectiveDpsHeroic = 3145;
    inline constexpr std::uint32_t kKellHealthNormal = 44000;
    inline constexpr std::uint32_t kKellHealthHeroic = 240000;
    inline constexpr std::uint32_t kSkeletonHealthNormal = 1200;
    inline constexpr std::uint32_t kSkeletonHealthHeroic = 6000;
    inline constexpr std::uint32_t kSkeletonsInFightNormal = 4;
    inline constexpr std::uint32_t kSkeletonsInFightHeroic = 8;

    constexpr float FightSeconds(bool heroic)
    {
        return heroic
            ? static_cast<float>(kKellHealthHeroic + kSkeletonsInFightHeroic * kSkeletonHealthHeroic)
                / static_cast<float>(kEffectiveDpsHeroic)
            : static_cast<float>(kKellHealthNormal + kSkeletonsInFightNormal * kSkeletonHealthNormal)
                / static_cast<float>(kEffectiveDpsNormal);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Pure picks
    // ----------------------------------------------------------------------------------------------------------------

    // AN2: the cloud's center, the case spot moved kCloudOffsetYd toward the aisle (west cases -y, east cases +y).
    constexpr Vec2 CloudCenter(CaseSpot const& c)
    {
        return { c.spot.x, c.spot.y + (c.west ? -kCloudOffsetYd : kCloudOffsetYd) };
    }

    // AN3: the bearing straight out of a case into the hall (radians; +x north, +y west: the direction is
    // (cos, sin)).
    constexpr float InwardBearing(CaseSpot const& c)
    {
        return CaseFacing(c);
    }

    // AN3: `kLinesPerStaff` bearings within kLineSpreadDeg of the inward bearing, at least kLineMinGapDeg apart.
    // `rand01()` returns [0, 1). After 64 refused tries the fan is the even one (-45, 0, +45 degrees).
    template <class Rand>
    std::array<float, kLinesPerStaff> LineBearings(CaseSpot const& c, Rand&& rand01)
    {
        constexpr float kDeg = 3.14159265358979f / 180.f;
        float const inward = InwardBearing(c);
        std::array<float, kLinesPerStaff> offsetsDeg{};
        for (int attempt = 0; attempt < 64; ++attempt)
        {
            bool ok = true;
            for (std::uint32_t i = 0; i < kLinesPerStaff && ok; ++i)
            {
                float const o = (rand01() * 2.f - 1.f) * kLineSpreadDeg;
                for (std::uint32_t j = 0; j < i; ++j)
                    if (std::fabs(o - offsetsDeg[j]) < kLineMinGapDeg)
                        ok = false;
                offsetsDeg[i] = o;
            }
            if (ok)
            {
                std::array<float, kLinesPerStaff> out{};
                for (std::uint32_t i = 0; i < kLinesPerStaff; ++i)
                    out[i] = inward + offsetsDeg[i] * kDeg;
                return out;
            }
        }
        return { inward - 45.f * kDeg, inward, inward + 45.f * kDeg };
    }

    // AN4: a skull may raise a skeleton when `live` stand below the cap (heroic: always).
    constexpr bool SkeletonMayRise(std::uint32_t live, bool heroic)
    {
        std::uint32_t const cap = kSkeletonCap(heroic);
        return cap == 0 || live < cap;
    }

    // AN4: the skeleton goes for the tank (a player holding Kell) when it is within kSkeletonTankSeekYd of the case.
    constexpr bool SkeletonSeeksTank(bool haveTank, float distToCaseYd)
    {
        return haveTank && distToCaseYd <= kSkeletonTankSeekYd;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The AI's own clock
    // ----------------------------------------------------------------------------------------------------------------

    // A repeating beat on the AI's own ms clock (start to start); a beat that cannot fire yet stays due.
    class BeatClock
    {
    public:
        void Start(std::uint64_t nowMs, std::uint32_t inMs)
        {
            _on = true;
            _dueMs = nowMs + inMs;
        }

        void Stop() { _on = false; }
        bool On() const { return _on; }
        std::uint64_t DueMs() const { return _dueMs; }

        bool Due(std::uint64_t nowMs) const { return _on && nowMs >= _dueMs; }

        // It fired: the next one is `everyMs` after this one's due time, never in the past.
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
