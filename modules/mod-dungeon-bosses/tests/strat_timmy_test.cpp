// Host tests for TimmyLogic.h (S3: Timmy the Cruel (10808)): the ids, the build spec numbers (ST 1035-1090), Playtime
// (timers, never health; the heroic pairs), the cast order of a pair, Freeze Tag's round (tags, bursts, Gotcha), the
// tag pick (never a frozen player), the burst's victims, the playmates' spots and focus, the rope's skips,
// and the arena.
#include "TimmyLogic.h"
#include "check.h"
#include <cmath>
#include <set>
#include <string>
#include <vector>

using namespace StratholmeRework;
using namespace StratTimmy;

namespace
{
    // Every Playtime event of a pull up to `endMs`, stepping `stepMs` (a long frame must not skip any).
    std::vector<Playtime::Event> Play(std::uint64_t endMs, std::uint64_t stepMs)
    {
        Playtime playtime;
        playtime.Reset();
        std::vector<Playtime::Event> out;
        for (std::uint64_t now = 0; now <= endMs; now += stepMs)
            for (Playtime::Event const& e : playtime.Advance(now))
                out.push_back(e);
        return out;
    }

    std::vector<std::uint64_t> TimesOf(std::vector<Playtime::Event> const& events, Playtime::Event::Kind kind)
    {
        std::vector<std::uint64_t> out;
        for (Playtime::Event const& e : events)
            if (e.kind == kind)
                out.push_back(e.at);
        return out;
    }
}

