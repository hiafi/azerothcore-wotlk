/*
 * mod-dungeon-bosses, Scholomance S4: Ras Frostwhisper (10508), normal and heroic. Build spec: SC 1171-1230 (build
 * spec), SC 1000-1170 (design: pitch C "Fear of Life"), RF1-RF8; handoff section 3.4 rows RF, section 3.5 row S4,
 * section 3.6. Replaces SmartAI 10508 (Frost Armor kept in C++; Fear 12096 and Freeze 18763 retired; Frostbolt Volley
 * 8398 and Chill Nova 18099 reworked below: WP-S4's SQL rev drops the rows). Bound by apps/dbc-tools
 * source/npcs/scholomance/ras_frostwhisper.py. The stock Boon of Life aura script (spell_scholomance_boon_of_life_aura,
 * quest 5466) stays registered and still turns him human through AI()->Talk(0) and DATA_RAS_HUMAN.
 *
 *   RF1 Chill            every player of the fight gains Chill (206170, 20 stacks, never melts or dispels): +1 a
 *                        second while cold; warm: nothing on normal, +1 every 3 s on heroic. 12+ stacks add the ice
 *                        look (206171). Bots: a self-keyed RunOut (8 yd) at 17+ stacks, so they step out to freeze
 *                        alone (rolling, never resolves).
 *   RF2 Warmth           a player with two or more living, not entombed allies within 8 yd is warm (206172, the
 *                        orange glow). Bots: an always-on Stack, Cluster(2) at 7 yd, for players below 17 Chill.
 *   RF3 Entombed         at 20 stacks the player freezes for 2 s (206173, a stun) and wakes with an empty meter.
 *   RF4 Thaw             the tomb bursts as it breaks: a registry circle of 6 yd on the frozen player (spared), 30% /
 *                        45% Frost and 1 Weakened; heroic +3 Chill on everyone hit.
 *   RF5 Frost Mark       10 s, then every 15 s: a random non-tank is marked (206175, emote line 1) for 5 s, then a
 *                        10 yd Chill Nova bursts on them (a registry RunOut): allies inside take 40% / 55% Frost, +5
 *                        Chill and a knockback (206177); the marked player is not hit.
 *   RF6 Blizzard         6 s, then every 15 s: a 1.5 s cast, then a 6 yd storm for 12 s on a random non-tank in the
 *                        warm stack (a persistent registry circle on a Blizzard anchor 300534): 8% / 12% Frost and +2
 *                        Chill a second. Heroic: one on each of up to 3 non-tanks, each drifting 1.5 yd/s.
 *   RF7 Frostbolt Volley 15 s, then every 20 s: a 3 s interruptible cast at the whole room (206182, interrupt list):
 *                        15% / 40% Frost (RefFlat at launch) and the stock slow; heroic +3 Chill on everyone hit.
 *   RF8 Frost Armor      stock 18100, out of combat (re-cast when missing).
 *   Melee                DamageModifier 3.5 (the stock value, set by the DT file); heroic is the heroic template's.
 *   Arena                RasArena() with LeashOptions (no grips; holds at the edge, evades after 10 s with nobody on
 *                        it).
 *
 * Every timer runs on the AI's own clock (RasLogic.h Timeline), never on BossAI's scheduler that a cast bar pauses; a
 * Volley or Blizzard that comes due while he casts waits for the cast to end. The hard mode (WP-S12, "the Torn
 * Keepsake") fights on this AI through RasFight.h (RasHardMode hooks; this class is its RasFight). Every firing logs
 * one INFO line "scholo ras <mechanic> ..." (module.dungeonbosses); `.dbtest scholo ras <mechanic>` fires one.
 */

#include "ArenaGuard.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "RasFight.h"
#include "RasLogic.h"
#include "Random.h"
#include "ScholomanceKit.h"
#include "ScholomanceRework.h"
#include "ScholomanceTestCommand.h"
#include "ScriptedCreature.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <memory>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;
using namespace ScholoRas;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;

namespace
{
    char const* const kBossLogName = "ras";

    RasHardModeFactory& HardModeFactory()
    {
        static RasHardModeFactory factory;
        return factory;
    }

