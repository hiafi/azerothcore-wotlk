/*
 * mod-dungeon-bosses, Scarlet Monastery D8:
 * Arcanist Doan (6487), "Burn in Righteous Fire", the pure, host-testable part (no engine headers). Build spec:
 * docs/dungeons/scarlet-monastery-2-library.md "Arcanist Doan" (DN0-DN4, Build spec), handoff section 3.5 row D8,
 * 3.6, 3.8 (the chamber, NAVMESH), 7 #22 A (the seal). Tested by tests/sm_doan_test.cpp.
 *
 *   Spells     the WP's ids, inside kSpellsDoan (212670-212709), declared in apps/dbc-tools
 *              source/npcs/scarlet_monastery/doan.py
 *   Chamber    the room's floor outline, its center, the anchor spots (the three NAVMESH spots 15 yd out at 120
 *              degrees, a fourth on heroic, then the spots further misses and the hard mode's arrivals take), the
 *              seal across the doorway and the stragglers' entry spot
 *   Tuning     NH<> percents and cadences straight from the build spec (percents of the reference row: N level 35
 *              normal, H level 60 heroic; the hard mode's own numbers are D8H's, through DoanFight.h)
 *   Rules      DN1 the anchors a bubble raises and the patches a miss lays (normal caps), the beats that wait while
 *              the bubble or Overloaded holds him
 *   Beats      the fight's clock: first delay and cadence per mechanic and difficulty
 */

#ifndef MOD_DUNGEON_BOSSES_SM_DOAN_LOGIC_H
#define MOD_DUNGEON_BOSSES_SM_DOAN_LOGIC_H

#include "DungeonKitMath.h"
#include "ScarletMonasteryRework.h"
#include <array>
#include <cstddef>
#include <cstdint>

