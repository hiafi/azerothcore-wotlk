/*
 * mod-dungeon-bosses, Scarlet Monastery D1:
 * Interrogator Vishas (3983), the pure, host-testable part (no engine headers). Build spec:
 * docs/dungeons/scarlet-monastery-1-graveyard.md "Interrogator Vishas" (VI1-VI4), handoff section 3.5 row D1, 3.6
 * (40k normal, 280k heroic), 3.8 (his H-shaped hall), 3.10 (VR). Tested by tests/sm_vishas_test.cpp.
 *
 *   Spells         the WP's ids, inside kSpellsVishas (212320-212349), declared in apps/dbc-tools
 *                  source/npcs/scarlet_monastery/vishas.py
 *   Tuning         NH<> percents and cadences, straight from the build spec (percents of the reference row)
 *   Phases         1 to 70%, 2 to 30%, 3 to 0% (exactly at 70 / 30%: one step at a time, never skipped)
 *   Interrogation  VI1 a RunOut: a 1.5 s bar, a 6 s debuff, an accomplice pulse every 2 s (three)
 *   Branding Iron  VI2 a 90 degree, 15 yd cone fixed at the bar's start, toward a random player's spot
 *   Pain           VI3 the own copy of Shadow Word: Pain (Magic, the dispel reward)
 *   Torment        VI4 (heroic) the split line Soak: 20% of the non-tank row a second, shared by everyone on it
 *   Beats          the fight's clock: first delay and cadence per mechanic and phase
 *   Floor          the hall's floor bounds for the bots and the two heroic carrier discs (NAVMESH-REPORT, Graveyard)
 */

#ifndef MOD_DUNGEON_BOSSES_SM_VISHAS_LOGIC_H
#define MOD_DUNGEON_BOSSES_SM_VISHAS_LOGIC_H

#include "DungeonKitLogic.h"
#include "DungeonKitMath.h"
#include "ScarletMonasteryRework.h"
#include <array>
#include <cstdint>
#include <utility>
#include <vector>

