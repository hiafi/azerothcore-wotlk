/*
 * mod-dungeon-bosses, Scarlet Monastery D7:
 * Lector Hollis Grey, the Librarian (300913), his Cursed Books (300914) and their stories' units (Infernal 300915,
 * Spiderling 300916, Spectral Troll 300917, Phantom Grunt 300918), the pure, host-testable part (no engine headers).
 * Build spec LIB "Lector Hollis Grey, the Librarian" (docs/dungeons/scarlet-monastery-2-library.md, LB1-LB9; hub
 * rulings 22, 25, 26), handoff sections 3.4 (F3, F8, F9, F45), 3.5 row D7, 3.6, 3.8 (NM: the reading hall, the
 * pocket), 3.10 and section 7 #26 A (he stands in the pocket (254.8, -389.2), not the 3 yd aisle). Tested by
 * tests/sm_hollis_grey_test.cpp.
 *
 *   Spells     the WP's ids, inside kSpellsHollisGrey (212610-212669), declared in apps/dbc-tools
 *              source/npcs/scarlet_monastery/hollis_grey.py (lib/test_scarlet_monastery_hollis_grey.py pins both)
 *   Tuning     NH<> constants from the build spec (normal / heroic); this WP's defaults where the spec gives none
 *              (the Infernal's Immolation, the adds' melee, Drowsy's 10%) are named in the report
 *   Shelf      LB1's shuffled shelf: six books in a random order, no repeat until all six are read
 *   Pages      LB1a: a page every 10 s a book stays open (normal stops at page 3), what each story does per page
 *   Picks      the throw spot (10 to 20 yd from him, on the hall's floor, apart from the open books), the adds'
 *              first target (the nearest tank, else the nearest player), the kill order by page
 *   Drowsy     LB6's stacks: one a second inside the mist, one off a second outside, the sleep at five
 *   Geometry   the hall's floor points (NAVMESH, a 3 yd grid with 1.5 yd of clearance), its bot bounds
 */

#ifndef MOD_DUNGEON_BOSSES_SM_HOLLIS_GREY_LOGIC_H
#define MOD_DUNGEON_BOSSES_SM_HOLLIS_GREY_LOGIC_H

