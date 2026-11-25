/*
 * mod-dungeon-bosses, Ragefire Chasm D2: Jergosh the Invoker (11518), normal and heroic. Build spec:
 * docs/dungeons/ragefire-chasm-rework.md "Jergosh the Invoker" (JR1-JR5, ruling 15); handoff sections 3.5 row D2, 3.6,
 * 3.8 (the hall), 3.10 (VR), 3.12, 7 #21, #29, #31-#36. Replaces SmartAI 11518 (dropped by S0's rev); bound by
 * apps/dbc-tools source/npcs/ragefire_chasm/jergosh.py. Pure rules: JergoshLogic.h; every number:
 * RagefireChasmRework.h namespace Jergosh.
 *
 *   JR1 Immolate        3 s, then every 3 s: a real 2 s Fire cast, kickable, on a random player (the tank included),
 *                       never one already burning; skipped while three burn (or everyone in the hall does). 56 and 16
 *                       a tick on normal, 5% and 5% a tick on heroic, 7 ticks of 3 s, not dispellable. A beat that
 *                       would run into Conflagrate is skipped. Unkicked, three burn at every Conflagrate
 *   JR2 Conflagrate     16 s, then every 20 s, always on time: emote line 1, a 2.5 s Arcane bar (never kicked, never
 *                       locked out: rule 25) and a registry Spread of 5 / 6 yd on everyone burning (SelfTrigger on
 *                       the Immolate aura: losing the burn in the middle drops that ring). At its end every burn is
 *                       consumed: the bearer 15% / 20% by script (no Weakened), anyone else in a ring 35% / 45% and
 *                       Weakened. Heroic (ruling 15): whoever another's ring hit then catches the same DoT, no cap
 *   JR3 pressure        his melee and the stock Curse of Weakness 18267 on his target, 1 s then every 30 s
 *   JR4 Drain Soul      heroic, 10 s, then every 20 s: a real 3 s Shadow channel, kickable, on a random player (the
 *                       tank included), emote line 2; completed (OnChannelFinished): Soul Tear, 25% Shadow to its
 *                       owner, and the wisp. A kick, the owner's death or an immunity: nothing
 *   JR5 The wisp        the kit's CrawlPickups: it appears 4 yd off its owner toward the offering spot and drifts
 *                       there at 3 yd/s; any living player within 2 yd sends it home (bots: one, healers last).
 *                       Eaten: emote line 3, the owner Soul-sick 30 s (if alive), a Tithe stack on him: +15% damage
 *                       dealt, no cap (ruling 15). The Tithe aura raises his melee; his own percent hits ignore
 *                       caster modifiers and are multiplied here (TitheFactor)
 *   Kicks               Immolate and Drain Soul: a kick's school lockout on him is 2 s, not the kick's own 4 to 8 s
 *                       (OnSpellFailed); a silence is left alone
 *   Boss data           Drain Soul (2) then Immolate (1) on the interrupt list; no dispels, no kill order
 *   Arena               JergoshArena() with LeashOptions (no grips). The Spread and the wisp's Soak set no `.Within`,
 *                       as in G1's drill (the claimer must be free to leave the group)
 *
 * Every timer runs on the AI's own clock (JergoshLogic.h Timeline), cast bar or not. Cleanup (a reset, an evade, his
 * death) takes back every ring, wisp, burn, Soul-sick, Tithe, his size and the offering patch. Every firing logs one
 * INFO line "rfc jergosh <mechanic> ..." (module.dungeonbosses); `.dbtest rfc jergosh <mechanic>` fires one.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitChase.h"
#include "InstanceScript.h"
#include "JergoshLogic.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "RagefireChasmKit.h"
#include "RagefireChasmRework.h"
#include "RagefireChasmTestCommand.h"
#include "ScriptedCreature.h"
#include "Spell.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ThreatManager.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace RagefireChasmRework;
using namespace RfcJergosh;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "jergosh";
    float constexpr kFloorBandYd = 4.f;

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    void LogJr(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, mechanic, detail);
    }

    // A player the fight acts on: in the world, alive, not a game master.
    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    // `p` on the hall's floor (a summon stands on it); the given height when the map has none near it (rule 33).
    Position OnFloor(WorldObject const* ref, Vec2 p, float z)
    {
        float const floor = ref->GetMapHeight(p.x, p.y, z + 3.f);
        bool const ok = floor > INVALID_HEIGHT + 1.f && std::fabs(floor - z) <= kFloorBandYd;
        return Position(p.x, p.y, ok ? floor : z, 0.f);
    }
}

// Jergosh the Invoker 11518
struct boss_jergosh_rework : public BossAI
{
    explicit boss_jergosh_rework(Creature* creature)
        : BossAI(creature, BOSS_JERGOSH), _arena(JergoshArena(), LeashOptions(kBossLogName)) { }

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
        _engaged = true;
        OnBossPull(me, kBossLogName);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_JERGOSH;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        Talk(YELL_JERGOSH_AGGRO);
        _timeline.Start(_heroic);
        if (_heroic)
            MarkOfferingSpot();
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        if (_engaged)
            LogJr("evade", Acore::StringFormat("reason={}", uint32(why)));
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        LogJr("death", Acore::StringFormat("clock={}s immolates={} conflagrates={} rings-hit={} relit={} drains={} "
            "torn={} caught={} tithe={} killer={}", _timeline.Now() / 1000, _counts.immolates, _counts.conflagrates,
            _counts.ringHits, _counts.relit, _counts.drains, _counts.torn, _counts.caught, Tithe(),
            killer ? killer->GetName() : "none"));
        Cleanup();
        BossAI::JustDied(killer);
    }

    // The wisps and the offering patch: never zoned into combat.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (!spell || !_engaged)
            return;
        switch (spell->Id)
        {
            case SPELL_JR_IMMOLATE:
                LogJr("immolate-stopped", ShortenKickLock(spell) ? "kicked" : "not kicked");
                break;
            case SPELL_JR_DRAIN_SOUL:
                ShortenKickLock(spell);
                EndDrain("stopped");
                break;
            case SPELL_JR_CONFLAGRATE_CAST:
                // Not interruptible: only a script or an engine stop. The rings go with the bar (rule 26); a bar that
                // has ended (its rings resolve in the same moment) stops nothing.
                if (_conflagrate.rings && _timeline.Now() + kBeatMarginMs < _conflagrate.endsAt)
                {
                    Mechanic::Cancel(me, _conflagrate.rings);
                    _conflagrate = ConflagrateState();
                    LogJr("conflagrate-stopped");
                }
                break;
            default:
                break;
        }
    }

    // A completed channel only (an interrupt never comes here).
    void OnChannelFinished(SpellInfo const* spell) override
    {
        BossAI::OnChannelFinished(spell);
        if (spell && spell->Id == SPELL_JR_DRAIN_SOUL && _engaged)
            SoulTorn();
    }

    void SpellHitTarget(Unit* target, SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_JR_IMMOLATE && target && _engaged && !_relighting)
            LogJr("immolate-lands", Acore::StringFormat("target={} burning={}", target->GetName(), Burning().size()));
    }

    void UpdateAI(uint32 diff) override
    {
        me->SetAssistanceTimer(0);      // section 7 #12 A: the flag stops the first call only
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_engaged)
            return;

        // The clock, the wisps and the channel's watch run on, cast bar or not.
        uint64 const before = _timeline.Now();
        if (_timeline.Advance(diff))
        {
            LogJr("immolate-skip", "conflagrate is due");
            NoteNext(Act::Immolate);
        }
        _wisps.Update(me, diff);
        WatchDrain();
        // Rings the registry no longer knows (they resolve with the bar's end).
        if (_conflagrate.rings && RingsLost(before, _conflagrate.endsAt))
            _conflagrate = ConflagrateState();
        if (!_engaged || !me->IsAlive() || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        // Nothing new starts between the bar's end and its burst.
        Act const act = _conflagrate.rings ? Act::None : _timeline.Next();
        if (act != Act::None)
        {
            if (Begin(act))
            {
                _timeline.Done(act);
                NoteNext(act);
            }
            else
                _timeline.Retry(act);
            if (me->HasUnitState(UNIT_STATE_CASTING))
                return;
        }
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest rfc jergosh` entry points (the numbers are the map's difficulty)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Immolate,
        Burn,
        BurnAll,
        Conflagrate,
        DrainSoul,
        Wisp,
        Tithe,
        Curse,
    };

    // An empty string when fired; otherwise why not. `who` is the GM's selected player (or the GM), `n` a count.
    std::string TestFire(TestMechanic mechanic, Player* who, uint32 n)
    {
        if (!_engaged || !me->IsEngaged())
            return "Jergosh must be in combat (the picks read his threat list, the mechanics his encounter).";
        Player* forced = CountsAsPlayer(who) ? who : nullptr;
        bool const casting = me->HasUnitState(UNIT_STATE_CASTING);
        switch (mechanic)
        {
            case TestMechanic::Immolate:
                if (casting)
                    return "He is casting already.";
                if (!CastImmolate(forced))
                    return "The engine refused it (a kick locked Fire?) or everyone burns.";
                break;
            case TestMechanic::Burn:
                if (!forced)
                    return "Select a living player that is not a game master.";
                Light(forced);
                break;
            case TestMechanic::BurnAll:
                for (Player* player : FightPlayers())
                    Light(player);
                break;
            case TestMechanic::Conflagrate:
                if (casting || _conflagrate.rings)
                    return "He is casting already.";
                StartConflagrate();
                break;
            case TestMechanic::DrainSoul:
                if (casting || _drain.active)
                    return "He is casting already.";
                if (!StartDrain(forced))
                    return "The engine refused it (a kick locked Shadow?) or nobody is there.";
                break;
            case TestMechanic::Wisp:
                if (!forced)
                    return "Select a living player that is not a game master.";
                SpawnWisp(forced->GetGUID(), forced->GetPosition());
                break;
            case TestMechanic::Tithe:
                SetTithe(n);
                break;
            case TestMechanic::Curse:
                if (!CastCurse())
                    return "The engine refused it (a kick locked Shadow?).";
                break;
        }
        return {};
    }

    std::string TestState()
    {
        return Acore::StringFormat("clock={}s heroic={} health={:.1f} burning={} wisps={} tithe={} (x{:.2f}) drain={} "
            "next: conflagrate {} ms, drain {} ms, immolate {} ms; relit={} caught={} torn={}",
            _timeline.Now() / 1000, _heroic ? 1 : 0, me->GetHealthPct(), Burning().size(), _wisps.Count(), Tithe(),
            TitheFactor(Tithe()), _drain.active ? 1 : 0, _timeline.In(Act::Conflagrate), _timeline.In(Act::DrainSoul),
            _timeline.In(Act::Immolate), _counts.relit, _counts.caught, _counts.torn);
    }

private:
    // ----------------------------------------------------------------------------------------------------------------
    // The beats
    // ----------------------------------------------------------------------------------------------------------------

    // False: refused by the engine (a lockout) or nobody to drain, tried again shortly. An Immolate with nobody to
    // light (three burn, or everyone) is a done beat.
    bool Begin(Act act)
    {
        switch (act)
        {
            case Act::Conflagrate:
                StartConflagrate();
                return true;
            case Act::DrainSoul:
                return StartDrain(nullptr);
            case Act::Immolate:
                return CastImmolate(nullptr);
            case Act::Curse:
                return CastCurse();
            case Act::None:
                break;
        }
        return true;
    }

    // The bots' overload hold reads when the kickable casts come next.
    void NoteNext(Act act)
    {
        if (act == Act::Immolate)
            Mechanic::NoteNextCastIn(me, SPELL_JR_IMMOLATE, Ms(_timeline.In(act)));
        else if (act == Act::DrainSoul)
            Mechanic::NoteNextCastIn(me, SPELL_JR_DRAIN_SOUL, Ms(_timeline.In(act)));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // JR1 Immolate
    // ----------------------------------------------------------------------------------------------------------------

    // Everyone who burns, on his threat list or not (a vanished rogue's burn bursts too, as the registry's ring does).
    std::vector<Player*> Burning() const
    {
        std::vector<Player*> out;
        for (MapReference const& ref : me->GetMap()->GetPlayers())
            if (Player* player = ref.GetSource())
                if (CountsAsPlayer(player) && player->HasAura(SPELL_JR_IMMOLATE, me->GetGUID()))
                    out.push_back(player);
        return out;
    }

    // A kick (Spell::EffectInterruptCast: a player's, a pet's, a creature's, a counterspell) locks the cast's school
    // and then interrupts the cast, which calls OnSpellFailed: the lock is there already and is cut to 2 s. Nothing
    // else that stops a cast (a silence, a stun, a death) locks a school, and he never starts a cast of a locked one:
    // no lock, nothing to cut, and the silence itself stays as long as it is.
    bool ShortenKickLock(SpellInfo const* spell)
    {
        SpellSchoolMask const school = spell->GetSchoolMask();
        if (!me->IsSpellProhibited(school))
            return false;
        me->ProhibitSpellSchool(school, Tune::kKickLockMs);
        return true;
    }

    int32 ImmolateAmount(Player* target, uint32 flat, float heroicPct) const
    {
        if (!_heroic)
            return static_cast<int32>(flat);
        return static_cast<int32>(DungeonKit::RefFlatOn(me, target, heroicPct * TitheFactor(Tithe())));
    }

    CastSpellExtraArgs ImmolateArgs(Player* target, bool withHit, TriggerCastFlags flags) const
    {
        CastSpellExtraArgs args(flags);
        args.AddSpellBP0(withHit ? ImmolateAmount(target, Tune::kImmolateFlatDirect, Tune::kImmolateHeroicDirectPct)
            : 0);
        args.AddSpellMod(SPELLVALUE_BASE_POINT1,
            ImmolateAmount(target, Tune::kImmolateFlatTick, Tune::kImmolateHeroicTickPct));
        return args;
    }

    // `forced`: the `.dbtest` target.
    bool CastImmolate(Player* forced)
    {
        Player* target = forced;
        if (!target)
        {
            std::vector<Player*> const burning = Burning();
            if (ImmolateFull(burning.size()))
            {
                LogJr("immolate-skip", Acore::StringFormat("burning={}", burning.size()));
                return true;
            }
            std::vector<uint64> skip = OffHall();
            for (Player* player : burning)
                skip.push_back(player->GetGUID().GetRawValue());
            target = DungeonKit::PickPlayer(me, ImmolatePick(std::move(skip)));
            if (!target)
            {
                LogJr("immolate-skip", "everyone burns");
                return true;
            }
        }
        me->StopMoving();
        SpellCastResult const result = me->CastSpell(target, SPELL_JR_IMMOLATE,
            ImmolateArgs(target, true, TRIGGERED_NONE));
        if (result != SPELL_CAST_OK)
        {
            LogRefused("immolate", result);
            return false;
        }
        ++_counts.immolates;
        LogJr("immolate", Acore::StringFormat("target={} tank={} burning={} tithe={}", target->GetName(),
            target == me->GetVictim() ? 1 : 0, Burning().size(), Tithe()));
        return true;
    }

    // The DoT without the hit (ruling 15's spread, `.dbtest`).
    void Light(Player* player)
    {
        _relighting = true;
        me->CastSpell(player, SPELL_JR_IMMOLATE, ImmolateArgs(player, false, TRIGGERED_FULL_MASK));
        _relighting = false;
    }

    // A refusal (a lockout) is retried every half second: one line per run of them.
    void LogRefused(char const* what, SpellCastResult result)
    {
        if (_timeline.Now() < _refusedLogAt)
            return;
        _refusedLogAt = _timeline.Now() + 3000;
        LogJr("refused", Acore::StringFormat("{} result={}", what, uint32(result)));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // JR2 Conflagrate
    // ----------------------------------------------------------------------------------------------------------------

    void StartConflagrate()
    {
        _conflagrate = ConflagrateState();
        _conflagrate.factor = TitheFactor(Tithe());
        _conflagrate.endsAt = _timeline.Now() + Tune::kConflagrateCastMs;
        me->StopMoving();
        DungeonKit::CastBar(me, SPELL_JR_CONFLAGRATE_CAST, nullptr, EMOTE_JERGOSH_CONFLAGRATE);
        float const pct = Tune::kConflagrateOthersPct(_heroic) * _conflagrate.factor;
        MechanicRef ref = Mechanic::Spread(me, Tune::kConflagrateRadius(_heroic), Ms(Tune::kConflagrateCastMs));
        ref.SelfTrigger(SPELL_JR_IMMOLATE, 1).School(SPELL_SCHOOL_FIRE).Damage(pct).TankDamage(pct)
            .Spell(SPELL_JR_CONFLAGRATE).Weakened().Tag(TAG_JR_CONFLAGRATE);
        ref.OnResolve(OnJergosh([](boss_jergosh_rework& ai, BossMechanics::ResolveResult const& result)
        {
            ai.Burst(result);
        }));
        _conflagrate.rings = ref.Handle();
        ++_counts.conflagrates;
        std::string names;
        for (Player* player : Burning())
            names += " " + player->GetName();
        LogJr("conflagrate", Acore::StringFormat("burning={} pct={:.1f} tithe={} bearers:{}", Burning().size(), pct,
            Tithe(), names.empty() ? " -" : names));
    }

    // The rings have hit (every carrier's, one report): each burn is consumed, its bearer takes their own burst, and
    // on heroic whoever another's ring hit catches fire. Consumed first: a bearer hit by another bearer ends burning.
    void Burst(BossMechanics::ResolveResult const& result)
    {
        if (!_conflagrate.rings || result.mechanicId != _conflagrate.rings.id)
            return;
        float const pct = Tune::kConflagrateBearerPct(_heroic) * _conflagrate.factor;
        _conflagrate = ConflagrateState();

        GuidVector bearers;
        for (Player* player : Burning())
            bearers.push_back(player->GetGUID());
        for (ObjectGuid const& guid : bearers)
            if (Player* player = ObjectAccessor::GetPlayer(*me, guid))
                player->RemoveAurasDueToSpell(SPELL_JR_IMMOLATE);
        for (ObjectGuid const& guid : bearers)
            if (Player* player = ObjectAccessor::GetPlayer(*me, guid))
                CastPercent(player, SPELL_JR_CONFLAGRATE_BEARER, pct);

        std::vector<uint64> hits;
        for (ObjectGuid const& guid : result.hits)
            if (guid.IsPlayer())
                hits.push_back(guid.GetRawValue());
        std::string names;
        uint32 lit = 0;
        for (uint64 const raw : BurningAfter(hits, _heroic))
        {
            Player* player = ObjectAccessor::GetPlayer(*me, ObjectGuid(raw));
            if (!CountsAsPlayer(player) || !player->IsInMap(me))
                continue;
            Light(player);
            names += " " + player->GetName();
            ++lit;
        }
        _counts.ringHits += static_cast<uint32>(hits.size());
        _counts.relit += lit;
        LogJr("burst", Acore::StringFormat("bearers={} ring-hits={} relit={}:{}", bearers.size(), hits.size(), lit,
            names.empty() ? " -" : names));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // JR3 Curse of Weakness (stock)
    // ----------------------------------------------------------------------------------------------------------------

    bool CastCurse()
    {
        Unit* victim = me->GetVictim();
        if (!victim)
            return false;
        SpellCastResult const result = me->CastSpell(victim, SPELL_CURSE_OF_WEAKNESS, false);
        if (result != SPELL_CAST_OK)
        {
            LogRefused("curse", result);
            return false;
        }
        LogJr("curse", Acore::StringFormat("target={}", victim->GetName()));
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // JR4 Drain Soul (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    bool StartDrain(Player* forced)
    {
        Player* target = forced ? forced : DungeonKit::PickPlayer(me, DrainSoulPick(OffHall()));
        if (!target)
            return false;
        me->StopMoving();
        SpellCastResult const result = me->CastSpell(target, SPELL_JR_DRAIN_SOUL, false);
        if (result != SPELL_CAST_OK)
        {
            LogRefused("drain-soul", result);
            return false;
        }
        Talk(EMOTE_JERGOSH_DRAIN_SOUL, target);
        _drain.active = true;
        _drain.owner = target->GetGUID();
        ++_counts.drains;
        LogJr("drain-soul", Acore::StringFormat("target={} tank={} tithe={}", target->GetName(),
            target == me->GetVictim() ? 1 : 0, Tithe()));
        return true;
    }

    // A channel whose owner died, left or became immune ends without any hook: nothing happens.
    void WatchDrain()
    {
        if (_drain.active && !me->FindCurrentSpellBySpellId(SPELL_JR_DRAIN_SOUL))
            EndDrain("broken");
    }

    void EndDrain(char const* why)
    {
        if (!_drain.active)
            return;
        Player* owner = ObjectAccessor::GetPlayer(*me, _drain.owner);
        _drain = DrainState();
        LogJr("drain-soul-end", Acore::StringFormat("why={} owner={}", why, owner ? owner->GetName() : "gone"));
    }

    void SoulTorn()
    {
        if (!_drain.active)
            return;
        ObjectGuid const guid = _drain.owner;
        _drain = DrainState();
        Player* owner = ObjectAccessor::GetPlayer(*me, guid);
        if (!CountsAsPlayer(owner) || !owner->IsInMap(me))
        {
            LogJr("drain-soul-end", "why=completed owner=gone");
            return;
        }
        Position const at = owner->GetPosition();
        ++_counts.torn;
        CastPercent(owner, SPELL_JR_SOUL_TEAR, Tune::kSoulTearPct * TitheFactor(Tithe()));
        SpawnWisp(guid, at);    // the owner may have died of the tear: the soul drifts on (section 7 #36 A)
    }

    // ----------------------------------------------------------------------------------------------------------------
    // JR5 the wisp and the Tithe (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    void SpawnWisp(ObjectGuid ownerGuid, Position const& ownerAt)
    {
        Vec2 const start = WispStart({ ownerAt.GetPositionX(), ownerAt.GetPositionY() }, kOfferingSpot.XY());
        // The start is always in the hall, its owner not always: the hall's height.
        Position const at = OnFloor(me, start, kJergoshSpawn.z);

        DungeonKit::CrawlPickupSpec spec;
        spec.entry = NPC_RFC_SOUL_WISP;
        spec.radius = Tune::kWispTouchYd;
        spec.wait = Milliseconds(0);
        spec.crawlSpeed = Tune::kWispSpeed;
        spec.reach = kWispReachYd;
        spec.count = 1;
        spec.tag = TAG_JR_WISP;
        BossMechanics::Ordering order;
        order.roleLast = BossMechanics::Role::Healer;
        spec.order = order;
        // Any living player may step in, its owner included (section 7 #29 A): no eligibility.
        Map* map = me->GetMap();
        ObjectGuid const boss = me->GetGUID();
        spec.onPick = [map, boss, ownerGuid](Player* taker, Position const& /*where*/)
        {
            if (boss_jergosh_rework* ai = From(map, boss))
                ai->SoulCaught(ownerGuid, taker);
        };
        spec.onReach = [map, boss, ownerGuid](ObjectGuid /*goal*/, Position const& /*where*/)
        {
            if (boss_jergosh_rework* ai = From(map, boss))
                ai->SoulEaten(ownerGuid);
        };
        DungeonKit::CrawlGoal goal;
        goal.point = Position(kOfferingSpot.x, kOfferingSpot.y, kOfferingSpot.z, 0.f);
        uint32 const id = _wisps.Add(me, at, std::move(spec), goal);
        Player* owner = ObjectAccessor::GetPlayer(*me, ownerGuid);
        LogJr(id ? "wisp" : "wisp-fail", Acore::StringFormat("owner={} at=({:.1f}, {:.1f}, {:.1f}) walk={:.1f} live={}",
            owner ? owner->GetName() : "gone", at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(),
            DungeonKit::Distance(start, kOfferingSpot.XY()), _wisps.Count()));
    }

    void SoulCaught(ObjectGuid ownerGuid, Player* taker)
    {
        ++_counts.caught;
        Player* owner = ObjectAccessor::GetPlayer(*me, ownerGuid);
        LogJr("wisp-caught", Acore::StringFormat("owner={} by={}", owner ? owner->GetName() : "gone",
            taker ? taker->GetName() : "gone"));
    }

    void SoulEaten(ObjectGuid ownerGuid)
    {
        if (!_engaged || !me->IsAlive())
            return;
        Talk(EMOTE_JERGOSH_EATEN);
        me->CastSpell(me, SPELL_JR_FEED_LOOK, true);
        Player* owner = ObjectAccessor::GetPlayer(*me, ownerGuid);
        bool const sick = CountsAsPlayer(owner) && owner->IsInMap(me);
        if (sick)
            me->CastSpell(owner, SPELL_JR_SOUL_SICK, true);
        SetTithe(Tithe() + 1);
        LogJr("wisp-eaten", Acore::StringFormat("owner={} soul-sick={} tithe={} factor={:.2f}",
            owner ? owner->GetName() : "gone", sick ? 1 : 0, Tithe(), TitheFactor(Tithe())));
    }

    uint32 Tithe() const
    {
        return DungeonKit::Stacks(me, SPELL_JR_TITHE);
    }

    void SetTithe(uint32 stacks)
    {
        uint32 const now = Tithe();
        DungeonKit::AddStacks(me, SPELL_JR_TITHE, int32(std::min(stacks, kTitheMaxStacks)) - int32(now), me,
            kTitheMaxStacks);
        me->SetObjectScale(me->GetNativeObjectScale() * TitheScale(Tithe()));
        _grown = true;
    }

    void MarkOfferingSpot()
    {
        Position const at = OnFloor(me, kOfferingSpot.XY(), kOfferingSpot.z);
        Creature* stalker = me->SummonCreature(NPC_RFC_STALKER, at, TEMPSUMMON_MANUAL_DESPAWN);
        if (!stalker)
        {
            LogJr("offering-spot-fail");
            return;
        }
        stalker->SetReactState(REACT_PASSIVE);
        stalker->CastSpell(stalker, SPELL_JR_OFFERING_SPOT, true);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data, plumbing, cleanup
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        BossMechanics::Descriptor d;
        if (_heroic)
        {
            d.interrupts.emplace_back(NPC_JERGOSH, SPELL_JR_DRAIN_SOUL, kDrainSoulKickPriority,
                Ms(Tune::kDrainSoulEveryMs));
        }
        d.interrupts.emplace_back(NPC_JERGOSH, SPELL_JR_IMMOLATE, kImmolateKickPriority,
            Ms(Tune::kImmolateEveryMs(_heroic)));
        Mechanic::Describe(me, std::move(d));
        Mechanic::NoteNextCastIn(me, SPELL_JR_IMMOLATE, Ms(Tune::kImmolateFirstMs(_heroic)));
        if (_heroic)
            Mechanic::NoteNextCastIn(me, SPELL_JR_DRAIN_SOUL, Ms(Tune::kDrainSoulFirstMs));
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

    // The players on his threat list the fight acts on.
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

    // The players the random picks skip: off his hall (the tunnels, the ridge, the strip), unless nobody is in it.
    std::vector<uint64> OffHall() const
    {
        std::vector<std::pair<uint64, bool>> players;
        for (Player* player : FightPlayers())
            players.emplace_back(player->GetGUID().GetRawValue(), _arena.Contains(player));
        return Outsiders(players);
    }

    static boss_jergosh_rework* From(Map* map, ObjectGuid guid)
    {
        Creature* boss = map ? map->GetCreature(guid) : nullptr;
        if (!boss || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_jergosh_rework*>(boss->AI());
    }

    // Runs `fn(ai, result)` on this boss when the registry calls back, if he is still there. Captures the map and the
    // guid only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnJergosh(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (boss_jergosh_rework* ai = From(map, guid))
                fn(*ai, result);
        };
    }

    // The pull's state, gone (a reset, an evade, his death, a new pull). `_engaged` goes first: the stopped casts'
    // OnSpellFailed then does nothing.
    void Cleanup()
    {
        _engaged = false;
        if (_conflagrate.rings)
            Mechanic::Cancel(me, _conflagrate.rings);
        _conflagrate = ConflagrateState();
        _drain = DrainState();
        if (me->IsNonMeleeSpellCast(false))
            me->InterruptNonMeleeSpells(false);
        _wisps.Clear(me);
        summons.DespawnAll();
        me->RemoveAurasDueToSpell(SPELL_JR_TITHE);
        if (_grown)
            me->SetObjectScale(me->GetNativeObjectScale());
        _grown = false;
        if (instance)
            for (uint32 const spell : { uint32(SPELL_JR_IMMOLATE), uint32(SPELL_JR_DRAIN_SOUL),
                uint32(SPELL_JR_SOUL_SICK) })
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
        _timeline = Timeline();
        _counts = Counts();
        _refusedLogAt = 0;
        _arena.Reset();
    }

    struct ConflagrateState
    {
        MechanicHandle rings;       // set from the bar's start to the burst
        uint64 endsAt = 0;          // the bar's end (the timeline's clock)
        float factor = 1.f;         // the Tithe at the bar's start
    };

    struct DrainState
    {
        bool active = false;
        ObjectGuid owner;
    };

    struct Counts
    {
        uint32 immolates = 0;
        uint32 conflagrates = 0;
        uint32 ringHits = 0;
        uint32 relit = 0;
        uint32 drains = 0;
        uint32 torn = 0;
        uint32 caught = 0;
    };

    DungeonKit::ArenaGuard _arena;
    DungeonKit::CrawlPickups _wisps;
    Timeline _timeline;
    ConflagrateState _conflagrate;
    DrainState _drain;
    Counts _counts;
    uint64 _refusedLogAt = 0;
    bool _heroic = false;
    bool _engaged = false;
    bool _grown = false;
    bool _relighting = false;
};