    // The floor under a point (the anchor stands on it); falls back to the given height.
    float FloorZ(WorldObject const* ref, float x, float y, float z)
    {
        float const floor = ref->GetMapHeight(x, y, z + 2.f);
        return (floor <= INVALID_HEIGHT + 1.f || std::fabs(floor - z) > 4.f) ? z : floor;
    }
}

void ScholoRas::RegisterRasHardMode(RasHardModeFactory factory)
{
    HardModeFactory() = std::move(factory);
}

std::unique_ptr<RasHardMode> ScholoRas::CreateRasHardMode(Creature* ras)
{
    RasHardModeFactory const& factory = HardModeFactory();
    return factory ? factory(ras) : nullptr;
}

// Ras Frostwhisper 10508
struct boss_ras_frostwhisper_rework : public BossAI, public RasFight
{
    explicit boss_ras_frostwhisper_rework(Creature* creature)
        : BossAI(creature, BOSS_RAS), _arena(RasArena(), LeashOptions(kBossLogName)) { }

    void Reset() override
    {
        _Reset();
        Cleanup(false);
        EnsureFrostArmor();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);       // DoZoneInCombat, BOSS_RAS IN_PROGRESS
        if (!me->IsEngaged())
            return;     // BossAI evaded

        Cleanup(false);     // a `.dbtest scholo ras` mechanic out of combat may have left something behind
        _heroic = DungeonKit::IsHeroicMap(me);
        _engaged = true;

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_RAS;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        RegisterWarmStack();
        RefreshSelfRunOut();

