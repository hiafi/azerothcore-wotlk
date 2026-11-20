/*
 * mod-dungeon-bosses, Blackrock Depths D23: Emperor Dagran Thaurissan (9019), the Imperial Guard (300843) and the
 * Twilight's Hammer Ambassador (300844), "The Royal Couple" (ruling 77: which of them falls first decides the fight).
 * Build spec S4 "Emperor Dagran Thaurissan" (docs/dungeons/blackrock-depths-4-imperial-seat.md, EM1-EM10; rulings
 * 77-80, 88, 90, 91), handoff sections 3.4 (rows D23), 3.5, 3.6, 3.8, 3.9 (`beam-block`), 7 #19. Replaces stock
 * `boss_emperor_dagran_thaurissan` (its CallForHelp room pull and the Avatar of Flame immunity are gone); Moira and the
 * High Priestess are boss_moira_bronzebeard_rework.cpp (one kit on both). Neither has SmartAI (live SELECT 2026-11-17).
 * Bound by apps/dbc-tools source/npcs/blackrock_depths/emperor.py. Pure rules: EmperorLogic.h. The hard mode (D24,
 * the Avatar of Ragnaros) fights on this AI through EmperorFight.h.
 *
 * He runs the whole fight's clock, Moira's Nemesis and Necrosis included (cast through her AI); her Mind Blast is her
 * own. The registry encounter is his (slot 18); Moira is a unit of it (TrackUnit).
 *
 *   The court (both alive)
 *   EM1  Hand of Thaurissan   4 s, then every 12-15 s: a random player (the tank too) in 30 yd, a Fire hit and a
 *                             2 s stun (a copy of 17492)
 *   EM2  Nemesis (Moira)      12 s, then every 25 s (heroic 20 s): Moira's 8 s channel into him, a tick a second:
 *                             every player on the 2 yd beam takes Radiant Burn (5% / 8%), an open tick heals both
 *                             1.5%. The bots' Soak (tag 21, G2's drill row), registered again when the tank walks
 *                             him far enough to make its frozen length wrong (G2's finding)
 *   EM3  Imperial Guard       20 s, then every 30 s (heroic 25 s): 2 elite guards from the wing ends (yell 8); at most
 *                             4 alive, a wave waits while 4 are up (ruling 91)
 *   EM5  Necrosis (H, Moira)  8 s, then every 15 s: a Magic DoT on a random player (dispel expected)
 *   EM6  Ambassadors (H)      from 70% of his health each wave brings a Twilight's Hammer Ambassador: it walks to 20
 *                             yd from him and tethers him (0.5% a second; a blocker takes 3% instead)
 *   EM7  Flamestrike (H)      from 40%, every 12 s: 6 yd under every player and at 3 random floor spots, 2 s, 45% +
 *                             Weakened, then 4 s of burning ground at 8% a second
 *   The tank's Spot           section 7 #19: the main tank holds him 13-19 yd from Moira (she is rooted on the dais)
 *   The enrage (Moira dead)
 *   EM8  Avatar of Flame      yell 9; +25% damage, +60% size, the Flames proc on his melee hits; no immunity
 *   EM9  Firestorm            enrage + 5 s, every 12 s (heroic 10 s): 3 (4) 6 yd circles under random players
 *   EM10 Hammer Slam          enrage + 8 s, every 15 s: a 1.5 s wind-up (emote 13), a 10 yd frontal cone, the tank
 *                             exempt, 40% / 60%, no Weakened
 *   Dagran first              normal (or heroic without D24): a real kill; Moira stands down (stock, the
 *                             Priestess's MoiraGUID bug fixed by the instance). Heroic with D24: Ragnaros Awakens
 *                             (EmperorFight.h, steps 1-6)
 *
 * Boss data: kill order Ambassador, Imperial Guard, Moira / the Priestess, Dagran; Mind Blast on the interrupt list (a
 * reward); Necrosis on the dispel list (heroic, expected). The `rti` kill-order yield is not built (section 7 #13):
 * bots always play Moira first. Every timer runs on the AI's own clock; every firing logs one INFO line
 * "brd emperor <mechanic> ..." (module.dungeonbosses); lambdas the registry keeps capture the map and guids only.
 */

#include "ArenaGuard.h"
#include "BlackrockDepthsKit.h"
#include "BlackrockDepthsRework.h"
#include "BlackrockDepthsTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "EmperorFight.h"
#include "EmperorLogic.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "Spell.h"
#include "SpellInfo.h"
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
using namespace BlackrockDepthsRework;
using namespace BrdEmperor;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBoss = "emperor";

    uint32 constexpr kPullZoneYd = 60;          // pulling either one pulls the other (the dais is 4 yd across them)
    uint32 constexpr kLeaveDespawnMs = 8000;    // a leaving add walks to its wing and is gone by then
    uint32 constexpr kPointStand = 1;
    uint32 constexpr kPointLeave = 2;
    int32 constexpr kActionLeave = 100;         // Dagran -> a guard or an Ambassador (the hard mode's transition)

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(ms);
    }

    void LogEm(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    EmperorHardModeFactory& HardModeFactory()
    {
        static EmperorHardModeFactory factory;
        return factory;
    }

    // The floor under a point: the map's height within 6 yd of `refZ`, else `refZ`.
    float GroundZ(WorldObject const* probe, float x, float y, float refZ)
    {
        float const h = probe->GetMapHeight(x, y, refZ + 2.f);
        if (h <= INVALID_HEIGHT || std::fabs(h - refZ) > 6.f)
            return refZ;
        return h;
    }

    bool IsChanneling(Unit const* caster, uint32 spellId)
    {
        if (!caster)
            return false;
        Spell const* spell = caster->GetCurrentSpell(CURRENT_CHANNELED_SPELL);
        return spell && spell->GetSpellInfo() && spell->GetSpellInfo()->Id == spellId;
    }

    // The nearer wing end of `p` (where a leaving add walks to).
    Point3 const& NearestEntry(Vec2 p)
    {
        return DungeonKit::Distance(p, kGuardEntries[0].XY()) <= DungeonKit::Distance(p, kGuardEntries[1].XY())
            ? kGuardEntries[0] : kGuardEntries[1];
    }

    // An add leaves the fight (the hard mode's transition: "guards and Ambassadors leave"): out of combat, not
    // selectable, walking to its wing; gone a few seconds later.
    void Leave(Creature* me)
    {
        me->InterruptNonMeleeSpells(false);
        me->SetReactState(REACT_PASSIVE);
        me->AttackStop();
        me->CombatStop(true);
        me->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->SetUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
        me->SetControlled(false, UNIT_STATE_ROOT);
        Point3 const& wing = NearestEntry(DungeonKit::PlaneOf(me));
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MovePoint(kPointLeave, wing.x, wing.y, wing.z);
        me->DespawnOrUnsummon(Milliseconds(kLeaveDespawnMs));
    }

    // The players of `me`'s threat list (alive, never a game master).
    std::vector<Player*> ThreatPlayers(Creature* me)
    {
        std::vector<Player*> players;
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
            if (Player* player = ref->GetVictim() ? ref->GetVictim()->ToPlayer() : nullptr)
                if (player->IsAlive() && !player->IsGameMaster())
                    players.push_back(player);
        return players;
    }

    // The players standing on the beam from `from` to `to` (2 yd, on the plane, within one floor of either end).
    std::vector<Player*> OnTheBeam(std::vector<Player*> const& players, Unit const* from, Unit const* to)
    {
        std::vector<Vec2> points;
        std::vector<Player*> candidates;
        float const zLow = std::min(from->GetPositionZ(), to->GetPositionZ()) - 4.f;
        float const zHigh = std::max(from->GetPositionZ(), to->GetPositionZ()) + 4.f;
        for (Player* p : players)
        {
            if (p->GetPositionZ() < zLow || p->GetPositionZ() > zHigh)
                continue;
            candidates.push_back(p);
            points.push_back(DungeonKit::PlaneOf(p));
        }
        std::vector<Player*> out;
        for (std::size_t i : BeamBlockers(DungeonKit::PlaneOf(from), DungeonKit::PlaneOf(to), kBeamWidthYd, points))
            out.push_back(candidates[i]);
        return out;
    }

    // The test commands' forced mechanics (`.dbtest brd emperor ...`; out of combat the GM stands in for the group).
    enum class TestKind : uint8
    {
        Hand,
        Nemesis,
        Wave,
        Necrosis,
        Flamestrike,
        Enrage,
        Firestorm,
        HammerSlam,
        Cage,
        Uncage,
        Clear,
    };
}