namespace SmDoan
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using ScarletMonasteryRework::Point3;

    // Every spell of this WP sits in this slice (ScarletMonasteryRework.h; ids.yaml reservation `scarlet_monastery`).
    inline constexpr ScarletMonasteryRework::IdSlice kSpellSlice = ScarletMonasteryRework::kSpellsDoan;

    enum DoanSpells : std::uint32_t
    {
        SPELL_DN_ARCANE_BUBBLE = kSpellSlice.first + 0,  // 212670 DN1 his immunity while the anchors stand
        SPELL_DN_DETONATION_CAST = kSpellSlice.first + 1,  // 212671 DN1 the 10 s bar (Arcane, not interruptible)
        SPELL_DN_DETONATION = kSpellSlice.first + 2,  // 212672 DN1 the blast on a miss (resolve copy, Fire)
        SPELL_DN_ANCHOR_BEAM = kSpellSlice.first + 3,  // 212673 DN1 an anchor's channel into the bubble (a look)
        SPELL_DN_OVERLOADED = kSpellSlice.first + 4,  // 212674 DN1 the reward: +50% damage taken for 10 s
        SPELL_DN_SCORCHED = kSpellSlice.first + 5,  // 212675 DN1a a patch's tick (resolve copy, Fire)
        SPELL_DN_SCORCHED_LOOK = kSpellSlice.first + 6,  // 212676 DN1a a patch's look (an aura on a stalker)
        SPELL_DN_EXPLOSION_CAST = kSpellSlice.first + 7,  // 212677 DN2 the 2 s bar (Arcane, not interruptible)
        SPELL_DN_ARCANE_EXPLOSION = kSpellSlice.first + 8,  // 212678 DN2 the hit (resolve copy, Arcane)
        SPELL_DN_EXPLOSION_LOOK = kSpellSlice.first + 9,  // 212679 DN2 the nova's look on him at the resolve
        SPELL_DN_MARK = kSpellSlice.first + 10,  // 212680 DN3 the 5 s debuff on a marked player (a look)
        SPELL_DN_MARK_BURST = kSpellSlice.first + 11,  // 212681 DN3 the burst on the others (resolve copy, Fire)
        SPELL_DN_MARK_SELF = kSpellSlice.first + 12,  // 212682 DN3 the marked player's own share (resolve, Fire)
        SPELL_DN_MARK_BURST_LOOK = kSpellSlice.first + 13,  // 212683 DN3 the burst's look on a stalker at the spot
        SPELL_DN_POOL = kSpellSlice.first + 14,  // 212684 DN3a a Righteous Fire pool's tick (resolve, Fire)
        SPELL_DN_POOL_LOOK = kSpellSlice.first + 15,  // 212685 DN3a a pool's look (an aura on a stalker)
        SPELL_DN_FLAMESTRIKE = kSpellSlice.first + 16,  // 212686 DN4 the 2.5 s interruptible cast (Fire)
        SPELL_DN_DETONATION_CAST_HEROIC = kSpellSlice.first + 17,  // 212687 DN1 heroic's 14 s bar (HANDOFF s10 D)
        // 212688-212709 spare
    };
    static_assert(SPELL_DN_DETONATION_CAST_HEROIC <= kSpellSlice.last, "Doan's spells must stay in his slice");

    // Registry tags (the build spec's mechanic numbers; the failure ledger and the playtest greps key on them).
    enum DoanTags : std::uint32_t
    {
        TAG_DN_DETONATION   = 1,    // DN1 a completed Detonation (group failure)
        TAG_DN_EXPLOSION    = 2,    // DN2 Arcane Explosion
        TAG_DN_MARK         = 3,    // DN3 a Mark's burst (and the marked player's own share)
        TAG_DN_SCORCHED     = 11,   // DN1a a Scorched patch
        TAG_DN_POOL         = 31,   // DN3a a Righteous Fire pool
    };

    // creature_text groups of 6487. 0-1 are the stock rows; 2-3 are D8H's (the Heresy's zone yell, HM5); 4-5 are this
    // WP's (data/sql/updates/pending_db_world/rev_doan_scarlet_monastery.sql).
    enum DoanTexts : std::uint8_t
    {
        SAY_AGGRO           = 0,    // yell (stock): "You will not defile these mysteries!"
        SAY_BUBBLE          = 1,    // yell (stock, now every bubble): "Burn in righteous fire!"
        SAY_HERESY          = 2,    // D8H: the fourth page read (zone yell)
        SAY_RISE_PURGED     = 3,    // D8H: HM5 the Risen Purged
        EMOTE_SEAL          = 4,    // boss emote: the chamber seals (DN0, the SealedArena's close)
        EMOTE_OVERLOADED    = 5,    // boss emote: the bubble shatters (DN1 broken)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The chamber (section 3.8, NAVMESH "Doan": x 130-166, y -409 to -449, 1,164 sq yd; compass +x north, +y west)
    // ----------------------------------------------------------------------------------------------------------------

    // The chamber's center (NAVMESH: r 15.0 clear there; P2 stands on it).
    inline constexpr Point3 kChamberCenter{ 144.2f, -429.2f, 18.5f };

    // The chamber floor's outline, about 1.5 yd inside its walls (the navmesh map at 2 yd resolution; about 990 sq
    // yd): the bots' drop spots and every registry spot of the fight keep inside it (rule 12). Clockwise in (x, y).
    inline constexpr std::array<Vec2, 8> kChamberOutline{ {
        { 133.f, -418.f }, { 138.f, -413.f }, { 160.f, -413.f }, { 164.f, -416.f },
        { 164.f, -443.f }, { 160.f, -446.f }, { 138.f, -446.f }, { 133.f, -441.f },
    } };
    inline constexpr float kChamberZMin = 15.f;
    inline constexpr float kChamberZMax = 24.f;

    // A point inside the outline (convex, clockwise: right of or on every edge).
    constexpr bool InChamberOutline(Vec2 p)
    {
        for (std::size_t i = 0; i < kChamberOutline.size(); ++i)
        {
            Vec2 const a = kChamberOutline[i];
            Vec2 const b = kChamberOutline[(i + 1) % kChamberOutline.size()];
            float const cross = (b.x - a.x) * (p.y - a.y) - (b.y - a.y) * (p.x - a.x);
            if (cross > 0.f)
                return false;
        }
        return true;
    }

    // DN1 the anchor spots: the first three are the NAVMESH spots 15 yd out at 120 degrees round his spawn (bearings
    // 90, 210 and 330 degrees, measured from +x toward +y); the fourth (heroic) and two more fill the 15 yd ring
    // between them (270, 30, 150 degrees); then an inner ring of six at 9 yd (0, 60, ... 300 degrees) for the spots
    // further misses and the hard mode's Risen Purged call for. A bubble takes them in this order.
    inline constexpr std::uint32_t kAnchorSpotCount = 12;
    inline constexpr std::array<Point3, kAnchorSpotCount> kAnchorSpots{ {
        { 148.3f, -413.7f, 18.5f }, { 135.3f, -436.2f, 18.5f }, { 161.3f, -436.2f, 18.5f },     // 90, 210, 330
        { 148.3f, -443.7f, 18.5f }, { 161.3f, -421.2f, 18.5f }, { 135.3f, -421.2f, 18.5f },     // 270, 30, 150
        { 157.3f, -428.7f, 18.5f }, { 152.8f, -420.9f, 18.5f }, { 143.8f, -420.9f, 18.5f },     // 0, 60, 120
        { 139.3f, -428.7f, 18.5f }, { 143.8f, -436.5f, 18.5f }, { 152.8f, -436.5f, 18.5f },     // 180, 240, 300
    } };
    inline constexpr float kAnchorRingYd = 15.f;
    inline constexpr float kAnchorInnerRingYd = 9.f;

    // DN0 the Chamber Seal (section 7 #22 A, NAVMESH misfit 6): the doorway to the outer hall is a 1.5-2.8 yd gap, 3
    // yd long, at x 169-172, its middle y -429.3 (the two Scarlet Monks outside stand at y -427.5 and -430.9). The seal
    // object (301319, GODI 523 RazorfenForceField01: 0.6 x 9.5 x 9.2 yd at size 1) stands across it at size 0.42,
    // about 4 yd wide and tall, facing north (its wide side runs along y). Stragglers land on the entry spot, 5 yd
    // inside, facing into the chamber.
    inline constexpr Point3 kSealSpot{ 170.3f, -429.3f, 18.55f };
    inline constexpr float kSealFacing = 0.f;
    inline constexpr float kSealSize = 0.42f;
    inline constexpr std::uint32_t kSealDisplay = 523;
    inline constexpr Point3 kSealEntry{ 165.f, -429.3f, 18.5f };
    inline constexpr float kSealEntryFacing = 3.14159265f;     // south: into the chamber

    // ----------------------------------------------------------------------------------------------------------------
    // The beats (Build spec "First, cooldown", normal / heroic; the hard mode's are D8H's overrides)
    // ----------------------------------------------------------------------------------------------------------------

    struct Beat
    {
        std::uint32_t firstMs;
        std::uint32_t everyMs;
    };

    inline constexpr NH<Beat> kBubbleBeat{ { 20000, 35000 }, { 20000, 30000 } };      // DN1
    inline constexpr NH<Beat> kExplosionBeat{ { 8000, 12000 }, { 8000, 12000 } };     // DN2
    inline constexpr NH<Beat> kMarkBeat{ { 15000, 20000 }, { 15000, 20000 } };        // DN3
    inline constexpr Beat kFlamestrikeBeat{ 10000, 15000 };                            // DN4 (heroic only)
    inline constexpr std::uint32_t kFlamestrikeRetryMs = 1000;      // DN4 after a refused cast (a silence, a lockout)

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (Build spec "Mechanics"; percents of the reference row: N level 35, H level 60)
    // ----------------------------------------------------------------------------------------------------------------

    // DN1 Burn in Righteous Fire: the bubble, the anchors and a 10 s Detonation. All anchors broken before the bar
    // ends: Overloaded for 10 s (+50% damage taken, no casts). The bar completes: the blast to every player in the
    // chamber (75%; heroic 130%, lethal on purpose, hub ruling 28), two Scorched patches and one more anchor next time
    // (normal caps: 5 anchors, 4 patches; heroic none).
    inline constexpr std::uint32_t kDetonationCastMs = 10000;
    // Heroic's bar is 14 s on its own bar spell (212687, the same look): the orchestrator's balance default, D8
    // designer question 1 option D (HANDOFF s10, 2026-11-20, pending the user's confirmation). Revert: 10000 here and
    // DetonationBarSpellFor back to 212671 on both (the 14 s spell can stay declared, unused).
    inline constexpr std::uint32_t kDetonationCastMsHeroic = 14000;
    constexpr std::uint32_t DetonationCastMsFor(bool heroic)
    {
        return heroic ? kDetonationCastMsHeroic : kDetonationCastMs;
    }
    // The bar spell whose DBC cast time is DetonationCastMsFor(heroic): the bar players read and the script's clock
    // agree.
    constexpr std::uint32_t DetonationBarSpellFor(bool heroic)
    {
        return heroic ? SPELL_DN_DETONATION_CAST_HEROIC : SPELL_DN_DETONATION_CAST;
    }
    inline constexpr NH<float> kDetonationPct{ 75.f, 130.f };
    inline constexpr NH<std::uint32_t> kAnchorsBase{ 3, 4 };
    inline constexpr NH<std::uint32_t> kAnchorCap{ 5, 0 };          // 0 = no cap
    inline constexpr std::uint32_t kPatchesPerMiss = 2;
    inline constexpr NH<std::uint32_t> kPatchCap{ 4, 0 };           // 0 = no cap
    inline constexpr std::uint32_t kOverloadedMs = 10000;
    inline constexpr float kOverloadedDamageTakenPct = 50.f;

    // DN1a Scorched: a 5 yd patch for the rest of the fight, 6% (heroic 10%) Fire a second; lingering, no Weakened.
    // Placed on a random floor spot of the chamber, off the anchor spots and the other patches.
    inline constexpr float kScorchedRadiusYd = 5.f;
    inline constexpr std::uint32_t kScorchedTickMs = 1000;
    inline constexpr NH<float> kScorchedPct{ 6.f, 10.f };
    inline constexpr std::uint32_t kLingerForeverMs = 20u * 60u * 1000u;   // longer than any fight; Cleanup cancels it
    inline constexpr float kScorchedMinRangeYd = 3.f;      // from the chamber's center
    inline constexpr float kScorchedMaxRangeYd = 14.f;
    inline constexpr float kScorchedAnchorMarginYd = 2.f;  // a patch's edge this far from an anchor spot
    inline constexpr float kScorchedApartYd = 10.f;        // patch centers at least this far apart

    // DN2 Arcane Explosion: a 2 s bar, then 10 yd round him, 30% (heroic 45%) Arcane and Weakened, the tank included.
    inline constexpr std::uint32_t kExplosionCastMs = 2000;
    inline constexpr float kExplosionRadiusYd = 10.f;
    inline constexpr NH<float> kExplosionPct{ 30.f, 45.f };

    // DN3 Mark of Righteous Fire: 2 (heroic 3) players, never the tank, marked 5 s; each bursts for 8 yd where they
    // stand: 15% (heroic 20%) Fire to the marked player, 35% (heroic 45%) and Weakened to anyone else inside.
    inline constexpr NH<std::uint32_t> kMarkCount{ 2, 3 };
    inline constexpr std::uint32_t kMarkMs = 5000;
    inline constexpr float kMarkRadiusYd = 8.f;
    inline constexpr NH<float> kMarkOthersPct{ 35.f, 45.f };
    inline constexpr NH<float> kMarkSelfPct{ 15.f, 20.f };

    // DN3a Righteous Fire pool (heroic): 3 yd at each burst, forming 1 s after it, 30 s, 10% Fire a second (lingering).
    inline constexpr float kPoolRadiusYd = 3.f;
    inline constexpr std::uint32_t kPoolFormMs = 1000;
    inline constexpr std::uint32_t kPoolLifeMs = 30000;
    inline constexpr std::uint32_t kPoolTickMs = 1000;
    inline constexpr float kPoolPct = 10.f;

    // DN4 Righteous Flamestrike (heroic): a 2.5 s interruptible cast; missed, 40% Fire to every player (the spell's own
    // effect, the kit's percent script). On the interrupt list (expected).
    inline constexpr std::uint32_t kFlamestrikeCastMs = 2500;
    inline constexpr float kFlamestrikePct = 40.f;
    // The cast has not taken yet this long after the call (UpdateFlamestrike waits before calling it done).
    inline constexpr std::uint32_t kCastStartGraceMs = 250;

    // The look stalkers outlive their zone by this much (the aura's last frame); the burst's look stands this long.
    inline constexpr std::uint32_t kLookTailMs = 1000;
    inline constexpr std::uint32_t kBurstLookMs = 2000;

    // ----------------------------------------------------------------------------------------------------------------
    // Rules
    // ----------------------------------------------------------------------------------------------------------------

    // DN1: the anchors a bubble raises: the base count (3, heroic 4), one more per earlier miss and per extra the
    // hard mode adds (HM5's arrivals), held at the normal cap of 5 and at the spots there are.
    constexpr std::uint32_t AnchorCount(bool heroic, std::uint32_t misses, std::uint32_t extra)
    {
        std::uint32_t n = kAnchorsBase(heroic) + misses + extra;
        std::uint32_t const cap = kAnchorCap(heroic);
        if (cap && n > cap)
            n = cap;
        return n > kAnchorSpotCount ? kAnchorSpotCount : n;
    }

    // DN1a: the patches a miss lays when `laid` already burn (2, held at the normal cap of 4).
    constexpr std::uint32_t PatchesToLay(bool heroic, std::uint32_t laid)
    {
        std::uint32_t const cap = kPatchCap(heroic);
        if (!cap)
            return kPatchesPerMiss;
        if (laid >= cap)
            return 0;
        return cap - laid < kPatchesPerMiss ? cap - laid : kPatchesPerMiss;
    }

    // The bubble and Overloaded hold his other beats (Explosion, Mark, Flamestrike: "never during the bubble"; "he
    // stops casting" while Overloaded). A held beat stays due and fires once the hold ends.
    constexpr bool BeatsHeld(bool bubble, bool overloaded)
    {
        return bubble || overloaded;
    }

    // DN1: the bubble breaks when no anchor of it stands (the hard mode's shard counts as one).
    constexpr bool BubbleBroken(std::uint32_t anchorsRaised, std::uint32_t anchorsStanding)
    {
        return anchorsRaised > 0 && anchorsStanding == 0;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Rule 20: the anchor window against the group's damage (Build spec "Tuning"; bots do about half of it)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kEffectiveDpsNormal = 666;      // level 35
    inline constexpr std::uint32_t kEffectiveDpsHeroic = 3145;
    inline constexpr std::uint32_t kBotAddDpsHeroic = 700;         // LESSONS 4.2: a 3-DPS bot group on adds at 60
    inline constexpr std::uint32_t kDoanHealthNormal = 46000;
    inline constexpr std::uint32_t kDoanHealthHeroic = 230000;
    // The anchors' health (the templates': doan.py normal, H's heroic table; the host and DT tests pin both). The
    // spec's 1.7k / 8k were cut by the orchestrator's balance default (HANDOFF s10, D8 question 1 option D, 2026-11-20,
    // pending the user's confirmation; revert: 1700 / 8000 here, in doan.py and in H's table): normal 3 x 1.2k = 3.6k
    // in the 10 s bar, heroic 4 x 5k = 20k in the 14 s bar.
    inline constexpr std::uint32_t kAnchorHealthNormal = 1200;
    inline constexpr std::uint32_t kAnchorHealthHeroic = 5000;

    // Seconds of `dps` to break a first bubble's anchors (no walking between them counted).
    constexpr float AnchorSeconds(bool heroic, std::uint32_t dps)
    {
        return dps ? static_cast<float>(kAnchorsBase(heroic) * (heroic ? kAnchorHealthHeroic : kAnchorHealthNormal))
            / static_cast<float>(dps) : 0.f;
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
