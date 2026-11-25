/*
 * mod-dungeon-bosses, Ragefire Chasm D4H: Starving, Taragaman's hard mode (heroic only). Build spec:
 * docs/dungeons/ragefire-chasm-rework.md "Hard mode kit: Starving" (TG7-TG9, the hard mode column; rulings 10, 12, 15
 * and 16), handoff section 3.7, section 7 #15-#18, #22, #25, #27, #30, #35-#37. Pure rules: TaragamanHardModeLogic.h;
 * every number is the tuning block RagefireChasmRework::Taragaman. It fights on D4's AI (boss_taragaman_rework) through
 * TaragamanFight.h.
 *
 *   The trigger      the Blood Shrine (GO 301340, beside the Orb in Jergosh's hall) gives whoever uses it the
 *                    Hungerer's Blood (10 min; gone on death, off the map, at logout); the pour spot (GO 301341, the
 *                    -x arm's foot) takes it: the instance's DATA_HARD_MODE (saved, with the loot bit), the look at
 *                    the lava, every other carrier's aura gone, Taragaman's line 9. Out of combat, never once he
 *                    fights or is dead. Both objects are heroic spawns and not selectable while the trigger is
 *                    closed. Bots never use them, and their use is refused (a bot's session is headless)
 *   From the pour    610,400 health and the red aura, through wipes and reloads (the idle hook: idempotent)
 *   Phase 1          the hunt: polled 4 times a second, the moment anyone is under 30% he marks the lowest, at least 6
 *                    s after the last mark; nobody: the lowest anyway every 15 s (D4's Feast timer, at heroic's pace).
 *                    The Felstorm's ring drifts 3 yd/s toward a random player, its center within 8 yd of his spawn (he
 *                    leaps back into that disc before the bar). The rest is D4's hard mode column
 *   Phase 2          at 30%, the blood lake: line 7, the lake's red look at the arm ends
 *     TG7 the combo  Felstorm every 25 s and the Nova 2 s after each spin (D4's timers held, the Feast's
 *                    hold after it 2 s)
 *     TG8 globules   every 20 s four Blood Globules (300987) crawl from the arm ends (32 yd) to him at 2.5 yd/s,
 *                    harmless, 6,000 health; one that reaches him is drunk: +2% health and a Gorged stack
 *     TG9 the burst  a globule that dies (it never bursts when drunk) marks a 6 yd circle where it died: 1.5 s, 30%
 *                    Shadow and Weakened
 *
 * Every unit comes from TaragamanFight::Summon and every registry handle goes to Track: D4's cleanup (wipe, evade,
 * death) takes both. The instance owns the flag, the kill slot BOSS_STARVING and the loot bit. Every firing logs one
 * INFO line "rfc taragaman starving-<what> ..." (module.dungeonbosses); `.dbtest rfc starving ...` fires one on demand.
 */

#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "MoveSpline.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "RagefireChasmKit.h"
#include "RagefireChasmRework.h"
#include "RagefireChasmTestCommand.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellMgr.h"
#include "StringFormat.h"
#include "TaragamanFight.h"
#include "TaragamanHardModeLogic.h"
#include "TaragamanLogic.h"
#include "TemporarySummon.h"
#include "WorldSession.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

using namespace Acore::ChatCommands;
using namespace RagefireChasmRework;
using namespace RfcStarving;
using BossMechanics::MechanicRef;
using RfcTaragaman::TaragamanFight;

namespace
{
    char const* const kBoss = "taragaman";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // Create health is the base the engine rebuilds max health from (the Baron's and Doan's hard mode pattern).
    void SetCreatureHealth(Creature* creature, uint32 health)
    {
        creature->SetCreateHealth(health);
        creature->SetStatFlatModifier(UNIT_MOD_HEALTH, BASE_VALUE, static_cast<float>(health));
        creature->UpdateMaxHealth();
        creature->SetHealth(creature->GetMaxHealth());
    }

    // The plateau's floor under a point (D4's probe band), the static map alone: a standing Searing Spike is no floor.
    std::optional<float> StaticFloor(WorldObject const* ref, float x, float y)
    {
        float const h = ref->GetMap()->GetHeight(x, y, RfcTaragaman::kFloorMidZ + RfcTaragaman::kFloorProbeUpYd);
        return h > INVALID_HEIGHT && RfcTaragaman::OnFloorBand(h) ? std::optional<float>(h) : std::nullopt;
    }

