/*
 * mod-dungeon-bosses, Zul'Farrak D4a: the Sandfury Executioner (7274) and the Block, stage 1 of the Pyramid, normal and
 * heroic. Build spec: SP 1346-1432 (PY1-PY3, PY15, PY16), design SP 1180-1281 (rulings 21-23, 46); handoff section 3.5
 * row D4a, sections 3.6, 3.8 (the top), section 7 #11 A (the stage machine: S0's), #12 A, #32 A, #43 A (a, c), #44 A.
 * Replaces SmartAI 7274 (dropped by rev_skeleton_zul_farrak.sql: the aggro line, Berserker Stance on aggro, Cleave,
 * the kill line; all four kept below). Bound by apps/dbc-tools source/npcs/zul_farrak/sandfury_executioner.py;
 * numbers in BlockLogic.h, health in ZulFarrakRework.h Health; the Pyramid-wide pieces in PyramidFight.h.
 *
 * He is stage 1 of the Pyramid, not a BossAI: the instance writes slot 5 (his pull sends DATA_PYRAMID_START 1, his
 * evade DATA_PYRAMID_FAIL 1, his death wins the stage). The crew are CR's: the prisoner is torn, chained, spared and
 * executed only through BlyCrew.h (rule 28).
 *
 *   PY1 Block    first at 10 s, then every 20 s (heroic gaps 18, 16, 14 ... s, floor 5 s: section 7 #43 A (a)); one
 *                at a time. He yells line 2 naming a random caged fighter (Bly, Raven, Oro or Murta; never Weegli),
 *                tears them from the cage and chains them 2.5 yd behind him (ZfCrew::TakePrisoner); once chained, the
 *                rope (a stalker at his feet, the channel fields, SV 9275), the 4 s Behead bar (Physical, not
 *                kickable) and a 2 yd registry Soak (1 body, tank included; heroic: wound-free bots only) on the
 *                prisoner. At the bar's end one player inside takes the axe (a wound-free one first, then the
 *                nearest): 40% / 60% Physical of the reference row (the tank row on the tank), heroic 150% on a
 *                soaker still carrying Grievous Wound; the prisoner jumps back to the cage. Nobody inside: the
 *                prisoner dies (ZfCrew::ExecutePrisoner); the instance counts the Offering (normal) or 30 Blood
 *                Price (heroic).
 *   PY2 Wound    heroic: the axe leaves Grievous Wound on its soaker (3% a second until healed to 95%, PyramidFight.h).
 *   PY3 / PY16   Offerings (normal) and Blood Price (heroic) on him, from the instance's counts (PyramidFight.h
 *                PyramidBuffs, run by this WP's stage director BlockStage).
 *   PY15         Berserker Stance on aggro, Cleave every 7 to 11 s, melee (stock values; heroic melee is WP-H's).
 *   Arena        PyramidTopArena() (the top and the landing) with LeashOptions.
 *
 * Every firing logs one INFO line "zf-build block <mechanic> ..."; `.dbtest zf block <subcommand>` fires one.
 */

#include "ArenaGuard.h"
#include "BlockLogic.h"
#include "BlyCrew.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MechanicDescriptor.h"
#include "MechanicRegistry.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "PyramidFight.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ZulFarrakKit.h"
#include "ZulFarrakRework.h"
#include "ZulFarrakTestCommand.h"
#include <cmath>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ZulFarrakRework;
using namespace ZfBlock;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;

namespace
{
    char const* const kBossKey = "block";
    uint8 constexpr kSchoolPhysical = 0;            // SPELL_SCHOOL_NORMAL
    // The stalker that holds the rope: gone on its own if a cleanup ever misses it.
    uint32 constexpr kStalkerLifeMs = 15000;

    char const* StepName(uint8 step)
    {
        switch (step)
        {
            case 0: return "idle";
            case 1: return "tearing";
            case 2: return "casting";
            default: return "?";
        }
    }
}

// Sandfury Executioner 7274
struct boss_sandfury_executioner_rework : public ScriptedAI
{
    explicit boss_sandfury_executioner_rework(Creature* creature)
        : ScriptedAI(creature), _arena(PyramidTopArena(), LeashOptions(kBossKey)), _top(PyramidTopArena())
    {
    }

    void Reset() override
    {
        Cleanup("reset");
    }