        bool const hardMode = _heroic && instance && instance->GetData(DATA_RAS_HARD_MODE) != 0;
        if (hardMode)
            _hardMode = CreateRasHardMode(me);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} hardmode={} handler={} at=({:.1f}, {:.1f}, {:.1f})", _heroic ? 1 : 0,
                hardMode ? 1 : 0, _hardMode ? 1 : 0, me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
        if (_hardMode)
            _hardMode->OnEngage(*this);
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "evade", Acore::StringFormat("reason={}", uint32(why)));
        Cleanup(false);
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Cleanup(true);
        BossAI::JustDied(killer);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death");
    }

    // His summons are the Blizzard anchors: invisible helpers, never zoned into combat.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        if (_hardMode && _engaged)
            _hardMode->OnDamageTaken(*this, attacker, damage);
        BossAI::DamageTaken(attacker, damage, type, mask);
    }

    void UpdateAI(uint32 diff) override
    {
        if (!me->IsInCombat())
        {
            _armorCheckMs += diff;
            if (_armorCheckMs >= kFrostArmorCheckMs)
            {
                _armorCheckMs = 0;
                EnsureFrostArmor();
            }
        }

        // Out of combat too: a `.dbtest` Blizzard goes live and drifts.
        _fightMs += diff;
        UpdateBlizzards();

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_engaged)
            return;

        // The fight clock moves every tick, cast bar or not (the Pilot's lesson); S12's transition holds it.
        bool const held = _hardMode && _hardMode->HoldsTimeline(*this);
        _timeline.Advance(diff, held);
        if (_hardMode)
        {
            _hardMode->OnUpdate(*this, diff);
            if (!_engaged || !me->IsAlive())
                return;     // the hook ended the fight
        }

        for (uint32 beats = _timeline.TakeChillBeats(); beats; --beats)
            ChillBeat();
        _runOutMs += diff;
        if (_runOutMs >= kRunOutRefreshMs)
            RefreshSelfRunOut();

        if (!held && _timeline.Due(Beat::FrostMark) && !(_hardMode && _hardMode->HoldsFrostMark(*this)))
            FrostMark(nullptr);

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;

        if (!held)
        {
            if (_timeline.Due(Beat::Volley))
                FrostboltVolley();
            else if (_timeline.Due(Beat::Blizzard))
                Blizzard(nullptr, _heroic);
        }

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ---- RasFight (the hard mode's view of the pull, RasFight.h) --------------------------------------------------

    Creature* Ras() override
    {
        return me;
    }

    bool Heroic() const override
    {
        return _heroic;
    }

    std::vector<Player*> FightPlayers() override
    {
        std::vector<Player*> out;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player || !player->IsAlive() || player->IsGameMaster() || !player->IsInWorld())
                continue;
            if (!me->IsInCombatWith(player) && !_arena.Contains(player))
                continue;
            out.push_back(player);
        }
        return out;
    }

    bool IsWarm(Player const* player) const override
    {
        return player && _warm.count(player->GetGUID());
    }

    bool IsEntombed(Player const* player) const override
    {
        return player && player->HasAura(SPELL_RF_ENTOMBED);
    }

    uint32 ChillOf(Player const* player) const override
    {
        return player ? DungeonKit::Stacks(player, SPELL_RF_CHILL) : 0;
    }

    uint32 AddChill(Player* player, int32 delta, char const* why) override
    {
        if (!player || !player->IsAlive() || IsEntombed(player) || !delta)
            return ChillOf(player);
        uint32 const now = DungeonKit::AddStacks(player, SPELL_RF_CHILL, delta, me, kChillMax);
        SyncChillLook(player, now);
        if (delta >= 3 || delta <= -3)
            Log("chill", Acore::StringFormat("player={} delta={} now={} why={}", player->GetName(), delta, now, why));
        if (Freezes(now))
        {
            Freeze(player);
            return 0;
        }
        return now;
    }

    void Thaw(Player* player, bool burst) override
    {
        if (!player)
            return;
        player->RemoveAurasDueToSpell(SPELL_RF_ENTOMBED);
        if (burst)
            ThawBurst(player, Milliseconds(kThawNowMs));
    }

    void Track(MechanicHandle handle) override
    {
        if (handle)
            _live.push_back(handle);
    }

    void Log(char const* mechanic, std::string const& detail = {}) override
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, mechanic, detail);
    }

    // ---- RF1 / RF2 / RF3 / RF4: Chill, warmth, the tomb and the thaw ------------------------------------------------

    // One second of the fight: warmth for everyone first (the buff and the record), then the Chill each one builds.
    void ChillBeat()
    {
        std::vector<Player*> const players = FightPlayers();
        std::vector<Player*> givers;
        for (Player* p : players)
            if (!IsEntombed(p))
                givers.push_back(p);

        std::vector<std::pair<Player*, bool>> states;
        for (Player* p : players)
        {
            bool warm = false;
            if (!IsEntombed(p))
            {
                uint32 allies = 0;
                for (Player* q : givers)
                    if (q != p && p->GetExactDist2d(q) <= kWarmRadius
                        && std::fabs(p->GetPositionZ() - q->GetPositionZ()) <= kWarmZBand)
                        ++allies;
                warm = ScholoRas::IsWarm(allies);
            }
            SetWarm(p, warm);
            states.emplace_back(p, warm);
        }

        if (_hardMode && _hardMode->HoldsChillBeat(*this))
            return;
        for (auto const& [player, warm] : states)
        {
            if (IsEntombed(player) || !player->IsAlive())
                continue;
            if (uint32 const gain = _clocks[player->GetGUID()].Beat(warm, _heroic))
                AddChill(player, int32(gain), warm ? "warm" : "cold");
        }
    }

    void SetWarm(Player* player, bool warm)
    {
        if (warm)
        {
            _warm.insert(player->GetGUID());
            if (!player->HasAura(SPELL_RF_WARMTH))
                player->AddAura(SPELL_RF_WARMTH, player);
        }
        else
        {
            _warm.erase(player->GetGUID());
            player->RemoveAurasDueToSpell(SPELL_RF_WARMTH);
        }
    }

    void SyncChillLook(Player* player, uint32 stacks)
    {
        bool const deep = DeepChill(stacks);
        if (deep && !player->HasAura(SPELL_RF_DEEP_CHILL))
            player->AddAura(SPELL_RF_DEEP_CHILL, player);
        else if (!deep)
            player->RemoveAurasDueToSpell(SPELL_RF_DEEP_CHILL);
    }

    // RF3: the meter empties; S12's permanent tomb takes the freeze when it wants it, else the 2 s tomb and its thaw.
    void Freeze(Player* player)
    {
        DungeonKit::AddStacks(player, SPELL_RF_CHILL, -int32(kChillMax), me, kChillMax);
        SyncChillLook(player, 0);
        _clocks.erase(player->GetGUID());
        SetWarm(player, false);
        if (_hardMode && _hardMode->OnFreeze(*this, player))
        {
            Log("freeze", Acore::StringFormat("player={} tomb=hardmode", player->GetName()));
            return;
        }
        me->AddAura(SPELL_RF_ENTOMBED, player);
        ThawBurst(player, Milliseconds(kTombMs));
        Log("freeze", Acore::StringFormat("player={} tomb={}ms", player->GetName(), kTombMs));
    }

    // RF4: a circle of 6 yd on the frozen player (the anchor is spared) that lands as the tomb breaks.
    void ThawBurst(Player* player, Milliseconds warn)
    {
        MechanicRef ref = Mechanic::Circle(me, player, kThawRadius, warn);
        ref.Damage(kThawPct(_heroic)).Weakened().Spell(SPELL_RF_THAW).Tag(TAG_THAW);
        if (uint32 const chill = kThawChill(_heroic))
            ref.OnHit(OnChillHit(chill, "thaw"));
        Track(ref.Handle());
    }

    // ---- RF5 Frost Mark ---------------------------------------------------------------------------------------------

    // False when nobody qualified (a non-tank, not entombed, on his threat list); `forced`: that player.
    bool FrostMark(Player* forced)
    {
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.tankIfAlone = false;       // never a tank (SC RF5)
            DungeonKit::ExcludeGuids(rule, EntombedGuids());
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!target)
        {
            _timeline.Retry(Beat::FrostMark);
            return false;
        }
        _timeline.Done(Beat::FrostMark);
        me->CastSpell(target, SPELL_RF_FROST_MARK, true);
        Talk(EMOTE_RAS_FROST_MARK, target);
        MechanicRef ref = Mechanic::RunOut(me, target, kFrostMarkRadius, Milliseconds(kFrostMarkWarnMs));
        ref.Damage(kFrostMarkPct(_heroic)).Spell(SPELL_RF_CHILL_NOVA).Rider(SPELL_RF_CHILL_NOVA_KNOCK)
            .Tag(TAG_FROST_MARK).OnHit(OnChillHit(kFrostMarkChill, "chill-nova"));
        Track(ref.Handle());
        Log("frost-mark", Acore::StringFormat("target={} heroic={}", target->GetName(), _heroic ? 1 : 0));
        return true;
    }

    // ---- RF6 Blizzard -----------------------------------------------------------------------------------------------

    // `forced`: one storm on that player (and on heroic two more beside them), else the build spec's picks.
    bool Blizzard(Player* forced, bool heroic)
    {
        uint32 const count = kBlizzardCount(heroic);
        std::vector<Position> spots;
        std::string names;
        if (forced)
        {
            Position const at = forced->GetPosition();
            spots.push_back(at);
            for (uint32 i = 1; i < count; ++i)
            {
                Vec2 const p = DungeonKit::Advance(DungeonKit::PlaneOf(forced), float(i) * 2.1f, kBlizzardRadius * 2.f);
                spots.emplace_back(p.x, p.y, at.GetPositionZ(), 0.f);
            }
            names = forced->GetName();
        }
        else
        {
            for (Player* target : PickBlizzardTargets(count))
            {
                spots.push_back(target->GetPosition());
                names += (names.empty() ? "" : ",") + target->GetName();
            }
        }
        if (spots.empty())
        {
            _timeline.Retry(Beat::Blizzard);
            return false;
        }
        _timeline.Done(Beat::Blizzard);
        DungeonKit::CastBar(me, SPELL_RF_BLIZZARD_CAST);
        for (Position const& at : spots)
            SpawnBlizzard(at, heroic);
        Log("blizzard", Acore::StringFormat("count={} on={} heroic={}", spots.size(), names, heroic ? 1 : 0));
        return true;
    }

    // Random non-tanks standing warm first (SC RF6: "in the stack"), then any non-tank (a solo tank in a test too).
    std::vector<Player*> PickBlizzardTargets(uint32 count)
    {
        GuidSet notWarm = EntombedGuids();
        for (Player* p : FightPlayers())
            if (!IsWarm(p))
                notWarm.insert(p->GetGUID());
        DungeonKit::PickRule warm;
        warm.nonTank = true;
        DungeonKit::ExcludeGuids(warm, notWarm);
        std::vector<Player*> picks = DungeonKit::PickPlayers(me, warm, count);
        if (picks.size() < count)
        {
            GuidSet taken = EntombedGuids();
            for (Player* p : picks)
                taken.insert(p->GetGUID());
            DungeonKit::PickRule any;
            any.nonTank = true;
            any.tankIfAlone = picks.empty();
            DungeonKit::ExcludeGuids(any, taken);
            for (Player* p : DungeonKit::PickPlayers(me, any, count - uint32(picks.size())))
                picks.push_back(p);
        }
        return picks;
    }

    // The anchor holds the registry circle (a persistent zone that follows it) and, once live, the storm's look.
    void SpawnBlizzard(Position const& at, bool drift)
    {
        float const z = FloorZ(me, at.GetPositionX(), at.GetPositionY(), at.GetPositionZ());
        Creature* anchor = me->SummonCreature(NPC_SC_BLIZZARD_ANCHOR, at.GetPositionX(), at.GetPositionY(), z, 0.f,
            TEMPSUMMON_TIMED_DESPAWN, kBlizzardAnchorLifeMs);
        if (!anchor)
            return;
        anchor->SetReactState(REACT_PASSIVE);
        MechanicRef ref = Mechanic::Circle(me, anchor, kBlizzardRadius, Milliseconds(kBlizzardCastMs));
        ref.Persistent(Milliseconds(kBlizzardLifeMs), Milliseconds(kBlizzardTickMs)).Damage(kBlizzardPct(drift))
            .Spell(SPELL_RF_BLIZZARD).Tag(TAG_BLIZZARD).OnHit(OnChillHit(kBlizzardChill, "blizzard"));
        Track(ref.Handle());
        _blizzards.push_back({ anchor->GetGUID(), _fightMs + kBlizzardCastMs, 0, drift, false });
    }

    // The storms go live after the cast: the look, and on heroic the drift (a new 3 s storm every 2 s on the way).
    void UpdateBlizzards()
    {
        for (auto it = _blizzards.begin(); it != _blizzards.end();)
        {
            Creature* anchor = me->GetMap()->GetCreature(it->guid);
            if (!anchor || !anchor->IsAlive())
            {
                it = _blizzards.erase(it);
                continue;
            }
            if (!it->live && _fightMs >= it->liveAt)
            {
                it->live = true;
                if (it->drift)
                {
                    StartDrift(anchor);
                    it->nextLook = _fightMs;
                }
                else
                    anchor->CastSpell(anchor, SPELL_RF_BLIZZARD_LOOK, true);
            }
            if (it->live && it->drift && _fightMs >= it->nextLook
                && _fightMs < it->liveAt + kBlizzardLifeMs)
            {
                anchor->CastSpell(anchor, SPELL_RF_BLIZZARD_DRIFT, true);
                it->nextLook = _fightMs + kBlizzardDriftLookEveryMs;
            }
            ++it;
        }
    }

    void StartDrift(Creature* anchor)
    {
        float const facing = frand(0.f, DungeonKit::kTwoPi);
        Vec2 const end = DriftEnd(DungeonKit::PlaneOf(anchor), facing, kBlizzardDriftYd, kDriftCenter, kDriftRadius,
            kDriftMargin);
        float const z = FloorZ(anchor, end.x, end.y, anchor->GetPositionZ());
        anchor->GetMotionMaster()->MovePoint(1, Position(end.x, end.y, z, facing), FORCED_MOVEMENT_NONE,
            kBlizzardDriftSpeed, false);
        Log("blizzard-drift", Acore::StringFormat("from=({:.1f},{:.1f}) to=({:.1f},{:.1f})", anchor->GetPositionX(),
            anchor->GetPositionY(), end.x, end.y));
    }

    // ---- RF7 Frostbolt Volley ---------------------------------------------------------------------------------------

    void FrostboltVolley()
    {
        _timeline.Done(Beat::Volley);
        SpellCastResult const result = me->CastSpell(me, SPELL_RF_FROSTBOLT_VOLLEY, false);
        Mechanic::NoteNextCastIn(me, SPELL_RF_FROSTBOLT_VOLLEY, Milliseconds(kVolleyEveryMs));
        Log("volley", Acore::StringFormat("heroic={} result={}", _heroic ? 1 : 0, uint32(result)));
    }

    // ---- `.dbtest scholo ras` entry points --------------------------------------------------------------------------

    bool HeroicMap() const
    {
        return DungeonKit::IsHeroicMap(me);
    }

    bool CastingNow() const
    {
        return me->HasUnitState(UNIT_STATE_CASTING);
    }

    void TestFrostMark(Player* target)
    {
        _heroic = _engaged ? _heroic : HeroicMap();
        FrostMark(target);
    }

    void TestBlizzard(Player* target, bool heroic)
    {
        Blizzard(target, heroic);
    }

    void TestVolley()
    {
        _heroic = _engaged ? _heroic : HeroicMap();
        FrostboltVolley();
    }

    uint32 TestSetChill(Player* player, uint32 stacks)
    {
        _heroic = _engaged ? _heroic : HeroicMap();
        return AddChill(player, int32(std::min(stacks, kChillMax)) - int32(ChillOf(player)), "test");
    }

    std::string TestState()
    {
        std::string out = Acore::StringFormat("engaged={} heroic={} hardmode={} t={}ms next mark/blizzard/volley="
            "{}/{}/{}ms blizzards={}", _engaged ? 1 : 0, _heroic ? 1 : 0, _hardMode ? 1 : 0, _timeline.now,
            _timeline.next[0], _timeline.next[1], _timeline.next[2], _blizzards.size());
        for (Player* p : FightPlayers())
            out += Acore::StringFormat("\n  {}: chill {} warm {} tomb {}", p->GetName(), ChillOf(p), IsWarm(p) ? 1 : 0,
                IsEntombed(p) ? 1 : 0);
        return out;
    }