    float FloorZ(WorldObject const* ref, Vec2 p, float fallback)
    {
        return StaticFloor(ref, p.x, p.y).value_or(fallback);
    }

    // A globule's straight way over it.
    std::vector<DungeonKit::FloorPathPoint> GlobulePath(WorldObject const* ref, Vec2 from, Vec2 to)
    {
        return DungeonKit::FloorPath(from, to, FloorZ(ref, from, ref->GetPositionZ()),
            [ref](float x, float y, float /*z*/) { return StaticFloor(ref, x, y); });
    }

    bool OnPlateauFloor(WorldObject const* o)
    {
        static DungeonKit::Arena const floor = PlateauFloor();
        return floor.Contains(DungeonKit::PlaneOf(o), o->GetPositionZ());
    }

    bool Armed(WorldObject const* o)
    {
        InstanceScript* instance = o->GetInstanceScript();
        return instance && DungeonKit::IsHeroicMap(o) && instance->GetData(DATA_HARD_MODE) != 0;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Taragaman out of combat: the hard mode's health and look while the flag is set, the template's and none when it
    // is not (a GM cleared it). Idempotent (D4 calls the idle hook every tick).
    // ----------------------------------------------------------------------------------------------------------------
    void SyncTaragaman(Creature* boss)
    {
        bool const armed = Armed(boss);
        if (armed && boss->GetCreateHealth() != Tune::kHealth.hardMode)
        {
            SetCreatureHealth(boss, Tune::kHealth.hardMode);
            DungeonKit::LogMechanic(kLogDungeon, kBoss, "starving-health", std::to_string(boss->GetMaxHealth()));
        }
        else if (!armed && boss->GetCreateHealth() == Tune::kHealth.hardMode)
        {
            boss->SelectLevel();    // the template's health again
            DungeonKit::LogMechanic(kLogDungeon, kBoss, "starving-health", Acore::StringFormat("{} (cleared)",
                boss->GetMaxHealth()));
        }

        bool const red = boss->HasAura(SPELL_HM_STARVING);
        if (armed && !red)
        {
            if (sSpellMgr->GetSpellInfo(SPELL_HM_STARVING))
                boss->CastSpell(boss, SPELL_HM_STARVING, true);
        }
        else if (!armed && red)
            boss->RemoveAurasDueToSpell(SPELL_HM_STARVING);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The trigger
    // ----------------------------------------------------------------------------------------------------------------
    uint32 TaragamanState(InstanceScript const* instance)
    {
        return static_cast<uint32>(instance->GetBossState(BOSS_TARAGAMAN));
    }

    TriggerState StateFor(Player const* player, InstanceScript const* instance)
    {
        TriggerState s;
        s.bot = !player->GetSession() || player->GetSession()->IsHeadless();
        s.heroic = player->GetMap()->IsHeroic();
        s.alive = player->IsAlive();
        s.inCombat = player->IsInCombat();
        s.carries = player->HasAura(SPELL_HM_HUNGERERS_BLOOD);
        s.taragamanState = TaragamanState(instance);
        s.armed = instance->GetData(DATA_HARD_MODE) != 0;
        return s;
    }

    Refusal Refused(Player* player, char const* what, Refusal refusal)
    {
        if (char const* notice = RefusalNotice(refusal))
            ChatHandler(player->GetSession()).SendNotification(std::string_view(notice));
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "starving-refused", Acore::StringFormat("{} by={} reason={}", what,
            player->GetName(), uint32(refusal)));
        return refusal;
    }

    // `player` uses the shrine.
    Refusal DrawBlood(Player* player)
    {
        InstanceScript* instance = player->GetInstanceScript();
        if (!instance || player->GetMapId() != kMapRagefireChasm)
            return Refusal::NotHeroic;
        Refusal const refusal = ShrineRefusal(StateFor(player, instance));
        if (refusal != Refusal::None)
            return Refused(player, "draw", refusal);
        player->CastSpell(player, SPELL_HM_HUNGERERS_BLOOD, true);
        ChatHandler(player->GetSession()).SendNotification(std::string_view(kDrawnNotice));
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "starving-draw", player->GetName());
        return Refusal::None;
    }