#include "DungeonKitMath.h"
#include "ScarletMonasteryRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace SmHollisGrey
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using ScarletMonasteryRework::Point3;

    // Every spell of this WP sits in this slice (ScarletMonasteryRework.h; ids.yaml reservation `scarlet_monastery`).
    inline constexpr ScarletMonasteryRework::IdSlice kSpellSlice = ScarletMonasteryRework::kSpellsHollisGrey;

    // The binding switch (S0): this WP declares 300913-300918 in hollis_grey.py and spawns him in its SQL rev, so his
    // script registers. Both sides flipped in one change.
    inline constexpr bool kBound = true;

    // ----------------------------------------------------------------------------------------------------------------
    // Spells (hollis_grey.py declares each; the comment names its row)
    // ----------------------------------------------------------------------------------------------------------------

    enum HollisGreySpells : std::uint32_t
    {
        SPELL_LB_OPEN_THE_INDEX         = kSpellSlice.first + 0,    // 212610 LB1 normal: the 2 s bar (Arcane, no kick)
        SPELL_LB_OPEN_THE_INDEX_HEROIC  = kSpellSlice.first + 1,    // 212611 LB1 heroic: the 3 s cast (a kick)
        SPELL_LB_TURNING_THE_PAGE       = kSpellSlice.first + 2,    // 212612 LB1a the book's page count (stacks)
        SPELL_LB_READERS_WARD           = kSpellSlice.first + 3,    // 212613 LB1b -25% damage taken a stack
        SPELL_LB_STORY_SPIDER           = kSpellSlice.first + 4,    // 212614 the book's story: War of the Spider
        SPELL_LB_STORY_ARCHIMONDE       = kSpellSlice.first + 5,    // 212615 ... Archimonde's Return
        SPELL_LB_STORY_TROLL_WARS       = kSpellSlice.first + 6,    // 212616 ... Arathor and the Troll Wars
        SPELL_LB_STORY_TITANS           = kSpellSlice.first + 7,    // 212617 ... Mythology of the Titans
        SPELL_LB_STORY_DREAM            = kSpellSlice.first + 8,    // 212618 ... The World Tree and the Emerald Dream
        SPELL_LB_STORY_AFTERMATH        = kSpellSlice.first + 9,    // 212619 ... Aftermath of the Second War
        SPELL_LB_WEB_SPRAY              = kSpellSlice.first + 10,   // 212620 LB2 look: the spray, book -> web spot
        SPELL_LB_WEB_SLOW               = kSpellSlice.first + 11,   // 212621 LB2 the web's 50% slow (the zone's rider)
        SPELL_LB_WEB_PATCH              = kSpellSlice.first + 12,   // 212622 LB2 look: the 6 yd web on a stalker
        SPELL_LB_HATCH                  = kSpellSlice.first + 13,   // 212623 LB2 look: the hatch on the web
        SPELL_LB_METEOR                 = kSpellSlice.first + 14,   // 212624 LB3 the meteor's hit (resolve copy)
        SPELL_LB_INFERNO                = kSpellSlice.first + 15,   // 212625 LB3 look: the falling infernal
        SPELL_LB_IMMOLATION             = kSpellSlice.first + 16,   // 212626 LB3 the Infernal's burn (5 yd, Fire)
        SPELL_LB_THROW_AXE              = kSpellSlice.first + 17,   // 212627 LB4 an axe line's hit (resolve copy)
        SPELL_LB_THROW_AXE_LOOK         = kSpellSlice.first + 18,   // 212628 LB4 look: the axe in flight
        SPELL_LB_TITAN_STOMP            = kSpellSlice.first + 19,   // 212629 LB5 a ring's hit (resolve copy)
        SPELL_LB_WAR_STOMP              = kSpellSlice.first + 20,   // 212630 LB5 look: the stomp (first ring)
        SPELL_LB_GROUND_SLAM            = kSpellSlice.first + 21,   // 212631 LB5 look: each later ring
        SPELL_LB_DREAM_MIST_6           = kSpellSlice.first + 22,   // 212632 LB6 look: the 6 yd mist rung (STATE)
        SPELL_LB_DREAM_MIST_9           = kSpellSlice.first + 23,   // 212633 LB6 look: 9 yd
        SPELL_LB_DREAM_MIST_12          = kSpellSlice.first + 24,   // 212634 LB6 look: 12 yd
        SPELL_LB_DROWSY                 = kSpellSlice.first + 25,   // 212635 LB6 the stacking slow (the mist's rider)
        SPELL_LB_DREAM_SLEEP            = kSpellSlice.first + 26,   // 212636 LB6 the 2 s sleep at five stacks
        SPELL_LB_DREAMING               = kSpellSlice.first + 27,   // 212637 LB6a heroic: the Magic debuff (dispel)
        SPELL_LB_PHANTOM_CHARGE         = kSpellSlice.first + 28,   // 212638 LB7 the charge line's hit (resolve copy)
        SPELL_LB_CHARGE_LOOK            = kSpellSlice.first + 29,   // 212639 LB7 look: the grunt's charge trail
        SPELL_LB_SEARING_REBUKE         = kSpellSlice.first + 30,   // 212640 LB8 the 2.5 s tank hit (Holy, a kick)
        SPELL_LB_BURNING_BOOK           = kSpellSlice.first + 31,   // 212641 LB9 heroic: the fire's tick (resolve copy)
        SPELL_LB_BURNING_BOOK_LOOK      = kSpellSlice.first + 32,   // 212642 LB9 look: the 5 yd fire on a stalker
        SPELL_LB_DREAM_MIST             = kSpellSlice.first + 33,   // 212643 LB6 the mist's tick (resolve copy)
        SPELL_LB_WEB                    = kSpellSlice.first + 34,   // 212644 LB2 the web's tick (resolve copy)
        // 212645-212669 spare
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_LB_WEB;
    static_assert(kLastSpell <= kSpellSlice.last, "Hollis Grey's spells must stay in his slice");

    // Registry tags (one per mechanic; the drills and the fight's ledger key on them).
    enum HollisGreyTags : std::uint32_t
    {
        TAG_LB_WEB          = 1,    // LB2
        TAG_LB_METEOR       = 2,    // LB3
        TAG_LB_AXE          = 3,    // LB4
        TAG_LB_STOMP        = 4,    // LB5
        TAG_LB_MIST         = 5,    // LB6 (and the heroic Dreaming mists)
        TAG_LB_CHARGE       = 6,    // LB7
        TAG_LB_BURNING_BOOK = 7,    // LB9
    };

    // creature_text groups of 300913 (LIB "Text"; S0 range 0-7, all new). Yells 0 and 7; the book emotes are boss
    // emotes (type 41), one per story: group = EMOTE_LB_BOOK_FIRST + story.
    enum HollisGreyTexts : std::uint8_t
    {
        SAY_LB_AGGRO        = 0,    // "Heretics, in my reading hall? Then hear what you came to read!"
        EMOTE_LB_BOOK_FIRST = 1,    // "%s opens a forbidden book: War of the Spider!" ... 6 Aftermath
        SAY_LB_DEATH        = 7,    // "Burn them... burn them all..."
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The six stories (LB2-LB7), in the spec's table order
    // ----------------------------------------------------------------------------------------------------------------

    enum class Story : std::uint8_t
    {
        Spider      = 0,    // LB2 War of the Spider
        Archimonde  = 1,    // LB3 Archimonde's Return and the Flight to Kalimdor
        TrollWars   = 2,    // LB4 Arathor and the Troll Wars
        Titans      = 3,    // LB5 Mythology of the Titans
        Dream       = 4,    // LB6 The World Tree and the Emerald Dream
        Aftermath   = 5,    // LB7 Aftermath of the Second War
    };
    inline constexpr std::uint8_t kStoryCount = 6;

    constexpr std::uint32_t StorySpell(Story s)
    {
        return SPELL_LB_STORY_SPIDER + static_cast<std::uint32_t>(s);
    }

    constexpr std::uint8_t StoryText(Story s)
    {
        return static_cast<std::uint8_t>(EMOTE_LB_BOOK_FIRST + static_cast<std::uint8_t>(s));
    }

    constexpr char const* StoryName(Story s)
    {
        switch (s)
        {
            case Story::Spider:     return "spider";
            case Story::Archimonde: return "archimonde";
            case Story::TrollWars:  return "troll-wars";
            case Story::Titans:     return "titans";
            case Story::Dream:      return "dream";
            case Story::Aftermath:  return "aftermath";
        }
        return "?";
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (build spec "Tuning starting points" and the Mechanics table; percents of the reference row)
    // ----------------------------------------------------------------------------------------------------------------

    // LB1 Open the Index: 8 s, then every 20 s (heroic 6 s, 15 s); a 2 s bar (heroic a 3 s cast, an expected kick:
    // missed, the book opens on page 2). Normal: no new book while 2 are open (he tries again every second).
    inline constexpr NH<std::uint32_t> kOpenFirstMs{ 8000, 6000 };
    inline constexpr NH<std::uint32_t> kOpenEveryMs{ 20000, 15000 };
    inline constexpr NH<std::uint32_t> kOpenCastMs{ 2000, 3000 };
    inline constexpr std::uint32_t kOpenBooksCapNormal = 2;
    inline constexpr std::uint32_t kRetryMs = 1000;
    inline constexpr std::uint8_t kOpenKickPriorityHeroic = 3;     // expected

    // The throw: a spot 10 to 20 yd from him in a random direction, on the hall's floor, at chest height.
    inline constexpr float kThrowMinYd = 10.f;
    inline constexpr float kThrowMaxYd = 20.f;
    inline constexpr float kBookSpacingYd = 6.f;      // never on top of another open book (relaxed when nothing fits)
    inline constexpr float kBookHoverYd = 1.2f;       // above the floor: melee reach it, it hangs open

    // LB1a Turning the page: every 10 s a book stays open; normal stops at page 3 (heroic: no cap, 0).
    inline constexpr std::uint32_t kPageEveryMs = 10000;
    inline constexpr NH<std::uint8_t> kPageCap{ 3, 0 };
    inline constexpr std::uint8_t kMaxShownPage = 10;  // the page aura's StackAmount (heroic keeps counting past it)

    // LB1b Reader's Ward: -25% damage taken per open book, at most 50% (heroic 75%).
    inline constexpr float kWardPctPerBook = 25.f;
    inline constexpr NH<float> kWardCapPct{ 50.f, 75.f };

    // LB2 War of the Spider: 2 s after opening, every 8 s, a 6 yd web on a random player's spot (2 s marker), slow
    // 50% inside, until the book closes (normal: 3 webs, the oldest fades); 2 Spiderlings hatch (+1 a page).
    inline constexpr std::uint32_t kWebFirstMs = 2000;
    inline constexpr std::uint32_t kWebEveryMs = 8000;
    inline constexpr std::uint32_t kWebWarnMs = 2000;
    inline constexpr float kWebRadiusYd = 6.f;
    inline constexpr std::uint32_t kWebTickMs = 1000;
    inline constexpr std::uint32_t kWebSlowPct = 50;
    inline constexpr NH<std::uint32_t> kWebCap{ 3, 0 };

    // LB3 Archimonde's Return: on opening and every 15 s, a meteor on a random player's spot (+1 a page): 8 yd,
    // 4 s marker, 50% / 60% Fire, then an Infernal rises (normal: 2 alive per book at most).
    inline constexpr std::uint32_t kMeteorFirstMs = 0;
    inline constexpr std::uint32_t kMeteorEveryMs = 15000;
    inline constexpr std::uint32_t kMeteorWarnMs = 4000;
    inline constexpr std::uint32_t kMeteorLookLeadMs = 1000;  // the falling infernal's look starts 1 s before impact
    inline constexpr float kMeteorRadiusYd = 8.f;
    inline constexpr NH<float> kMeteorPct{ 50.f, 60.f };
    inline constexpr NH<std::uint32_t> kInfernalCap{ 2, 0 };
    // The Infernal's Immolation (gap 12: this WP's default): 2% / 2% of the row every 2 s within 5 yd of it.
    inline constexpr std::uint32_t kImmolationEveryMs = 2000;
    inline constexpr NH<float> kImmolationPct{ 2.f, 2.f };
    inline constexpr float kImmolationRadiusYd = 5.f;

    // LB4 Arathor and the Troll Wars: a Spectral Troll at the book; 2 s after opening, every 6 s, axes at 2 random
    // players (+1 a page): lines 3 yd wide, 35 yd long from the troll through the player, 2 s marker, 35% / 45%
    // Physical + Weakened.
    inline constexpr std::uint32_t kAxeFirstMs = 2000;
    inline constexpr std::uint32_t kAxeEveryMs = 6000;
    inline constexpr std::uint32_t kAxeWarnMs = 2000;
    inline constexpr std::uint32_t kAxeLookLeadMs = 500;      // the axe leaves the troll's hand 0.5 s before the hit
    inline constexpr float kAxeWidthYd = 3.f;
    inline constexpr float kAxeLengthYd = 35.f;
    inline constexpr NH<float> kAxePct{ 35.f, 45.f };
    inline constexpr float kTrollOffsetYd = 2.f;              // the troll stands beside the book, toward him

    // LB5 Mythology of the Titans: 3 s after opening, every 10 s, the stomp rolls out from the book: 0-8, 8-16,
    // 16-24 yd, 1.5 s apart, 2 s marker each, 35% / 45% Physical + Weakened per ring; +1 ring a page, to 32 yd.
    inline constexpr std::uint32_t kStompFirstMs = 3000;
    inline constexpr std::uint32_t kStompEveryMs = 10000;
    inline constexpr std::uint32_t kStompWarnMs = 2000;
    inline constexpr std::uint32_t kStompRingGapMs = 1500;
    inline constexpr float kStompRingYd = 8.f;
    inline constexpr std::uint8_t kStompRingsBase = 3;        // page 1
    inline constexpr std::uint8_t kStompRingsMax = 4;         // 32 yd
    inline constexpr NH<float> kStompPct{ 35.f, 45.f };

    // LB6 The World Tree and the Emerald Dream: a 6 yd mist round the book while it is open, +3 yd a page; each
    // second inside adds a Drowsy stack (10% slower movement and casting each, this WP's starting guess), a second
    // outside takes one off, at 5 stacks a 2 s sleep. Heroic Dreaming: each page a 6 s Magic debuff on a random
    // player (an expected dispel); missed, a 2 s sleep and a new 6 yd mist at their spot until the book closes.
    inline constexpr float kMistBaseYd = 6.f;
    inline constexpr float kMistPerPageYd = 3.f;
    inline constexpr std::uint32_t kMistTickMs = 1000;
    inline constexpr std::uint32_t kMistWarnMs = 1500;
    inline constexpr std::uint8_t kDrowsyMaxStacks = 5;
    inline constexpr std::uint32_t kDrowsyPct = 10;
    inline constexpr std::uint32_t kDrowsyDecayMs = 1000;
    inline constexpr std::uint32_t kDrowsyCheckMs = 250;
    inline constexpr std::uint32_t kDreamSleepMs = 2000;
    inline constexpr std::uint32_t kDreamingMs = 6000;
    inline constexpr float kDreamingMistYd = 6.f;
    inline constexpr std::uint8_t kDreamingDispelPriority = 2;  // expected

    // LB7 Aftermath of the Second War: 3 s after opening, every 10 s, a phantom grunt charges a random player (+1 a
    // page): a line 6 yd wide from the book through the player to the wall, 3 s marker, 50% / 60% Physical.
    inline constexpr std::uint32_t kChargeFirstMs = 3000;
    inline constexpr std::uint32_t kChargeEveryMs = 10000;
    inline constexpr std::uint32_t kChargeWarnMs = 3000;
    inline constexpr float kChargeWidthYd = 6.f;
    inline constexpr float kChargeOverrunYd = 80.f;       // to the wall: LineStrike clips at the hall's edge
    inline constexpr NH<float> kChargePct{ 50.f, 60.f };
    inline constexpr float kChargeSpeedYd = 30.f;         // the grunt's run along its line
    inline constexpr std::uint32_t kGruntFadeMs = 1500;   // after its run

    // LB8 Searing Rebuke: a 2.5 s cast on his target, 5 s, then every 10 s: 20% / 30% of the tank row, Holy; a kick
    // stops it (a reward).
    inline constexpr std::uint32_t kRebukeFirstMs = 5000;
    inline constexpr std::uint32_t kRebukeEveryMs = 10000;
    inline constexpr std::uint32_t kRebukeCastMs = 2500;
    inline constexpr NH<float> kRebukePct{ 20.f, 30.f };
    inline constexpr std::uint8_t kRebukeKickPriority = 1;    // a reward

    // LB9 Burning Book (heroic): a destroyed book leaves a 5 yd fire for the rest of the fight, 10% Fire a second.
    inline constexpr float kBurningBookYd = 5.f;
    inline constexpr float kBurningBookPct = 10.f;
    inline constexpr std::uint32_t kBurningBookTickMs = 1000;

    // Health (handoff section 3.6; the templates carry the normal values, WP-H's overrides the heroic ones). Every
    // combat unit of the fight is level 35, his level, so a percent hit cast by a book or an Infernal reads the same
    // reference row as his own (rule 2); the HealthModifiers are on the level 35 bases (mage 902, warrior 1,220).
    inline constexpr NH<std::uint32_t> kBossHealth{ 36000, 220000 };
    inline constexpr NH<std::uint32_t> kBookHealth{ 3500, 15000 };
    inline constexpr NH<std::uint32_t> kInfernalHealth{ 4000, 20000 };
    inline constexpr NH<std::uint32_t> kSpiderlingHealth{ 500, 2500 };

    // Rule 20 (LS 4.2): the book window against the spec's effective group DPS and the measured bot throughput
    // (about half of it).
    inline constexpr NH<std::uint32_t> kSpecGroupDps{ 666, 3145 };

    constexpr float BookCloseSeconds(std::uint32_t bookHealth, std::uint32_t dps)
    {
        return dps ? static_cast<float>(bookHealth) / static_cast<float>(dps) : 0.f;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LB1 the shelf: six books in a random order, no repeat until all six have been read
    // ----------------------------------------------------------------------------------------------------------------

    class Shelf
    {
    public:
        // A fresh shuffled shelf. `rand(n)` returns [0, n).
        template <class Rand>
        void Shuffle(Rand&& rand)
        {
            for (std::uint8_t i = 0; i < kStoryCount; ++i)
                _order[i] = static_cast<Story>(i);
            for (std::uint8_t i = kStoryCount - 1; i > 0; --i)
            {
                std::uint32_t const j = static_cast<std::uint32_t>(rand(static_cast<std::uint32_t>(i) + 1));
                std::swap(_order[i], _order[std::min<std::uint32_t>(j, i)]);
            }
            _next = 0;
        }

        // The book he opens next.
        Story Peek() const { return _order[_next]; }

        // He opened it: the next one, a fresh shuffle once all six have been read. `rand` as Shuffle's.
        template <class Rand>
        Story Take(Rand&& rand)
        {
            Story const taken = _order[_next];
            if (++_next >= kStoryCount)
                Shuffle(rand);
            return taken;
        }

        // `.dbtest sm hollis open <story>`: that book next (swapped in from its place on this round's shelf; a book
        // already read this round is read again).
        void PutNext(Story s)
        {
            for (std::uint8_t i = _next; i < kStoryCount; ++i)
                if (_order[i] == s)
                {
                    std::swap(_order[i], _order[_next]);
                    return;
                }
            _order[_next] = s;
        }

        std::uint8_t ReadThisRound() const { return _next; }
        std::array<Story, kStoryCount> const& Order() const { return _order; }

    private:
        std::array<Story, kStoryCount> _order{ Story::Spider, Story::Archimonde, Story::TrollWars, Story::Titans,
            Story::Dream, Story::Aftermath };
        std::uint8_t _next = 0;
    };

    // Normal: no new book while 2 are open. Heroic: no cap.
    constexpr bool MayOpenBook(std::uint32_t openBooks, bool heroic)
    {
        return heroic || openBooks < kOpenBooksCapNormal;
    }

    // LB1 heroic: a finished Open the Index (nobody kicked it) opens the book on page 2; a kicked one on page 1.
    // Normal: always page 1 (no kick).
    constexpr std::uint8_t OpeningPage(bool heroic, bool kicked)
    {
        return heroic && !kicked ? 2 : 1;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LB1a pages: the next page (held at the cap), and what each story does on a page
    // ----------------------------------------------------------------------------------------------------------------

    constexpr std::uint8_t NextPage(std::uint8_t page, bool heroic)
    {
        std::uint8_t const cap = kPageCap(heroic);
        if (cap && page >= cap)
            return page;
        return page < 255 ? static_cast<std::uint8_t>(page + 1) : page;
    }

    // LB2: Spiderlings per web (2 on page 1, +1 a page).
    constexpr std::uint32_t SpiderlingsPerWeb(std::uint8_t page)
    {
        return 1u + std::max<std::uint32_t>(page, 1);
    }

    // LB2: the oldest web fades when the book holds more than this (normal 3; heroic none).
    constexpr bool WebsOverCap(std::uint32_t webs, bool heroic)
    {
        std::uint32_t const cap = kWebCap(heroic);
        return cap && webs > cap;
    }

    // LB3: meteors per fall (1 on page 1, +1 a page).
    constexpr std::uint32_t MeteorsPerFall(std::uint8_t page)
    {
        return std::max<std::uint32_t>(page, 1);
    }

    // LB3: a meteor raises an Infernal while the book has fewer than the cap alive (normal 2; heroic none).
    constexpr bool InfernalMayRise(std::uint32_t aliveInfernals, bool heroic)
    {
        std::uint32_t const cap = kInfernalCap(heroic);
        return !cap || aliveInfernals < cap;
    }

    // LB4: axes per volley (2 on page 1, +1 a page).
    constexpr std::uint32_t AxesPerVolley(std::uint8_t page)
    {
        return 1u + std::max<std::uint32_t>(page, 1);
    }

    // LB4: the line runs 35 yd from the troll: past the player by what is left (a player farther off is the end).
    constexpr float AxeOverrun(float distanceToPlayer)
    {
        return std::max(0.f, kAxeLengthYd - distanceToPlayer);
    }

    // LB5: rings per stomp (3 on page 1, +1 a page, at most 4: 32 yd).
    constexpr std::uint8_t StompRings(std::uint8_t page)
    {
        std::uint32_t const rings = kStompRingsBase + std::max<std::uint32_t>(page, 1) - 1;
        return static_cast<std::uint8_t>(std::min<std::uint32_t>(rings, kStompRingsMax));
    }

    struct StompRing
    {
        float inner = 0.f;              // 0: the first ring is a circle
        float outer = 0.f;
        std::uint32_t warnMs = 0;       // from the stomp's registration
    };

    // Ring `index` (0 first): 8 yd wide, each 1.5 s after the one before, the first 2 s after the stomp starts.
    constexpr StompRing StompRingAt(std::uint8_t index)
    {
        return { kStompRingYd * index, kStompRingYd * (index + 1), kStompWarnMs + kStompRingGapMs * index };
    }

    // LB6: the mist's radius on `page` (6 yd, +3 yd a page).
    constexpr float MistRadius(std::uint8_t page)
    {
        return kMistBaseYd + kMistPerPageYd * static_cast<float>(std::max<std::uint32_t>(page, 1) - 1);
    }

    // LB7: grunts per charge (1 on page 1, +1 a page: a second target).
    constexpr std::uint32_t GruntsPerCharge(std::uint8_t page)
    {
        return std::max<std::uint32_t>(page, 1);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LB6 Drowsy
    // ----------------------------------------------------------------------------------------------------------------

    struct DrowsyStep
    {
        std::uint8_t stacks = 0;
        bool sleep = false;             // five reached: the 2 s sleep, the stacks gone
    };

    // A stack is added by the mist's own tick (the registry's rider); this is the boss's check: at five the sleep,
    // and once a second a player outside every mist loses one.
    constexpr DrowsyStep DrowsyCheck(std::uint8_t stacks, bool insideMist, bool decayTick)
    {
        if (stacks >= kDrowsyMaxStacks)
            return { 0, true };
        if (decayTick && !insideMist && stacks > 0)
            return { static_cast<std::uint8_t>(stacks - 1), false };
        return { stacks, false };
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The kill order (F45: highest page first) and the adds' first target
    // ----------------------------------------------------------------------------------------------------------------

    // The descriptor priority of a book on `page` (the boss is 0): page 1 = 2, page 2 = 3, page 3 and up = 4.
    constexpr std::int8_t BookPriority(std::uint8_t page)
    {
        return static_cast<std::int8_t>(1 + std::clamp<std::uint32_t>(page, 1, 3));
    }
    inline constexpr std::int8_t kStoryAddPriority = -1;     // tanked, fade with their book: below him

    struct ArrivalCandidate
    {
        float distance = 0.f;
        bool tank = false;
    };

    // An Infernal's or a Spiderling's first target (rule 19): the nearest tank, else the nearest player. -1: none.
    inline int PickArrival(std::span<ArrivalCandidate const> candidates)
    {
        for (bool const tanksOnly : { true, false })
        {
            int best = -1;
            for (std::size_t i = 0; i < candidates.size(); ++i)
            {
                if (tanksOnly && !candidates[i].tank)
                    continue;
                if (best < 0 || candidates[i].distance < candidates[static_cast<std::size_t>(best)].distance)
                    best = static_cast<int>(i);
            }
            if (best >= 0)
                return best;
        }
        return -1;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Geometry: the reading hall (NAVMESH x 248-282, y -346 to -417, three lanes with tables between)
    // ----------------------------------------------------------------------------------------------------------------

    // His spot: the pocket (section 7 #26 A), r 6.9; floor z [db] from the hall's trash (20.48).
    inline constexpr Point3 kHollisGreyPocket{ 254.8f, -389.2f, 20.49f };
    inline constexpr float kHollisGreyFacing = 0.f;           // north, across the hall toward the aisle

    // The bots' bounds while he fights: the hall's floor rectangle (NAVMESH bbox x 247.75-282.25, y -344.25 to
    // -418.75), 1 yd in from the navmesh edge.
    inline constexpr std::array<Vec2, 4> kHallBounds{ Vec2{ 248.75f, -345.25f }, Vec2{ 281.25f, -345.25f },
        Vec2{ 281.25f, -417.75f }, Vec2{ 248.75f, -417.75f } };
    inline constexpr float kHallZMin = 18.f;
    inline constexpr float kHallZMax = 23.5f;

    // The hall's floor on a 3 yd grid, every point with at least 1.5 yd of clearance (NAVMESH, 2026-11-20; z is the
    // navmesh's, up to about 1 yd over the real floor: the script probes the floor under the point). The throw picks
    // from these, so a book never hangs over a table or outside the hall.
    inline constexpr std::array<Point3, 150> kHallFloor{ {
        { 249.0f, -350.0f, 21.5f }, { 249.0f, -353.0f, 21.4f }, { 249.0f, -368.0f, 21.5f }, { 249.0f, -386.0f, 21.5f },
        { 249.0f, -389.0f, 21.4f }, { 249.0f, -401.0f, 21.5f }, { 249.0f, -404.0f, 21.7f }, { 249.0f, -407.0f, 21.8f },
        { 252.0f, -347.0f, 21.4f }, { 252.0f, -350.0f, 21.3f }, { 252.0f, -353.0f, 21.2f }, { 252.0f, -356.0f, 21.2f },
        { 252.0f, -359.0f, 21.1f }, { 252.0f, -362.0f, 21.2f }, { 252.0f, -365.0f, 21.1f }, { 252.0f, -368.0f, 21.2f },
        { 252.0f, -371.0f, 21.2f }, { 252.0f, -374.0f, 21.3f }, { 252.0f, -383.0f, 21.2f }, { 252.0f, -386.0f, 21.1f },
        { 252.0f, -389.0f, 21.1f }, { 252.0f, -392.0f, 21.1f }, { 252.0f, -395.0f, 21.2f }, { 252.0f, -398.0f, 21.2f },
        { 252.0f, -401.0f, 21.2f }, { 252.0f, -404.0f, 21.2f }, { 252.0f, -407.0f, 21.4f }, { 252.0f, -410.0f, 21.5f },
        { 255.0f, -347.0f, 21.2f }, { 255.0f, -350.0f, 21.1f }, { 255.0f, -353.0f, 21.1f }, { 255.0f, -356.0f, 21.0f },
        { 255.0f, -359.0f, 20.9f }, { 255.0f, -362.0f, 20.8f }, { 255.0f, -365.0f, 20.9f }, { 255.0f, -368.0f, 21.0f },
        { 255.0f, -371.0f, 21.0f }, { 255.0f, -374.0f, 21.1f }, { 255.0f, -383.0f, 21.0f }, { 255.0f, -386.0f, 20.7f },
        { 255.0f, -389.0f, 20.7f }, { 255.0f, -392.0f, 20.7f }, { 255.0f, -395.0f, 20.7f }, { 255.0f, -398.0f, 20.7f },
        { 255.0f, -401.0f, 20.7f }, { 255.0f, -404.0f, 20.7f }, { 255.0f, -407.0f, 21.0f }, { 255.0f, -410.0f, 21.1f },
        { 258.0f, -350.0f, 21.3f }, { 258.0f, -353.0f, 21.4f }, { 258.0f, -356.0f, 21.4f }, { 258.0f, -368.0f, 21.4f },
        { 258.0f, -371.0f, 21.4f }, { 258.0f, -386.0f, 20.9f }, { 258.0f, -389.0f, 20.9f }, { 258.0f, -392.0f, 20.9f },
        { 258.0f, -404.0f, 20.5f }, { 258.0f, -407.0f, 20.5f }, { 261.0f, -353.0f, 20.3f }, { 261.0f, -356.0f, 20.3f },
        { 261.0f, -368.0f, 20.3f }, { 261.0f, -371.0f, 20.3f }, { 261.0f, -389.0f, 20.7f }, { 261.0f, -392.0f, 20.3f },
        { 261.0f, -404.0f, 20.5f }, { 261.0f, -407.0f, 20.5f }, { 264.0f, -350.0f, 20.7f }, { 264.0f, -353.0f, 20.7f },
        { 264.0f, -356.0f, 20.7f }, { 264.0f, -359.0f, 21.3f }, { 264.0f, -362.0f, 21.4f }, { 264.0f, -365.0f, 20.5f },
        { 264.0f, -368.0f, 20.3f }, { 264.0f, -371.0f, 20.3f }, { 264.0f, -374.0f, 20.4f }, { 264.0f, -383.0f, 21.1f },
        { 264.0f, -386.0f, 20.7f }, { 264.0f, -389.0f, 20.7f }, { 264.0f, -392.0f, 20.7f }, { 264.0f, -395.0f, 21.4f },
        { 264.0f, -398.0f, 21.4f }, { 264.0f, -401.0f, 20.6f }, { 264.0f, -404.0f, 20.5f }, { 264.0f, -407.0f, 20.5f },
        { 264.0f, -410.0f, 20.7f }, { 267.0f, -350.0f, 20.7f }, { 267.0f, -353.0f, 20.7f }, { 267.0f, -356.0f, 20.7f },
        { 267.0f, -368.0f, 20.3f }, { 267.0f, -371.0f, 20.3f }, { 267.0f, -386.0f, 20.7f }, { 267.0f, -389.0f, 20.7f },
        { 267.0f, -392.0f, 20.6f }, { 267.0f, -404.0f, 20.5f }, { 267.0f, -407.0f, 20.5f }, { 270.0f, -353.0f, 20.7f },
        { 270.0f, -356.0f, 20.6f }, { 270.0f, -368.0f, 20.6f }, { 270.0f, -371.0f, 20.7f }, { 270.0f, -389.0f, 20.7f },
        { 270.0f, -392.0f, 20.6f }, { 270.0f, -404.0f, 20.5f }, { 270.0f, -407.0f, 20.5f }, { 273.0f, -347.0f, 21.3f },
        { 273.0f, -350.0f, 21.2f }, { 273.0f, -353.0f, 21.0f }, { 273.0f, -356.0f, 20.8f }, { 273.0f, -365.0f, 20.9f },
        { 273.0f, -368.0f, 21.0f }, { 273.0f, -371.0f, 21.0f }, { 273.0f, -374.0f, 21.1f }, { 273.0f, -383.0f, 21.2f },
        { 273.0f, -386.0f, 20.8f }, { 273.0f, -389.0f, 20.7f }, { 273.0f, -392.0f, 20.6f }, { 273.0f, -401.0f, 20.6f },
        { 273.0f, -404.0f, 20.5f }, { 273.0f, -407.0f, 20.5f }, { 273.0f, -410.0f, 20.9f }, { 276.0f, -347.0f, 21.3f },
        { 276.0f, -350.0f, 21.2f }, { 276.0f, -353.0f, 21.0f }, { 276.0f, -356.0f, 20.9f }, { 276.0f, -359.0f, 20.7f },
        { 276.0f, -362.0f, 20.6f }, { 276.0f, -365.0f, 20.9f }, { 276.0f, -368.0f, 21.0f }, { 276.0f, -371.0f, 21.0f },
        { 276.0f, -374.0f, 21.1f }, { 276.0f, -383.0f, 21.0f }, { 276.0f, -386.0f, 20.9f }, { 276.0f, -389.0f, 20.8f },
        { 276.0f, -392.0f, 20.7f }, { 276.0f, -395.0f, 20.6f }, { 276.0f, -398.0f, 20.5f }, { 276.0f, -401.0f, 20.4f },
        { 276.0f, -404.0f, 20.6f }, { 276.0f, -407.0f, 20.4f }, { 276.0f, -410.0f, 21.0f }, { 279.0f, -350.0f, 21.4f },
        { 279.0f, -353.0f, 21.4f }, { 279.0f, -356.0f, 21.4f }, { 279.0f, -368.0f, 21.2f }, { 279.0f, -371.0f, 21.2f },
        { 279.0f, -386.0f, 21.1f }, { 279.0f, -389.0f, 21.1f }, { 279.0f, -392.0f, 21.1f }, { 279.0f, -401.0f, 21.2f },
        { 279.0f, -404.0f, 21.0f }, { 279.0f, -407.0f, 21.0f },
    } };

    // LB1's throw spot: a random floor point 10 to 20 yd from him (`from`) and at least kBookSpacingYd from every open
    // book; with none there, the spacing is dropped; with still none (he was pulled far off), the floor point nearest
    // to 15 yd from him. nullopt only for an empty floor list. `rand(n)` returns [0, n).
    template <class Rand>
    std::optional<std::size_t> PickThrowSpot(Vec2 from, std::span<Point3 const> floor, std::span<Vec2 const> books,
        Rand&& rand)
    {
        if (floor.empty())
            return std::nullopt;
        for (bool const spaced : { true, false })
        {
            std::vector<std::size_t> pool;
            for (std::size_t i = 0; i < floor.size(); ++i)
            {
                float const d = DungeonKit::Distance(from, floor[i].XY());
                if (d < kThrowMinYd || d > kThrowMaxYd)
                    continue;
                bool clear = true;
                if (spaced)
                    for (Vec2 const& b : books)
                        if (DungeonKit::Distance(b, floor[i].XY()) < kBookSpacingYd)
                            clear = false;
                if (clear)
                    pool.push_back(i);
            }
            if (!pool.empty())
                return pool[std::min<std::size_t>(rand(static_cast<std::uint32_t>(pool.size())), pool.size() - 1)];
        }
        std::size_t best = 0;
        float bestGap = 1e9f;
        float const mid = (kThrowMinYd + kThrowMaxYd) * 0.5f;
        for (std::size_t i = 0; i < floor.size(); ++i)
        {
            float const gap = std::fabs(DungeonKit::Distance(from, floor[i].XY()) - mid);
            if (gap < bestGap)
            {
                bestGap = gap;
                best = i;
            }
        }
        return best;
    }
}

#endif