private:
    struct BlizzardAnchor
    {
        ObjectGuid guid;
        uint32 liveAt = 0;          // _fightMs
        uint32 nextLook = 0;
        bool drift = false;
        bool live = false;
    };

    static uint32 constexpr kThawNowMs = 250;       // a thaw S12 lands at once (its broken tomb)
    static float constexpr kWarmZBand = 5.f;        // allies on the same floor

    void Describe()
    {
        // Boss data (build spec): target Ras; interrupt the Volley; nothing to dispel. S12 adds the tombs.
        BossMechanics::Descriptor d;
        d.interrupts.emplace_back(NPC_RAS, SPELL_RF_FROSTBOLT_VOLLEY, 2, Milliseconds(kVolleyEveryMs));
        Mechanic::Describe(me, std::move(d));
    }

    // RF2 for the bots: an always-on Stack, Cluster(2) at 7 yd, for every player below 17 Chill. No telegraph: the
    // humans read the Warmth glow and buff (rings on every player for the whole fight would bury the real markers).
    void RegisterWarmStack()
    {
        BossMechanics::Eligibility eligible;
        eligible.auraSpell = SPELL_RF_CHILL;
        eligible.minStacks = 0;
        eligible.maxStacks = uint8(kChillRunOutAt - 1);
        MechanicRef ref = Mechanic::Stack(me, me, kWarmStackRadius, Milliseconds(kWarmStackTickMs));
        ref.Cluster(uint8(kWarmAllies)).Eligible(eligible)
            .Persistent(Milliseconds(kWarmStackMs), Milliseconds(kWarmStackTickMs)).NoTelegraph().Tag(TAG_WARMTH);
        _warmStack = ref.Handle();
    }

    // RF1 for the bots: a RunOut keyed to the player's own Chill (17+), replaced before it resolves. No telegraph:
    // the humans read their stacks and the ice look from 12.
    void RefreshSelfRunOut()
    {
        _runOutMs = 0;
        if (_selfRunOut)
            Mechanic::Cancel(me, _selfRunOut);
        MechanicRef ref = Mechanic::RunOut(me, nullptr, kChillRunOutRadius, Milliseconds(kRunOutWarnMs));
        ref.SelfTrigger(SPELL_RF_CHILL, kChillRunOutAt).NoTelegraph().Tag(TAG_CHILL);
        _selfRunOut = ref.Handle();
    }

    // +`stacks` Chill on each player a registry mechanic hits (captures the map and guid only, never a Unit*).
    std::function<void(Unit*)> OnChillHit(uint32 stacks, char const* why)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, stacks, why](Unit* hit)
        {
            Player* player = hit ? hit->ToPlayer() : nullptr;
            Creature* ras = map ? map->GetCreature(guid) : nullptr;
            if (!player || !ras || !ras->IsAlive() || !ras->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_ras_frostwhisper_rework*>(ras->AI()))
                ai->AddChill(player, int32(stacks), why);
        };
    }

    GuidSet EntombedGuids()
    {
        GuidSet out;
        for (Player* p : FightPlayers())
            if (IsEntombed(p))
                out.insert(p->GetGUID());
        return out;
    }

    void EnsureFrostArmor()
    {
        if (me->IsAlive() && !me->HasAura(SPELL_FROST_ARMOR))
            DoCastSelf(SPELL_FROST_ARMOR, true);
    }

    // The pull's state, gone: the hard mode's own end first, every mechanic, the anchors, every aura of the fight.
    void Cleanup(bool died)
    {
        if (_hardMode)
        {
            _hardMode->OnEnd(*this, died);
            _hardMode.reset();
        }
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        if (_selfRunOut)
            Mechanic::Cancel(me, _selfRunOut);
        if (_warmStack)
            Mechanic::Cancel(me, _warmStack);
        _selfRunOut = {};
        _warmStack = {};
        summons.DespawnAll();
        _blizzards.clear();
        _clocks.clear();
        _warm.clear();
        _timeline = Timeline{};
        _runOutMs = 0;
        _engaged = false;
        _arena.Reset();
        if (instance)
            for (uint32 spell : { uint32(SPELL_RF_CHILL), uint32(SPELL_RF_DEEP_CHILL), uint32(SPELL_RF_WARMTH),
                uint32(SPELL_RF_ENTOMBED), uint32(SPELL_RF_FROST_MARK) })
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
    }

    DungeonKit::ArenaGuard _arena;
    Timeline _timeline;
    std::unique_ptr<RasHardMode> _hardMode;
    std::unordered_map<ObjectGuid, ChillClock> _clocks;
    GuidSet _warm;
    std::vector<BlizzardAnchor> _blizzards;
    std::vector<MechanicHandle> _live;
    MechanicHandle _selfRunOut;
    MechanicHandle _warmStack;
    uint32 _fightMs = 0;            // ms the AI has run (anchors' clock; never held)
    uint32 _runOutMs = 0;
    uint32 _armorCheckMs = 0;
    bool _heroic = false;
    bool _engaged = false;
};