    // `player` uses the pour spot (`source`: the object, or the GM). The pour counts when the instance took the flag;
    // then every carrier's blood is gone. A refused pour keeps it.
    Refusal PourBlood(Player* player, WorldObject* source)
    {
        InstanceScript* instance = player->GetInstanceScript();
        if (!instance || player->GetMapId() != kMapRagefireChasm)
            return Refusal::NotHeroic;
        Refusal const refusal = PourRefusal(StateFor(player, instance));
        if (refusal != Refusal::None)
            return Refused(player, "pour", refusal);
        instance->SetData(DATA_HARD_MODE, 1);       // the flag, its save, the loot bit, his health and line 9
        if (!instance->GetData(DATA_HARD_MODE))
            return Refused(player, "pour", Refusal::Instance);
        instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_HM_HUNGERERS_BLOOD);
        Position const lava(kPourLava.x, kPourLava.y, kPourLava.z);
        if (Creature* stalker = source->SummonCreature(NPC_RFC_STALKER, lava, TEMPSUMMON_TIMED_DESPAWN, kPourLookMs))
            stalker->CastSpell(stalker, SPELL_HM_POUR, true);
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "starving-pour", player->GetName());
        return Refusal::None;
    }
}

// The trigger's objects: not selectable while the trigger is closed for everyone. A click never reaches the engine's
// goober use.
struct RfcStarvingTriggerAI : public GameObjectAI
{
    RfcStarvingTriggerAI(GameObject* go) : GameObjectAI(go) { }

    void UpdateAI(uint32 diff) override
    {
        if (_pollMs > diff)
        {
            _pollMs -= diff;
            return;
        }
        _pollMs = kTriggerPollMs;
        InstanceScript* instance = me->GetInstanceScript();
        if (!instance)
            return;
        bool const open = ClosedFor(DungeonKit::IsHeroicMap(me), TaragamanState(instance),
            instance->GetData(DATA_HARD_MODE) != 0) == Refusal::None;
        bool const flagged = me->HasGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        if (open && flagged)
            me->RemoveGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        else if (!open && !flagged)
            me->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
    }

    bool GossipHello(Player* player, bool reportUse) override
    {
        if (player && !reportUse)       // a report-use follows some clicks
            Used(player);
        return true;
    }

protected:
    virtual void Used(Player* player) = 0;

private:
    uint32 _pollMs = 0;
};

// Blood Shrine 301340 (heroic spawn only)
struct go_rfc_blood_shrine : public RfcStarvingTriggerAI
{
    explicit go_rfc_blood_shrine(GameObject* go) : RfcStarvingTriggerAI(go) { }

protected:
    void Used(Player* player) override { DrawBlood(player); }
};

// The pour spot 301341 (heroic spawn only)
struct go_rfc_pour_spot : public RfcStarvingTriggerAI
{
    explicit go_rfc_pour_spot(GameObject* go) : RfcStarvingTriggerAI(go) { }

protected:
    void Used(Player* player) override { PourBlood(player, me); }
};

// -------------------------------------------------------------------------------------------------------------------
// Blood Globule 300987 (TG8): crawls to Taragaman over the plateau and never fights. The hard mode reads where it is
// (drunk, dead); the unit only moves. A stun, a root or a fear holds it, a slow slows it; it cannot be taunted or
// knocked back (flags_extra). Its way: a straight floor line, through the hub when he is on another arm, the navmesh
// when neither is all floor; one that is off the plateau for kGlobuleOffFloorMs is put back on it. Never evades on its
// own (its fight is his; D4's cleanup despawns it).
// -------------------------------------------------------------------------------------------------------------------

struct npc_rfc_blood_globule : public ScriptedAI
{
    explicit npc_rfc_blood_globule(Creature* creature) : ScriptedAI(creature) { }

    void InitializeAI() override
    {
        me->SetReactState(REACT_PASSIVE);
        ScriptedAI::InitializeAI();
    }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
        me->SetWalk(true);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void EnterEvadeMode(EvadeReason /*why*/) override { }

