/*
 * mod-dungeon-bosses, Blackrock Depths D4: the Ring of Law's wave mobs (npc_ring_beast_rework on all six: Dredge Worm
 * 8925, Deep Stinger 8926, Dark Screecher 8927, Burrowing Thundersnout 8928, Borer Beetle 8932, Cave Creeper 8933).
 * Build spec S1 "Waves" and RW1-RW6 (docs/dungeons/blackrock-depths-1-detention-block.md; ruling 20). Replaces their
 * SmartAI (rev_ring_of_law_blackrock_depths.sql drops the rows; ring_of_law.py binds the script). Summoned only by
 * Grimstone (npc_grimstone_rework.cpp): the opener wave and Trial by Beasts' adds. Pure rules: RingOfLawLogic.h.
 *
 *   Opening   the opener's first beast casts its type's stock debuff once it is inside the floor (Dredge Sickness,
 *             Barbed Sting, Aural Shock, Disjunction, Creeper Venom, Putrid Enzyme); Grimstone removes it when the wave
 *             dies. Trial by
 *             Beasts' adds cast none (S1 section 8 #16).
 *   RW1       Burrow (Grimstone's clock, one worm every 12 s): the worm sinks (unselectable, rooted) and erupts 2 s
 *             later under a random player's spot, 5 yd, 25% / 40% + Weakened.
 *   RW2       Tail Sting (Grimstone's clock, one stinger every 10 s): it turns on a random player within 15 yd (the
 *             tank too, ruling 88): a 2 s 60 degree / 15 yd cone locked at the cast, 20% / 35% + Weakened + a poison.
 *   RW3       Screech (each bat, 18 s): a 2 s kickable cast; landed, everyone within 10 yd takes 10% / 15% and is
 *             silenced 2 s (the stock 6 s Sonic Burst retired).
 *   RW4       Thunderclap (each lizard, the stock 8 s): a 2 s wind-up, a 10 yd ring at the lizard (the tank too),
 *             20% / 35% + Weakened + the stock slow. A stun that breaks the wind-up stops the clap.
 *   RW5       Venom Spit (Grimstone's clock, one spider every 10 s): a 4 yd pool at a random player's spot, 1.5 s, for
 *             12 s, 4% / 6% a second (owned by Grimstone: the pool outlives the spider; the stock 5 s Web retired).
 *   RW6       Acid Burst (each beetle): on its death it lies swelling 2 s (a held body, KT-D1), then bursts in a 4 yd
 *             circle at its corpse, 15% / 25% + Weakened, and dies.
 *   Stock     Poison and Venom Spit (worm), Lizard Bolt (lizard) rescaled as copies; Cleave (stinger) and Pierce Armor
 *             (beetle) kept as they are.
 *
 * Every dodgeable hit feeds Crowd Favor (RingOfLawFight.h Judged). Every firing logs one INFO line "brd ring <mechanic>
 * ..." (module.dungeonbosses).
 */

#include "BlackrockDepthsRework.h"
#include "BossMechanics.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitBodies.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "RingOfLawFight.h"
#include "RingOfLawLogic.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <array>
#include <string>
#include <vector>

using namespace BlackrockDepthsRework;
using namespace BrdRingOfLaw;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBoss = "ring";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    void LogBeast(char const* mechanic, Creature const* beast, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, Acore::StringFormat("beast={}/{} {}",
            beast->GetEntry(), beast->GetGUID().GetCounter(), detail));
    }

    float GroundZ(WorldObject const* probe, float x, float y, float refZ)
    {
        float const h = probe->GetMapHeight(x, y, refZ + 2.f);
        if (h <= INVALID_HEIGHT || std::fabs(h - refZ) > 6.f)
            return refZ;
        return h;
    }
}

struct npc_ring_beast_rework : public ScriptedAI
{
    enum class State : uint8
    {
        Fight,
        Burrowed,       // RW1: under the floor for 2 s
        Stinging,       // RW2: the 2 s cast bar, the cone locked
        Clapping,       // RW4: the 2 s wind-up
    };