void BrdEmperor::RegisterEmperorHardMode(EmperorHardModeFactory factory)
{
    HardModeFactory() = std::move(factory);
}

bool BrdEmperor::HasEmperorHardMode()
{
    return static_cast<bool>(HardModeFactory());
}

std::unique_ptr<EmperorHardMode> BrdEmperor::CreateEmperorHardMode(Creature* boss)
{
    EmperorHardModeFactory const& factory = HardModeFactory();
    return factory ? factory(boss) : nullptr;
}

// ---------------------------------------------------------------------------------------------------------------------
// The Imperial Guard 300843 (EM3): an elite that marches in from a wing end and fights in melee (the template's
// DamageModifier). Summoned by Dagran (his summon list: he puts it in combat with the room and despawns it with the
// fight); it leaves when he rises as the Avatar.
// ---------------------------------------------------------------------------------------------------------------------
struct npc_brd_imperial_guard : public ScriptedAI
{
    explicit npc_brd_imperial_guard(Creature* creature) : ScriptedAI(creature) { }

    void DoAction(int32 action) override
    {
        if (action == kActionLeave && !_leaving)
        {
            _leaving = true;
            Leave(me);
        }
    }

    // A guard that loses its fight is gone (it never walks back to where it was summoned).
    void EnterEvadeMode(EvadeReason /*why*/) override
    {
        me->DespawnOrUnsummon();
    }

    void UpdateAI(uint32 /*diff*/) override
    {
        if (_leaving || !UpdateVictim())
            return;
        DoMeleeAttackIfReady();
    }

private:
    bool _leaving = false;
};

// ---------------------------------------------------------------------------------------------------------------------
// The Twilight's Hammer Ambassador 300844 (EM6, heroic): it walks to its stand (20 yd from Dagran toward its wing),
// roots, and channels the Twilight Tether into him until it dies; a tick a second, its own clock: a player on the 2 yd
// beam takes Twilight Burn (3%), an open tick heals Dagran 0.5% of his health. Never melees. Kill order: first.
// ---------------------------------------------------------------------------------------------------------------------
struct npc_brd_twilight_ambassador : public ScriptedAI
{
    explicit npc_brd_twilight_ambassador(Creature* creature) : ScriptedAI(creature) { }

    // Passive (it never picks a victim: UpdateVictim keeps it in the fight while players are on its threat list) and
    // still: it walks only where it is sent.
    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
        me->SetCombatMovement(false);
    }

    void AttackStart(Unit* /*who*/) override { }

    // Dagran's order, right after the summon: the stand and the unit it tethers.
    void Begin(ObjectGuid dagran, Position const& stand)
    {
        _dagran = dagran;
        _stand = stand;
        WalkToStand();
    }

    void DoAction(int32 action) override
    {
        if (action == kActionLeave && !_leaving)
        {
            _leaving = true;
            Leave(me);
        }
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type != POINT_MOTION_TYPE || id != kPointStand || _leaving)
            return;
        _walking = false;
        me->SetControlled(true, UNIT_STATE_ROOT);
        Tether();
    }

    void EnterEvadeMode(EvadeReason /*why*/) override
    {
        me->DespawnOrUnsummon();
    }

    void UpdateAI(uint32 diff) override
    {
        if (_leaving || !UpdateVictim())
            return;
        _clockMs += diff;
        if (_walking || _clockMs < _nextTickMs)
            return;
        _nextTickMs = _clockMs + kTetherTickMs;

        Creature* dagran = Dagran();
        if (!dagran)
            return;
        // The tank walked him off: walk to a new stand.
        if (me->GetExactDist2d(dagran) > kTetherRangeYd)
        {
            me->InterruptNonMeleeSpells(false);
            me->SetControlled(false, UNIT_STATE_ROOT);
            Point3 const& wing = NearestEntry(DungeonKit::PlaneOf(me));
            Vec2 const at = AmbassadorStand(DungeonKit::PlaneOf(dagran), wing.XY());
            _stand = Position(at.x, at.y, GroundZ(me, at.x, at.y, kFloorZ), 0.f);
            WalkToStand();
            return;
        }
        if (!IsChanneling(me, SPELL_EM_TWILIGHT_TETHER))
        {
            Tether();
            return;
        }
        TetherTick(dagran);
    }

private:
    Creature* Dagran() const
    {
        Creature* dagran = _dagran ? ObjectAccessor::GetCreature(*me, _dagran) : nullptr;
        return dagran && dagran->IsAlive() ? dagran : nullptr;
    }

    void WalkToStand()
    {
        _walking = true;
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MovePoint(kPointStand, _stand.GetPositionX(), _stand.GetPositionY(),
            _stand.GetPositionZ());
    }

    void Tether()
    {
        Creature* dagran = Dagran();
        if (!dagran || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (me->CastSpell(dagran, SPELL_EM_TWILIGHT_TETHER, false) == SPELL_CAST_OK)
            DungeonKit::LogMechanic(kLogDungeon, kBoss, "tether", Acore::StringFormat("at=({:.1f}, {:.1f}) "
                "range={:.1f}", me->GetPositionX(), me->GetPositionY(), me->GetExactDist2d(dagran)));
    }

    // One second of the tether: every blocker burns, or Dagran heals.
    void TetherTick(Creature* dagran)
    {
        std::vector<Player*> const blockers = OnTheBeam(ThreatPlayers(me), me, dagran);
        if (blockers.empty())
        {
            int32 const heal = static_cast<int32>(TickHeal(dagran->GetMaxHealth(), kTetherHealPct));
            me->CastCustomSpell(SPELL_EM_TETHER_HEAL, SPELLVALUE_BASE_POINT0, heal, dagran, true);
            ++_openTicks;
            return;
        }
        for (Player* player : blockers)
            me->CastSpell(player, SPELL_EM_TWILIGHT_BURN, true);
        ++_blockedTicks;
    }

    ObjectGuid _dagran;
    Position _stand;
    uint64 _clockMs = 0;
    uint64 _nextTickMs = 0;
    uint32 _openTicks = 0;
    uint32 _blockedTicks = 0;
    bool _walking = false;
    bool _leaving = false;
};

// ---------------------------------------------------------------------------------------------------------------------
// Emperor Dagran Thaurissan 9019
// ---------------------------------------------------------------------------------------------------------------------
struct boss_emperor_dagran_thaurissan_rework : public BossAI, public EmperorFight
{
private:
    struct Nemesis
    {
        bool active = false;
        uint64 startMs = 0;
        uint64 nextTickMs = 0;
        uint32 ticks = 0;
        uint32 blocked = 0;
        uint32 open = 0;
        MechanicHandle soak;
        float registeredYd = 0.f;
    };