    void UpdateAI(uint32 diff) override
    {
        if (!me->IsAlive())
            return;
        _aimMs += diff;
        if (_aimMs < kGlobuleAimMs)
            return;
        uint32 const elapsed = _aimMs;
        _aimMs = 0;
        Aim(elapsed);
    }

private:
    void Aim(uint32 elapsed)
    {
        if (me->HasUnitState(UNIT_STATE_NOT_MOVE | UNIT_STATE_LOST_CONTROL | UNIT_STATE_JUMPING))
            return;
        TempSummon* summon = me->ToTempSummon();
        Unit* taragaman = summon ? summon->GetSummonerUnit() : nullptr;
        if (!taragaman || !taragaman->IsAlive())
            return;

        Vec2 const here = DungeonKit::PlaneOf(me);
        Vec2 const him = DungeonKit::PlaneOf(taragaman);
        float const speed = GlobuleSpeed(me->GetMaxNegativeAuraModifier(SPELL_AURA_MOD_DECREASE_SPEED));
        Leg leg = Leg::Path;
        if (OnPlateauFloor(me))
        {
            _offFloorMs = 0;
            leg = GlobuleLeg(here, him);
        }
        else
        {
            _offFloorMs += elapsed;
            if (_offFloorMs >= kGlobuleOffFloorMs)
            {
                _offFloorMs = 0;
                Vec2 const in = ClampInto(kPlateauArenaPolygon, here);
                me->GetMotionMaster()->Clear();
                me->StopMoving();
                me->NearTeleportTo(in.x, in.y, FloorZ(me, in, kHub.z), me->GetOrientation());
                return;
            }
        }

        // Off the plateau the way back is to the hub, never into the air under a leaping Taragaman.
        Vec2 const goal = leg == Leg::ToHub || _offFloorMs ? kHub.XY() : him;
        bool const same = leg == _leg && DungeonKit::Distance(goal, _goal) <= kGlobuleReaimYd
            && std::fabs(speed - _speed) < 0.1f;
        if (same && !me->movespline->Finalized())
            return;
        _leg = leg;
        _goal = goal;
        _speed = speed;
        float const z = FloorZ(me, goal, kHub.z);
        if (leg == Leg::Path)
        {
            me->GetMotionMaster()->MovePoint(1, goal.x, goal.y, z, FORCED_MOVEMENT_WALK, speed);
            return;
        }
        if (DungeonKit::Distance(here, goal) < 0.5f)
            return;
        if (me->GetMotionMaster()->GetCurrentMovementGeneratorType() != IDLE_MOTION_TYPE)
            me->GetMotionMaster()->Clear();
        DungeonKit::MoveAlongFloor(me, GlobulePath(me, here, goal), speed);
    }

    Vec2 _goal{};
    float _speed = 0.f;
    Leg _leg = Leg::Path;
    uint32 _aimMs = kGlobuleAimMs;      // the first step on its first tick
    uint32 _offFloorMs = 0;
};

// -------------------------------------------------------------------------------------------------------------------
// The hard mode for one pull (TaragamanFight.h TaragamanHardMode)
// -------------------------------------------------------------------------------------------------------------------

class StarvingFight : public RfcTaragaman::TaragamanHardMode
{
public:
    void OnEngage(TaragamanFight& fight) override
    {
        Creature* boss = fight.Taragaman();
        SyncTaragaman(boss);        // the pull may come before his first idle tick (a cold load)
        fight.Log("starving-engage", Acore::StringFormat("health={} line={:.0f}% gap={}ms fallback={}ms",
            boss->GetMaxHealth(), Tune::kStarvingLinePct, Tune::kStarvingGapMs,
            Tune::kFeastEveryMs(Mode::HardMode)));
    }

    // Phase 2 first, then the combo, then the Feast's poll: a set piece that is due goes before a new Feast (rule 24:
    // a group that stays under the line never starves the combo; the hold after one keeps the Feast its turn).
    void OnUpdate(TaragamanFight& fight, uint32 diff) override
    {
        uint64 const now = fight.ClockMs();
        if (!_phase2 && Phase2Due(fight.Taragaman()->GetHealthPct()))
            StartPhase2(fight);
        if (_phase2)
        {
            UpdateGlobules(fight);
            if (_waves.Take(now))
                RaiseGlobules(fight);
            switch (_combo.At(now))
            {
                case ComboClock::Due::Felstorm:
                    if (fight.StartFelstorm())
                        ++_combos;
                    break;
                case ComboClock::Due::Nova:
                    fight.StartNova();
                    break;
                case ComboClock::Due::None:
                    break;
            }
        }

        _pollMs += diff;
        if (_pollMs < Tune::kStarvingPollMs)
            return;
        _pollMs %= Tune::kStarvingPollMs;
        PollFeast(fight);
    }

    // The fallback is D4's own Feast timer, in its queue of beats; in phase 2 a due combo goes before it.
    bool FeastByTimer(TaragamanFight const& fight) const override
    {
        return TimerFeastMay(fight.ClockMs(), fight.LastFeastMs(), _combo);
    }

    void OnFeastStart(TaragamanFight& fight, Player* prey) override
    {
        ++_feasts;
        if (!_lineWake)
            ++_fallbacks;
        fight.Log("starving-wake", Acore::StringFormat("prey={} health={:.0f}% why={}", prey->GetName(),
            prey->GetHealthPct(), _lineWake ? "line" : "fallback"));
    }

