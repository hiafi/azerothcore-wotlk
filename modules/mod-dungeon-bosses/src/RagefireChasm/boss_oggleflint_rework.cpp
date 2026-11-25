/*
 * mod-dungeon-bosses, Ragefire Chasm D1: Oggleflint, Ragefire Chieftain (11517). Build spec:
 * docs/dungeons/ragefire-chasm-rework.md "Oggleflint" (ruling 15), handoff sections 3.5 row D1, 3.6, 3.8, 3.12. Pure
 * rules: OggleflintLogic.h; every number: RagefireChasmRework.h namespace Oggleflint. Replaces his SmartAI (Cleave
 * 40505 is no longer cast).
 *
 *   OG1 Borer Hunt      at 10 s, then every 15 s (heroic 12 s), a Borer (300985: an invisible carrier with a dirt
 *                       trail, not selectable, not attackable) tunnels from his feet after a random player, the tank
 *                       included, for 4 s at 4 (5) yd/s. A 3 yd circle on it, for the hunted player only, deals
 *                       nothing: the mound is the tell. The hunted player dead: it stops there and still erupts
 *                       (section 7 #36 A)
 *   OG2 the eruption    a 4 yd ring where it stopped, 2 s: 30% (45%) Physical, Weakened, thrown straight up
 *   OG3 Club Swing      at 6 s, then every 12 s: a 2 s wind-up bar, then a 90 degree, 8 yd cone in front of him: 30%
 *                       (40%) and Weakened to anyone but the tank, who takes 10% of the tank row
 *   OG4 the Beating     heroic, at 15 s, then every 20 s: he leaves the tank for a random player, the tank included,
 *                       never a hunted one, and leaps after them three times: a 3 yd circle on the spot they stood when
 *                       it was marked, 1.5 s, the next marked as the last lands; 35% and Weakened a blow. Then back to
 *                       the top of his threat list, unchanged. Skipped while every player is hunted
 *   More Borers         heroic (ruling 15, section 7 #28 A): one more at 40 s and every 40 s, no cap, each hunt beat
 *                       sending every Borer after a player of its own, never the beaten one; a join with no player left
 *                       for it waits for the next mark
 *
 * A hunt and a swing never start within 3 s of each other; a swing and the Beating never overlap. Every percent hit is
 * a percent of the reference row (his spells ignore caster modifiers). Boss data: no kill order, interrupts, dispels or
 * purges. Every firing logs one INFO line "rfc oggleflint <mechanic> ..." (module.dungeonbosses); `.dbtest rfc
 * oggleflint ...` fires one mechanic on demand.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitChase.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "OggleflintLogic.h"
#include "Player.h"
#include "RagefireChasmKit.h"
#include "RagefireChasmRework.h"
#include "RagefireChasmTestCommand.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ThreatManager.h"
#include <cmath>
#include <functional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace RagefireChasmRework;
using namespace RfcOggleflint;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBoss = "oggleflint";

    // A probed floor farther than this from the den's is another level (a ledge 17 yd up): rule 33.
    float constexpr kFloorBandYd = 3.f;

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    void LogOg(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    // A player the fight acts on: in the world, alive, not a game master.
    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    // `p` on the den's floor: the landing clamp (section 7 #24 A) at the floor's height.
    Position DenPoint(WorldObject const* probe, Vec2 p)
    {
        Vec2 const in = ClampInto(kDenFloorPolygon, p);
        float const z = probe->GetMapHeight(in.x, in.y, kDenFloorZ + kFloorBandYd);
        bool const floor = z > INVALID_HEIGHT && std::fabs(z - kDenFloorZ) <= kFloorBandYd;
        return Position(in.x, in.y, floor ? z : kDenFloorZ, 0.f);
    }
}

// The Borer 300985: a mover of Oggleflint's. His AI drives its chase and its eruption; it never fights.
struct npc_rfc_borer : public ScriptedAI
{
    explicit npc_rfc_borer(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void EnterEvadeMode(EvadeReason /*why*/) override { }
    void UpdateAI(uint32 /*diff*/) override { }
};

