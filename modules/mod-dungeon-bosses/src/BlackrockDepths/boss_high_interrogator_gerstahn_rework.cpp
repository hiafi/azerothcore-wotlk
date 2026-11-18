/*
 * mod-dungeon-bosses, Blackrock Depths D1: High Interrogator Gerstahn (9018), "Everyone talks eventually". Build spec:
 * docs/dungeons/blackrock-depths-1-detention-block.md "High Interrogator Gerstahn" (S1 45-228, GE1-GE7, rulings 9-12
 * and 88), handoff section 3.4 rows D1, 3.5 row D1, 3.6, 3.8 (her hall). Replaces the stock
 * boss_high_interrogator_gerstahn (still registered, unbound by apps/dbc-tools source/npcs/blackrock_depths/
 * gerstahn.py); Mana Burn 14033 and Psychic Scream 13704 are retired. Pure rules: GerstahnLogic.h.
 *
 *   GE1 Doubt        a stacking debuff on players, no duration, not dispellable. At 4 the swirl shows; at 5 the player
 *       Broken       breaks: Broken (2 s fear) and Dread (30% / heroic 40% Shadow over 10 s), Doubt back to 0, and
 *       Knowledge    she gains a stack of Knowledge (+10% damage, 5 at most on normal, no cap on heroic; yell line 1)
 *   GE2 Shadow Word: random player, the tank included, at 4 s then every 8 s (heroic 6 s); 2% (3%) a 3 s tick for
 *       Pain         18 s; a Doubt every 6 s (heroic every 3 s). A Magic dispel clears all of that player's Doubt
 *                    (heroic: and leaves GE6 where they stood)
 *   GE3 Mind Flay    at 8 s then every 12 s (heroic 10 s) on the player with the most Doubt (random on a tie), the tank
 *                    included: a 3 s interruptible channel, 3 ticks of 6% (8%) and a Doubt each. A kick or a silence
 *                    clears all of the target's Doubt
 *   GE4 Interrogation at 15 s then every 25 s (heroic 20 s): a 2.5 s cast bar (emote line 2) and a 10 yd ring at her;
 *       Circle       inside when it lands: 15% (25%) Shadow and 3 Doubt, the tank included (ruling 88)
 *   GE5 Mind Sear    at 20 s then every 20 s (heroic 15 s), never during a GE4 cast: 5 s on a random non-tank who is
 *                    not the Mind Flay target (emote line 3); every second everyone else within 8 yd of them takes 3%
 *                    (5%) Shadow and 1 Doubt. A registry RunOut tells the bots; the script ticks
 *   GE6 Lingering    heroic: a 5 yd pool for 8 s where a dispelled Shadow Word: Pain's player stood; each second
 *       Doubt        inside adds a Doubt (a telegraph-only persistent Zone; the script reads who is inside)
 *   GE7 Shadow Shield at 8 s then every 25 s on herself: absorbs about 4,000 (6,500), a small Shadow hit on melee
 *                    attackers; Magic, a purge is a reward
 *
 * Doubt replaces Weakened on every mechanic (ruling 11). Her spells ignore caster modifiers (rule 2): Knowledge
 * raises her melee through its aura and her spells through the scripts here (the registry percent at registration,
 * the DoTs and the sear tick through GerstahnLogic.h ScaledPct). Boss data: no kill order; Mind Flay on the interrupt
 * list; Shadow Word: Pain on the dispel list, the player with the most Doubt first (BM DispelEntry::MostStacksFirst);
 * Shadow Shield on the purge list. Every timer runs on the AI's own clock. Every firing logs one INFO line
 * "brd gerstahn <mechanic> ..." (module.dungeonbosses); `.dbtest brd gerstahn ...` fires one mechanic on demand.
 */

#include "ArenaGuard.h"
#include "BlackrockDepthsKit.h"
#include "BlackrockDepthsRework.h"
#include "BlackrockDepthsTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "GerstahnLogic.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ThreatManager.h"
#include <functional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdGerstahn;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "gerstahn";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // A player the fight acts on: in the world, alive, not a game master.
    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    // The generic stalker 300796 (the pool's look) is the orchestrator's template: without it the look is skipped,
    // never an error line per pool (the registry's ring is the telegraph either way).
    bool StalkerExists()
    {
        return sObjectMgr->GetCreatureTemplate(NPC_BRD_STALKER) != nullptr;
    }
}