    void OnFelstormStart(TaragamanFight& fight) override
    {
        _spinning = true;
        uint64 const now = fight.ClockMs();
        _combo.SpinStarted(now > Tune::kFelstormCastMs ? now - Tune::kFelstormCastMs : 0);
    }

    void OnFelstormEnd(TaragamanFight& fight) override
    {
        _spinning = false;
        _combo.SpinEnded(fight.ClockMs());
    }

    void OnNovaStart(TaragamanFight& /*fight*/) override
    {
        _combo.NovaStarted();
    }

    std::optional<Position> FelstormSpot(TaragamanFight& fight) override
    {
        Creature* boss = fight.Taragaman();
        std::optional<Vec2> const spot = FelstormSpotFor(DungeonKit::PlaneOf(boss));
        if (!spot)
            return std::nullopt;
        return DungeonKit::ToPosition(*spot, FloorZ(boss, *spot, kHub.z));
    }

    // TG3: toward a random player of the fight on the plateau, the tank included, inside the disc.
    std::optional<Position> DriftTarget(TaragamanFight& fight) override
    {
        std::vector<Player*> players;
        for (Player* player : fight.FightPlayers())
            if (fight.FeastEligible(player))
                players.push_back(player);
        if (players.empty())
            return std::nullopt;
        Creature* boss = fight.Taragaman();
        Player* player = players[urand(0, static_cast<uint32>(players.size()) - 1)];
        Vec2 const to = DriftClamp(DungeonKit::PlaneOf(player));
        fight.Log("starving-drift", Acore::StringFormat("toward={} from=({:.1f}, {:.1f}) to=({:.1f}, {:.1f}) "
            "spawn-distance={:.1f}", player->GetName(), boss->GetPositionX(), boss->GetPositionY(), to.x, to.y,
            DungeonKit::Distance(DungeonKit::PlaneOf(boss), kTaragamanSpawn.XY())));
        return DungeonKit::ToPosition(to, FloorZ(boss, to, kHub.z));
    }

    // TG9: a globule that died, however far it got.
    void OnSummonDied(TaragamanFight& fight, Creature* summon) override
    {
        if (summon->GetEntry() != NPC_RFC_BLOOD_GLOBULE)
            return;
        Forget(summon->GetGUID());
        ++_killed;
        Burst(fight, summon->GetPosition());
        summon->DespawnOrUnsummon(Ms(kGlobuleCorpseMs));
    }

    void OnEnd(TaragamanFight& fight, bool died) override
    {
        fight.Log("starving-end", Acore::StringFormat("died={} phase={} feasts={} (fallback {}) combos={} waves={} "
            "killed={} drunk={}", died ? 1 : 0, _phase2 ? kPhaseBloodLake : kPhaseHunt, _feasts, _fallbacks, _combos,
            _waveCount, _killed, _drunk));
        _globules.clear();
    }

    // The bots' kill order: the globule nearest to him first; the tank stays on him.
    void DescribeExtra(TaragamanFight& /*fight*/, BossMechanics::Descriptor& d) override
    {
        if (!_phase2)
            return;
        using BossMechanics::Condition;
        using BossMechanics::TargetEntry;
        using BossMechanics::Who;
        for (GlobuleTier const& tier : kGlobuleTiers)
            d.targets.push_back(TargetEntry(NPC_RFC_BLOOD_GLOBULE, tier.priority, Who::Dps,
                Condition::NearUnit(NPC_TARAGAMAN, tier.withinYd)).AoeOk());
        d.targets.push_back(TargetEntry(NPC_RFC_BLOOD_GLOBULE, -1, Who::Tank));
    }

    // `.dbtest rfc starving` entry points: an empty string when fired, otherwise why not.
    std::string TestPhase2(TaragamanFight& fight)
    {
        if (_phase2)
            return "Phase 2 is on already.";
        StartPhase2(fight);
        return {};
    }

    std::string TestGlobules(TaragamanFight& fight)
    {
        if (!_phase2)
            return "The globules are phase 2's (.dbtest rfc starving phase2).";
        RaiseGlobules(fight);
        return {};
    }

    std::string TestBurst(TaragamanFight& fight, Player* at)
    {
        return Burst(fight, at->GetPosition()) ? std::string() : "The burst was not registered.";
    }

    std::string TestCombo(TaragamanFight& fight)
    {
        if (!_phase2)
            return "The combo is phase 2's (.dbtest rfc starving phase2).";
        _combo.Hurry(fight.ClockMs());
        return {};
    }