namespace SmVishas
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (ScarletMonasteryRework.h; ids.yaml reservation `scarlet_monastery`).
    inline constexpr ScarletMonasteryRework::IdSlice kSpellSlice = ScarletMonasteryRework::kSpellsVishas;

    enum VishasSpells : std::uint32_t
    {
        SPELL_VI_INTERROGATION_CAST = kSpellSlice.first + 0,    // 212320 VI1 the 1.5 s bar
        SPELL_VI_INTERROGATION      = kSpellSlice.first + 1,    // 212321 VI1 the 6 s debuff, 4% a second (healer work)
        SPELL_VI_ACCOMPLICE         = kSpellSlice.first + 2,    // 212322 VI1 the pulse on an accomplice (resolve copy)
        SPELL_VI_BRANDING_IRON_CAST = kSpellSlice.first + 3,    // 212323 VI2 the 2 s bar
        SPELL_VI_BRANDING_IRON      = kSpellSlice.first + 4,    // 212324 VI2 the cone's hit (resolve copy, Fire)
        SPELL_VI_PAIN               = kSpellSlice.first + 5,    // 212325 VI3 the copy of Shadow Word: Pain 2767
        SPELL_VI_TORMENT            = kSpellSlice.first + 6,    // 212326 VI4 the channeled beam (heroic)
        SPELL_VI_TORMENT_SHARE      = kSpellSlice.first + 7,    // 212327 VI4 one share of a second's tick
        // 212328-212349 spare
    };
    static_assert(SPELL_VI_TORMENT_SHARE <= kSpellSlice.last, "Vishas's spells must stay in his slice");

    // Stock spell of 3983 retired from the kit (GY "Stock kit"): Shadow Word: Pain 2767 carries a live spell_dbc
    // player override (the priest rework), so his Pain is a copy in the slice (rule 15). Never cast by the rework.
    inline constexpr std::uint32_t SPELL_STOCK_SHADOW_WORD_PAIN = 2767;

    // His stock weapon "Monster - Hot Iron Poker" (creature_equip_template 3983 has it in both hands): he starts
    // unarmed and takes one into the main hand at the 70% yell (VR, handoff section 3.10; _visuals.py
    // ITEM_VISHAS_WEAPON).
    inline constexpr std::uint32_t kItemHotIronPoker = 5532;

    // Registry tags (the build spec's mechanic numbers; the failure ledger, the drills and the playtest greps key on
    // them). VI3 Pain is a plain spell (no registry mechanic).
    enum VishasTags : std::uint32_t
    {
        VI1 = 1,    // Interrogation (RunOut, accomplice pulses)
        VI2 = 2,    // Branding Iron (cone Zone)
        VI4 = 4,    // Torment (split line Soak, heroic)
    };

    // creature_text groups 3983 (0-3 stock, 4-6 data/sql/updates/pending_db_world/rev_vishas_scarlet_monastery.sql).
    enum VishasTexts : std::uint8_t
    {
        SAY_PULL            = 0,    // yell: "Tell me... tell me everything!" (stock)
        SAY_HOT_IRONS       = 1,    // yell: "Naughty secrets!" (stock, moved to exactly 70%)
        SAY_RIP_SECRETS     = 2,    // yell: "I'll rip the secrets from your flesh!" (stock, moved to exactly 30%)
        SAY_KILL            = 3,    // yell: "Purged by pain!" (stock, a kill)
        EMOTE_CONFESSION    = 4,    // emote: "%s demands a confession from $n!" (VI1)
        EMOTE_IRONS         = 5,    // emote: "%s takes a branding iron from the coals." (phase 2)
        EMOTE_TORMENT       = 6,    // emote: "%s turns his torments on $n!" (VI4, heroic)
    };
    // Vorrel Sengutz 3981 says his stock line 0 when Vishas dies (SmartAI 3983 row 5, dropped by S0's rev).
    inline constexpr std::uint8_t SAY_VORREL_DEATH = 0;
    inline constexpr float kVorrelRange = 100.f;
    // The stock kill line's lockout (SmartAI 3983 row 1: 5 s).
    inline constexpr std::uint32_t kKillYellGapMs = 5000;

    // ----------------------------------------------------------------------------------------------------------------
    // Phases (GY "Phases"): 1 The Question to 70%, 2 Hot Irons to 30%, 3 Rip the Secrets to 0%
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kPhase2Pct = 70.f;
    inline constexpr float kPhase3Pct = 30.f;

    // The phase his health (percent) calls for.
    constexpr std::uint32_t PhaseFor(float healthPct)
    {
        if (healthPct <= kPhase3Pct)
            return 3;
        if (healthPct <= kPhase2Pct)
            return 2;
        return 1;
    }

    // The next phase to run from `current` at `healthPct` (one step at a time: a hit from above 70 to under 30 runs
    // phase 2's yell and iron, then phase 3's), or `current` when none is due.
    constexpr std::uint32_t NextPhase(std::uint32_t current, float healthPct)
    {
        return PhaseFor(healthPct) > current ? current + 1 : current;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VI1 Interrogation: a random non-tank (the tank is the carried-spread exemption); heroic phase 3: two
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kInterrogationCastMs = 1500;
    inline constexpr std::uint32_t kInterrogationMs = 6000;             // the debuff
    inline constexpr std::uint32_t kInterrogationTickMs = 1000;
    inline constexpr NH<float> kInterrogationPct{ 4.f, 4.f };          // the target, a second (healer work)
    inline constexpr float kAccompliceRadius = 8.f;
    inline constexpr std::uint32_t kAccomplicePulseMs = 2000;
    inline constexpr std::uint32_t kAccomplicePulses = kInterrogationMs / kAccomplicePulseMs;
    inline constexpr NH<float> kAccomplicePct{ 12.f, 20.f };           // each accomplice, a pulse; no Weakened (L7)
    static_assert(kAccomplicePulses == 3, "a pulse every 2 s over the 6 s debuff");

    // The RunOut's warning: the bar, then the first pulse 2 s into the debuff.
    constexpr std::uint32_t AccompliceWarnMs()
    {
        return kInterrogationCastMs + kAccomplicePulseMs;
    }

    // The RunOut's Persistent window: a pass at its resolve and one every pulse after it (the registry's pass clock
    // takes a pass while it is before `until`), so the last pass lands as the debuff ends and the ring goes 1 ms later.
    constexpr std::uint32_t AccomplicePersistMs()
    {
        return (kAccomplicePulses - 1) * kAccomplicePulseMs + 1;
    }

    // The passes of a Persistent window (BM Judge::TakePass: a pass at 0, then one every `tick` while < `persistMs`).
    constexpr std::uint32_t PassesIn(std::uint32_t persistMs, std::uint32_t tickMs)
    {
        if (!tickMs)
            return 1;
        std::uint32_t passes = 1;
        for (std::uint32_t at = tickMs; at < persistMs; at += tickMs)
            ++passes;
        return passes;
    }
    static_assert(PassesIn(AccomplicePersistMs(), kAccomplicePulseMs) == kAccomplicePulses, "three pulses");
    static_assert(AccompliceWarnMs() + AccomplicePersistMs() - 1 == kInterrogationCastMs + kInterrogationMs,
        "the last pulse lands as the debuff ends");

    // How many players he interrogates at once: one; two in heroic phase 3 (who keep 8 yd from each other too).
    constexpr std::uint32_t InterrogationCount(bool heroic, std::uint32_t phase)
    {
        return heroic && phase >= 3 ? 2 : 1;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VI2 Branding Iron: from 70%; a random player, the tank included
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kBrandCastMs = 2000;
    inline constexpr float kBrandAngleDeg = 90.f;
    inline constexpr float kBrandLength = 15.f;
    inline constexpr NH<float> kBrandPct{ 35.f, 45.f };                // plus Weakened, every difficulty

    // The cone's facing: from Vishas toward the picked player's spot at the bar's start; his own facing when the
    // player stands on him.
    inline float BrandFacing(Vec2 vishas, Vec2 target, float ownFacing)
    {
        if (DungeonKit::Distance(vishas, target) < 0.5f)
            return ownFacing;
        return DungeonKit::BearingTo(vishas, target);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VI3 Pain: a random player, the tank included; 18 s, a tick every 3 s; Magic (a dispel is the reward)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kPainMs = 18000;
    inline constexpr std::uint32_t kPainTickMs = 3000;
    inline constexpr NH<float> kPainPct{ 2.f, 4.f };
    inline constexpr std::uint32_t kPainFirstMinMs = 3000;
    inline constexpr std::uint32_t kPainFirstMaxMs = 7000;
    inline constexpr std::uint32_t kPainEveryMinMs = 10000;
    inline constexpr std::uint32_t kPainEveryMaxMs = 14000;

    // ----------------------------------------------------------------------------------------------------------------
    // VI4 Torment (heroic): a beam from Vishas to a random player (TormentRule); everyone else available soaks
    // ----------------------------------------------------------------------------------------------------------------

    // The registration (SM-BM's F2 example, which G1's `torment` drill row mirrors): a line Soak from him to the
    // target, 3 yd wide, a 1.5 s warning, then 8 s of passes a second; the target backs off 10 yd when it is the tank
    // (EndBacksOff), the tank soaks in the first 4 yd (TankNearSource); no MissedSoak (the split is the cost).
    inline constexpr float kTormentWidth = 3.f;
    inline constexpr std::uint32_t kTormentWarnMs = 1500;
    inline constexpr std::uint32_t kTormentMs = 8000;
    inline constexpr std::uint32_t kTormentTickMs = 1000;
    inline constexpr float kTormentBackOffYd = 10.f;
    inline constexpr float kTormentTankNearYd = 4.f;
    // Each second, 20% of the non-tank row split evenly among every player on the line, the target included.
    inline constexpr NH<float> kTormentTickPct{ 20.f, 20.f };
    inline constexpr std::uint32_t kTormentTicks = kTormentMs / kTormentTickMs;
    static_assert(PassesIn(kTormentMs, kTormentTickMs) == kTormentTicks, "eight ticks of a second");

    // The beam's pick (R-1-GY MN-4): any player, the tank included, but not a live Interrogation carrier (the line's
    // soakers would stand in the carrier's 8 yd ring). The script picks with the carriers excluded first and, when
    // nobody else qualifies, again with TormentRule({}).
    inline DungeonKit::PickRule TormentRule(std::vector<std::uint64_t> carriers)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;       // the tank included
        rule.exclude = std::move(carriers);
        return rule;
    }

    // The beam (his channel) lasts the warning and the 8 ticks: he stands still and does not melee meanwhile.
    constexpr std::uint32_t TormentChannelMs()
    {
        return kTormentWarnMs + kTormentMs;
    }

    // A player's percent of the row a tick with `onLine` players on the line (the target counts).
    constexpr float TormentSharePct(std::uint32_t onLine, bool heroic)
    {
        return onLine ? kTormentTickPct(heroic) / static_cast<float>(onLine) : 0.f;
    }

    // A player's percent over the whole channel.
    constexpr float TormentTotalPct(std::uint32_t onLine, bool heroic)
    {
        return TormentSharePct(onLine, heroic) * static_cast<float>(kTormentTicks);
    }
    static_assert(TormentTotalPct(1, true) >= 100.f, "alone the target dies (hub ruling 12)");
    static_assert(TormentTotalPct(3, true) < 60.f, "the target, the tank and one more: about 53% each");

    // ----------------------------------------------------------------------------------------------------------------
    // The beats (GY "Build spec" first / cooldown)
    // ----------------------------------------------------------------------------------------------------------------

    struct Beat
    {
        std::uint32_t firstMs;
        std::uint32_t everyMs;
        std::uint32_t everyPhase3Ms;
    };

    inline constexpr Beat kInterrogationBeat{ 6000, 18000, 14000 };    // VI1 from the pull
    inline constexpr Beat kBrandBeat{ 3000, 12000, 10000 };            // VI2 from the 70% yell
    inline constexpr Beat kTormentBeat{ 10000, 25000, 25000 };         // VI4 heroic, from the pull

    constexpr std::uint32_t Cadence(Beat const& beat, std::uint32_t phase)
    {
        return phase >= 3 ? beat.everyPhase3Ms : beat.everyMs;
    }

    // A repeating beat on the AI's own ms clock (start to start); a beat that cannot fire yet (a cast, the Torment
    // channel) stays due.
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

        // A shorter cadence starts (phase 3): a beat due later than `everyMs` from now comes at `everyMs`.
        void Shorten(std::uint64_t nowMs, std::uint32_t everyMs)
        {
            if (_on && _dueMs > nowMs + everyMs)
                _dueMs = nowMs + everyMs;
        }

    private:
        bool _on = false;
        std::uint64_t _dueMs = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The hall (NAVMESH-REPORT "Graveyard / Vishas": an H-shaped hall, box x 1740-1800, y 1098-1162, z 7-9.6)
    // ----------------------------------------------------------------------------------------------------------------

    struct FloorRect
    {
        float minX;
        float maxX;
        float minY;
        float maxY;

        constexpr bool Contains(Vec2 p) const { return p.x >= minX && p.x <= maxX && p.y >= minY && p.y <= maxY; }
        // A disc of `r` round `p` fits inside.
        constexpr bool ContainsDisc(Vec2 p, float r) const
        {
            return p.x - r >= minX && p.x + r <= maxX && p.y - r >= minY && p.y + r <= maxY;
        }
    };

    // The bots' hard bounds (BM Within): the two chambers of the hall (navmesh/maps.txt "Vishas torture chamber"),
    // north (his, x 1771-1797) and south (x 1743-1771), y 1107-1155. Inside the arena box; the corridors out of the
    // hall (west y 1160-1172, east y 1090-1106) are left out.
    inline constexpr std::array<FloorRect, 2> kFloor{ {
        { 1771.f, 1797.f, 1107.f, 1155.f },
        { 1743.f, 1771.f, 1107.f, 1155.f },
    } };
    inline constexpr float kFloorZMin = 5.f;
    inline constexpr float kFloorZMax = 12.f;

    constexpr bool OnFloor(Vec2 p)
    {
        for (FloorRect const& r : kFloor)
            if (r.Contains(p))
                return true;
        return false;
    }

    // The two free 8 yd discs that take the heroic phase 3 carriers (NM: r 8.8 and r 8.3, 33 yd apart).
    inline constexpr std::array<Vec2, 2> kCarrierDiscs{ { { 1758.2f, 1120.8f }, { 1782.8f, 1143.2f } } };
    inline constexpr std::array<float, 2> kCarrierDiscRadii{ { 8.8f, 8.3f } };
    // NM: the longest free line in the hall (Torment's beam fits up to here).
    inline constexpr float kLongestFreeLine = 37.5f;
}

#endif
