/*
 * mod-dungeon-bosses, Zul'Farrak D6: Chief Ukorz Sandscalp (7267, boss_ukorz_rework) and Ruuzlu (7797,
 * boss_ruuzlu_rework), the Dungeon Finder end (encounter 600, slot 7). Build spec: docs/dungeons/zul-farrak-rework.md
 * "Chief Ukorz Sandscalp and Ruuzlu" (UK1-UK14, Build spec; rulings 31 to 35, 45), handoff sections 3.5 row D6, 3.6,
 * 3.8 (the mesa), 3.9 rows 8 and 12, 7 #10, #34, #41 and #42 (all A), section 10. Replaces SmartAI 7267 and 7797
 * (WP-S0's rev drops the rows); Ruuzlu's stock Execute 38959 on targets under 20% is retired. Pure rules and every
 * number: UkorzLogic.h (namespace ZfUkorz, Tune); health: ZulFarrakRework.h Health.
 *
 * Ukorz's AI runs the fight for both (the director): the meters, every set piece, the sunk and the rescues, the pits,
 * the transition and phase 3; every registry mechanic is his encounter's (Ruuzlu's Bladestorm is anchored on Ruuzlu
 * but owned by Ukorz). He never dies before Ruuzlu: on normal a lethal hit while Ruuzlu stands leaves him a held body
 * (DungeonKit::HeldBody: lying, not attackable) until Ruuzlu falls, then he dies for real and the credit lands; on
 * heroic the 30% hold stops both first. Ruuzlu's AI melees and Cleaves and reports his damage, casts and evades to
 * Ukorz; his acts (roar, storm, execute) are Ukorz's orders.
 *
 *   UK1  Fury of the Sands  a meter on each boss (aura stacks 0-10, +3% / +4% damage done each), a stack per 4% / 3%
 *                           of the partner's health lost (any damage, splash included); a stack off every 4 s / 5 s
 *                           once the partner lost under 1% in the last 4 s (section 7 #41 A)
 *   UK2  Battle Roar        at 5 stacks, once per fill: a 2.5 s / 2 s kickable cast (Fire: a kick locks none of the
 *                           bars). Landed: the meter fills to 10 (heroic: the next spin lasts 9 s)
 *   UK3  Bladestorm         at 10: the yell, a 2 s wind-up, then 6 s / 8 s of an 8 yd ring on the boss, 12% / 15% a
 *                           second, the tank included; he walks at a random player on the mesa at 5 yd/s and turns to
 *                           a new one every 2 s. The meter goes back to 0. Heroic phase 3: every 25 s, no meter
 *   UK4  The trail          heroic: a 4 yd quicksand circle (stalker 301025) every 2 yd he walks, 15 s, 50% slow
 *   UK5  Sinking Sands      Ukorz stamps (2 s / 1.5 s bar) and a 6 yd circle opens under 1 / 2 random players, the
 *                           tank included: 12 s, every 20 s / 15 s. The pit stays 30 s as quicksand (50% slow); after
 *                           his normal 30% Frenzy the pits stop closing
 *   UK6  Sunk               anyone in a pit at its resolve is rooted for 8 s (they still fight); another player who
 *                           stands within 3 yd of them for 2 s (DungeonKit::DwellSoaks) pulls them out
 *   UK7  Execute            Ruuzlu (section 7 #42 A: Ukorz once Ruuzlu is gone; heroic phase 1 one each) leaves his
 *                           target, walks to the sunk and casts a 4 s bar (not kickable); landed, 50% / 75% Physical.
 *                           The root holds until the bar ends; a rescue stops the bar
 *   UK8  Frenzy             stock 8269 at Ukorz's 30% (normal) / at phase 3 (heroic), stock line 1
 *   UK9  Vengeance / hold   normal: the survivor's meter fills a stack every 3 s and never fades; heroic: each holds
 *                           at 30% ("Not yet") until the other is there too
 *   UK10 Call of Sul'thraze heroic, both at 30%: Ruuzlu throws the blade and falls, Ukorz takes his remaining health,
 *                           casts a 10 s bar (not kickable; damage lands freely); Fury ends
 *   UK11 The sands rise     with UK10: a pit under every player at once (1.5 s)
 *   UK12 Lash of Sul'thraze phase 3: every 10 s a 2 s bar and a mark on a random player (the tank included), then a
 *                           25% Shadow lash that jumps to every other player within 8 yd of a struck one (4 jumps at
 *                           most) with 15% less of every stat for 15 s (a registry Spread for the bots)
 *   UK13 Creeping Sands     from the Call: a quicksand donut round the mesa's middle (section 7 #34 A), 30 yd inside,
 *                           closing 5 yd every 20 s of phase 3 to nothing (ruling 45: no floor), 8% Shadow a second and
 *                           the slow
 *   UK14 Steady pressure    stock Cleave 15496 (first 3-8 s, then 7-11 s) and melee on both
 *
 * Boss data: Battle Roar of both on the interrupt list; kill order: the boss whose partner's Fury is lower
 * (PickFavored, a shared atomic the bots' conditions read), each KillTogether(partner, 10); the other ignored by DPS
 * bots (section 7 #10 A: IgnoreEntry.For(Who::Dps), so their AoE counts stop splashing it); neither AoeOk; the
 * stalkers ignored. No dispel entry (Sunk, the slow, the lash's debuff are not dispellable).
 *
 * A wipe, an evade or Ukorz's death clears every registry handle, held Soak, stalker, aura and act of both, restores
 * Ruuzlu's react state and gives back a Ruuzlu who died in the failed attempt (Respawn, else ForceCreatureRespawn by
 * spawn id: RB-20). Every firing logs one INFO line "zf-build ukorz <mechanic> ..."; `.dbtest zf ukorz ...` fires one.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitBodies.h"
#include "DungeonKitSoaks.h"
#include "GameTime.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "Spell.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "UkorzLogic.h"
#include "ZulFarrakKit.h"
#include "ZulFarrakRework.h"
#include "ZulFarrakTestCommand.h"
#include <algorithm>
#include <array>
#include <atomic>
#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ZulFarrakRework;
using namespace ZfUkorz;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBoss = "ukorz";

    // Registry tags (one per mechanic; the bots and `.mech` read them).
    uint32 constexpr TAG_UK_STORM = 1;
    uint32 constexpr TAG_UK_TRAIL = 2;
    uint32 constexpr TAG_UK_PIT = 3;
    uint32 constexpr TAG_UK_QUICKSAND = 4;
    uint32 constexpr TAG_UK_RESCUE = 5;
    uint32 constexpr TAG_UK_LASH = 6;
    uint32 constexpr TAG_UK_CREEP = 7;

    // Movement ids.
    uint32 constexpr POINT_UK_STORM = 1;
    uint32 constexpr POINT_UK_EXECUTE = 2;

    float constexpr kZBandYd = 6.f;             // a zone's height band (the mesa floor runs z 50 to 57)
    float constexpr kCreepZBandYd = 10.f;       // the donut's: the west strip lies 3 to 8 yd lower
    uint32 constexpr kExecuteRepathMs = 1000;   // the walk re-aims at the sunk this often (a knockback moves them)
    uint32 constexpr kRestoreCheckMs = 2000;    // out of combat: Ruuzlu given back this often at most

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    char const* SideName(Side side)
    {
        return side == Side::Ukorz ? "ukorz" : "ruuzlu";
    }

    // A player the fight acts on: in the world, alive, not a game master.
    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    // On the mesa's floor (its arena with the z band): L6, every pick filters by the arena and by z.
    bool OnMesa(WorldObject const* object)
    {
        static DungeonKit::Arena const mesa = MesaArena();
        return object && mesa.Contains(DungeonKit::PlaneOf(object), object->GetPositionZ());
    }

    Position MesaCenter()
    {
        return DungeonKit::ToPosition(kMesaDonutCenter.XY(), kMesaDonutCenter.z);
    }

    // The bots' spots inside the Creeping Sands' safe circle, clipped to the mesa (F-1 MI-4: the bare circle reached
    // past the walls at its first sizes).
    BossMechanics::SpotBounds CreepBounds(float innerYd)
    {
        std::vector<Position> points;
        for (DungeonKit::Vec2 const& v : CreepSafeFloor(CreepBoundsYd(innerYd)))
            points.emplace_back(v.x, v.y, kMesaDonutCenter.z);
        BossMechanics::SpotBounds bounds;
        if (points.size() >= 3)
            bounds.Polygon(std::move(points), kMesaZMin, kMesaZMax);
        else
            bounds.Circle(MesaCenter(), CreepBoundsYd(innerYd), kMesaZMin, kMesaZMax);
        return bounds;
    }

    // Pulling either pulls both: the partner, alive and not fighting yet, turns on `who` and takes the players of the
    // mesa onto its threat list.
    void PullPartner(Creature* partner, Unit* who)
    {
        if (!partner || !partner->IsAlive() || partner->IsInCombat() || !partner->IsAIEnabled || !partner->AI())
            return;
        if (who)
            partner->AI()->AttackStart(who);
        partner->AI()->DoZoneInCombat(partner, 60.f);
    }

    // He lets go of his target: passive, no chase, his threat list untouched.
    void StopFighting(Creature* unit)
    {
        if (!unit)
            return;
        unit->SetReactState(REACT_PASSIVE);
        unit->AttackStop();
        unit->StopMoving();
        unit->GetMotionMaster()->Clear();
    }

    // Back to his top-threat unit.
    void ResumeFighting(Creature* unit)
    {
        if (!unit || !unit->IsAlive() || !unit->IsInCombat())
            return;
        unit->SetReactState(REACT_AGGRESSIVE);
        if (Unit* victim = unit->SelectVictim())
            if (unit->IsAIEnabled && unit->AI())
                unit->AI()->AttackStart(victim);
    }
}

// Chief Ukorz Sandscalp 7267: the director of both.
struct boss_ukorz_rework : public BossAI
{
    enum class Act : uint8
    {
        None,           // fighting
        Roar,           // UK2 the cast
        StormWindup,    // UK3 the 2 s bar
        StormSpin,      // UK3 the walk
        ExecuteWalk,    // UK7 to the sunk
        ExecuteCast,    // UK7 the bar
        Stamp,          // UK5 the bar (Ukorz)
        Lash,           // UK12 the bar (Ukorz)
        Call,           // UK10 the bar (Ukorz)
    };

    enum class Phase : uint8
    {
        One,            // both (normal: the whole fight)
        Call,           // heroic UK10, the 10 s cast
        Three,          // heroic, Ukorz alone
    };

    explicit boss_ukorz_rework(Creature* creature)
        : BossAI(creature, BOSS_UKORZ), _arena(MesaArena(), LeashOptions(kBoss)), _floor(UkorzFloorBounds()),
            _body(BodySpec()), _favored(std::make_shared<std::atomic<uint64>>(0)) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();
        Cleanup(false);
        _body.Reset(me);
        RestoreRuuzlu("reset");
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        _engaged = true;
        _heroic = IsHeroicMap(me);
        _clockMs = 0;
        _phase = Phase::One;
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_UKORZ;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);
        Talk(SAY_UKORZ_AGGRO);
        me->CastSpell(me, SPELL_BERSERKER_STANCE, true);
        _cleaveAtMs = urand(Tune::kCleaveFirstMinMs, Tune::kCleaveFirstMaxMs);
        _nextStampMs = Tune::kStampFirstMs;
        for (Fighter& f : _f)
            f = Fighter{};
        _f[Index(Side::Ukorz)].lastPct = me->GetHealthPct();
        Creature* ruuzlu = Ruuzlu();
        if (ruuzlu)
        {
            PullPartner(ruuzlu, who);
            Mechanic::TrackUnit(me, ruuzlu);
            _f[Index(Side::Ruuzlu)].lastPct = ruuzlu->GetHealthPct();
        }
        OnBossPull(me, kBoss);
        UpdateFavored();
        Describe();
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        if (_evading)
            return;
        _evading = true;
        Log("evade", Acore::StringFormat("reason={} phase={}", uint32(why), uint32(_phase)));
        Cleanup(false);
        _body.Reset(me);
        if (Creature* ruuzlu = Ruuzlu())
            if (ruuzlu->IsAlive() && ruuzlu->IsInCombat() && ruuzlu->IsAIEnabled && ruuzlu->AI())
                ruuzlu->AI()->EnterEvadeMode(why);
        BossAI::EnterEvadeMode(why);
        _evading = false;
    }

    void JustDied(Unit* killer) override
    {
        uint32 const phase = uint32(_phase);
        Cleanup(true);
        BossAI::JustDied(killer);
        Log("death", Acore::StringFormat("phase={} killer={}", phase,
            killer ? killer->GetName() : std::string("none")));
    }

    void KilledUnit(Unit* victim) override
    {
        if (!victim || !victim->IsPlayer() || _clockMs < _killLineAtMs)
            return;
        _killLineAtMs = _clockMs + Tune::kKillLineGapMs;
        Talk(urand(0, 1) ? SAY_UKORZ_KILL : SAY_UKORZ_KILL_2);
    }

    // The stalkers join the summon list (despawned on reset, evade and death) but never the fight.
    void JustSummoned(Creature* summon) override
    {
        if (summon)
            summons.Summon(summon);
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        if (_engaged && _heroic && _phase == Phase::One)
            damage = HoldDamage(me->GetHealth(), me->GetMaxHealth(), damage, Tune::kHoldPct);
        // Never before Ruuzlu: a lethal hit while he stands leaves a held body (the credit waits for him).
        if (_body.Fallen() || RuuzluStands())
            _body.Intercept(me, damage);
        BossAI::DamageTaken(attacker, damage, type, mask);
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        BossAI::OnSpellCast(spell);
        if (spell)
            OnCast(Side::Ukorz, spell->Id, true);
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (spell && !_ownInterrupt)
            OnCast(Side::Ukorz, spell->Id, false);
    }

    void UpdateAI(uint32 diff) override
    {
        ZulFarrak::NoAssist(me);        // rule 27, LESSONS L1: every tick, before UpdateVictim
        _body.Update(me, diff);
        if (_body.Fallen())
        {
            // A held body never fights (and never calls UpdateVictim); the fight goes on round Ruuzlu.
            if (_engaged)
            {
                _clockMs += diff;
                Direct(diff);
            }
            return;
        }
        if (!me->IsInCombat())
            UpdateRestore(diff);
        if (!UpdateVictim())
            return;
        if (!_engaged)
            return;
        _clockMs += diff;
        // While an act places him (a walk, a spin) the guard waits, or it would turn him meanwhile.
        if (!Busy(Side::Ukorz) && !_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        Direct(diff);
        if (!_engaged || !me->IsAlive() || _body.Fallen())
            return;
        if (Busy(Side::Ukorz) || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (_clockMs >= _cleaveAtMs)
        {
            _cleaveAtMs = _clockMs + urand(Tune::kCleaveEveryMinMs, Tune::kCleaveEveryMaxMs);
            if (Unit* victim = me->GetVictim())
                if (me->IsWithinMeleeRange(victim))
                    me->CastSpell(victim, SPELL_CLEAVE, false);
        }
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Ruuzlu's AI reports here
    // ----------------------------------------------------------------------------------------------------------------

    void PartnerEngaged(Unit* who)
    {
        if (me->IsAlive() && !me->IsInCombat() && who)
        {
            AttackStart(who);
            DoZoneInCombat(me, 60.f);
        }
    }

    void PartnerEvaded(EvadeReason why)
    {
        if (me->IsAlive() && (me->IsInCombat() || _engaged))
            EnterEvadeMode(why);
    }

    // Ruuzlu's damage taken: the heroic hold (UK9).
    uint32 RuuzluDamage(Creature* ruuzlu, uint32 damage) const
    {
        if (!_engaged || !_heroic || _phase != Phase::One || !ruuzlu)
            return damage;
        return HoldDamage(ruuzlu->GetHealth(), ruuzlu->GetMaxHealth(), damage, Tune::kHoldPct);
    }

    void PartnerSpell(SpellInfo const* spell, bool landed)
    {
        if (spell && (landed || !_ownInterrupt))
            OnCast(Side::Ruuzlu, spell->Id, landed);
    }

    // The side runs an act (no melee, no Cleave, no arena guard).
    bool Busy(Side side) const
    {
        return _engaged && _f[Index(side)].act != Act::None;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest zf ukorz` entry points
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Roar,
        Storm,
        Stamp,
        Sink,
        Call,
        Lash,
        Creep,
    };

    // An empty string when fired; otherwise why not. `who` is the GM's selected player (or the GM).
    std::string TestFire(TestMechanic mechanic, Side side, Player* who)
    {
        if (!_engaged || !me->IsEngaged())
            return "Ukorz must be in combat (the picks read the mesa, the mechanics his encounter).";
        Creature* unit = UnitOf(side);
        bool const sideFree = unit && Stands(side) && !Busy(side) && !unit->HasUnitState(UNIT_STATE_CASTING);
        switch (mechanic)
        {
            case TestMechanic::Roar:
                if (_phase != Phase::One || !sideFree)
                    return "Only in phase 1, with that boss standing and free.";
                _f[Index(side)].fury.Set(Tune::kRoarAtStacks);
                SetFuryAura(side);
                StartRoar(side);
                break;
            case TestMechanic::Storm:
                if (!sideFree || (_phase != Phase::One && side != Side::Ukorz))
                    return "That boss must stand and be free.";
                StartStorm(side, "gm");
                break;
            case TestMechanic::Stamp:
                if (!sideFree || side != Side::Ukorz)
                    return "Ukorz must stand and be free.";
                Stamp(who);
                break;
            case TestMechanic::Sink:
                if (!CountsAsPlayer(who) || IsSunk(who))
                    return "The sink needs a living player (.gm off) who is not sunk already.";
                Sink(who, "gm");
                break;
            case TestMechanic::Call:
                if (_phase != Phase::One || !RuuzluStands() || !Stands(Side::Ukorz))
                    return "Only in phase 1 with both standing (any difficulty: the transition is heroic's).";
                StartCall("gm");
                break;
            case TestMechanic::Lash:
                if (!sideFree || side != Side::Ukorz)
                    return "Ukorz must stand and be free.";
                StartLash(who);
                break;
            case TestMechanic::Creep:
                if (_phase == Phase::One)
                    FormCreep();
                else if (_creepStep < CreepStep(UINT64_MAX))
                    RegisterCreep(_creepStep + 1, Tune::kCreepStepWarnMs);
                else
                    return "Creeping Sands is shut already.";
                break;
        }
        return {};
    }

    // `.dbtest zf ukorz fury <side> <stacks>`.
    bool TestFury(Side side, uint32 stacks)
    {
        if (!_engaged || _phase != Phase::One || !Stands(side))
            return false;
        _f[Index(side)].fury.Set(stacks);
        SetFuryAura(side);
        Log("fury-set", Acore::StringFormat("who={} stacks={}", SideName(side), _f[Index(side)].fury.Stacks()));
        return true;
    }

    // The heroic form on any map until the end of the pull (the reference row stays the map's), phase 1 only.
    bool TestHeroic(bool heroic)
    {
        if (!_engaged || _phase != Phase::One)
            return false;
        for (Side side : { Side::Ukorz, Side::Ruuzlu })
            if (Creature* unit = UnitOf(side))
                unit->RemoveAurasDueToSpell(FurySpell());
        _heroic = heroic;
        for (Side side : { Side::Ukorz, Side::Ruuzlu })
            SetFuryAura(side);
        Describe();
        return true;
    }

    std::string TestState()
    {
        Fighter const& u = _f[Index(Side::Ukorz)];
        Fighter const& r = _f[Index(Side::Ruuzlu)];
        return Acore::StringFormat("clock={}s heroic={} phase={} fury ukorz={} ruuzlu={} act ukorz={} ruuzlu={} "
            "favored={} fallen={} frenzied={} sunk={} rescues={} pits={} next stamp={}ms creep step={} inner={:.0f} "
            "handles={}", _clockMs / 1000, _heroic ? 1 : 0, uint32(_phase), u.fury.Stacks(), r.fury.Stacks(),
            uint32(u.act), uint32(r.act), _favoredSide ? SideName(*_favoredSide) : "none", _body.Fallen() ? 1 : 0,
            _frenzied ? 1 : 0, _sunk.size(), _rescues.Count(), _pits.size(),
            _nextStampMs > _clockMs ? _nextStampMs - _clockMs : 0, _creepStep, CreepInnerYd(_creepStep),
            _live.size());
    }

private:
    struct Fighter
    {
        FuryMeter fury;
        Act act = Act::None;
        uint64 actStartMs = 0;
        uint64 actUntilMs = 0;
        float lastPct = 100.f;      // the health percent the partner's meter last read
        bool roared = false;        // heroic: a landed roar makes the next spin 9 s
        bool held = false;          // heroic: at the 30% line
        bool vengeance = false;     // normal: the partner is down
        // the storm
        MechanicHandle stormZone;
        uint32 spinMs = 0;
        uint64 nextRepickMs = 0;
        Vec2 lastPos;
        float walkedYd = 0.f;
        // the execute
        ObjectGuid victim;
        uint64 repathAtMs = 0;
    };

    struct SunkRecord
    {
        ObjectGuid player;
        uint64 sunkAtMs = 0;
        std::optional<Side> executioner;
    };

    struct PitRecord
    {
        MechanicHandle zone;
        ObjectGuid stalker;
        uint64 closeAtMs = 0;       // 0: never (the pits after his normal Frenzy)
        bool trail = false;
    };

    static DungeonKit::HeldBodySpec BodySpec()
    {
        DungeonKit::HeldBodySpec spec;
        spec.holds = 1;
        spec.dungeon = kLogDungeon;
        spec.boss = kBoss;
        return spec;
    }

    // Runs `fn(ai, args...)` on this boss when a registry or kit callback fires, if he is still in the same fight.
    // Captures the map, the guid and the cleanup count only (a kept lambda must not hold a Unit*).
    template <typename Fn>
    auto OnUkorz(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        uint32 const generation = _generation;
        return [map, guid, generation, fn](auto&&... args)
        {
            Creature* boss = map ? map->GetCreature(guid) : nullptr;
            auto* ai = boss && boss->IsAIEnabled ? dynamic_cast<boss_ukorz_rework*>(boss->AI()) : nullptr;
            if (ai && ai->_generation == generation)
                fn(*ai, std::forward<decltype(args)>(args)...);
        };
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Units
    // ----------------------------------------------------------------------------------------------------------------

    Creature* Ruuzlu() const
    {
        return instance ? instance->GetCreature(kGuidRuuzlu) : nullptr;
    }

    Creature* UnitOf(Side side) const
    {
        return side == Side::Ukorz ? me : Ruuzlu();
    }

    bool RuuzluStands() const
    {
        Creature* ruuzlu = Ruuzlu();
        return ruuzlu && ruuzlu->IsAlive() && ruuzlu->IsInWorld();
    }

    // Alive and fighting (Ukorz: not a held body).
    bool Stands(Side side) const
    {
        if (side == Side::Ukorz)
            return me->IsAlive() && !_body.Fallen();
        return RuuzluStands();
    }

    bool Free(Side side) const
    {
        Creature* unit = UnitOf(side);
        return unit && Stands(side) && _f[Index(side)].act == Act::None && !unit->HasUnitState(UNIT_STATE_CASTING);
    }

    std::optional<Side> SideOf(Creature const* unit) const
    {
        if (unit == me)
            return Side::Ukorz;
        if (unit && unit->GetEntry() == NPC_RUUZLU)
            return Side::Ruuzlu;
        return std::nullopt;
    }

    uint32 FurySpell() const { return _heroic ? SPELL_UK_FURY_HEROIC : SPELL_UK_FURY; }
    uint32 RoarSpell() const { return _heroic ? SPELL_UK_ROAR_HEROIC : SPELL_UK_ROAR; }

    // Every living, non-GM player on the mesa in combat with either boss (L6: picks filter by the arena and z).
    std::vector<Player*> MesaPlayers() const
    {
        std::vector<Player*> out;
        Map* map = me->GetMap();
        if (!map)
            return out;
        Creature* ruuzlu = Ruuzlu();
        for (auto const& ref : map->GetPlayers())
            if (Player* player = ref.GetSource())
                if (CountsAsPlayer(player) && OnMesa(player)
                    && (player->IsInCombatWith(me) || (ruuzlu && player->IsInCombatWith(ruuzlu))))
                    out.push_back(player);
        return out;
    }

    Player* RandomMesaPlayer(std::vector<ObjectGuid> const& exclude = {}) const
    {
        std::vector<Player*> pool;
        for (Player* player : MesaPlayers())
            if (std::find(exclude.begin(), exclude.end(), player->GetGUID()) == exclude.end())
                pool.push_back(player);
        return pool.empty() ? nullptr : pool[urand(0, uint32(pool.size()) - 1)];
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The director
    // ----------------------------------------------------------------------------------------------------------------

    void Direct(uint32 diff)
    {
        // Normal: Ukorz lies as a held body and Ruuzlu fell: the real death, the credit.
        if (_body.Fallen() && !RuuzluStands())
        {
            Log("finish", "Ruuzlu fell: the chief dies");
            _body.Finish(me, nullptr);
            return;
        }
        if (_body.Fallen() && !_fallSeen)
        {
            // Normal: he lies as a held body until Ruuzlu falls; Ruuzlu fights on with Vengeance.
            _fallSeen = true;
            EndAct(Side::Ukorz, "fell");
            me->RemoveAurasDueToSpell(FurySpell());
            _f[Index(Side::Ukorz)].fury.Reset();
            Log("fall", "a held body until Ruuzlu falls");
        }

        if (_phase == Phase::One)
        {
            UpdateMeters(diff);
            if (_heroic)
                UpdateHold();
            else
                UpdateFrenzy();
            if (!_engaged)
                return;
            if (_phase == Phase::One)
                StartDueFuryActs();
        }
        for (Side side : { Side::Ukorz, Side::Ruuzlu })
        {
            UpdateAct(side);
            if (!_engaged)
                return;
        }
        UpdateSunk();
        if (!_engaged)
            return;
        UpdateBeats();
        UpdateCreep();
        UpdatePits();
        _rescues.Update(me, diff);
        UpdateFavored();
        RefreshDescriptor();
    }

    // UK1, UK9: both meters from the partners' health lost since the last tick.
    void UpdateMeters(uint32 diff)
    {
        std::array<float, 2> lost{ 0.f, 0.f };
        std::array<bool, 2> up{ Stands(Side::Ukorz), Stands(Side::Ruuzlu) };
        for (Side side : { Side::Ukorz, Side::Ruuzlu })
        {
            Fighter& f = _f[Index(side)];
            Creature* unit = UnitOf(side);
            if (!up[Index(side)] || !unit)
                continue;
            float const pct = unit->GetHealthPct();
            lost[Index(side)] = std::max(0.f, f.lastPct - pct);
            f.lastPct = pct;
        }
        for (Side side : { Side::Ukorz, Side::Ruuzlu })
        {
            if (!up[Index(side)])
                continue;
            Side const partner = Other(side);
            Fighter& f = _f[Index(side)];
            FuryEvents const e = f.fury.Update(_clockMs, diff, lost[Index(partner)], up[Index(partner)], _heroic,
                !_heroic);
            if (e.gained || e.faded)
            {
                SetFuryAura(side);
                Log("fury", Acore::StringFormat("who={} stacks={} gained={} faded={} partner-lost={:.1f}%",
                    SideName(side), f.fury.Stacks(), e.gained, e.faded, lost[Index(partner)]));
            }
            bool const vengeance = !_heroic && !up[Index(partner)];
            if (vengeance && !f.vengeance)
            {
                f.vengeance = true;
                if (Creature* unit = UnitOf(side))
                    unit->CastSpell(unit, SPELL_UK_VENGEANCE, true);
                Log("vengeance", Acore::StringFormat("who={} stacks={}", SideName(side), f.fury.Stacks()));
            }
        }
    }

    void SetFuryAura(Side side)
    {
        Creature* unit = UnitOf(side);
        if (!unit || !unit->IsAlive())
            return;
        uint32 const want = _f[Index(side)].fury.Stacks();
        uint32 const have = DungeonKit::Stacks(unit, FurySpell());
        if (want != have)
            DungeonKit::AddStacks(unit, FurySpell(), int32(want) - int32(have), unit, Tune::kFuryMaxStacks);
    }

    // UK2, UK3: a full meter storms, a meter at 5 roars (once per fill), when the boss is free.
    void StartDueFuryActs()
    {
        for (Side side : { Side::Ukorz, Side::Ruuzlu })
        {
            if (!Free(side))
                continue;
            FuryMeter const& fury = _f[Index(side)].fury;
            if (fury.Stacks() >= Tune::kFuryMaxStacks)
                StartStorm(side, "full");
            else if (!fury.RoarUsed() && fury.Stacks() >= Tune::kRoarAtStacks)
                StartRoar(side);
        }
    }

    // UK8 normal: Ukorz's 30%.
    void UpdateFrenzy()
    {
        if (_frenzied || !Stands(Side::Ukorz) || me->GetHealthPct() > Tune::kFrenzyAtPct)
            return;
        Frenzy("30%");
    }

    void Frenzy(char const* why)
    {
        _frenzied = true;
        me->CastSpell(me, SPELL_FRENZY, true);
        Talk(SAY_UKORZ_FRENZY);
        // Normal: the pits stop closing from here to his death (the ones open now too). Heroic phase 3 keeps the 30 s
        // (SP's phase 3 space math counts two pits at a time; designer question).
        if (!_heroic)
        {
            _pitsStay = true;
            for (PitRecord& pit : _pits)
                if (!pit.trail)
                    pit.closeAtMs = 0;
        }
        Log("frenzy", Acore::StringFormat("why={} health={:.0f}% pits-stay={}", why, me->GetHealthPct(),
            _pitsStay ? 1 : 0));
    }

    // UK9 heroic: each holds at 30% until the other is there; both there: UK10.
    void UpdateHold()
    {
        for (Side side : { Side::Ukorz, Side::Ruuzlu })
        {
            Creature* unit = UnitOf(side);
            Fighter& f = _f[Index(side)];
            if (!unit || !Stands(side) || f.held || !AtHold(unit->GetHealth(), unit->GetMaxHealth(), Tune::kHoldPct))
                continue;
            f.held = true;
            unit->CastSpell(unit, SPELL_UK_HELD, true);
            if (side == Side::Ukorz)
                Talk(SAY_UKORZ_HOLD);
            else if (unit->IsAIEnabled && unit->AI())
                unit->AI()->Talk(SAY_RUUZLU_HOLD);
            Log("hold", Acore::StringFormat("who={} health={}", SideName(side), unit->GetHealth()));
        }
        if (_f[Index(Side::Ukorz)].held && _f[Index(Side::Ruuzlu)].held && Stands(Side::Ukorz) && RuuzluStands())
            StartCall("both at 30%");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The acts
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateAct(Side side)
    {
        Fighter& f = _f[Index(side)];
        Creature* unit = UnitOf(side);
        if (f.act == Act::None)
            return;
        if (!unit || !Stands(side))
        {
            EndAct(side, "down");
            return;
        }
        switch (f.act)
        {
            case Act::None:
                break;
            case Act::Roar:
            case Act::Stamp:
                if (_clockMs >= f.actUntilMs)
                    EndAct(side, "done");
                break;
            case Act::StormWindup:
                if (_clockMs >= f.actUntilMs)
                    StartSpin(side);
                break;
            case Act::StormSpin:
                UpdateSpin(side);
                break;
            case Act::ExecuteWalk:
                UpdateExecuteWalk(side);
                break;
            case Act::ExecuteCast:
                if (_clockMs >= f.actUntilMs)
                    EndExecute(side, "backstop");
                break;
            case Act::Lash:
                if (_clockMs >= f.actUntilMs)
                {
                    f.act = Act::None;
                    LashResolve();
                }
                break;
            case Act::Call:
                if (_clockMs >= f.actUntilMs)
                    StartPhaseThree("backstop");
                break;
        }
    }

    // Any act, however it stands, ends now: the bar stopped, the look off, the walk over, back to fighting.
    void EndAct(Side side, char const* why)
    {
        Fighter& f = _f[Index(side)];
        Creature* unit = UnitOf(side);
        Act const act = f.act;
        if (act == Act::None)
            return;
        if (act == Act::ExecuteWalk || act == Act::ExecuteCast)
        {
            EndExecute(side, why);
            return;
        }
        f.act = Act::None;
        if (act == Act::StormWindup || act == Act::StormSpin)
        {
            Mechanic::Cancel(me, f.stormZone);
            f.stormZone = MechanicHandle();
        }
        if (unit && unit->IsAlive())
        {
            unit->RemoveAurasDueToSpell(SPELL_UK_STORM_SPIN);
            if (unit->HasUnitState(UNIT_STATE_CASTING))
                InterruptOwn(unit);
            unit->StopMoving();
            unit->GetMotionMaster()->Clear();
            if (Stands(side))
                ResumeFighting(unit);
        }
        Log("act-end", Acore::StringFormat("who={} act={} why={}", SideName(side), uint32(act), why));
    }

    void InterruptOwn(Creature* unit)
    {
        _ownInterrupt = true;
        unit->InterruptNonMeleeSpells(false);
        _ownInterrupt = false;
    }

    // A cast of either boss started, landed or was stopped (a kick, a silence, his own stop).
    void OnCast(Side side, uint32 spellId, bool landed)
    {
        if (!_engaged)
            return;
        Fighter& f = _f[Index(side)];
        switch (spellId)
        {
            case SPELL_UK_ROAR:
            case SPELL_UK_ROAR_HEROIC:
                if (f.act != Act::Roar)
                    return;
                f.act = Act::None;
                if (landed)
                {
                    f.fury.Fill();
                    SetFuryAura(side);
                    if (_heroic)
                        f.roared = true;
                }
                Log(landed ? "roar-landed" : "roar-stopped", Acore::StringFormat("who={} stacks={}", SideName(side),
                    f.fury.Stacks()));
                break;
            case SPELL_UK_EXECUTE_BAR:
                if (f.act != Act::ExecuteCast)
                    return;
                if (landed)
                    ExecuteLands(side);
                else
                    EndExecute(side, "stopped");
                break;
            case SPELL_UK_CALL:
                if (side == Side::Ukorz && _phase == Phase::Call)
                    StartPhaseThree(landed ? "cast" : "stopped");
                break;
            default:
                break;
        }
    }

    // --- UK2 Battle Roar ---------------------------------------------------------------------------------------------

    void StartRoar(Side side)
    {
        Creature* unit = UnitOf(side);
        Fighter& f = _f[Index(side)];
        if (!unit)
            return;
        f.fury.UseRoar();
        unit->StopMoving();
        SpellCastResult const result = unit->CastSpell(unit, RoarSpell(), false);
        if (result != SPELL_CAST_OK)
        {
            // A kick's school lockout (Fire) or a silence: no roar this fill.
            Log("roar-refused", Acore::StringFormat("who={} result={}", SideName(side), uint32(result)));
            return;
        }
        f.act = Act::Roar;
        f.actStartMs = _clockMs;
        f.actUntilMs = _clockMs + Tune::kRoarCastMs(_heroic) + Tune::kRoarBackstopMs;
        Log("roar", Acore::StringFormat("who={} stacks={} cast={}ms", SideName(side), f.fury.Stacks(),
            Tune::kRoarCastMs(_heroic)));
    }

    // --- UK3 Bladestorm, UK4 the trail -------------------------------------------------------------------------------

    void StartStorm(Side side, char const* why)
    {
        Creature* unit = UnitOf(side);
        Fighter& f = _f[Index(side)];
        if (!unit)
            return;
        uint32 spin = Tune::kStormSpinMs(_heroic);
        if (_heroic && f.roared)
            spin = Tune::kStormRoaredSpinMs;
        f.roared = false;
        if (_phase == Phase::One)
        {
            f.fury.Empty();
            SetFuryAura(side);
        }
        if (side == Side::Ukorz)
            Talk(SAY_UKORZ_STORM);
        else if (unit->IsAIEnabled && unit->AI())
            unit->AI()->Talk(SAY_RUUZLU_STORM);
        StopFighting(unit);
        unit->CastSpell(unit, SPELL_UK_FURY_FULL, true);
        unit->CastSpell(unit, SPELL_UK_STORM_WINDUP, false);

        float const pct = Tune::kStormTickPct(_heroic);
        MechanicRef ring = Mechanic::Circle(me, unit, Tune::kStormRadiusYd, Ms(Tune::kStormWindupMs));
        ring.AnchorOn(unit).Persistent(Ms(spin), Ms(Tune::kStormTickMs)).Damage(pct).TankDamage(pct)
            .School(SPELL_SCHOOL_NORMAL).Spell(SPELL_UK_STORM).ZTolerance(kZBandYd).Within(Bounds())
            .Tag(TAG_UK_STORM);
        f.stormZone = ring.Handle();
        Track(f.stormZone);
        f.act = Act::StormWindup;
        f.actStartMs = _clockMs;
        f.actUntilMs = _clockMs + Tune::kStormWindupMs;
        f.spinMs = spin;
        Log("storm", Acore::StringFormat("who={} why={} spin={}ms tick={:.0f}% registered={}", SideName(side), why,
            spin, pct, ring.IsValid() ? 1 : 0));
    }

    void StartSpin(Side side)
    {
        Creature* unit = UnitOf(side);
        Fighter& f = _f[Index(side)];
        f.act = Act::StormSpin;
        f.actUntilMs = _clockMs + f.spinMs;
        f.nextRepickMs = _clockMs;
        f.lastPos = DungeonKit::PlaneOf(unit);
        f.walkedYd = 0.f;
        unit->CastSpell(unit, SPELL_UK_STORM_SPIN, true);
        DungeonKit::ShortenAura(unit, SPELL_UK_STORM_SPIN, unit->GetGUID(), Ms(f.spinMs));
        UpdateSpin(side);
    }

    // The walk: a new random player on the mesa (the tank included) every 2 s, at 5 yd/s (RB-22: the walk is the
    // mechanic; it carries the boss up to 45 yd and never leaves the mesa: the target is on it).
    void UpdateSpin(Side side)
    {
        Creature* unit = UnitOf(side);
        Fighter& f = _f[Index(side)];
        if (_clockMs >= f.nextRepickMs)
        {
            f.nextRepickMs = _clockMs + Tune::kStormRepickMs;
            if (Player* target = RandomMesaPlayer())
                unit->GetMotionMaster()->MovePoint(POINT_UK_STORM, target->GetPosition(), FORCED_MOVEMENT_NONE,
                    Tune::kStormWalkYdS);
        }
        if (_heroic)
        {
            Vec2 const now = DungeonKit::PlaneOf(unit);
            f.walkedYd += DungeonKit::Distance(f.lastPos, now);
            f.lastPos = now;
            for (uint32 drops = TrailDrops(f.walkedYd); drops > 0; --drops)
            {
                f.walkedYd -= Tune::kTrailStepYd;
                DropTrail(unit->GetPosition());
            }
        }
        if (_clockMs >= f.actUntilMs)
            EndAct(side, "spun");
    }

    void DropTrail(Position const& at)
    {
        std::size_t trails = 0;
        for (PitRecord const& pit : _pits)
            if (pit.trail)
                ++trails;
        if (trails >= Tune::kTrailCap)
            return;
        PitRecord pit;
        pit.trail = true;
        pit.closeAtMs = _clockMs + Tune::kTrailLifeMs;
        if (Creature* stalker = me->SummonCreature(NPC_ZF_QUICKSAND, at, TEMPSUMMON_TIMED_DESPAWN,
            Tune::kTrailLifeMs + 1000))
        {
            stalker->CastSpell(stalker, SPELL_UK_TRAIL_LOOK, true);
            pit.stalker = stalker->GetGUID();
        }
        MechanicRef ref = Mechanic::Circle(me, at, Tune::kTrailRadiusYd, Ms(Tune::kPitTickMs));
        ref.Persistent(Ms(Tune::kForeverMs), Ms(Tune::kPitTickMs)).Rider(SPELL_UK_QUICKSAND).NoFillTimer()
            .ZTolerance(kZBandYd).Within(Bounds()).Tag(TAG_UK_TRAIL);
        pit.zone = ref.Handle();
        Track(pit.zone);
        _pits.push_back(pit);
    }

    // --- UK5 Sinking Sands, UK11 the sands rise ----------------------------------------------------------------------

    // The stamp: the bar, then 1 / 2 pits under random players (`forced` first when given: the GM test).
    void Stamp(Player* forced)
    {
        std::vector<ObjectGuid> exclude;
        for (SunkRecord const& s : _sunk)
            exclude.push_back(s.player);
        std::vector<Player*> targets;
        if (CountsAsPlayer(forced) && !IsSunk(forced))
        {
            targets.push_back(forced);
            exclude.push_back(forced->GetGUID());
        }
        uint32 const count = Tune::kPitCount(_heroic || _phase == Phase::Three);
        while (targets.size() < count)
        {
            Player* pick = RandomMesaPlayer(exclude);
            if (!pick)
                break;
            targets.push_back(pick);
            exclude.push_back(pick->GetGUID());
        }
        if (targets.empty())
        {
            Log("stamp-skip", "nobody on the mesa to stand a pit under");
            return;
        }
        uint32 const castMs = Tune::kStampCastMs(_heroic);
        bool const emote = _clockMs >= _stampEmoteAtMs;
        if (emote)
            _stampEmoteAtMs = _clockMs + Tune::kStampEmoteGapMs;
        me->StopMoving();
        DungeonKit::CastBar(me, _heroic ? SPELL_UK_STAMP_HEROIC : SPELL_UK_STAMP, nullptr,
            emote ? std::optional<uint8>(EMOTE_UKORZ_STAMP) : std::nullopt, targets.front());
        Fighter& f = _f[Index(Side::Ukorz)];
        f.act = Act::Stamp;
        f.actStartMs = _clockMs;
        f.actUntilMs = _clockMs + castMs;
        std::string names;
        for (Player* target : targets)
        {
            OpenPit(target->GetPosition(), castMs);
            names += (names.empty() ? "" : ",") + target->GetName();
        }
        Log("stamp", Acore::StringFormat("pits={} under={} warn={}ms", targets.size(), names, castMs));
    }

    // A 6 yd pit at `at` after `warnMs`: everyone inside at the resolve sinks; then 30 s of quicksand.
    void OpenPit(Position const& at, uint32 warnMs)
    {
        MechanicRef ref = Mechanic::Circle(me, at, Tune::kPitRadiusYd, Ms(warnMs));
        ref.ZTolerance(kZBandYd).Within(Bounds()).Tag(TAG_UK_PIT)
            .OnResolve(OnUkorz([at](boss_ukorz_rework& ai, BossMechanics::ResolveResult const& r)
            {
                if (r.fizzled)
                    return;
                for (ObjectGuid const& guid : r.hits)
                    if (Player* player = ObjectAccessor::GetPlayer(*ai.me, guid))
                        ai.Sink(player, "pit");
                ai.PitLingers(at);
            }));
        Track(ref.Handle());
    }

    void PitLingers(Position const& at)
    {
        PitRecord pit;
        pit.closeAtMs = _pitsStay ? 0 : _clockMs + Tune::kPitLifeMs;
        if (Creature* stalker = me->SummonCreature(NPC_ZF_QUICKSAND, at, TEMPSUMMON_MANUAL_DESPAWN))
        {
            stalker->CastSpell(stalker, SPELL_UK_PIT_LOOK, true);
            pit.stalker = stalker->GetGUID();
        }
        MechanicRef ref = Mechanic::Circle(me, at, Tune::kPitRadiusYd, Ms(Tune::kPitTickMs));
        ref.Persistent(Ms(Tune::kForeverMs), Ms(Tune::kPitTickMs)).Rider(SPELL_UK_QUICKSAND).NoFillTimer()
            .ZTolerance(kZBandYd).Within(Bounds()).Tag(TAG_UK_QUICKSAND);
        pit.zone = ref.Handle();
        Track(pit.zone);
        _pits.push_back(pit);
    }

    void UpdatePits()
    {
        for (auto it = _pits.begin(); it != _pits.end();)
        {
            if (!it->closeAtMs || _clockMs < it->closeAtMs)
            {
                ++it;
                continue;
            }
            Mechanic::Cancel(me, it->zone);
            if (Creature* stalker = ObjectAccessor::GetCreature(*me, it->stalker))
                stalker->DespawnOrUnsummon();
            it = _pits.erase(it);
        }
    }

    // --- UK6 Sunk and the rescue -------------------------------------------------------------------------------------

    bool IsSunk(Player const* player) const
    {
        return player && std::any_of(_sunk.begin(), _sunk.end(), [player](SunkRecord const& s)
        {
            return s.player == player->GetGUID();
        });
    }

    void Sink(Player* player, char const* why)
    {
        if (!CountsAsPlayer(player) || IsSunk(player))
            return;
        me->CastSpell(player, SPELL_UK_SUNK, true);
        if (!player->HasAura(SPELL_UK_SUNK))
        {
            Log("sunk-refused", Acore::StringFormat("player={} why={}", player->GetName(), why));
            return;
        }
        SunkRecord record;
        record.player = player->GetGUID();
        record.sunkAtMs = _clockMs;
        _sunk.push_back(record);

        DungeonKit::DwellSoakSpec spec;
        spec.radius = Tune::kRescueRadiusYd;
        spec.zBand = kZBandYd;
        spec.dwell = Ms(Tune::kRescueDwellMs);
        spec.excludeAura = SPELL_UK_SUNK;
        spec.tag = TAG_UK_RESCUE;
        BossMechanics::SpotBounds const bounds = Bounds();
        spec.configure = [bounds](MechanicRef& ref) { ref.Within(bounds); };
        spec.onDone = OnUkorz([](boss_ukorz_rework& ai, Player* taker, Unit* anchor)
        {
            if (anchor)
                ai.EndSunk(anchor->GetGUID(), Acore::StringFormat("rescued by {}", taker ? taker->GetName()
                    : std::string("someone")).c_str());
        });
        spec.onLost = OnUkorz([](boss_ukorz_rework& ai, ObjectGuid anchor)
        {
            ai.EndSunk(anchor, "lost");
        });
        spec.dungeon = kLogDungeon;
        spec.boss = kBoss;
        spec.name = "rescue";
        _rescues.Add(me, player, std::move(spec));
        Log("sunk", Acore::StringFormat("player={} why={} sunk={}", player->GetName(), why, _sunk.size()));
    }

    // The sunk player is out (rescued, executed, the root ran out, dead or gone): the root off, the held Soak and the
    // executioner's walk or bar stopped.
    void EndSunk(ObjectGuid guid, char const* why)
    {
        auto it = std::find_if(_sunk.begin(), _sunk.end(), [guid](SunkRecord const& s) { return s.player == guid; });
        if (it == _sunk.end())
            return;
        std::optional<Side> const executioner = it->executioner;
        _sunk.erase(it);
        if (Player* player = ObjectAccessor::GetPlayer(*me, guid))
            player->RemoveAurasDueToSpell(SPELL_UK_SUNK);
        _rescues.CancelOn(me, guid);
        if (executioner && _f[Index(*executioner)].victim == guid)
            EndExecute(*executioner, why);
        Log("sunk-end", Acore::StringFormat("why={} sunk={}", why, _sunk.size()));
    }

    void UpdateSunk()
    {
        std::vector<ObjectGuid> out;
        for (SunkRecord const& s : _sunk)
        {
            Player* player = ObjectAccessor::GetPlayer(*me, s.player);
            if (!player || !player->IsAlive() || !player->HasAura(SPELL_UK_SUNK))
                out.push_back(s.player);
        }
        for (ObjectGuid const& guid : out)
            EndSunk(guid, "the root ended");

        // Section 7 #42 A: who walks to each sunk player still waiting, in the order they sank.
        for (SunkRecord& s : _sunk)
        {
            if (s.executioner)
                continue;
            ExecutionerView v;
            v.ruuzluStands = RuuzluStands();
            v.ruuzluFree = Free(Side::Ruuzlu);
            v.ukorzStands = Stands(Side::Ukorz) && _phase != Phase::Call;
            v.ukorzFree = Free(Side::Ukorz);
            v.heroicPhaseOne = _heroic && _phase == Phase::One;
            std::optional<Side> const who = ExecutionerFor(v);
            if (!who)
                break;      // in order: the next waits for a free executioner too
            StartExecute(*who, s);
        }
    }

    // --- UK7 Execute of the sunk -------------------------------------------------------------------------------------

    // RB-22: the walk carries the executioner up to the mesa's width (80 yd) to a sunk player on it; that is the
    // mechanic (his leaving the tank is the rescue's clock).
    void StartExecute(Side side, SunkRecord& s)
    {
        Creature* unit = UnitOf(side);
        Player* victim = ObjectAccessor::GetPlayer(*me, s.player);
        if (!unit || !victim)
            return;
        Fighter& f = _f[Index(side)];
        s.executioner = side;
        f.victim = s.player;
        f.act = Act::ExecuteWalk;
        f.actStartMs = _clockMs;
        f.repathAtMs = 0;
        StopFighting(unit);
        Log("execute-walk", Acore::StringFormat("who={} sunk={} distance={:.1f}", SideName(side), victim->GetName(),
            unit->GetExactDist2d(victim)));
        UpdateExecuteWalk(side);
    }

    void UpdateExecuteWalk(Side side)
    {
        Creature* unit = UnitOf(side);
        Fighter& f = _f[Index(side)];
        Player* victim = ObjectAccessor::GetPlayer(*me, f.victim);
        if (!victim || !victim->HasAura(SPELL_UK_SUNK))
        {
            EndExecute(side, "freed on the way");
            return;
        }
        if (_clockMs >= f.actStartMs + Tune::kExecuteWalkLimitMs)
        {
            EndExecute(side, "never reached them");
            return;
        }
        if (unit->GetExactDist2d(victim) > Tune::kExecuteReachYd)
        {
            if (_clockMs >= f.repathAtMs)
            {
                f.repathAtMs = _clockMs + kExecuteRepathMs;
                unit->GetMotionMaster()->MovePoint(POINT_UK_EXECUTE, victim->GetPosition());
            }
            return;
        }
        unit->StopMoving();
        unit->GetMotionMaster()->Clear();
        if (unit->CastSpell(victim, SPELL_UK_EXECUTE_BAR, false) != SPELL_CAST_OK)
        {
            EndExecute(side, "bar refused");
            return;
        }
        f.act = Act::ExecuteCast;
        f.actUntilMs = _clockMs + Tune::kExecuteCastMs + Tune::kExecuteBackstopMs;
        // The root holds until the bar ends: the Execute lands only on someone nobody came back for.
        uint32 const hold = Tune::kExecuteCastMs + Tune::kExecuteHoldSlackMs;
        if (Aura* root = victim->GetAura(SPELL_UK_SUNK))
            if (root->GetDuration() >= 0 && uint32(root->GetDuration()) < hold)
            {
                root->SetMaxDuration(int32(hold));
                root->SetDuration(int32(hold));
            }
        Log("execute-cast", Acore::StringFormat("who={} sunk={} after={}ms", SideName(side), victim->GetName(),
            _clockMs - f.actStartMs));
    }

    void ExecuteLands(Side side)
    {
        Creature* unit = UnitOf(side);
        Fighter& f = _f[Index(side)];
        ObjectGuid const guid = f.victim;
        Player* victim = ObjectAccessor::GetPlayer(*me, guid);
        if (unit && CountsAsPlayer(victim) && victim->HasAura(SPELL_UK_SUNK))
        {
            float const pct = Tune::kExecutePct(_heroic)
                * (_phase == Phase::One ? FuryFactor(f.fury.Stacks(), _heroic) : 1.f);
            uint32 const damage = ScriptHit(unit, victim, SPELL_UK_EXECUTE, pct);
            Log("execute", Acore::StringFormat("who={} sunk={} pct={:.0f} damage={}", SideName(side),
                victim->GetName(), pct, damage));
        }
        EndExecute(side, "landed", false);    // the bar is finishing: never interrupt it
        EndSunk(guid, "executed");
    }

    void EndExecute(Side side, char const* why, bool interrupt = true)
    {
        Fighter& f = _f[Index(side)];
        if (f.act != Act::ExecuteWalk && f.act != Act::ExecuteCast)
            return;
        Act const act = f.act;
        ObjectGuid const victim = f.victim;
        f.act = Act::None;
        f.victim = ObjectGuid::Empty;
        for (SunkRecord& s : _sunk)
            if (s.player == victim && s.executioner == side)
                s.executioner.reset();      // still sunk: another (or he again) may take them
        if (Creature* unit = UnitOf(side))
            if (unit->IsAlive())
            {
                if (interrupt && act == Act::ExecuteCast && unit->HasUnitState(UNIT_STATE_CASTING))
                    InterruptOwn(unit);
                unit->StopMoving();
                unit->GetMotionMaster()->Clear();
                if (Stands(side))
                    ResumeFighting(unit);
            }
        Log("execute-end", Acore::StringFormat("who={} why={}", SideName(side), why));
    }

    // A percent of the reference row (the tank's on the tank) on one player, owner Ukorz (rule 2): the amount is the
    // spell's base point. Returns it.
    uint32 ScriptHit(Creature* caster, Player* target, uint32 spellId, float pct)
    {
        uint32 const amount = DungeonKit::RefFlatOn(me, target, pct);
        CastSpellExtraArgs args(TRIGGERED_FULL_MASK);
        args.AddSpellBP0(static_cast<int32>(amount));
        caster->CastSpell(target, spellId, args);
        return amount;
    }

    // --- UK10 Call of Sul'thraze, UK11 the sands rise ----------------------------------------------------------------

    void StartCall(char const* why)
    {
        Creature* ruuzlu = Ruuzlu();
        if (!ruuzlu || !ruuzlu->IsAlive())
            return;
        _phase = Phase::Call;
        _phaseAtMs = _clockMs;
        for (Side side : { Side::Ukorz, Side::Ruuzlu })
            EndAct(side, "the Call");
        // Ruuzlu throws Sang'thraze to his chief and falls; Ukorz takes what life he had left.
        uint32 const given = ruuzlu->GetHealth();
        uint32 const before = me->GetHealth();
        if (ruuzlu->IsAIEnabled && ruuzlu->AI())
            ruuzlu->AI()->Talk(SAY_RUUZLU_CALL);
        me->SetHealth(CalledHealth(before, given, me->GetMaxHealth()));
        // Fury ends with the pair.
        for (Side side : { Side::Ukorz, Side::Ruuzlu })
            if (Creature* unit = UnitOf(side))
            {
                unit->RemoveAurasDueToSpell(FurySpell());
                unit->RemoveAurasDueToSpell(SPELL_UK_HELD);
                _f[Index(side)].fury.Reset();
            }
        Unit::Kill(ruuzlu, ruuzlu, false);
        Talk(SAY_UKORZ_CALL);
        StopFighting(me);
        me->CastSpell(me, SPELL_UK_CALL, false);
        Fighter& f = _f[Index(Side::Ukorz)];
        f.act = Act::Call;
        f.actStartMs = _clockMs;
        f.actUntilMs = _clockMs + Tune::kCallBackstopMs;
        // The sands rise: a pit under every player at once, and the donut along the walls.
        std::vector<Player*> const players = MesaPlayers();
        for (Player* player : players)
            OpenPit(player->GetPosition(), Tune::kRiseWarnMs);
        FormCreep();
        Log("call", Acore::StringFormat("why={} ukorz={} + ruuzlu={} -> {} pits={}", why, before, given,
            me->GetHealth(), players.size()));
        RefreshDescriptor();
    }

    void StartPhaseThree(char const* why)
    {
        if (_phase == Phase::Three)
            return;
        _phase = Phase::Three;
        _phaseThreeAtMs = _clockMs;
        Fighter& f = _f[Index(Side::Ukorz)];
        if (f.act == Act::Call)
        {
            f.act = Act::None;
            ResumeFighting(me);
        }
        if (!_frenzied)
            Frenzy("phase 3");
        _nextLashMs = _clockMs + Tune::kLashFirstMs;
        _nextStormMs = _clockMs + Tune::kPhase3StormFirstMs;
        _nextStampMs = _clockMs + Tune::kPhase3StampFirstMs;
        Log("phase3", Acore::StringFormat("why={} health={}", why, me->GetHealth()));
        RefreshDescriptor();
    }

    // --- the beats: UK5 the stamp (both phases), phase 3's Lash and Bladestorm ---------------------------------------

    void UpdateBeats()
    {
        if (!Free(Side::Ukorz))
            return;
        if (_phase == Phase::Three)
        {
            if (_clockMs >= _nextStormMs)
            {
                _nextStormMs = NextDue(_nextStormMs, Tune::kPhase3StormEveryMs, _clockMs);
                StartStorm(Side::Ukorz, "phase 3");
                return;
            }
            if (_clockMs >= _nextLashMs)
            {
                _nextLashMs = NextDue(_nextLashMs, Tune::kLashEveryMs, _clockMs);
                StartLash(nullptr);
                return;
            }
        }
        if (_phase != Phase::Call && _clockMs >= _nextStampMs)
        {
            uint32 const every = Tune::kStampEveryMs(_heroic || _phase == Phase::Three);
            _nextStampMs = NextDue(_nextStampMs, every, _clockMs);
            Stamp(nullptr);
        }
    }

    // --- UK12 Lash of Sul'thraze -------------------------------------------------------------------------------------

    void StartLash(Player* forced)
    {
        Player* target = CountsAsPlayer(forced) ? forced : RandomMesaPlayer();
        if (!target)
        {
            Log("lash-skip", "nobody on the mesa");
            return;
        }
        me->StopMoving();
        me->CastSpell(me, SPELL_UK_LASH_BAR, false);
        me->CastSpell(target, SPELL_UK_LASH_MARK, true);
        MechanicRef ref = Mechanic::Spread(me, Tune::kLashRadiusYd, Ms(Tune::kLashWarnMs));
        ref.Within(Bounds()).Tag(TAG_UK_LASH);
        Track(ref.Handle());
        _lashTarget = target->GetGUID();
        Fighter& f = _f[Index(Side::Ukorz)];
        f.act = Act::Lash;
        f.actStartMs = _clockMs;
        f.actUntilMs = _clockMs + Tune::kLashWarnMs;
        Log("lash", Acore::StringFormat("mark={}", target->GetName()));
    }

    // The chain, on his clock as the bar ends: the marked player, then every player within 8 yd of a struck one.
    void LashResolve()
    {
        Player* first = ObjectAccessor::GetPlayer(*me, _lashTarget);
        _lashTarget = ObjectGuid::Empty;
        if (first)
            first->RemoveAurasDueToSpell(SPELL_UK_LASH_MARK);
        if (!CountsAsPlayer(first) || !OnMesa(first))
        {
            Log("lash-fizzle", "the marked player is gone");
            return;
        }
        std::vector<Player*> players = MesaPlayers();
        auto it = std::find(players.begin(), players.end(), first);
        if (it == players.end())
            players.push_back(first);
        std::vector<Vec2> points;
        std::size_t firstIndex = 0;
        for (std::size_t i = 0; i < players.size(); ++i)
        {
            points.push_back(DungeonKit::PlaneOf(players[i]));
            if (players[i] == first)
                firstIndex = i;
        }
        std::vector<std::size_t> const chain = LashChain(points, firstIndex, Tune::kLashRadiusYd,
            Tune::kLashMaxJumps);
        std::string names;
        for (std::size_t index : chain)
        {
            Player* player = players[index];
            ScriptHit(me, player, SPELL_UK_LASH, Tune::kLashPct);
            if (player->IsAlive())
                me->CastSpell(player, SPELL_UK_LASH_DEBUFF, true);
            names += (names.empty() ? "" : ",") + player->GetName();
        }
        Log("lash-hit", Acore::StringFormat("struck={} who={}", chain.size(), names));
    }

    // --- UK13 Creeping Sands -----------------------------------------------------------------------------------------

    void FormCreep()
    {
        if (_creepFormed)
            return;
        _creepFormed = true;
        if (Creature* stalker = me->SummonCreature(NPC_ZF_CREEPING_SANDS, MesaCenter(), TEMPSUMMON_MANUAL_DESPAWN))
            _creepStalker = stalker->GetGUID();
        RegisterCreep(0, Tune::kCreepFormWarnMs);
    }

    // The donut at `step` (inside it the safe circle; at the last step the whole mesa), live after `warnMs`; the old
    // one is canceled as the new one goes live (UpdateCreep).
    void RegisterCreep(uint32 step, uint32 warnMs)
    {
        float const inner = CreepInnerYd(step);
        Position const center = MesaCenter();
        MechanicRef ref = inner > 0.f
            ? Mechanic::Donut(me, center, inner, Tune::kCreepOuterYd, Ms(warnMs))
            : Mechanic::Circle(me, center, Tune::kCreepOuterYd, Ms(warnMs));
        ref.Persistent(Ms(Tune::kForeverMs), Ms(Tune::kCreepTickMs)).Damage(Tune::kCreepPct)
            .TankDamage(Tune::kCreepPct).School(SPELL_SCHOOL_SHADOW).Spell(SPELL_UK_CREEPING)
            .Rider(SPELL_UK_QUICKSAND).ZTolerance(kCreepZBandYd).Within(CreepBounds(inner)).Tag(TAG_UK_CREEP);
        if (_creepNext)
            Mechanic::Cancel(me, _creepNext);   // a GM step over a pending one
        _creepNext = ref.Handle();
        Track(_creepNext);
        _creepSwapAtMs = _clockMs + warnMs;
        _creepStep = step;
        Log("creep", Acore::StringFormat("step={} inner={:.0f} outer={:.0f} warn={}ms registered={}", step, inner,
            Tune::kCreepOuterYd, warnMs, ref.IsValid() ? 1 : 0));
    }

    void UpdateCreep()
    {
        if (!_creepFormed)
            return;
        if (_creepSwapAtMs && _clockMs >= _creepSwapAtMs)
        {
            _creepSwapAtMs = 0;
            if (_creepLive)
                Mechanic::Cancel(me, _creepLive);
            _creepLive = _creepNext;
            _creepNext = MechanicHandle();
        }
        if (_phase == Phase::Three)
        {
            uint32 const step = CreepStep(_clockMs - _phaseThreeAtMs);
            if (step > _creepStep)
                RegisterCreep(step, Tune::kCreepStepWarnMs);
        }
    }

    // The bots' planned spots: the mesa, or the Creeping Sands' safe circle once it is up.
    BossMechanics::SpotBounds Bounds() const
    {
        return _creepFormed ? CreepBounds(CreepInnerYd(_creepStep)) : _floor;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateFavored()
    {
        Creature* ruuzlu = Ruuzlu();
        FavorView v;
        v.up[Index(Side::Ukorz)] = Stands(Side::Ukorz);
        v.up[Index(Side::Ruuzlu)] = RuuzluStands();
        v.held[Index(Side::Ukorz)] = _f[Index(Side::Ukorz)].held;
        v.held[Index(Side::Ruuzlu)] = _f[Index(Side::Ruuzlu)].held;
        v.healthPct[Index(Side::Ukorz)] = me->GetHealthPct();
        v.healthPct[Index(Side::Ruuzlu)] = ruuzlu ? ruuzlu->GetHealthPct() : 0.f;
        v.fury[Index(Side::Ukorz)] = _f[Index(Side::Ukorz)].fury.Stacks();
        v.fury[Index(Side::Ruuzlu)] = _f[Index(Side::Ruuzlu)].fury.Stacks();
        std::optional<Side> const pick = PickFavored(_favoredSide, v);
        if (pick != _favoredSide)
        {
            Log("favor", Acore::StringFormat("hit={} fury ukorz={} ruuzlu={} health ukorz={:.0f}% ruuzlu={:.0f}%",
                pick ? SideName(*pick) : "none", v.fury[0], v.fury[1], v.healthPct[0], v.healthPct[1]));
            _favoredSide = pick;
        }
        Creature* unit = pick ? UnitOf(*pick) : nullptr;
        _favored->store(unit ? unit->GetGUID().GetRawValue() : 0);
    }

    // A new descriptor whenever who stands or the phase changes (the favored boss changes live through _favored).
    void RefreshDescriptor()
    {
        uint32 const shape = uint32(_phase) | (Stands(Side::Ukorz) ? 0x10 : 0) | (RuuzluStands() ? 0x20 : 0)
            | (_heroic ? 0x40 : 0);
        if (shape != _describedShape)
            Describe();
    }

    void Describe()
    {
        using BossMechanics::Condition;
        using BossMechanics::IgnoreEntry;
        using BossMechanics::TargetEntry;
        using BossMechanics::Who;
        if (!_engaged)
            return;
        bool const uUp = Stands(Side::Ukorz);
        bool const rUp = RuuzluStands();
        _describedShape = uint32(_phase) | (uUp ? 0x10 : 0) | (rUp ? 0x20 : 0) | (_heroic ? 0x40 : 0);
        BossMechanics::Descriptor d;
        if (_phase == Phase::One)
        {
            if (uUp)
                d.interrupts.emplace_back(NPC_UKORZ, RoarSpell(), Tune::kRoarKickPriority);
            if (rUp)
                d.interrupts.emplace_back(NPC_RUUZLU, RoarSpell(), Tune::kRoarKickPriority);
        }
        if (_phase == Phase::One && uUp && rUp)
        {
            // Capture the shared pick only (never this, a Creature* or the instance).
            std::shared_ptr<std::atomic<uint64>> const favored = _favored;
            auto const isFavored = [favored](Unit const* unit)
            {
                return unit && favored->load() == unit->GetGUID().GetRawValue();
            };
            auto const isDisfavored = [favored](Unit const* unit)
            {
                uint64 const pick = favored->load();
                return unit && pick && pick != unit->GetGUID().GetRawValue();
            };
            for (auto const& [entry, partner] : { std::pair<uint32, uint32>{ NPC_UKORZ, NPC_RUUZLU },
                std::pair<uint32, uint32>{ NPC_RUUZLU, NPC_UKORZ } })
            {
                d.targets.push_back(TargetEntry(entry, 2, Who::Dps, Condition::Custom(isFavored))
                    .KillTogether(partner, Tune::kKillTogetherPct));
                d.targets.push_back(TargetEntry(entry, 1, Who::Dps).KillTogether(partner, Tune::kKillTogetherPct));
                d.ignores.push_back(IgnoreEntry(entry, Condition::Custom(isDisfavored)).For(Who::Dps));
            }
        }
        else if (rUp && !uUp)
            d.targets.emplace_back(NPC_RUUZLU, 1);
        d.ignores.emplace_back(NPC_ZF_QUICKSAND);
        d.ignores.emplace_back(NPC_ZF_CREEPING_SANDS);
        Mechanic::Describe(me, std::move(d));
        Log("describe", Acore::StringFormat("phase={} ukorz={} ruuzlu={}", uint32(_phase), uUp ? 1 : 0, rUp ? 1 : 0));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Reset and restore
    // ----------------------------------------------------------------------------------------------------------------

    // A wipe gives back a Ruuzlu who died in the failed attempt (never once the slot is DONE): Respawn on a dead
    // object, ForceCreatureRespawn when the object is gone (RB-20).
    void RestoreRuuzlu(char const* why)
    {
        if (!instance || !me->IsAlive() || instance->GetBossState(BOSS_UKORZ) == DONE)
            return;
        if (Creature* ruuzlu = Ruuzlu())
        {
            if (ruuzlu->IsAlive())
                return;
            ruuzlu->Respawn(true);
        }
        else
        {
            Map* map = me->GetMap();
            if (!map || map->GetCreatureRespawnTime(kSpawnRuuzlu) <= GameTime::GetGameTime().count())
                return;
            map->ForceCreatureRespawn(kSpawnRuuzlu);
        }
        Log("ruuzlu-restored", why);
    }

    void UpdateRestore(uint32 diff)
    {
        _restoreCheckMs += diff;
        if (_restoreCheckMs < kRestoreCheckMs)
            return;
        _restoreCheckMs = 0;
        RestoreRuuzlu("idle check");
    }

    // The fight's state: nothing registered, no stalker, held Soak, aura or act of it on anyone, both bosses given
    // back their react state (Reset, evade, death).
    void Cleanup(bool died)
    {
        ++_generation;
        _engaged = false;
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        _rescues.Clear(me);
        summons.DespawnAll();
        if (instance)
            for (uint32 const spell : { uint32(SPELL_UK_SUNK), uint32(SPELL_UK_QUICKSAND), uint32(SPELL_UK_LASH_MARK),
                uint32(SPELL_UK_LASH_DEBUFF) })
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
        for (Side side : { Side::Ukorz, Side::Ruuzlu })
        {
            Creature* unit = UnitOf(side);
            if (!unit || !unit->IsAlive())
                continue;
            for (uint32 const spell : { uint32(SPELL_UK_FURY), uint32(SPELL_UK_FURY_HEROIC),
                uint32(SPELL_UK_STORM_SPIN), uint32(SPELL_UK_HELD), uint32(SPELL_UK_VENGEANCE), SPELL_FRENZY })
                unit->RemoveAurasDueToSpell(spell);
            if (_f[Index(side)].act != Act::None && unit->HasUnitState(UNIT_STATE_CASTING))
                InterruptOwn(unit);
            unit->SetReactState(REACT_AGGRESSIVE);
        }
        _arena.Reset();
        for (Fighter& f : _f)
            f = Fighter{};
        _sunk.clear();
        _pits.clear();
        _phase = Phase::One;
        _clockMs = 0;
        _phaseAtMs = 0;
        _phaseThreeAtMs = 0;
        _cleaveAtMs = 0;
        _nextStampMs = 0;
        _nextLashMs = 0;
        _nextStormMs = 0;
        _stampEmoteAtMs = 0;
        _killLineAtMs = 0;
        _lashTarget = ObjectGuid::Empty;
        _creepFormed = false;
        _creepStalker = ObjectGuid::Empty;
        _creepLive = MechanicHandle();
        _creepNext = MechanicHandle();
        _creepSwapAtMs = 0;
        _creepStep = 0;
        _frenzied = false;
        _pitsStay = false;
        _fallSeen = false;
        _favoredSide.reset();
        _favored->store(0);
        _describedShape = 0;
        if (died)
            Log("cleanup", "death");
    }

    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 192)     // the oldest ones resolved long ago (live pits are re-listed below)
        {
            _live.erase(_live.begin(), _live.begin() + 96);
            for (PitRecord const& pit : _pits)
                if (std::find(_live.begin(), _live.end(), pit.zone) == _live.end())
                    _live.push_back(pit.zone);
            for (MechanicHandle const h : { _creepLive, _creepNext })
                if (h && std::find(_live.begin(), _live.end(), h) == _live.end())
                    _live.push_back(h);
        }
    }

    void Log(char const* mechanic, std::string const& detail = {}) const
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    DungeonKit::ArenaGuard _arena;
    BossMechanics::SpotBounds _floor;
    DungeonKit::HeldBody _body;
    DungeonKit::DwellSoaks _rescues;
    std::shared_ptr<std::atomic<uint64>> _favored;     // the kill order's pick (raw guid), read by the bots
    std::array<Fighter, 2> _f;
    std::vector<SunkRecord> _sunk;
    std::vector<PitRecord> _pits;
    std::vector<MechanicHandle> _live;
    std::optional<Side> _favoredSide;
    Phase _phase = Phase::One;
    uint64 _clockMs = 0;            // ms since the pull: every timer of the fight
    uint64 _phaseAtMs = 0;
    uint64 _phaseThreeAtMs = 0;
    uint64 _cleaveAtMs = 0;
    uint64 _nextStampMs = 0;
    uint64 _nextLashMs = 0;
    uint64 _nextStormMs = 0;
    uint64 _stampEmoteAtMs = 0;
    uint64 _killLineAtMs = 0;
    uint64 _creepSwapAtMs = 0;
    ObjectGuid _lashTarget;
    ObjectGuid _creepStalker;
    MechanicHandle _creepLive;
    MechanicHandle _creepNext;
    uint32 _creepStep = 0;
    uint32 _restoreCheckMs = 0;
    uint32 _generation = 0;         // bumped by every cleanup: a stale callback does nothing
    uint32 _describedShape = 0;
    bool _engaged = false;
    bool _heroic = false;
    bool _frenzied = false;
    bool _pitsStay = false;
    bool _creepFormed = false;
    bool _ownInterrupt = false;
    bool _evading = false;
    bool _fallSeen = false;
};

namespace
{
    boss_ukorz_rework* ChiefOf(Creature const* ruuzlu)
    {
        InstanceScript* instance = ruuzlu ? ruuzlu->GetInstanceScript() : nullptr;
        Creature* ukorz = instance ? instance->GetCreature(kGuidBossBase + BOSS_UKORZ) : nullptr;
        return ukorz && ukorz->IsAIEnabled ? dynamic_cast<boss_ukorz_rework*>(ukorz->AI()) : nullptr;
    }
}

// Ruuzlu 7797: melee and Cleave of his own; his acts are Ukorz's orders, his damage and casts are reported to him.
struct boss_ruuzlu_rework : public ScriptedAI
{
    explicit boss_ruuzlu_rework(Creature* creature)
        : ScriptedAI(creature), _arena(MesaArena(), LeashOptions("ruuzlu")) { }

    void Reset() override
    {
        _arena.Reset();
        _clockMs = 0;
        _cleaveAtMs = 0;
        me->SetReactState(REACT_AGGRESSIVE);
    }

    void JustEngagedWith(Unit* who) override
    {
        ScriptedAI::JustEngagedWith(who);
        _clockMs = 0;
        _cleaveAtMs = urand(Tune::kCleaveFirstMinMs, Tune::kCleaveFirstMaxMs);
        me->CastSpell(me, SPELL_BERSERKER_STANCE, true);
        _arena.Engage(me);
        OnBossPull(me, "ruuzlu");
        if (boss_ukorz_rework* chief = ChiefOf(me))
            chief->PartnerEngaged(who);
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        _arena.Reset();
        ScriptedAI::EnterEvadeMode(why);
        if (boss_ukorz_rework* chief = ChiefOf(me))
            chief->PartnerEvaded(why);
    }

    void JustDied(Unit* killer) override
    {
        _arena.Reset();
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "ruuzlu-death", Acore::StringFormat("killer={}",
            killer ? killer->GetName() : std::string("none")));
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        if (boss_ukorz_rework* chief = ChiefOf(me))
            damage = chief->RuuzluDamage(me, damage);
        ScriptedAI::DamageTaken(attacker, damage, type, mask);
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        ScriptedAI::OnSpellCast(spell);
        if (boss_ukorz_rework* chief = ChiefOf(me))
            chief->PartnerSpell(spell, true);
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        ScriptedAI::OnSpellFailed(spell);
        if (boss_ukorz_rework* chief = ChiefOf(me))
            chief->PartnerSpell(spell, false);
    }

    void UpdateAI(uint32 diff) override
    {
        ZulFarrak::NoAssist(me);        // rule 27, LESSONS L1: every tick, before UpdateVictim
        if (!UpdateVictim())
            return;
        _clockMs += diff;
        boss_ukorz_rework* chief = ChiefOf(me);
        bool const busy = chief && chief->Busy(Side::Ruuzlu);
        if (!busy && !_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (busy || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (_clockMs >= _cleaveAtMs)
        {
            _cleaveAtMs = _clockMs + urand(Tune::kCleaveEveryMinMs, Tune::kCleaveEveryMaxMs);
            if (Unit* victim = me->GetVictim())
                if (me->IsWithinMeleeRange(victim))
                    me->CastSpell(victim, SPELL_CLEAVE, false);
        }
        DoMeleeAttackIfReady();
    }

private:
    DungeonKit::ArenaGuard _arena;
    uint64 _clockMs = 0;
    uint64 _cleaveAtMs = 0;
};

// The quicksand under a pit or a Bladestorm trail (301025), and the Creeping Sands' anchor (301026): looks only, never
// in the fight (KIT_HELPER: not selectable, not attackable).
struct npc_zf_quicksand : public ScriptedAI
{
    explicit npc_zf_quicksand(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override { me->SetReactState(REACT_PASSIVE); }
    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void UpdateAI(uint32 /*diff*/) override { }
};

