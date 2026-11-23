/*
 * mod-dungeon-bosses, Scarlet Monastery D8H:
 * Arcanist Doan's hard mode, the Kel'Thuzad Heresy, the pure, host-testable part (no engine headers). Build spec:
 * docs/dungeons/scarlet-monastery-2-library.md "Hard mode: The Kel'Thuzad Heresy" (HM1-HM5) and its Build spec rows,
 * handoff section 3.7, 3.8 row "D8H pages", 7 #27 A (the page spots). Tested by tests/sm_doan_hard_mode_test.cpp.
 *
 *   Spells     the WP's ids, inside kSpellsHeresy (212710-212749), declared in apps/dbc-tools
 *              source/npcs/scarlet_monastery/doan_hard_mode.py
 *   Pages      the four evidence pages (gameobjects 301320-301323, heroic only): their spots (section 7 #27 A), their
 *              page_text ids, why a read is refused, the "(n of 4)" emote
 *   Tuning     the hard mode's numbers on top of D8's heroic kit (DoanFight.h tuning queries): Doan 400k, anchors
 *              and the Phylactery Shard RELATIVE to D8's heroic anchor (so a retune of the base window carries over),
 *              the 35 s bubble, the 30 s Marks, permanent pools, Detonation 200%, Icy Death, Shadow Fissure, the
 *              Risen Purged
 *   Rules      which of D8's hits carry Icy Death, when the fissures and the Risen start, a Risen's arrival, the
 *              rule 20 window math (humans and bots)
 */

#ifndef MOD_DUNGEON_BOSSES_SM_DOAN_HARD_MODE_LOGIC_H
#define MOD_DUNGEON_BOSSES_SM_DOAN_HARD_MODE_LOGIC_H

#include "DoanLogic.h"
#include "ScarletMonasteryRework.h"
#include <array>
#include <cstdint>
#include <string>

namespace SmHeresy
{
    using ScarletMonasteryRework::Point3;

    // Every spell of this WP sits in this slice (ScarletMonasteryRework.h; ids.yaml reservation `scarlet_monastery`).
    inline constexpr ScarletMonasteryRework::IdSlice kSpellSlice = ScarletMonasteryRework::kSpellsHeresy;

    enum DoanHardModeSpells : std::uint32_t
    {
        SPELL_HERESY_ICY_DEATH = kSpellSlice.first + 0,     // 212710 HM1 the Curse (slow, Frost DoT) his hits apply
        SPELL_HERESY_AURA = kSpellSlice.first + 1,          // 212711 the hard mode's red aura on Doan (holds a wipe)
        SPELL_HERESY_SHARD_WARD = kSpellSlice.first + 2,    // 212712 HM3 the shard's immunity while an anchor stands
        SPELL_HERESY_FISSURE = kSpellSlice.first + 3,       // 212713 HM4 Shadow Fissure's hit (resolve copy, Shadow)
        SPELL_HERESY_FISSURE_LOOK = kSpellSlice.first + 4,  // 212714 HM4 the fissure's look (an aura on a stalker)
        SPELL_HERESY_RAISE_LOOK = kSpellSlice.first + 5,    // 212715 HM5 a Risen Purged rising (Raise Dead's look)
        // 212716-212749 spare
    };
    static_assert(SPELL_HERESY_RAISE_LOOK <= kSpellSlice.last, "the Heresy's spells must stay in its slice");