// High Interrogator Gerstahn 9018
struct boss_high_interrogator_gerstahn_rework : public BossAI
{
    explicit boss_high_interrogator_gerstahn_rework(Creature* creature)
        : BossAI(creature, BOSS_GERSTAHN), _arena(GerstahnArena(), LeashOptions(kBossLogName)) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

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

        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        _heroic = IsHeroicMap(me);
        OnBossPull(me, kBossLogName);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_GERSTAHN;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        Talk(SAY_PULL);

        _painClock.Start(_clockMs, kPainBeat(_heroic).firstMs);
        _flayClock.Start(_clockMs, kFlayBeat(_heroic).firstMs);
        _circleClock.Start(_clockMs, kCircleBeat(_heroic).firstMs);
        _searClock.Start(_clockMs, kSearBeat(_heroic).firstMs);
        _shieldClock.Start(_clockMs, kShieldBeat(_heroic).firstMs);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f})", _heroic ? 1 : 0, me->GetPositionX(),
                me->GetPositionY(), me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        Talk(SAY_DEATH);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("breaks={} knowledge={} kicks={} dispels={} pools={} killer={}", _breaks, Knowledge(),
                _kicks, _dispels, _pools, killer ? killer->GetName() : "none"));
        Cleanup();
    }

    // Stalkers are her summons (they go with her reset and death) but never zone into her fight.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    // GE3: a kick or a silence stopped Mind Flay: the target's Doubt is cleared. Her own stops (an evade, her death, a
    // reset) are not interrupts: Cleanup drops the channel's state before the engine interrupts it.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (spell && spell->Id == SPELL_GE_MIND_FLAY && _flay.active)
            FlayInterrupted();
    }

    void OnChannelFinished(SpellInfo const* spell) override
    {
        BossAI::OnChannelFinished(spell);
        if (spell && spell->Id == SPELL_GE_MIND_FLAY && _flay.active)
            FlayEnded("done");
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off her arena, or nobody on it for 10 s: evading

        UpdateSear();
        UpdateFlay();
        UpdateBeats();
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The beats
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateBeats()
    {
        // The instants are triggered: they never wait for a cast and never break the Mind Flay channel.
        if (_painClock.Due(_clockMs))
        {
            _painClock.Fired(_clockMs, kPainBeat(_heroic).everyMs);
            CastPain(nullptr);
        }
        if (_shieldClock.Due(_clockMs))
        {
            _shieldClock.Fired(_clockMs, kShieldBeat(_heroic).everyMs);
            CastShield();
        }
        // Mind Sear is a triggered aura on its target, not her channel: only the Circle's cast holds it (S1 GE5).
        if (_searClock.Due(_clockMs) && !CircleCasting())
        {
            _searClock.Fired(_clockMs, kSearBeat(_heroic).everyMs);
            StartMindSear(nullptr);
        }
        // The Circle's bar and the Mind Flay channel wait for each other (and for any cast in progress): a new cast
        // would break the channel, and that must never read as a kick.
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (_circleClock.Due(_clockMs))
        {
            _circleClock.Fired(_clockMs, kCircleBeat(_heroic).everyMs);
            StartCircle();
        }
        else if (_flayClock.Due(_clockMs))
        {
            if (StartMindFlay(nullptr))
                _flayClock.Fired(_clockMs, kFlayBeat(_heroic).everyMs);
            else
                _flayClock.Start(_clockMs, kFlayRetryMs);    // a school lockout or nobody in reach: try shortly
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GE1 Doubt, Broken, Knowledge
    // ----------------------------------------------------------------------------------------------------------------

    uint32 Knowledge() const
    {
        return DungeonKit::Stacks(me, SPELL_GE_KNOWLEDGE);
    }

    // `add` Doubt on `player` from `source` (the log's word): a break at 5.
    void GiveDoubt(Player* player, uint32 add, char const* source)
    {
        if (!CountsAsPlayer(player) || !add || !me->IsAlive())
            return;
        uint32 const current = DungeonKit::Stacks(player, SPELL_GE_DOUBT);
        DoubtStep const step = BrdGerstahn::AddDoubt(current, add);
        if (step.broke)
        {
            Break(player, current, source);
            return;
        }
        DungeonKit::AddStacks(player, SPELL_GE_DOUBT, static_cast<int32>(step.stacks) - static_cast<int32>(current),
            me, kDoubtBreakAt);
        SetSwirl(player, step.stacks);
    }

    // The player breaks: Doubt to 0, a 2 s fear, Dread (at her Knowledge before this break), and her Knowledge + 1.
    void Break(Player* player, uint32 from, char const* source)
    {
        player->RemoveAurasDueToSpell(SPELL_GE_DOUBT);
        SetSwirl(player, 0);
        me->CastSpell(player, SPELL_GE_BROKEN, true);
        me->CastSpell(player, SPELL_GE_DREAD, true);
        uint32 const before = Knowledge();
        uint32 const after = KnowledgeAfterBreak(before, _heroic);
        if (after > before)
            DungeonKit::AddStacks(me, SPELL_GE_KNOWLEDGE, static_cast<int32>(after - before), me,
                KnowledgeStackLimit(_heroic));
        ++_breaks;
        if (!_yelledBreak || _clockMs >= _lastBreakYellMs + kBreakYellGapMs)
        {
            Talk(SAY_BREAK);
            _yelledBreak = true;
            _lastBreakYellMs = _clockMs;
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "break",
            Acore::StringFormat("player={} source={} from={} knowledge={} breaks={}", player->GetName(), source, from,
                Knowledge(), _breaks));
    }

    // All of `player`'s Doubt goes (a kicked Mind Flay, a dispelled Shadow Word: Pain).
    void ClearDoubt(Unit* unit, char const* why)
    {
        Player* player = unit ? unit->ToPlayer() : nullptr;
        if (!player)
            return;
        uint32 const had = DungeonKit::Stacks(player, SPELL_GE_DOUBT);
        player->RemoveAurasDueToSpell(SPELL_GE_DOUBT);
        SetSwirl(player, 0);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "clear",
            Acore::StringFormat("why={} player={} doubt={}", why, player->GetName(), had));
    }

    // The high-Doubt swirl (gap 6) on at 4, off below.
    void SetSwirl(Player* player, uint32 stacks)
    {
        bool const want = SwirlOn(stacks);
        bool const has = player->HasAura(SPELL_GE_DOUBT_SWIRL);
        if (want && !has)
            me->AddAura(SPELL_GE_DOUBT_SWIRL, player);
        else if (!want && has)
            player->RemoveAurasDueToSpell(SPELL_GE_DOUBT_SWIRL);
    }

    // A tick of one of her periodic spells on `target` (spell_brd_gerstahn_periodic): Shadow Word: Pain and Mind Flay
    // add Doubt.
    void OnPeriodicTick(uint32 spellId, Unit* target, uint32 tick)
    {
        Player* player = target ? target->ToPlayer() : nullptr;
        if (!player || !me->IsEngaged())
            return;
        if (spellId == SPELL_GE_SHADOW_WORD_PAIN && PainTickAddsDoubt(tick, _heroic))
            GiveDoubt(player, 1, "pain");
        else if (spellId == SPELL_GE_MIND_FLAY)
        {
            if (_flay.active && _flay.target == player->GetGUID())
                ++_flay.ticks;
            GiveDoubt(player, kFlayDoubtPerTick, "flay");
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GE2 Shadow Word: Pain
    // ----------------------------------------------------------------------------------------------------------------

    void CastPain(Player* forced)
    {
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = false;   // the tank included (S1 GE2)
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!target)
            return;
        me->CastSpell(target, SPELL_GE_SHADOW_WORD_PAIN, true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "pain",
            Acore::StringFormat("target={} doubt={}", target->GetName(), DungeonKit::Stacks(target, SPELL_GE_DOUBT)));
    }

    // A Magic dispel took Shadow Word: Pain off `target` (spell_brd_gerstahn_shadow_word_pain): their Doubt is
    // cleared; on heroic a Lingering Doubt pool stays where they stood.
    void OnPainDispelled(Unit* target)
    {
        if (!target || !me->IsAlive() || !me->IsEngaged())
            return;
        ++_dispels;
        Position const at = target->GetPosition();
        ClearDoubt(target, "dispel");
        if (_heroic)
            SpawnPool(at);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GE3 Mind Flay
    // ----------------------------------------------------------------------------------------------------------------

    // The player with the most Doubt on her threat list, random on a tie, the tank included.
    Player* PickFlayPlayer() const
    {
        std::vector<Player*> const players = FightPlayers();
        std::vector<FlayCandidate> candidates;
        candidates.reserve(players.size());
        for (Player* player : players)
            candidates.push_back({ player->GetGUID().GetRawValue(), DungeonKit::Stacks(player, SPELL_GE_DOUBT) });
        std::optional<std::size_t> const pick = PickFlayTarget(candidates,
            [](uint32 n) { return n ? urand(0, n - 1) : 0u; });
        return pick ? players[*pick] : nullptr;
    }

    bool StartMindFlay(Player* forced)
    {
        Player* target = forced ? forced : PickFlayPlayer();
        if (!target)
            return false;
        uint32 const doubt = DungeonKit::Stacks(target, SPELL_GE_DOUBT);
        // The channel's interrupt flag 0x08 is the move bit: a spline step taken after the cast (she was chasing)
        // would end it and count as a kick. Stopping first, before the channel adds the bit, is harmless.
        me->StopMoving();
        SpellCastResult const result = me->CastSpell(target, SPELL_GE_MIND_FLAY, false);
        if (result != SPELL_CAST_OK)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "flay-failed",
                Acore::StringFormat("target={} result={}", target->GetName(), static_cast<uint32>(result)));
            return false;
        }
        _flay = FlayState();
        _flay.active = true;
        _flay.target = target->GetGUID();
        _flay.startedMs = _clockMs;
        Mechanic::NoteNextCastIn(me, SPELL_GE_MIND_FLAY, Ms(kFlayBeat(_heroic).everyMs));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "flay",
            Acore::StringFormat("target={} doubt={} tank={}", target->GetName(), doubt,
                target == me->GetVictim() ? 1 : 0));
        return true;
    }

    // The channel ended without a hook (its target died or left): the state goes.
    void UpdateFlay()
    {
        if (!_flay.active || me->FindCurrentSpellBySpellId(SPELL_GE_MIND_FLAY))
            return;
        if (_clockMs < _flay.startedMs + kFlayStartGraceMs)
            return;     // the channel has not taken yet
        FlayEnded("gone");
    }

    void FlayInterrupted()
    {
        ObjectGuid const targetGuid = _flay.target;
        uint32 const ticks = _flay.ticks;
        _flay = FlayState();
        if (!me->IsAlive() || !me->IsEngaged())
            return;
        ++_kicks;
        Player* target = ObjectAccessor::GetPlayer(*me, targetGuid);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "flay-interrupted",
            Acore::StringFormat("target={} ticks={}", target ? target->GetName() : "gone", ticks));
        if (target)
            ClearDoubt(target, "interrupt");
    }

    void FlayEnded(char const* how)
    {
        uint32 const ticks = _flay.ticks;
        _flay = FlayState();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "flay-end", Acore::StringFormat("how={} ticks={}", how,
            ticks));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GE4 Interrogation Circle
    // ----------------------------------------------------------------------------------------------------------------

    bool CircleCasting() const
    {
        return _circleEndMs && _clockMs < _circleEndMs;
    }

    void StartCircle()
    {
        DungeonKit::CastBar(me, SPELL_GE_CIRCLE_CAST, nullptr, EMOTE_CIRCLE);
        float const pct = ScaledPct(SPELL_GE_CIRCLE, _heroic, Knowledge());
        MechanicRef ref = Mechanic::Circle(me, me, kCircleRadius, Ms(kCircleCastMs));
        ref.Damage(pct).TankDamage(pct).Spell(SPELL_GE_CIRCLE).Tag(TAG_GE_CIRCLE);
        ref.OnHit(OnGerstahnHit([](boss_high_interrogator_gerstahn_rework& ai, Unit* hit)
        {
            if (Player* player = hit ? hit->ToPlayer() : nullptr)
                ai.GiveDoubt(player, kCircleDoubt, "circle");
        }));
        Track(ref.Handle());
        _circleEndMs = _clockMs + kCircleCastMs;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "circle",
            Acore::StringFormat("pct={:.1f} radius={:.0f} knowledge={}", pct, kCircleRadius, Knowledge()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GE5 Mind Sear
    // ----------------------------------------------------------------------------------------------------------------

    bool StartMindSear(Player* forced)
    {
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.tankIfAlone = true;
            if (_flay.active)
                rule.exclude.push_back(_flay.target.GetRawValue());
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!target)
            return false;
        if (_sear.active)
            EndSear("replaced");
        me->CastSpell(target, SPELL_GE_MIND_SEAR, true);
        Talk(EMOTE_MIND_SEAR, target);
        // Telegraph only (the script ticks): everyone else keeps 8 yd from the target for the whole sear.
        MechanicRef ref = Mechanic::RunOut(me, target, kSearRadius, Ms(kSearMs));
        ref.Tag(TAG_GE_MIND_SEAR);
        _sear = SearState();
        _sear.active = true;
        _sear.target = target->GetGUID();
        _sear.startedMs = _clockMs;
        _sear.handle = ref.Handle();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "sear",
            Acore::StringFormat("target={} flay-target-excluded={}", target->GetName(), _flay.active ? 1 : 0));
        return true;
    }

    void UpdateSear()
    {
        if (!_sear.active)
            return;
        Player* target = ObjectAccessor::GetPlayer(*me, _sear.target);
        if (!CountsAsPlayer(target))
        {
            EndSear("target-gone");
            return;
        }
        while (_sear.ticks < kSearTicks && _clockMs >= _sear.startedMs + (_sear.ticks + 1) * kSearTickMs)
        {
            ++_sear.ticks;
            SearTick(target);
        }
        if (_sear.ticks >= kSearTicks)
            EndSear("done");
    }

    // Every other player of the fight within 8 yd of the target: the tick (Shadow) and 1 Doubt. Never the target.
    void SearTick(Player* target)
    {
        for (Player* player : FightPlayers())
        {
            if (player == target)
                continue;
            if (!InSear(player->GetExactDist2d(target), player->GetPositionZ() - target->GetPositionZ()))
                continue;
            me->CastSpell(player, SPELL_GE_MIND_SEAR_TICK, true);
            GiveDoubt(player, kSearDoubtPerTick, "sear");
            ++_sear.hits;
        }
    }

    void EndSear(char const* how)
    {
        if (!_sear.active)
            return;
        SearState const sear = _sear;
        _sear = SearState();
        if (sear.handle)
            Mechanic::Cancel(me, sear.handle);
        if (Player* target = ObjectAccessor::GetPlayer(*me, sear.target))
            target->RemoveAurasDueToSpell(SPELL_GE_MIND_SEAR, me->GetGUID());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "sear-end",
            Acore::StringFormat("how={} ticks={} hits={}", how, sear.ticks, sear.hits));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GE6 Lingering Doubt (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    // A 5 yd pool at `at` for 8 s: a telegraph-only persistent Zone whose every pass (1 s) lists who is inside; each of
    // them takes a Doubt. The look is a stalker carrying the shadow pool state.
    void SpawnPool(Position const& at)
    {
        MechanicRef ref = Mechanic::Circle(me, at, kPoolRadius, Ms(kPoolWarnMs));
        ref.Persistent(Ms(kPoolMs - kPoolWarnMs), Ms(kPoolTickMs)).Tag(TAG_GE_LINGERING);
        ref.OnResolve(OnGerstahn([](boss_high_interrogator_gerstahn_rework& ai,
            BossMechanics::ResolveResult const& result)
        {
            ai.PoolPass(result);
        }));
        Track(ref.Handle());
        if (StalkerExists())
            if (TempSummon* stalker = me->SummonCreature(NPC_BRD_STALKER, at, TEMPSUMMON_TIMED_DESPAWN, kPoolMs))
                stalker->CastSpell(stalker, SPELL_GE_LINGERING_DOUBT, true);
        ++_pools;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "pool",
            Acore::StringFormat("at=({:.1f}, {:.1f}, {:.1f}) pools={}", at.GetPositionX(), at.GetPositionY(),
                at.GetPositionZ(), _pools));
    }

    void PoolPass(BossMechanics::ResolveResult const& result)
    {
        for (ObjectGuid const& guid : result.hits)
            if (Player* player = ObjectAccessor::GetPlayer(*me, guid))
                GiveDoubt(player, kPoolDoubtPerTick, "pool");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GE7 Shadow Shield
    // ----------------------------------------------------------------------------------------------------------------

    void CastShield()
    {
        me->CastSpell(me, ShieldSpell(_heroic), true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "shield",
            Acore::StringFormat("absorb={}", kShieldAbsorb(_heroic)));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (S1 "Bots")
    // ----------------------------------------------------------------------------------------------------------------

    // No kill order. Mind Flay on the interrupt list (a reward on normal, expected on heroic); Shadow Word: Pain on the
    // dispel list, the player with the most Doubt first (DS's rank key); Shadow Shield on the purge list (a reward).
    void Describe()
    {
        BossMechanics::Descriptor d;
        d.interrupts.emplace_back(NPC_GERSTAHN, SPELL_GE_MIND_FLAY, 3, Ms(kFlayBeat(_heroic).everyMs));
        d.dispels.push_back(BossMechanics::DispelEntry(SPELL_GE_SHADOW_WORD_PAIN, 2).MostStacksFirst(SPELL_GE_DOUBT));
        d.purges.emplace_back(NPC_GERSTAHN, ShieldSpell(_heroic), 1);
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brd gerstahn` entry points (the numbers are the map's difficulty)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Pain,
        Flay,
        Circle,
        Sear,
        Shield,
        Pool,
        Doubt,
        Clear,
    };

    // An empty string when fired; otherwise why not. `who` is the GM's selected player (or the GM), `n` a count.
    std::string TestFire(TestMechanic mechanic, Player* who, uint32 n)
    {
        if (!me->IsEngaged())
            return "Gerstahn must be in combat (the picks read her threat list, the mechanics her encounter).";
        switch (mechanic)
        {
            case TestMechanic::Pain:
                CastPain(nullptr);
                break;
            case TestMechanic::Flay:
                if (me->HasUnitState(UNIT_STATE_CASTING))
                    return "She is casting already.";
                if (!StartMindFlay(nullptr))
                    return "Mind Flay did not start (see the log).";
                break;
            case TestMechanic::Circle:
                if (me->HasUnitState(UNIT_STATE_CASTING))
                    return "She is casting already.";
                StartCircle();
                break;
            case TestMechanic::Sear:
                if (!StartMindSear(nullptr))
                    return "Nobody to sear.";
                break;
            case TestMechanic::Shield:
                CastShield();
                break;
            case TestMechanic::Pool:
                if (!who)
                    return "No player to put a pool under.";
                SpawnPool(who->GetPosition());
                break;
            case TestMechanic::Doubt:
                if (!CountsAsPlayer(who))
                    return "No living player without GM mode selected (`.gm off`).";
                GiveDoubt(who, n ? n : 1, "test");
                break;
            case TestMechanic::Clear:
                if (!who)
                    return "No player selected.";
                ClearDoubt(who, "test");
                break;
        }
        return {};
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s heroic={} knowledge={} breaks={} kicks={} dispels={} pools={} flay={} "
            "sear={} circle={} live={} summons={}", _clockMs / 1000, _heroic ? 1 : 0, Knowledge(), _breaks, _kicks,
            _dispels, _pools, _flay.active ? 1 : 0, _sear.active ? 1 : 0, CircleCasting() ? 1 : 0, _live.size(),
            summons.size());
    }

private:
    static constexpr uint32 kFlayRetryMs = 1000;

    struct FlayState
    {
        bool active = false;
        ObjectGuid target;
        uint64 startedMs = 0;
        uint32 ticks = 0;
    };

    struct SearState
    {
        bool active = false;
        ObjectGuid target;
        uint64 startedMs = 0;
        uint32 ticks = 0;
        uint32 hits = 0;
        MechanicHandle handle;
    };

    // The players on her threat list the fight acts on.
    std::vector<Player*> FightPlayers() const
    {
        std::vector<Player*> out;
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
        {
            Unit* unit = ref->GetVictim();
            Player* player = unit ? unit->ToPlayer() : nullptr;
            if (!CountsAsPlayer(player) || !player->IsInMap(me))
                continue;
            out.push_back(player);
        }
        return out;
    }

    // Runs `fn(ai, args...)` on this boss when the registry calls back, if she is still there. Captures the map and the
    // guid only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnGerstahn(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (boss_high_interrogator_gerstahn_rework* ai = From(map, guid))
                fn(*ai, result);
        };
    }

    template <typename Fn>
    std::function<void(Unit*)> OnGerstahnHit(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](Unit* hit)
        {
            if (boss_high_interrogator_gerstahn_rework* ai = From(map, guid))
                fn(*ai, hit);
        };
    }

    static boss_high_interrogator_gerstahn_rework* From(Map* map, ObjectGuid guid)
    {
        if (!map)
            return nullptr;
        Creature* boss = map->GetCreature(guid);
        if (!boss || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_high_interrogator_gerstahn_rework*>(boss->AI());
    }

    // A mechanic of the fight (the Circle, a sear's run-out, a pool): kept to cancel it on a reset.
    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 64)      // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 32);
    }

    // The pull's state: nothing registered, no stalker, no aura of hers on anyone, no stack on her (Reset, evade,
    // death, a new pull). The Mind Flay state goes first, so the engine's interrupt of her channel on an evade or her
    // death never reads as a kick.
    void Cleanup()
    {
        _flay = FlayState();
        if (_sear.handle)
            Mechanic::Cancel(me, _sear.handle);
        _sear = SearState();
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        summons.DespawnAll();
        _clockMs = 0;
        _circleEndMs = 0;
        _painClock.Stop();
        _flayClock.Stop();
        _circleClock.Stop();
        _searClock.Stop();
        _shieldClock.Stop();
        _breaks = 0;
        _kicks = 0;
        _dispels = 0;
        _pools = 0;
        _yelledBreak = false;
        _lastBreakYellMs = 0;
        _arena.Reset();
        for (uint32 const spell : { uint32(SPELL_GE_KNOWLEDGE), uint32(SPELL_GE_SHADOW_SHIELD),
            uint32(SPELL_GE_SHADOW_SHIELD_H) })
            me->RemoveAurasDueToSpell(spell);
        if (instance)
            for (uint32 const spell : { uint32(SPELL_GE_DOUBT), uint32(SPELL_GE_DOUBT_SWIRL), uint32(SPELL_GE_BROKEN),
                uint32(SPELL_GE_DREAD), uint32(SPELL_GE_SHADOW_WORD_PAIN), uint32(SPELL_GE_MIND_FLAY),
                uint32(SPELL_GE_MIND_SEAR) })
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
    }

    DungeonKit::ArenaGuard _arena;
    BeatClock _painClock;
    BeatClock _flayClock;
    BeatClock _circleClock;
    BeatClock _searClock;
    BeatClock _shieldClock;
    FlayState _flay;
    SearState _sear;
    std::vector<MechanicHandle> _live;
    uint64 _clockMs = 0;            // ms since the reset: every timer of the fight
    uint64 _circleEndMs = 0;        // the Circle's bar ends (0: none)
    uint64 _lastBreakYellMs = 0;
    uint32 _breaks = 0;
    uint32 _kicks = 0;
    uint32 _dispels = 0;
    uint32 _pools = 0;
    bool _yelledBreak = false;
    bool _heroic = false;
};

namespace
{
    boss_high_interrogator_gerstahn_rework* GerstahnAIOf(Unit* unit)
    {
        Creature* boss = unit ? unit->ToCreature() : nullptr;
        if (!boss || !boss->IsAIEnabled || boss->GetEntry() != NPC_GERSTAHN)
            return nullptr;
        return dynamic_cast<boss_high_interrogator_gerstahn_rework*>(boss->AI());
    }

    boss_high_interrogator_gerstahn_rework* FindGerstahnAI(ChatHandler* handler)
    {
        Creature* boss = BrdTest::FindBoss(handler, NPC_GERSTAHN);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_high_interrogator_gerstahn_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Gerstahn is not running boss_high_interrogator_gerstahn_rework (check the "
                "ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_high_interrogator_gerstahn_rework::TestMechanic mechanic, char const* what,
        uint32 n = 0)
    {
        boss_high_interrogator_gerstahn_rework* ai = FindGerstahnAI(handler);
        if (!ai)
            return false;
        Player* who = handler->GetSession() ? handler->getSelectedPlayerOrSelf() : nullptr;
        std::string const error = ai->TestFire(mechanic, who, n);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Gerstahn: {} fired ({}).", what,
            ai->HeroicMap() ? "heroic numbers" : "normal numbers");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowBossInfo(handler, NPC_GERSTAHN, BOSS_GERSTAHN);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_high_interrogator_gerstahn_rework* ai = FindGerstahnAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Gerstahn: {}", ai->TestState());
        return true;
    }

    bool HandlePain(ChatHandler* handler)
    {
        return Fire(handler, boss_high_interrogator_gerstahn_rework::TestMechanic::Pain,
            "Shadow Word: Pain (GE2: a random player, Doubt on its ticks)");
    }

    bool HandleFlay(ChatHandler* handler)
    {
        return Fire(handler, boss_high_interrogator_gerstahn_rework::TestMechanic::Flay,
            "Mind Flay (GE3: the most Doubt; kick it to clear the target's Doubt)");
    }

    bool HandleCircle(ChatHandler* handler)
    {
        return Fire(handler, boss_high_interrogator_gerstahn_rework::TestMechanic::Circle,
            "Interrogation Circle (GE4: 2.5 s, then 10 yd around her, 3 Doubt)");
    }

    bool HandleSear(ChatHandler* handler)
    {
        return Fire(handler, boss_high_interrogator_gerstahn_rework::TestMechanic::Sear,
            "Mind Sear (GE5: 5 s, everyone else within 8 yd of the target)");
    }

    bool HandleShield(ChatHandler* handler)
    {
        return Fire(handler, boss_high_interrogator_gerstahn_rework::TestMechanic::Shield, "Shadow Shield (GE7)");
    }

    bool HandlePool(ChatHandler* handler)
    {
        return Fire(handler, boss_high_interrogator_gerstahn_rework::TestMechanic::Pool,
            "Lingering Doubt (GE6: a 5 yd pool under the selected player, any difficulty)");
    }

    bool HandleDoubt(ChatHandler* handler, Optional<uint32> count)
    {
        return Fire(handler, boss_high_interrogator_gerstahn_rework::TestMechanic::Doubt,
            "Doubt on the selected player (GE1: a break at 5)", count.value_or(1));
    }

    bool HandleClear(ChatHandler* handler)
    {
        return Fire(handler, boss_high_interrogator_gerstahn_rework::TestMechanic::Clear,
            "the selected player's Doubt cleared");
    }

    // `.dbtest brd gerstahn <sub>`: the numbers are the map's difficulty.
    ChatCommandTable const& BossHighInterrogatorGerstahnTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",   HandleInfo,   SEC_GAMEMASTER, Console::No },
            { "state",  HandleState,  SEC_GAMEMASTER, Console::No },
            { "pain",   HandlePain,   SEC_GAMEMASTER, Console::No },
            { "flay",   HandleFlay,   SEC_GAMEMASTER, Console::No },
            { "circle", HandleCircle, SEC_GAMEMASTER, Console::No },
            { "sear",   HandleSear,   SEC_GAMEMASTER, Console::No },
            { "shield", HandleShield, SEC_GAMEMASTER, Console::No },
            { "pool",   HandlePool,   SEC_GAMEMASTER, Console::No },
            { "doubt",  HandleDoubt,  SEC_GAMEMASTER, Console::No },
            { "clear",  HandleClear,  SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

// Her periodic spells (Shadow Word: Pain, Mind Flay, Dread): each tick is a percent of the reference row (the tank row
// on the tank) times her Knowledge at the cast (GerstahnLogic.h ScaledPct; the spells ignore caster modifiers), and
// a tick of Shadow Word: Pain or Mind Flay tells her AI (Doubt).
class spell_brd_gerstahn_periodic : public AuraScript
{
    PrepareAuraScript(spell_brd_gerstahn_periodic);

    void CalcAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        Unit* caster = GetCaster();
        Unit* owner = GetUnitOwner();
        Unit* source = caster ? caster : owner;
        if (!source)
            return;
        uint32 const knowledge = caster ? DungeonKit::Stacks(caster, SPELL_GE_KNOWLEDGE) : 0;
        float const pct = ScaledPct(GetId(), IsHeroicMap(source), knowledge);
        amount = static_cast<int32>(DungeonKit::RefFlatOn(source, owner, pct));
        canBeRecalculated = false;
    }

    void OnTick(AuraEffect const* aurEff)
    {
        if (boss_high_interrogator_gerstahn_rework* ai = GerstahnAIOf(GetCaster()))
            ai->OnPeriodicTick(GetId(), GetUnitOwner(), aurEff->GetTickNumber());
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_brd_gerstahn_periodic::CalcAmount, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_brd_gerstahn_periodic::OnTick, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE);
    }
};

// GE2: a Magic dispel of her Shadow Word: Pain clears that player's Doubt (heroic: and leaves a Lingering Doubt pool).
class spell_brd_gerstahn_shadow_word_pain : public AuraScript
{
    PrepareAuraScript(spell_brd_gerstahn_shadow_word_pain);

    void Dispelled(DispelInfo* /*dispelInfo*/)
    {
        if (boss_high_interrogator_gerstahn_rework* ai = GerstahnAIOf(GetCaster()))
            ai->OnPainDispelled(GetUnitOwner());
    }

    void Register() override
    {
        AfterDispel += AuraDispelFn(spell_brd_gerstahn_shadow_word_pain::Dispelled);
    }
};

// GE5: a Mind Sear tick, a percent of the reference row times her Knowledge, set at launch.
class spell_brd_gerstahn_damage : public SpellScript
{
    PrepareSpellScript(spell_brd_gerstahn_damage);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;
        float const pct = ScaledPct(GetSpellInfo()->Id, IsHeroicMap(caster),
            DungeonKit::Stacks(caster, SPELL_GE_KNOWLEDGE));
        SetEffectValue(static_cast<int32>(DungeonKit::RefFlatOn(caster, GetHitUnit(), pct)));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_brd_gerstahn_damage::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

void AddSC_boss_high_interrogator_gerstahn_rework()
{
    RegisterDungeonReworkCreatureAI(boss_high_interrogator_gerstahn_rework, BlackrockDepthsRework::kInstanceScriptName);
    RegisterSpellScript(spell_brd_gerstahn_periodic);
    RegisterSpellScript(spell_brd_gerstahn_shadow_word_pain);
    RegisterSpellScript(spell_brd_gerstahn_damage);
    BrdTest::RegisterBoss("gerstahn", BossHighInterrogatorGerstahnTestCommands());
}
