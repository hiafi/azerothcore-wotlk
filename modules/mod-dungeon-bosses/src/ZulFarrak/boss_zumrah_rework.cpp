/*
 * mod-dungeon-bosses, Zul'Farrak D3: Witch Doctor Zum'rah (7271), normal and heroic. Build spec:
 * docs/dungeons/zul-farrak-rework.md "Witch Doctor Zum'rah" (ZR1-ZR14, rulings 17-20, 45); handoff sections 3.5 row
 * D3, 3.6, 3.8 (the bowl), 3.9 rows 3 and 4, 3.10, 7 #29, #30, #48, 10. Replaces SmartAI 7271 (dropped by S0's rev) and
 * gives the stock Skeleton of Zum'rah 7786 a script. Bound by apps/dbc-tools source/npcs/zul_farrak/zumrah.py. Pure
 * rules and every number: ZumrahLogic.h.
 *
 *   Faction       35 until area trigger 962's SmartAI sets 37 (as stock; DC hook 5 reads 35 / 37), restored in Reset.
 *                 He stands at his cauldron and never moves (combat movement off); melee only when a target is there
 *   ZR1 Rend      15 s, then every 25 s on a fixed grid: a 2 s Arcane bar (never kickable, never locked by a kicked
 *                 Shadow cast: rule 24) and emote line 3 naming the walker: everyone in turn, the tank and the healer
 *                 included (RendCandidates), never the walker
 *   ZR2 walk      Between Worlds on the walker for 15 s: the ghost look, +40% speed, sight of the spirit world
 *                 (invisibility type 11). The living side cannot reach the walker: his CanAIAttack and the
 *                 Skeletons' refuse a walker, the Volley and the echoes skip them. Their kit stays (ruling 19)
 *   ZR3 husk      an Empty Vessel 301010 where they stood, wearing their look (aura 247 cast by the walker) and the
 *                 tether (a channel field). Skeleton hits on it land on the walker; other damage to it is passed to
 *                 the walker. At the walk's end the walker snaps back to the husk and it goes
 *   ZR4 souls     a Lost Soul 301011 every 6 s (heroic 2 s) from the pull, from a grave within 60 yd of the cauldron
 *                 (7 #29 A), crawling to the cauldron along the floor at 3 (4) yd/s: the kit's CrawlPickups with
 *                 onlyWhileCarriers (walkers only, dormant between walks; a soul still crawling when a walk ends is
 *                 the next walker's: G1). The walker takes one by touch (2 yd): a Gathered Souls stack
 *   ZR6 bound     a soul at the cauldron binds: a Bound Dead 301012 at his feet (then the neck mouth, 7 #30 A), emote
 *                 line 4 at most every 10 s; normal caps them at 4 (past it the soul is lost), heroic none (ruling
 *                 45). A walker with two Gathered Souls within 3 yd frees one (the kit's DwellSoaks, dwell 0)
 *   ZR7 ward      Ward of the Dead on him: one stack a Bound Dead, the amount set here (WardReductionPct)
 *   ZR8 Skeletons the stock Ward of Zum'rah 11086 at 2 s, then every 30-36 s (heroic 25 s); its Skeletons
 *                 (npc_zf_zumrah_skeleton) live until killed, go for the husk if one stands (10,000 threat: a taunt
 *                 takes them), else the tank, else the nearest player; a hit every 2 s for 3% (heroic 5%)
 *   ZR9 Volley    8 s, then every 12-16 s (never sooner than 10 s): a kickable 3 s (heroic 2 s) Shadow cast; landed,
 *                 20% (heroic 35%) on every player within 30 yd but the walker
 *   ZR10 Bolt     1 s, then every 3-4 s, only where it ends before the next Rend and Volley: a kickable 3 s Shadow
 *                 bolt, 8% on his target (a random living player while the target walks)
 *   Heroic        ZR11 Soul Burn 6% on the walker and ZR12 a Soul Echo (5 yd under a random living player, 2 s, 35%
 *                 and Weakened, the living only) for every soul gathered; ZR13 a Restless Wail from each Bound Dead
 *                 within 15 yd of the walker every 4 s (6 yd, 1.5 s, 40% and Weakened); ZR14 Grasping Graves every
 *                 3 s of a walk (two graves within 20 yd of the walker, 6 yd, 1.5 s, 40% and Weakened). The walker's
 *                 circles are seen only in the spirit world (BM-1 SeenOnlyWith, 7 #48 A)
 *   Bots          the souls' Soaks (walkers, one claim a bot, nearest first), the Bound Dead's (2 Gathered Souls), the
 *                 Volley on the interrupt list, the ward then Skeletons on a husk in the kill order
 *
 * Every timer runs on the AI's own clock (ZumrahLogic.h Timeline), cast bar or not. Cleanup (a reset, an evade, his
 * death) ends the walk (the walker snaps back), takes back every soul, Bound Dead, Skeleton, ward, circle and aura.
 * Every firing logs one INFO line "zf-build zumrah <mechanic> ..."; `.dbtest zf zumrah <mechanic>` fires one.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitChase.h"
#include "DungeonKitSoaks.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ThreatManager.h"
#include "ZulFarrakKit.h"
#include "ZulFarrakRework.h"
#include "ZulFarrakTestCommand.h"
#include "ZumrahLogic.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <set>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ZulFarrakRework;
using namespace ZfZumrah;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "zumrah";
    float constexpr kFloorBandYd = 4.f;
    float constexpr kSpiritZBandYd = 6.f;           // the walker's circles and the Wail's reach: same floor
    uint32 constexpr kGatheredMaxStacks = 99;       // the aura's CumulativeAura (zumrah.py)
    uint32 constexpr kWardMaxStacks = 99;
    uint32 constexpr kSkeletonPollMs = 1000;
    uint32 constexpr kFreedLookMs = 1500;           // a freed Bound Dead stays this long for its look
    int32 constexpr kHuskWalkerGuid = 1;            // npc_zf_empty_vessel::SetGUID id

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    void LogZr(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, mechanic, detail);
    }

    // A player the fight acts on: in the world, alive, not a game master.
    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    // The walker (Between Worlds): nothing on the living side reaches them.
    bool IsWalker(Unit const* unit)
    {
        return unit && unit->HasAura(SPELL_ZR_BETWEEN_WORLDS);
    }

    // `p` on the bowl's floor; the given height when the map has none near it.
    Position OnFloor(WorldObject const* ref, Vec2 p, float z, float o = 0.f)
    {
        float const floor = ref->GetMapHeight(p.x, p.y, z + 3.f);
        bool const ok = floor > INVALID_HEIGHT + 1.f && std::fabs(floor - z) <= kFloorBandYd;
        return Position(p.x, p.y, ok ? floor : z, o);
    }

    // The souls' Soaks are the kit's (CrawlPickups::RegisterSoak). BM-1 asks for `.HealerWithinTankReach()` (section
    // 7 #30 A: a bot healer walker takes only the souls within reach of its tank) and `.SeenOnlyWith(11)` (7 #48 A:
    // the living never see a soul's ring) on them. The kit's CrawlPickupSpec has no hook for registry options yet
    // (STAGE-D3-REPORT Shared-file request 1: a `configure` member, as DwellSoakSpec has); this sets it the moment the
    // kit has it, and reports whether it could.
    template <class Spec>
    bool ConfigureSoulSoak(Spec& spec)
    {
        if constexpr (requires { spec.configure; })
        {
            spec.configure = [](BossMechanics::MechanicRef& ref)
            {
                ref.HealerWithinTankReach().SeenOnlyWith(kSpiritWorldType);
            };
            return true;
        }
        else
            return false;
    }
}

// Witch Doctor Zum'rah 7271
struct boss_zumrah_rework : public BossAI
{
    explicit boss_zumrah_rework(Creature* creature)
        : BossAI(creature, BOSS_ZUMRAH), _arena(BowlArena(), LeashOptions(kBossLogName))
    {
        me->SetCombatMovement(false);   // he stands at his cauldron (SP "does not move")
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();
        Cleanup(true);
        // Faction 35 until area trigger 962's SmartAI sets 37 (DC hook 5 reads 35 / 37): his stock SmartAI's reset
        // row restored it; it is dropped, so Reset does.
        me->RestoreFaction();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        Cleanup(true);      // a `.dbtest` mechanic out of combat may have left something behind
        _heroic = IsHeroicMap(me);
        _engaged = true;
        OnBossPull(me, kBossLogName);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_ZUMRAH;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        Talk(SAY_ZUMRAH_AGGRO);
        _timeline.Start(_heroic);
        _soulClock.Start(_heroic);
        DungeonKit::CrawlPickupSpec probe;
        _soulSoakOptions = ConfigureSoulSoak(probe);
        LogZr("setup", Acore::StringFormat("rise-graves={} soul-soak-options={} (healreach, seen=11)",
            RiseGraveList().size(), _soulSoakOptions ? 1 : 0));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        if (_engaged)
            LogZr("evade", Acore::StringFormat("reason={} {}", uint32(why), Counts()));
        Cleanup(true);
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        LogZr("death", Acore::StringFormat("clock={}s {} killer={}", _timeline.Now() / 1000, Counts(),
            killer ? killer->GetName() : "none"));
        Cleanup(true);
        BossAI::JustDied(killer);
    }

    void KilledUnit(Unit* victim) override
    {
        if (victim && victim->IsPlayer())
            Talk(SAY_ZUMRAH_KILL);
    }

    // The wards, husks, souls, Bound Dead and looks: never zoned into combat.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    // Nothing on the living side reaches a walker (appendix B 2.3: by script, not an immunity).
    bool CanAIAttack(Unit const* who) const override
    {
        return !IsWalker(who);
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        BossAI::OnSpellCast(spell);
        if (!spell || !_engaged)
            return;
        if (spell->Id == SPELL_ZR_SPIRIT_REND)
            RendLands();
        else if (spell->Id == VolleySpell())
            VolleyLands();
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (!spell || !_engaged)
            return;
        if (spell->Id == VolleySpell())
        {
            ++_counts.volleysStopped;
            LogZr("volley-stopped");
        }
        else if (spell->Id == SPELL_ZR_SHADOW_BOLT)
            ++_counts.boltsStopped;
        else if (spell->Id == SPELL_ZR_SPIRIT_REND && _rend.pending)
        {
            // Not interruptible and he is stun immune: only a script or an engine stop. The walk still happens.
            LogZr("rend-stopped", "the walk starts anyway");
            RendLands();
        }
    }

    void UpdateAI(uint32 diff) override
    {
        ZulFarrak::NoAssist(me);        // rule 27, LESSONS L1: every tick, before UpdateVictim
        bool const hasVictim = UpdateVictim();
        if (!_engaged || !me->IsEngaged() || !me->IsAlive())
            return;

        // The fight's clocks run whether he has a victim or not (a walker alone on his threat list leaves him none).
        _timeline.Advance(diff);
        TickWalk();
        TickSouls(diff);
        _frees.Update(me, diff);
        TickBoundDead();
        TickWard();
        TickSkeletons(diff);
        if (!_engaged)
            return;
        if (!hasVictim)
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_engaged || me->HasUnitState(UNIT_STATE_CASTING))
            return;

        if (_timeline.SkipBolt(RollBoltGap()))
            ++_counts.boltsSkipped;
        Act const act = _timeline.Next();
        if (act != Act::None)
        {
            if (Begin(act))
            {
                _timeline.Done(act, act == Act::Volley ? RollVolleyGap() : RollBoltGap());
                NoteNext();
            }
            else
                _timeline.Retry(act);
            if (me->HasUnitState(UNIT_STATE_CASTING))
                return;
        }
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // For the adds (the Skeletons and the husk find him through the instance)
    // ----------------------------------------------------------------------------------------------------------------

    Creature* Self() const { return me; }
    bool Engaged() const { return _engaged && me->IsAlive(); }
    bool Heroic() const { return _heroic; }
    ObjectGuid Husk() const { return _walk.husk; }
    ObjectGuid Walker() const { return _walk.walker; }

    void SkeletonRisen(Creature* skeleton)
    {
        if (!skeleton)
            return;
        _skeletons.insert(skeleton->GetGUID());
        ++_counts.skeletons;
    }

    void SkeletonGone(ObjectGuid guid)
    {
        _skeletons.erase(guid);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest zf zumrah` entry points (the numbers are the map's difficulty)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Rend,
        EndWalk,
        Soul,
        Bind,
        FreeAll,
        Ward,
        Volley,
        Bolt,
        Echo,
        Wail,
        Graves,
    };

    // An empty string when fired; otherwise why not. `who` is the GM's selected player (or the GM), `n` a count.
    std::string TestFire(TestMechanic mechanic, Player* who, uint32 n)
    {
        if (!_engaged || !me->IsEngaged())
            return "Zum'rah must be in combat (the picks read his threat list, the mechanics his encounter).";
        Player* forced = CountsAsPlayer(who) ? who : nullptr;
        bool const casting = me->HasUnitState(UNIT_STATE_CASTING);
        switch (mechanic)
        {
            case TestMechanic::Rend:
                if (_walk.Active() || _rend.pending)
                    return "A walk is running (end it with `endwalk`).";
                if (forced)
                    StartWalk(forced);
                else if (casting || !BeginRend())
                    return "He is casting, or nobody can walk.";
                break;
            case TestMechanic::EndWalk:
                if (!_walk.Active())
                    return "Nobody walks.";
                EndWalk("gm", true);
                break;
            case TestMechanic::Soul:
                for (uint32 i = 0; i < std::max<uint32>(1, n); ++i)
                    RaiseSoul();
                break;
            case TestMechanic::Bind:
                for (uint32 i = 0; i < std::max<uint32>(1, n); ++i)
                    SoulArrived();
                break;
            case TestMechanic::FreeAll:
                while (!_bound.empty())
                    FreeBound(_bound.front().unit, nullptr);
                break;
            case TestMechanic::Ward:
                CastWard();
                break;
            case TestMechanic::Volley:
                if (casting)
                    return "He is casting already.";
                if (!CastVolley())
                    return "The engine refused it (a kick locked Shadow?).";
                break;
            case TestMechanic::Bolt:
                if (casting)
                    return "He is casting already.";
                if (!CastBolt(forced))
                    return "The engine refused it (a kick locked Shadow?) or nobody is there.";
                break;
            case TestMechanic::Echo:
                if (!RegisterEcho(forced))
                    return "Nobody living to put it under.";
                break;
            case TestMechanic::Wail:
            {
                Player* walker = WalkerPlayer();
                if (!walker)
                    return "Nobody walks.";
                RegisterWail(walker, me->GetGUID());
                break;
            }
            case TestMechanic::Graves:
            {
                Player* walker = WalkerPlayer();
                if (!walker)
                    return "Nobody walks.";
                EruptGraves(walker);
                break;
            }
        }
        return {};
    }

    std::string TestState()
    {
        Player* walker = WalkerPlayer();
        return Acore::StringFormat("clock={}s heroic={} health={:.1f} walker={} walk-left={}ms souls={} bound={} "
            "ward={}% skeletons={} next: rend {} ms, volley {} ms, bolt {} ms, ward {} ms, soul {} ms; {}",
            _timeline.Now() / 1000, _heroic ? 1 : 0, me->GetHealthPct(), walker ? walker->GetName() : "-",
            _walk.Active() && _walk.endsAt > _timeline.Now() ? _walk.endsAt - _timeline.Now() : 0, _souls.Count(),
            _bound.size(), WardReductionPct(static_cast<uint32>(_bound.size()), _heroic), _skeletons.size(),
            _timeline.In(Act::Rend), _timeline.In(Act::Volley), _timeline.In(Act::Bolt), _timeline.WardIn(),
            _soulClock.In(_timeline.Now()), Counts());
    }

private:
    // ----------------------------------------------------------------------------------------------------------------
    // His casts
    // ----------------------------------------------------------------------------------------------------------------

    uint32 VolleySpell() const
    {
        return _heroic ? SPELL_ZR_VOLLEY_HEROIC : SPELL_ZR_VOLLEY;
    }

    static uint32 RollVolleyGap()
    {
        return urand(Tune::kVolleyEveryMinMs, Tune::kVolleyEveryMaxMs);
    }

    static uint32 RollBoltGap()
    {
        return urand(Tune::kBoltEveryMinMs, Tune::kBoltEveryMaxMs);
    }

    // False: refused by the engine (a lockout), tried again shortly. Nobody to act on is a done beat.
    bool Begin(Act act)
    {
        switch (act)
        {
            case Act::Rend:
                if (!BeginRend())
                    LogZr("rend-skip", "nobody can walk");
                return true;
            case Act::Volley:
                return CastVolley();
            case Act::Bolt:
                return CastBolt(nullptr);
            case Act::None:
                break;
        }
        return true;
    }

    // The bots' overload hold reads when the kickable Volley comes next.
    void NoteNext()
    {
        Mechanic::NoteNextCastIn(me, VolleySpell(), Ms(_timeline.In(Act::Volley)));
    }

    // A refusal (a lockout) is retried every half second: one line per run of them.
    void LogRefused(char const* what, SpellCastResult result)
    {
        if (_timeline.Now() < _refusedLogAt)
            return;
        _refusedLogAt = _timeline.Now() + 3000;
        LogZr("refused", Acore::StringFormat("{} result={}", what, uint32(result)));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // ZR1 Spirit Rend, ZR2 Between Worlds, ZR3 the Empty Vessel
    // ----------------------------------------------------------------------------------------------------------------

    // The player Spirit Rend tears next: everyone in turn (RendCandidates), the tank and the healer included, never
    // the walker, never one off the bowl.
    Player* PickWalker()
    {
        std::vector<uint64> candidates;
        for (Player* player : FightPlayers())
            if (_arena.Contains(player) && !IsWalker(player))
                candidates.push_back(player->GetGUID().GetRawValue());
        if (candidates.empty())
            return nullptr;
        std::vector<uint64> const pool = RendCandidates(candidates, _walked, _lastWalker);
        if (pool.empty())
            return nullptr;
        uint64 const raw = pool[urand(0, uint32(pool.size()) - 1)];
        return ObjectAccessor::GetPlayer(*me, ObjectGuid(raw));
    }

    bool BeginRend()
    {
        Player* target = PickWalker();
        if (!target)
            return false;
        me->StopMoving();
        SpellCastResult const result = me->CastSpell(me, SPELL_ZR_SPIRIT_REND, false);
        if (result != SPELL_CAST_OK)
        {
            LogRefused("rend", result);
            return false;
        }
        Talk(EMOTE_ZUMRAH_REND, target);
        _rend.pending = true;
        _rend.target = target->GetGUID();
        _rend.endsAt = _timeline.Now() + Tune::kRendCastMs;
        ++_counts.rends;
        LogZr("rend", Acore::StringFormat("target={} tank={} walked={}", target->GetName(),
            target == me->GetVictim() ? 1 : 0, _walked.size()));
        return true;
    }

    // The bar has ended (OnSpellCast; the poll's fallback if the hook never came).
    void RendLands()
    {
        if (!_rend.pending)
            return;
        ObjectGuid const guid = _rend.target;
        _rend = RendState();
        Player* target = ObjectAccessor::GetPlayer(*me, guid);
        if (!CountsAsPlayer(target) || !target->IsInMap(me) || !_arena.Contains(target))
        {
            // Gone or dead during the bar: the next in turn walks instead.
            target = PickWalker();
            LogZr("rend-retarget", Acore::StringFormat("new={}", target ? target->GetName() : "none"));
        }
        if (target)
            StartWalk(target);
    }

    void StartWalk(Player* walker)
    {
        if (_walk.Active())
            EndWalk("replaced", true);
        uint64 const raw = walker->GetGUID().GetRawValue();
        _walked.insert(raw);
        _lastWalker = raw;
        _walk = WalkState();
        _walk.walker = walker->GetGUID();
        _walk.endsAt = _timeline.Now() + Tune::kWalkMs;
        _walk.nextGravesAt = _timeline.Now() + Tune::kGravesEveryMs;
        ++_counts.walks;

        Position const at = walker->GetPosition();
        if (TempSummon* husk = me->SummonCreature(NPC_ZF_EMPTY_VESSEL, at, TEMPSUMMON_MANUAL_DESPAWN))
        {
            _walk.husk = husk->GetGUID();
            if (husk->IsAIEnabled)
                husk->AI()->SetGUID(walker->GetGUID(), kHuskWalkerGuid);
            walker->CastSpell(husk, SPELL_ZR_EMPTY_VESSEL, true);
            husk->SetGuidValue(UNIT_FIELD_CHANNEL_OBJECT, walker->GetGUID());
            husk->SetUInt32Value(UNIT_CHANNEL_SPELL, SPELL_ZR_TETHER);
        }
        me->CastSpell(walker, SPELL_ZR_BETWEEN_WORLDS, true);
        _souls.SetCarriers(me, GuidSet{ walker->GetGUID() });
        for (BoundDead& b : _bound)
            b.nextWailAt = _timeline.Now() + WailFirstMs(b.slot);
        LogZr("walk", Acore::StringFormat("walker={} tank={} at=({:.1f}, {:.1f}, {:.1f}) husk={} souls={} bound={}",
            walker->GetName(), walker == me->GetVictim() ? 1 : 0, at.GetPositionX(), at.GetPositionY(),
            at.GetPositionZ(), _walk.husk ? 1 : 0, _souls.Count(), _bound.size()));
    }

    // `snapBack`: a living walker returns to the husk (wherever it stands). Gathered souls still carried are lost.
    void EndWalk(char const* why, bool snapBack)
    {
        if (!_walk.Active())
            return;
        WalkState const walk = _walk;
        _walk = WalkState();
        _souls.SetCarriers(me, GuidSet());
        Player* walker = ObjectAccessor::GetPlayer(*me, walk.walker);
        Creature* husk = walk.husk ? ObjectAccessor::GetCreature(*me, walk.husk) : nullptr;
        uint32 lost = 0;
        if (walker)
        {
            lost = DungeonKit::Stacks(walker, SPELL_ZR_GATHERED_SOULS);
            walker->RemoveAurasDueToSpell(SPELL_ZR_GATHERED_SOULS);
            walker->RemoveAurasDueToSpell(SPELL_ZR_BETWEEN_WORLDS);
            if (snapBack && husk && walker->IsAlive() && walker->IsInMap(me))
                walker->NearTeleportTo(husk->GetPositionX(), husk->GetPositionY(), husk->GetPositionZ(),
                    husk->GetOrientation());
        }
        if (husk)
        {
            husk->SetGuidValue(UNIT_FIELD_CHANNEL_OBJECT, ObjectGuid::Empty);
            husk->SetUInt32Value(UNIT_CHANNEL_SPELL, 0);
            husk->DespawnOrUnsummon();
        }
        _counts.soulsLost += lost;
        LogZr("walk-end", Acore::StringFormat("why={} walker={} alive={} gathered={} lost={} snapped={}", why,
            walker ? walker->GetName() : "gone", walker && walker->IsAlive() ? 1 : 0, walk.gathered, lost,
            snapBack && husk && walker && walker->IsAlive() ? 1 : 0));
    }

    Player* WalkerPlayer() const
    {
        if (!_walk.Active())
            return nullptr;
        Player* walker = ObjectAccessor::GetPlayer(*me, _walk.walker);
        return CountsAsPlayer(walker) && walker->IsInMap(me) ? walker : nullptr;
    }

    void TickWalk()
    {
        if (_rend.pending && _timeline.Now() >= _rend.endsAt + kRetryMs)
            RendLands();    // OnSpellCast never came
        if (!_walk.Active())
            return;
        Player* walker = ObjectAccessor::GetPlayer(*me, _walk.walker);
        if (!walker || !walker->IsInWorld() || !walker->IsInMap(me))
        {
            EndWalk("left", false);
            return;
        }
        if (!walker->IsAlive())
        {
            EndWalk("died", false);
            return;
        }
        if (_timeline.Now() >= _walk.endsAt)
        {
            EndWalk("timeout", true);
            return;
        }
        if (!walker->HasAura(SPELL_ZR_BETWEEN_WORLDS))
        {
            EndWalk("aura-gone", true);
            return;
        }
        if (_heroic && _timeline.Now() >= _walk.nextGravesAt)
        {
            _walk.nextGravesAt += Tune::kGravesEveryMs;
            EruptGraves(walker);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // ZR4 Lost Souls, ZR5 Gathered Souls, ZR11 Soul Burn, ZR12 Soul Echo
    // ----------------------------------------------------------------------------------------------------------------

    static std::vector<std::size_t> const& RiseGraveList()
    {
        static std::vector<std::size_t> const graves = RiseGraves();
        return graves;
    }

    void TickSouls(uint32 diff)
    {
        for (uint32 n = _soulClock.Rises(_timeline.Now()); n > 0; --n)
            RaiseSoul();
        _souls.Update(me, diff);
    }

    void RaiseSoul()
    {
        std::vector<std::size_t> const& graves = RiseGraveList();
        if (graves.empty())
            return;
        std::size_t const index = graves[urand(0, uint32(graves.size()) - 1)];
        Point3 const& grave = kGraves[index];
        Position const at = OnFloor(me, grave.XY(), grave.z);

        DungeonKit::CrawlPickupSpec spec;
        spec.entry = NPC_ZF_LOST_SOUL;
        spec.radius = Tune::kSoulTouchYd;
        spec.wait = Milliseconds(0);
        spec.crawlSpeed = Tune::kSoulSpeed(_heroic);
        spec.reach = Tune::kSoulBindReachYd;
        spec.count = 1;
        spec.oneClaimPerBot = true;
        spec.onlyWhileCarriers = true;
        spec.tag = TAG_ZR_SOUL;
        ConfigureSoulSoak(spec);
        Map* map = me->GetMap();
        ObjectGuid const boss = me->GetGUID();
        spec.onPick = [map, boss](Player* taker, Position const& /*where*/)
        {
            if (boss_zumrah_rework* ai = From(map, boss))
                ai->SoulGathered(taker);
        };
        spec.onReach = [map, boss](ObjectGuid /*goal*/, Position const& /*where*/)
        {
            if (boss_zumrah_rework* ai = From(map, boss))
                ai->SoulArrived();
        };
        DungeonKit::CrawlGoal goal;
        goal.point = Position(kCauldron.x, kCauldron.y, kCauldron.z, 0.f);
        uint32 const id = _souls.Add(me, at, std::move(spec), goal);
        ++_counts.souls;
        LogZr(id ? "soul" : "soul-fail", Acore::StringFormat("grave={} at=({:.1f}, {:.1f}) out={:.1f} live={} "
            "dormant={}", index, at.GetPositionX(), at.GetPositionY(), DungeonKit::Distance(grave.XY(),
            kCauldron.XY()), _souls.Count(), id && _souls.Dormant(id) ? 1 : 0));
    }

    void SoulGathered(Player* taker)
    {
        if (!_engaged || !taker)
            return;
        uint32 const stacks = DungeonKit::AddStacks(taker, SPELL_ZR_GATHERED_SOULS, 1, me, kGatheredMaxStacks);
        ++_walk.gathered;
        ++_counts.gathered;
        if (_heroic)
        {
            CastPercent(taker, SPELL_ZR_SOUL_BURN, Tune::kSoulBurnPct);
            RegisterEcho(nullptr);
        }
        LogZr("soul-gathered", Acore::StringFormat("by={} walker={} stacks={} walk-total={}", taker->GetName(),
            taker->GetGUID() == _walk.walker ? 1 : 0, stacks, _walk.gathered));
    }

    // ZR12: a 5 yd Circle AoE under a random living player (the tank included, never the walker), 2 s, 35% and
    // Weakened, the living only.
    bool RegisterEcho(Player* forced)
    {
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = false;
            rule.exclude = OffBowl();
            if (_walk.Active())
                rule.exclude.push_back(_walk.walker.GetRawValue());
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!target)
            return false;
        BossMechanics::Eligibility living;
        living.carriers = LivingSet();
        living.playersOnly = true;
        if (living.carriers.empty())
            return false;
        Position const at = target->GetPosition();
        MechanicRef ref = Mechanic::Circle(me, at, Tune::kEchoRadiusYd, Ms(Tune::kEchoWarnMs));
        ref.School(SPELL_SCHOOL_SHADOW).Spell(SPELL_ZR_SOUL_ECHO).Damage(Tune::kEchoPct).TankDamage(Tune::kEchoPct)
            .Weakened().Eligible(living).Tag(TAG_ZR_ECHO).Within(ZumrahFloorBounds());
        Map* map = me->GetMap();
        ObjectGuid const boss = me->GetGUID();
        ref.OnResolve([map, boss, at](BossMechanics::ResolveResult const& /*result*/)
        {
            if (boss_zumrah_rework* ai = From(map, boss))
                ai->LandingLook(at, SPELL_ZR_FREED, false);
        });
        ++_counts.echoes;
        LogZr("echo", Acore::StringFormat("under={} tank={} at=({:.1f}, {:.1f})", target->GetName(),
            target == me->GetVictim() ? 1 : 0, at.GetPositionX(), at.GetPositionY()));
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // ZR6 the Bound Dead, ZR7 the Ward of the Dead, ZR13 Restless Wail, ZR14 Grasping Graves
    // ----------------------------------------------------------------------------------------------------------------

    void SoulArrived()
    {
        if (!_engaged || !me->IsAlive())
            return;
        uint32 const bound = static_cast<uint32>(_bound.size());
        if (!BindsOrLost(bound, _heroic))
        {
            ++_counts.soulsPastCap;
            LogZr("soul-past-cap", Acore::StringFormat("bound={}", bound));
            return;
        }
        std::vector<bool> taken;
        for (BoundDead const& b : _bound)
        {
            if (b.slot >= taken.size())
                taken.resize(b.slot + 1, false);
            taken[b.slot] = true;
        }
        std::size_t const slot = FirstFreeSlot(taken);
        Point3 const spot = BoundDeadSpot(slot);
        float const facing = std::atan2(kZumrahSpawn.y - spot.y, kZumrahSpawn.x - spot.x);
        Position const at = OnFloor(me, spot.XY(), spot.z, facing);
        TempSummon* unit = me->SummonCreature(NPC_ZF_BOUND_DEAD, at, TEMPSUMMON_MANUAL_DESPAWN);
        if (!unit)
        {
            LogZr("bind-fail", Acore::StringFormat("slot={}", slot));
            return;
        }
        unit->CastSpell(unit, SPELL_ZR_SPIRIT_WORLD, true);
        unit->CastSpell(unit, SPELL_ZR_BOUND, true);
        BoundDead b;
        b.unit = unit->GetGUID();
        b.slot = slot;
        b.nextWailAt = _timeline.Now() + WailFirstMs(slot);
        b.freeSoak = AddFreeSoak(unit);
        _bound.push_back(b);
        ++_counts.bound;
        UpdateWard();
        if (_timeline.Now() >= _boundEmoteAt)
        {
            _boundEmoteAt = _timeline.Now() + Tune::kBoundEmoteEveryMs;
            Talk(EMOTE_ZUMRAH_BOUND);
        }
        LogZr("bound", Acore::StringFormat("slot={} bound={} ward={}% walker={}", slot, _bound.size(),
            WardReductionPct(static_cast<uint32>(_bound.size()), _heroic), _walk.Active() ? 1 : 0));
    }

    // ZR6: a walker with two Gathered Souls within 3 yd frees it (bots: a Soak for those carriers, seen only in the
    // spirit world; a bot healer past its tank's reach is not offered it).
    uint32 AddFreeSoak(Creature* unit)
    {
        DungeonKit::DwellSoakSpec spec;
        spec.radius = Tune::kFreeRadiusYd;
        spec.zBand = kSpiritZBandYd;
        spec.dwell = Milliseconds(0);
        spec.count = 1;
        spec.who.auraSpell = SPELL_ZR_GATHERED_SOULS;
        spec.who.minStacks = static_cast<uint8>(Tune::kSoulsToFree);
        spec.who.playersOnly = true;
        spec.oneClaimPerBot = true;
        spec.tag = TAG_ZR_FREE;
        spec.configure = [](BossMechanics::MechanicRef& ref)
        {
            ref.HealerWithinTankReach().SeenOnlyWith(kSpiritWorldType);
        };
        Map* map = me->GetMap();
        ObjectGuid const boss = me->GetGUID();
        spec.onDone = [map, boss](Player* taker, Unit* anchor)
        {
            if (boss_zumrah_rework* ai = From(map, boss))
                if (anchor)
                    ai->FreeBound(anchor->GetGUID(), taker);
        };
        spec.onLost = [map, boss](ObjectGuid anchor)
        {
            if (boss_zumrah_rework* ai = From(map, boss))
                ai->BoundLost(anchor);
        };
        spec.dungeon = kLogDungeon;
        spec.boss = kBossLogName;
        spec.name = "free";
        return _frees.Add(me, unit, std::move(spec));
    }

    // `taker`: the walker who brought the souls (none: `.dbtest`).
    void FreeBound(ObjectGuid guid, Player* taker)
    {
        auto const it = std::find_if(_bound.begin(), _bound.end(), [guid](BoundDead const& b)
        {
            return b.unit == guid;
        });
        if (it == _bound.end())
            return;
        BoundDead const b = *it;
        _bound.erase(it);
        _frees.CancelOn(me, guid);
        if (taker)
            DungeonKit::AddStacks(taker, SPELL_ZR_GATHERED_SOULS, -int32(Tune::kSoulsToFree), me, kGatheredMaxStacks);
        if (Creature* unit = ObjectAccessor::GetCreature(*me, guid))
        {
            unit->CastSpell(unit, SPELL_ZR_FREED, true);
            unit->DespawnOrUnsummon(Ms(kFreedLookMs));
        }
        ++_counts.freed;
        UpdateWard();
        LogZr("freed", Acore::StringFormat("slot={} by={} bound={} ward={}%", b.slot,
            taker ? taker->GetName() : "gm", _bound.size(),
            WardReductionPct(static_cast<uint32>(_bound.size()), _heroic)));
    }

    // A Bound Dead gone by anything else (a GM, a despawn): out of the count.
    void BoundLost(ObjectGuid guid)
    {
        auto const it = std::find_if(_bound.begin(), _bound.end(), [guid](BoundDead const& b)
        {
            return b.unit == guid;
        });
        if (it == _bound.end())
            return;
        _bound.erase(it);
        UpdateWard();
        LogZr("bound-lost", Acore::StringFormat("bound={}", _bound.size()));
    }

    // ZR7: one stack a Bound Dead (the count players read), the amount WardReductionPct (ruling 45 past four).
    void UpdateWard()
    {
        uint32 const n = static_cast<uint32>(_bound.size());
        uint32 const now = DungeonKit::Stacks(me, SPELL_ZR_WARD_OF_THE_DEAD);
        if (n != now)
            DungeonKit::AddStacks(me, SPELL_ZR_WARD_OF_THE_DEAD, int32(n) - int32(now), me, kWardMaxStacks);
        if (!n)
            return;
        if (Aura* aura = me->GetAura(SPELL_ZR_WARD_OF_THE_DEAD))
            if (AuraEffect* effect = aura->GetEffect(EFFECT_0))
                effect->ChangeAmount(-WardReductionPct(n, _heroic));
    }

    // ZR13 (heroic): each Bound Dead within 15 yd of the walker wails at them every 4 s, a second apart.
    void TickBoundDead()
    {
        if (!_heroic || !_walk.Active())
            return;
        Player* walker = WalkerPlayer();
        if (!walker)
            return;
        for (BoundDead& b : _bound)
        {
            if (_timeline.Now() < b.nextWailAt)
                continue;
            Creature* unit = ObjectAccessor::GetCreature(*me, b.unit);
            bool const inRange = unit && unit->GetExactDist2d(walker) <= Tune::kWailRangeYd
                && std::fabs(unit->GetPositionZ() - walker->GetPositionZ()) <= kSpiritZBandYd;
            if (!inRange)
            {
                b.nextWailAt = _timeline.Now() + WailFirstMs(b.slot);
                continue;
            }
            b.nextWailAt = _timeline.Now() + Tune::kWailEveryMs;
            RegisterWail(walker, b.unit);
        }
    }

    // The walker-only circles: the walker alone is hit, the living never see them (7 #48 A).
    BossMechanics::Eligibility WalkerOnly(Player* walker) const
    {
        BossMechanics::Eligibility e;
        e.carriers = GuidSet{ walker->GetGUID() };
        e.playersOnly = true;
        return e;
    }

    void RegisterWail(Player* walker, ObjectGuid from)
    {
        Position const at = walker->GetPosition();
        MechanicRef ref = Mechanic::Circle(me, at, Tune::kWailRadiusYd, Ms(Tune::kWailWarnMs));
        ref.School(SPELL_SCHOOL_SHADOW).Spell(SPELL_ZR_RESTLESS_WAIL).Damage(Tune::kWailPct)
            .TankDamage(Tune::kWailPct).Weakened().Eligible(WalkerOnly(walker)).SeenOnlyWith(kSpiritWorldType)
            .Tag(TAG_ZR_WAIL).Within(ZumrahFloorBounds());
        ++_counts.wails;
        LogZr("wail", Acore::StringFormat("walker={} from={} at=({:.1f}, {:.1f})", walker->GetName(),
            from.ToString(), at.GetPositionX(), at.GetPositionY()));
    }

    // ZR14 (heroic): two graves within 20 yd of the walker (fewer in range: only those, 7 #29 A).
    void EruptGraves(Player* walker)
    {
        std::vector<std::size_t> near = GravesNear({ walker->GetPositionX(), walker->GetPositionY() },
            Tune::kGravesRangeYd);
        uint32 erupted = 0;
        while (!near.empty() && erupted < Tune::kGravesCount)
        {
            std::size_t const pick = urand(0, uint32(near.size()) - 1);
            std::size_t const index = near[pick];
            near.erase(near.begin() + pick);
            Point3 const& grave = kGraves[index];
            Position const at = OnFloor(me, grave.XY(), grave.z);
            MechanicRef ref = Mechanic::Circle(me, at, Tune::kGravesRadiusYd, Ms(Tune::kGravesWarnMs));
            ref.School(SPELL_SCHOOL_SHADOW).Spell(SPELL_ZR_GRASPING_GRAVES).Damage(Tune::kGravesPct)
                .TankDamage(Tune::kGravesPct).Weakened().Eligible(WalkerOnly(walker)).SeenOnlyWith(kSpiritWorldType)
                .Tag(TAG_ZR_GRAVE).Within(ZumrahFloorBounds());
            Map* map = me->GetMap();
            ObjectGuid const boss = me->GetGUID();
            ref.OnResolve([map, boss, at](BossMechanics::ResolveResult const& /*result*/)
            {
                if (boss_zumrah_rework* ai = From(map, boss))
                    ai->LandingLook(at, SPELL_ZR_GRAVE_ERUPTION, true);
            });
            ++erupted;
        }
        _counts.graves += erupted;
        LogZr("graves", Acore::StringFormat("walker={} erupted={}", walker->GetName(), erupted));
    }

    // A look where a circle lands: a stalker casting `spell`, seen only in the spirit world when `spiritWorld`.
    void LandingLook(Position const& at, uint32 spell, bool spiritWorld)
    {
        if (!_engaged)
            return;
        Creature* stalker = me->SummonCreature(NPC_ZF_GRAVE_STALKER, at, TEMPSUMMON_TIMED_DESPAWN,
            Tune::kGraveLookMs);
        if (!stalker)
            return;
        stalker->SetReactState(REACT_PASSIVE);
        if (spiritWorld)
            stalker->CastSpell(stalker, SPELL_ZR_SPIRIT_WORLD, true);
        stalker->CastSpell(stalker, spell, true);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // ZR8 Ward of Zum'rah and its Skeletons
    // ----------------------------------------------------------------------------------------------------------------

    void TickWard()
    {
        if (!_timeline.WardDue())
            return;
        CastWard();
        _timeline.WardDone(urand(Tune::kWardEveryMinMs(_heroic), Tune::kWardEveryMaxMs(_heroic)));
    }

    // The stock spell as it is (the ward and its Skeletons are stock entries); triggered, so no lockout stops it.
    void CastWard()
    {
        me->CastSpell(me, SPELL_WARD_OF_ZUMRAH, true);
        ++_counts.wards;
        LogZr("ward", Acore::StringFormat("skeletons={} husk={}", _skeletons.size(), _walk.husk ? 1 : 0));
    }

    void TickSkeletons(uint32 diff)
    {
        _skeletonPollMs += diff;
        if (_skeletonPollMs < kSkeletonPollMs)
            return;
        _skeletonPollMs = 0;
        for (auto it = _skeletons.begin(); it != _skeletons.end();)
        {
            Creature* s = ObjectAccessor::GetCreature(*me, *it);
            if (!s || !s->IsAlive())
                it = _skeletons.erase(it);
            else
                ++it;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // ZR9 Shadow Bolt Volley and ZR10 Shadow Bolt
    // ----------------------------------------------------------------------------------------------------------------

    bool CastVolley()
    {
        me->StopMoving();
        SpellCastResult const result = me->CastSpell(me, VolleySpell(), false);
        if (result != SPELL_CAST_OK)
        {
            LogRefused("volley", result);
            return false;
        }
        ++_counts.volleys;
        LogZr("volley", Acore::StringFormat("cast={}ms", Tune::kVolleyCastMs(_heroic)));
        return true;
    }

    // Landed (not kicked): every player within 30 yd but the walker.
    void VolleyLands()
    {
        float const pct = Tune::kVolleyPct(_heroic);
        uint32 hit = 0;
        for (MapReference const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!CountsAsPlayer(player) || IsWalker(player) || !me->IsWithinDist(player, Tune::kVolleyRangeYd))
                continue;
            CastPercent(player, SPELL_ZR_VOLLEY_HIT, pct);
            ++hit;
        }
        ++_counts.volleysLanded;
        LogZr("volley-lands", Acore::StringFormat("hit={} pct={:.0f}", hit, pct));
    }

    // His target, or a random living player while the target walks (or is off the bowl).
    bool CastBolt(Player* forced)
    {
        Unit* target = forced;
        if (!target)
        {
            Unit* victim = me->GetVictim();
            Player* player = victim ? victim->ToPlayer() : nullptr;
            if (CountsAsPlayer(player) && !IsWalker(player) && _arena.Contains(player))
                target = player;
            else
            {
                DungeonKit::PickRule rule;
                rule.nonTank = false;
                rule.exclude = OffBowl();
                if (_walk.Active())
                    rule.exclude.push_back(_walk.walker.GetRawValue());
                target = DungeonKit::PickPlayer(me, rule);
            }
        }
        if (!target)
            return true;    // nobody to bolt: a done beat
        CastSpellExtraArgs args;
        args.AddSpellBP0(static_cast<int32>(DungeonKit::RefFlatOn(me, target, Tune::kBoltPct(_heroic))));
        SpellCastResult const result = me->CastSpell(target, SPELL_ZR_SHADOW_BOLT, args);
        if (result != SPELL_CAST_OK)
        {
            LogRefused("bolt", result);
            return false;
        }
        ++_counts.bolts;
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data, plumbing, cleanup
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        using BossMechanics::Condition;
        using BossMechanics::TargetEntry;
        using BossMechanics::Who;
        BossMechanics::Descriptor d;
        d.interrupts.emplace_back(NPC_ZUMRAH, VolleySpell(), kVolleyKickPriority, Ms(Tune::kVolleyEveryMinMs));
        d.targets.push_back(TargetEntry(NPC_WARD_OF_ZUMRAH, kWardKillPriority, Who::Dps));
        d.targets.push_back(TargetEntry(NPC_SKELETON_OF_ZUMRAH, kHuskSkeletonKillPriority, Who::Dps,
            Condition::Custom([](Unit const* u)
            {
                Unit const* victim = u ? u->GetVictim() : nullptr;
                return victim && victim->GetEntry() == NPC_ZF_EMPTY_VESSEL;
            })));
        Mechanic::Describe(me, std::move(d));
        Mechanic::NoteNextCastIn(me, VolleySpell(), Ms(Tune::kVolleyFirstMs));
    }

    // `pct` percent of the reference row (the tank row on the tank) on `target` through one of his script-amount
    // spells.
    void CastPercent(Player* target, uint32 spellId, float pct)
    {
        if (!CountsAsPlayer(target))
            return;
        CastSpellExtraArgs args(TRIGGERED_FULL_MASK);
        args.AddSpellBP0(static_cast<int32>(DungeonKit::RefFlatOn(me, target, pct)));
        me->CastSpell(target, spellId, args);
    }

    // The players on his threat list the fight acts on (a walker's reference is offline, so read the whole list).
    std::vector<Player*> FightPlayers() const
    {
        std::vector<Player*> out;
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
        {
            Unit* unit = ref->GetVictim();
            Player* player = unit ? unit->ToPlayer() : nullptr;
            if (CountsAsPlayer(player) && player->IsInMap(me))
                out.push_back(player);
        }
        return out;
    }

    // Who the random picks skip: whoever is off the bowl (L6: never a corpse runner).
    std::vector<uint64> OffBowl() const
    {
        std::vector<uint64> out;
        for (Player* player : FightPlayers())
            if (!_arena.Contains(player))
                out.push_back(player->GetGUID().GetRawValue());
        return out;
    }

    // The living side now: every player in the fight on the bowl but the walker.
    GuidSet LivingSet() const
    {
        GuidSet out;
        for (Player* player : FightPlayers())
            if (!IsWalker(player) && _arena.Contains(player))
                out.insert(player->GetGUID());
        return out;
    }

    std::string Counts() const
    {
        return Acore::StringFormat("rends={} walks={} souls={} gathered={} lost={} bound={} past-cap={} freed={} "
            "wards={} skeletons={} volleys={} landed={} stopped={} bolts={} bolts-stopped={} bolts-skipped={} "
            "echoes={} wails={} graves={}", _counts.rends, _counts.walks, _counts.souls, _counts.gathered,
            _counts.soulsLost, _counts.bound, _counts.soulsPastCap, _counts.freed, _counts.wards, _counts.skeletons,
            _counts.volleys, _counts.volleysLanded, _counts.volleysStopped, _counts.bolts, _counts.boltsStopped,
            _counts.boltsSkipped, _counts.echoes, _counts.wails, _counts.graves);
    }

    static boss_zumrah_rework* From(Map* map, ObjectGuid guid)
    {
        Creature* boss = map ? map->GetCreature(guid) : nullptr;
        if (!boss || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_zumrah_rework*>(boss->AI());
    }

    // The pull's state, gone (a reset, an evade, his death, a new pull). `_engaged` goes first: the stopped casts'
    // OnSpellFailed then does nothing. `snapBack`: a living walker returns to the husk.
    void Cleanup(bool snapBack)
    {
        _engaged = false;
        EndWalk("cleanup", snapBack);
        _rend = RendState();
        if (me->IsNonMeleeSpellCast(false))
            me->InterruptNonMeleeSpells(false);
        _souls.Clear(me);
        _frees.Clear(me);
        for (BoundDead const& b : _bound)
            if (Creature* unit = ObjectAccessor::GetCreature(*me, b.unit))
                unit->DespawnOrUnsummon();
        _bound.clear();
        for (ObjectGuid const& guid : _skeletons)
            if (Creature* s = ObjectAccessor::GetCreature(*me, guid))
                s->DespawnOrUnsummon();
        _skeletons.clear();
        summons.DespawnAll();
        me->RemoveAurasDueToSpell(SPELL_ZR_WARD_OF_THE_DEAD);
        if (instance)
            for (uint32 const spell : { uint32(SPELL_ZR_BETWEEN_WORLDS), uint32(SPELL_ZR_GATHERED_SOULS) })
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
        _timeline = Timeline();
        _soulClock = SoulClock();
        _walked.clear();
        _lastWalker = 0;
        _boundEmoteAt = 0;
        _skeletonPollMs = 0;
        _counts = CountsState();
        _refusedLogAt = 0;
        _arena.Reset();
    }

    struct RendState
    {
        bool pending = false;       // the bar is up; the walk starts when it ends
        ObjectGuid target;
        uint64 endsAt = 0;
    };

    struct WalkState
    {
        ObjectGuid walker;
        ObjectGuid husk;
        uint64 endsAt = 0;
        uint64 nextGravesAt = 0;
        uint32 gathered = 0;

        bool Active() const { return !walker.IsEmpty(); }
    };

    struct BoundDead
    {
        ObjectGuid unit;
        std::size_t slot = 0;
        uint64 nextWailAt = 0;
        uint32 freeSoak = 0;
    };

    struct CountsState
    {
        uint32 rends = 0;
        uint32 walks = 0;
        uint32 souls = 0;
        uint32 gathered = 0;
        uint32 soulsLost = 0;
        uint32 bound = 0;
        uint32 soulsPastCap = 0;
        uint32 freed = 0;
        uint32 wards = 0;
        uint32 skeletons = 0;
        uint32 volleys = 0;
        uint32 volleysLanded = 0;
        uint32 volleysStopped = 0;
        uint32 bolts = 0;
        uint32 boltsStopped = 0;
        uint32 boltsSkipped = 0;
        uint32 echoes = 0;
        uint32 wails = 0;
        uint32 graves = 0;
    };

    DungeonKit::ArenaGuard _arena;
    DungeonKit::CrawlPickups _souls;
    DungeonKit::DwellSoaks _frees;
    Timeline _timeline;
    SoulClock _soulClock;
    RendState _rend;
    WalkState _walk;
    std::vector<BoundDead> _bound;
    GuidSet _skeletons;
    std::set<uint64> _walked;
    uint64 _lastWalker = 0;
    uint64 _boundEmoteAt = 0;
    uint64 _refusedLogAt = 0;
    uint32 _skeletonPollMs = 0;
    CountsState _counts;
    bool _heroic = false;
    bool _engaged = false;
    bool _soulSoakOptions = false;
};

namespace
{
    boss_zumrah_rework* ZumrahAI(WorldObject const* from)
    {
        InstanceScript* instance = from ? from->GetInstanceScript() : nullptr;
        if (!instance)
            return nullptr;
        Creature* boss = ObjectAccessor::GetCreature(*from, instance->GetGuidData(kGuidBossBase + BOSS_ZUMRAH));
        if (!boss || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_zumrah_rework*>(boss->AI());
    }
}

// Skeleton of Zum'rah 7786 (stock entry, summoned by the stock ward): lives until killed, goes for the husk first.
struct npc_zf_zumrah_skeleton : public ScriptedAI
{
    explicit npc_zf_zumrah_skeleton(Creature* creature) : ScriptedAI(creature) { }

    void IsSummonedBy(WorldObject* /*summoner*/) override
    {
        // SP ZR8 "Skeletons until killed": the stock 11088 summons them for 20 s.
        if (TempSummon* summon = me->ToTempSummon())
            summon->SetTempSummonType(TEMPSUMMON_CORPSE_DESPAWN);
        boss_zumrah_rework* boss = ZumrahAI(me);
        if (!boss || !boss->Engaged())
        {
            me->DespawnOrUnsummon();
            return;
        }
        _boss = boss->Self()->GetGUID();
        _heroic = boss->Heroic();
        boss->SkeletonRisen(me);
        Pick(true);
    }

    void Reset() override
    {
        _strikeMs = Tune::kSkeletonStrikeEveryMs;
        _pollMs = 0;
        _pickMs = 0;
    }

    // Nothing on the living side reaches a walker.
    bool CanAIAttack(Unit const* who) const override
    {
        return !IsWalker(who);
    }

    // Its threat list ran dry (the husk went, its target died): a new target while he fights, else it goes.
    void EnterEvadeMode(EvadeReason why) override
    {
        if (Pick(false))
            return;
        ScriptedAI::EnterEvadeMode(why);
        me->DespawnOrUnsummon();
    }

    void JustDied(Unit* /*killer*/) override
    {
        if (boss_zumrah_rework* boss = Boss())
            boss->SkeletonGone(me->GetGUID());
    }

    void UpdateAI(uint32 diff) override
    {
        _pollMs += diff;
        if (_pollMs >= kSkeletonPollMs)
        {
            _pollMs = 0;
            boss_zumrah_rework* boss = Boss();
            if (!boss || !boss->Engaged())
            {
                me->DespawnOrUnsummon();
                return;
            }
        }
        if (!UpdateVictim())
        {
            _pickMs += diff;
            if (_pickMs >= kSkeletonPollMs)
            {
                _pickMs = 0;
                Pick(false);
            }
            return;
        }
        if (_strikeMs > diff)
        {
            _strikeMs -= diff;
            return;
        }
        Unit* victim = me->GetVictim();
        if (!victim || !me->IsWithinMeleeRange(victim))
            return;
        _strikeMs = Tune::kSkeletonStrikeEveryMs;
        Strike(victim);
    }

private:
    boss_zumrah_rework* Boss() const
    {
        Creature* boss = _boss ? ObjectAccessor::GetCreature(*me, _boss) : nullptr;
        return boss && boss->IsAIEnabled ? dynamic_cast<boss_zumrah_rework*>(boss->AI()) : nullptr;
    }

    // The husk if one stands (rising during a walk), else his tank, else the nearest player on the bowl (rule 19).
    bool Pick(bool rising)
    {
        boss_zumrah_rework* boss = Boss();
        if (!boss || !boss->Engaged())
            return false;
        Creature* husk = boss->Husk() ? ObjectAccessor::GetCreature(*me, boss->Husk()) : nullptr;
        if (rising && husk && husk->IsAlive())
        {
            me->GetThreatMgr().AddThreat(husk, Tune::kVesselThreat);
            AttackStart(husk);
            LogZr("skeleton", Acore::StringFormat("target=husk walker={}", boss->Walker().ToString()));
            return true;
        }
        Unit* tank = boss->Self()->GetVictim();
        Player* target = tank ? tank->ToPlayer() : nullptr;
        if (!CountsAsPlayer(target) || IsWalker(target) || !BowlArena().Contains({ target->GetPositionX(),
            target->GetPositionY() }, target->GetPositionZ()))
        {
            target = nullptr;
            float best = 0.f;
            for (MapReference const& ref : me->GetMap()->GetPlayers())
            {
                Player* p = ref.GetSource();
                if (!CountsAsPlayer(p) || IsWalker(p)
                    || !BowlArena().Contains({ p->GetPositionX(), p->GetPositionY() }, p->GetPositionZ()))
                    continue;
                float const d = me->GetExactDist2d(p);
                if (!target || d < best)
                {
                    target = p;
                    best = d;
                }
            }
        }
        if (!target)
            return false;
        AttackStart(target);
        if (rising)
            LogZr("skeleton", Acore::StringFormat("target={}", target->GetName()));
        return true;
    }

    // A hit every 2 s: 3% (heroic 5%) of the reference row of whoever takes it. On the husk, the walker takes it.
    void Strike(Unit* victim)
    {
        boss_zumrah_rework* boss = Boss();
        if (!boss)
            return;
        Unit* takes = victim;
        if (victim->GetEntry() == NPC_ZF_EMPTY_VESSEL)
        {
            Player* walker = boss->Walker() ? ObjectAccessor::GetPlayer(*me, boss->Walker()) : nullptr;
            if (!CountsAsPlayer(walker))
                return;
            takes = walker;
        }
        CastSpellExtraArgs args(TRIGGERED_FULL_MASK);
        args.AddSpellBP0(static_cast<int32>(DungeonKit::RefFlatOn(boss->Self(), takes,
            SkeletonStrikePct(_heroic))));
        me->HandleEmoteCommand(EMOTE_ONESHOT_ATTACK1H);
        me->CastSpell(takes, SPELL_ZR_SKELETAL_STRIKE, args);
    }

    ObjectGuid _boss;
    uint32 _strikeMs = Tune::kSkeletonStrikeEveryMs;
    uint32 _pollMs = 0;
    uint32 _pickMs = 0;
    bool _heroic = false;
};

// Empty Vessel 301010: the walker's body (their look, aura 247). Never moves, never dies: damage to it goes to the
// walker (the Skeletons strike the walker directly; anything else is passed on here, in the next tick).
struct npc_zf_empty_vessel : public NullCreatureAI
{
    explicit npc_zf_empty_vessel(Creature* creature) : NullCreatureAI(creature)
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void SetGUID(ObjectGuid const& guid, int32 id) override
    {
        if (id == kHuskWalkerGuid)
            _walker = guid;
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask school) override
    {
        if (!damage)
            return;
        _debt += damage;
        _debtSchool = school;
        if (attacker)
            _debtFrom = attacker->GetGUID();
        damage = 0;
    }

    void UpdateAI(uint32 /*diff*/) override
    {
        if (!_debt)
            return;
        uint32 const share = _debt;
        _debt = 0;
        Player* walker = _walker ? ObjectAccessor::GetPlayer(*me, _walker) : nullptr;
        if (!CountsAsPlayer(walker) || !walker->IsInMap(me))
            return;
        Unit* from = _debtFrom ? ObjectAccessor::GetUnit(*me, _debtFrom) : nullptr;
        Unit::DealDamage(from && from->IsAlive() ? from : nullptr, walker, share, nullptr, DIRECT_DAMAGE, _debtSchool,
            nullptr, false);
    }

private:
    ObjectGuid _walker;
    ObjectGuid _debtFrom;
    uint32 _debt = 0;
    SpellSchoolMask _debtSchool = SPELL_SCHOOL_MASK_NORMAL;
};

// Lost Soul 301011: a wisp in the spirit world (type 11), moved, judged and removed by the boss's CrawlPickups.
struct npc_zf_lost_soul : public NullCreatureAI
{
    explicit npc_zf_lost_soul(Creature* creature) : NullCreatureAI(creature) { }

    void IsSummonedBy(WorldObject* /*summoner*/) override
    {
        me->CastSpell(me, SPELL_ZR_SPIRIT_WORLD, true);
        me->CastSpell(me, SPELL_ZR_LOST_SOUL, true);
    }
};

// Bound Dead 301012: a troll spirit at his feet, in the spirit world; the boss binds, frees and removes it.
struct npc_zf_bound_dead : public NullCreatureAI
{
    explicit npc_zf_bound_dead(Creature* creature) : NullCreatureAI(creature) { }
};

// The grave stalker 301013: a look where a circle lands (the graves in the spirit world, the echoes in ours).
struct npc_zf_grave_stalker : public NullCreatureAI
{
    explicit npc_zf_grave_stalker(Creature* creature) : NullCreatureAI(creature) { }
};

namespace
{
    boss_zumrah_rework* FindZumrahAI(ChatHandler* handler)
    {
        Creature* boss = ZfTest::FindBoss(handler, NPC_ZUMRAH);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_zumrah_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Zum'rah is not running boss_zumrah_rework (check the ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_zumrah_rework::TestMechanic mechanic, char const* what, uint32 n = 0)
    {
        boss_zumrah_rework* ai = FindZumrahAI(handler);
        if (!ai)
            return false;
        Player* who = handler->GetSession() ? handler->getSelectedPlayerOrSelf() : nullptr;
        std::string const error = ai->TestFire(mechanic, who, n);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Zum'rah: {} fired.", what);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return ZfTest::ShowBossInfo(handler, NPC_ZUMRAH, BOSS_ZUMRAH);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_zumrah_rework* ai = FindZumrahAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Zum'rah: {}", ai->TestState());
        return true;
    }

    bool HandleRend(ChatHandler* handler)
    {
        return Fire(handler, boss_zumrah_rework::TestMechanic::Rend,
            "a walk (ZR1-ZR3: the selected player at once, else his Spirit Rend on the next in turn)");
    }

    bool HandleEndWalk(ChatHandler* handler)
    {
        return Fire(handler, boss_zumrah_rework::TestMechanic::EndWalk, "the walk's end (the walker snaps back)");
    }

    bool HandleSoul(ChatHandler* handler, Optional<uint32> count)
    {
        return Fire(handler, boss_zumrah_rework::TestMechanic::Soul, "Lost Souls (ZR4, from random graves)",
            count.value_or(1));
    }

    bool HandleBind(ChatHandler* handler, Optional<uint32> count)
    {
        return Fire(handler, boss_zumrah_rework::TestMechanic::Bind, "souls bound at the cauldron (ZR6)",
            count.value_or(1));
    }

    bool HandleFreeAll(ChatHandler* handler)
    {
        return Fire(handler, boss_zumrah_rework::TestMechanic::FreeAll, "every Bound Dead freed");
    }

    bool HandleWard(ChatHandler* handler)
    {
        return Fire(handler, boss_zumrah_rework::TestMechanic::Ward, "Ward of Zum'rah (ZR8)");
    }

    bool HandleVolley(ChatHandler* handler)
    {
        return Fire(handler, boss_zumrah_rework::TestMechanic::Volley, "Shadow Bolt Volley (ZR9, kickable)");
    }

    bool HandleBolt(ChatHandler* handler)
    {
        return Fire(handler, boss_zumrah_rework::TestMechanic::Bolt,
            "Shadow Bolt (ZR10: the selected player, else his target)");
    }

    bool HandleEcho(ChatHandler* handler)
    {
        return Fire(handler, boss_zumrah_rework::TestMechanic::Echo,
            "a Soul Echo (ZR12: under the selected player, else random; any difficulty)");
    }

    bool HandleWail(ChatHandler* handler)
    {
        return Fire(handler, boss_zumrah_rework::TestMechanic::Wail, "a Restless Wail on the walker (ZR13)");
    }

    bool HandleGraves(ChatHandler* handler)
    {
        return Fire(handler, boss_zumrah_rework::TestMechanic::Graves, "Grasping Graves round the walker (ZR14)");
    }

    // `.dbtest zf zumrah <sub>`: the numbers are the map's difficulty.
    ChatCommandTable const& ZumrahTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",    HandleInfo,    SEC_GAMEMASTER, Console::No },
            { "state",   HandleState,   SEC_GAMEMASTER, Console::No },
            { "rend",    HandleRend,    SEC_GAMEMASTER, Console::No },
            { "endwalk", HandleEndWalk, SEC_GAMEMASTER, Console::No },
            { "soul",    HandleSoul,    SEC_GAMEMASTER, Console::No },
            { "bind",    HandleBind,    SEC_GAMEMASTER, Console::No },
            { "freeall", HandleFreeAll, SEC_GAMEMASTER, Console::No },
            { "ward",    HandleWard,    SEC_GAMEMASTER, Console::No },
            { "volley",  HandleVolley,  SEC_GAMEMASTER, Console::No },
            { "bolt",    HandleBolt,    SEC_GAMEMASTER, Console::No },
            { "echo",    HandleEcho,    SEC_GAMEMASTER, Console::No },
            { "wail",    HandleWail,    SEC_GAMEMASTER, Console::No },
            { "graves",  HandleGraves,  SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_zumrah_rework()
{
    RegisterDungeonReworkCreatureAI(boss_zumrah_rework, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_zf_zumrah_skeleton, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_zf_empty_vessel, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_zf_lost_soul, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_zf_bound_dead, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_zf_grave_stalker, ZulFarrakRework::kInstanceScriptName);
    ZfTest::RegisterBoss("zumrah", ZumrahTestCommands());
}
