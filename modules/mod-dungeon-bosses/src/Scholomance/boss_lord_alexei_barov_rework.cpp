/*
 * mod-dungeon-bosses, Scholomance S9: Lord Alexei Barov (10504), "the Code of Conduct". Build spec SC 2460-2533
 * (docs/dungeons/scholomance-rework.md; design SC 2275-2459), handoff section 3.4 rows AB, 3.5 row S9, 3.7, 3.8.
 * Replaces stock SmartAI 10504 (Unholy Aura on reset, Immolate, Veil of Shadow, the death SetData: WP-S9's SQL rev
 * drops it; BossAI keeps the death's instance data as the boss state); bound by apps/dbc-tools
 * source/npcs/scholomance/lord_alexei_barov.py. Pure rules: AlexeiLogic.h.
 *
 *   AB1  Rule            first at 10 s, every 25 s: his yell names the rule, its icon (206290-206295) goes on everyone
 *                        in the vault, 3 s (heroic 4 s) to get ready, then a 6 s window. Random, never the same set
 *                        twice in a row; heroic: every rule after the first is an approved pair (AB8)
 *   AB2  No running      registry HoldStill, tolerance 1 yd, through the window
 *   AB3  Assembly        registry Stack Cluster(2), 6 yd, judged at the close (only with three or more players)
 *   AB4  Keep distance   registry Spread 8 yd, judged at the close (206298, no damage)
 *   AB5  Out of bounds   registry Zone on the third most of the group stands in (30 x 19.5 yd), every second of the
 *                        window (206297, no damage)
 *   AB6  Line up (H)     registry Stack on a 4 yd lane down the north side, judged at the close; cut short of a
 *                        forbidden third
 *   AB7  Desks (H)       registry Spot: each player's own 3 yd desk (8 yd apart, outside a forbidden third)
 *   AB9  Demerit, Rod    any break (one per player per announcement): a Demerit (206299, 5 stacks, the fight) and
 *                        the Dean's Rod at once (206300): N 20-60%, H 30-90% by Demerits held, + 1 Weakened; emote 7
 *   AB10 The fortune     1 (heroic 2) gold piles (300543 + the stock Gold Coins look) 8-12 yd from the group where
 *                        taking it breaks the rule, from the window's opening to its close: walked over, Ill-Gotten
 *                        Gains (206301, +40% damage and healing, 15 s) and the Demerit. A count-0 registry Soak, so the
 *                        bots see it and nobody claims it
 *   AB11 Veil of Shadow  206302 on the tank: 1.5 s cast, -50% healing taken 10 s, Curse; 5-12 s, then 15-25 s,
 *                        never during a rule; on the interrupt and dispel lists (rewards)
 *   AB12 Unholy Aura     stock 17467 on aggro, removed on the reset
 *   Arena                ScholomanceRework::LeashOptions on AlexeiArena() (no grips; the gate is the instance's)
 *   Detention            the Barov Family Vault's solo lesson (BarovVaultLesson, SoloLesson.h; S11 runs it)
 *   Examiner             npc_sc_examiner_alexei (S13 binds 300553 to it; registered once wave C binds, kWaveCBound):
 *                        the same rule book at heroic values, 80k, no boss state, no Veil or aura, no Passing Grade
 *
 * Every timer runs on the rule book's own clock, never on BossAI's scheduler (the Veil's cast bar pauses that one):
 * the rules, the windows and the fortunes keep running through the cast. Every firing logs one INFO line
 * "scholo alexei <mechanic> ..." (module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "AlexeiLogic.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureTextMgr.h"
#include "DungeonKit.h"
#include "GameObject.h"
#include "Map.h"
#include "MechanicWeakened.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "PassiveAI.h"
#include "Player.h"
#include "Random.h"
#include "ScholomanceKit.h"
#include "ScholomanceRework.h"
#include "ScholomanceTestCommand.h"
#include "ScriptedCreature.h"
#include "SoloLesson.h"
#include "SpellAuras.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;
using namespace ScholoAlexei;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kLogBoss = "alexei";
    char const* const kLogExaminer = "alexei-examiner";

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(static_cast<int64>(ms));
    }

    float Rand01()
    {
        return std::min(0.9999f, static_cast<float>(rand_norm()));
    }

    // The vault's floor under `p` (both tiers, never the pit), else nullopt. The search starts under the Hall of the
    // Damned's floor (z 85), so it never lands on the room above.
    std::optional<float> VaultFloorZ(WorldObject const* ref, Vec2 p)
    {
        float const z = ref->GetMapHeight(p.x, p.y, kFortuneFloorMaxZ + 2.f);
        if (z <= INVALID_HEIGHT + 1.f || z < kFortuneFloorMinZ || z > kFortuneFloorMaxZ)
            return std::nullopt;
        return z;
    }

    // The floor z for an anchor: the measured floor, else the tier (the gate tier, z 75, runs to about y -60).
    float FloorOr(WorldObject const* ref, Vec2 p)
    {
        if (std::optional<float> z = VaultFloorZ(ref, p))
            return *z;
        return p.y > -60.f ? 75.f : kVaultFloorZ;
    }

    // The players of the fight: alive, not game masters, inside the vault's arena.
    std::vector<Player*> VaultPlayers(Creature* owner)
    {
        std::vector<Player*> out;
        Arena const arena = AlexeiArena();
        for (auto const& ref : owner->GetMap()->GetPlayers())
        {
            Player* p = ref.GetSource();
            if (!p || !p->IsAlive() || p->IsGameMaster())
                continue;
            if (arena.Contains(DungeonKit::PlaneOf(p), p->GetPositionZ()))
                out.push_back(p);
        }
        return out;
    }

    // A creature_text line, when the speaker has it (the examiner 300553 has none until S13 copies them).
    void SayIfAny(Creature* owner, uint8 group, WorldObject const* target = nullptr)
    {
        if (owner->IsAIEnabled && sCreatureTextMgr->TextExist(owner->GetEntry(), group))
            owner->AI()->Talk(group, target);
    }

    // One Weakened stack (ruling 21). `record`: on `owner`'s registry encounter, so the encounter's end takes it off
    // again like a registry hit's.
    void AddWeakened(Creature* owner, Player* player, bool record)
    {
        BossMechanics::Weakened::AddStack(player);
        if (record)
            BossMechanics::Registry::GetOrCreate(owner->GetMap()).BeginEncounter(owner->GetGUID())
                .weakenedPlayers.insert(player->GetGUID());
    }

    // The Dean's Rod (206300) from `caster` on `player`: `pct` of the reference row (the tank's on a tank) as the
    // spell's base point, so the target's own reductions apply (the spell ignores caster modifiers).
    uint32 Rod(Creature* caster, Player* player, float pct)
    {
        uint32 const damage = DungeonKit::RefFlatOn(caster, player, pct);
        caster->CastCustomSpell(SPELL_AX_DEANS_ROD, SPELLVALUE_BASE_POINT0, static_cast<int32>(damage), player, true);
        return damage;
    }

    // A fortune on the floor: the 300543 unit, the stock Gold Coins look (not selectable) and the bots' count-0 Soak.
    struct Fortune
    {
        Position at;
        ObjectGuid unit;
        ObjectGuid look;
        MechanicHandle soak;
        bool live = false;
    };

    Fortune SpawnFortune(Creature* owner, Vec2 p, uint32 lifeMs)
    {
        Fortune f;
        f.at = Position(p.x, p.y, FloorOr(owner, p), Rand01() * 6.2831853f);
        if (TempSummon* unit = owner->SummonCreature(NPC_SC_BAROV_FORTUNE, f.at, TEMPSUMMON_TIMED_DESPAWN,
                lifeMs + 1000))
        {
            unit->SetReactState(REACT_PASSIVE);
            f.unit = unit->GetGUID();
            if (GameObject* go = unit->SummonGameObject(GO_GOLD_COINS, f.at.GetPositionX(), f.at.GetPositionY(),
                    f.at.GetPositionZ(), f.at.GetOrientation(), 0.f, 0.f, 0.f, 0.f, lifeMs / 1000 + 2))
            {
                go->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
                f.look = go->GetGUID();
            }
        }
        MechanicRef ref = Mechanic::Soak(owner, f.at, kFortunePickupYd, 0, Ms(lifeMs + 2000));
        ref.NoFillTimer().Tag(TAG_FORTUNE);
        f.soak = ref.Handle();
        f.live = true;
        return f;
    }

    // `map`: where the pile lies when the owner is gone (the lesson's end after its stalker left); the registry soak
    // then simply runs out.
    void RemoveFortune(Creature* owner, Fortune& f, Map* map = nullptr)
    {
        if (!f.live)
            return;
        f.live = false;
        if (owner)
        {
            Mechanic::Cancel(owner, f.soak);
            map = owner->GetMap();
        }
        if (!map)
            return;
        if (GameObject* go = map->GetGameObject(f.look))
            go->Delete();
        if (Creature* unit = map->GetCreature(f.unit))
            unit->DespawnOrUnsummon();
    }

    // The first eligible player within reach of a live fortune (2 yd, the z band), else nullptr.
    Player* FortuneTaker(Map* map, Fortune const& f, std::function<bool(Player*)> const& eligible)
    {
        for (auto const& ref : map->GetPlayers())
        {
            Player* p = ref.GetSource();
            if (!p || !p->IsAlive() || p->IsGameMaster() || !eligible(p))
                continue;
            if (p->GetExactDist2d(f.at.GetPositionX(), f.at.GetPositionY()) <= kFortunePickupYd
                && std::fabs(p->GetPositionZ() - f.at.GetPositionZ()) <= kFortuneZBand)
                return p;
        }
        return nullptr;
    }

    // A strip on the floor, anchored at the floor height of its middle on the north side (the two tiers differ by
    // 3 yd; the zone's z tolerance holds both and the pit).
    BossMechanics::ZoneSpec StripSpec(WorldObject const* ref, Strip const& s)
    {
        float const z = FloorOr(ref, { kLaneCenterX, s.from.y - 0.5f * s.length });
        return BossMechanics::Shapes::LineFacing(Position(s.from.x, s.from.y, z, s.facing), s.facing, s.length,
            s.width);
    }

    std::string SetName(RuleSet set)
    {
        std::string out;
        for (std::size_t i = 0; i < kRuleCount; ++i)
            if (Has(set, kRules[i]))
                out += (out.empty() ? "" : "+") + std::string(kRuleKeys[i]);
        return out.empty() ? "none" : out;
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// The Code of Conduct and the Bargain for one fight: Alexei's, or his Graduate Examiner's
// ---------------------------------------------------------------------------------------------------------------------
class BarovRuleBook
{
public:
    struct Options
    {
        bool heroic = false;
        uint32 firstMs = kRuleFirstMs;
        uint32 everyMs = kRuleEveryMs;
    };

    void Begin(Creature* owner, Options const& options)
    {
        Clear(owner);
        _options = options;
        _active = true;
        _nextAnnounceMs = options.firstMs;
    }

    bool Active() const { return _active; }
    bool Heroic() const { return _options.heroic; }
    uint64 NowMs() const { return _clockMs; }
    uint64 NextAnnounceMs() const { return _nextAnnounceMs; }
    bool RuleRunning() const { return _set != RULE_NONE && _times.PhaseAt(_clockMs) != RulePhase::Idle; }

    // Every AI tick in combat, before the cast check (the own clock: a cast bar never pauses it).
    void Update(Creature* owner, uint32 diff)
    {
        if (!_active)
            return;
        _clockMs += diff;
        if (_set != RULE_NONE)
        {
            if (!_opened && _clockMs >= _times.OpenMs())
                OpenWindow(owner);
            if (_opened && !_closed)
            {
                _pollMs += diff;
                if (_pollMs >= kFortunePollMs)
                {
                    _pollMs = 0;
                    PollFortunes(owner);
                }
                if (_clockMs >= _times.CloseMs())
                    Close(owner);
            }
        }
        if (_clockMs >= _nextAnnounceMs && !RuleRunning())
        {
            std::vector<Player*> const players = VaultPlayers(owner);
            RuleSet const set = PickRuleSet(RulePool(_options.heroic, _announced, uint32(players.size()), _previous),
                Rand01());
            if (set != RULE_NONE)
                Announce(owner, set);
            else
                _nextAnnounceMs = _clockMs + 1000;
        }
    }

    // The fight ends (death, evade, reset): rules and fortunes gone, every player's Demerits and rule icons off.
    void Clear(Creature* owner)
    {
        if (owner)
        {
            CloseFortunes(owner);
            for (MechanicHandle const& h : _live)
                Mechanic::Cancel(owner, h);
            for (auto const& ref : owner->GetMap()->GetPlayers())
                if (Player* p = ref.GetSource())
                {
                    RemoveRuleIcons(p);
                    p->RemoveAurasDueToSpell(SPELL_AX_DEMERIT);
                }
        }
        _live.clear();
        _ruleMechanics.clear();
        _demerited.clear();
        _takers.clear();
        _fortunes.clear();
        _set = RULE_NONE;
        _previous = RULE_NONE;
        _announced = 0;
        _clockMs = 0;
        _nextAnnounceMs = 0;
        _opened = false;
        _closed = false;
        _active = false;
        _forbidden.reset();
        _lane.reset();
        _desks.clear();
    }

    // AB1: announce `set` now (the timer, or `.dbtest`). Registers the rule's mechanics; the fortunes come with the
    // window.
    void Announce(Creature* owner, RuleSet set)
    {
        if (_set != RULE_NONE && !_closed)
        {
            // A `.dbtest` rule over a running one: the old rule's mechanics go too (they could no longer punish).
            Close(owner);
            for (MechanicHandle const& h : _live)
                if (_ruleMechanics.count(h.id))
                    Mechanic::Cancel(owner, h);
        }
        ++_serial;
        ++_announced;
        _previous = set;
        _set = set;
        _times = RuleTimes{ _clockMs, kRuleWarnMs(_options.heroic), kRuleWindowMs };
        _nextAnnounceMs = _clockMs + _options.everyMs;
        _opened = false;
        _closed = false;
        _pollMs = 0;
        _demerited.clear();
        _takers.clear();
        _ruleMechanics.clear();
        _forbidden.reset();
        _lane.reset();
        _desks.clear();

        std::vector<Player*> const players = VaultPlayers(owner);
        std::vector<Vec2> spots;
        float sumY = 0.f;
        // Only the players in the vault are judged (they get the icon; in an instance the registry would otherwise
        // judge every living player on the map, a revived runner at the entrance included).
        BossMechanics::Eligibility vault;
        for (Player* p : players)
        {
            spots.push_back(DungeonKit::PlaneOf(p));
            sumY += p->GetPositionY();
            vault.carriers.insert(p->GetGUID());
        }
        float const groupY = players.empty() ? owner->GetPositionY() : sumY / float(players.size());

        uint32 const warn = _times.warnMs;
        uint32 const atClose = warn + _times.windowMs;
        owner->CastSpell(owner, SPELL_AX_ANNOUNCE, true);
        // Nobody in the vault (a `.dbtest` from outside): the yell, no rule mechanic (empty carriers mean everyone).
        bool const judged = !vault.carriers.empty();
        // Out of bounds first: Line up and the desks are placed around its third.
        if (judged && Has(set, RULE_OUT_OF_BOUNDS))
        {
            _forbidden = PickForbiddenThird(spots, Rand01());
            MechanicRef ref = Mechanic::Zone(owner, StripSpec(owner, ThirdZone(*_forbidden)), Ms(warn));
            ref.Persistent(Ms(_times.windowMs), Ms(kOutOfBoundsTickMs)).ZTolerance(kVaultZTolerance).Eligible(vault)
                .Spell(SPELL_AX_OUT_OF_BOUNDS).OnHit([](Unit*) { }).Tag(TAG_OUT_OF_BOUNDS);
            Keep(ref.Handle());
        }
        if (judged && Has(set, RULE_NO_RUNNING))
        {
            MechanicRef ref = Mechanic::HoldStill(owner, vault.carriers, Ms(_times.windowMs), Ms(warn));
            ref.Tolerance(kNoRunningToleranceYd).Tag(TAG_NO_RUNNING);
            Keep(ref.Handle());
        }
        if (judged && Has(set, RULE_ASSEMBLY))
        {
            MechanicRef ref = Mechanic::Stack(owner, owner, kAssemblyRadius, Ms(atClose));
            ref.Cluster(kAssemblyMinOthers).Eligible(vault).Tag(TAG_ASSEMBLY);
            Keep(ref.Handle());
        }
        if (judged && Has(set, RULE_KEEP_DISTANCE))
        {
            MechanicRef ref = Mechanic::Spread(owner, kKeepDistanceRadius, Ms(atClose));
            ref.Eligible(vault).Spell(SPELL_AX_KEEP_DISTANCE).OnHit([](Unit*) { }).Tag(TAG_KEEP_DISTANCE);
            Keep(ref.Handle());
        }
        if (judged && Has(set, RULE_LINE_UP))
        {
            _lane = LaneFor(_forbidden, groupY);
            MechanicRef ref = Mechanic::Stack(owner, StripSpec(owner, LaneStrip(*_lane)), Ms(atClose));
            ref.ZTolerance(kVaultZTolerance).Eligible(vault).Tag(TAG_LINE_UP);
            Keep(ref.Handle());
        }
        if (judged && Has(set, RULE_DESKS))
        {
            std::vector<Vec2> const candidates = DeskCandidates(_forbidden, players.size());
            std::vector<std::size_t> const picks = AssignDesks(spots, candidates);
            std::unordered_map<ObjectGuid, Position> desks;
            for (std::size_t i = 0; i < players.size(); ++i)
            {
                if (picks[i] == kNoDesk)
                    continue;
                Vec2 const d = candidates[picks[i]];
                desks[players[i]->GetGUID()] = Position(d.x, d.y, FloorOr(owner, d), 0.f);
                _desks.push_back(d);
            }
            if (!desks.empty())
            {
                MechanicRef ref = Mechanic::Spot(owner, desks, Ms(atClose), kDeskRadius);
                ref.Tag(TAG_DESKS);
                Keep(ref.Handle());
            }
        }

        // The yells (a pair: both) and the icons on everyone in the vault until the close.
        for (RuleBit r : kRules)
        {
            if (!Has(set, r))
                continue;
            SayIfAny(owner, RuleYell(r));
            for (Player* p : players)
                if (Aura* aura = owner->AddAura(RuleAura(r), p))
                {
                    aura->SetMaxDuration(static_cast<int32>(atClose));
                    aura->SetDuration(static_cast<int32>(atClose));
                }
        }

        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "rule",
            Acore::StringFormat("set={} heroic={} n={} players={} third={} lane={} desks={} warn={} window={}",
                SetName(set), _options.heroic ? 1 : 0, _announced, players.size(),
                _forbidden ? int(*_forbidden) : -1,
                _lane ? Acore::StringFormat("{:.1f}..{:.1f}", _lane->yMin, _lane->yMax) : std::string("-"),
                _desks.size(), warn, _times.windowMs));
    }

    // A registry failure of this owner's encounter (GradeWatch's chain, or the examiner's own OnFailure). Only the
    // current announcement's rule mechanics punish (R-A B-1: the failure must mean a broken rule, nothing else).
    void HandleFailure(Creature* owner, BossMechanics::FailureEvent const& ev)
    {
        if (ev.player.IsEmpty() || !_ruleMechanics.count(ev.mechanicId))
            return;
        if (Player* player = ObjectAccessor::GetPlayer(owner->GetMap(), ev.player))
            Punish(owner, player, BossMechanics::FailureTypeName(ev.type), ev.tag);
    }

    // AB9: a Demerit and the Dean's Rod, once per player per announcement (`.dbtest` forces another).
    void Punish(Creature* owner, Player* player, char const* why, uint32 tag, bool force = false)
    {
        if (!player || !player->IsAlive())
            return;
        if (!_demerited.insert(player->GetGUID()).second && !force)
            return;
        uint32 const held = DungeonKit::Stacks(player, SPELL_AX_DEMERIT);
        float const pct = RodPct(_options.heroic, held);
        uint32 const now = DungeonKit::AddStacks(player, SPELL_AX_DEMERIT, 1, owner, kDemeritCap);
        uint32 const damage = Rod(owner, player, pct);
        AddWeakened(owner, player, true);
        SayIfAny(owner, EMOTE_ALEXEI_DEMERIT, player);
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "demerit",
            Acore::StringFormat("player={} why={} tag={} held={} now={} rod={:.1f}% damage={} set={}",
                player->GetName(), why, tag, held, now, pct, damage, SetName(_set)));
    }

    std::string State() const
    {
        std::size_t const live = std::count_if(_fortunes.begin(), _fortunes.end(),
            [](Fortune const& f) { return f.live; });
        return Acore::StringFormat("active={} heroic={} clock={}s announced={} set={} phase={} next={}s third={} "
            "fortunes={} demerited={} serial={}", _active ? 1 : 0, _options.heroic ? 1 : 0, _clockMs / 1000,
            _announced, SetName(_set), int(_times.PhaseAt(_clockMs)), _nextAnnounceMs / 1000,
            _forbidden ? int(*_forbidden) : -1, live, _demerited.size(), _serial);
    }

private:
    void Keep(MechanicHandle h)
    {
        if (!h)
            return;
        _live.push_back(h);
        _ruleMechanics.insert(h.id);
    }

    static void RemoveRuleIcons(Player* p)
    {
        for (RuleBit r : kRules)
            p->RemoveAurasDueToSpell(RuleAura(r));
    }

    // AB10: the window opens and the fortunes go down.
    void OpenWindow(Creature* owner)
    {
        _opened = true;
        FortuneRules rules;
        rules.set = _set;
        for (Player* p : VaultPlayers(owner))
            rules.players.push_back(DungeonKit::PlaneOf(p));
        rules.forbidden = _forbidden;
        rules.lane = _lane;
        rules.desks = _desks;
        uint32 const count = kFortunesPerRule(_options.heroic);
        std::vector<Vec2> const spots = PickFortuneSpots(rules, count, Rand01, [owner](Vec2 p)
        {
            return VaultFloorZ(owner, p).has_value();
        });
        for (Vec2 const& p : spots)
            _fortunes.push_back(SpawnFortune(owner, p, _times.windowMs));
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "fortune",
            Acore::StringFormat("set={} placed={} of {}", SetName(_set), spots.size(), count));
    }

    void PollFortunes(Creature* owner)
    {
        Map* map = owner->GetMap();
        for (Fortune& f : _fortunes)
        {
            if (!f.live)
                continue;
            Player* taker = FortuneTaker(map, f, [this](Player* p) { return !_takers.count(p->GetGUID()); });
            if (!taker)
                continue;
            _takers.insert(taker->GetGUID());
            RemoveFortune(owner, f);
            taker->CastSpell(taker, SPELL_AX_ILL_GOTTEN_GAINS, true);
            DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "fortune-taken",
                Acore::StringFormat("player={} set={}", taker->GetName(), SetName(_set)));
            // The dean catches the thief (round 3): the Demerit, whatever the rule.
            Punish(owner, taker, "fortune", TAG_FORTUNE);
        }
    }

    void CloseFortunes(Creature* owner)
    {
        for (Fortune& f : _fortunes)
            RemoveFortune(owner, f);
        _fortunes.clear();
    }

    // The window closes: the icons come off and the fortunes go; the at-close rules resolve on their own (registry).
    void Close(Creature* owner)
    {
        _closed = true;
        CloseFortunes(owner);
        for (auto const& ref : owner->GetMap()->GetPlayers())
            if (Player* p = ref.GetSource())
                RemoveRuleIcons(p);
    }

    Options _options;
    bool _active = false;
    uint64 _clockMs = 0;
    uint64 _nextAnnounceMs = 0;
    uint32 _announced = 0;
    uint32 _serial = 0;
    uint32 _pollMs = 0;
    RuleSet _set = RULE_NONE;
    RuleSet _previous = RULE_NONE;
    RuleTimes _times;
    bool _opened = false;
    bool _closed = false;
    std::optional<std::size_t> _forbidden;
    std::optional<LaneSpan> _lane;
    std::vector<Vec2> _desks;
    std::vector<Fortune> _fortunes;
    std::vector<MechanicHandle> _live;
    std::unordered_set<uint32> _ruleMechanics;     // this announcement's rule mechanics (the only ones that punish)
    GuidSet _demerited;                            // punished this announcement
    GuidSet _takers;                               // took a fortune this announcement
};

// The AI side the registry callbacks find again by guid (no Unit* in a stored lambda).
struct BarovRulesHost
{
    virtual ~BarovRulesHost() = default;
    virtual BarovRuleBook& Rules() = 0;
};

namespace
{
    std::function<void(BossMechanics::FailureEvent const&)> RuleFailureHandler(Creature* owner)
    {
        Map* map = owner->GetMap();
        ObjectGuid const guid = owner->GetGUID();
        return [map, guid](BossMechanics::FailureEvent const& ev)
        {
            Creature* c = map ? map->GetCreature(guid) : nullptr;
            if (!c || !c->IsAlive() || !c->IsAIEnabled)
                return;
            if (auto* host = dynamic_cast<BarovRulesHost*>(c->AI()))
                host->Rules().HandleFailure(c, ev);
        };
    }
}

// Lord Alexei Barov 10504 (his Graduate Examiner is npc_sc_examiner_alexei below).
struct boss_lord_alexei_barov_rework : public BossAI, public BarovRulesHost
{
    explicit boss_lord_alexei_barov_rework(Creature* creature)
        : BossAI(creature, BOSS_ALEXEI), _arena(AlexeiArena(), LeashOptions(kLogBoss)) { }

    BarovRuleBook& Rules() override { return _rules; }

    void Reset() override
    {
        _Reset();
        Cleanup();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        Cleanup();      // a `.dbtest` rule out of combat may have left something behind
        bool const heroic = IsHeroicMap(me);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_ALEXEI;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _grades.Begin(me, Instructor::Alexei, RuleFailureHandler(me));    // the Rod rides the grades' handler
        _arena.Engage(me);

        BarovRuleBook::Options rules;
        rules.heroic = heroic;
        rules.firstMs = kRuleFirstMs;
        rules.everyMs = kRuleEveryMs;
        _rules.Begin(me, rules);

        Talk(YELL_ALEXEI_AGGRO);
        me->CastSpell(me, SPELL_UNHOLY_AURA, true);     // AB12: on aggro, not on reset
        _nextVeilMs = urand(kVeilFirstMinMs, kVeilFirstMaxMs);
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "engage",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f}) health={}", heroic ? 1 : 0,
                me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), me->GetMaxHealth()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        _grades.Reset();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        _grades.AwardAtDeath(me);
        Talk(YELL_ALEXEI_DEATH);
        BossAI::JustDied(killer);   // DONE (the gate opens, Gandling's count), the summons despawn
        Cleanup();
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "death",
            Acore::StringFormat("killer={}", killer ? killer->GetName() : "none"));
    }

    // The fortunes are props: never zoned into combat (BossAI::JustSummoned would).
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;

        // The rule book's own clock: nothing below waits for the Veil's cast bar.
        _rules.Update(me, diff);

        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;

        UpdateVeil();
        DoMeleeAttackIfReady();
    }

    // AB11: the tank only; never during a rule (the cast clear of the next announcement).
    void UpdateVeil()
    {
        uint64 const now = _rules.NowMs();
        if (!_nextVeilMs || now < _nextVeilMs)
            return;
        if (!VeilMayStart(now, _rules.RuleRunning(), _rules.NextAnnounceMs()))
        {
            _nextVeilMs = now + kVeilAfterCloseMs;
            return;
        }
        Unit* victim = me->GetVictim();
        if (!victim)
            return;
        me->CastSpell(victim, SPELL_AX_VEIL_OF_SHADOW, false);
        uint32 const next = urand(kVeilEveryMinMs, kVeilEveryMaxMs);
        _nextVeilMs = now + next;
        Mechanic::NoteNextCastIn(me, SPELL_AX_VEIL_OF_SHADOW, Ms(next));
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "veil", victim->GetName());
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (SC): target priority none; interrupt and dispel Veil of Shadow (rewards); the fortunes are props
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        using BossMechanics::Who;
        BossMechanics::Descriptor d;
        d.interrupts.emplace_back(NPC_ALEXEI, SPELL_AX_VEIL_OF_SHADOW, 1, Ms(kVeilEveryMinMs));
        d.dispels.emplace_back(SPELL_AX_VEIL_OF_SHADOW, 1);
        d.targets.emplace_back(me->GetEntry(), 1, Who::Any);
        d.ignores.emplace_back(NPC_SC_BAROV_FORTUNE);
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest scholo alexei` entry points
    // ----------------------------------------------------------------------------------------------------------------

    std::string TestRule(RuleSet set)
    {
        if (!me->IsEngaged() || !_rules.Active())
            return "Alexei must be in combat (the rule book runs only in the fight).";
        if (!IsAllowedSet(set, _rules.Heroic()))
            DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "rule-test",
                Acore::StringFormat("set={} is not an approved set for this difficulty (fired anyway)", SetName(set)));
        _rules.Announce(me, set);
        return {};
    }

    std::string TestVeil()
    {
        Unit* victim = me->GetVictim();
        if (!me->IsEngaged() || !victim)
            return "Alexei must be in combat with a victim.";
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return "Alexei is casting; try again in a moment.";
        me->CastSpell(victim, SPELL_AX_VEIL_OF_SHADOW, false);
        return {};
    }

    std::string TestDemerit(Player* player)
    {
        if (!player)
            return "Select a player.";
        if (!_rules.Active())
            return "Alexei must be in combat.";
        _rules.Punish(me, player, "test", 0, true);
        return {};
    }

    std::string TestState() const
    {
        return Acore::StringFormat("veilAt={}s {}", _nextVeilMs / 1000, _rules.State());
    }

private:
    void Cleanup()
    {
        _rules.Clear(me);
        _arena.Reset();
        _nextVeilMs = 0;
        me->RemoveAurasDueToSpell(SPELL_UNHOLY_AURA);
    }

    DungeonKit::ArenaGuard _arena;
    GradeWatch _grades;
    BarovRuleBook _rules;
    uint64 _nextVeilMs = 0;
};

// The Graduate Examiner, Alexei (300553, S13's gauntlet; ScriptName kExaminerScriptName, registered once wave C binds):
// the Code of Conduct and the Bargain at heroic values on any map, 80k. No boss state, no Veil, no Unholy Aura, no
// Passing Grade, no lines unless S13 copies them; its own registry encounter, ended at its evade and death.
struct npc_sc_examiner_alexei : public ScriptedAI, public BarovRulesHost
{
    explicit npc_sc_examiner_alexei(Creature* creature)
        : ScriptedAI(creature), _arena(AlexeiArena(), LeashOptions(kLogExaminer)) { }

    BarovRuleBook& Rules() override { return _rules; }

    void Reset() override
    {
        _rules.Clear(me);
        _arena.Reset();
        me->SetMaxHealth(kExaminerHealth);
        me->SetHealth(kExaminerHealth);
    }

    void JustEngagedWith(Unit* /*who*/) override
    {
        _rules.Clear(me);
        Mechanic::BeginEncounter(me);
        BossMechanics::Descriptor d;
        d.targets.emplace_back(me->GetEntry(), 1, BossMechanics::Who::Any);
        d.ignores.emplace_back(NPC_SC_BAROV_FORTUNE);
        Mechanic::Describe(me, std::move(d));
        Mechanic::OnFailure(me, RuleFailureHandler(me));
        _arena.Engage(me);

        BarovRuleBook::Options rules;
        rules.heroic = kExaminerHeroic;
        rules.firstMs = kExaminerFirstRuleMs;
        rules.everyMs = kExaminerRuleEveryMs;
        _rules.Begin(me, rules);
        DungeonKit::LogMechanic(kLogDungeon, kLogExaminer, "engage",
            Acore::StringFormat("at=({:.1f}, {:.1f}, {:.1f}) health={}", me->GetPositionX(), me->GetPositionY(),
                me->GetPositionZ(), me->GetMaxHealth()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        _rules.Clear(me);
        _arena.Reset();
        Mechanic::EndEncounter(me);
        ScriptedAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        _rules.Clear(me);
        _arena.Reset();
        Mechanic::EndEncounter(me);
        DungeonKit::LogMechanic(kLogDungeon, kLogExaminer, "death",
            Acore::StringFormat("killer={}", killer ? killer->GetName() : "none"));
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;
        _rules.Update(me, diff);
        if (!_arena.Update(me, diff))
            return;
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

private:
    DungeonKit::ArenaGuard _arena;
    BarovRuleBook _rules;
};

// ---------------------------------------------------------------------------------------------------------------------
// The Barov Family Vault's solo lesson (Gandling's detention; SC 2960-2971, handoff section 3.7)
// ---------------------------------------------------------------------------------------------------------------------
class BarovVaultLesson : public TimedSoloLesson
{
public:
    BarovVaultLesson() : TimedSoloLesson(Classroom::BarovVault) { }

protected:
    void OnStart(Creature* owner, Player* /*student*/, bool /*heroic*/) override
    {
        _map = owner->GetMap();
        _ms = 0;
        for (Step& s : _steps)
            s = Step();
    }

    void OnUpdate(uint32 diff, Creature* owner, Player* student) override
    {
        if (!owner || !student)
            return;
        _ms += diff;
        for (std::size_t i = 0; i < kLessonRules.size(); ++i)
        {
            LessonRule const& rule = kLessonRules[i];
            Step& step = _steps[i];
            if (!step.announced && _ms >= rule.times.announceMs)
                Announce(owner, student, i);
            if (step.announced && !step.opened && _ms >= rule.times.OpenMs())
                Open(owner, student, i);
            if (step.opened && !step.closed)
            {
                if (step.fortune.live && FortuneTaker(owner->GetMap(), step.fortune,
                        [student](Player* p) { return p == student; }))
                {
                    RemoveFortune(owner, step.fortune);
                    student->CastSpell(student, SPELL_AX_ILL_GOTTEN_GAINS, true);
                    FailStudent();      // a script failure: "fortune left" is part of the pass
                    Punish(owner, student, i, "fortune");
                }
                if (_ms >= rule.times.CloseMs())
                {
                    step.closed = true;
                    RemoveFortune(owner, step.fortune);
                    student->RemoveAurasDueToSpell(RuleAura(rule.rule));
                }
            }
            // The rule's own registry failures: the student's ledger under the owner, by the rule's tag (the base
            // counts them for the verdict; this lands the hit once).
            if (step.announced && !step.punished)
                if (BossMechanics::PlayerLedger const* ledger = Mechanic::Failures(owner, student->GetGUID()))
                {
                    auto it = ledger->byTag.find(RuleTag(rule.rule));
                    if (it != ledger->byTag.end() && it->second > 0)
                        Punish(owner, student, i, "broke the rule");
                }
        }
    }

    void OnEnd(LessonEnd /*why*/, Creature* owner) override
    {
        Player* student = Student();
        for (std::size_t i = 0; i < kLessonRules.size(); ++i)
        {
            RemoveFortune(owner, _steps[i].fortune, _map);     // the owner may be gone: the pile goes anyway
            if (student)
                student->RemoveAurasDueToSpell(RuleAura(kLessonRules[i].rule));
        }
    }

private:
    struct Step
    {
        bool announced = false;
        bool opened = false;
        bool closed = false;
        bool punished = false;
        std::optional<std::size_t> third;
        Fortune fortune;
    };

    void Announce(Creature* owner, Player* student, std::size_t i)
    {
        LessonRule const& rule = kLessonRules[i];
        Step& step = _steps[i];
        step.announced = true;
        uint32 const warn = rule.times.warnMs;
        uint32 const window = rule.times.windowMs;
        owner->Whisper(Acore::StringFormat("The vault echoes: \"{}\"", RuleWords(rule.rule)), LANG_UNIVERSAL, student,
            true);
        if (Aura* aura = owner->AddAura(RuleAura(rule.rule), student))
        {
            aura->SetMaxDuration(static_cast<int32>(warn + window));
            aura->SetDuration(static_cast<int32>(warn + window));
        }
        if (rule.rule == RULE_OUT_OF_BOUNDS)
        {
            Vec2 const at = DungeonKit::PlaneOf(student);
            std::size_t const third = ThirdOf(at);
            step.third = third < kThirdCount ? third : PickForbiddenThird({ at }, 0.f);
            BossMechanics::Eligibility only;
            only.carriers.insert(student->GetGUID());
            MechanicRef ref = Mechanic::Zone(owner, StripSpec(owner, ThirdZone(*step.third)), Ms(warn));
            ref.Persistent(Ms(window), Ms(kOutOfBoundsTickMs)).ZTolerance(kVaultZTolerance).Eligible(only)
                .Spell(SPELL_AX_OUT_OF_BOUNDS).OnHit([](Unit*) { }).Tag(TAG_OUT_OF_BOUNDS);
        }
        else if (rule.rule == RULE_NO_RUNNING)
        {
            GuidSet who;
            who.insert(student->GetGUID());
            MechanicRef ref = Mechanic::HoldStill(owner, who, Ms(window), Ms(warn));
            ref.Tolerance(kNoRunningToleranceYd).Tag(TAG_NO_RUNNING);
        }
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "lesson-rule",
            Acore::StringFormat("rule={} student={} heroic={} third={}", RuleWords(rule.rule), student->GetName(),
                Heroic() ? 1 : 0, step.third ? int(*step.third) : -1));
    }

    // "A fortune lies in reach": inside the forbidden third, or a few steps away.
    void Open(Creature* owner, Player* student, std::size_t i)
    {
        LessonRule const& rule = kLessonRules[i];
        Step& step = _steps[i];
        step.opened = true;
        FortuneRules rules;
        rules.set = rule.rule;
        rules.players.push_back(DungeonKit::PlaneOf(student));
        rules.forbidden = step.third;
        rules.minYd = rule.fortuneMinYd;
        rules.maxYd = rule.fortuneMaxYd;
        std::vector<Vec2> const spots = PickFortuneSpots(rules, 1, Rand01, [owner](Vec2 p)
        {
            return VaultFloorZ(owner, p).has_value();
        });
        if (!spots.empty())
            step.fortune = SpawnFortune(owner, spots.front(), rule.times.windowMs);
    }

    // A failure hit: 15% (heroic 25%) of the reference row plus Weakened, once per rule.
    void Punish(Creature* owner, Player* student, std::size_t i, char const* why)
    {
        Step& step = _steps[i];
        if (step.punished)
            return;
        step.punished = true;
        uint32 const damage = Rod(owner, student, LessonFailurePct(Heroic()));
        // Not recorded on the stalker's encounter: the Weakened goes back to the study with the student (30 s).
        AddWeakened(owner, student, false);
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "lesson-fail",
            Acore::StringFormat("rule={} student={} why={} damage={}", RuleWords(kLessonRules[i].rule),
                student->GetName(), why, damage));
    }

    Map* _map = nullptr;
    uint32 _ms = 0;
    std::array<Step, kLessonRules.size()> _steps{};
};