struct npc_zf_creeping_sands : public ScriptedAI
{
    explicit npc_zf_creeping_sands(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override { me->SetReactState(REACT_PASSIVE); }
    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void UpdateAI(uint32 /*diff*/) override { }
};

namespace
{
    boss_ukorz_rework* UkorzAI(ChatHandler* handler)
    {
        Creature* boss = ZfTest::FindBoss(handler, NPC_UKORZ);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_ukorz_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{} does not run the reworked script.", boss->GetName());
        return ai;
    }

    Side SideArg(Optional<uint32> side)
    {
        return side.value_or(0) == 1 ? Side::Ruuzlu : Side::Ukorz;
    }

    bool Fire(ChatHandler* handler, boss_ukorz_rework::TestMechanic mechanic, Side side, char const* what)
    {
        boss_ukorz_rework* ai = UkorzAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestFire(mechanic, side, handler->getSelectedPlayerOrSelf());
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Ukorz: {}.", what);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return ZfTest::ShowBossInfo(handler, NPC_UKORZ, BOSS_UKORZ);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_ukorz_rework* ai = UkorzAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Ukorz: {}", ai->TestState());
        return true;
    }

    // `.dbtest zf ukorz fury <0 ukorz | 1 ruuzlu> <stacks>`.
    bool HandleFury(ChatHandler* handler, uint32 side, uint32 stacks)
    {
        boss_ukorz_rework* ai = UkorzAI(handler);
        if (!ai)
            return false;
        if (!ai->TestFury(side == 1 ? Side::Ruuzlu : Side::Ukorz, stacks))
        {
            handler->SendErrorMessage("Only in phase 1, in combat, with that boss standing.");
            return false;
        }
        handler->PSendSysMessage("Ukorz: Fury set (UK1; 5 roars, 10 storms on the next tick).");
        return true;
    }