// RF7 Frostbolt Volley 206182: 15% / 40% of the reference row on every player it hits (RefFlat at launch, so the
// target's defensives count; the spell ignores caster modifiers), and on heroic +3 Chill when it lands.
class spell_scholo_ras_frostbolt_volley : public SpellScript
{
    PrepareSpellScript(spell_scholo_ras_frostbolt_volley);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        if (Unit* caster = GetCaster())
            SetEffectValue(static_cast<int32>(DungeonKit::RefFlatOn(caster, GetHitUnit(),
                kVolleyPct(DungeonKit::IsHeroicMap(caster)))));
    }

    void AddChill()
    {
        Player* target = GetHitUnit() ? GetHitUnit()->ToPlayer() : nullptr;
        Creature* caster = GetCaster() ? GetCaster()->ToCreature() : nullptr;
        if (!target || !caster || !caster->IsAIEnabled)
            return;
        uint32 const chill = kVolleyChill(DungeonKit::IsHeroicMap(caster));
        if (!chill)
            return;
        if (auto* ai = dynamic_cast<boss_ras_frostwhisper_rework*>(caster->AI()))
            ai->AddChill(target, int32(chill), "volley");
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_scholo_ras_frostbolt_volley::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
        AfterHit += SpellHitFn(spell_scholo_ras_frostbolt_volley::AddChill);
    }
};