int main()
{
    // ---- ids and slice --------------------------------------------------------------------------------------------
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    CHECK(kSpellSlice.first == 206460 && kSpellSlice.last == 206479);
    CHECK(SPELL_TC_TAGGED == 206460 && SPELL_TC_TRIPPED == 206468);
    std::set<std::uint32_t> const ids{ SPELL_TC_TAGGED, SPELL_TC_FROZEN, SPELL_TC_SHATTER, SPELL_TC_PATTY_CAKE,
        SPELL_TC_CLAP, SPELL_TC_JUMP_ROPE, SPELL_TC_JUMP_ROPE_FAST, SPELL_TC_TRIP, SPELL_TC_TRIPPED };
    CHECK(ids.size() == 9);
    for (std::uint32_t id : ids)
        CHECK(kSpellSlice.Contains(id));
    // The Playmate is the wave 2 slice's (heroic mint order: it mints after the Gutter Rat, before the Infernal).
    CHECK(kCreaturesWave2.Contains(NPC_ST_PLAYMATE));
    CHECK(NPC_ST_PLAYMATE == 300604);
    CHECK(NPC_ST_GUTTER_RAT < NPC_ST_PLAYMATE && NPC_ST_PLAYMATE < NPC_ST_INFERNAL);
    // The kept stock kit.
    CHECK(SPELL_THRASH == 12787 && SPELL_RAVENOUS_CLAW == 17470 && SPELL_ENRAGE_TIMMY == 8599);
    // Texts: his lines 0-6 (0 the stock "TIMMY!"), the Playmate's line 0.
    CHECK(YELL_TIMMY_AGGRO == 0 && YELL_TIMMY_TAG == 1 && EMOTE_TIMMY_CLAP == 2 && YELL_TIMMY_TIMMIES == 3);
    CHECK(YELL_TIMMY_JUMP == 4 && EMOTE_TIMMY_JUMP_ROPE == 5 && YELL_TIMMY_DEATH == 6 && YELL_PLAYMATE_TIMMY == 0);
    // Tags are distinct.
    std::set<std::uint32_t> const tags{ TAG_TAG, TAG_THAW, TAG_SHATTER, TAG_JUMP_ROPE };
    CHECK(tags.size() == 4);

    // ---- the build spec's numbers ---------------------------------------------------------------------------------
    CHECK(kFreezeFirstMs == 8000 && kFreezeEveryMs == 40000);
    CHECK(kSlotFirstMs == 20000 && kSlotEveryMs == 15000);
    CHECK(kRoundMs == 15000 && kTagEveryMs == 3000 && kTagWarnMs == 2000);
    CHECK(kTagRadius == 6.f && kThawRadius == 3.f);
    CHECK(kFrozenSlowPct == 70 && kFrozenTickPct == 2.f && kShatterPct == 30.f);
    CHECK(kFrozenMs > kRoundMs);
    CHECK(kPattyCakeMs == 4000 && kClaps == 4 && kClapEveryMs == 1000);
    CHECK(kClapPct(false) == 10.f && kClapPct(true) == 20.f);
    // A full channel: 40% normal, 80% heroic (ST TC6, ruling 16).
    CHECK(kClapPct(false) * kClaps == 40.f && kClapPct(true) * kClaps == 80.f);
    CHECK(kPlaymates(false) == 3 && kPlaymates(true) == 4);
    CHECK(kPlaymateHealth(false) == 5000 && kPlaymateHealth(true) == 7000);
    CHECK(kTripPct == 25.f && kTrippedMs == 1000);
    CHECK(kClawMinMs == 10000 && kClawMaxMs == 15000 && kEnrageAtPct == 50.f);
    // The stock gate and emerge.
    CHECK(kGateEntries.size() == 4 && kGateEntries[0] == 10418 && kGateEntries[3] == 10424);
    CHECK(kGateRangeYd == 70.f && kGateCheckMs == 10000 && kEmergeMs == 3500 && kEmoteEmerge == 449);
    CHECK(kPatrolPath == 2472270);
    // Every hit stays under 50% of the reference row (Weakened is the penalty, not a one-shot).
    CHECK(kShatterPct < 50.f && kTripPct < 50.f && kClapPct(true) < 50.f);

    // ---- TC1 Playtime: Freeze Tag at 8 s then every 40 s; slots every 15 s from 20 s ------------------------------
    {
        std::vector<Playtime::Event> const events = Play(140000, 50);
        std::vector<std::uint64_t> const rounds = TimesOf(events, Playtime::Event::Kind::FreezeTag);
        std::vector<std::uint64_t> const slots = TimesOf(events, Playtime::Event::Kind::Slot);
        CHECK(rounds == (std::vector<std::uint64_t>{ 8000, 48000, 88000, 128000 }));
        CHECK(slots == (std::vector<std::uint64_t>{ 20000, 35000, 50000, 65000, 80000, 95000, 110000, 125000,
            140000 }));
        // In order, numbered from 0.
        for (std::size_t i = 1; i < events.size(); ++i)
            CHECK(events[i - 1].at <= events[i].at);
        std::uint32_t round = 0;
        std::uint32_t slot = 0;
        for (Playtime::Event const& e : events)
            CHECK(e.index == (e.kind == Playtime::Event::Kind::FreezeTag ? round++ : slot++));
        // A long frame catches up without losing one.
        std::vector<Playtime::Event> const coarse = Play(140000, 7000);
        CHECK(coarse.size() == events.size());
        CHECK(TimesOf(coarse, Playtime::Event::Kind::FreezeTag) == rounds);
        CHECK(TimesOf(coarse, Playtime::Event::Kind::Slot) == slots);
        // Nothing before 8 s.
        Playtime p;
        p.Reset();
        CHECK(p.Advance(7999).empty());
        CHECK(p.Advance(8000).size() == 1);
        CHECK(p.NextRoundAt() == 48000 && p.NextSlotAt() == 20000);
    }

    // ---- TC1 games of a slot: normal one, heroic two (rotating pairs) ---------------------------------------------
    {
        CHECK(GamesOfSlot(0, false).count == 1 && GamesOfSlot(0, false).games[0] == Game::GuessWho);
        CHECK(GamesOfSlot(1, false).games[0] == Game::JumpRope);
        CHECK(GamesOfSlot(2, false).games[0] == Game::PattyCake);
        CHECK(GamesOfSlot(3, false).games[0] == Game::GuessWho);
        SlotGames const h0 = GamesOfSlot(0, true);
        SlotGames const h1 = GamesOfSlot(1, true);
        SlotGames const h2 = GamesOfSlot(2, true);
        CHECK(h0.count == 2 && HasGame(h0, Game::GuessWho) && HasGame(h0, Game::JumpRope));
        CHECK(h1.count == 2 && HasGame(h1, Game::PattyCake) && HasGame(h1, Game::GuessWho));
        CHECK(h2.count == 2 && HasGame(h2, Game::JumpRope) && HasGame(h2, Game::PattyCake));
        CHECK(GamesOfSlot(3, true).games == h0.games);
        // Every game plays once in every three slots on normal and twice on heroic.
        for (Game game : { Game::GuessWho, Game::JumpRope, Game::PattyCake })
        {
            std::uint32_t normal = 0;
            std::uint32_t heroic = 0;
            for (std::uint32_t s = 0; s < 3; ++s)
            {
                normal += HasGame(GamesOfSlot(s, false), game) ? 1 : 0;
                heroic += HasGame(GamesOfSlot(s, true), game) ? 1 : 0;
            }
            CHECK(normal == 1);
            CHECK(heroic == 2);
        }
        // A pair never holds the same game twice.
        for (std::uint32_t s = 0; s < 3; ++s)
            CHECK(GamesOfSlot(s, true).games[0] != GamesOfSlot(s, true).games[1]);
        // Cast order: one cast at a time, Patty Cake first; Guess Who is not a cast.
        CHECK(CastOrder(h0) == (std::vector<Game>{ Game::JumpRope }));
        CHECK(CastOrder(h1) == (std::vector<Game>{ Game::PattyCake }));
        CHECK(CastOrder(h2) == (std::vector<Game>{ Game::PattyCake, Game::JumpRope }));
        CHECK(CastOrder(GamesOfSlot(0, false)).empty());
        CHECK(!IsCast(Game::GuessWho) && IsCast(Game::JumpRope) && IsCast(Game::PattyCake));
        // The back-to-back pair fits its slot, the Double Dutch fallback included.
        CHECK(kPattyCakeMs + RopeMs(false) < kSlotEveryMs);
        CHECK(kPattyCakeMs + RopeMs(true) < kSlotEveryMs);
        CHECK(std::string(GameName(Game::PattyCake)) == "patty-cake");
    }

    // ---- TC2-TC5 a Freeze Tag round ---------------------------------------------------------------------------------
    {
        FreezeRound r;
        CHECK(!r.Active() && !r.TagDue(0) && !r.Over(100000, 5, 5));
        r.Begin(8000);
        CHECK(r.Active() && r.EndsAt() == 23000);
        std::vector<std::uint64_t> tagsAt;
        for (std::uint64_t now = 8000; now <= 23000; now += 50)
            if (r.TagDue(now))
                tagsAt.push_back(now);
        CHECK(tagsAt == (std::vector<std::uint64_t>{ 8000, 11000, 14000, 17000, 20000 }));
        CHECK(r.Tags() == kTagsPerRound);
        // Every burst (2 s after its tag) lands inside the round.
        for (std::uint64_t at : tagsAt)
            CHECK(at + kTagWarnMs <= r.EndsAt());
        // Gotcha: time, or everyone frozen at once; never with nobody alive.
        CHECK(!r.Over(22999, 5, 4));
        CHECK(r.Over(23000, 5, 0));
        CHECK(r.Over(12000, 5, 5));
        CHECK(r.Over(12000, 1, 1));
        CHECK(!r.Over(12000, 0, 0));
        r.End();
        CHECK(!r.Active() && !r.Over(30000, 5, 5));
        // A long frame does not lose a tag (they come one per call).
        FreezeRound late;
        late.Begin(0);
        CHECK(late.TagDue(9500) && late.TagDue(9500) && late.TagDue(9500) && late.TagDue(9500));
        CHECK(!late.TagDue(9500));
        // Rounds never overlap: 15 s in a 40 s cadence.
        CHECK(kRoundMs < kFreezeEveryMs);
    }

    // ---- TC2 the tag pick: never a frozen player, the tank too ------------------------------------------------------
    {
        std::vector<TagCandidate> const c{ { 1, true }, { 2, false }, { 3, true }, { 4, false } };
        std::set<std::uint64_t> picked;
        for (std::uint32_t k = 0; k < 8; ++k)
        {
            std::optional<std::uint64_t> const p = PickTag(c, [k](std::uint32_t n) { return k % n; });
            CHECK(p.has_value());
            if (p)
            {
                CHECK(*p == 2 || *p == 4);
                picked.insert(*p);
            }
        }
        CHECK(picked.size() == 2);
        std::vector<TagCandidate> const all{ { 1, true }, { 2, true } };
        CHECK(!PickTag(all, [](std::uint32_t) { return 0u; }).has_value());
        CHECK(!PickTag(std::vector<TagCandidate>{}, [](std::uint32_t) { return 0u; }).has_value());
        // A bad random number never reads past the pool.
        CHECK(PickTag(c, [](std::uint32_t n) { return n + 5; }) == std::optional<std::uint64_t>(4));
    }

    // ---- TC3 the burst's victims ------------------------------------------------------------------------------------
    {
        CHECK(BurstVictims(7, { 3, 4 }) == (std::vector<std::uint64_t>{ 7, 3, 4 }));
        CHECK(BurstVictims(7, { 7, 3, 3 }) == (std::vector<std::uint64_t>{ 7, 3 }));
        CHECK(BurstVictims(std::nullopt, { 3 }) == (std::vector<std::uint64_t>{ 3 }));
        CHECK(BurstVictims(std::nullopt, {}).empty());
        // A stacked group of five is frozen by one burst.
        CHECK(BurstVictims(1, { 2, 3, 4, 5 }).size() == 5);
    }

    // ---- TC7 the playmates ------------------------------------------------------------------------------------------
    {
        std::vector<Vec2> const normal = PlaymateSpots(false);
        std::vector<Vec2> const heroic = PlaymateSpots(true);
        CHECK(normal.size() == kPlaymates(false));
        CHECK(heroic.size() == kPlaymates(true));
        // Every spot is on the square (his arena), at its edges: 15 yd or more from its middle.
        Arena const arena = TimmyArena();
        for (Vec2 const& s : heroic)
        {
            CHECK(arena.Contains(s, 127.f));
            CHECK(DungeonKit::Distance(s, Vec2{ 3668.0f, -3176.0f }) >= 15.f);
        }
        CHECK(heroic.back().x == kTimmyHeroicBurst.x && heroic.back().y == kTimmyHeroicBurst.y);
        // The cap.
        CHECK(PlaymatesToSummon(false, 0) == 3 && PlaymatesToSummon(true, 0) == 4);
        CHECK(PlaymatesToSummon(true, kPlaymateCap - 2) == 2);
        CHECK(PlaymatesToSummon(true, kPlaymateCap) == 0 && PlaymatesToSummon(false, kPlaymateCap + 3) == 0);
        // Focus: the nearest frozen player; nobody frozen: none.
        std::vector<FocusCandidate> const c{ { 1, false, 2.f }, { 2, true, 20.f }, { 3, true, 9.f } };
        CHECK(PlaymateFocus(c) == std::optional<std::uint64_t>(3));
        std::vector<FocusCandidate> const none{ { 1, false, 2.f }, { 2, false, 1.f } };
        CHECK(!PlaymateFocus(none).has_value());
        CHECK(!PlaymateFocus({}).has_value());
    }

    // ---- TC8 / TC9 the rope -----------------------------------------------------------------------------------------
    {
        CHECK(SkipsOf(false) == (std::vector<std::uint32_t>{ 2000, 2000, 2000 }));
        CHECK(SkipsOf(true) == (std::vector<std::uint32_t>{ 2000, 2000, 1500, 1500, 1500 }));
        CHECK(RopeMs(false) == 6000 && RopeMs(true) == 8500);
        CHECK(SkipSpell(2000) == SPELL_TC_JUMP_ROPE && SkipSpell(1500) == SPELL_TC_JUMP_ROPE_FAST);
        CHECK(!kHeroicDoubleDutch);
        // One Jump per skip, its warning the cast: every skip is long enough for a bot's hop (X3: at least ~0.3 s).
        for (std::uint32_t ms : SkipsOf(true))
            CHECK(ms >= 1000);
        // The sweep covers the whole square: the arena's circle, its height band inside the sweep's.
        CHECK(kRopeRadius == 52.f);
        CHECK(kRopeZ - kRopeZTolerance <= 126.f && kRopeZ + kRopeZTolerance >= 136.f);
        // Every point of the patrol path and his spawn lies inside the sweep.
        Vec2 const center{ 3668.0f, -3176.0f };
        CHECK(DungeonKit::Distance(kTimmySpawn.XY(), center) <= kRopeRadius);
    }

    // ---- the arena ------------------------------------------------------------------------------------------------
    CHECK(TimmyArena().Contains(kTimmySpawn.XY(), kTimmySpawn.z));
    CHECK(ArenaFor(BOSS_TIMMY).Contains(kTimmySpawn.XY(), kTimmySpawn.z));
    for (Vec2 const& b : kTimmyBursts)
        CHECK(TimmyArena().Contains(b, 127.f));

    return Report("strat_timmy_test");
}