    bool HandleRoar(ChatHandler* handler, Optional<uint32> side)
    {
        return Fire(handler, boss_ukorz_rework::TestMechanic::Roar, SideArg(side),
            "Battle Roar (UK2; 0 Ukorz, 1 Ruuzlu)");
    }

    bool HandleStorm(ChatHandler* handler, Optional<uint32> side)
    {
        return Fire(handler, boss_ukorz_rework::TestMechanic::Storm, SideArg(side),
            "Bladestorm (UK3; heroic UK4 trail; 0 Ukorz, 1 Ruuzlu)");
    }

    bool HandleStamp(ChatHandler* handler)
    {
        return Fire(handler, boss_ukorz_rework::TestMechanic::Stamp, Side::Ukorz,
            "Sinking Sands, a pit under the selected player first (UK5)");
    }

    bool HandleSink(ChatHandler* handler)
    {
        return Fire(handler, boss_ukorz_rework::TestMechanic::Sink, Side::Ukorz,
            "the selected player sinks (UK6; the executioner walks, UK7)");
    }

    bool HandleCall(ChatHandler* handler)
    {
        return Fire(handler, boss_ukorz_rework::TestMechanic::Call, Side::Ukorz,
            "Call of Sul'thraze now (UK10, UK11, UK13; then phase 3)");
    }