    explicit npc_ring_beast_rework(Creature* creature)
        : ScriptedAI(creature), _type(WaveIndexOf(creature->GetEntry()).value_or(0)), _body(BodySpec()) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Engine hooks
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        Cleanup();
        if (IsBeetle())
            _body.Reset(me);
    }

    void SetData(uint32 id, uint32 value) override
    {
        if (id == kBeastDataSlot)
            _slot = value;
    }

    uint32 GetData(uint32 id) const override
    {
        if (id == kBeastDataFree)
            return Free() ? 1 : 0;
        return 0;
    }

    // Grimstone's clock: this beast's group signature now.
    void DoAction(int32 action) override
    {
        if (action == kBeastActionSignature && Free())
            GroupSignature();
    }

    void JustEngagedWith(Unit* /*who*/) override
    {
        _heroic = IsHeroicMap(me);
        WaveKind const& w = Type();
        uint32 const index = _slot ? _slot - 1 : 0;
        for (std::size_t i = 0; i < w.casts.size(); ++i)
            _castAtMs[i] = w.casts[i].spell ? _clockMs + w.casts[i].firstMs : 0;
        _sigAtMs = w.perBeast && w.signature != Signature::AcidBurst ? _clockMs + FirstSignatureMs(w, index) : 0;
        // The opener's first beast lays its type's stock opening debuff on the group (an add of Trial by Beasts none),
        // once it is inside the floor (UpdateAI): from the south alcove its 30 yd aura reaches nobody.
        _openingPending = _slot == 1 && w.openingDebuff != 0;
    }

    void DamageTaken(Unit* /*attacker*/, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*mask*/) override
    {
        if (IsBeetle())
            _body.Intercept(me, damage);
    }

    // While the Ring runs a beast never walks off: back into the fight on a player on the floor.
    void EnterEvadeMode(EvadeReason why) override
    {
        if (IsBeetle() && _body.Fallen())
            return;
        if (RingFrame* frame = FrameOf(me))
        {
            std::vector<Player*> const players = frame->FloorPlayers();
            if (!players.empty() && FrameRuns(frame->CurrentStep()))
            {
                for (Player* player : players)
                    me->AddThreat(player, 0.f);
                AttackStart(players[urand(0, uint32(players.size() - 1))]);
                if (me->IsEngaged())
                    return;
            }
        }
        Cleanup();
        ScriptedAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* /*killer*/) override
    {
        Cleanup();
    }

    // RW2 / RW4: a wind-up broken (a stun, a silence) lands nothing (rule 13).
    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (!spell)
            return;
        if ((spell->Id == SPELL_RW_TAIL_STING_BAR && _state == State::Stinging)
            || (spell->Id == SPELL_RW_THUNDERCLAP_BAR && _state == State::Clapping))
        {
            if (_pending)
                Mechanic::Cancel(me, _pending);
            _pending = MechanicHandle();
            LogBeast(_state == State::Stinging ? "tail-sting-stopped" : "thunderclap-stopped", me);
            _state = State::Fight;
        }
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        if (IsBeetle())
        {
            _body.Update(me, diff);
            if (_burstAtMs && _clockMs >= _burstAtMs)
            {
                _burstAtMs = 0;
                me->CastSpell(me, SPELL_RW_ACID_BURST_LOOK, true);
            }
            if (_body.Fallen())
                return;
        }

        if (_state == State::Burrowed)
        {
            if (_clockMs >= _stateEndMs)
                Erupt();
            return;     // under the floor: no target, no evade
        }

        if (!UpdateVictim())
            return;

        if (_state != State::Fight)
        {
            if (_clockMs >= _stateEndMs)
            {
                _state = State::Fight;
                _pending = MechanicHandle();
            }
            return;
        }
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;

        WaveKind const& w = Type();
        if (OpeningDebuffDue(_openingPending, DungeonKit::PlaneOf(me)))
        {
            _openingPending = false;
            DoCastSelf(w.openingDebuff);
            LogBeast("opening-debuff", me, Acore::StringFormat("spell={}", w.openingDebuff));
            return;
        }
        if (_sigAtMs && _clockMs >= _sigAtMs)
        {
            _sigAtMs = _clockMs + w.everyMs;
            if (w.signature == Signature::Screech)
                Screech();
            else if (w.signature == Signature::Thunderclap)
                Thunderclap();
            return;
        }
        for (std::size_t i = 0; i < w.casts.size(); ++i)
        {
            StockCast const& c = w.casts[i];
            if (!c.spell || !_castAtMs[i] || _clockMs < _castAtMs[i])
                continue;
            _castAtMs[i] = _clockMs + c.everyMs;
            Unit* target = c.target == CastTarget::Victim ? me->GetVictim() : RandomPlayer(100.f);
            if (target)
            {
                DoCast(target, c.spell);
                return;
            }
        }
        DoMeleeAttackIfReady();
    }