// Soul Wisp 300986: a body the boss's CrawlPickups moves, judges and removes.
struct npc_rfc_soul_wisp : public NullCreatureAI
{
    explicit npc_rfc_soul_wisp(Creature* creature) : NullCreatureAI(creature) { }
};

namespace
{
    boss_jergosh_rework* FindJergoshAI(ChatHandler* handler)
    {
        Creature* boss = RfcTest::FindBoss(handler, NPC_JERGOSH);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_jergosh_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Jergosh is not running boss_jergosh_rework (check the ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_jergosh_rework::TestMechanic mechanic, char const* what, uint32 n = 0)
    {
        boss_jergosh_rework* ai = FindJergoshAI(handler);
        if (!ai)
            return false;
        Player* who = handler->GetSession() ? handler->getSelectedPlayerOrSelf() : nullptr;
        std::string const error = ai->TestFire(mechanic, who, n);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Jergosh: {} fired.", what);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return RfcTest::ShowBossInfo(handler, NPC_JERGOSH, BOSS_JERGOSH);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_jergosh_rework* ai = FindJergoshAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Jergosh: {}", ai->TestState());
        return true;
    }

    bool HandleImmolate(ChatHandler* handler)
    {
        return Fire(handler, boss_jergosh_rework::TestMechanic::Immolate,
            "Immolate (JR1: the selected player, else random; kickable)");
    }