    bool HandleLash(ChatHandler* handler)
    {
        return Fire(handler, boss_ukorz_rework::TestMechanic::Lash, Side::Ukorz,
            "Lash of Sul'thraze on the selected player (UK12)");
    }

    bool HandleCreep(ChatHandler* handler)
    {
        return Fire(handler, boss_ukorz_rework::TestMechanic::Creep, Side::Ukorz,
            "Creeping Sands: formed, or its next step (UK13)");
    }

    // `.dbtest zf ukorz heroic [0|1]`: the heroic form on a normal map until the end of the pull (phase 1 only).
    bool HandleHeroic(ChatHandler* handler, Optional<uint32> on)
    {
        boss_ukorz_rework* ai = UkorzAI(handler);
        if (!ai)
            return false;
        if (!ai->TestHeroic(on.value_or(1) != 0))
        {
            handler->SendErrorMessage("Only in combat, in phase 1.");
            return false;
        }
        handler->SendSysMessage("Set until the end of the pull (the reference row stays the map's).");
        return true;
    }

    ChatCommandTable const& UkorzTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",   HandleInfo,   SEC_GAMEMASTER, Console::No },
            { "state",  HandleState,  SEC_GAMEMASTER, Console::No },
            { "fury",   HandleFury,   SEC_GAMEMASTER, Console::No },
            { "roar",   HandleRoar,   SEC_GAMEMASTER, Console::No },
            { "storm",  HandleStorm,  SEC_GAMEMASTER, Console::No },
            { "stamp",  HandleStamp,  SEC_GAMEMASTER, Console::No },
            { "sink",   HandleSink,   SEC_GAMEMASTER, Console::No },
            { "call",   HandleCall,   SEC_GAMEMASTER, Console::No },
            { "lash",   HandleLash,   SEC_GAMEMASTER, Console::No },
            { "creep",  HandleCreep,  SEC_GAMEMASTER, Console::No },
            { "heroic", HandleHeroic, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_ukorz_rework()
{
    RegisterDungeonReworkCreatureAI(boss_ukorz_rework, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(boss_ruuzlu_rework, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_zf_quicksand, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_zf_creeping_sands, ZulFarrakRework::kInstanceScriptName);
    ZfTest::RegisterBoss("ukorz", UkorzTestCommands());
}