    // A Flamestrike circle's burning ground look, due once its impact lands.
    struct Ground
    {
        Position at;
        uint64 dueMs = 0;
    };

public:
    explicit boss_emperor_dagran_thaurissan_rework(Creature* creature)
        : BossAI(creature, BOSS_EMPEROR), _arena(EmperorArena(), LeashOptions(kBoss)) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Engine hooks
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();       // despawns the summon list (guards, Ambassadors, the looks' stalkers)
        EndHardMode(false);
        Cleanup();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded
        StartFight(who);
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        LogEm("evade", Acore::StringFormat("reason={} phase={}", uint32(why), uint32(_phase)));
        EndHardMode(false);
        Cleanup();
        BossAI::EnterEvadeMode(why);
        // The fight is one encounter: she goes home with him (and leaves her cage).
        if (Creature* moira = Moira())
            if (moira->IsAlive() && moira->IsInCombat() && moira->IsAIEnabled && !moira->IsInEvadeMode())
                moira->AI()->EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        bool const avatar = _phase == Phase::Avatar;
        EndHardMode(true);
        Cleanup();
        BossAI::JustDied(killer);       // slot 18 DONE: the instance records the Avatar kill and Moira saved
        // Stock: she stands down when he falls (the instance keeps her friendly on every load from now on).
        if (Creature* moira = Moira())
            if (moira->IsAlive() && moira->IsAIEnabled)
                moira->AI()->DoAction(ACTION_EM_STAND_DOWN);
        LogEm("death", Acore::StringFormat("avatar={} killer={}", avatar ? 1 : 0,
            killer ? killer->GetName() : std::string("none")));
    }

    void KilledUnit(Unit* victim) override
    {
        if (victim && victim->IsPlayer())
            Talk(YELL_EM_SLAY);
    }

    // Stock: the instance pushes the share of the room's senators dead (a yell per 20%).
    void SetData(uint32 type, uint32 data) override
    {
        if (type != DATA_EMPEROR_SENATORS_DEAD)
            return;
        if (std::optional<uint8> const yell = SenatorYell(data, _senatorYells))
        {
            if (me->IsAlive())
                Talk(*yell);
            ++_senatorYells;
        }
    }

    void DoAction(int32 action) override
    {
        if (action == ACTION_EM_MOIRA_DIED)
            Enrage("moira-died");
    }

    // Guards and Ambassadors join the fight (BossAI: the room's players at 0 threat, rule 11) and the encounter; the
    // looks' stalkers do neither.
    void JustSummoned(Creature* summon) override
    {
        if (!summon)
            return;
        summons.Summon(summon);
        uint32 const entry = summon->GetEntry();
        if (entry == NPC_BRD_IMPERIAL_GUARD || entry == NPC_BRD_TWILIGHT_AMBASSADOR)
        {
            if (me->IsEngaged())
                DoZoneInCombat(summon);
            Mechanic::TrackUnit(me, summon);
            return;
        }
        summon->SetReactState(REACT_PASSIVE);
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*mask*/) override
    {
        if (!_fighting)
            return;
        // Step 1 of the Dagran-first branch: the lethal hit while Moira lives (heroic, D24 registered).
        if (_phase == Phase::Court && damage >= me->GetHealth() && !_awakenPending
            && AwakensOnLethal(_heroic, MoiraStandsInCourt(), HasEmperorHardMode(), _phase, _awakenRefused))
        {
            _lethal.Arm();
            if (_lethal.Intercept(me, damage))
            {
                _awakenPending = true;
                LogEm("lethal-held", Acore::StringFormat("by={}", attacker ? attacker->GetName() : "none"));
            }
        }
        else if (_awakenPending || _phase == Phase::Transition)
            _lethal.Intercept(me, damage);

        if (_hardMode && (_phase == Phase::Transition || _phase == Phase::Avatar))
            _hardMode->OnDamageTaken(*this, attacker, damage);
    }

    // EM8: the Flames proc on each of his melee hits while enraged.
    void DamageDealt(Unit* victim, uint32& /*damage*/, DamageEffectType type, SpellSchoolMask /*mask*/) override
    {
        if (_phase != Phase::Enraged || type != DIRECT_DAMAGE || !victim || victim != me->GetVictim())
            return;
        me->CastSpell(victim, SPELL_EM_FLAMES, true);
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        UpdateGrounds();

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_fighting)
            return;

        if (_awakenPending)
        {
            _awakenPending = false;
            Awaken();
        }

        switch (_phase)
        {
            case Phase::Court:
            case Phase::Enraged:
                CheckThresholds();
                RunBeats();
                UpdateNemesis();
                break;
            case Phase::Transition:
                if (_clockMs >= _awakenAtMs + kTransitionMs)
                    Rise();
                return;     // no swing in the transition
            case Phase::Avatar:
                RunBeats();
                if (_hardMode)
                    _hardMode->OnUpdate(*this, diff);
                if (_hardMode && !_hardMode->Melee(*this))
                    return;
                break;
            default:
                return;
        }
        if (!me->HasUnitState(UNIT_STATE_CASTING))
            DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The pull
    // ----------------------------------------------------------------------------------------------------------------

    void StartFight(Unit* who)
    {
        if (!_heroicForced)
            _heroic = IsHeroicMap(me);
        _heroicForced = false;
        OnBossPull(me, kBoss);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_EMPEROR;
        Mechanic::BeginEncounter(me, options);
        _registered = true;
        _arena.Engage(me);
        _fighting = true;
        _pullMs = _clockMs;
        _phase = Phase::Court;
        _awakenRefused = false;
        _lethal.Reset();
        _lethal.Disarm();       // armed only for the lethal hit of the Dagran-first branch
        _beats.Start(_heroic, _clockMs);
        Talk(AggroYell(_senatorYells));

        // Pulling either pulls both; she is a unit of his encounter (the descriptor's interrupt entry finds her).
        Creature* moira = Moira();
        if (moira && moira->IsAlive() && moira->IsAIEnabled)
        {
            if (!moira->IsInCombat())
            {
                if (who)
                    moira->AI()->AttackStart(who);
                moira->AI()->DoZoneInCombat(moira, kPullZoneYd);
            }
            Mechanic::TrackUnit(me, moira);
        }
        if (!MoiraStandsInCourt())
            Enrage("no-moira");     // a pull without her (she fell in an earlier attempt that he survived)
        Describe();
        LogEm("engage", Acore::StringFormat("heroic={} moira={} hand={}s nemesis={}s guards={}s every={}s "
            "hardmode-registered={}", _heroic ? 1 : 0, MoiraStandsInCourt() ? 1 : 0, kHandFirstMs / 1000,
            kNemesisFirstMs / 1000, kGuardFirstMs / 1000, kGuardEveryMs(_heroic) / 1000,
            HasEmperorHardMode() ? 1 : 0));
    }

    // Boss data (S4 "Bots" / "Boss data"): the kill order Ambassador, Imperial Guard, Moira (or the Priestess),
    // Dagran (0); Mind Blast kicks (a reward); Necrosis dispels (heroic, expected).
    void Describe()
    {
        BossMechanics::Descriptor d;
        d.targets.push_back(BossMechanics::TargetEntry(NPC_BRD_TWILIGHT_AMBASSADOR, 3, BossMechanics::Who::Dps));
        d.targets.push_back(BossMechanics::TargetEntry(NPC_BRD_IMPERIAL_GUARD, 2, BossMechanics::Who::Dps));
        if (_phase == Phase::Court)
        {
            d.targets.push_back(BossMechanics::TargetEntry(NPC_MOIRA, 1, BossMechanics::Who::Dps));
            d.targets.push_back(BossMechanics::TargetEntry(NPC_PRIESTESS, 1, BossMechanics::Who::Dps));
            d.interrupts.emplace_back(NPC_MOIRA, SPELL_EM_MIND_BLAST, 1, Ms(kMindBlastEveryMinMs));
            d.interrupts.emplace_back(NPC_PRIESTESS, SPELL_EM_MIND_BLAST, 1, Ms(kMindBlastEveryMinMs));
        }
        if (_heroic)
            d.dispels.emplace_back(SPELL_EM_NECROSIS, 2);
        Mechanic::Describe(me, std::move(d));
    }

    // The transition and the Avatar phase: nothing of the court is left (the adds left, Moira is caged); D24 adds its
    // own entries.
    void DescribeAvatar()
    {
        BossMechanics::Descriptor d;
        if (_hardMode)
            _hardMode->ConfigureDescriptor(*this, d);
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The clocks
    // ----------------------------------------------------------------------------------------------------------------

    bool BeatOn(Beat beat) const
    {
        if (_phase == Phase::Avatar)
            return _hardMode ? _hardMode->AvatarBeat(*this, beat) : BeatRunsIn(beat, _phase, _heroic);
        return BeatRunsIn(beat, _phase, _heroic);
    }

    void CheckThresholds()
    {
        if (!_heroic)
            return;
        float const pct = me->GetHealthPct();
        if (Crossed(pct, kAmbassadorPct, _ambassadorsArmed))
        {
            _ambassadorsArmed = true;
            LogEm("ambassadors-armed", Acore::StringFormat("health={:.0f}%", pct));
        }
        if (Crossed(pct, kFlamestrikePct, _flamestrikeArmed))
        {
            _flamestrikeArmed = true;
            _beats.ArmFlamestrike(_clockMs);
            LogEm("flamestrike-armed", Acore::StringFormat("health={:.0f}%", pct));
        }
    }

    void RunBeats()
    {
        if (_clockMs < _holdUntilMs)
            return;
        bool const casting = me->HasUnitState(UNIT_STATE_CASTING);

        if (_beats.Due(Beat::TankSpot, _clockMs))
        {
            if (BeatOn(Beat::TankSpot))
                PostTankSpot();
            _beats.Fired(Beat::TankSpot, _clockMs);
        }
        if (_beats.Due(Beat::Nemesis, _clockMs))
        {
            if (!BeatOn(Beat::Nemesis))
                _beats.At(Beat::Nemesis) = 0;
            else if (StartNemesis())
                _beats.Fired(Beat::Nemesis, _clockMs);
            else
                _beats.Retry(Beat::Nemesis, _clockMs);
        }
        if (_beats.Due(Beat::Guards, _clockMs))
        {
            if (!BeatOn(Beat::Guards))
                _beats.At(Beat::Guards) = 0;
            else if (SendWave())
                _beats.Fired(Beat::Guards, _clockMs);
            else
                _beats.Retry(Beat::Guards, _clockMs);
        }
        if (_beats.Due(Beat::Necrosis, _clockMs))
        {
            if (!BeatOn(Beat::Necrosis))
                _beats.At(Beat::Necrosis) = 0;
            else if (CastNecrosis(nullptr))
                _beats.Fired(Beat::Necrosis, _clockMs);
            else
                _beats.Retry(Beat::Necrosis, _clockMs);
        }
        if (_beats.Due(Beat::Flamestrike, _clockMs))
        {
            if (!BeatOn(Beat::Flamestrike))
                _beats.At(Beat::Flamestrike) = 0;
            else if (Flamestrike())
                _beats.Fired(Beat::Flamestrike, _clockMs);
            else
                _beats.Retry(Beat::Flamestrike, _clockMs);
        }
        if (_beats.Due(Beat::Firestorm, _clockMs))
        {
            uint32 every = kFirestormEveryMs(_heroic);
            if (_phase == Phase::Avatar && _hardMode)
                every = _hardMode->FirestormEveryMs(*this, every);
            if (!BeatOn(Beat::Firestorm))
                _beats.At(Beat::Firestorm) = 0;
            else if (Firestorm(0, nullptr))
                _beats.Fired(Beat::Firestorm, _clockMs, every);
            else
                _beats.Retry(Beat::Firestorm, _clockMs);
        }
        // Casts: never over another cast.
        if (_beats.Due(Beat::HammerSlam, _clockMs) && !casting)
        {
            if (!BeatOn(Beat::HammerSlam))
                _beats.At(Beat::HammerSlam) = 0;
            else if (StartHammerSlam())
                _beats.Fired(Beat::HammerSlam, _clockMs);
            else
                _beats.Retry(Beat::HammerSlam, _clockMs);
        }
        if (_beats.Due(Beat::Hand, _clockMs) && !me->HasUnitState(UNIT_STATE_CASTING))
        {
            if (!BeatOn(Beat::Hand))
                _beats.At(Beat::Hand) = 0;
            else if (CastHand(nullptr))
                _beats.Fired(Beat::Hand, _clockMs, urand(kHandEveryMinMs, kHandEveryMaxMs));
            else
                _beats.Retry(Beat::Hand, _clockMs);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EM1 Hand of Thaurissan
    // ----------------------------------------------------------------------------------------------------------------

    Player* PickAny(float maxRange, bool los)
    {
        if (!me->IsEngaged())
            return _testPlayer.IsEmpty() ? nullptr : ObjectAccessor::GetPlayer(*me, _testPlayer);
        DungeonKit::PickRule rule;
        rule.nonTank = false;           // ruling 88: the tank too
        rule.maxRange = maxRange;
        rule.requireLos = los;
        return DungeonKit::PickPlayer(me, rule);
    }

    bool CastHand(Player* forced)
    {
        Player* target = forced ? forced : PickAny(kHandRangeYd, true);
        if (!target || me->CastSpell(target, SPELL_EM_HAND_OF_THAURISSAN, false) != SPELL_CAST_OK)
            return false;
        LogEm("hand", Acore::StringFormat("heroic={} on={} pct={:.0f} stun={}s", _heroic ? 1 : 0, target->GetName(),
            kHandPct(_heroic), kHandStunMs / 1000));
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EM2 Nemesis (Moira's channel; his clock)
    // ----------------------------------------------------------------------------------------------------------------

    // Moira channels into him (her AI casts it and says emote 1); the Soak for the bots is registered as it starts.
    // False: she cannot now (casting, caged, gone).
    bool StartNemesis()
    {
        Creature* moira = Moira();
        if (!moira || !MoiraStandsInCourt() || _nemesis.active || moira->HasUnitState(UNIT_STATE_CASTING))
            return false;
        moira->AI()->DoAction(ACTION_EM_NEMESIS);
        if (!IsChanneling(moira, SPELL_EM_NEMESIS))
        {
            LogEm("nemesis-refused", "she could not channel");
            return false;
        }
        _nemesis = Nemesis{};
        _nemesis.active = true;
        _nemesis.startMs = _clockMs;
        _nemesis.nextTickMs = _clockMs + kNemesisTickMs;
        RegisterBeamSoak(moira, kNemesisSoakWarnMs, kNemesisSoakLiveMs);
        LogEm("nemesis", Acore::StringFormat("heroic={} beam={:.1f}yd burn={:.0f}% heal={:.1f}%", _heroic ? 1 : 0,
            moira->GetExactDist2d(me), kRadiantBurnPct(_heroic), kNemesisHealPct));
        return true;
    }

    // The bots' telegraph: a 2 yd line Soak from her to him, one body (a damage dealer: the tank holds him, the
    // healer heals), `warn` to step in, judged every second for `live`. The script judges the ticks itself.
    void RegisterBeamSoak(Creature* moira, uint32 warn, uint32 live)
    {
        if (_nemesis.soak)
            Mechanic::Cancel(me, _nemesis.soak);
        _nemesis.soak = MechanicHandle();
        _nemesis.registeredYd = 0.f;
        if (live < kNemesisTickMs)
            return;
        BossMechanics::Eligibility dps;
        dps.roles = BossMechanics::Role::Damage;
        MechanicRef ref = Mechanic::Soak(me, BossMechanics::Shapes::Line(BossMechanics::Anchor(moira),
            BossMechanics::Anchor(me), kBeamWidthYd), 1, Ms(warn));
        ref.Eligible(dps).Persistent(Ms(live), Ms(kNemesisTickMs)).Tag(TAG_EM_NEMESIS);
        if (!ref.IsValid())
        {
            LogEm("nemesis-soak-refused");
            return;
        }
        _nemesis.soak = ref.Handle();
        _nemesis.registeredYd = moira->GetExactDist2d(me);
        Track(_nemesis.soak);
    }

    void UpdateNemesis()
    {
        if (!_nemesis.active)
            return;
        // The channel ends on its own at 8 s, as the last tick comes due: a channel gone before that was broken.
        Creature* moira = Moira();
        bool const ending = _clockMs + kNemesisTickMs / 4 >= _nemesis.startMs + kNemesisChannelMs;
        if (!moira || !moira->IsAlive() || (!IsChanneling(moira, SPELL_EM_NEMESIS) && !ending))
        {
            EndNemesis("broken");
            return;
        }
        while (_nemesis.active && _clockMs >= _nemesis.nextTickMs)
        {
            _nemesis.nextTickMs += kNemesisTickMs;
            NemesisTick(moira);
            if (++_nemesis.ticks >= kNemesisTicks)
            {
                EndNemesis("done");
                return;
            }
        }
        // G2's finding: the Soak's length is frozen at registration; the tank walking him makes it wrong.
        uint64 const endMs = _nemesis.startMs + kNemesisChannelMs;
        uint32 const left = _clockMs < endMs ? uint32(endMs - _clockMs) : 0;
        if (left >= kBeamRefreshMinLeftMs && BeamNeedsRefresh(_nemesis.registeredYd, moira->GetExactDist2d(me)))
        {
            uint64 const judgedFrom = _nemesis.startMs + kNemesisSoakWarnMs;
            uint32 const warn = _clockMs + kBeamRefreshWarnMs < judgedFrom ? uint32(judgedFrom - _clockMs)
                : kBeamRefreshWarnMs;
            LogEm("nemesis-refresh", Acore::StringFormat("{:.1f}yd -> {:.1f}yd", _nemesis.registeredYd,
                moira->GetExactDist2d(me)));
            RegisterBeamSoak(moira, warn, left > warn ? left - warn : 0);
        }
    }

    // One second of the channel: every player on the beam burns; nobody: both heal.
    void NemesisTick(Creature* moira)
    {
        std::vector<Player*> const blockers = OnTheBeam(FightPlayers(), moira, me);
        if (blockers.empty())
        {
            ++_nemesis.open;
            moira->CastCustomSpell(SPELL_EM_NEMESIS_HEAL, SPELLVALUE_BASE_POINT0,
                static_cast<int32>(TickHeal(me->GetMaxHealth(), kNemesisHealPct)), me, true);
            moira->CastCustomSpell(SPELL_EM_NEMESIS_HEAL, SPELLVALUE_BASE_POINT0,
                static_cast<int32>(TickHeal(moira->GetMaxHealth(), kNemesisHealPct)), moira, true);
            return;
        }
        ++_nemesis.blocked;
        for (Player* player : blockers)
            moira->CastSpell(player, SPELL_EM_RADIANT_BURN, true);
    }

    void EndNemesis(char const* why)
    {
        if (!_nemesis.active)
            return;
        if (_nemesis.soak)
            Mechanic::Cancel(me, _nemesis.soak);
        LogEm("nemesis-end", Acore::StringFormat("why={} ticks={} blocked={} open={}", why, _nemesis.ticks,
            _nemesis.blocked, _nemesis.open));
        _nemesis = Nemesis{};
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EM3 Imperial Guard, EM6 the Ambassadors (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    uint32 GuardsAlive()
    {
        uint32 n = 0;
        for (ObjectGuid const& guid : summons)
            if (Creature* add = ObjectAccessor::GetCreature(*me, guid))
                if (add->GetEntry() == NPC_BRD_IMPERIAL_GUARD && add->IsAlive())
                    ++n;
        return n;
    }

    // The wave due now: 2 guards from the wing ends (fewer when 4 would be passed), an Ambassador from 70% (heroic).
    // False: 4 guards are up (the wave waits, ruling 91), or the summon failed.
    bool SendWave()
    {
        Wave const wave = WaveFor(GuardsAlive(), _heroic && _ambassadorsArmed);
        if (wave.waits)
            return false;
        uint32 const coin = urand(0, 1);
        uint32 sent = 0;
        for (uint32 i = 0; i < wave.guards; ++i)
        {
            Point3 const& wing = kGuardEntries[GuardEntryFor(i, wave.guards, coin)];
            if (me->SummonCreature(NPC_BRD_IMPERIAL_GUARD, wing.x, wing.y, wing.z, 0.f,
                TEMPSUMMON_CORPSE_TIMED_DESPAWN, 5000))
                ++sent;
        }
        bool ambassador = false;
        if (wave.ambassador)
            ambassador = SendAmbassador(kGuardEntries[urand(0, 1)]);
        if (!sent && !ambassador)
            return false;
        Talk(YELL_EM_GUARDS);
        LogEm("guards", Acore::StringFormat("heroic={} sent={} alive={} ambassador={}", _heroic ? 1 : 0, sent,
            GuardsAlive(), ambassador ? 1 : 0));
        return true;
    }

    bool SendAmbassador(Point3 const& wing)
    {
        Creature* add = me->SummonCreature(NPC_BRD_TWILIGHT_AMBASSADOR, wing.x, wing.y, wing.z, 0.f,
            TEMPSUMMON_CORPSE_TIMED_DESPAWN, 5000);
        if (!add)
            return false;
        Vec2 const at = AmbassadorStand(DungeonKit::PlaneOf(me), wing.XY());
        Position const stand(at.x, at.y, GroundZ(me, at.x, at.y, kFloorZ), 0.f);
        if (add->IsAIEnabled)
            if (auto* ai = dynamic_cast<npc_brd_twilight_ambassador*>(add->AI()))
                ai->Begin(me->GetGUID(), stand);
        return true;
    }

    void SendAddsAway()
    {
        for (ObjectGuid const& guid : summons)
            if (Creature* add = ObjectAccessor::GetCreature(*me, guid))
                if (add->IsAlive() && add->IsAIEnabled
                    && (add->GetEntry() == NPC_BRD_IMPERIAL_GUARD || add->GetEntry() == NPC_BRD_TWILIGHT_AMBASSADOR))
                    add->AI()->DoAction(kActionLeave);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EM5 Necrosis (heroic; Moira casts it)
    // ----------------------------------------------------------------------------------------------------------------

    bool CastNecrosis(Player* forced)
    {
        Creature* moira = Moira();
        if (!moira || !MoiraStandsInCourt())
            return false;
        Player* target = forced ? forced : PickAny(100.f, false);
        if (!target)
            return false;
        moira->AI()->SetGUID(target->GetGUID(), GUID_EM_NECROSIS);
        if (!target->HasAura(SPELL_EM_NECROSIS))
            return false;       // refused (her school locked by a kick, say): again in a second
        LogEm("necrosis", Acore::StringFormat("on={} pct={:.0f}/s for={}s", target->GetName(), kNecrosisTickPct,
            kNecrosisMs / 1000));
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EM7 Flamestrike (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    std::optional<Position> RandomFloorSpot(std::vector<Vec2> const& taken)
    {
        DungeonKit::FloorSpotRules rules;
        rules.near = DungeonKit::PlaneOf(me);
        rules.minRange = kFlamestrikeSpotMinYd;
        rules.maxRange = kFlamestrikeSpotMaxYd;
        rules.awayFrom = taken;
        rules.minFromAway = kFlamestrikeRadiusYd;
        DungeonKit::FloorProbe probe;
        probe.z = kFloorZ;
        probe.zBand = 3.f;
        DungeonKit::Arena const arena = EmperorArena();
        return DungeonKit::PickFloorSpot(me, &arena, rules, probe);
    }

    bool PlaceFlamestrike(Position const& at)
    {
        DungeonKit::ImpactSpec impact;
        impact.shape = BossMechanics::Shapes::Circle(at, kFlamestrikeRadiusYd);
        impact.warn = Ms(kFlamestrikeWarnMs);
        impact.pct = kFlamestrikeHitPct;
        impact.tankPct = kFlamestrikeHitPct;
        impact.school = SPELL_SCHOOL_FIRE;
        impact.spellId = SPELL_EM_FLAMESTRIKE;
        impact.weakened = true;
        impact.tag = TAG_EM_FLAMESTRIKE;
        DungeonKit::LingerSpec linger;
        linger.duration = Ms(kFlamestrikeBurnMs);
        linger.tick = Ms(kFlamestrikeBurnTickMs);
        linger.pct = kFlamestrikeBurnPct;
        linger.school = SPELL_SCHOOL_FIRE;
        linger.spellId = SPELL_EM_FLAMESTRIKE_BURN;
        linger.slow = false;
        linger.tag = TAG_EM_FLAMESTRIKE_BURN;
        MechanicHandle const handle = DungeonKit::ImpactThenLinger(me, impact, linger);
        if (!handle)
            return false;
        Track(handle);
        _grounds.push_back({ at, _clockMs + kFlamestrikeWarnMs });
        return true;
    }

    // One round: a circle under every player of the fight (the tank too) and 3 at random floor spots.
    bool Flamestrike()
    {
        std::vector<Player*> const players = me->IsEngaged() ? FightPlayers() : TestPlayers();
        std::vector<Vec2> taken;
        uint32 placed = 0;
        for (Player* p : players)
        {
            Position const at(p->GetPositionX(), p->GetPositionY(),
                GroundZ(me, p->GetPositionX(), p->GetPositionY(), p->GetPositionZ()), 0.f);
            if (PlaceFlamestrike(at))
            {
                ++placed;
                taken.push_back(DungeonKit::PlaneOf(p));
            }
        }
        uint32 random = 0;
        for (uint32 i = 0; i < kFlamestrikeRandomSpots; ++i)
            if (std::optional<Position> const spot = RandomFloorSpot(taken))
                if (PlaceFlamestrike(*spot))
                {
                    ++random;
                    taken.push_back({ spot->GetPositionX(), spot->GetPositionY() });
                }
        if (!placed && !random)
            return false;
        me->CastSpell(me, SPELL_EM_FLAMESTRIKE_LOOK, true);
        LogEm("flamestrike", Acore::StringFormat("players={} random={} circles={} pct={:.0f} burn={:.0f}/s",
            placed, random, FlamestrikeCircles(placed), kFlamestrikeHitPct, kFlamestrikeBurnPct));
        return true;
    }

    // The burning ground's look, once each impact landed: a stalker with the 6 yd lava pool for the burn's 4 s.
    void UpdateGrounds()
    {
        for (auto it = _grounds.begin(); it != _grounds.end();)
        {
            if (_clockMs < it->dueMs)
            {
                ++it;
                continue;
            }
            if (TempSummon* stalker = me->SummonCreature(NPC_BRD_STALKER, it->at, TEMPSUMMON_TIMED_DESPAWN,
                kFlamestrikeBurnMs))
                stalker->CastSpell(stalker, SPELL_EM_FLAMESTRIKE_GROUND, true);
            it = _grounds.erase(it);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EM8 the enrage, EM9 Firestorm, EM10 Hammer Slam
    // ----------------------------------------------------------------------------------------------------------------

    // Moira fell (or was never there at the pull): the standard enrage.
    void Enrage(char const* why)
    {
        if (_phase != Phase::Court)
            return;
        _phase = Phase::Enraged;
        EndNemesis("enrage");
        _beats.Enrage(_clockMs);
        me->CastSpell(me, SPELL_EM_AVATAR_OF_FLAME, true);
        Talk(YELL_EM_ENRAGE);
        if (_tankSpot)
            Mechanic::Cancel(me, _tankSpot);
        _tankSpot = MechanicHandle();
        Describe();
        LogEm("enrage", Acore::StringFormat("why={} heroic={} damage=+{:.0f}% firestorm={}s slam={}s", why,
            _heroic ? 1 : 0, kEnrageDamagePct, kFirestormAfterMs / 1000, kHammerSlamAfterMs / 1000));
    }

    uint32 Firestorm(uint32 count, Player* forced) override
    {
        if (!count)
        {
            count = kFirestormCount(_heroic);
            if (_phase == Phase::Avatar && _hardMode)
                count = _hardMode->FirestormCount(*this, count);
        }
        std::vector<Player*> targets;
        if (forced)
            targets.push_back(forced);
        if (me->IsEngaged() && targets.size() < count)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = false;
            if (forced)
                rule.exclude.push_back(forced->GetGUID().GetRawValue());
            for (Player* p : DungeonKit::PickPlayers(me, rule, count - uint32(targets.size())))
                targets.push_back(p);
        }
        else if (!me->IsEngaged() && targets.empty())
            targets = TestPlayers();
        float const pct = kFirestormPct(_heroic);
        uint32 placed = 0;
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        for (Player* p : targets)
        {
            Position const at(p->GetPositionX(), p->GetPositionY(),
                GroundZ(me, p->GetPositionX(), p->GetPositionY(), p->GetPositionZ()), 0.f);
            MechanicRef ref = Mechanic::Circle(me, at, kFirestormRadiusYd, Ms(kFirestormWarnMs));
            ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_FIRE).Spell(SPELL_EM_FIRESTORM).Weakened()
                .Tag(TAG_EM_FIRESTORM)
                .OnResolve([map, guid, at](BossMechanics::ResolveResult const& r)
                {
                    Creature* boss = map ? map->GetCreature(guid) : nullptr;
                    if (boss && !r.fizzled)
                        boss->CastSpell(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(),
                            SPELL_EM_FIRESTORM_LOOK, true);
                });
            if (!ref.IsValid())
                continue;
            Track(ref.Handle());
            ++placed;
        }
        if (placed)
            LogEm("firestorm", Acore::StringFormat("heroic={} phase={} circles={} pct={:.0f}", _heroic ? 1 : 0,
                uint32(_phase), placed, pct));
        return placed;
    }

    // The 1.5 s wind-up (emote 13), then the 10 yd frontal cone; the tank is exempt (a Frontal). False: casting.
    bool StartHammerSlam()
    {
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return false;
        if (me->CastSpell(me, SPELL_EM_HAMMER_SLAM_CAST, false) != SPELL_CAST_OK)
            return false;
        float const pct = kHammerSlamPct(_heroic);
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        MechanicRef ref = Mechanic::Cone(me, me, kHammerSlamAngleDeg, kHammerSlamLengthYd, Ms(kHammerSlamCastMs),
            BossMechanics::TankExempt::Yes);
        ref.Damage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_EM_HAMMER_SLAM).Tag(TAG_EM_HAMMER_SLAM)
            .OnResolve([map, guid](BossMechanics::ResolveResult const& r)
            {
                Creature* boss = map ? map->GetCreature(guid) : nullptr;
                if (!boss || r.fizzled)
                    return;
                float const o = boss->GetOrientation();
                float const reach = kHammerSlamLengthYd * 0.5f;
                boss->CastSpell(boss->GetPositionX() + std::cos(o) * reach, boss->GetPositionY() + std::sin(o) * reach,
                    boss->GetPositionZ(), SPELL_EM_HAMMER_SLAM_LOOK, true);
            });
        if (!ref.IsValid())
        {
            me->InterruptNonMeleeSpells(false);
            LogEm("hammer-slam-refused");
            return false;
        }
        Track(ref.Handle());
        Talk(EMOTE_EM_HAMMER_SLAM);
        LogEm("hammer-slam", Acore::StringFormat("heroic={} pct={:.0f} cone={:.0f}deg/{:.0f}yd", _heroic ? 1 : 0, pct,
            kHammerSlamAngleDeg, kHammerSlamLengthYd));
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The tank's Spot (section 7 #19)
    // ----------------------------------------------------------------------------------------------------------------

    void PostTankSpot()
    {
        Unit* victim = me->GetVictim();
        Player* tank = victim ? victim->ToPlayer() : nullptr;
        if (!tank || tank->IsGameMaster())
            return;
        if (_tankSpot)
            Mechanic::Cancel(me, _tankSpot);
        std::unordered_map<ObjectGuid, Position> spots;
        spots[tank->GetGUID()] = Position(kTankSpot.x, kTankSpot.y, GroundZ(me, kTankSpot.x, kTankSpot.y, kFloorZ),
            0.f);
        MechanicRef ref = Mechanic::Spot(me, spots, Ms(kTankSpotEveryMs), kTankSpotRadiusYd);
        ref.NoTelegraph().Tag(TAG_EM_TANK_SPOT);
        _tankSpot = ref.Handle();
        Track(_tankSpot);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Dagran-first branch (EmperorFight.h steps 2, 3, 5, 6)
    // ----------------------------------------------------------------------------------------------------------------

    // Step 2: the transition (he is held at 1 health already).
    void Awaken()
    {
        // Moira may have fallen on the same tick (Moira first after all): no branch.
        bool const moira = MoiraStandsInCourt();
        if (moira)
            _hardMode = CreateEmperorHardMode(me);
        if (_hardMode && instance)
            instance->SetData(DATA_AVATAR, 1);
        if (!_hardMode || !instance || instance->GetData(DATA_AVATAR) != 1)
        {
            // Refused (Moira gone, no factory, wave 2 unbound, not heroic, the slot not IN_PROGRESS): the branch is a
            // real kill after all. He stays at 1 health until the next hit, which kills him: the latch keeps
            // DamageTaken from re-arming the hold for the rest of this pull (R-2-C m1).
            _awakenRefused = true;
            LogEm("awaken-refused", Acore::StringFormat("moira={} factory={} flag={}", moira ? 1 : 0,
                _hardMode ? 1 : 0, instance ? instance->GetData(DATA_AVATAR) : 0));
            _hardMode.reset();
            _lethal.Disarm();
            return;
        }
        _phase = Phase::Transition;
        _awakenAtMs = _clockMs;
        _beats.Stop();
        EndNemesis("awaken");
        if (_tankSpot)
            Mechanic::Cancel(me, _tankSpot);
        _tankSpot = MechanicHandle();
        me->InterruptNonMeleeSpells(false);
        me->SetCombatMovement(false);
        me->GetMotionMaster()->Clear();
        SendAddsAway();
        CageMoira("awaken");
        Talk(YELL_EM_RAGNAROS_AWAKENS);
        DescribeAvatar();
        LogEm("awaken", Acore::StringFormat("transition={}s", kTransitionMs / 1000));
        _hardMode->OnAwaken(*this);
    }

    // Step 3: the Avatar rises (D24); his death is real from now on.
    void Rise()
    {
        if (_hardMode)
            _hardMode->OnRise(*this);
        _lethal.Disarm();
        _phase = Phase::Avatar;
        _beats.Avatar(_clockMs, _hardMode ? _hardMode->FirstFirestormMs(*this) : kFirestormAfterMs);
        DescribeAvatar();
        LogEm("avatar-rises", Acore::StringFormat("health={}", me->GetMaxHealth()));
    }

    // Steps 5 and 6: D24 undoes its changes (death, evade or reset).
    void EndHardMode(bool died)
    {
        if (!_hardMode)
            return;
        _hardMode->OnEnd(*this, died);
        _hardMode.reset();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EmperorFight (D24's view)
    // ----------------------------------------------------------------------------------------------------------------

    Creature* Dagran() override
    {
        return me;
    }

    Creature* Moira() override
    {
        if (!instance)
            return nullptr;
        ObjectGuid const guid = instance->GetGuidData(DATA_MOIRA);
        return guid ? ObjectAccessor::GetCreature(*me, guid) : nullptr;
    }

    bool Heroic() const override
    {
        return _heroic;
    }

    Phase CurrentPhase() const override
    {
        return _phase;
    }

    EmperorHardMode* ActiveHardMode() override
    {
        return _hardMode.get();
    }

    uint64 FightMs() const override
    {
        return _fighting ? _clockMs - _pullMs : 0;
    }

    uint64 SinceAwakenMs() const override
    {
        return _awakenAtMs && _clockMs >= _awakenAtMs ? _clockMs - _awakenAtMs : 0;
    }

    std::vector<Player*> FightPlayers() override
    {
        return ThreatPlayers(me);
    }

    bool MoiraCaged() const override
    {
        return _moiraCaged;
    }

    void CageMoira(char const* why) override
    {
        Creature* moira = Moira();
        if (!moira || !moira->IsAlive() || !moira->IsAIEnabled)
            return;
        moira->AI()->DoAction(ACTION_EM_CAGE);
        _moiraCaged = true;
        LogEm("moira-caged", why);
    }

    void UncageMoira(char const* why) override
    {
        if (!_moiraCaged)
            return;
        _moiraCaged = false;
        if (Creature* moira = Moira())
            if (moira->IsAlive() && moira->IsAIEnabled)
                moira->AI()->DoAction(ACTION_EM_UNCAGE);
        LogEm("moira-uncaged", why);
    }

    void HoldBeats(uint64 untilMs) override
    {
        _holdUntilMs = std::max(_holdUntilMs, _pullMs + untilMs);
    }

    void Track(MechanicHandle handle) override
    {
        if (!handle)
            return;
        _registered = true;     // a registry encounter of ours exists now (a `.dbtest` one included)
        _live.push_back(handle);
        if (_live.size() > 128)     // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 64);
    }

    void TrackSummon(Creature* summon) override
    {
        if (summon)
            _hardSummons.push_back(summon->GetGUID());
    }

    void Log(char const* mechanic, std::string const& detail) override
    {
        LogEm(mechanic, detail);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // State
    // ----------------------------------------------------------------------------------------------------------------

    // Moira can still play her part: alive, on the dais, not caged and not standing down.
    bool MoiraStandsInCourt()
    {
        Creature* moira = Moira();
        return moira && moira->IsAlive() && !_moiraCaged && moira->GetFaction() != kFactionFriend;
    }

    // Out of combat the GM of a test command stands in for the group.
    std::vector<Player*> TestPlayers()
    {
        std::vector<Player*> out;
        if (Player* gm = _testPlayer.IsEmpty() ? nullptr : ObjectAccessor::GetPlayer(*me, _testPlayer))
            out.push_back(gm);
        return out;
    }

    // The pull's state: nothing pending, no stalker, no aura of the fight (Reset, evade, death, a new pull). The
    // registry's encounter ends too.
    void Cleanup()
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        if (_registered)
        {
            Mechanic::EndEncounter(me);
            _registered = false;
        }
        for (ObjectGuid const& guid : _hardSummons)
            if (Creature* summon = ObjectAccessor::GetCreature(*me, guid))
                summon->DespawnOrUnsummon();
        _hardSummons.clear();
        _grounds.clear();
        UncageMoira("cleanup");
        _moiraCaged = false;
        _nemesis = Nemesis{};
        _tankSpot = MechanicHandle();
        _beats = Beats{};
        _phase = Phase::Idle;
        _fighting = false;
        _awakenPending = false;
        _awakenRefused = false;
        _awakenAtMs = 0;
        _holdUntilMs = 0;
        _pullMs = _clockMs;
        _ambassadorsArmed = false;
        _flamestrikeArmed = false;
        _lethal.Reset();
        _lethal.Disarm();
        me->RemoveAurasDueToSpell(SPELL_EM_AVATAR_OF_FLAME);
        me->SetCombatMovement(true);
        if (instance)
        {
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_EM_HAND_OF_THAURISSAN);
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_EM_NECROSIS);
        }
        _arena.Reset();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brd emperor` entry points
    // ----------------------------------------------------------------------------------------------------------------
public:
    // An empty string when fired; otherwise why not. `gm` stands in for the group out of combat.
    std::string TestFire(TestKind kind, Player* gm)
    {
        _testPlayer = gm ? gm->GetGUID() : ObjectGuid::Empty;
        switch (kind)
        {
            case TestKind::Hand:
                if (!CastHand(me->IsEngaged() ? nullptr : gm))
                    return "No Hand of Thaurissan: nobody in 30 yd and in sight, or casting.";
                break;
            case TestKind::Nemesis:
                if (!_fighting)
                    return "Nemesis runs on his clock: pull him first.";
                if (!StartNemesis())
                    return "Moira cannot channel now (casting, caged, dead or standing down).";
                break;
            case TestKind::Wave:
                if (!_fighting)
                    return "The guards join a fight: pull him first.";
                if (!SendWave())
                    return "The wave waits: 4 guards are up (ruling 91).";
                break;
            case TestKind::Necrosis:
                if (!CastNecrosis(gm))
                    return "No Necrosis: Moira cannot cast it now.";
                break;
            case TestKind::Flamestrike:
                if (!Flamestrike())
                    return "The registry refused every circle.";
                break;
            case TestKind::Enrage:
                if (_phase != Phase::Court)
                    return "Only from the court phase (both alive, in combat).";
                Enrage("test");
                break;
            case TestKind::Firestorm:
                if (!Firestorm(0, me->IsEngaged() ? nullptr : gm))
                    return "No circle placed (nobody to pick).";
                break;
            case TestKind::HammerSlam:
                if (!StartHammerSlam())
                    return "He is casting.";
                break;
            case TestKind::Cage:
                CageMoira("test");
                break;
            case TestKind::Uncage:
                UncageMoira("test");
                break;
            case TestKind::Clear:
                if (me->IsEngaged())
                {
                    // Mid-pull: a cleanup alone would leave him idle in combat (R-2-C n2); the evade does the
                    // cleanup and takes Moira home with him.
                    EnterEvadeMode(EVADE_REASON_OTHER);
                    break;
                }
                EndHardMode(false);
                Cleanup();
                break;
        }
        return {};
    }

    // `.dbtest brd emperor heroic <0|1>`: the heroic form on a normal map (and back) until the end of the next pull.
    void TestHeroic(bool heroic)
    {
        _heroic = heroic;
        _heroicForced = true;
        _beats.heroic = heroic;
    }

    std::string TestState()
    {
        auto left = [this](Beat b) -> std::string
        {
            uint64 const at = _beats.At(b);
            return at ? std::to_string(at > _clockMs ? (at - _clockMs) / 1000 : 0) + "s" : "-";
        };
        return Acore::StringFormat("emperor heroic={} phase={} hand={} nemesis={}{} guards={} (alive {}) necrosis={} "
            "flamestrike={} firestorm={} slam={} ambassadors={} caged={} hardmode={} registered={} live={}",
            _heroic ? 1 : 0, uint32(_phase), left(Beat::Hand), left(Beat::Nemesis), _nemesis.active ? " (on)" : "",
            left(Beat::Guards), GuardsAlive(), left(Beat::Necrosis), left(Beat::Flamestrike), left(Beat::Firestorm),
            left(Beat::HammerSlam), _ambassadorsArmed ? 1 : 0, _moiraCaged ? 1 : 0, _hardMode ? 1 : 0,
            HasEmperorHardMode() ? 1 : 0, _live.size());
    }

private:
    DungeonKit::ArenaGuard _arena;
    DungeonKit::LethalGuard _lethal;
    std::unique_ptr<EmperorHardMode> _hardMode;
    Beats _beats;
    Nemesis _nemesis;
    Phase _phase = Phase::Idle;
    bool _heroic = false;
    bool _heroicForced = false;     // `.dbtest ... heroic`: kept through the next pull
    bool _fighting = false;
    bool _registered = false;       // a registry encounter of ours exists
    bool _awakenPending = false;    // the lethal hit was held: the transition starts on the next tick
    bool _awakenRefused = false;    // the instance refused the awakening this pull: the next lethal hit is real
    bool _moiraCaged = false;
    bool _ambassadorsArmed = false; // heroic, 70%
    bool _flamestrikeArmed = false; // heroic, 40%
    uint64 _clockMs = 0;            // the AI's own clock: nothing here waits for a cast bar
    uint64 _pullMs = 0;
    uint64 _awakenAtMs = 0;
    uint64 _holdUntilMs = 0;
    uint32 _senatorYells = 0;
    MechanicHandle _tankSpot;
    std::vector<MechanicHandle> _live;
    std::vector<Ground> _grounds;
    GuidVector _hardSummons;
    ObjectGuid _testPlayer;
};

namespace
{
    boss_emperor_dagran_thaurissan_rework* EmperorAI(ChatHandler* handler)
    {
        Creature* boss = BrdTest::FindBoss(handler, NPC_EMPEROR);
        auto* ai = boss && boss->IsAIEnabled ? dynamic_cast<boss_emperor_dagran_thaurissan_rework*>(boss->AI())
            : nullptr;
        if (!ai && boss)
            handler->SendErrorMessage("{} does not run the reworked script.", boss->GetName());
        return ai;
    }

    bool Fire(ChatHandler* handler, TestKind kind, char const* ok)
    {
        boss_emperor_dagran_thaurissan_rework* ai = EmperorAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestFire(kind, handler->GetPlayer());
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->SendSysMessage(ok);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowBossInfo(handler, NPC_EMPEROR, BOSS_EMPEROR);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_emperor_dagran_thaurissan_rework* ai = EmperorAI(handler);
        if (!ai)
            return false;
        handler->SendSysMessage(ai->TestState());
        return true;
    }

    bool HandleHand(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Hand, "Hand of Thaurissan: a Fire hit and a 2 s stun.");
    }

    bool HandleNemesis(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Nemesis, "Nemesis: Moira's 8 s beam into him (2 yd).");
    }

    bool HandleWave(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Wave, "A guard wave from the wing ends (an Ambassador from 70% on heroic).");
    }

    bool HandleNecrosis(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Necrosis, "Necrosis on you: 6% a second for 10 s (Magic).");
    }

    bool HandleFlamestrike(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Flamestrike, "Flamestrike: under every player and 3 random spots.");
    }

    bool HandleEnrage(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Enrage, "The enrage: Avatar of Flame, Firestorm 5 s, Hammer Slam 8 s.");
    }

    bool HandleFirestorm(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Firestorm, "Firestorm: 6 yd circles under random players.");
    }

    bool HandleSlam(ChatHandler* handler)
    {
        return Fire(handler, TestKind::HammerSlam, "Hammer Slam: a 1.5 s wind-up, then the 10 yd cone.");
    }

    bool HandleCage(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Cage, "Moira is caged (the hard mode's look and state).");
    }

    bool HandleUncage(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Uncage, "The cage breaks.");
    }

    bool HandleClear(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Clear, "Cleared.");
    }

    bool HandleHeroic(ChatHandler* handler, Optional<uint32> on)
    {
        boss_emperor_dagran_thaurissan_rework* ai = EmperorAI(handler);
        if (!ai)
            return false;
        ai->TestHeroic(!on || *on != 0);
        handler->SendSysMessage("The heroic form is set until the end of the next pull.");
        return true;
    }

    ChatCommandTable const& BossEmperorDagranThaurissanTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",        HandleInfo,        SEC_GAMEMASTER, Console::No },
            { "state",       HandleState,       SEC_GAMEMASTER, Console::No },
            { "hand",        HandleHand,        SEC_GAMEMASTER, Console::No },
            { "nemesis",     HandleNemesis,     SEC_GAMEMASTER, Console::No },
            { "wave",        HandleWave,        SEC_GAMEMASTER, Console::No },
            { "necrosis",    HandleNecrosis,    SEC_GAMEMASTER, Console::No },
            { "flamestrike", HandleFlamestrike, SEC_GAMEMASTER, Console::No },
            { "enrage",      HandleEnrage,      SEC_GAMEMASTER, Console::No },
            { "firestorm",   HandleFirestorm,   SEC_GAMEMASTER, Console::No },
            { "slam",        HandleSlam,        SEC_GAMEMASTER, Console::No },
            { "cage",        HandleCage,        SEC_GAMEMASTER, Console::No },
            { "uncage",      HandleUncage,      SEC_GAMEMASTER, Console::No },
            { "clear",       HandleClear,       SEC_GAMEMASTER, Console::No },
            { "heroic",      HandleHeroic,      SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_emperor_dagran_thaurissan_rework()
{
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_emperor_dagran_thaurissan_rework,
            BlackrockDepthsRework::kInstanceScriptName);
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_brd_imperial_guard, BlackrockDepthsRework::kInstanceScriptName);
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_brd_twilight_ambassador, BlackrockDepthsRework::kInstanceScriptName);
    BrdTest::RegisterBoss("emperor", BossEmperorDagranThaurissanTestCommands());
}