private:
    // ----------------------------------------------------------------------------------------------------------------
    // The group signatures (Grimstone's clock)
    // ----------------------------------------------------------------------------------------------------------------

    void GroupSignature()
    {
        switch (Type().signature)
        {
            case Signature::Burrow:
                Burrow();
                break;
            case Signature::TailSting:
                TailSting();
                break;
            case Signature::VenomSpit:
                VenomSpit();
                break;
            default:
                break;
        }
    }

    // RW1: sink, then erupt under the spot 2 s later.
    void Burrow()
    {
        Player* target = RandomPlayer(100.f);
        if (!target)
            return;
        _spot = Position(target->GetPositionX(), target->GetPositionY(), target->GetPositionZ(), me->GetOrientation());
        me->CastSpell(me, SPELL_RW_BURROW_SINK, true);
        me->InterruptNonMeleeSpells(false);
        me->AttackStop();
        me->GetMotionMaster()->Clear();
        me->StopMoving();
        me->SetReactState(REACT_PASSIVE);
        me->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->SetControlled(true, UNIT_STATE_ROOT);
        _state = State::Burrowed;
        _stateEndMs = _clockMs + kBurrowWarnMs;
        _returnTo = target->GetGUID();

        MechanicRef ref = Mechanic::Circle(me, BossMechanics::Anchor(_spot), kBurrowRadius, Ms(kBurrowWarnMs));
        ref.Damage(kBurrowPct(_heroic)).TankDamage(kBurrowPct(_heroic))
            .Weakened().Spell(SPELL_RW_BURROW).Tag(TAG_RW_BURROW);
        Judged(ref, me, "burrow");
        _pending = ref.Handle();
        LogBeast("burrow", me, Acore::StringFormat("target={} pct={:.0f}", target->GetName(), kBurrowPct(_heroic)));
    }

    void Erupt()
    {
        _state = State::Fight;
        _pending = MechanicHandle();
        me->SetControlled(false, UNIT_STATE_ROOT);
        me->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->SetReactState(REACT_AGGRESSIVE);
        float const z = GroundZ(me, _spot.GetPositionX(), _spot.GetPositionY(), _spot.GetPositionZ());
        me->NearTeleportTo(_spot.GetPositionX(), _spot.GetPositionY(), z, me->GetOrientation());
        me->CastSpell(me, SPELL_RW_BURROW_ERUPT, true);
        Unit* target = ObjectAccessor::GetPlayer(*me, _returnTo);
        if (!target || !target->IsAlive())
            target = RandomPlayer(100.f);
        if (target)
            AttackStart(target);
    }

    // RW2: a 60 degree / 15 yd cone toward a random player within 15 yd, locked at the cast.
    void TailSting()
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        rule.maxRange = kTailStingRange;
        Player* target = DungeonKit::PickPlayer(me, rule);
        if (!target)
        {
            LogBeast("tail-sting-none", me, "nobody within 15 yd");
            return;
        }
        float const facing = DungeonKit::BearingTo(DungeonKit::PlaneOf(me), DungeonKit::PlaneOf(target));
        me->SetFacingTo(facing);
        me->CastSpell(me, SPELL_RW_TAIL_STING_BAR, false);
        _state = State::Stinging;
        _stateEndMs = _clockMs + kTailStingWarnMs;
        Position const apex(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), facing);
        MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::Cone(BossMechanics::Anchor(apex),
            kTailStingAngleDeg, kTailStingLength), Ms(kTailStingWarnMs));
        ref.Damage(kTailStingPct(_heroic)).TankDamage(kTailStingPct(_heroic))
            .Weakened().Spell(SPELL_RW_TAIL_STING).Rider(SPELL_RW_TAIL_STING_POISON)
            .Tag(TAG_RW_TAIL_STING);
        Judged(ref, me, "tail-sting");
        _pending = ref.Handle();
        LogBeast("tail-sting", me, Acore::StringFormat("target={} pct={:.0f}", target->GetName(),
            kTailStingPct(_heroic)));
    }

    // RW5: a 4 yd pool at a random player's spot for 12 s (Grimstone owns it: it outlives the spider).
    void VenomSpit()
    {
        Player* target = RandomPlayer(100.f);
        if (!target)
            return;
        RingFrame* frame = FrameOf(me);
        Creature* owner = frame ? frame->Owner() : me;
        float const z = GroundZ(me, target->GetPositionX(), target->GetPositionY(), target->GetPositionZ());
        Position const spot(target->GetPositionX(), target->GetPositionY(), z, 0.f);
        me->SetFacingToObject(target);
        MechanicRef ref = Mechanic::Circle(owner, BossMechanics::Anchor(spot), kVenomSpitRadius, Ms(kVenomSpitWarnMs));
        ref.Persistent(Ms(kVenomSpitLifeMs), Ms(kVenomSpitTickMs)).Damage(kVenomSpitPct(_heroic))
            .TankDamage(kVenomSpitPct(_heroic))
            .Spell(SPELL_RW_VENOM_SPIT).Tag(TAG_RW_VENOM_SPIT);
        JudgedPersistent(ref, me, "venom-spit");
        if (ref.IsValid())
            if (Creature* pool = owner->SummonCreature(NPC_BRD_STALKER, spot, TEMPSUMMON_TIMED_DESPAWN,
                kVenomSpitWarnMs + kVenomSpitLifeMs))
                pool->CastSpell(pool, SPELL_RW_VENOM_SPIT_POOL, true);
        LogBeast("venom-spit", me, Acore::StringFormat("target={} ok={} pct={:.0f}/s", target->GetName(),
            ref.IsValid() ? 1 : 0, kVenomSpitPct(_heroic)));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The per-beast signatures
    // ----------------------------------------------------------------------------------------------------------------

    // RW3: the 2 s kickable cast (the spell itself hits within 10 yd and silences; spell_dungeon_refflat_damage).
    void Screech()
    {
        me->CastSpell(me, SPELL_RW_SCREECH, false);
        LogBeast("screech", me, Acore::StringFormat("pct={:.0f}", kScreechPct(_heroic)));
    }

    // RW4: the 2 s wind-up and a 10 yd ring at the lizard (the tank too).
    void Thunderclap()
    {
        me->CastSpell(me, SPELL_RW_THUNDERCLAP_BAR, false);
        _state = State::Clapping;
        _stateEndMs = _clockMs + kThunderclapWarnMs;
        Position const at(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), 0.f);
        MechanicRef ref = Mechanic::Circle(me, BossMechanics::Anchor(at), kThunderclapRadius, Ms(kThunderclapWarnMs));
        ref.Damage(kThunderclapPct(_heroic)).TankDamage(kThunderclapPct(_heroic))
            .Weakened().Spell(SPELL_RW_THUNDERCLAP).Rider(SPELL_RW_THUNDERCLAP_SLOW)
            .Tag(TAG_RW_THUNDERCLAP);
        Judged(ref, me, "thunderclap");
        _pending = ref.Handle();
        LogBeast("thunderclap", me, Acore::StringFormat("pct={:.0f}", kThunderclapPct(_heroic)));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RW6: the beetle's held body
    // ----------------------------------------------------------------------------------------------------------------

    static DungeonKit::HeldBodySpec BodySpec()
    {
        DungeonKit::HeldBodySpec spec;
        spec.holds = 1;
        spec.holdLimit = Ms(kAcidBodyHoldMs);
        spec.look = true;
        spec.root = true;
        spec.fallAura = SPELL_RW_ACID_SWELL;
        spec.dungeon = kLogDungeon;
        spec.boss = kBoss;
        spec.onFall = [](Creature* body)
        {
            if (auto* ai = body && body->IsAIEnabled ? dynamic_cast<npc_ring_beast_rework*>(body->AI()) : nullptr)
                ai->AcidBurst();
        };
        return spec;
    }

    void AcidBurst()
    {
        bool const heroic = IsHeroicMap(me);
        Position const spot(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), 0.f);
        MechanicRef ref = Mechanic::Circle(me, BossMechanics::Anchor(spot), kAcidBurstRadius, Ms(kAcidSwellMs));
        ref.Damage(kAcidBurstPct(heroic)).TankDamage(kAcidBurstPct(heroic))
            .Weakened().Spell(SPELL_RW_ACID_BURST).Tag(TAG_RW_ACID_BURST);
        Judged(ref, me, "acid-burst");
        _burstAtMs = _clockMs + kAcidSwellMs;
        LogBeast("acid-burst", me, Acore::StringFormat("ok={} pct={:.0f}", ref.IsValid() ? 1 : 0,
            kAcidBurstPct(heroic)));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Helpers
    // ----------------------------------------------------------------------------------------------------------------

    WaveKind const& Type() const { return kWaveTypes[_type]; }
    bool IsBeetle() const { return Type().signature == Signature::AcidBurst; }

    bool Free() const
    {
        return me->IsAlive() && _state == State::Fight && !me->HasUnitState(UNIT_STATE_CASTING)
            && !(IsBeetle() && _body.Fallen());
    }

    // A random player in its fight (the tank too, ruling 88).
    Player* RandomPlayer(float range)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        rule.maxRange = range;
        return DungeonKit::PickPlayer(me, rule);
    }

    // Every change of the fight undone (rule 6): the burrow's flags, the root, a pending zone.
    void Cleanup()
    {
        if (_pending)
            Mechanic::Cancel(me, _pending);
        _pending = MechanicHandle();
        if (_state == State::Burrowed)
        {
            me->SetControlled(false, UNIT_STATE_ROOT);
            me->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        }
        me->SetReactState(REACT_AGGRESSIVE);
        _state = State::Fight;
        _openingPending = false;
        _sigAtMs = 0;
        _burstAtMs = 0;
        _castAtMs.fill(0);
    }

    uint32 _type = 0;
    uint32 _slot = 0;
    bool _openingPending = false;
    bool _heroic = false;
    uint32 _clockMs = 0;
    State _state = State::Fight;
    uint32 _stateEndMs = 0;
    uint32 _sigAtMs = 0;
    uint32 _burstAtMs = 0;
    std::array<uint32, 2> _castAtMs{ { 0, 0 } };
    Position _spot;
    ObjectGuid _returnTo;
    MechanicHandle _pending;
    DungeonKit::HeldBody _body;
};

void AddSC_npc_ring_beast_rework()
{
    if (BrdRingOfLaw::kBound)
        RegisterDungeonReworkCreatureAI(npc_ring_beast_rework, BlackrockDepthsRework::kInstanceScriptName);
}