    std::string TestFeast(TaragamanFight& fight)
    {
        Player* prey = fight.LowestPrey();
        if (!prey)
            return "Nobody alive (and not .gm on) on the plateau within 40 yd of the hub.";
        return fight.StartFeast(prey) ? std::string()
            : "Refused: a beat runs, a set piece is due, or the hold after one (a phase's 2 s) does.";
    }

    std::string State(TaragamanFight& fight) const
    {
        uint64 const now = fight.ClockMs();
        auto in = [now](uint64 due) -> int64 { return static_cast<int64>(due) - static_cast<int64>(now); };
        uint64 const last = fight.LastFeastMs();
        std::string phase2 = "off";
        if (_phase2)
            phase2 = Acore::StringFormat("combo in {}ms, wave in {}ms, globules {}", in(_combo.FelstormDueMs()),
                in(_waves.DueMs()), _globules.size());
        return Acore::StringFormat("health={}/{} phase={} feast: last {}ms ago, {} of them fallback {}; phase 2: {}; "
            "combos={} waves={} killed={} drunk={} gorged={}", fight.Taragaman()->GetHealth(),
            fight.Taragaman()->GetMaxHealth(), _phase2 ? kPhaseBloodLake : kPhaseHunt, last ? now - last : 0, _feasts,
            _fallbacks, phase2, _combos, _waveCount, _killed, _drunk, fight.GorgedStacks());
    }

private:
    // ----------------------------------------------------------------------------------------------------------------
    // TG1
    // ----------------------------------------------------------------------------------------------------------------
    void PollFeast(TaragamanFight& fight)
    {
        Player* prey = fight.LowestPrey();
        if (!prey)
            return;
        if (!LineWake(fight.ClockMs(), fight.LastFeastMs(), prey->GetHealthPct()))
            return;
        _lineWake = true;
        fight.StartFeast(prey);     // refused (a beat, its hold): asked again at the next poll
        _lineWake = false;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Phase 2
    // ----------------------------------------------------------------------------------------------------------------
    void StartPhase2(TaragamanFight& fight)
    {
        _phase2 = true;
        uint64 const now = fight.ClockMs();
        fight.Say(YELL_TARAGAMAN_BLOOD_LAKE);
        fight.NotePhaseChange(kPhaseBloodLake);
        fight.HoldSetPieces(true);
        fight.SetFeastHold(Tune::kPhase2FeastHoldMs);
        _combo.Start(now, _spinning);
        _waves.Start(now);
        fight.RefreshDescriptor();
        for (Point3 const& spot : kBloodLakeSpots)
            if (Creature* stalker = fight.Summon(NPC_RFC_STALKER, Position(spot.x, spot.y, spot.z)))
                stalker->CastSpell(stalker, SPELL_HM_BLOOD_LAKE, true);
    }

    // TG8: four globules, one per arm end; each is in the fight (so nobody leaves combat) and harmless.
    void RaiseGlobules(TaragamanFight& fight)
    {
        Creature* boss = fight.Taragaman();
        fight.Say(EMOTE_TARAGAMAN_GLOBULES);
        ++_waveCount;
        uint32 raised = 0;
        for (Point3 const& start : kGlobuleStarts)
        {
            Vec2 const p = start.XY();
            Creature* globule = fight.Summon(NPC_RFC_BLOOD_GLOBULE, DungeonKit::ToPosition(p,
                FloorZ(boss, p, start.z), DungeonKit::BearingTo(p, kHub.XY())));
            if (!globule)
                continue;
            Mechanic::TrackUnit(boss, globule);
            if (boss->IsAIEnabled)
                boss->AI()->DoZoneInCombat(globule);
            _globules.push_back(globule->GetGUID());
            ++raised;
        }
        fight.Log("starving-globules", Acore::StringFormat("wave={} raised={} up={}", _waveCount, raised,
            _globules.size()));
    }

    // The ones that reached him are drunk: no burst.
    void UpdateGlobules(TaragamanFight& fight)
    {
        Creature* boss = fight.Taragaman();
        for (auto it = _globules.begin(); it != _globules.end();)
        {
            Creature* globule = ObjectAccessor::GetCreature(*boss, *it);
            if (!globule || !globule->IsAlive())
            {
                it = _globules.erase(it);
                continue;
            }
            if (!Drunk(globule->GetExactDist2d(boss), globule->GetPositionZ() - boss->GetPositionZ()))
            {
                ++it;
                continue;
            }
            it = _globules.erase(it);
            ++_drunk;
            fight.Log("starving-drunk", Acore::StringFormat("health={}/{} drunk={}", globule->GetHealth(),
                globule->GetMaxHealth(), _drunk));
            globule->DespawnOrUnsummon();
            fight.Gorge(Tune::kGlobuleDrunkHealPct);
        }
    }

    // TG9: the burst where it died. Not his hit: the Gorged factor does not raise it.
    bool Burst(TaragamanFight& fight, Position const& at)
    {
        Creature* boss = fight.Taragaman();
        ObjectGuid look;
        if (Creature* stalker = fight.Summon(NPC_RFC_STALKER, at, Tune::kGlobuleBurstWarnMs + kBurstStalkerMs))
            look = stalker->GetGUID();
        Map* map = boss->GetMap();
        MechanicRef ref = Mechanic::Circle(boss, at, Tune::kGlobuleBurstRadius, Ms(Tune::kGlobuleBurstWarnMs));
        ref.School(SPELL_SCHOOL_SHADOW).Spell(SPELL_HM_BURST).Damage(Tune::kGlobuleBurstPct)
            .TankDamage(Tune::kGlobuleBurstPct).Weakened().Within(TaragamanFloorBounds()).Tag(TAG_HM_BURST)
            .OnResolve([map, look](BossMechanics::ResolveResult const& result)
            {
                Creature* stalker = !result.fizzled && map ? map->GetCreature(look) : nullptr;
                if (stalker)
                    stalker->CastSpell(stalker, SPELL_HM_BURST_LOOK, true);
                if (!result.fizzled)
                    DungeonKit::LogMechanic(kLogDungeon, kBoss, "starving-burst-hit", std::to_string(
                        result.hits.size()));
            });
        if (!ref.IsValid())
        {
            fight.Log("starving-burst-refused");
            return false;
        }
        fight.Track(ref.Handle());
        fight.Log("starving-burst", Acore::StringFormat("at=({:.1f}, {:.1f}) boss-distance={:.1f}", at.GetPositionX(),
            at.GetPositionY(), boss->GetExactDist2d(at.GetPositionX(), at.GetPositionY())));
        return true;
    }

    void Forget(ObjectGuid guid)
    {
        _globules.erase(std::remove(_globules.begin(), _globules.end(), guid), _globules.end());
    }

    ComboClock _combo;
    WaveClock _waves;
    std::vector<ObjectGuid> _globules;      // alive, on their way
    uint32 _pollMs = 0;
    uint32 _feasts = 0;
    uint32 _fallbacks = 0;
    uint32 _combos = 0;
    uint32 _waveCount = 0;
    uint32 _killed = 0;
    uint32 _drunk = 0;
    bool _phase2 = false;
    bool _spinning = false;
    bool _lineWake = false;                 // the Feast starting now is the poll's
};

// -------------------------------------------------------------------------------------------------------------------
// `.dbtest rfc starving` (the arming itself is `.dbtest rfc taragaman hardmode [0|1]`)
// -------------------------------------------------------------------------------------------------------------------

namespace
{
    // The running pull's hard mode (an error and nullptr when there is none).
    StarvingFight* FindStarving(ChatHandler* handler, TaragamanFight*& fight)
    {
        Creature* boss = RfcTest::FindBoss(handler, NPC_TARAGAMAN);
        if (!boss)
            return nullptr;
        fight = boss->IsAIEnabled ? dynamic_cast<TaragamanFight*>(boss->AI()) : nullptr;
        auto* starving = fight ? dynamic_cast<StarvingFight*>(fight->ActiveHardMode()) : nullptr;
        if (!starving)
            handler->SendErrorMessage("{}", "No Starving pull is running (heroic: pour the blood or `.dbtest rfc "
                "taragaman hardmode`, then pull him).");
        return starving;
    }

