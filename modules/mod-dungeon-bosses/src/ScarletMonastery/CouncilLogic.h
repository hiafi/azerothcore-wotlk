/*
 * mod-dungeon-bosses, Scarlet Monastery D3: Azshir the Sleepless (6490) and the Fallen Champion (6488), the council,
 * the pure, host-testable part (no engine headers). Build spec: docs/dungeons/scarlet-monastery-1-graveyard.md
 * "Azshir and the Fallen Champion rework" (CV1-CV8), handoff section 3.5 row D3, section 3.6, section 3.8 row D3 and
 * section 7 #18 A (the council fights on the lawn, Azshir 3 yd behind the Champion). Tested by
 * tests/sm_council_test.cpp; the spell ids and numbers are pinned against apps/dbc-tools
 * source/npcs/scarlet_monastery/council.py by lib/test_scarlet_monastery_council.py.
 */

#ifndef MOD_DUNGEON_BOSSES_SM_COUNCIL_LOGIC_H
#define MOD_DUNGEON_BOSSES_SM_COUNCIL_LOGIC_H

#include "ScarletMonasteryRework.h"
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace SmCouncil
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (ScarletMonasteryRework.h; ids.yaml reservation `scarlet_monastery`).
    inline constexpr ScarletMonasteryRework::IdSlice kSpellSlice = ScarletMonasteryRework::kSpellsCouncil;

    enum CouncilSpells : std::uint32_t
    {
        SPELL_CV_HOLY_SHOCK             = kSpellSlice.first + 0,    // CV2 the hit (percent by script)
        SPELL_CV_HOLY_LIGHT             = kSpellSlice.first + 1,    // CV3 the 2.5 s heal (interruptible)
        SPELL_CV_HOLY_WRATH_CAST        = kSpellSlice.first + 2,    // CV4 the 2 s bar (Physical: never locked)
        SPELL_CV_HOLY_WRATH             = kSpellSlice.first + 3,    // CV4 the ring's hit (resolve copy, Holy)
        SPELL_CV_HOLY_WRATH_BURN        = kSpellSlice.first + 4,    // CV4 the Champion inside: 5% of him + pacify
        SPELL_CV_EXORCISM_CAST          = kSpellSlice.first + 5,    // CV5 the 2 s bar
        SPELL_CV_EXORCISM               = kSpellSlice.first + 6,    // CV5 the line's hit (resolve copy, Holy)
        SPELL_CV_JUDGEMENT              = kSpellSlice.first + 7,    // CV6a the tank hit (percent by script)
        SPELL_CV_SEAL_OF_COMMAND        = kSpellSlice.first + 8,    // CV6b the held seal (buff)
        SPELL_CV_COMMAND_CLEAVE         = kSpellSlice.first + 9,    // CV6b the frontal's hit (resolve copy)
        SPELL_CV_SEAL_OF_RIGHTEOUSNESS  = kSpellSlice.first + 10,   // CV6c the held seal (buff)
        SPELL_CV_RIGHTEOUS_BRAND        = kSpellSlice.first + 11,   // CV6c the 5 s brand on a carrier
        SPELL_CV_RIGHTEOUS_BURST        = kSpellSlice.first + 12,   // CV6c the burst's hit (resolve copy, Holy)
        SPELL_CV_SEAL_OF_JUSTICE        = kSpellSlice.first + 13,   // CV6d the held seal (buff)
        SPELL_CV_JUSTICE_MARK           = kSpellSlice.first + 14,   // CV6d the 5 s mark (the hammer over the target)
        SPELL_CV_JUSTICE_HAMMER         = kSpellSlice.first + 15,   // CV6d a share of the split (percent by script)
        SPELL_CV_AVENGERS_SHIELD_CAST   = kSpellSlice.first + 16,   // CV7 the 2 s bar
        SPELL_CV_AVENGERS_SHIELD        = kSpellSlice.first + 17,   // CV7 the first hit + 2 s silence
        SPELL_CV_AVENGERS_SHIELD_BOUNCE = kSpellSlice.first + 18,   // CV7 a bounce's hit
        SPELL_CV_LAST_VIGIL             = kSpellSlice.first + 19,   // CV1 Azshir's 8 s channel (not interruptible)
        SPELL_CV_LAST_VIGIL_RING        = kSpellSlice.first + 20,   // CV1 the ring under the fallen Champion
        SPELL_CV_LAST_VIGIL_RISE        = kSpellSlice.first + 21,   // CV1 the rise's look
        SPELL_CV_GRIEF                  = kSpellSlice.first + 22,   // CV1 the stacking buff on the Champion
        SPELL_CV_EXECUTION_SENTENCE     = kSpellSlice.first + 23,   // CV8 heroic: the heal absorb (aura 301)
        SPELL_CV_EXECUTION_BURST        = kSpellSlice.first + 24,   // CV8 the room burst's hit (percent by script)
        SPELL_CV_EXECUTION_WAVE         = kSpellSlice.first + 25,   // CV8 the room wave's look on Azshir
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_CV_EXECUTION_WAVE;
    static_assert(kSpellSlice.Contains(kLastSpell), "the council's spells stay in its slice");

    // creature_text groups (ScarletMonasteryRework.h kTextRanges: Azshir 0-2, the Champion 0-3; none stock).
    enum AzshirTexts : std::uint8_t
    {
        YELL_AZSHIR_VIGIL       = 0,    // "Rise, brother! The vigil is not over!" (CV1)
        YELL_AZSHIR_AGGRO       = 1,    // "Scourge! You will not have his grave!"
        EMOTE_AZSHIR_EXECUTION  = 2,    // "A hammer of light hangs over $n!" (CV8, heroic; boss emote)
    };
    enum ChampionTexts : std::uint8_t
    {
        EMOTE_CHAMPION_COMMAND       = 0,   // "%s calls on the Seal of Command!"
        EMOTE_CHAMPION_RIGHTEOUSNESS = 1,   // "%s calls on the Seal of Righteousness!"
        EMOTE_CHAMPION_JUSTICE       = 2,   // "%s calls on the Seal of Justice!"
        EMOTE_CHAMPION_GRIEF         = 3,   // "%s is consumed by grief!"
    };

    // Cross-AI actions (CreatureAI::DoAction), Azshir <-> the Champion. Each side queues them for its next tick.
    enum CouncilActions : std::int32_t
    {
        ACTION_CV_VIGIL_BEGIN   = 0x43560001,   // the Champion fell while Azshir stands: start the channel
        ACTION_CV_VIGIL_RISE    = 0x43560002,   // the channel ended with Azshir alive: the Champion rises
        ACTION_CV_AZSHIR_FELL   = 0x43560003,   // Azshir died: Grief, or the fallen Champion's death becomes real
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The place (section 7 #18 A; NAVMESH council: the grave's dais has no walk route)
    // ----------------------------------------------------------------------------------------------------------------

    // The Champion stands on the lawn disc facing south (toward the yard the group comes up), Azshir 3 yd behind him.
    // Axes: +x north, +y west; orientation 0 looks north, pi south.
    inline constexpr float kFacingSouth = DungeonKit::kPi;
    inline constexpr float kAzshirBehindYd = 3.f;
    inline constexpr ScarletMonasteryRework::Point4 kChampionLawnSpot{ ScarletMonasteryRework::kCouncilLawn.x,
        ScarletMonasteryRework::kCouncilLawn.y, ScarletMonasteryRework::kCouncilLawn.z, kFacingSouth };
    inline constexpr ScarletMonasteryRework::Point4 kAzshirLawnSpot{ ScarletMonasteryRework::kCouncilLawn.x
        + kAzshirBehindYd, ScarletMonasteryRework::kCouncilLawn.y, ScarletMonasteryRework::kCouncilLawn.z,
        kFacingSouth };

    // The fight's leash frame: the lawn disc (NM: clearance 18.8, 4,633 sq yd of floor within 40 yd). The crypt
    // (z -9 to -8) and its z 0 court are more than 50 yd away and below the band.
    // Cut at y 1317 on Ironspine's side (RF-1 m-4, the mirror of his yard's cut, R-1-GY MN-3): a whole disc reached
    // y 1308.5, 23 yd from his home (1796.5, 1285.5), so a tank or a knockback could carry the council into his aggro.
    // The cut leaves 31.5 yd from the center (every bot spot is within kSpotBoundsYd 30) and 31.5 yd to his home. The
    // outline is the header's (CouncilLawnRegion, F-2a): one polygon for this AI, the instance's guard and the
    // Desecration's lawn.
    inline constexpr float kArenaRadiusYd = 40.f;
    inline constexpr float kArenaZMin = 15.f;
    inline constexpr float kArenaZMax = 26.f;
    inline constexpr float kArenaSouthCutY = ScarletMonasteryRework::kCouncilLawnSouthY;
    inline DungeonKit::Arena FightArena()
    {
        return DungeonKit::Arena(ScarletMonasteryRework::CouncilLawnRegion());
    }
    // The bots' planned spots stay within 30 yd of the disc's center (NM: 2,658 sq yd of floor within 30 yd).
    inline constexpr float kSpotBoundsYd = 30.f;
    // The room for the room-wide hits and the pull: the arena disc.
    inline constexpr float kRoomYd = kArenaRadiusYd;
    inline constexpr float kPullZoneYd = kArenaRadiusYd;

    // ----------------------------------------------------------------------------------------------------------------
    // Timers (ms from the pull; every cadence counts from the planned time, not the late start)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kHolyShockFirstMs = 4000;            // CV2
    inline constexpr std::uint32_t kHolyShockEveryMs = 7000;
    inline constexpr std::uint32_t kExorcismFirstMs = 8000;             // CV5
    inline constexpr std::uint32_t kExorcismEveryMs = 12000;
    inline constexpr std::uint32_t kExorcismCastMs = 2000;
    inline constexpr std::uint32_t kHolyWrathFirstMs = 14000;           // CV4
    inline constexpr std::uint32_t kHolyWrathEveryMs = 16000;
    inline constexpr std::uint32_t kHolyWrathCastMs = 2000;
    inline constexpr std::uint32_t kHolyLightFirstMs = 18000;           // CV3
    inline constexpr std::uint32_t kHolyLightEveryMs = 18000;
    inline constexpr std::uint32_t kHolyLightCastMs = 2500;
    inline constexpr std::uint32_t kExecutionFirstMs = 20000;           // CV8 (heroic)
    inline constexpr std::uint32_t kExecutionEveryMs = 30000;
    inline constexpr std::uint32_t kExecutionMs = 8000;                 // the hammer falls on its own at 8 s
    inline constexpr std::uint32_t kJudgementFirstMs = 10000;           // CV6a
    inline constexpr std::uint32_t kJudgementEveryMs = 10000;
    inline constexpr NH<std::uint32_t> kSealEveryMs{ 20000, 15000 };    // CV6: the seal changes
    inline constexpr std::uint32_t kSealWarnMs = 2000;                  // Command's front is live 2 s after the emote
    inline constexpr std::uint32_t kSwingTickMs = 2000;                 // Command: one cleave per swing (2.0 s)
    inline constexpr std::uint32_t kBrandMs = 5000;                     // CV6c
    inline constexpr std::uint32_t kJusticeMarkMs = 5000;               // CV6d
    inline constexpr std::uint32_t kShieldFirstMs = 10000;              // CV7
    inline constexpr std::uint32_t kShieldEveryMs = 15000;
    inline constexpr std::uint32_t kShieldCastMs = 2000;
    inline constexpr std::uint32_t kShieldSilenceMs = 2000;
    inline constexpr std::uint32_t kVigilChannelMs = 8000;              // CV1
    inline constexpr std::uint32_t kVigilWatchdogMs = kVigilChannelMs + 4000;   // no word from Azshir: settle it
    inline constexpr std::uint32_t kVigilRingMs = kVigilChannelMs + 1000;
    inline constexpr std::uint32_t kGriefEveryMs = 5000;                // CV1: a stack every 5 s after Azshir falls
    inline constexpr std::uint32_t kPacifyMs = 2000;                    // CV4 on the Champion
    inline constexpr std::uint32_t kRetryMs = 1000;                     // nobody to aim at: try again
    inline constexpr std::uint32_t kCastSpacingMs = 500;                // Azshir's queue: casts never overlap

    // ----------------------------------------------------------------------------------------------------------------
    // Numbers (percent of the reference row; N = level 32 normal, H = level 60 heroic)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr NH<float> kHolyShockPct{ 12.f, 18.f };             // CV2, the tank on the tank row
    inline constexpr NH<float> kHolyLightHealPct{ 10.f, 25.f };         // CV3, of the brother's own health
    inline constexpr NH<float> kHolyWrathPct{ 35.f, 45.f };             // CV4 + Weakened
    inline constexpr float kHolyWrathRadiusYd = 10.f;
    inline constexpr float kHolyWrathBurnPct = 5.f;                     // CV4 on the Champion: of his own health
    inline constexpr NH<float> kExorcismPct{ 35.f, 45.f };              // CV5 + Weakened
    inline constexpr float kExorcismWidthYd = 4.f;
    inline constexpr float kExorcismLengthYd = 40.f;
    inline constexpr NH<float> kJudgementTankPct{ 25.f, 35.f };         // CV6a, of tank health
    inline constexpr NH<float> kCommandPct{ 30.f, 45.f };               // CV6b + Weakened, never the tank
    inline constexpr float kCommandConeDeg = 120.f;
    inline constexpr float kCommandLengthYd = 8.f;
    inline constexpr NH<float> kRighteousnessPct{ 35.f, 45.f };         // CV6c + Weakened, each other player in 6 yd
    inline constexpr NH<std::uint32_t> kBrandCount{ 2, 3 };
    inline constexpr float kRighteousnessRadiusYd = 6.f;
    inline constexpr NH<float> kJusticeTotalPct{ 150.f, 250.f };        // CV6d split among everyone in 6 yd
    inline constexpr NH<float> kJusticeShareCapPct{ 75.f, 0.f };        // a lone share at most 75% (N); 0: no cap
    inline constexpr float kJusticeRadiusYd = 6.f;
    inline constexpr NH<float> kShieldFirstPct{ 20.f, 25.f };           // CV7 + 2 s silence (the carrier: no Weakened)
    inline constexpr NH<float> kShieldBouncePct{ 30.f, 40.f };          // CV7 + Weakened
    inline constexpr NH<std::uint32_t> kShieldHits{ 3, 5 };
    inline constexpr float kShieldMinRangeYd = 10.f;                    // thrown at a player more than 10 yd away
    inline constexpr float kShieldBounceYd = 8.f;
    inline constexpr float kExecutionAbsorbPct = 75.f;                  // CV8, the tank row on the tank
    inline constexpr float kExecutionBasePct = 10.f;                    // healed off: 10% + 5% a second up
    inline constexpr float kExecutionPerSecondPct = 5.f;
    inline constexpr float kExecutionFullPct = 50.f;                    // at 8 s on its own
    inline constexpr float kGriefPctPerStack = 20.f;                    // CV1: damage done and attack speed
    inline constexpr NH<std::uint32_t> kGriefMaxStacks{ 5, 255 };       // heroic: no cap (255 is the aura's ceiling)
    // CV1 raises per fight. Heroic was uncapped (spec); capped at 2 by the orchestrator's balance default (HANDOFF s10,
    // add sizing C, 2026-11-20, pending the user's confirmation; revert: { 2, 0 }, 0 = no cap).
    inline constexpr NH<std::uint32_t> kMaxRaises{ 2, 2 };
    inline constexpr float kKillTogetherPct = 10.f;                     // the bots keep the two within 10%
    inline constexpr NH<std::uint8_t> kHolyLightKickPriority{ 2, 3 };   // a reward (N), expected (H)

    // ----------------------------------------------------------------------------------------------------------------
    // CV6 the seals
    // ----------------------------------------------------------------------------------------------------------------

    enum class Seal : std::uint8_t
    {
        Command,
        Righteousness,
        Justice,
    };
    inline constexpr std::uint32_t kSealCount = 3;

    // Command, Righteousness, Justice, repeat.
    constexpr Seal SealAt(std::uint32_t index)
    {
        return static_cast<Seal>(index % kSealCount);
    }

    constexpr char const* SealName(Seal s)
    {
        switch (s)
        {
            case Seal::Command:         return "command";
            case Seal::Righteousness:   return "righteousness";
            case Seal::Justice:         return "justice";
        }
        return "?";
    }

    constexpr std::uint8_t SealEmote(Seal s)
    {
        switch (s)
        {
            case Seal::Command:         return EMOTE_CHAMPION_COMMAND;
            case Seal::Righteousness:   return EMOTE_CHAMPION_RIGHTEOUSNESS;
            case Seal::Justice:         return EMOTE_CHAMPION_JUSTICE;
        }
        return EMOTE_CHAMPION_COMMAND;
    }

    constexpr std::uint32_t SealAura(Seal s)
    {
        switch (s)
        {
            case Seal::Command:         return SPELL_CV_SEAL_OF_COMMAND;
            case Seal::Righteousness:   return SPELL_CV_SEAL_OF_RIGHTEOUSNESS;
            case Seal::Justice:         return SPELL_CV_SEAL_OF_JUSTICE;
        }
        return SPELL_CV_SEAL_OF_COMMAND;
    }

    // The rider a Judgement carries under the seal: none under Command (its cleave is the swings).
    enum class Rider : std::uint8_t
    {
        None,
        Brand,      // Righteousness: brand 2 / 3 random non-tank players
        Mark,       // Justice: mark one random player, the tank included
    };

    constexpr Rider RiderOf(Seal s)
    {
        switch (s)
        {
            case Seal::Command:         return Rider::None;
            case Seal::Righteousness:   return Rider::Brand;
            case Seal::Justice:         return Rider::Mark;
        }
        return Rider::None;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // CV1 The Last Vigil
    // ----------------------------------------------------------------------------------------------------------------

    // The Champion falls while Azshir stands: may he be raised again? `raisesDone` counts the raises already started.
    // Twice at most (normal; heroic by the s10 default above). A cap of 0 means no cap.
    constexpr bool RaiseAllowed(bool heroic, std::uint32_t raisesDone)
    {
        std::uint32_t const cap = kMaxRaises(heroic);
        return cap == 0 || raisesDone < cap;
    }

    // The health the Champion rises with on raise `raiseNumber` (1-based): normal 40% then 20%, heroic 50% each time.
    constexpr float RiseHealthPct(bool heroic, std::uint32_t raiseNumber)
    {
        if (heroic)
            return 50.f;
        return raiseNumber <= 1 ? 40.f : 20.f;
    }

    // Grief: each stack +20% damage done (multiplied into every script percent of his) and attack speed.
    constexpr float GriefDamageFactor(std::uint32_t stacks)
    {
        return 1.f + kGriefPctPerStack / 100.f * static_cast<float>(stacks);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // CV3 Holy Light: the brother with the lower percent of health (the fallen Champion is never a target)
    // ----------------------------------------------------------------------------------------------------------------

    enum class Brother : std::uint8_t
    {
        Champion,
        Azshir,
    };

    constexpr Brother HolyLightTarget(float championPct, float azshirPct, bool championAvailable)
    {
        if (!championAvailable)
            return Brother::Azshir;
        return championPct <= azshirPct ? Brother::Champion : Brother::Azshir;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // CV8 Execution Sentence (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    // The hammer's fall on the room: healed off after `msUp`, 10% plus 5% for every whole second it was up; on its
    // own at 8 s (`expired`), 50%. Never above 50%.
    constexpr float ExecutionBurstPct(std::uint32_t msUp, bool expired)
    {
        if (expired)
            return kExecutionFullPct;
        float const pct = kExecutionBasePct + kExecutionPerSecondPct * static_cast<float>(msUp / 1000);
        return pct > kExecutionFullPct ? kExecutionFullPct : pct;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // CV5 Exorcism: a fixed 40 yd line from Azshir through the target's spot at the cast start
    // ----------------------------------------------------------------------------------------------------------------

    // The facing (radians) of the line from `from` through `through`; nullopt when the two share a spot.
    inline std::optional<float> LineFacing(Vec2 from, Vec2 through)
    {
        if (DungeonKit::Distance(from, through) < 0.1f)
            return std::nullopt;
        return DungeonKit::BearingTo(from, through);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // CV7 Avenger's Shield: the first target, then the nearest player within 8 yd of the last hit, never twice
    // ----------------------------------------------------------------------------------------------------------------

    // Indices into `points` in hit order, starting with `first`, at most `maxHits` long.
    inline std::vector<std::size_t> ShieldChain(std::vector<Vec2> const& points, std::size_t first, float bounceYd,
        std::uint32_t maxHits)
    {
        std::vector<std::size_t> hits;
        if (first >= points.size() || maxHits == 0)
            return hits;
        std::vector<bool> used(points.size(), false);
        hits.push_back(first);
        used[first] = true;
        while (hits.size() < maxHits)
        {
            Vec2 const from = points[hits.back()];
            std::optional<std::size_t> best;
            float bestDist = 0.f;
            for (std::size_t i = 0; i < points.size(); ++i)
            {
                if (used[i])
                    continue;
                float const d = DungeonKit::Distance(from, points[i]);
                if (d > bounceYd)
                    continue;
                if (!best || d < bestDist)
                {
                    best = i;
                    bestDist = d;
                }
            }
            if (!best)
                break;
            used[*best] = true;
            hits.push_back(*best);
        }
        return hits;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Cadence
    // ----------------------------------------------------------------------------------------------------------------

    // The next planned time after `planned`, `every` apart, never at or before `now` (a late cast does not shift the
    // cadence; a long hold skips the turns it missed).
    constexpr std::uint64_t NextDue(std::uint64_t planned, std::uint64_t every, std::uint64_t now)
    {
        std::uint64_t next = planned + every;
        while (every && next <= now)
            next += every;
        return next;
    }
}

#endif