namespace
{
    boss_ras_frostwhisper_rework* FindRasAI(ChatHandler* handler)
    {
        Creature* boss = ScholoTest::FindBoss(handler, NPC_RAS);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_ras_frostwhisper_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Ras is not running boss_ras_frostwhisper_rework (check the ScriptName).");
        return ai;
    }

    // The selected player, else the GM.
    Player* TestTarget(ChatHandler* handler)
    {
        if (Player* selected = handler->getSelectedPlayer())
            return selected;
        return handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return ScholoTest::ShowBossInfo(handler, NPC_RAS, BOSS_RAS);
    }

    // `.dbtest scholo ras state`: the clock and every fight player's Chill, warmth and tomb.
    bool HandleState(ChatHandler* handler)
    {
        boss_ras_frostwhisper_rework* ai = FindRasAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Ras: {}", ai->TestState());
        return true;
    }

    // `.dbtest scholo ras chill <n>`: sets the selected player's (or your) Chill; 20 freezes (RF1, RF3, RF4).
    bool HandleChill(ChatHandler* handler, uint32 stacks)
    {
        boss_ras_frostwhisper_rework* ai = FindRasAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        uint32 const now = ai->TestSetChill(target, stacks);
        handler->PSendSysMessage("Ras: {} has {} Chill{}.", target->GetName(), now,
            stacks >= kChillMax ? " (frozen: the 2 s tomb, then the thaw)" : "");
        return true;
    }