    void JustEngagedWith(Unit* who) override
    {
        ScriptedAI::JustEngagedWith(who);

        Cleanup("pull");        // a `.dbtest zf block` mechanic out of combat may have left something behind
        _heroic = DungeonKit::IsHeroicMap(me);
        _engaged = true;
        _cleaveAt = urand(Tune::kCleaveFirstMinMs, Tune::kCleaveFirstMaxMs);

        OnBossPull(me, kBossKey);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_PYRAMID;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        Talk(SAY_AGGRO);
        me->CastSpell(me, SPELL_BERSERKER_STANCE, true);
        if (InstanceScript* instance = me->GetInstanceScript())
        {
            instance->SetData(DATA_PYRAMID_START, PYRAMID_STAGE_BLOCK);     // refused unless it is the stage in play
            ZfPyramid::ApplySandfuryBuff(me, instance);
        }
        Log("engage", Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f}) crew={} candidates={}",
            _heroic ? 1 : 0, me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), CrewAlive(),
            Candidates()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Log("evade", Acore::StringFormat("reason={}", uint32(why)));
        Cleanup("evade");
        ScriptedAI::EnterEvadeMode(why);
        // After the base: he is out of combat, so the instance's wipe does not evade him a second time.
        if (InstanceScript* instance = me->GetInstanceScript())
            instance->SetData(DATA_PYRAMID_FAIL, PYRAMID_STAGE_BLOCK);
    }

    void JustDied(Unit* /*killer*/) override
    {
        Cleanup("death");
        Log("death", Acore::StringFormat("blocks={} crew={}", _blocksDone, CrewAlive()));
    }

    // Stock "Justice is done!" (SmartAI 7274 event 5, cooldown 5 s): a player, or a prisoner under the axe.
    void KilledUnit(Unit* victim) override
    {
        if (!victim || (!victim->IsPlayer() && !CrewMemberOf(victim->ToCreature())))
            return;
        if (_killLineAt && _clock.now < _killLineAt)
            return;
        _killLineAt = _clock.now + Tune::kKillLineCooldownMs;
        Talk(SAY_KILL);
    }

    // The bar is not kickable (InterruptFlags 0, PreventionType 0) and his immunity set holds the controls that stop
    // casts. AzerothCore calls OnSpellFailed only from an interrupt (Unit::InterruptSpell: his death, an evade, a
    // script's InterruptNonMeleeSpells), which gives the Block up here (rule 15); a bar that fails at its own end
    // never reaches this hook and needs nothing from it: the axe runs on his clock.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_PY_BEHEAD_BAR && _step == Step::Casting)
            AbortBlock("bar-failed");
    }

    void DoAction(int32 action) override
    {
        if (action != ACTION_ZF_PYRAMID_STAGE)
            return;
        InstanceScript* instance = me->GetInstanceScript();
        if (!instance || !_engaged)
            return;
        uint32 const stage = instance->GetData(DATA_PYRAMID_STAGE);
        bool const running = instance->GetData(DATA_PYRAMID_RUNNING) != 0;
        if (stage != PYRAMID_STAGE_BLOCK || !running)
            Log("stage", Acore::StringFormat("stage={} running={} (engaged outside the Block)",
                kPyramidStageNames[std::min<uint32>(stage, PYRAMID_STAGE_DONE)], running ? 1 : 0));
    }

    void UpdateAI(uint32 diff) override
    {
        ZulFarrak::NoAssist(me);        // rule 27, LESSONS L1: every tick, before UpdateVictim
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_engaged)
            return;

        // The fight clock moves every tick, cast bar or not.
        _clock.Advance(diff);
        UpdateBlock();
        if (!_engaged || !me->IsAlive())
            return;

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (_clock.now >= _cleaveAt && me->GetVictim())
        {
            DoCastVictim(SPELL_CLEAVE);
            _cleaveAt = _clock.now + urand(Tune::kCleaveMinMs, Tune::kCleaveMaxMs);
        }
        DoMeleeAttackIfReady();
    }

    // ---- `.dbtest zf block` --------------------------------------------------------------------------------------

    bool Engaged() const { return _engaged; }

    // A Block now (on `member` when given and free); false when one runs or nobody can be taken.
    bool TestBlock(std::optional<uint32> member)
    {
        if (!_engaged || _step != Step::Idle)
            return false;
        _clock.busy = false;
        _clock.exhausted = false;
        _clock.nextDue = _clock.now;
        return TryStartBlock(member, "gm");
    }

    std::string TestState()
    {
        InstanceScript* instance = me->GetInstanceScript();
        ZfPyramid::PyramidRead const r = ZfPyramid::ReadPyramid(instance);
        return Acore::StringFormat("engaged={} heroic={} now={} next={} started={} done={} step={} prisoner={} "
            "candidates={} crew={} stage={} running={} offerings={} bloodprice={} bleeding={} buff={}",
            _engaged ? 1 : 0, _heroic ? 1 : 0, _clock.now, _clock.nextDue, _clock.started, _blocksDone,
            StepName(uint8(_step)), _step == Step::Idle ? "-" : kCrewNames[_member], Candidates(), CrewAlive(),
            kPyramidStageNames[std::min<uint32>(r.stage, PYRAMID_STAGE_DONE)], r.running ? 1 : 0, r.offerings,
            r.bloodPrice, ZfPyramid::CountBleeding(me->GetMap()),
            DungeonKit::Stacks(me, r.heroic ? uint32(SPELL_PY_BLOOD_PRICE) : uint32(SPELL_PY_OFFERINGS)));
    }

