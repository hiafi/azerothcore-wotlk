/*
 * mod-dungeon-bosses, Scarlet Monastery D4:
 * Bloodmage Thalnos (4543), the pure, host-testable part (no engine headers). Build spec:
 * docs/dungeons/scarlet-monastery-1-graveyard.md "Bloodmage Thalnos" (TH1-TH6; TH7 / TH8 and the risen are the hard
 * mode's, WP-D4H, on the hooks of ThalnosFight.h), handoff section 3.5 row D4, 3.6 (48k normal, 300k heroic), 3.8
 * (the crypt: NAVMESH-REPORT "Thalnos"), 3.10 (VR). Tested by tests/sm_thalnos_test.cpp.
 *
 *   Spells         the WP's ids, inside kSpellsThalnos (212440-212479), declared in apps/dbc-tools
 *                  source/npcs/scarlet_monastery/thalnos.py
 *   Tuning         NH<> percents and cadences, straight from the build spec (percents of the reference row)
 *   Blood Ritual   TH1 the stack frame: +1 per player a plain spell hits, thresholds and costs of the empowered
 *                  versions, the normal cap (heroic uncapped)
 *   Blood Nova     TH5 / TH5e the interrupt state machine (the empowered nova's first kick strips the blood: a plain
 *                  2 s restart; a second kick stops it)
 *   Blood Brand    TH6 (heroic) the "at most one stack a second" gate
 *   Beats          first delay and cadence per mechanic (start to start), the BeatClock
 *   Ground         the crypt's floor (bots' bounds, Flame Spike's edge room, Blood Lance's wall) and the lawn the hard
 *                  mode moves the fight to (75%: kNoRestPct)
 */

#ifndef MOD_DUNGEON_BOSSES_SM_THALNOS_LOGIC_H
#define MOD_DUNGEON_BOSSES_SM_THALNOS_LOGIC_H