    // `.dbtest scholo ras mark`: Frost Mark on the selected player (or you), the Nova 5 s later (RF5).
    bool HandleMark(ChatHandler* handler)
    {
        boss_ras_frostwhisper_rework* ai = FindRasAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        ai->TestFrostMark(target);
        handler->PSendSysMessage("Ras: Frost Mark on {} (RF5).", target->GetName());
        return true;
    }

    // `.dbtest scholo ras blizzard [1]`: a Blizzard on the selected player (or you); 1 = the heroic form (three,
    // drifting), 0 = normal; default the map's (RF6).
    bool HandleBlizzard(ChatHandler* handler, Optional<uint32> heroic)
    {
        boss_ras_frostwhisper_rework* ai = FindRasAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        if (ai->CastingNow())
        {
            handler->SendErrorMessage("{}", "Ras is casting; try again in a moment.");
            return false;
        }
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        ai->TestBlizzard(target, isHeroic);
        handler->PSendSysMessage("Ras: Blizzard ({}) on {} (RF6).", isHeroic ? "heroic, drifting" : "normal",
            target->GetName());
        return true;
    }

    // `.dbtest scholo ras volley`: the Frostbolt Volley now (RF7; kick it to test the interrupt).
    bool HandleVolley(ChatHandler* handler)
    {
        boss_ras_frostwhisper_rework* ai = FindRasAI(handler);
        if (!ai)
            return false;
        if (ai->CastingNow())
        {
            handler->SendErrorMessage("{}", "Ras is casting; try again in a moment.");
            return false;
        }
        ai->TestVolley();
        handler->PSendSysMessage("{}", "Ras: Frostbolt Volley (RF7).");
        return true;
    }

    ChatCommandTable const& RasTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",    HandleState,    SEC_GAMEMASTER, Console::No },
            { "chill",    HandleChill,    SEC_GAMEMASTER, Console::No },
            { "mark",     HandleMark,     SEC_GAMEMASTER, Console::No },
            { "blizzard", HandleBlizzard, SEC_GAMEMASTER, Console::No },
            { "volley",   HandleVolley,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_ras_frostwhisper_rework()
{
    RegisterDungeonReworkCreatureAI(boss_ras_frostwhisper_rework, ScholomanceRework::kInstanceScriptName);
    RegisterSpellScript(spell_scholo_ras_frostbolt_volley);
    ScholoTest::RegisterBoss("ras", RasTestCommands());
}