// Oggleflint 11517
struct boss_oggleflint_rework : public BossAI
{
    explicit boss_oggleflint_rework(Creature* creature)
        : BossAI(creature, BOSS_OGGLEFLINT), _arena(OggleflintArena(), LeashOptions(kBoss)) { }

    // One Borer out: its player, the chase (OG1), then the ring (OG2). Gone once it erupted.
    struct BorerHunt
    {
        ObjectGuid borer;
        ObjectGuid target;
        DungeonKit::Chaser chase;
        MechanicHandle circle;
        MechanicHandle ring;
    };

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

        _heroic = IsHeroicMap(me);
        OnBossPull(me, kBoss);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_OGGLEFLINT;
        Mechanic::BeginEncounter(me, options);
        // Nothing to kick, dispel, purge or focus (the Borers cannot be selected).
        Mechanic::Describe(me, BossMechanics::Descriptor());
        _arena.Engage(me);

        _clockMs = 0;
        _borers = 1;
        _timeline.Start(_heroic);
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        LogOg("evade", Acore::StringFormat("reason={} clock={}s", uint32(why), _clockMs / 1000));
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        LogOg("death", Acore::StringFormat("clock={}s borers={} hunts={} eruptions={} swings={} beatings={} skipped={} "
            "killer={}", _clockMs / 1000, _borers, _huntCount, _eruptions, _swings, _beatings, _beatingsSkipped,
            killer ? killer->GetName() : std::string("none")));
        Cleanup();
    }

    // The Borers are his (they go with his reset and death) and never join the fight.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    // OG3: a wind-up that broke takes its cone with it (rule 13). His own stops are not breaks: Cleanup drops the state
    // before the engine interrupts the cast.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (!spell || spell->Id != SPELL_OG_SWING_BAR || !_swingCone)
            return;
        Drop(_swingCone);
        LogOg("swing-broken");
    }

    void UpdateAI(uint32 diff) override
    {
        me->SetAssistanceTimer(0);      // section 7 #12 A: the flag stops the first call only
        if (!UpdateVictim())
            return;
        // During the Beating he holds no target and every landing is clamped to the den: the guard waits.
        if (!_chain.active && !_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        _clockMs += diff;
        UpdateHunts(diff);
        UpdateBeating();
        UpdateTimeline();
        if (_chain.active || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The timeline
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateTimeline()
    {
        if (!_timeline.On())
            return;
        if (_timeline.BorerMark(_clockMs))
        {
            _timeline.BorerMarkPassed(_clockMs);
            JoinBorer();
        }
        if (_timeline.BeatingMayStart(_clockMs) && !me->HasUnitState(UNIT_STATE_CASTING))
        {
            _timeline.BeatingBeat(_clockMs);
            if (!StartBeating(nullptr))
            {
                ++_beatingsSkipped;
                LogOg("beating-skipped", Acore::StringFormat("hunted={} players={}", _hunts.size(),
                    FightPlayers().size()));
            }
        }
        if (_timeline.HuntMayStart(_clockMs))
        {
            _timeline.HuntStarted(_clockMs);
            HuntBeat();
        }
        if (_timeline.SwingMayStart(_clockMs) && !me->HasUnitState(UNIT_STATE_CASTING))
        {
            _timeline.SwingStarted(_clockMs);
            Swing();
        }
    }

    // Ruling 15: one more Borer, from the next hunt beat on.
    bool JoinBorer()
    {
        uint32 const living = static_cast<uint32>(FightPlayers().size());
        bool const joins = BorerMayJoin(_borers, living, _chain.active);
        if (joins)
            ++_borers;
        LogOg(joins ? "borer-joins" : "borer-waits", Acore::StringFormat("borers={} players={} beating={} clock={}s",
            _borers, living, _chain.active ? 1 : 0, _clockMs / 1000));
        return joins;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // OG1 Borer Hunt, OG2 the eruption
    // ----------------------------------------------------------------------------------------------------------------

    // Every Borer after a player of its own, never the beaten one.
    void HuntBeat()
    {
        std::vector<ObjectGuid> excluded = Hunted();
        if (_chain.active)
            excluded.push_back(_beaten);
        std::vector<ObjectGuid> const picks = PickDistinctIds(GuidsOf(FightPlayers()), excluded, _borers,
            [](uint32 n) { return urand(0, n - 1); });
        for (ObjectGuid const& guid : picks)
            StartHunt(ObjectAccessor::GetPlayer(*me, guid));
        LogOg("hunt-beat", Acore::StringFormat("borers={} sent={} clock={}s", _borers, picks.size(),
            _clockMs / 1000));
    }

    bool StartHunt(Player* player)
    {
        if (!CountsAsPlayer(player) || !player->IsInMap(me))
            return false;
        Position const at = DenPoint(me, DungeonKit::PlaneOf(me));
        TempSummon* borer = me->SummonCreature(NPC_RFC_BORER, at, TEMPSUMMON_TIMED_DESPAWN, kBorerLifeMs);
        if (!borer)
        {
            LogOg("hunt-failed", "no Borer (the template 300985 is missing or the summon failed)");
            return false;
        }
        borer->SetReactState(REACT_PASSIVE);
        borer->CastSpell(borer, SPELL_OG_TUNNEL, true);

        BorerHunt hunt;
        hunt.borer = borer->GetGUID();
        hunt.target = player->GetGUID();
        // The kit's Chaser: no threat of its own (no fixate), so a target that goes ends the chase where it is.
        DungeonKit::ChaserSpec spec;
        spec.speed = Tune::kChaseSpeed(_heroic);
        spec.life = Ms(Tune::kChaseMs);
        spec.endOnArrive = false;
        spec.fixate = false;
        if (!hunt.chase.Start(borer, player, spec))
        {
            borer->DespawnOrUnsummon();
            return false;
        }
        {
            BossMechanics::Eligibility hunted;
            hunted.carriers = { player->GetGUID() };
            hunted.playersOnly = true;
            MechanicRef ref = Mechanic::Circle(me, borer, Tune::kChaseRadius, Ms(kChaseArmMs));
            ref.Persistent(Ms(kChaseStandsMs), Milliseconds(0)).Eligible(hunted).NoTelegraph()
                .Within(OggleflintFloorBounds()).Tag(TAG_OG_CHASE);
            hunt.circle = ref.Handle();
        }   // the ref commits here

        Talk(EMOTE_OGGLEFLINT_HUNT, player);
        ++_huntCount;
        LogOg("hunt", Acore::StringFormat("target={} tank={} speed={:.0f} live={}", player->GetName(),
            player == me->GetVictim() ? 1 : 0, spec.speed, _hunts.size() + 1));
        _hunts.push_back(std::move(hunt));
        return true;
    }

    void UpdateHunts(uint32 diff)
    {
        for (std::size_t i = 0; i < _hunts.size();)
        {
            BorerHunt& hunt = _hunts[i];
            Creature* borer = ObjectAccessor::GetCreature(*me, hunt.borer);
            if (!borer)
            {
                Drop(hunt.circle);
                Drop(hunt.ring);
                _hunts.erase(_hunts.begin() + static_cast<std::ptrdiff_t>(i));
                continue;
            }
            if (!hunt.ring)
            {
                hunt.chase.Update(borer, diff);
                if (!hunt.chase.Active())
                    MarkEruption(hunt, borer);      // its 4 s are over, or its player is gone
            }
            ++i;
        }
    }

    void MarkEruption(BorerHunt& hunt, Creature* borer)
    {
        Drop(hunt.circle);
        float const pct = Tune::kEruptionPct(_heroic);
        ObjectGuid const guid = borer->GetGUID();
        MechanicRef ref = Mechanic::Circle(me, borer->GetPosition(), Tune::kEruptionRadius,
            Ms(Tune::kEruptionWarnMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_OG_ERUPTION).Weakened()
            .Within(OggleflintFloorBounds()).Tag(TAG_OG_ERUPTION)
            .OnHit([](Unit* hit)
            {
                // Straight up: no sideways speed (pets stay down: the engine drops a knockback without any).
                if (Player* player = hit ? hit->ToPlayer() : nullptr)
                    if (player->IsAlive())
                        player->KnockbackFrom(player->GetPositionX(), player->GetPositionY(), 0.f, kKnockUpSpeedZ);
            })
            .OnResolve(OnOggleflint([guid](boss_oggleflint_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai.Erupt(guid, r);
            }));
        hunt.ring = ref.Handle();
        LogOg("eruption-mark", Acore::StringFormat("at=({:.1f}, {:.1f}, {:.1f}) pct={:.0f}", borer->GetPositionX(),
            borer->GetPositionY(), borer->GetPositionZ(), pct));
        if (!hunt.ring)
            borer->DespawnOrUnsummon();     // refused: UpdateHunts drops it
    }

    // The worm bursts up and sinks again.
    void Erupt(ObjectGuid borerGuid, BossMechanics::ResolveResult const& result)
    {
        for (std::size_t i = 0; i < _hunts.size(); ++i)
            if (_hunts[i].borer == borerGuid)
            {
                _hunts.erase(_hunts.begin() + static_cast<std::ptrdiff_t>(i));
                break;
            }
        Creature* borer = ObjectAccessor::GetCreature(*me, borerGuid);
        if (borer)
        {
            borer->RemoveAurasDueToSpell(SPELL_OG_TUNNEL);
            borer->SetDisplayId(kWormDisplay, kWormScale);
            borer->CastSpell(borer->GetPositionX(), borer->GetPositionY(), borer->GetPositionZ(),
                SPELL_OG_ERUPTION_LOOK, true);
            borer->DespawnOrUnsummon(Ms(kWormMs));
        }
        ++_eruptions;
        LogOg("eruption", Acore::StringFormat("hits={} borer={}", result.hits.size(), borer ? 1 : 0));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // OG3 Club Swing
    // ----------------------------------------------------------------------------------------------------------------

    // The 2 s wind-up (he stands for it), the registry's cone beside it, the tank's own hit as it lands.
    bool Swing()
    {
        me->StopMoving();
        DungeonKit::CastBar(me, SPELL_OG_SWING_BAR, nullptr, EMOTE_OGGLEFLINT_SWING);
        MechanicRef ref = Mechanic::Cone(me, me, Tune::kSwingAngleDeg, Tune::kSwingLength, Ms(Tune::kSwingWarnMs),
            BossMechanics::TankExempt::Yes);
        ref.Damage(Tune::kSwingPct(_heroic)).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_OG_SWING).Weakened()
            .Within(OggleflintFloorBounds()).Tag(TAG_OG_SWING)
            .OnResolve(OnOggleflint([](boss_oggleflint_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai.SwingLands(r);
            }));
        _swingCone = ref.Handle();
        ++_swings;
        LogOg("swing", Acore::StringFormat("pct={:.0f} tank-pct={:.0f} clock={}s", Tune::kSwingPct(_heroic),
            Tune::kSwingTankPct, _clockMs / 1000));
        return bool(_swingCone);
    }

    void SwingLands(BossMechanics::ResolveResult const& result)
    {
        _swingCone = MechanicHandle();
        if (result.fizzled)
            return;
        Unit* victim = me->GetVictim();
        bool const tankHit = victim && victim->IsAlive() && DungeonKit::InFrontalCone(DungeonKit::PlaneOf(me),
            me->GetOrientation(), DungeonKit::PlaneOf(victim), Tune::kSwingAngleDeg, Tune::kSwingLength,
            me->GetCombatReach());
        if (tankHit)
            me->CastSpell(victim, SPELL_OG_SWING_TANK, true);
        else
            me->CastSpell(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), SPELL_OG_SWING_LOOK, true);
        LogOg("swing-lands", Acore::StringFormat("hits={} tank={}", result.hits.size(), tankHit ? 1 : 0));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // OG4 the Beating (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    // `forced` (a test): that player. False when nobody is free: every player is hunted.
    bool StartBeating(Player* forced)
    {
        Player* target = forced;
        if (!target)
        {
            std::vector<ObjectGuid> const pick = PickDistinctIds(GuidsOf(FightPlayers()), Hunted(), 1,
                [](uint32 n) { return urand(0, n - 1); });
            target = pick.empty() ? nullptr : ObjectAccessor::GetPlayer(*me, pick.front());
        }
        if (!CountsAsPlayer(target) || !target->IsInMap(me))
            return false;

        bool const tank = target == me->GetVictim();
        _chain.Start();
        _beaten = target->GetGUID();
        _timeline.BeatingStarted();
        ++_beatings;
        me->SetReactState(REACT_PASSIVE);
        me->AttackStop();
        me->StopMoving();
        me->GetMotionMaster()->Clear();
        me->SetFacingToObject(target);      // standing: the first leap is kBeatingBlowMs - kLeapMs away (rule 26)
        Talk(EMOTE_OGGLEFLINT_BEATING, target);
        LogOg("beating", Acore::StringFormat("target={} tank={} hunted={} clock={}s", target->GetName(), tank ? 1 : 0,
            _hunts.size(), _clockMs / 1000));
        MarkBlow();
        return _chain.active;
    }

    // The next blow on the spot the player stands on now.
    void MarkBlow()
    {
        Player* target = ObjectAccessor::GetPlayer(*me, _beaten);
        if (!CountsAsPlayer(target) || !target->IsInMap(me))
        {
            EndBeating("target-gone");
            return;
        }
        Position const spot = target->GetPosition();
        _landing = DenPoint(me, DungeonKit::PlaneOf(target));
        _chain.Marked(_clockMs);
        {
            MechanicRef ref = Mechanic::Circle(me, spot, Tune::kBeatingRadius, Ms(Tune::kBeatingBlowMs));
            ref.Damage(Tune::kBeatingPct).TankDamage(Tune::kBeatingPct).School(SPELL_SCHOOL_NORMAL)
                .Spell(SPELL_OG_BLOW).Weakened().Within(OggleflintFloorBounds()).Tag(TAG_OG_BLOW)
                .OnResolve(OnOggleflint([](boss_oggleflint_rework& ai, BossMechanics::ResolveResult const& r)
                {
                    ai.BlowLands(r);
                }));
            _blow = ref.Handle();
        }   // the ref commits here
        LogOg("blow-mark", Acore::StringFormat("blow={} at=({:.1f}, {:.1f}) dist={:.1f}", _chain.blow,
            spot.GetPositionX(), spot.GetPositionY(), me->GetExactDist2d(&_landing)));
        if (!_blow)
            EndBeating("refused");
    }

    void BlowLands(BossMechanics::ResolveResult const& result)
    {
        if (!_chain.active)
            return;
        _blow = MechanicHandle();
        me->HandleEmoteCommand(EMOTE_ONESHOT_ATTACK1H);
        LogOg("blow", Acore::StringFormat("blow={} hits={} off={:.1f}", _chain.blow, result.hits.size(),
            me->GetExactDist2d(&_landing)));
        if (_chain.Last())
            EndBeating("done");
        else if (result.fizzled)
            EndBeating("fizzled");
        else
            MarkBlow();
    }

    void UpdateBeating()
    {
        if (!_chain.active)
            return;
        if (_chain.LeapDue(_clockMs))
        {
            _chain.leapt = true;
            float const dist = me->GetExactDist2d(&_landing);
            if (dist >= kLeapMinYd)
                DungeonKit::JumpTo(me, _landing, LeapSpeedXY(dist, _chain.FlightMs(_clockMs)));
        }
        if (_chain.Overdue(_clockMs))
            EndBeating("overdue");
    }

    // Back to the top of his threat list, unchanged (rule 35).
    void EndBeating(char const* why)
    {
        if (!_chain.active)
            return;
        uint32 const blows = _chain.blow;
        _chain.Stop();
        _beaten.Clear();
        Drop(_blow);
        _timeline.BeatingEnded(_clockMs);
        if (me->IsAlive() && me->IsEngaged())
        {
            me->SetReactState(REACT_AGGRESSIVE);
            if (Unit* victim = me->SelectVictim())
                AttackStart(victim);
        }
        LogOg("beating-end", Acore::StringFormat("why={} blows={}", why, blows));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest rfc oggleflint` entry points (the numbers are the map's difficulty)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Hunt,
        Swing,
        Beating,
        Join,
    };

    // An empty string when fired; otherwise why not. `who` is the GM's selected player (or the GM).
    std::string TestFire(TestMechanic mechanic, Player* who)
    {
        if (!me->IsEngaged())
            return "Oggleflint must be in combat (the picks read his threat list, the mechanics his encounter).";
        Player* player = CountsAsPlayer(who) ? who : nullptr;
        bool const busy = _chain.active || me->HasUnitState(UNIT_STATE_CASTING);
        switch (mechanic)
        {
            case TestMechanic::Hunt:
                if (player)
                {
                    if (!StartHunt(player))
                        return "The hunt did not start (see the log).";
                }
                else
                    HuntBeat();
                _timeline.HuntStarted(_clockMs, false);
                break;
            case TestMechanic::Swing:
                if (busy)
                    return "He is casting or beating.";
                _timeline.SwingStarted(_clockMs, false);
                if (!Swing())
                    return "The registry refused the swing.";
                break;
            case TestMechanic::Beating:
                if (busy)
                    return "He is casting or beating.";
                if (!StartBeating(player))
                    return "Nobody to beat (every player is hunted).";
                break;
            case TestMechanic::Join:
                if (!JoinBorer())
                    return "No player left for another Borer.";
                break;
        }
        return {};
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s heroic={} borers={} live-hunts={} beating={} (blow {}) hunts={} "
            "eruptions={} swings={} beatings={} skipped={}", _clockMs / 1000, _heroic ? 1 : 0, _borers, _hunts.size(),
            _chain.active ? 1 : 0, _chain.blow, _huntCount, _eruptions, _swings, _beatings, _beatingsSkipped);
    }

private:
    // The players on his threat list the fight acts on: in the den or its neck (section 7 #13 A: a player on the ledge
    // above is not in the fight).
    std::vector<Player*> FightPlayers() const
    {
        std::vector<Player*> out;
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
        {
            Unit* unit = ref->GetVictim();
            Player* player = unit ? unit->ToPlayer() : nullptr;
            if (CountsAsPlayer(player) && player->IsInMap(me) && _arena.Contains(player))
                out.push_back(player);
        }
        return out;
    }

    static std::vector<ObjectGuid> GuidsOf(std::vector<Player*> const& players)
    {
        std::vector<ObjectGuid> out;
        for (Player const* player : players)
            out.push_back(player->GetGUID());
        return out;
    }

    // Everyone a Borer is after, until it erupted.
    std::vector<ObjectGuid> Hunted() const
    {
        std::vector<ObjectGuid> out;
        for (BorerHunt const& hunt : _hunts)
            out.push_back(hunt.target);
        return out;
    }

    // Cancels a live mechanic and forgets it.
    void Drop(MechanicHandle& handle)
    {
        if (handle)
            Mechanic::Cancel(me, handle);
        handle = MechanicHandle();
    }

    // Runs `fn(ai, result)` on this boss when the registry calls back, if this pull still runs. Captures the map and
    // the guid only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnOggleflint(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn, pull = _pull](BossMechanics::ResolveResult const& result)
        {
            Creature* boss = map ? map->GetCreature(guid) : nullptr;
            if (!boss || !boss->IsAlive() || !boss->IsEngaged() || !boss->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_oggleflint_rework*>(boss->AI()))
                if (ai->_pull == pull)
                    fn(*ai, result);
        };
    }

    // Nothing left of the pull (reset, evade, death): no shape, no Borer, no hold.
    void Cleanup()
    {
        ++_pull;        // callbacks of the old pull drop
        _timeline.Stop();
        Drop(_swingCone);      // before the engine interrupts the bar, so it never reads as a break
        Drop(_blow);
        for (BorerHunt& hunt : _hunts)
        {
            Drop(hunt.circle);
            Drop(hunt.ring);
            if (Creature* borer = ObjectAccessor::GetCreature(*me, hunt.borer))
                hunt.chase.Stop(borer);
        }
        _hunts.clear();
        summons.DespawnAll();       // the worms of erupted Borers too
        _chain.Stop();
        _beaten.Clear();
        _arena.Reset();
        _clockMs = 0;
        _borers = 1;
        _huntCount = 0;
        _eruptions = 0;
        _swings = 0;
        _beatings = 0;
        _beatingsSkipped = 0;
        if (me->IsAlive() && !me->HasReactState(REACT_AGGRESSIVE))
            me->SetReactState(REACT_AGGRESSIVE);
    }

    DungeonKit::ArenaGuard _arena;
    Timeline _timeline;
    BeatingChain _chain;
    std::vector<BorerHunt> _hunts;
    MechanicHandle _swingCone;
    MechanicHandle _blow;
    ObjectGuid _beaten;
    Position _landing;
    uint64 _clockMs = 0;            // ms since the pull
    uint32 _pull = 0;
    uint32 _borers = 1;
    uint32 _huntCount = 0;
    uint32 _eruptions = 0;
    uint32 _swings = 0;
    uint32 _beatings = 0;
    uint32 _beatingsSkipped = 0;
    bool _heroic = false;
};

namespace
{
    boss_oggleflint_rework* FindOggleflintAI(ChatHandler* handler)
    {
        Creature* boss = RfcTest::FindBoss(handler, NPC_OGGLEFLINT);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_oggleflint_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Oggleflint is not running boss_oggleflint_rework (check the ScriptName).");
        return ai;
    }

    using Mech = boss_oggleflint_rework::TestMechanic;

    bool Fire(ChatHandler* handler, Mech mechanic, char const* what)
    {
        boss_oggleflint_rework* ai = FindOggleflintAI(handler);
        if (!ai)
            return false;
        Player* who = handler->GetSession() ? handler->getSelectedPlayerOrSelf() : nullptr;
        std::string const error = ai->TestFire(mechanic, who);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Oggleflint: {} fired ({}).", what,
            ai->HeroicMap() ? "heroic numbers" : "normal numbers");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return RfcTest::ShowBossInfo(handler, NPC_OGGLEFLINT, BOSS_OGGLEFLINT);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_oggleflint_rework* ai = FindOggleflintAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Oggleflint: {}", ai->TestState());
        return true;
    }

    bool HandleHunt(ChatHandler* handler)
    {
        return Fire(handler, Mech::Hunt, "a Borer Hunt after the selected player (OG1, OG2; a GM: the whole beat)");
    }

    bool HandleSwing(ChatHandler* handler)
    {
        return Fire(handler, Mech::Swing, "Club Swing (OG3)");
    }

    bool HandleBeating(ChatHandler* handler)
    {
        return Fire(handler, Mech::Beating, "the Beating on the selected player (OG4, any difficulty)");
    }

    bool HandleJoin(ChatHandler* handler)
    {
        return Fire(handler, Mech::Join, "one more Borer from the next hunt beat on (ruling 15)");
    }

    ChatCommandTable const& OggleflintTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",    HandleInfo,    SEC_GAMEMASTER, Console::No },
            { "state",   HandleState,   SEC_GAMEMASTER, Console::No },
            { "hunt",    HandleHunt,    SEC_GAMEMASTER, Console::No },
            { "swing",   HandleSwing,   SEC_GAMEMASTER, Console::No },
            { "beating", HandleBeating, SEC_GAMEMASTER, Console::No },
            { "join",    HandleJoin,    SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_oggleflint_rework()
{
    RegisterDungeonReworkCreatureAI(boss_oggleflint_rework, RagefireChasmRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_rfc_borer, RagefireChasmRework::kInstanceScriptName);
    RfcTest::RegisterBoss("oggleflint", OggleflintTestCommands());
}