    bool Fire(ChatHandler* handler, std::string (StarvingFight::*test)(TaragamanFight&), char const* what)
    {
        TaragamanFight* fight = nullptr;
        StarvingFight* starving = FindStarving(handler, fight);
        if (!starving)
            return false;
        std::string const error = (starving->*test)(*fight);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Starving: {}.", what);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return RfcTest::ShowHardModeInfo(handler);
    }

    bool HandleState(ChatHandler* handler)
    {
        if (!RfcTest::ShowHardModeInfo(handler))
            return false;
        Creature* boss = RfcTest::FindBoss(handler, NPC_TARAGAMAN);
        if (!boss)
            return false;
        auto* fight = boss->IsAIEnabled ? dynamic_cast<TaragamanFight*>(boss->AI()) : nullptr;
        auto* starving = fight ? dynamic_cast<StarvingFight*>(fight->ActiveHardMode()) : nullptr;
        handler->PSendSysMessage("Starving pull: {}", starving ? starving->State(*fight) : Acore::StringFormat(
            "none (health {}/{}, red aura {})", boss->GetHealth(), boss->GetMaxHealth(),
            boss->HasAura(SPELL_HM_STARVING) ? 1 : 0));
        return true;
    }

    // The shrine's and the pour spot's own use by the GM where he stands (their rules; `.gm on` changes nothing).
    bool HandleDraw(ChatHandler* handler)
    {
        if (!RfcTest::RequireRagefireChasm(handler))
            return false;
        Refusal const refusal = DrawBlood(handler->GetPlayer());
        handler->PSendSysMessage("Draw: {} (refusal {}).", refusal == Refusal::None ? "done" : "refused",
            uint32(refusal));
        return true;
    }