    bool HandleBurn(ChatHandler* handler)
    {
        return Fire(handler, boss_jergosh_rework::TestMechanic::Burn, "a burn on the selected player (no hit)");
    }

    bool HandleBurnAll(ChatHandler* handler)
    {
        return Fire(handler, boss_jergosh_rework::TestMechanic::BurnAll, "a burn on everyone in the fight (no hit)");
    }

    bool HandleConflagrate(ChatHandler* handler)
    {
        return Fire(handler, boss_jergosh_rework::TestMechanic::Conflagrate,
            "Conflagrate (JR2: a ring on everyone burning)");
    }

    bool HandleDrain(ChatHandler* handler)
    {
        return Fire(handler, boss_jergosh_rework::TestMechanic::DrainSoul,
            "Drain Soul (JR4: the selected player, else random; any difficulty)");
    }

    bool HandleWisp(ChatHandler* handler)
    {
        return Fire(handler, boss_jergosh_rework::TestMechanic::Wisp,
            "a soul wisp (JR5) from the selected player, without the channel");
    }

    bool HandleTithe(ChatHandler* handler, uint32 stacks)
    {
        return Fire(handler, boss_jergosh_rework::TestMechanic::Tithe, "the Tithe's stacks (0 to 99)", stacks);
    }

    bool HandleCurse(ChatHandler* handler)
    {
        return Fire(handler, boss_jergosh_rework::TestMechanic::Curse, "Curse of Weakness (JR3) on his target");
    }

    // `.dbtest rfc jergosh <sub>`: the numbers are the map's difficulty.
    ChatCommandTable const& JergoshTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",        HandleInfo,        SEC_GAMEMASTER, Console::No },
            { "state",       HandleState,       SEC_GAMEMASTER, Console::No },
            { "immolate",    HandleImmolate,    SEC_GAMEMASTER, Console::No },
            { "burn",        HandleBurn,        SEC_GAMEMASTER, Console::No },
            { "burnall",     HandleBurnAll,     SEC_GAMEMASTER, Console::No },
            { "conflagrate", HandleConflagrate, SEC_GAMEMASTER, Console::No },
            { "drain",       HandleDrain,       SEC_GAMEMASTER, Console::No },
            { "wisp",        HandleWisp,        SEC_GAMEMASTER, Console::No },
            { "tithe",       HandleTithe,       SEC_GAMEMASTER, Console::No },
            { "curse",       HandleCurse,       SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_jergosh_rework()
{
    RegisterDungeonReworkCreatureAI(boss_jergosh_rework, RagefireChasmRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_rfc_soul_wisp, RagefireChasmRework::kInstanceScriptName);
    RfcTest::RegisterBoss("jergosh", JergoshTestCommands());
}