    // Registry tags (D8's are 1, 2, 3, 11 and 31).
    enum HeresyTags : std::uint32_t
    {
        TAG_HM_FISSURE = 4,     // HM4 Shadow Fissure
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The evidence trail (section 3.7, 7 #27 A): four pages, any order, each read once per instance; the fourth
    // lights DATA_HARD_MODE_DOAN (the instance's, saved) and Doan yells line 2 across the Library.
    // ----------------------------------------------------------------------------------------------------------------

    struct EvidencePage
    {
        std::uint32_t entry;        // gameobject_template (a goober showing its page_text)
        std::uint32_t pageText;     // page_text id (the same number as the entry)
        Point3 spot;
        float facing;
        char const* what;           // for the log
    };

    // Page 1 the kennel hall's real north corner (NAVMESH misfit 9: 41 yd off the route, no mob within 12 yd); page 2
    // at the Large Solid Chest of the corridor to the long hall (its spot (223.9, -292.7) kept; the page lies at the
    // chest's south side, 1.2 yd off it, so a click never takes the chest); page 3 the reading hall's east nook on its
    // floor; page 4 the passage before the Athenaeum beside The Scourge of Lordaeron (kept: the passage's Monk and
    // Diviner must be dead first).
    inline constexpr std::uint32_t kPageCount = ScarletMonasteryRework::kDoanPages;
    inline constexpr std::array<EvidencePage, kPageCount> kPages{ {
        { ScarletMonasteryRework::GO_SM_EVIDENCE_PAGE_1, 301320, { 156.0f, -241.0f, 19.2f }, 0.f, "kennel-ledger" },
        { ScarletMonasteryRework::GO_SM_EVIDENCE_PAGE_2, 301321, { 222.7f, -292.7f, 19.2f }, 0.f, "catalog-page" },
        { ScarletMonasteryRework::GO_SM_EVIDENCE_PAGE_3, 301322, { 276.2f, -428.2f, 18.7f }, 0.f, "index-page" },
        { ScarletMonasteryRework::GO_SM_EVIDENCE_PAGE_4, 301323, { 219.0f, -424.0f, 19.9f }, 0.f, "doans-copy" },
    } };

    // The page index (0-3) of a page gameobject entry; kPageCount when it is none of them.
    constexpr std::uint32_t PageOf(std::uint32_t entry)
    {
        for (std::uint32_t i = 0; i < kPageCount; ++i)
            if (kPages[i].entry == entry)
                return i;
        return kPageCount;
    }

    // Why a read does not count (the instance's DoanPageAllowed, with the reason for the reader).
    enum class PageRefusal : std::uint8_t
    {
        None,
        NotHeroic,
        NotAPage,
        AlreadyRead,
        DoanFighting,
        DoanDead,
    };

    constexpr PageRefusal PageRefusalFor(bool heroic, std::uint32_t doanState, std::uint32_t mask, std::uint32_t page)
    {
        if (!heroic)
            return PageRefusal::NotHeroic;
        if (page >= kPageCount)
            return PageRefusal::NotAPage;
        if (doanState == DungeonKit::State::Done)
            return PageRefusal::DoanDead;
        if (doanState == DungeonKit::State::InProgress)
            return PageRefusal::DoanFighting;
        if (mask & (1u << page))
            return PageRefusal::AlreadyRead;
        return PageRefusal::None;
    }

    // Only a fight in progress is worth a notice; the other refusals still show the page's text and say nothing.
    constexpr char const* PageRefusalNotice(PageRefusal why)
    {
        return why == PageRefusal::DoanFighting ? "The Arcanist is fighting. The evidence can wait." : nullptr;
    }

    // The emote to the reader (LIB "Text": "You have found evidence of heresy (%u of 4).").
    inline std::string PageEmote(std::uint32_t read)
    {
        return "You have found evidence of heresy (" + std::to_string(read) + " of " + std::to_string(kPageCount)
            + ").";
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (Build spec, the "Hard mode" columns; percents of the heroic reference row, level 60)
    // ----------------------------------------------------------------------------------------------------------------

    // Doan: 400k from the pull (heroic 230k), back on a wipe.
    inline constexpr std::uint32_t kDoanHealth = 400000;

    // DN1 / HM3: the spec's 10k anchors and 25k shard (on the spec's 8k heroic anchor), kept RELATIVE to D8's heroic
    // anchor (H's template), so the retune of the base window carries into the hard mode: an anchor is 1.25 x its
    // heroic health, the shard 2.5 x a hard mode anchor. On the HANDOFF s10 option D heroic anchor (5k): 6.25k anchors
    // and a 15.6k shard, 40.6k a bubble of 4.
    inline constexpr float kAnchorScale = 1.25f;
    inline constexpr float kShardToAnchor = 2.5f;

    constexpr std::uint32_t HardModeAnchorHealth(std::uint32_t heroicAnchorHealth)
    {
        return static_cast<std::uint32_t>(static_cast<float>(heroicAnchorHealth) * kAnchorScale + 0.5f);
    }

    constexpr std::uint32_t ShardHealth(std::uint32_t hardModeAnchorHealth)
    {
        return static_cast<std::uint32_t>(static_cast<float>(hardModeAnchorHealth) * kShardToAnchor + 0.5f);
    }

    // HM3: the shard's spot, the first of D8's anchor spots no living anchor stands on (`takenMask` bit i: spot i is
    // taken). A refused anchor summon leaves its spot free, so the count of raised anchors is not the next free spot.
    // kAnchorSpotCount when all 12 are taken (heroic has no anchor cap): the caller sets the shard beside the last
    // spot, kShardCrowdedStepYd toward Doan.
    inline constexpr float kShardSpotTakenYd = 1.5f;        // an anchor this close to a spot stands on it
    inline constexpr float kShardCrowdedStepYd = 3.f;
    constexpr std::uint32_t ShardSpotIndex(std::uint32_t takenMask)
    {
        for (std::uint32_t i = 0; i < SmDoan::kAnchorSpotCount; ++i)
            if (!(takenMask & (1u << i)))
                return i;
        return SmDoan::kAnchorSpotCount;
    }

    // DoanFight.h tuning queries: the bubble every 35 s (heroic 30 s), Marks every 30 s (heroic 20 s), the pools for
    // the rest of the fight (0, D8's "permanent"), Detonation 200% (heroic 130%).
    inline constexpr std::uint32_t kBubbleEveryMs = 35000;
    inline constexpr std::uint32_t kMarkEveryMs = 30000;
    inline constexpr std::uint32_t kPoolLifeMs = 0;
    inline constexpr float kDetonationPct = 200.f;

    // HM1 Icy Death: a Curse for 8 s, refreshed by each hit, 60% slower movement and Frost a second (the spec's
    // starting guess 3% of the reference row). Declared in doan_hard_mode.py (the kit's
    // spell_dungeon_refflat_periodic).
    inline constexpr std::uint32_t kIcyDeathMs = 8000;
    inline constexpr std::int32_t kIcyDeathSlowPct = 60;
    inline constexpr std::uint32_t kIcyDeathTickMs = 1000;
    inline constexpr std::uint32_t kIcyDeathHundredths = 300;      // 3% a tick

    // D8's hits (DoanFight.h DoanHit, the same order; doan_hard_mode.cpp static_asserts it) and the ones Icy Death
    // rides: "every damaging ability of his (Arcane Explosion, the Mark burst, Flamestrike, Shadow Fissure, the
    // pools)". The Mark's own share is the burst too; the Scorched patches and Detonation are not in the list.
    enum class RiddenHit : std::uint8_t
    {
        Explosion,
        MarkBurst,
        MarkSelf,
        Pool,
        Flamestrike,
        Scorched,
        Detonation,
    };

    constexpr bool IcyDeathRides(RiddenHit hit)
    {
        switch (hit)
        {
            case RiddenHit::Explosion:
            case RiddenHit::MarkBurst:
            case RiddenHit::MarkSelf:
            case RiddenHit::Pool:
            case RiddenHit::Flamestrike:
                return true;
            case RiddenHit::Scorched:
            case RiddenHit::Detonation:
                return false;
        }
        return false;
    }

    // HM4 Shadow Fissure: from the end of his first bubble, every 10 s, a 6 yd circle under 2 random players (the tank
    // can be one), a 3 s marker, then 60% Shadow (and Icy Death). Held while he is Overloaded ("he stops casting"); it
    // keeps coming during the bubble.
    inline constexpr std::uint32_t kFissureAfterBubble = 1;
    inline constexpr std::uint32_t kFissureEveryMs = 10000;
    inline constexpr std::uint32_t kFissureCount = 2;
    inline constexpr float kFissureRadiusYd = 6.f;
    inline constexpr std::uint32_t kFissureWarnMs = 3000;
    inline constexpr float kFissurePct = 60.f;
    inline constexpr std::uint32_t kFissureLookTailMs = 500;

    constexpr bool FissuresStart(std::uint32_t bubbleIndex)
    {
        return bubbleIndex == kFissureAfterBubble;
    }

    constexpr bool FissureHeld(bool overloaded)
    {
        return overloaded;
    }

    // HM5 the Risen Purged: once, at the end of his second bubble, six rise along the chamber's south wall (x 136,
    // NAVMESH floor, 4 yd off the wall and the Strongbox corner), yell line 3, and walk to him; each that reaches him
    // is one more anchor at the next bubble (DoanFight::AddNextBubbleAnchors) and is gone. Passive: they never stop to
    // fight (designer question), so a slow, a root or a stun holds them back. 6k each (H's heroic template).
    inline constexpr std::uint32_t kRisenAfterBubble = 2;
    inline constexpr std::uint32_t kRisenCount = 6;
    inline constexpr std::array<Point3, kRisenCount> kRisenSpots{ {
        { 136.0f, -417.0f, 18.5f }, { 136.0f, -422.0f, 18.5f }, { 136.0f, -427.0f, 18.5f },
        { 136.0f, -432.0f, 18.5f }, { 136.0f, -437.0f, 18.5f }, { 136.0f, -442.0f, 18.5f },
    } };
    inline constexpr std::uint32_t kRisenRiseMs = 1500;        // Raise Dead's look before the first step
    inline constexpr float kRisenSpeedYdPerSec = 1.2f;         // 8-15 yd to him: about 10 s
    inline constexpr std::uint32_t kRisenReaimMs = 1000;
    inline constexpr float kRisenReachYd = 3.f;                // past his combat reach
    inline constexpr std::uint32_t kRisenHealth = 6000;

    constexpr bool RisenRise(std::uint32_t bubbleIndex)
    {
        return bubbleIndex == kRisenAfterBubble;
    }

    // A Risen Purged has reached him: within its reach of his edge (2D center distance less his combat reach).
    constexpr bool RisenArrived(float centerDistYd, float doanCombatReachYd)
    {
        return centerDistYd - doanCombatReachYd <= kRisenReachYd;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Rule 20: the bubble window (D8's heroic Detonation bar, 14 s: no override here) against the group's damage
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kEffectiveDpsHardMode = 3774;     // 4,440 x 0.85 (Build spec "Tuning")
    inline constexpr std::uint32_t kBotAddDps = SmDoan::kBotAddDpsHeroic;   // about 700 (LESSONS 4.2)
    inline constexpr std::uint32_t kHardModeAnchors = 4;             // heroic's 4 (D8), plus the shard

    // Seconds of `dps` to break a bubble of `anchors` hard mode anchors and the shard (no walking counted).
    constexpr float BubbleSeconds(std::uint32_t anchors, std::uint32_t heroicAnchorHealth, std::uint32_t dps)
    {
        std::uint32_t const anchor = HardModeAnchorHealth(heroicAnchorHealth);
        return dps ? static_cast<float>(anchors * anchor + ShardHealth(anchor)) / static_cast<float>(dps) : 0.f;
    }
}

#endif