    bool HandlePour(ChatHandler* handler)
    {
        if (!RfcTest::RequireRagefireChasm(handler))
            return false;
        Refusal const refusal = PourBlood(handler->GetPlayer(), handler->GetPlayer());
        handler->PSendSysMessage("Pour: {} (refusal {}).", refusal == Refusal::None ? "done" : "refused",
            uint32(refusal));
        return true;
    }

    bool HandleFeast(ChatHandler* handler)
    {
        return Fire(handler, &StarvingFight::TestFeast, "a Starving Feast on the lowest (TG1)");
    }

    bool HandlePhase2(ChatHandler* handler)
    {
        return Fire(handler, &StarvingFight::TestPhase2, "phase 2, the blood lake (TG7, TG8)");
    }

    bool HandleGlobules(ChatHandler* handler)
    {
        return Fire(handler, &StarvingFight::TestGlobules, "a wave of four globules (TG8)");
    }

    bool HandleCombo(ChatHandler* handler)
    {
        return Fire(handler, &StarvingFight::TestCombo, "Felstorm into Nova as soon as no beat runs (TG7)");
    }

    bool HandleBurst(ChatHandler* handler)
    {
        TaragamanFight* fight = nullptr;
        StarvingFight* starving = FindStarving(handler, fight);
        if (!starving)
            return false;
        std::string const error = starving->TestBurst(*fight, handler->getSelectedPlayerOrSelf());
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->SendSysMessage("Starving: a globule's burst at the selected player (TG9).");
        return true;
    }

    ChatCommandTable const& StarvingTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",    HandleState,    SEC_GAMEMASTER, Console::No },
            { "draw",     HandleDraw,     SEC_GAMEMASTER, Console::No },
            { "pour",     HandlePour,     SEC_GAMEMASTER, Console::No },
            { "feast",    HandleFeast,    SEC_GAMEMASTER, Console::No },
            { "phase2",   HandlePhase2,   SEC_GAMEMASTER, Console::No },
            { "globules", HandleGlobules, SEC_GAMEMASTER, Console::No },
            { "combo",    HandleCombo,    SEC_GAMEMASTER, Console::No },
            { "burst",    HandleBurst,    SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_rfc_taragaman_hard_mode()
{
    RfcTaragaman::RegisterTaragamanHardMode([](Creature* /*taragaman*/) { return std::make_unique<StarvingFight>(); });
    RfcTaragaman::RegisterTaragamanIdleHook([](Creature* taragaman) { SyncTaragaman(taragaman); });
    // Line 9 at the pour; his health and look follow at once (D4 runs the idle hook after the action).
    RfcTaragaman::RegisterTaragamanActionHook([](Creature* taragaman, int32 action)
    {
        if (action == ACTION_RFC_HARD_MODE_ARMED && taragaman->IsAIEnabled && taragaman->AI())
            taragaman->AI()->Talk(YELL_TARAGAMAN_POURED);
    });
    RegisterDungeonReworkCreatureAI(npc_rfc_blood_globule, RagefireChasmRework::kInstanceScriptName);
    RegisterDungeonReworkGameObjectAI(go_rfc_blood_shrine, RagefireChasmRework::kInstanceScriptName);
    RegisterDungeonReworkGameObjectAI(go_rfc_pour_spot, RagefireChasmRework::kInstanceScriptName);
    RfcTest::RegisterBoss("starving", StarvingTestCommands());
}