private:
    enum class Step : uint8
    {
        Idle    = 0,
        Tearing = 1,    // the prisoner jumps from the cage to the chain
        Casting = 2,    // the bar, the rope and the Soak
    };

    // ---- PY1 the Block -------------------------------------------------------------------------------------------

    void UpdateBlock()
    {
        switch (_step)
        {
            case Step::Idle:
                if (_clock.Due() && !me->HasUnitState(UNIT_STATE_CASTING))
                    TryStartBlock(std::nullopt, "due");
                break;
            case Step::Tearing:
            {
                ZfCrew::BlyCrewAI* ai = PrisonerAI();
                if (!ai || !ai->Me()->IsAlive()
                    || (ai->Prisoner() != ZfCrew::PrisonerState::Torn
                        && ai->Prisoner() != ZfCrew::PrisonerState::Chained))
                {
                    AbortBlock("prisoner-lost");
                    break;
                }
                if (ai->Prisoner() == ZfCrew::PrisonerState::Chained || _clock.now >= _tornAt + Tune::kChainWaitMs)
                    StartBehead(ai->Me());
                break;
            }
            case Step::Casting:
            {
                ZfCrew::BlyCrewAI* ai = PrisonerAI();
                if (!ai || !ai->Me()->IsAlive())
                {
                    AbortBlock("prisoner-lost");
                    break;
                }
                if (_clock.now >= _castAt + Tune::kBeheadCastMs)
                    ResolveBlock(ai->Me());
                break;
            }
        }
    }

    bool TryStartBlock(std::optional<uint32> forced, char const* why)
    {
        InstanceScript* instance = me->GetInstanceScript();
        if (!instance)
            return false;
        uint32 const candidates = Candidates();
        if (!candidates)
        {
            if (!(CrewAlive() & kCrewFighters))
            {
                _clock.Exhaust();
                Log("none-left", Acore::StringFormat("blocks={} (every fighter lost: no more Blocks)", _blocksDone));
            }
            else
                _clock.Retry();     // a prisoner still jumping back to the cage
            return false;
        }
        std::optional<uint32> member;
        if (forced && (candidates & CrewBit(*forced)))
            member = forced;
        else
            member = PickPrisoner(candidates, urand(0, 1023));
        if (!member)
            return false;

        Position const chain = ChainSpot();
        if (!ZfCrew::TakePrisoner(instance, *member, chain))
        {
            Log("take-refused", Acore::StringFormat("prisoner={} why={}", kCrewNames[*member], why));
            _clock.Retry();
            return false;
        }
        _clock.Start(_heroic);
        _step = Step::Tearing;
        _member = *member;
        _tornAt = _clock.now;
        Creature* prisoner = ZfCrew::CrewAI(instance, *member) ? ZfCrew::CrewAI(instance, *member)->Me() : nullptr;
        Talk(YELL_BLOCK, prisoner);
        Log("take", Acore::StringFormat("prisoner={} block={} why={} chain=({:.1f}, {:.1f}, {:.1f}) next_in={} "
            "heroic={}", kCrewNames[*member], _clock.started, why, chain.GetPositionX(), chain.GetPositionY(),
            chain.GetPositionZ(), _clock.nextDue - _clock.now, _heroic ? 1 : 0));
        return true;
    }

    // Chained (or the wait ran out): the rope, the bar and the Soak on the prisoner.
    void StartBehead(Creature* prisoner)
    {
        me->StopMoving();
        me->SetFacingToObject(prisoner);
        SpawnRope(prisoner);
        DungeonKit::CastBar(me, SPELL_PY_BEHEAD_BAR, prisoner);
        MechanicRef ref = Mechanic::Soak(me, prisoner, Tune::kSoakRadiusYd, 1, Milliseconds(Tune::kBeheadCastMs));
        // Players only (a pet is never the soaker); heroic: wound-free only (section 7 #43 A (c)).
        BossMechanics::Eligibility who = _heroic ? ZfPyramid::WoundFree() : BossMechanics::Eligibility{};
        who.playersOnly = true;
        ref.ZTolerance(Tune::kSoakZToleranceYd).MissedSoak(BossMechanics::MissedSoakMode::Never)
            .Within(BlockFloorBounds()).Eligible(who).Tag(TAG_BLOCK);
        _soak = ref.Handle();
        _castAt = _clock.now;
        _step = Step::Casting;
        Log("behead", Acore::StringFormat("prisoner={} chained={} wait={} at=({:.1f}, {:.1f}, {:.1f})",
            kCrewNames[_member], PrisonerAI() && PrisonerAI()->Prisoner() == ZfCrew::PrisonerState::Chained ? 1 : 0,
            _clock.now - _tornAt, prisoner->GetPositionX(), prisoner->GetPositionY(), prisoner->GetPositionZ()));
    }

    // The axe falls: one soaker takes it and the prisoner goes back, or nobody did and the prisoner dies.
    void ResolveBlock(Creature* prisoner)
    {
        InstanceScript* instance = me->GetInstanceScript();
        std::vector<Player*> players;
        std::vector<SoakerCandidate> candidates;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player || !player->IsAlive() || player->IsGameMaster() || !player->IsInWorld())
                continue;
            players.push_back(player);
            candidates.push_back({ player->GetExactDist2d(prisoner), player->GetPositionZ() - prisoner->GetPositionZ(),
                ZfPyramid::HasWound(player) });
        }
        me->CastSpell(prisoner, SPELL_PY_BEHEAD_LOOK, true);
        std::optional<SoakerPick> const pick = PickSoaker(candidates);
        ++_blocksDone;
        if (pick)
        {
            Player* soaker = players[pick->index];
            float const pct = BeheadPct(_heroic, pick->wounded);
            DungeonKit::RegistryHitSpec spec;
            spec.pct = pct;
            spec.tankPct = pct;
            spec.school = kSchoolPhysical;
            spec.spellId = SPELL_PY_BEHEAD;
            spec.weakened = false;      // a soak (SP PY1)
            spec.rider = _heroic ? uint32(SPELL_PY_GRIEVOUS_WOUND) : 0u;
            spec.tag = TAG_BEHEAD_HIT;
            Track(DungeonKit::RegistryHit(me, GuidSet{ soaker->GetGUID() }, spec));
            if (_heroic)
                me->CastSpell(soaker, SPELL_PY_GRIEVOUS_LOOK, true);
            bool const spared = instance && ZfCrew::SparePrisoner(instance, _member);
            Log("soaked", Acore::StringFormat("prisoner={} soaker={} pct={:.0f} wounded={} tank={} spared={} "
                "inside={} block={}", kCrewNames[_member], soaker->GetName(), pct, pick->wounded ? 1 : 0,
                me->GetVictim() == soaker ? 1 : 0, spared ? 1 : 0, Inside(candidates), _blocksDone));
        }
        else
        {
            bool const executed = instance && ZfCrew::ExecutePrisoner(instance, _member, me);
            if (instance)
                ZfPyramid::ApplySandfuryBuff(me, instance);     // the instance counted the loss in Unit::Kill
            ZfPyramid::PyramidRead const r = ZfPyramid::ReadPyramid(instance);
            Log("executed", Acore::StringFormat("prisoner={} executed={} offerings={} bloodprice={} crew={} block={}",
                kCrewNames[_member], executed ? 1 : 0, r.offerings, r.bloodPrice, CrewAlive(), _blocksDone));
        }
        EndBlock();
    }

    // The Block given up before the axe (the prisoner gone, the bar ended early): the prisoner goes back if alive.
    void AbortBlock(char const* why)
    {
        if (_step == Step::Idle)
            return;
        Log("abort", Acore::StringFormat("prisoner={} step={} why={}", kCrewNames[_member], StepName(uint8(_step)),
            why));
        bool const casting = _step == Step::Casting;
        if (InstanceScript* instance = me->GetInstanceScript())
            if (ZfCrew::CurrentPrisoner(instance) == _member)
                ZfCrew::SparePrisoner(instance, _member);
        EndBlock();
        if (casting && me->IsAlive() && me->HasUnitState(UNIT_STATE_CASTING))
            me->InterruptNonMeleeSpells(false);
    }

    void EndBlock()
    {
        if (_soak)
            Mechanic::Cancel(me, _soak);
        _soak = MechanicHandle();
        DespawnRope();
        _step = Step::Idle;
        _clock.End();
    }

    // Behind him (away from his victim) first, kChainDistYd out, on the top's floor near his height and in his sight;
    // else at his feet.
    Position ChainSpot()
    {
        Vec2 const boss{ me->GetPositionX(), me->GetPositionY() };
        float away = me->GetOrientation() + float(M_PI);
        if (Unit* victim = me->GetVictim())
            away = DungeonKit::BearingTo({ victim->GetPositionX(), victim->GetPositionY() }, boss);
        float const myZ = me->GetPositionZ();
        for (Vec2 const& p : ChainSpotCandidates(boss, away))
        {
            float const z = me->GetMapHeight(p.x, p.y, myZ + 2.f);
            if (z <= INVALID_HEIGHT + 1.f || std::fabs(z - myZ) > Tune::kChainZBandYd)
                continue;
            if (!_top.Contains(p, z) || !me->IsWithinLOS(p.x, p.y, z + 1.f))
                continue;
            return Position(p.x, p.y, z, DungeonKit::BearingTo(p, boss));
        }
        return Position(me->GetPositionX(), me->GetPositionY(), myZ, me->GetOrientation());
    }

    // The rope from his feet to the prisoner (SV 9275 through the channel fields of a stalker; never cast).
    void SpawnRope(Creature* prisoner)
    {
        DespawnRope();
        Creature* stalker = me->SummonCreature(NPC_ZF_PYRAMID_STALKER, me->GetPosition(),
            TEMPSUMMON_TIMED_DESPAWN, kStalkerLifeMs);
        if (!stalker)
            return;
        stalker->SetGuidValue(UNIT_FIELD_CHANNEL_OBJECT, prisoner->GetGUID());
        stalker->SetUInt32Value(UNIT_CHANNEL_SPELL, SPELL_PY_CHAIN);
        _rope = stalker->GetGUID();
    }

    void DespawnRope()
    {
        if (_rope.IsEmpty())
            return;
        if (Creature* stalker = ObjectAccessor::GetCreature(*me, _rope))
        {
            stalker->SetGuidValue(UNIT_FIELD_CHANNEL_OBJECT, ObjectGuid::Empty);
            stalker->SetUInt32Value(UNIT_CHANNEL_SPELL, 0);
            stalker->DespawnOrUnsummon();
        }
        _rope.Clear();
    }

    // ---- helpers ---------------------------------------------------------------------------------------------------

    ZfCrew::BlyCrewAI* PrisonerAI()
    {
        InstanceScript* instance = me->GetInstanceScript();
        return instance ? ZfCrew::CrewAI(instance, _member) : nullptr;
    }

    uint32 Candidates()
    {
        InstanceScript* instance = me->GetInstanceScript();
        return instance ? ZfCrew::PrisonerCandidates(instance) : 0;
    }

    uint32 CrewAlive() const
    {
        InstanceScript const* instance = me->GetInstanceScript();
        return instance ? instance->GetData(DATA_CREW_ALIVE) : 0;
    }

    static uint32 Inside(std::vector<SoakerCandidate> const& candidates)
    {
        uint32 n = 0;
        for (SoakerCandidate const& c : candidates)
            if (InsideSoak(c))
                ++n;
        return n;
    }

    void Log(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossKey, mechanic, detail);
    }

    void Track(MechanicHandle handle)
    {
        if (handle)
            _live.push_back(handle);
    }

    // Boss data (SP "Boss data"): heroic, Grievous Wound carriers are healed on to 95% (BM-1 healUntil). Nothing to
    // kick (the bar is not kickable), nothing to dispel (the wound is not dispellable), no adds.
    void Describe()
    {
        BossMechanics::Descriptor d;
        ZfPyramid::AddWoundHealRule(d, _heroic);
        Mechanic::Describe(me, std::move(d));
    }

    // The pull's state, gone (RB-1): the Block (the prisoner back to the cage, the rope, the Soak), every registry
    // handle, the clock, the latches, his buff. The players' wounds are the stage director's (a wipe clears them, a
    // win carries them into the Stair).
    void Cleanup(char const* why)
    {
        if (_step != Step::Idle)
            AbortBlock(why);
        DespawnRope();
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        if (_soak)
            Mechanic::Cancel(me, _soak);
        _soak = MechanicHandle();
        _clock = BlockClock{};
        _step = Step::Idle;
        _cleaveAt = 0;
        _killLineAt = 0;
        _tornAt = 0;
        _castAt = 0;
        _blocksDone = 0;
        _engaged = false;
        _arena.Reset();
        ZfPyramid::RemoveSandfuryBuff(me);
    }

    DungeonKit::ArenaGuard _arena;
    Arena _top;
    BlockClock _clock;
    Step _step = Step::Idle;
    uint32 _member = 0;
    uint32 _tornAt = 0;
    uint32 _castAt = 0;
    uint32 _cleaveAt = 0;
    uint32 _killLineAt = 0;
    uint32 _blocksDone = 0;
    MechanicHandle _soak;
    ObjectGuid _rope;
    std::vector<MechanicHandle> _live;
    bool _heroic = false;
    bool _engaged = false;
};

