/*
 * mod-dungeon-bosses, Stratholme S2: Hearthsinger Forresten (10558), the pure, host-testable part (no engine
 * headers). Build spec ST 826-882 (docs/dungeons/stratholme-rework.md), handoff section 3.4 rows HF and 3.5 row S2.
 * Tested by tests/strat_forresten_test.cpp.
 *
 *   Spells         the WP's ids, inside kSpellsForresten (206440-206459), declared in apps/dbc-tools
 *                  source/npcs/stratholme/hearthsinger_forresten.py
 *   Tuning         NH<> constants and pairs: one number per difficulty, straight from the build spec
 *   SetList        HF1 the fixed rotation Jig, Lullaby, Piper's Tune on timers (first song at 6 s; songs 20 s / 18 s,
 *                  breaks 6 s / 4 s), never on health
 *   RatsAtStart    HF2 how many Gutter Rats a song calls
 *   NoteCount      HF4 how many players a beat drops a note under (two, or every player on heroic)
 *   DrowsyStep     HF6 a Drowsy tick: +1 stack, three stacks put the player to sleep for 2 s and clear the stacks
 *   InHearth       HF5 / HF6 the hearth's 8 yd circle (planar, with a height band)
 *   HearthRules    HF5 / HF10 where the hearth lights: 10..15 yd from him (moved: 15..20), away from the old one
 *   TurnOrder      HF7 players are taken in turn, so every player draws volley lines
 *   AimPoint       HF7 a point 0 to 4 yd from a player in a random direction
 *   LaneEnd        HF7 / HF11 the end of a line from him through an aim point: his back wall, or the cap
 *   Volley         HF7 the queue: one line every 0.5 s while rats are staged; the second volley's start
 *   LullabyFocus   HF2 / HF6 which player the rats go for during The Lullaby (asleep, then most Drowsy)
 *   BiteStacks     HF3 Plague Bite: +1 stack per rat bite, at most 5
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_FORRESTEN_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_FORRESTEN_LOGIC_H

#include "DungeonKitFloor.h"
#include "DungeonKitMath.h"
#include "StratholmeRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <set>
#include <utility>
#include <vector>

namespace StratForresten
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsForresten;

    enum ForrestenSpells : std::uint32_t
    {
        SPELL_HF_NOTE               = kSpellSlice.first + 0,    // 206440 HF4 the note's hit (resolve copy, Arcane)
        SPELL_HF_DANCE              = kSpellSlice.first + 1,    // 206441 HF4 the 1.5 s dance (the note's rider)
        SPELL_HF_DROWSY             = kSpellSlice.first + 2,    // 206442 HF6 the stacking debuff, three stacks sleep
        SPELL_HF_ASLEEP             = kSpellSlice.first + 3,    // 206443 HF6 the 2 s sleep
        SPELL_HF_RAT_LINE           = kSpellSlice.first + 4,    // 206444 HF7 a rat line's hit (resolve copy, Physical)
        SPELL_HF_CRESCENDO_LINE     = kSpellSlice.first + 5,    // 206445 HF11 the big line's hit (resolve copy)
        SPELL_HF_CRESCENDO          = kSpellSlice.first + 6,    // 206446 HF8 the 3 s interruptible cast
        SPELL_HF_PLAGUE_BITE        = kSpellSlice.first + 7,    // 206447 HF3 the rats' Disease DoT
        SPELL_HF_HEARTH_GLOW        = kSpellSlice.first + 8,    // 206448 HF5 the hearth's glow, on its stalker
        // 206449-206459 spare
    };
    static_assert(SPELL_HF_HEARTH_GLOW <= kSpellSlice.last, "Forresten's spells must stay in his slice");

    // Registry tags (one per mechanic; the failure ledger and the playtest greps key on them).
    enum ForrestenTags : std::uint32_t
    {
        TAG_NOTE            = 1,    // HF4
        TAG_HEARTH          = 2,    // HF5 / HF10
        TAG_RAT_LINE        = 3,    // HF7
        TAG_CRESCENDO_LINE  = 4,    // HF11
    };

    // Emote state 10 (EMOTE_STATE_DANCE): the dance of the note's rider (V-2 EMOTE_STATE_DANCE).
    inline constexpr std::uint32_t kEmoteStateDance = 10;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (ST 826-882; percents of the reference row: N 3,670 / 3,710, H 4,120 / 4,110)
    // ----------------------------------------------------------------------------------------------------------------

    enum class Song : std::uint8_t
    {
        Jig,
        Lullaby,
        Piper,
    };

    inline constexpr char const* SongName(Song song)
    {
        return song == Song::Jig ? "jig" : (song == Song::Lullaby ? "lullaby" : "piper");
    }

    inline constexpr Song NextSong(Song song)
    {
        return song == Song::Jig ? Song::Lullaby : (song == Song::Lullaby ? Song::Piper : Song::Jig);
    }

    // HF1 Set list: the first song at 6 s; a song 20 s (heroic 18 s), a break 6 s (heroic 4 s); he shoots in the
    // breaks. The cadence is song start to song start.
    inline constexpr std::uint32_t kFirstSongMs = 6000;
    inline constexpr NH<std::uint32_t> kSongMs{ 20000, 18000 };
    inline constexpr NH<std::uint32_t> kBreakMs{ 6000, 4000 };

    // HF2 Gutter Rats: pour out of the gutters at the start of each song: 6 at the Jig and the Lullaby, 3 at the
    // Piper's Tune (heroic 8, 8, 4). No cap in the build spec; kRatCap is a safety valve against a wipe loop.
    inline constexpr NH<std::uint32_t> kRatsJigLullaby{ 6, 8 };
    inline constexpr NH<std::uint32_t> kRatsPiper{ 3, 4 };
    inline constexpr std::uint32_t kRatCap = 40;

    inline constexpr std::uint32_t RatsAtStart(Song song, bool heroic)
    {
        return song == Song::Piper ? kRatsPiper(heroic) : kRatsJigLullaby(heroic);
    }

    // HF3 Plague Bite: a Disease, 1% a second a stack, up to 5 stacks, 10 s. Every rat bite that lands adds a stack
    // (cast with the boss as the caster, so the rats' stacks add up).
    inline constexpr std::uint32_t kBiteMaxStacks = 5;
    inline constexpr std::uint32_t kBiteMs = 10000;

    inline constexpr std::uint32_t BiteStacks(std::uint32_t now)
    {
        return now >= kBiteMaxStacks ? kBiteMaxStacks : now + 1;
    }

    // HF4 Note (The Jig): a beat every 2 s (1 s after a missed Crescendo) drops a 4 yd circle, a 1.5 s marker, under 2
    // random players (heroic: every player) and 2 random spots: 20% Arcane + Weakened + a 1.5 s dance. The first beat
    // comes a second into the song.
    inline constexpr std::uint32_t kJigFirstBeatMs = 1000;
    inline constexpr NH<std::uint32_t> kJigBeatMs{ 2000, 2000 };
    inline constexpr std::uint32_t kJigDoubleBeatMs = 1000;
    inline constexpr float kNoteRadius = 4.f;
    inline constexpr std::uint32_t kNoteWarnMs = 1500;
    inline constexpr float kNotePct = 20.f;
    inline constexpr std::uint32_t kNotePlayersNormal = 2;
    inline constexpr std::uint32_t kNoteSpots = 2;
    inline constexpr float kNoteSpotMaxYd = 24.f;           // random spots lie this near the arena's center
    inline constexpr float kNoteSpotAwayYd = 4.f;           // and this far from the note under a player
    inline constexpr std::uint32_t kDanceMs = 1500;

    inline constexpr std::uint32_t NoteCount(bool heroic, std::uint32_t players)
    {
        return heroic ? players : std::min(kNotePlayersNormal, players);
    }

    // HF5 Hearth (The Lullaby): an 8 yd circle 10..15 yd from him; non-tanks outside it gain Drowsy every 2 s; at 3
    // stacks they sleep for 2 s and the stacks clear; tanks are exempt. HF10: a missed Crescendo moves it 15..20 yd,
    // with a 2 s glow before it counts.
    inline constexpr float kHearthRadius = 8.f;
    inline constexpr float kHearthZBand = 6.f;
    inline constexpr std::pair<float, float> kHearthRing{ 10.f, 15.f };
    inline constexpr std::pair<float, float> kMovedHearthRing{ 15.f, 20.f };
    inline constexpr float kHearthAwayFromOldYd = 8.f;
    inline constexpr std::uint32_t kMovedGlowMs = 2000;
    inline constexpr std::uint32_t kDrowsyTickMs = 2000;
    inline constexpr std::uint32_t kDrowsyToSleep = 3;
    inline constexpr std::uint32_t kDrowsyMs = 6000;
    inline constexpr std::uint32_t kSleepMs = 2000;

    struct DrowsyResult
    {
        std::uint32_t stacks = 0;   // the stacks after the tick (0 when the sleep begins)
        bool sleep = false;
    };

    inline constexpr DrowsyResult DrowsyStep(std::uint32_t stacksNow)
    {
        std::uint32_t const next = stacksNow + 1;
        if (next >= kDrowsyToSleep)
            return { 0, true };
        return { next, false };
    }

    // The planar circle with a height band (a player on another level is not in it).
    inline bool InHearth(float dist2d, float dz)
    {
        return dist2d <= kHearthRadius && std::fabs(dz) <= kHearthZBand;
    }

    // Where the hearth lights: a floor spot in the ring around him, away from the old one (a moved hearth). The
    // measured hearths of the navmesh report are the fallbacks (StratholmeRework.h kForrestenHearths and
    // kForrestenMovedHearths).
    inline DungeonKit::FloorSpotRules HearthRules(Vec2 boss, bool moved, std::optional<Vec2> old)
    {
        DungeonKit::FloorSpotRules rules;
        rules.near = boss;
        std::pair<float, float> const ring = moved ? kMovedHearthRing : kHearthRing;
        rules.minRange = ring.first;
        rules.maxRange = ring.second;
        rules.tries = 24;
        rules.bestEffort = true;
        if (old)
        {
            rules.awayFrom.push_back(*old);
            rules.minFromAway = kHearthAwayFromOldYd;
        }
        return rules;
    }

    inline std::vector<Vec2> HearthFallbacks(bool moved)
    {
        if (moved)
            return std::vector<Vec2>(StratholmeRework::kForrestenMovedHearths.begin(),
                StratholmeRework::kForrestenMovedHearths.end());
        return std::vector<Vec2>(StratholmeRework::kForrestenHearths.begin(),
            StratholmeRework::kForrestenHearths.end());
    }

    // HF2 / HF6 during The Lullaby the rats go for the drowsy and the sleeping first.
    struct FocusCandidate
    {
        std::uint64_t id = 0;
        bool asleep = false;
        std::uint32_t drowsy = 0;
        float distToRat = 0.f;
    };

    // Asleep first, then the most Drowsy stacks, then the nearest; nullopt when nobody is drowsy or asleep.
    inline std::optional<std::uint64_t> LullabyFocus(std::vector<FocusCandidate> const& candidates)
    {
        std::optional<FocusCandidate> best;
        for (FocusCandidate const& c : candidates)
        {
            if (!c.asleep && c.drowsy == 0)
                continue;
            if (!best)
            {
                best = c;
                continue;
            }
            if (c.asleep != best->asleep)
            {
                if (c.asleep)
                    best = c;
                continue;
            }
            if (c.drowsy != best->drowsy)
            {
                if (c.drowsy > best->drowsy)
                    best = c;
                continue;
            }
            if (c.distToRat < best->distToRat)
                best = c;
        }
        if (!best)
            return std::nullopt;
        return best->id;
    }

    // HF8 Crescendo: once per song, 5 to 12 s into it, a 3 s interruptible cast. Not interrupted: the Jig goes double
    // time, the Lullaby's hearth moves, the Piper's Tune adds a big line at each non-tank; heroic: 4 more rats.
    inline constexpr std::pair<std::uint32_t, std::uint32_t> kCrescendoWindowMs{ 5000, 12000 };
    inline constexpr std::uint32_t kCrescendoCastMs = 3000;
    inline constexpr NH<std::uint32_t> kMissedRats{ 0, 4 };

    inline std::uint32_t CrescendoOffsetMs(float rand01)
    {
        float const u = std::clamp(rand01, 0.f, 1.f);
        return kCrescendoWindowMs.first + static_cast<std::uint32_t>(
            u * static_cast<float>(kCrescendoWindowMs.second - kCrescendoWindowMs.first));
    }

    // HF11: a 6 yd line from him through each non-tank, a 2 s marker, 30% + Weakened, out to the wall (capped).
    inline constexpr float kBigLineWidth = 6.f;
    inline constexpr std::uint32_t kBigLineWarnMs = 2000;
    inline constexpr float kBigLinePct = 30.f;
    inline constexpr float kBigLineCapYd = 60.f;

    // HF7 Rat volley (The Piper's Tune): every rat still alive falls in behind him and streams out, one 2 yd line per
    // rat, a new line every 0.5 s, each aimed 0..4 yd from a player taken in turn (the tank too), a 2 s marker that
    // stays until the rat is back; 15% + Weakened. The first volley starts 4 s into the song; the second 2 s after
    // the first's last line, when at least 3 s of the song remain. The rat runs the line out and back at
    // kRatRunSpeed; the registry tracks it (declared speed kRatLineSpeed, a little under, so the registry's own
    // expiry never ends a line before the rat is back). A line never runs longer than kRatLineCapYd.
    inline constexpr std::uint32_t kVolleyFirstMs = 4000;
    inline constexpr std::uint32_t kVolleyLineEveryMs = 500;
    inline constexpr std::uint32_t kVolleySecondGapMs = 2000;
    inline constexpr std::uint32_t kVolleySecondMinLeftMs = 3000;
    inline constexpr std::uint32_t kVolleyAssembleTimeoutMs = 8000;   // a rat that never reaches him is dropped
    inline constexpr float kRatLineWidth = 2.f;
    inline constexpr std::uint32_t kRatLineWarnMs = 2000;
    inline constexpr float kRatLinePct = 15.f;
    inline constexpr float kRatLineCapYd = 30.f;
    inline constexpr float kRatAimMaxYd = 4.f;
    inline constexpr float kRatRunSpeed = 12.f;                 // yd/s: the rat's spline
    inline constexpr float kRatLineSpeed = 11.5f;               // yd/s: the registry's projectile
    inline constexpr float kRatStagedYd = 3.f;                  // "in behind him": this near the gather point
    inline constexpr std::uint32_t kRatFocusEveryMs = 1000;     // how often the Lullaby retargets the rats
    static_assert(kRatLineSpeed < kRatRunSpeed, "the registry's expiry must not end a line before its rat is back");

    // His back wall (navmesh report: (3590, -3492) through (3596, -3514) to (3612, -3525)), extended 10 yd at both
    // ends along its own direction. A line that meets it stops there (the rats' lines are short on that side).
    inline constexpr std::array<Vec2, 5> kBackWall{ {
        { 3587.4f, -3482.4f }, { 3590.0f, -3492.0f }, { 3596.0f, -3514.0f }, { 3612.0f, -3525.0f },
        { 3620.2f, -3530.7f } } };

    // The gutters the rats pour out of [navmesh estimate, report section 2]: his back wall, the square's east and west
    // edges, and the avenue's north-west wall. A wave takes them in a random order, wrapping when it is larger.
    inline constexpr std::array<StratholmeRework::Point3, 10> kGutters{ {
        { 3588.5f, -3488.5f, 136.0f }, { 3604.0f, -3516.5f, 138.1f },
        { 3615.0f, -3534.0f, 138.7f }, { 3628.0f, -3536.0f, 139.2f }, { 3640.0f, -3534.5f, 138.8f },
        { 3612.0f, -3478.5f, 137.2f }, { 3625.0f, -3480.0f, 138.6f }, { 3638.0f, -3476.5f, 138.5f },
        { 3598.0f, -3461.0f, 136.5f }, { 3580.0f, -3455.0f, 137.2f } } };

    // Distance along the ray from `origin` (looking along `orientation`) to the nearest segment of the open polyline.
    inline std::optional<float> RayToPolyline(std::array<Vec2, 5> const& poly, Vec2 origin, float orientation)
    {
        float const dx = std::cos(orientation);
        float const dy = std::sin(orientation);
        std::optional<float> best;
        for (std::size_t i = 1; i < poly.size(); ++i)
        {
            Vec2 const a = poly[i - 1];
            Vec2 const b = poly[i];
            float const ex = b.x - a.x;
            float const ey = b.y - a.y;
            float const denom = dx * ey - dy * ex;
            if (std::fabs(denom) < 1e-6f)
                continue;
            float const ox = a.x - origin.x;
            float const oy = a.y - origin.y;
            float const t = (ox * ey - oy * ex) / denom;
            float const s = (ox * dy - oy * dx) / denom;
            if (t > 1e-4f && s >= 0.f && s <= 1.f && (!best || t < *best))
                best = t;
        }
        return best;
    }

    // The end of a line from `from` through `through`: at most `capYd` long, stopping 0.5 yd short of his back wall.
    inline Vec2 LaneEnd(Vec2 from, Vec2 through, float capYd)
    {
        float const orientation = DungeonKit::BearingTo(from, through);
        float length = capYd;
        if (std::optional<float> const wall = RayToPolyline(kBackWall, from, orientation))
            length = std::min(length, std::max(0.f, *wall - 0.5f));
        return DungeonKit::Advance(from, orientation, length);
    }

    // A point 0..4 yd from `player` in a random direction (`angle01`, `dist01` in [0, 1)).
    inline Vec2 AimPoint(Vec2 player, float angle01, float dist01)
    {
        return DungeonKit::Advance(player, angle01 * DungeonKit::kTwoPi, dist01 * kRatAimMaxYd);
    }

    // Players are taken in turn: each cycle every id comes up once, in random order; the cycle starts over when all
    // the ids still present have had theirs. An id that left is skipped; one that joined takes its turn this cycle.
    class TurnOrder
    {
    public:
        void Reset() { _taken.clear(); }

        // `pick(n)` returns an index in [0, n).
        template <class Pick>
        std::optional<std::uint64_t> Next(std::vector<std::uint64_t> const& ids, Pick&& pick)
        {
            if (ids.empty())
                return std::nullopt;
            std::vector<std::uint64_t> left = Left(ids);
            if (left.empty())
            {
                _taken.clear();
                left = ids;
            }
            std::size_t index = static_cast<std::size_t>(pick(static_cast<std::uint32_t>(left.size())));
            if (index >= left.size())
                index = left.size() - 1;
            _taken.insert(left[index]);
            return left[index];
        }

    private:
        std::vector<std::uint64_t> Left(std::vector<std::uint64_t> const& ids) const
        {
            std::vector<std::uint64_t> out;
            for (std::uint64_t id : ids)
                if (!_taken.count(id))
                    out.push_back(id);
            return out;
        }

        std::set<std::uint64_t> _taken;
    };

    // One volley's queue. `staged` is the number of rats waiting at his back that have not run yet; `waiting` the
    // number still on their way to him. A line is due every kVolleyLineEveryMs while a rat is staged; the volley ends
    // when no rat is left to launch.
    class Volley
    {
    public:
        void Reset()
        {
            *this = Volley();
        }

        void Begin(std::uint64_t now)
        {
            Reset();
            _active = true;
            _beganAt = now;
            _nextLineAt = now;
        }

        bool Active() const { return _active; }
        std::uint64_t BeganAt() const { return _beganAt; }
        std::uint32_t Launched() const { return _launched; }
        std::uint64_t LastLaunchAt() const { return _lastLaunchAt; }

        bool LineDue(std::uint64_t now, std::uint32_t staged) const
        {
            return _active && staged > 0 && now >= _nextLineAt;
        }

        void LineLaunched(std::uint64_t now)
        {
            ++_launched;
            _lastLaunchAt = now;
            _nextLineAt = now + kVolleyLineEveryMs;
        }

        // True once nothing is staged and nothing is left on its way: the volley is over.
        bool Done(std::uint32_t staged, std::uint32_t waiting) const
        {
            return _active && staged == 0 && waiting == 0;
        }

        void End()
        {
            _active = false;
        }

    private:
        bool _active = false;
        std::uint64_t _beganAt = 0;
        std::uint64_t _nextLineAt = 0;
        std::uint64_t _lastLaunchAt = 0;
        std::uint32_t _launched = 0;
    };

    // The second volley of a song: 2 s after the first's last line, when at least 3 s of the song remain then.
    inline std::optional<std::uint64_t> SecondVolleyAt(std::uint64_t firstLastLineMs, std::uint64_t songEndMs)
    {
        std::uint64_t const at = firstLastLineMs + kVolleySecondGapMs;
        if (at >= songEndMs || songEndMs - at < kVolleySecondMinLeftMs)
            return std::nullopt;
        return at;
    }

    // How long a rat takes to run a line of `lengthYd` out and back.
    inline std::uint32_t RatRunMs(float lengthYd)
    {
        return static_cast<std::uint32_t>(std::ceil(2.f * lengthYd / kRatRunSpeed * 1000.f));
    }

    // HF13 Stock: Shoot 16100 every 2 s and Multi-Shot 14443 once, in the breaks only. Both are 5..30 yd spells, so a
    // target in melee reach is skipped for a ranged player.
    inline constexpr std::uint32_t kShootFirstMs = 500;
    inline constexpr std::uint32_t kShootEveryMs = 2000;
    inline constexpr std::uint32_t kMultiShotAtMs = 1500;
    inline constexpr float kShootMinYd = 8.f;
    inline constexpr float kShootMaxYd = 30.f;

    // The set list: who plays when. Times are ms since the pull. Advance(now) returns what happened since the last
    // call, in order (a song's start, a song's end), so a long frame never skips one.
    class SetList
    {
    public:
        struct Event
        {
            enum class Kind : std::uint8_t
            {
                SongStart,
                SongEnd,
            };

            Kind kind = Kind::SongStart;
            Song song = Song::Jig;
            std::uint32_t index = 0;        // 0 for the first song of the pull
            std::uint64_t at = 0;           // the moment it was due
        };

        void Reset(bool heroic)
        {
            _heroic = heroic;
            _active = false;
            _song = Song::Jig;
            _index = 0;
            _start = 0;
            _end = 0;
            _nextStart = kFirstSongMs;
            _nextSong = Song::Jig;
        }

        std::vector<Event> Advance(std::uint64_t now)
        {
            std::vector<Event> out;
            for (;;)
            {
                if (_active)
                {
                    if (now < _end)
                        break;
                    out.push_back({ Event::Kind::SongEnd, _song, _index, _end });
                    _active = false;
                    _nextStart = _end + kBreakMs(_heroic);
                    _nextSong = NextSong(_song);
                    ++_index;
                }
                else
                {
                    if (now < _nextStart)
                        break;
                    _active = true;
                    _song = _nextSong;
                    _start = _nextStart;
                    _end = _start + kSongMs(_heroic);
                    out.push_back({ Event::Kind::SongStart, _song, _index, _start });
                }
            }
            return out;
        }

        // A GM test: the song plays now, instead of waiting for its turn; the rotation goes on after it. False when
        // a song is playing.
        bool Force(Song song, std::uint64_t now)
        {
            if (_active)
                return false;
            _nextSong = song;
            _nextStart = now;
            return true;
        }

        bool Heroic() const { return _heroic; }
        bool InSong() const { return _active; }
        // Time between songs (the shooting breaks, and the 6 s before the first song).
        bool InBreak() const { return !_active; }
        Song Current() const { return _song; }
        std::uint32_t Index() const { return _index; }
        std::uint64_t StartMs() const { return _start; }
        std::uint64_t EndMs() const { return _end; }
        std::uint64_t NextStartMs() const { return _nextStart; }
        Song NextPlaying() const { return _nextSong; }

    private:
        bool _heroic = false;
        bool _active = false;
        Song _song = Song::Jig;
        std::uint32_t _index = 0;
        std::uint64_t _start = 0;
        std::uint64_t _end = 0;
        std::uint64_t _nextStart = kFirstSongMs;
        Song _nextSong = Song::Jig;
    };
}

#endif