#include "DungeonKitMath.h"
#include "ScarletMonasteryRework.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace SmThalnos
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (ScarletMonasteryRework.h; ids.yaml reservation `scarlet_monastery`).
    inline constexpr ScarletMonasteryRework::IdSlice kSpellSlice = ScarletMonasteryRework::kSpellsThalnos;

    enum ThalnosSpells : std::uint32_t
    {
        SPELL_TH_BLOOD_RITUAL           = kSpellSlice.first + 0,    // 212440 TH1 his stack buff (the count)
        SPELL_TH_HANDS_RUN_RED          = kSpellSlice.first + 1,    // 212441 TH1 an empowered cast's look (on him)
        SPELL_TH_BLOOD_BOLT             = kSpellSlice.first + 2,    // 212442 TH2 the 2.5 s cast on the tank (kick)
        SPELL_TH_BLOOD_LANCE            = kSpellSlice.first + 3,    // 212443 TH2e the 2.5 s cast, the tank's hit (kick)
        SPELL_TH_BLOOD_LANCE_LINE       = kSpellSlice.first + 4,    // 212444 TH2e the line's hit (resolve copy)
        SPELL_TH_FLAME_SPIKE_CAST       = kSpellSlice.first + 5,    // 212445 TH3 the 2 s bar (no kick, Fire)
        SPELL_TH_FLAME_SPIKE            = kSpellSlice.first + 6,    // 212446 TH3 the carrier's debuff (the carry)
        SPELL_TH_FLAME_SPIKE_PILLAR     = kSpellSlice.first + 7,    // 212447 TH3 the pillar (resolve copy, Fire)
        SPELL_TH_FLAME_SPIKE_POOL       = kSpellSlice.first + 8,    // 212448 TH3 the pool's tick (resolve copy)
        SPELL_TH_FLAME_SPIKE_LOOK       = kSpellSlice.first + 9,    // 212449 TH3 the pool's look (a stalker's state)
        SPELL_TH_BOILING_BLOOD          = kSpellSlice.first + 10,   // 212450 TH4 the carrier's 5 s debuff
        SPELL_TH_BOILING_BLOOD_SPLASH   = kSpellSlice.first + 11,   // 212451 TH4 the eruption on others (resolve)
        SPELL_TH_BOILING_BLOOD_BURST    = kSpellSlice.first + 12,   // 212452 TH4 the eruption on the carrier
        SPELL_TH_BLOOD_NOVA_CAST        = kSpellSlice.first + 13,   // 212453 TH5 the 3 s bar (kick, Shadow)
        SPELL_TH_EMPOWERED_NOVA_CAST    = kSpellSlice.first + 14,   // 212454 TH5e the 3 s bar (kick, Shadow)
        SPELL_TH_BLOOD_NOVA_RESTART     = kSpellSlice.first + 15,   // 212455 TH5e the 2 s restart (kick, Physical)
        SPELL_TH_BLOOD_NOVA             = kSpellSlice.first + 16,   // 212456 TH5 the plain nova's hit on a player
        SPELL_TH_EMPOWERED_NOVA         = kSpellSlice.first + 17,   // 212457 TH5e the empowered nova's hit
        SPELL_TH_BLOOD_BRAND            = kSpellSlice.first + 18,   // 212458 TH6 (heroic) the Magic debuff
        SPELL_TH_FLAME_SPIKE_ERUPT      = kSpellSlice.first + 19,   // 212459 TH3 the pillar's look (a stalker's)
        // 212460-212479 spare
    };
    static_assert(SPELL_TH_FLAME_SPIKE_ERUPT <= kSpellSlice.last, "Thalnos's spells must stay in his slice");

    // Stock spells of 4543 retired from the kit (GY "Stock kit"): never cast by the rework. Flame Shock 8053 and Fire
    // Nova 12470 carry live spell_dbc player overrides (rule 15): his versions are copies in the slice.
    inline constexpr std::uint32_t SPELL_STOCK_SHADOW_BOLT = 9613;
    inline constexpr std::uint32_t SPELL_STOCK_FLAME_SPIKE = 8814;
    inline constexpr std::uint32_t SPELL_STOCK_FLAME_SHOCK = 8053;
    inline constexpr std::uint32_t SPELL_STOCK_FIRE_NOVA = 12470;

    // Registry tags (the build spec's mechanic numbers; the failure ledger, the drills and the playtest greps key on
    // them). TH1, TH2, TH5 and TH6 are not registry mechanics; TH7 / TH8 and RH1-RH6 are D4H's.
    enum ThalnosTags : std::uint32_t
    {
        TH2 = 2,    // Blood Lance's line (TH2e)
        TH3 = 3,    // Flame Spike: the carry, the pillar, the pool
        TH4 = 4,    // Boiling Blood (RunOut)
    };

    // creature_text groups 4543 (0-2 stock; 3 data/sql/updates/pending_db_world/rev_thalnos_scarlet_monastery.sql;
    // 4 is D4H's: the Desecration's right answer).
    enum ThalnosTexts : std::uint8_t
    {
        SAY_AGGRO           = 0,    // yell: "We hunger for vengeance." (stock)
        SAY_NO_REST         = 1,    // yell: "No rest... for the angry dead!" (stock, moved: his first empowered spell
                                    // on normal and heroic; the hard mode's 75% teleport, D4H)
        SAY_KILL            = 2,    // yell: "More... More souls!" (stock, a kill)
        EMOTE_HANDS_RUN_RED = 3,    // emote: "%s's hands run red with blood!" (TH1, each empowered cast)
        SAY_WAKE_THEM_ALL   = 4,    // yell: "Yes... wake them all!" (D4H: the Desecration answered)
    };
    // The stock kill line's lockout (SmartAI 4543 row 1: 5 s).
    inline constexpr std::uint32_t kKillYellGapMs = 5000;

    // ----------------------------------------------------------------------------------------------------------------
    // TH1 Blood Ritual: the stacks. Each player a plain spell hits gives one (once per player per cast; pool ticks
    // none; empowered spells none); an empowered version needs a number held and spends fewer
    // ----------------------------------------------------------------------------------------------------------------

    enum class Empowered : std::uint8_t
    {
        Lance,      // Blood Bolt -> Blood Lance
        Spike,      // Flame Spike -> three targets
        Boil,       // Boiling Blood -> two carriers
        Nova,       // Blood Nova -> the empowered nova
    };

    struct Cost
    {
        std::uint32_t needs;
        std::uint32_t spends;
    };

    // GY TH1 table (revised 2026-11-17: one shared cost let the cheap Lance eat every stack).
    constexpr Cost CostOf(Empowered e)
    {
        switch (e)
        {
            case Empowered::Lance: return { 3, 1 };
            case Empowered::Spike: return { 3, 2 };
            case Empowered::Boil:  return { 4, 2 };
            case Empowered::Nova:  return { 5, 3 };
        }
        return { 0, 0 };
    }
    static_assert(CostOf(Empowered::Lance).needs == 3 && CostOf(Empowered::Nova).spends == 3, "the build spec table");

    // Normal caps the stacks at 10 (a group failure, capped below 60); heroic has no cap (level 60). The aura's
    // StackAmount (255, the client's byte) is the only bound left there.
    inline constexpr std::uint32_t kNormalStackCap = 10;
    inline constexpr std::uint32_t kAuraStackLimit = 255;

    constexpr std::uint32_t StackCap(bool heroic)
    {
        return heroic ? kAuraStackLimit : kNormalStackCap;
    }

    class Ritual
    {
    public:
        void Reset(bool heroic)
        {
            _heroic = heroic;
            _stacks = 0;
            _gained = 0;
            _spent = 0;
        }

        std::uint32_t Stacks() const { return _stacks; }
        std::uint32_t Gained() const { return _gained; }
        std::uint32_t Spent() const { return _spent; }
        bool Heroic() const { return _heroic; }

        // `n` players hit by a plain spell (or anything the hard mode counts as his): the new count, at the cap.
        std::uint32_t Add(std::uint32_t n)
        {
            std::uint32_t const before = _stacks;
            _stacks = std::min(StackCap(_heroic), _stacks + n);
            _gained += _stacks - before;
            return _stacks;
        }

        // A spell comes up: does he hold its threshold?
        bool Holds(Empowered e) const { return _stacks >= CostOf(e).needs; }

        // He casts the empowered version: the cost leaves at the cast's start (a kicked empowered cast stays spent).
        std::uint32_t Spend(Empowered e)
        {
            std::uint32_t const cost = std::min(_stacks, CostOf(e).spends);
            _stacks -= cost;
            _spent += cost;
            return _stacks;
        }

        // GM / test: the count as given (at the cap).
        void Set(std::uint32_t n) { _stacks = std::min(StackCap(_heroic), n); }

    private:
        std::uint32_t _stacks = 0;
        std::uint32_t _gained = 0;
        std::uint32_t _spent = 0;
        bool _heroic = false;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // TH2 Blood Bolt / TH2e Blood Lance: 2.5 s casts on the tank (kickable: a kicked bolt deals nothing and gives no
    // stack). The Lance adds a 4 yd line from him through the tank to the wall: others in it take 35% / 45%, Weakened
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kBoltCastMs = 2500;
    inline constexpr NH<float> kBoltTankPct{ 20.f, 30.f };             // of the tank row (the spell's own value)
    inline constexpr NH<float> kLanceTankPct{ 30.f, 40.f };
    inline constexpr NH<float> kLanceLinePct{ 35.f, 45.f };            // others in the line, plus Weakened
    inline constexpr float kLanceWidth = 4.f;
    inline constexpr float kLanceMaxYd = 30.f;                         // the spec's 30 yd; the crypt's wall comes first
    inline constexpr float kLanceMinBehindYd = 2.f;                    // the line always reaches past the tank
    // The line resolves just after the bar ends, so a kick in the bar's last moment still cancels it.
    inline constexpr std::uint32_t kLanceResolveLagMs = 150;

    // ----------------------------------------------------------------------------------------------------------------
    // TH3 Flame Spike: a 2 s bar on a random player (the tank included) who carries a debuff; at the bar's end a 4 yd
    // marker lands where they stand; 1.5 s later the pillar (35% / 45% and Weakened), then a pool (5% / 8% a second for
    // 20 s / 30 s, no Weakened). Empowered: three targets
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kSpikeCastMs = 2000;
    inline constexpr std::uint32_t kSpikeMarkerMs = 1500;
    inline constexpr float kSpikeRadius = 4.f;
    inline constexpr NH<float> kSpikePillarPct{ 35.f, 45.f };
    inline constexpr NH<float> kSpikePoolPct{ 5.f, 8.f };              // a second
    inline constexpr NH<std::uint32_t> kSpikePoolMs{ 20000, 30000 };
    inline constexpr std::uint32_t kSpikePoolTickMs = 1000;
    inline constexpr std::uint32_t kSpikeTargetsPlain = 1;
    inline constexpr std::uint32_t kSpikeTargetsEmpowered = 3;
    // A carrier bot keeps its drop this far from a live pool's center (the pool's radius plus a step).
    inline constexpr float kSpikeAvoidPoolYd = kSpikeRadius + 1.5f;

    constexpr std::uint32_t SpikeTargets(bool empowered)
    {
        return empowered ? kSpikeTargetsEmpowered : kSpikeTargetsPlain;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TH4 Boiling Blood: a 5 s debuff on a random non-tank (the large-spread exemption), then it erupts: the carrier
    // 25% / 35%, everyone else within 8 / 10 yd 35% / 45% and Weakened. Empowered: two carriers (8 yd from each other)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kBoilMs = 5000;
    inline constexpr NH<float> kBoilRadius{ 8.f, 10.f };
    inline constexpr NH<float> kBoilCarrierPct{ 25.f, 35.f };
    inline constexpr NH<float> kBoilSplashPct{ 35.f, 45.f };

    constexpr std::uint32_t BoilCarriers(bool empowered)
    {
        return empowered ? 2 : 1;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TH5 Blood Nova: a 3 s cast that hits every player on his ground (the crypt; the lawn on hard mode). Kicked: no
    // hits, no stacks. TH5e (needs 5, spends 3): 3 s, a bigger hit; the first kick strips the blood and he restarts it
    // at once as a plain 2 s nova; a second kick stops it
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kNovaCastMs = 3000;
    inline constexpr std::uint32_t kNovaRestartCastMs = 2000;
    // Designer question 1 (the report): the heroic bullet "a missed plain nova is 30% (H)" against the build spec's
    // damage column and the Hits bullet (15% / 20%). Built: the column.
    inline constexpr NH<float> kNovaPct{ 15.f, 20.f };
    inline constexpr NH<float> kEmpoweredNovaPct{ 25.f, 35.f };

    enum class NovaStage : std::uint8_t
    {
        Idle,
        Plain,              // the plain 3 s bar
        Empowered,          // the empowered 3 s bar
        RestartPending,     // the empowered bar was kicked: the plain 2 s bar starts on the next tick
        Restart,            // the plain 2 s restart
    };

    // What a nova bar's end does.
    enum class NovaOutcome : std::uint8_t
    {
        None,               // not the bar of this stage (a stray or repeated callback): nothing
        PlainLands,         // a plain nova or the restart finished: the plain hit and its stacks
        EmpoweredLands,     // the empowered nova finished: the big hit, no stacks
        Restart,            // the empowered nova was kicked: start the plain restart
        Stopped,            // a plain nova or the restart was kicked: nothing at all
    };

    // The nova's state as the bars start and end. A second callback for a bar that already ended (the engine reports
    // a finished spell again when the next one replaces it) finds the stage moved on and does nothing.
    class NovaState
    {
    public:
        NovaStage Stage() const { return _stage; }
        bool Busy() const { return _stage != NovaStage::Idle; }

        void StartPlain() { _stage = NovaStage::Plain; }
        void StartEmpowered() { _stage = NovaStage::Empowered; }
        void StartRestart() { _stage = NovaStage::Restart; }
        void Clear() { _stage = NovaStage::Idle; }

        // The bar `which` (Plain, Empowered or Restart) finished casting.
        NovaOutcome Finished(NovaStage which)
        {
            if (which != _stage || which == NovaStage::Idle || which == NovaStage::RestartPending)
                return NovaOutcome::None;
            _stage = NovaStage::Idle;
            return which == NovaStage::Empowered ? NovaOutcome::EmpoweredLands : NovaOutcome::PlainLands;
        }

        // The bar `which` was kicked (or silenced).
        NovaOutcome Kicked(NovaStage which)
        {
            if (which != _stage || which == NovaStage::Idle || which == NovaStage::RestartPending)
                return NovaOutcome::None;
            if (which == NovaStage::Empowered)
            {
                _stage = NovaStage::RestartPending;
                return NovaOutcome::Restart;
            }
            _stage = NovaStage::Idle;
            return NovaOutcome::Stopped;
        }

        // The restart could not start (silenced, his own stop): the nova is over.
        void RestartFailed()
        {
            if (_stage == NovaStage::RestartPending)
                _stage = NovaStage::Idle;
        }

    private:
        NovaStage _stage = NovaStage::Idle;
    };

    // The stage a nova bar's spell id stands for (Idle: not a nova bar).
    constexpr NovaStage NovaStageOf(std::uint32_t spellId)
    {
        switch (spellId)
        {
            case SPELL_TH_BLOOD_NOVA_CAST:      return NovaStage::Plain;
            case SPELL_TH_EMPOWERED_NOVA_CAST:  return NovaStage::Empowered;
            case SPELL_TH_BLOOD_NOVA_RESTART:   return NovaStage::Restart;
            default:                            return NovaStage::Idle;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TH6 Blood Brand (heroic): a 12 s Magic debuff on a random player (the tank included); each time the carrier takes
    // damage (from any source) he gains a stack, at most one a second
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kBrandMs = 12000;
    inline constexpr std::uint32_t kBrandStackGapMs = 1000;

    // The gate on one carrier: a hit at `nowMs` counts when the last counted hit is at least the gap old.
    class BrandGate
    {
    public:
        bool Take(std::uint64_t nowMs)
        {
            if (_counted && nowMs < _lastMs + kBrandStackGapMs)
                return false;
            _counted = true;
            _lastMs = nowMs;
            return true;
        }

    private:
        std::uint64_t _lastMs = 0;
        bool _counted = false;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The beats (GY "Build spec" first / cooldown): start to start
    // ----------------------------------------------------------------------------------------------------------------

    struct Beat
    {
        std::uint32_t firstMs;
        NH<std::uint32_t> everyMs;
    };

    inline constexpr Beat kBoltBeat{ 2000, { 8000, 6000 } };           // TH2 (and the Lance in its place)
    inline constexpr Beat kSpikeBeat{ 6000, { 15000, 15000 } };        // TH3
    inline constexpr Beat kBoilBeat{ 10000, { 15000, 15000 } };        // TH4
    inline constexpr Beat kNovaBeat{ 15000, { 20000, 20000 } };        // TH5
    inline constexpr Beat kBrandBeat{ 12000, { 20000, 20000 } };       // TH6, heroic

    // A repeating beat on the AI's own ms clock; a beat that cannot fire yet (a cast, a hold) stays due.
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

    // ----------------------------------------------------------------------------------------------------------------
    // The ground: the crypt (NAVMESH-REPORT "Thalnos": z -9.3 to -8, 584 sq yd, x 1801-1819 by y 1400-1433, his nook
    // at the north edge; navmesh/maps.txt "Thalnos crypt") and the lawn the hard mode moves the fight to
    // ----------------------------------------------------------------------------------------------------------------

    enum class Ground : std::uint8_t
    {
        Crypt,
        Lawn,       // the hard mode, after the 75% teleport (D4H calls ThalnosFight::SetGround)
    };

    // The crypt floor read off the 1 yd map (half a yard inside the mesh edge), round the octagon and the nook he
    // stands in (x 1818.5-1824.5, y 1413.5-1418). The stair south (x 1787-1800, y 1413-1417) is left out.
    inline constexpr std::array<Vec2, 12> kCryptFloor{ {
        { 1800.5f, 1403.5f }, { 1800.5f, 1426.5f }, { 1803.5f, 1431.f }, { 1814.5f, 1432.5f },
        { 1818.5f, 1428.f }, { 1818.5f, 1418.f }, { 1824.5f, 1418.f }, { 1824.5f, 1413.5f },
        { 1818.5f, 1413.5f }, { 1818.5f, 1401.5f }, { 1815.f, 1398.5f }, { 1804.f, 1398.5f },
    } };
    inline constexpr float kCryptZMin = -12.f;
    inline constexpr float kCryptZMax = -4.f;

    // The lawn (the council's disc, section 7 #18 A; NM: the clear disc (1798.5, 1348.5) r 19.1, floor within 30 yd
    // 2,658 sq yd). The bots' bounds there: 30 yd round it; the arena 40 yd (the Desecration's lawn region), z 15-26.
    inline constexpr Vec2 kLawnCenter{ ScarletMonasteryRework::kCouncilLawn.x, ScarletMonasteryRework::kCouncilLawn.y };
    inline constexpr float kLawnBoundsYd = 30.f;
    inline constexpr float kLawnArenaYd = 40.f;
    inline constexpr float kLawnZMin = 15.f;
    inline constexpr float kLawnZMax = 26.f;
    // The lawn is cut at y 1317 on Ironspine's side (RF-1 m-4, his yard's north edge): the header's CouncilLawnRegion
    // is the frame, 31.5 yd short of his home; the 30 yd bounds stay inside it.
    inline constexpr float kLawnSouthCutY = ScarletMonasteryRework::kCouncilLawnSouthY;

    // On the lawn: inside the cut 40 yd disc and its z band (the hard mode's lawn players and the risen's leash).
    inline bool OnLawnFloor(Vec2 p, float z)
    {
        return ScarletMonasteryRework::CouncilLawnRegion().Contains(p, z);
    }

    // The mechanics registered with one ground's bots' bounds (R-1-GY MJ-1). A bot's target must lie inside the bounds
    // of EVERY live mechanic of the fight, so a crypt pool, pillar or boil still live after the 75% teleport would pin
    // every bot on the lawn for up to 30 s: the move to another ground cancels the old ground's ones (nobody is left
    // there to hurt; the pools' stalker looks stay behind). Handle is the registry handle (an int in the host tests).
    template <typename Handle>
    class GroundedHandles
    {
    public:
        void Add(Ground ground, Handle handle)
        {
            _entries.push_back({ ground, handle });
        }

        // Removes and returns every handle bound to a ground other than `to`.
        std::vector<Handle> Leave(Ground to)
        {
            std::vector<Handle> out;
            std::erase_if(_entries, [&](Entry const& e)
            {
                if (e.ground == to)
                    return false;
                out.push_back(e.handle);
                return true;
            });
            return out;
        }

        // Drops the handles `live(handle)` says are over (resolved or cancelled).
        template <typename Live>
        void Prune(Live&& live)
        {
            std::erase_if(_entries, [&](Entry const& e) { return !live(e.handle); });
        }

        void Clear() { _entries.clear(); }
        std::size_t Size() const { return _entries.size(); }

        std::size_t CountOn(Ground ground) const
        {
            return static_cast<std::size_t>(std::count_if(_entries.begin(), _entries.end(),
                [ground](Entry const& e) { return e.ground == ground; }));
        }

    private:
        struct Entry
        {
            Ground ground;
            Handle handle;
        };
        std::vector<Entry> _entries;
    };

    // The hard mode's transition point (GY TH7: "at 75%", designer 2026-11-17). D4 calls the hard mode's OnThreshold
    // once, the first tick his health is at or below the hard mode's ThresholdPct (default this).
    inline constexpr float kNoRestPct = 75.f;

    // The crypt's floor area (the shoelace sum; NM measured 584 sq yd on the mesh).
    constexpr float PolygonArea(std::array<Vec2, 12> const& poly)
    {
        float twice = 0.f;
        for (std::size_t i = 0, j = poly.size() - 1; i < poly.size(); j = i++)
            twice += poly[j].x * poly[i].y - poly[i].x * poly[j].y;
        return (twice < 0.f ? -twice : twice) * 0.5f;
    }

    inline bool OnCryptFloor(Vec2 p)
    {
        return DungeonKit::PointInPolygon(std::span<Vec2 const>(kCryptFloor), p);
    }

    // TH2e: the Lance's length from Thalnos at `boss` through the tank at `tank` to the wall: the crypt's floor edge
    // beyond the tank (the ray from the tank on, so the nook's walls behind him never cut it short), never past
    // kLanceMaxYd and always at least kLanceMinBehindYd past the tank. On the lawn: kLanceMaxYd.
    inline float LanceLength(Ground ground, Vec2 boss, Vec2 tank)
    {
        float const toTank = DungeonKit::Distance(boss, tank);
        if (ground != Ground::Crypt || toTank < 0.5f || !OnCryptFloor(tank))
            return kLanceMaxYd;     // the lawn, the tank on him, or the tank off the floor polygon: the spec's length
        float const minimum = std::min(kLanceMaxYd, toTank + kLanceMinBehindYd);
        std::optional<float> const beyond = DungeonKit::RayToPolygonEdge(kCryptFloor, tank,
            DungeonKit::BearingTo(boss, tank));
        if (!beyond)
            return kLanceMaxYd;
        return std::clamp(toTank + *beyond, minimum, kLanceMaxYd);
    }
}

#endif