// The chain and lane stalker 301019 (D4a's rope; D4b's lane markers may use it too): invisible, inert.
struct npc_zf_pyramid_stalker : public NullCreatureAI
{
    explicit npc_zf_pyramid_stalker(Creature* creature) : NullCreatureAI(creature) { }
};

// PY2 Grievous Wound 213963 (heroic): the kit's spell_dungeon_refflat_periodic sets each tick (3% of the reference
// row, the tank row on the tank); this ends it once the carrier is healed to 95% or more (the tick deals nothing then).
// PyramidFight.h PyramidBuffs also clears it at every 250 ms poll while a stage runs.
class spell_zf_pyramid_grievous_wound : public AuraScript
{
    PrepareAuraScript(spell_zf_pyramid_grievous_wound);

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Unit* owner = GetUnitOwner();
        if (!owner || !ZfBlock::WoundClears(owner->GetHealthPct()))
            return;
        PreventDefaultAction();
        Remove(AURA_REMOVE_BY_DEFAULT);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_zf_pyramid_grievous_wound::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE);
    }
};

// Stage 1's director (ZulFarrakKit.h PyramidStageDirector): the Sandfury watch on the Executioner while the Block
// runs (Offerings, Blood Price, the wounds). The Block itself is his AI.
class BlockStage : public ZfPyramid::PyramidStage
{
public:
    explicit BlockStage(InstanceScript* instance) : ZfPyramid::PyramidStage(instance, PYRAMID_STAGE_BLOCK) { }