// The Barov fortune (300543): a prop the rule book places and removes (the registry anchor and the Gold Coins look's
// summoner). `.dbtest scholo alexei lesson` also makes one the owner of a test lesson, which its AI then runs.
struct npc_sc_barov_fortune : public NullCreatureAI
{
    explicit npc_sc_barov_fortune(Creature* creature) : NullCreatureAI(creature) { }

    void UpdateAI(uint32 diff) override
    {
        if (!_lesson)
            return;
        _lesson->Update(diff);
        if (!_lesson->Done())
            return;
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "lesson-test-end",
            Acore::StringFormat("passed={} failed={}", _lesson->Passed() ? 1 : 0, _lesson->Failed() ? 1 : 0));
        _lesson.reset();
        me->DespawnOrUnsummon(1s);
    }

    void DriveLesson(std::unique_ptr<SoloLesson> lesson)
    {
        _lesson = std::move(lesson);
    }

private:
    std::unique_ptr<SoloLesson> _lesson;
};

namespace
{
    boss_lord_alexei_barov_rework* FindAlexeiAI(ChatHandler* handler)
    {
        Creature* boss = ScholoTest::FindBoss(handler, NPC_ALEXEI);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_lord_alexei_barov_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}",
                "Alexei is not running boss_lord_alexei_barov_rework (check the ScriptName).");
        return ai;
    }

    std::optional<RuleBit> RuleByKey(std::string const& key)
    {
        for (std::size_t i = 0; i < kRuleCount; ++i)
            if (key == kRuleKeys[i])
                return kRules[i];
        return std::nullopt;
    }

    Player* SelectedOrSelf(ChatHandler* handler)
    {
        Player* player = handler->getSelectedPlayer();
        return player ? player : handler->GetPlayer();
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return ScholoTest::ShowBossInfo(handler, NPC_ALEXEI, BOSS_ALEXEI);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_lord_alexei_barov_rework* ai = FindAlexeiAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Alexei: {}", ai->TestState());
        if (Player* p = SelectedOrSelf(handler))
            handler->PSendSysMessage("{}: {} Demerit(s)", p->GetName(), DungeonKit::Stacks(p, SPELL_AX_DEMERIT));
        return true;
    }

    // `.dbtest scholo alexei rule <key> [<key>]`: that rule (or pair) now; keys norunning, assembly, distance, bounds,
    // lineup, desks.
    bool HandleRule(ChatHandler* handler, std::string first, Optional<std::string> second)
    {
        std::optional<RuleBit> const a = RuleByKey(first);
        std::optional<RuleBit> const b = second ? RuleByKey(*second) : std::optional<RuleBit>(RULE_NONE);
        if (!a || !b)
        {
            handler->SendErrorMessage("{}", "Rules: norunning, assembly, distance, bounds, lineup, desks.");
            return false;
        }
        boss_lord_alexei_barov_rework* ai = FindAlexeiAI(handler);
        if (!ai)
            return false;
        RuleSet const set = RuleSet(*a | *b);
        std::string const error = ai->TestRule(set);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Alexei: rule {} announced.", SetName(set));
        return true;
    }

    bool HandleVeil(ChatHandler* handler)
    {
        boss_lord_alexei_barov_rework* ai = FindAlexeiAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestVeil();
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("{}", "Alexei: Veil of Shadow on his victim (AB11).");
        return true;
    }

    // `.dbtest scholo alexei demerit`: a Demerit and the Rod on the selected player (or you), as for a broken rule.
    bool HandleDemerit(ChatHandler* handler)
    {
        boss_lord_alexei_barov_rework* ai = FindAlexeiAI(handler);
        if (!ai)
            return false;
        Player* p = SelectedOrSelf(handler);
        std::string const error = ai->TestDemerit(p);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Alexei: a Demerit on {} (now {}).", p->GetName(),
            DungeonKit::Stacks(p, SPELL_AX_DEMERIT));
        return true;
    }

    // `.dbtest scholo alexei lesson [1]`: the Barov Family Vault's detention lesson on the selected player (or you),
    // where they stand, owned by a fortune unit that runs it (S11's lesson stalker in the real cycle); 1 = heroic.
    bool HandleLesson(ChatHandler* handler, Optional<uint32> heroic)
    {
        if (!ScholoTest::RequireScholomance(handler))
            return false;
        Player* student = SelectedOrSelf(handler);
        if (!student)
            return false;
        TempSummon* owner = student->SummonCreature(NPC_SC_BAROV_FORTUNE, student->GetPosition(),
            TEMPSUMMON_TIMED_DESPAWN, 30000);
        auto* ai = owner && owner->IsAIEnabled ? dynamic_cast<npc_sc_barov_fortune*>(owner->AI()) : nullptr;
        if (!ai)
        {
            handler->SendErrorMessage("{}", "Could not summon the lesson's owner (300543 npc_sc_barov_fortune).");
            if (owner)
                owner->DespawnOrUnsummon();
            return false;
        }
        std::unique_ptr<SoloLesson> lesson = CreateSoloLesson(Classroom::BarovVault);
        if (!lesson)
        {
            handler->SendErrorMessage("{}", "No lesson is registered for the Barov Family Vault.");
            owner->DespawnOrUnsummon();
            return false;
        }
        bool const isHeroic = heroic ? *heroic != 0 : IsHeroicMap(student);
        lesson->Start(owner, student, isHeroic);
        ai->DriveLesson(std::move(lesson));
        handler->PSendSysMessage("The Barov Family Vault's lesson on {} ({}): Out of bounds, then No running, 15 s.",
            student->GetName(), isHeroic ? "heroic" : "normal");
        return true;
    }

    // `.dbtest scholo alexei examiner`: the Graduate Examiner (300553, S13's template) where you stand.
    bool HandleExaminer(ChatHandler* handler)
    {
        if (!ScholoTest::RequireScholomance(handler))
            return false;
        if (!sObjectMgr->GetCreatureTemplate(NPC_SC_EXAMINER_ALEXEI))
        {
            handler->SendErrorMessage("{}", "No creature_template 300553 yet (S13 declares the examiners).");
            return false;
        }
        Player* gm = handler->GetPlayer();
        Creature* examiner = gm->SummonCreature(NPC_SC_EXAMINER_ALEXEI, gm->GetPosition(),
            TEMPSUMMON_CORPSE_TIMED_DESPAWN, 30000);
        if (!examiner)
        {
            handler->SendErrorMessage("{}", "The summon failed.");
            return false;
        }
        handler->PSendSysMessage("Graduate Examiner (Alexei) summoned: {} health, script {}.", examiner->GetMaxHealth(),
            examiner->GetScriptName());
        return true;
    }

    // `.dbtest scholo alexei <sub>`.
    ChatCommandTable const& AlexeiTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",    HandleState,    SEC_GAMEMASTER, Console::No },
            { "rule",     HandleRule,     SEC_GAMEMASTER, Console::No },
            { "veil",     HandleVeil,     SEC_GAMEMASTER, Console::No },
            { "demerit",  HandleDemerit,  SEC_GAMEMASTER, Console::No },
            { "lesson",   HandleLesson,   SEC_GAMEMASTER, Console::No },
            { "examiner", HandleExaminer, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_lord_alexei_barov_rework()
{
    RegisterDungeonReworkCreatureAI(boss_lord_alexei_barov_rework, ScholomanceRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sc_barov_fortune, ScholomanceRework::kInstanceScriptName);
    // The examiner's script name is AlexeiLogic.h kExaminerScriptName; S13 binds the entry in wave C.
    if (kWaveCBound)
        RegisterDungeonReworkCreatureAI(npc_sc_examiner_alexei, ScholomanceRework::kInstanceScriptName);
    RegisterSoloLesson(Classroom::BarovVault, []() -> std::unique_ptr<SoloLesson>
    {
        return std::make_unique<BarovVaultLesson>();
    });
    ScholoTest::RegisterBoss("alexei", AlexeiTestCommands());
}