    void OnStart(bool restart) override
    {
        ZfPyramid::PyramidStage::OnStart(restart);
        if (Creature* executioner = Instance()->GetCreature(kGuidExecutioner))
            Buffs().Track(executioner);
        ZfPyramid::PyramidRead const r = ZfPyramid::ReadPyramid(Instance());
        DungeonKit::LogMechanic(kLogDungeon, kBossKey, "stage-start", Acore::StringFormat(
            "restart={} offerings={} bloodprice={} heroic={}", restart ? 1 : 0, r.offerings, r.bloodPrice,
            r.heroic ? 1 : 0));
    }

    void OnEnd(bool won) override
    {
        ZfPyramid::PyramidStage::OnEnd(won);
        DungeonKit::LogMechanic(kLogDungeon, kBossKey, "stage-end", won ? "won" : "lost");
    }
};

namespace
{
    boss_sandfury_executioner_rework* FindExecutionerAI(ChatHandler* handler)
    {
        Creature* boss = ZfTest::FindBoss(handler, NPC_EXECUTIONER);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_sandfury_executioner_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "The Executioner is not running boss_sandfury_executioner_rework.");
        return ai;
    }

    // The selected player, else the GM.
    Player* TestTarget(ChatHandler* handler)
    {
        if (Player* selected = handler->getSelectedPlayer())
            return selected;
        return handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
    }

    std::optional<uint32> FighterByName(std::string const& name)
    {
        for (uint32 m = 0; m < kCrewCount; ++m)
            if (m != CREW_WEEGLI && StringEqualI(name, kCrewNames[m]))
                return m;
        return std::nullopt;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return ZfTest::ShowBossInfo(handler, NPC_EXECUTIONER, BOSS_PYRAMID);
    }

    // `.dbtest zf block state`: the Block's clock, the prisoner, the Offerings / Blood Price and the wounds.
    bool HandleState(ChatHandler* handler)
    {
        boss_sandfury_executioner_rework* ai = FindExecutionerAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Executioner: {}", ai->TestState());
        return true;
    }

    // `.dbtest zf block block [bly|raven|oro|murta]`: a Block now (PY1), on the named fighter when free.
    bool HandleBlock(ChatHandler* handler, Optional<std::string> member)
    {
        boss_sandfury_executioner_rework* ai = FindExecutionerAI(handler);
        if (!ai)
            return false;
        if (!ai->Engaged())
        {
            handler->SendErrorMessage("{}", "The Executioner must be in combat.");
            return false;
        }
        std::optional<uint32> forced;
        if (member)
        {
            forced = FighterByName(*member);
            if (!forced)
            {
                handler->SendErrorMessage("{}", "Usage: .dbtest zf block block [bly|raven|oro|murta]");
                return false;
            }
        }
        if (!ai->TestBlock(forced))
        {
            handler->SendErrorMessage("{}", "Refused: a Block is running, or no caged fighter is free (see the log).");
            return false;
        }
        handler->PSendSysMessage("{}", "Executioner: a Block (PY1).");
        return true;
    }

    // `.dbtest zf block wound`: Grievous Wound on the selected player (or you), heroic only (PY2).
    bool HandleWound(ChatHandler* handler)
    {
        boss_sandfury_executioner_rework* ai = FindExecutionerAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        Creature* boss = ZfTest::FindBoss(handler, NPC_EXECUTIONER);
        if (!boss || !ZfPyramid::ApplyGrievousWound(boss, target))
        {
            handler->SendErrorMessage("{}", "Refused: Grievous Wound is heroic only (or the target is dead).");
            return false;
        }
        handler->PSendSysMessage("Executioner: Grievous Wound on {} (PY2).", target->GetName());
        return true;
    }

    // `.dbtest zf block bloodprice <n>`: the Blood Price total (heroic, PY16); the watch shows it within a second.
    bool HandleBloodPrice(ChatHandler* handler, uint32 total)
    {
        InstanceScript* instance = ZfTest::GmInstance(handler);
        if (!instance)
            return false;
        if (!instance->instance->IsHeroic())
        {
            handler->SendErrorMessage("{}", "Blood Price is heroic only.");
            return false;
        }
        instance->SetData(DATA_BLOOD_PRICE, total);
        if (Creature* executioner = instance->GetCreature(kGuidExecutioner))
            ZfPyramid::ApplySandfuryBuff(executioner, instance);
        handler->PSendSysMessage("Blood Price: {} (+{}% damage done).", instance->GetData(DATA_BLOOD_PRICE),
            BloodPriceDamagePct(instance->GetData(DATA_BLOOD_PRICE)));
        return true;
    }

    ChatCommandTable const& BlockTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,       SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,      SEC_GAMEMASTER, Console::No },
            { "block",      HandleBlock,      SEC_GAMEMASTER, Console::No },
            { "wound",      HandleWound,      SEC_GAMEMASTER, Console::No },
            { "bloodprice", HandleBloodPrice, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_sandfury_executioner_rework()
{
    RegisterDungeonReworkCreatureAI(boss_sandfury_executioner_rework, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_zf_pyramid_stalker, ZulFarrakRework::kInstanceScriptName);
    RegisterSpellScript(spell_zf_pyramid_grievous_wound);
    RegisterPyramidStage(PYRAMID_STAGE_BLOCK, [](InstanceScript* instance)
    {
        return std::make_unique<BlockStage>(instance);
    });
    ZfTest::RegisterBoss("block", BlockTestCommands());
}
