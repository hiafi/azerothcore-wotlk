/*
 * mod-dungeon-bosses, Blackrock Depths D12: Lord Incendius's hard mode, Lord of the Lake (heroic only). Build spec:
 * docs/dungeons/blackrock-depths-2-shadowforge-city.md "Hard mode" and "Build spec" (IN9-IN14; rulings 81-84, 90),
 * handoff sections 3.5 row D12, 3.6, 3.7, 7 #14 A, 7 #15. It fights on D11's AI (boss_lord_incendius_rework) through
 * IncendiusFight.h: D11 makes one LordOfTheLake per heroic pull with DATA_CINDER_USED lit and calls its hooks; the
 * idle hook poses him in the lake out of combat. Pure rules, numbers and geometry: IncendiusHardModeLogic.h.
 *
 *   IN9  The Cinder     item 70621's use spell (211260, spell_brd_cinder_of_the_firelord): heroic, the user out of
 *                       combat on the island, Incendius alive and idle (a refusal keeps the item). It lights
 *                       DATA_CINDER_USED (saved until the hard mode kill or a reset: a wipe never burns it; the
 *                       instance arms the loot bit), the Cinder arcs into the lava, he yells (line 4), jumps off the
 *                       south-east edge and rises at kLakeLordSpot as the giant (his display 1204 at scale 9, rooted,
 *                       hovering at causeway height, line 8). Out of combat the giant waits (defensive: the group
 *                       pulls him); after a reload or a wipe he rises again (the idle hook).
 *   The pull            340k, one kill (no rebirth); both necks seal (D11's 4 yd bands, lethal after 5 s); the boss
 *                       leash is off (he stands in the lake). His own combat reach is small (kGiantReachYd: hunters
 *                       and wands are never too close, R-1-B M2); the melee and the tank hit his Hand (300828, on the
 *                       near rim by the tank's soak line), which shares his health: every hit on it lands on him and
 *                       its threat moves to him.
 *   Kit                 Curse and Fiery Burst as heroic; Fire Storm every 10 s, patches 20 s; Magma Fist every 20 s,
 *                       never the tank (ruling 90; a tank standing in its line is hit, ruling 88), its line starting
 *                       at its near end (R-1-B m3); Fire Storm, Magma Fist and Fiery Burst scaled by Firelord's Will;
 *                       Lava Surge off; his melee on the tank in the reach band (the script's swing).
 *   IN10 Crushing Fist  from 10 s, every 15 s: a 3 s 6 yd circle on the tank's spot; anyone else inside 45% +
 *                       Weakened (the circle spares the tank), the tank 35% (his hit to take, the script's).
 *   IN11 Arm Sweep      from 20 s, every 30 s: a 4 s cast (line 6), a 10 yd band across the floor at one of three
 *                       spots (never the same twice running); 30% and a throw over the far edge (the FallWatch: a fall
 *                       is death). Fire Storm, Magma Fist and Crushing Fist hold from 3 s before it to its end.
 *   IN12 Lava Spawn     from 15 s, every 20 s: 2 climb out on the long edges (line 9) and walk to The Black Anvil in
 *                       about 10 s; each that arrives heals him 5% and gives Firelord's Will (+10% damage, 10 max).
 *   IN13 The crumble    at 40, 80 and 120 s the next 2 yd of both long edges (D11's step, 5 s marker first), then no
 *                       more (section 7 #14 A: three steps).
 *   IN14 The Breath     every 1 s: nobody in the reach band (6 yd along the current near edge) for 3 s, he breathes
 *                       over the island (line 7), 8% a second to everyone until someone is back.
 *   Bots                kill order Lava Spawn; the melee and the tank strictly on the floor (no behind: behind him is
 *                       the lava); a tank-only soak line in the reach band; Crushing Fist spares the tank; the Arm
 *                       Sweep is a lethal Zone line (tag 15, G1's drill).
 *   The end             death: the lethal hit puts the giant on the near rim at the Hand's spot (gravity back on, so
 *                       the death does not drop him into the lava: R-1-B M1), where his corpse is looted; the
 *                       instance records BOSS_LORD_OF_THE_LAKE and clears the Cinder. Evade: his heroic health,
 *                       look, root and spot back, the spawns, Will and the zones gone (D11 despawns the summons and
 *                       clears the bands); the idle hook raises the giant again once the evade ends.
 *
 * Every firing logs one INFO line "brd incendius lake-<mechanic> ..." (module.dungeonbosses); `.dbtest brd lake <...>`
 * fires them.
 */

#include "BlackrockDepthsKit.h"
#include "BlackrockDepthsRework.h"
#include "BlackrockDepthsTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DataMap.h"
#include "DungeonKit.h"
#include "DungeonKitFlex.h"
#include "DungeonKitFlow.h"
#include "IncendiusFight.h"
#include "IncendiusHardModeLogic.h"
#include "IncendiusLogic.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ThreatManager.h"
#include "WorldSession.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdLordOfTheLake;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using BrdIncendius::IncendiusFight;
using BrdIncendius::IncendiusHardMode;

namespace
{
    char const* const kBossLogName = "incendius";
    char const* const kStateKey = "brd-lord-of-the-lake";
    // The bots' shapes (the no-behind carrier, the reach soak) outlast any pull; re-registered at every crumble step.
    constexpr uint32 kShapeLifeMs = 900000;

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(ms);
    }

    void LogLake(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, mechanic, detail);
    }

    // The causeway's floor under (x, y) near its height; the causeway's height when the probe finds nothing close.
    float FloorZ(WorldObject const* ref, float x, float y)
    {
        float const z = ref->GetMap()->GetHeight(ref->GetPhaseMask(), x, y, BrdIncendius::kFloorZ + 3.f, true, 10.f);
        return (z > INVALID_HEIGHT && std::fabs(z - BrdIncendius::kFloorZ) <= 4.f) ? z : BrdIncendius::kFloorZ;
    }

    Position OnFloor(WorldObject const* ref, Vec2 p, float o = 0.f)
    {
        return Position(p.x, p.y, FloorZ(ref, p.x, p.y), o);
    }

    // The ground under a unit (a unit in the air gets the floor within 10 yd below, else its own height).
    Position GroundUnder(Unit const* unit)
    {
        float const x = unit->GetPositionX();
        float const y = unit->GetPositionY();
        float const z = unit->GetPositionZ();
        float const floor = unit->GetMap()->GetHeight(unit->GetPhaseMask(), x, y, z + 2.f, true, 12.f);
        return Position(x, y, (floor > INVALID_HEIGHT && std::fabs(floor - z) <= 10.f) ? floor : z, 0.f);
    }

    // Firelord's Will on him now: the multiplier of his reference-sized hits.
    float WillOf(Unit const* boss)
    {
        return WillFactor(DungeonKit::Stacks(boss, SPELL_LAKE_FIRELORDS_WILL));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The giant's look, kept on the creature (DataMap) so the idle hook, the pull and the end share it
    // ----------------------------------------------------------------------------------------------------------------

    struct LakeState : public DataMap::Base
    {
        bool posed = false;
        // The intro after the Cinder (the idle hook runs it): ms since the toss, the steps fired so far.
        bool intro = false;
        uint32 introMs = 0;
        uint8 introFired = 0;
        uint32 checkMs = 0;
        // His look before the giant (put back by RemoveGiant).
        uint32 display = 0;
        float scale = 1.f;
        float reach = 0.f;
        float bounding = 0.f;
    };

    LakeState* StateOf(Creature* boss)
    {
        return boss->CustomData.GetDefault<LakeState>(kStateKey);
    }

    bool CinderLit(Creature* boss)
    {
        InstanceScript* instance = boss->GetInstanceScript();
        return instance && DungeonKit::IsHeroicMap(boss) && instance->GetData(DATA_CINDER_USED) != 0;
    }

    float FacingToAnvil()
    {
        return DungeonKit::BearingTo(kGiantSpot.XY(), BrdIncendius::kAnvil.XY());
    }

    void SetGiantReach(Creature* boss, float reach)
    {
        boss->SetFloatValue(UNIT_FIELD_COMBATREACH, reach);
    }

    // The giant in the lake: rooted, hovering at kGiantSpot, his display at kGiantScale, the reach for `steps`. A pose
    // already in place keeps its spot (only the reach and the root are made sure of).
    void ApplyGiant(Creature* boss, uint32 steps)
    {
        LakeState* st = StateOf(boss);
        if (!st->posed)
        {
            st->display = boss->GetDisplayId();
            st->scale = boss->GetObjectScale();
            st->reach = boss->GetCombatReach();
            st->bounding = boss->GetFloatValue(UNIT_FIELD_BOUNDINGRADIUS);
            boss->GetMotionMaster()->Clear(false);
            boss->GetMotionMaster()->MoveIdle();
            boss->StopMoving();
            boss->SetDisableGravity(true);
            boss->NearTeleportTo(kGiantSpot.x, kGiantSpot.y, kGiantSpot.z, FacingToAnvil());
            boss->SetDisplayId(kGiantDisplay, kGiantScale);
            st->posed = true;
        }
        boss->SetDisableGravity(true);
        boss->SetControlled(true, UNIT_STATE_ROOT);
        SetGiantReach(boss, kGiantReachYd);     // small (R-1-B M2): `steps` only moves the band
        (void)steps;
    }

    // His own look back and, with `home`, his spawn (the evade's walk home is then immediate).
    void RemoveGiant(Creature* boss, bool home)
    {
        LakeState* st = StateOf(boss);
        if (!st->posed)
            return;
        st->posed = false;
        boss->SetControlled(false, UNIT_STATE_ROOT);
        boss->SetDisableGravity(false);
        boss->SetDisplayId(st->display, st->scale);
        SetGiantReach(boss, st->reach);
        boss->SetFloatValue(UNIT_FIELD_BOUNDINGRADIUS, st->bounding);
        if (home)
        {
            Position const& h = boss->GetHomePosition();
            boss->NearTeleportTo(h.GetPositionX(), h.GetPositionY(), h.GetPositionZ(), h.GetOrientation());
        }
    }

    // The giant rises at his spot (the intro's end, a reload, a wipe): the pose, the look, line 8; out of combat he
    // waits for the group (defensive: the pull is theirs).
    void Rise(Creature* boss, char const* why)
    {
        ApplyGiant(boss, 0);
        boss->SetReactState(REACT_DEFENSIVE);
        boss->CastSpell(boss, SPELL_LAKE_LORD_RISES, true);
        boss->CastSpell(kGiantSpot.x, kGiantSpot.y, kLakeSurfaceZ, SPELL_LAKE_ERUPTION, true);
        if (boss->IsAIEnabled && boss->AI())
            boss->AI()->Talk(EMOTE_LAKE_RISES);
        LogLake("lake-rises", Acore::StringFormat("why={} at=({:.1f}, {:.1f}, {:.1f}) scale={:.1f} reach={:.1f}", why,
            boss->GetPositionX(), boss->GetPositionY(), boss->GetPositionZ(), boss->GetObjectScale(),
            boss->GetCombatReach()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The idle hook (D11 calls it every tick while he is alive and not engaged): the intro after the Cinder, the giant
    // after a reload or a wipe, back to his patrol when the Cinder goes out (the kill or `.dbtest`)
    // ----------------------------------------------------------------------------------------------------------------

    void RunIntro(Creature* boss, LakeState& st, uint32 diff)
    {
        st.introMs += diff;
        uint8 const due = static_cast<uint8>(IntroStepAt(st.introMs)) + 1;
        while (st.introFired < due)
        {
            switch (static_cast<IntroStep>(st.introFired++))
            {
                case IntroStep::Yell:
                    boss->GetMotionMaster()->Clear(false);
                    boss->GetMotionMaster()->MoveIdle();
                    boss->StopMoving();
                    boss->SetReactState(REACT_PASSIVE);
                    boss->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
                    boss->SetUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
                    boss->SetFacingTo(DungeonKit::BearingTo(DungeonKit::PlaneOf(boss), kGiantSpot.XY()));
                    if (boss->IsAIEnabled && boss->AI())
                        boss->AI()->Talk(YELL_LAKE_CINDER);
                    LogLake("lake-intro", "step=yell");
                    break;
                case IntroStep::Jump:
                    DungeonKit::JumpTo(boss, Position(kGiantSpot.x, kGiantSpot.y, kLakeSurfaceZ), kIntroJumpSpeedXY,
                        kIntroJumpMinSpeedZ);
                    LogLake("lake-intro", "step=jump");
                    break;
                case IntroStep::Rise:
                    st.intro = false;
                    boss->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
                    boss->RemoveUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
                    Rise(boss, "cinder");
                    return;
            }
        }
    }

    void LakeIdle(Creature* boss, uint32 diff)
    {
        LakeState* st = StateOf(boss);
        if (st->intro)
        {
            RunIntro(boss, *st, diff);
            return;
        }
        st->checkMs += diff;
        if (st->checkMs < kIdleCheckMs)
            return;
        st->checkMs = 0;
        if (boss->IsInEvadeMode())
            return;     // the walk home first (an evade's OnEnd took the giant down)
        bool const lit = CinderLit(boss);
        if (lit && !st->posed)
            Rise(boss, "reload");
        else if (!lit && st->posed)
        {
            RemoveGiant(boss, true);
            boss->SetReactState(REACT_AGGRESSIVE);
            boss->GetMotionMaster()->Initialize();      // his patrol (path 477330)
            LogLake("lake-unposed", "why=cinder-out");
        }
        else if (st->posed)
        {
            // Out of combat the giant waits for the group (a Reset puts him back to aggressive).
            if (!boss->HasReactState(REACT_DEFENSIVE))
                boss->SetReactState(REACT_DEFENSIVE);
            if (std::fabs(boss->GetCombatReach() - kGiantReachYd) > 0.1f)
                SetGiantReach(boss, kGiantReachYd);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Cinder (IN9)
    // ----------------------------------------------------------------------------------------------------------------

    Creature* IncendiusNear(Player* user)
    {
        InstanceScript* instance = user ? user->GetInstanceScript() : nullptr;
        if (!instance)
            return nullptr;
        Creature* boss = ObjectAccessor::GetCreature(*user, instance->GetGuidData(kGuidBossBase + BOSS_INCENDIUS));
        if (!boss)
            boss = user->FindNearestCreature(NPC_INCENDIUS, kCinderBossRangeYd, true);
        return boss;
    }

    CinderRefusal CinderRefusalFor(Player* user)
    {
        CinderCheck c;
        if (!user)
            return CinderRefusal::NotInDungeon;
        InstanceScript* instance = user->GetInstanceScript();
        c.mapId = user->GetMapId();
        c.hasInstance = instance != nullptr;
        c.heroic = user->GetMap()->IsHeroic();
        c.lit = instance && instance->GetData(DATA_CINDER_USED) != 0;
        Creature* boss = IncendiusNear(user);
        c.incendiusAlive = boss && boss->IsAlive() && boss->IsWithinDist2d(user, kCinderBossRangeYd);
        c.incendiusEngaged = boss && (boss->IsEngaged() || boss->IsInCombat() || boss->IsInEvadeMode());
        c.incendiusState = instance ? static_cast<uint32>(instance->GetBossState(BOSS_INCENDIUS)) : 0;
        c.casterInCombat = user->IsInCombat();
        c.onTheIsland = OnTheIsland(DungeonKit::PlaneOf(user), user->GetPositionZ());
        return CinderUseRefusal(c);
    }

    // The success path: the flag (saved; the instance arms the loot bit), the toss, the intro. False when the
    // instance refused the flag (it re-checks heroic and his state).
    bool TossCinder(Player* user, char const* by)
    {
        InstanceScript* instance = user->GetInstanceScript();
        instance->SetData(DATA_CINDER_USED, 1);
        if (!instance->GetData(DATA_CINDER_USED))
        {
            LogLake("lake-cinder", Acore::StringFormat("by={} refused-by-instance=1", user->GetName()));
            return false;
        }
        user->CastSpell(kGiantSpot.x, kGiantSpot.y, kLakeSurfaceZ, SPELL_LAKE_CINDER_TOSS, true);
        Creature* boss = IncendiusNear(user);
        if (boss && boss->IsAlive() && !boss->IsEngaged())
        {
            LakeState* st = StateOf(boss);
            st->intro = true;
            st->introMs = 0;
            st->introFired = 0;
        }
        LogLake("lake-cinder", Acore::StringFormat("by={} via={} at=({:.1f}, {:.1f}, {:.1f}) boss={}", user->GetName(),
            by, user->GetPositionX(), user->GetPositionY(), user->GetPositionZ(), boss ? 1 : 0));
        return true;
    }
}

// -------------------------------------------------------------------------------------------------------------------
// Lava Spawn 300795 (IN12): walks to The Black Anvil and never fights. The hard mode reads where it is (arrived,
// dead); the spawn only moves, re-aimed every second so a slow, a root or a stun holds it back (D11's Ember pattern).
// -------------------------------------------------------------------------------------------------------------------

struct npc_brd_lava_spawn : public ScriptedAI
{
    explicit npc_brd_lava_spawn(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }

    // Nobody left to fight (the boss's cleanup despawns it anyway): gone, never a walk home.
    void EnterEvadeMode(EvadeReason /*why*/) override
    {
        me->DespawnOrUnsummon();
    }

    // The hard mode starts the walk: `speed` yd/s toward the Anvil.
    void Walk(float speed)
    {
        _speed = speed;
        _walking = true;
        _aimMs = 0;
        Aim();
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim() || !_walking)
            return;
        _aimMs += diff;
        if (_aimMs < kSpawnReaimMs)
            return;
        _aimMs = 0;
        Aim();
    }

private:
    void Aim()
    {
        if (!me->IsAlive() || me->HasUnitState(UNIT_STATE_ROOT | UNIT_STATE_STUNNED | UNIT_STATE_CONFUSED |
            UNIT_STATE_FLEEING | UNIT_STATE_DISTRACTED))
            return;
        // A slow on the spawn cuts its walk (its run speed rate against the template's).
        float rate = 1.f;
        if (CreatureTemplate const* t = me->GetCreatureTemplate())
            if (t->speed_run > 0.f)
                rate = std::clamp(me->GetSpeedRate(MOVE_RUN) / t->speed_run, 0.1f, 1.5f);
        Point3 const& anvil = BrdIncendius::kAnvil;
        me->GetMotionMaster()->MovePoint(1, anvil.x, anvil.y, anvil.z, FORCED_MOVEMENT_RUN, _speed * rate);
    }

    float _speed = 1.f;
    uint32 _aimMs = 0;
    bool _walking = false;
};

// -------------------------------------------------------------------------------------------------------------------
// Hand of Incendius 300828 (R-1-B M2): the giant's stand-in on the near rim. It shares his health: every hit on it
// lands on him (Unit::DealDamage from the same attacker: his threat, the kill and the loot follow), its own threat
// (a spell's flat bonus) moves to him, its health shows his. Rooted, passive, never evades; the boss's cleanup
// despawns it.
// -------------------------------------------------------------------------------------------------------------------

struct npc_brd_lake_hand : public ScriptedAI
{
    explicit npc_brd_lake_hand(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
        me->SetCombatMovement(false);
        me->SetControlled(true, UNIT_STATE_ROOT);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void EnterEvadeMode(EvadeReason /*why*/) override { }
    void HealReceived(Unit* /*healer*/, uint32& heal) override { heal = 0; }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        uint32 const dealt = damage;
        damage = 0;
        Creature* giant = Giant();
        if (!attacker || !giant || !giant->IsAlive() || !dealt || _forwarding)
            return;
        _forwarding = true;
        Unit::DealDamage(attacker, giant, dealt, nullptr, type, mask, nullptr, false);
        _forwarding = false;
        if (giant->IsAlive())
            Mirror(giant);
    }

    void UpdateAI(uint32 diff) override
    {
        _syncMs += diff;
        if (_syncMs < kHandSyncMs)
            return;
        _syncMs = 0;
        Creature* giant = Giant();
        if (!giant || !giant->IsAlive())
        {
            me->DespawnOrUnsummon();
            return;
        }
        Mirror(giant);
        MoveThreat(giant);
    }

private:
    Creature* Giant() const
    {
        TempSummon const* summon = me->ToTempSummon();
        ObjectGuid const guid = summon ? summon->GetSummonerGUID() : ObjectGuid::Empty;
        return guid ? ObjectAccessor::GetCreature(*me, guid) : nullptr;
    }

    // Its health shows his (a pool of one: the frame of the unit the melee hit).
    void Mirror(Creature* giant)
    {
        if (me->GetMaxHealth() != giant->GetMaxHealth())
            me->SetMaxHealth(giant->GetMaxHealth());
        me->SetHealth(std::max<uint32>(1, giant->GetHealth()));
    }

    // Threat it gathered on its own (a spell's flat threat: Sunder Armor, a taunt's) goes to him.
    void MoveThreat(Creature* giant)
    {
        for (ThreatReference* ref : me->GetThreatMgr().GetModifiableThreatList())
        {
            Unit* who = ref->GetVictim();
            float const threat = ref->GetThreat();
            if (!who || threat <= 0.f)
                continue;
            giant->GetThreatMgr().AddThreat(who, threat, nullptr, true, true);
            ref->ScaleThreat(0.f);
        }
    }

    uint32 _syncMs = 0;
    bool _forwarding = false;
};

// -------------------------------------------------------------------------------------------------------------------
// The hard mode of one pull
// -------------------------------------------------------------------------------------------------------------------

class LordOfTheLake final : public IncendiusHardMode
{
public:
    LordOfTheLake() : _serial(++NextSerial()) { }

    // The pull's hard mode, as a registry callback or a command finds it again: his AI's ActiveHardMode on the same
    // pull (`serial`; 0: any), or nullptr.
    static LordOfTheLake* Find(Map* map, ObjectGuid bossGuid, uint32 serial, IncendiusFight** fightOut = nullptr)
    {
        if (!map)
            return nullptr;
        Creature* boss = map->GetCreature(bossGuid);
        if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
            return nullptr;
        auto* fight = dynamic_cast<IncendiusFight*>(boss->AI());
        auto* lake = fight ? dynamic_cast<LordOfTheLake*>(fight->ActiveHardMode()) : nullptr;
        if (!lake || (serial && lake->_serial != serial))
            return nullptr;
        if (fightOut)
            *fightOut = fight;
        return lake;
    }

    // ---- the policy hooks (S2 "Kit in the hard mode") ---------------------------------------------------------------

    uint32 Rebirths(IncendiusFight const& /*fight*/, uint32 /*base*/) const override { return kRebirths; }
    bool LavaSurge(IncendiusFight const& /*fight*/) const override { return kLavaSurge; }
    uint32 FireStormLifeMs(IncendiusFight const& /*fight*/, uint32 /*base*/) const override { return kFireStormLifeMs; }
    uint32 FireStormEveryMs(IncendiusFight const& /*fight*/, uint32 /*base*/) const override
    {
        return kFireStormEveryMs;
    }
    bool MagmaFistOnTank(IncendiusFight const& /*fight*/) const override { return kMagmaFistOnTank; }
    // R-1-B m3: the giant stands far out over the lava; the line starts where it still reaches past a far target.
    bool FistFromNearEnd(IncendiusFight const& /*fight*/) const override { return true; }
    // D12 request 1: Firelord's Will scales D11's Fire Storm and Magma Fist too (Fiery Burst through its script).
    float DamageScale(IncendiusFight& fight) const override { return WillOf(fight.Boss()); }
    // R-1-B M2: his swings are the script's (SwingAtTank): his own reach is small.
    bool Melee(IncendiusFight const& /*fight*/) const override { return false; }

    // He stands in the lake, off the causeway: no boss leash (the no-target leash stays: a group gone from the island
    // for 10 s is a wipe).
    void ConfigureArena(IncendiusFight& /*fight*/, DungeonKit::Arena& /*arena*/,
        DungeonKit::ArenaGuardOptions& options) override
    {
        options.evadeWhenBossOff = false;
    }

    // ---- the pull ---------------------------------------------------------------------------------------------------

    void OnEngage(IncendiusFight& fight) override
    {
        Creature* boss = fight.Boss();
        _map = boss->GetMap();
        _bossGuid = boss->GetGUID();
        StateOf(boss)->intro = false;
        _steps = fight.CrumbleSteps();
        _reach = kGiantReachYd;
        ApplyGiant(boss, _steps);
        _baseHealth = boss->GetMaxHealth();
        DungeonKit::Flex::SetHealth(boss, kLakeHealth, true);
        _corpsePlaced = false;
        DungeonKit::SetHardModeLoot(boss, true);            // rule 1: at the pull (the instance keeps it too)
        boss->RemoveAurasDueToSpell(SPELL_LAKE_FIRELORDS_WILL);
        fight.SealNecks("pull");                            // section 7 #14 A: the trap is closed from the start

        uint64 const now = fight.FightMs();
        _crushing.Start(now, kCrushingFirstMs);
        _sweep.Start(now, kSweepFirstMs);
        _spawn.Start(now, kSpawnFirstMs);
        _nextCrumble = 0;
        _lastSpot = kNoSpot;
        RefreshBotShapes(fight, "pull");
        SpawnHand(fight);
        Describe(boss);
        fight.Log("lake-engage", Acore::StringFormat("serial={} health={} base={} reach={:.1f} at=({:.1f}, {:.1f}, "
            "{:.1f}) players={}", _serial, boss->GetMaxHealth(), _baseHealth, _reach, boss->GetPositionX(),
            boss->GetPositionY(), boss->GetPositionZ(), fight.FightPlayers().size()));
    }

    void OnUpdate(IncendiusFight& fight, uint32 diff) override
    {
        Creature* boss = fight.Boss();
        uint64 const now = fight.FightMs();

        // A crumble step (D11 counts it from its 5 s marker): the reach band and the bots' shapes move in.
        if (fight.CrumbleSteps() != _steps)
        {
            _steps = fight.CrumbleSteps();
            RefreshBotShapes(fight, "crumble");
            MoveHand(fight);
            fight.Log("lake-reach", Acore::StringFormat("steps={} reach={:.1f} band-far={:.1f}", _steps, _reach,
                GiantCombatReach(_steps)));
        }
        // A scale recalculation (an aura) resets the combat reach to the model's: put the giant's back.
        if (std::fabs(boss->GetCombatReach() - _reach) > 0.1f)
            SetGiantReach(boss, _reach);
        // He hovers (no creature_template_movement row: a movement flag update may turn his gravity back on).
        if (!boss->IsLevitating())
            boss->SetDisableGravity(true);

        // IN13: the timed steps (each raised 5 s before it crumbles).
        while (_nextCrumble < kCrumbleAtMs.size() && now >= CrumbleRaiseMs(_nextCrumble))
        {
            ++_nextCrumble;
            fight.Crumble("timer");
        }

        UpdateSweep(fight, now);
        if (_crushing.Due(now))
        {
            _crushing.Fired(now, kCrushingEveryMs);
            CrushingFist(fight);
        }
        if (_spawn.Due(now))
        {
            _spawn.Fired(now, kSpawnEveryMs);
            SpawnLava(fight);
        }
        PollSpawns(fight);
        UpdateBreath(fight, diff);
        SwingAtTank(fight);
    }

    // R-1-B M1: the lethal hit puts him on the near rim (gravity back on first: Creature::setDeathState drops a
    // flying or hovering corpse), so the corpse lies on the causeway, lootable, not 38 yd down in the lava.
    void OnDamageTaken(IncendiusFight& fight, Unit* /*attacker*/, uint32& damage) override
    {
        Creature* boss = fight.Boss();
        if (_corpsePlaced || !damage || damage < boss->GetHealth())
            return;
        _corpsePlaced = true;
        Position const at = OnFloor(boss, CorpseSpot(_steps), FacingToAnvil());
        boss->SetDisableGravity(false);
        boss->NearTeleportTo(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), at.GetOrientation());
        fight.Log("lake-corpse", Acore::StringFormat("at=({:.1f}, {:.1f}, {:.1f}) steps={}", at.GetPositionX(),
            at.GetPositionY(), at.GetPositionZ(), _steps));
    }

    // ---- R-1-B M2: the giant's swing and his Hand ------------------------------------------------------------------

    // His melee on his victim standing in the reach band (on the causeway): no range check (his own reach is small).
    void SwingAtTank(IncendiusFight& fight)
    {
        Creature* boss = fight.Boss();
        Unit* victim = boss->GetVictim();
        if (!victim || !victim->IsAlive() || !boss->isAttackReady() || boss->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (std::fabs(victim->GetPositionZ() - BrdIncendius::kFloorZ) > kReachZToleranceYd
            || !InReach(DungeonKit::PlaneOf(victim), _steps))
            return;
        boss->AttackerStateUpdate(victim);
        boss->resetAttackTimer();
    }

    Position HandPosition(Creature* boss) const
    {
        Vec2 const spot = HandSpot(_steps);
        return OnFloor(boss, spot, DungeonKit::BearingTo(spot, kGiantSpot.XY()));
    }

    void SpawnHand(IncendiusFight& fight)
    {
        Creature* boss = fight.Boss();
        Position const at = HandPosition(boss);
        TempSummon* hand = boss->SummonCreature(NPC_LAKE_HAND, at, TEMPSUMMON_MANUAL_DESPAWN);
        if (!hand)
        {
            fight.Log("lake-hand", "summon failed (is creature 300828 declared?)");
            return;
        }
        _hand = hand->GetGUID();
        Mechanic::TrackUnit(boss, hand);
        hand->SetLevel(boss->GetLevel());
        hand->SetObjectScale(kHandScale);
        hand->SetMaxHealth(boss->GetMaxHealth());
        hand->SetHealth(boss->GetHealth());
        // In the fight with everyone (0 threat: it never attacks, and a one-entry list would not hold it in combat).
        for (Player* player : fight.FightPlayers())
            hand->GetThreatMgr().AddThreat(player, 0.f, nullptr, true, true);
        fight.Log("lake-hand", Acore::StringFormat("at=({:.1f}, {:.1f}, {:.1f}) health={}", at.GetPositionX(),
            at.GetPositionY(), at.GetPositionZ(), hand->GetMaxHealth()));
    }

    // A crumble step (from its warning): the Hand moves in with the edge.
    void MoveHand(IncendiusFight& fight)
    {
        Creature* hand = _map ? _map->GetCreature(_hand) : nullptr;
        if (!hand || !hand->IsAlive())
            return;
        Position const at = HandPosition(fight.Boss());
        hand->NearTeleportTo(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), at.GetOrientation());
    }

    // ---- the end ----------------------------------------------------------------------------------------------------

    void OnEnd(IncendiusFight& fight, bool died) override
    {
        Creature* boss = fight.Boss();
        CancelBotShapes(boss);
        if (Creature* hand = boss->GetMap()->GetCreature(_hand))
            hand->DespawnOrUnsummon();
        _hand.Clear();
        for (SpawnState const& s : _spawns)
            if (Creature* spawn = boss->GetMap()->GetCreature(s.guid))
                spawn->DespawnOrUnsummon();
        _spawns.clear();
        boss->RemoveAurasDueToSpell(SPELL_LAKE_FIRELORDS_WILL);
        if (_sweepCasting && boss->IsNonMeleeSpellCast(false))
            boss->InterruptNonMeleeSpells(false);
        _sweepCasting = false;
        _breathing = false;
        _noReachMs = 0;
        if (!died)
        {
            // His heroic health and his own look back; the idle hook raises the giant again once the evade ends (the
            // Cinder stays lit: a wipe never burns it). On a death the giant's corpse lies on the near rim
            // (OnDamageTaken put him there).
            if (_baseHealth)
                DungeonKit::Flex::SetHealth(boss, _baseHealth, true);
            RemoveGiant(boss, true);
        }
        fight.Log("lake-end", Acore::StringFormat("serial={} died={} steps={} sweeps={} fists={} spawns={} arrived={} "
            "killed={} will={} breath-ticks={}", _serial, died ? 1 : 0, _steps, _sweeps, _fists, _spawned, _arrived,
            _killed, DungeonKit::Stacks(boss, SPELL_LAKE_FIRELORDS_WILL), _breathTicks));
    }

    // ---- IN10 Crushing Fist -----------------------------------------------------------------------------------------

    // The circle on the tank's spot (`forced`: that unit's spot instead).
    MechanicHandle CrushingFist(IncendiusFight& fight, Unit* forced = nullptr)
    {
        Creature* boss = fight.Boss();
        Unit* tank = forced ? forced : boss->GetVictim();
        if (!tank || !tank->IsAlive())
        {
            fight.Log("lake-crushing-fist", "no tank");
            return {};
        }
        Position const at = GroundUnder(tank);
        float const will = WillOf(boss);
        MechanicRef ref = Mechanic::Circle(boss, at, kCrushingRadiusYd, Ms(kCrushingWarnMs));
        ref.TankExempt().Damage(kCrushingOthersPct * will).Spell(SPELL_LAKE_CRUSHING_FIST).Weakened()
            .Within(fight.Bounds()).Tag(TAG_LAKE_CRUSHING_FIST);
        ref.OnResolve(OnLake(boss, [at](LordOfTheLake& lake, IncendiusFight& f, BossMechanics::ResolveResult const& r)
        {
            lake.CrushingLanded(f, at, r.hits.size());
        }));
        MechanicHandle const handle = ref.Handle();
        if (!handle)
            return {};
        fight.Track(handle);
        ++_fists;
        fight.Log("lake-crushing-fist", Acore::StringFormat("on={} at=({:.1f}, {:.1f}, {:.1f}) r={:.0f} others={:.0f} "
            "tank={:.0f} will={:.1f}", tank->GetName(), at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(),
            kCrushingRadiusYd, kCrushingOthersPct * will, kCrushingTankPct * will, will));
        return handle;
    }

    // The fist comes down: the crack, and the tank's own hit (his current victim: the one the circle spared).
    void CrushingLanded(IncendiusFight& fight, Position const& at, std::size_t hits)
    {
        Creature* boss = fight.Boss();
        boss->CastSpell(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), SPELL_LAKE_CRUSHING_FIST_LOOK, true);
        Unit* tank = boss->GetVictim();
        if (tank && tank->IsAlive())
            boss->CastSpell(tank, SPELL_LAKE_CRUSHING_FIST_TANK, true);
        fight.Log("lake-crushing-fist-landed", Acore::StringFormat("hits={} tank={}", hits,
            tank ? tank->GetName() : std::string("none")));
    }

    // ---- IN11 Arm Sweep ---------------------------------------------------------------------------------------------

    void UpdateSweep(IncendiusFight& fight, uint64 now)
    {
        if (_sweepCasting)
        {
            if (now >= _sweepEndMs)
                _sweepCasting = false;
            return;
        }
        // Nothing lands during the Sweep: hold the other markers from kSweepPreHoldMs before it.
        if (!_preHeld && now + kSweepPreHoldMs >= _sweep.DueMs())
        {
            _preHeld = true;
            HoldFor(fight, _sweep.DueMs() + kSweepCastMs);
        }
        // A Fiery Burst cast bar in progress: the sweep waits for it (1.5 s at most).
        if (_sweep.Due(now) && !fight.Boss()->HasUnitState(UNIT_STATE_CASTING))
            ArmSweep(fight, std::nullopt);
    }

    void HoldFor(IncendiusFight& fight, uint64 untilMs)
    {
        fight.HoldBeats(untilMs);
        _crushing.NotBefore(untilMs);
    }

    MechanicHandle ArmSweep(IncendiusFight& fight, std::optional<SweepSpot> forced)
    {
        Creature* boss = fight.Boss();
        uint64 const now = fight.FightMs();
        SweepSpot const spot = forced ? *forced : PickSweepSpot(_lastSpot, _lastSpot == kNoSpot ? urand(0, 2)
            : urand(0, 1));
        Band const band = SweepBand(spot);
        float const will = WillOf(boss);
        float const pct = kSweepPct * will;
        float const bearing = SweepThrowBearing();
        uint64 const until = now + kSweepCastMs;
        HoldFor(fight, until);
        if (!forced)
        {
            _sweep.Fired(now, kSweepEveryMs);   // a `.dbtest` sweep leaves the timer alone
            _preHeld = false;
        }

        MechanicRef ref = Mechanic::Line(boss, OnFloor(boss, band.from), OnFloor(boss, band.to), band.width,
            Ms(kSweepCastMs));
        ref.Damage(pct).TankDamage(pct).Spell(SPELL_LAKE_ARM_SWEEP).Lethal().Within(fight.Bounds())
            .Tag(TAG_LAKE_ARM_SWEEP);
        ref.OnHit(OnLakeUnit(boss, [bearing](LordOfTheLake& /*lake*/, IncendiusFight& f, Unit* hit)
        {
            f.ThrowOff(hit, bearing, "arm-sweep");
        }));
        ref.OnResolve(OnLake(boss, [spot](LordOfTheLake& /*lake*/, IncendiusFight& f,
            BossMechanics::ResolveResult const& r)
        {
            f.Log("lake-arm-sweep-landed", Acore::StringFormat("spot={} hits={}", SweepSpotName(spot), r.hits.size()));
        }));
        MechanicHandle const handle = ref.Handle();
        if (!handle)
        {
            fight.Log("lake-arm-sweep", "refused");
            return {};
        }
        fight.Track(handle);
        boss->CastSpell(boss, SPELL_LAKE_ARM_SWEEP_CAST, false);       // the 4 s bar (Physical, not kickable)
        if (boss->IsAIEnabled && boss->AI())
            boss->AI()->Talk(EMOTE_LAKE_ARM_RAISED);
        _lastSpot = static_cast<uint8>(spot);
        _sweepCasting = true;
        _sweepEndMs = until;
        ++_sweeps;
        fight.Log("lake-arm-sweep", Acore::StringFormat("spot={} s={:.0f} width={:.0f} pct={:.0f} will={:.1f}",
            SweepSpotName(spot), kSweepSpots[static_cast<std::size_t>(spot)], band.width, pct, will));
        return handle;
    }

    // ---- IN12 Lava Spawn --------------------------------------------------------------------------------------------

    uint32 SpawnLava(IncendiusFight& fight)
    {
        Creature* boss = fight.Boss();
        std::vector<Player*> const players = fight.FightPlayers();
        Vec2 const anvil = BrdIncendius::kAnvil.XY();
        uint32 spawned = 0;
        std::string spots;
        for (bool const southEast : { true, false })
        {
            Vec2 const spot = SpawnSpot(SpawnS(frand(0.f, 1.f)), southEast, _steps);
            Position const at = OnFloor(boss, spot, DungeonKit::BearingTo(spot, anvil));
            TempSummon* spawn = boss->SummonCreature(NPC_BRD_LAVA_SPAWN, at, TEMPSUMMON_CORPSE_TIMED_DESPAWN,
                kSpawnCorpseMs);
            if (!spawn)
                continue;
            ++spawned;
            Mechanic::TrackUnit(boss, spawn);
            // Everyone in the fight at 0 (a one-entry threat list evades); it never attacks.
            for (Player* player : players)
                spawn->GetThreatMgr().AddThreat(player, 0.f, nullptr, true, true);
            spawn->CastSpell(spawn, SPELL_LAKE_LAVA_SPAWN_CLIMB, true);
            boss->CastSpell(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), SPELL_LAKE_ERUPTION, true);
            if (auto* ai = dynamic_cast<npc_brd_lava_spawn*>(spawn->AI()))
                ai->Walk(SpawnSpeed(DungeonKit::Distance(spot, anvil)));
            _spawns.push_back({ spawn->GetGUID() });
            spots += Acore::StringFormat(" ({:.1f}, {:.1f})", at.GetPositionX(), at.GetPositionY());
        }
        if (spawned && boss->IsAIEnabled && boss->AI())
            boss->AI()->Talk(EMOTE_LAKE_SPAWNS);
        _spawned += spawned;
        fight.Log("lake-lava-spawn", Acore::StringFormat("count={} steps={} at{}", spawned, _steps, spots));
        return spawned;
    }

    // Each tick: a spawn within kSpawnArriveYd of the Anvil arrived (he heals 5%, Firelord's Will +1); a dead or gone
    // one is done.
    void PollSpawns(IncendiusFight& fight)
    {
        Creature* boss = fight.Boss();
        Vec2 const anvil = BrdIncendius::kAnvil.XY();
        std::erase_if(_spawns, [this, boss, &fight, anvil](SpawnState const& s)
        {
            Creature* spawn = boss->GetMap()->GetCreature(s.guid);
            if (!spawn || !spawn->IsAlive())
            {
                ++_killed;
                fight.Log("lake-lava-spawn-killed", Acore::StringFormat("killed={}", _killed));
                return true;
            }
            if (DungeonKit::Distance(DungeonKit::PlaneOf(spawn), anvil) > kSpawnArriveYd)
                return false;
            ++_arrived;
            spawn->CastSpell(spawn, SPELL_LAKE_LAVA_SPAWN_ARRIVES, true);
            spawn->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
            spawn->SetUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
            spawn->DespawnOrUnsummon(Ms(500));
            uint32 const before = boss->GetHealth();
            boss->SetHealth(HealedHealth(before, boss->GetMaxHealth()));
            uint32 const will = DungeonKit::AddStacks(boss, SPELL_LAKE_FIRELORDS_WILL, 1, boss, kWillMaxStacks);
            fight.Log("lake-lava-spawn-arrived", Acore::StringFormat("arrived={} health={}->{} will={}", _arrived,
                before, boss->GetHealth(), will));
            return true;
        });
    }

    // ---- IN14 Firelord's Breath -------------------------------------------------------------------------------------

    // Is anyone (a player of the fight, on the causeway) in the reach band now?
    bool AnyoneInReach(IncendiusFight& fight) const
    {
        for (Player* player : fight.FightPlayers())
            if (std::fabs(player->GetPositionZ() - BrdIncendius::kFloorZ) <= kReachZToleranceYd
                && InReach(DungeonKit::PlaneOf(player), _steps))
                return true;
        return false;
    }

    void UpdateBreath(IncendiusFight& fight, uint32 diff)
    {
        _breathCheckMs += diff;
        if (_breathCheckMs < kBreathCheckMs)
            return;
        _breathCheckMs = 0;
        if (!_forceBreath && AnyoneInReach(fight))
        {
            if (_breathing)
                fight.Log("lake-breath-end", Acore::StringFormat("ticks={}", _breathTicks));
            _breathing = false;
            _noReachMs = 0;
            return;
        }
        _noReachMs += kBreathCheckMs;
        if (_noReachMs < kBreathGraceMs)
            return;
        _forceBreath = false;
        Creature* boss = fight.Boss();
        if (!_breathing)
        {
            _breathing = true;
            if (boss->IsAIEnabled && boss->AI())
                boss->AI()->Talk(EMOTE_LAKE_BREATH);
            fight.Log("lake-breath", Acore::StringFormat("steps={} pct={:.0f} will={:.1f}", _steps, kBreathPct,
                WillOf(boss)));
        }
        for (Player* player : fight.FightPlayers())
            boss->CastSpell(player, SPELL_LAKE_FIRELORDS_BREATH, true);
        ++_breathTicks;
    }

    // ---- the bots ---------------------------------------------------------------------------------------------------

    // The melee and the tank strictly on the floor (no behind: behind him is the lava) and the tank-only soak line in
    // the reach band (DS's composition); both move in with every crumble step.
    void RefreshBotShapes(IncendiusFight& fight, char const* why)
    {
        Creature* boss = fight.Boss();
        CancelBotShapes(boss);
        BossMechanics::SpotBounds strict = fight.Bounds();
        strict.For(BossMechanics::BoundsFor::Melee | BossMechanics::BoundsFor::Tank).Strict();
        {
            MechanicRef carrier = Mechanic::Spot(boss, {}, Ms(kShapeLifeMs));
            carrier.NoTelegraph().Within(strict).Tag(TAG_LAKE_NO_BEHIND);
            _noBehind = carrier.Handle();
        }
        Band const soak = SoakLine(_steps);
        BossMechanics::Eligibility tanks;
        tanks.roles = BossMechanics::Role::Tank;
        {
            MechanicRef ref = Mechanic::Soak(boss, BossMechanics::Shapes::Line(OnFloor(boss, soak.from),
                OnFloor(boss, soak.to), soak.width), 1, Ms(0));
            ref.Persistent(Ms(kShapeLifeMs), Ms(1000)).MissedSoak(BossMechanics::MissedSoakMode::Never)
                .Eligible(tanks).NoTelegraph().Within(fight.Bounds()).Tag(TAG_LAKE_REACH);
            _reachSoak = ref.Handle();
        }
        fight.Log("lake-bot-shapes", Acore::StringFormat("why={} steps={} no-behind={} soak={}", why, _steps,
            _noBehind ? 1 : 0, _reachSoak ? 1 : 0));
    }

    void CancelBotShapes(Creature* boss)
    {
        if (_noBehind)
            Mechanic::Cancel(boss, _noBehind);
        if (_reachSoak)
            Mechanic::Cancel(boss, _reachSoak);
        _noBehind = {};
        _reachSoak = {};
    }

    // Kill order: the Lava Spawn (every role; AoE welcome), on top of D11's descriptor (the Curse, Fiery Burst).
    void Describe(Creature* boss)
    {
        Mechanic::EditDescriptor(boss, [](BossMechanics::Descriptor& d)
        {
            d.targets.push_back(BossMechanics::TargetEntry(NPC_BRD_LAVA_SPAWN, 2, BossMechanics::Who::Any).AoeOk());
            // R-1-B M2: the melee and the tank hit his Hand (he is out of their reach); the ranged hit him.
            d.targets.push_back(BossMechanics::TargetEntry(NPC_LAKE_HAND, 1, BossMechanics::Who::Melee));
            d.targets.push_back(BossMechanics::TargetEntry(NPC_LAKE_HAND, 1, BossMechanics::Who::Tank));
        });
    }

    // ---- `.dbtest brd lake` entry points ----------------------------------------------------------------------------

    void TestBreath() { _forceBreath = true; _noReachMs = kBreathGraceMs; }

    bool TestCrumble(IncendiusFight& fight)
    {
        if (_nextCrumble >= kCrumbleAtMs.size())
            return false;
        ++_nextCrumble;
        return fight.Crumble("dbtest");
    }

    std::string TestState(IncendiusFight& fight) const
    {
        uint64 const now = fight.FightMs();
        return Acore::StringFormat("serial={} t={}ms steps={} reach={:.1f} (combat reach {:.1f}) health={}/{} will={} "
            "next: fist {}ms sweep {}ms spawn {}ms crumble {} | sweeps={} fists={} spawns={} alive={} arrived={} "
            "killed={} breathing={} no-reach={}ms ticks={} reach-now={}", _serial, now, _steps, _reach,
            fight.Boss()->GetCombatReach(), fight.Boss()->GetHealth(), fight.Boss()->GetMaxHealth(),
            DungeonKit::Stacks(fight.Boss(), SPELL_LAKE_FIRELORDS_WILL), Until(_crushing, now), Until(_sweep, now),
            Until(_spawn, now), _nextCrumble < kCrumbleAtMs.size() ? Acore::StringFormat("{}ms",
            CrumbleRaiseMs(_nextCrumble) > now ? CrumbleRaiseMs(_nextCrumble) - now : 0) : std::string("done"),
            _sweeps, _fists, _spawned, _spawns.size(), _arrived, _killed, _breathing ? 1 : 0, _noReachMs, _breathTicks,
            AnyoneInReach(fight) ? 1 : 0);
    }

    uint32 Steps() const { return _steps; }

private:
    struct SpawnState
    {
        ObjectGuid guid;
    };

    static uint32& NextSerial()
    {
        static uint32 serial = 0;
        return serial;
    }

    static int64 Until(BrdIncendius::FightClock const& clock, uint64 now)
    {
        return clock.On() ? static_cast<int64>(clock.DueMs()) - static_cast<int64>(now) : -1;
    }

    // Runs `fn(lake, fight, result)` on this pull's hard mode when a mechanic resolves, if it is still the same pull
    // (the map, the guid and the serial only: a lambda the registry keeps never holds a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnLake(Creature* boss, Fn fn)
    {
        Map* map = boss->GetMap();
        ObjectGuid const guid = boss->GetGUID();
        uint32 const serial = _serial;
        return [map, guid, serial, fn](BossMechanics::ResolveResult const& result)
        {
            IncendiusFight* fight = nullptr;
            if (LordOfTheLake* lake = Find(map, guid, serial, &fight))
                fn(*lake, *fight, result);
        };
    }

    template <typename Fn>
    std::function<void(Unit*)> OnLakeUnit(Creature* boss, Fn fn)
    {
        Map* map = boss->GetMap();
        ObjectGuid const guid = boss->GetGUID();
        uint32 const serial = _serial;
        return [map, guid, serial, fn](Unit* hit)
        {
            IncendiusFight* fight = nullptr;
            if (LordOfTheLake* lake = Find(map, guid, serial, &fight))
                fn(*lake, *fight, hit);
        };
    }

    uint32 const _serial;
    Map* _map = nullptr;
    ObjectGuid _bossGuid;
    BrdIncendius::FightClock _crushing;
    BrdIncendius::FightClock _sweep;
    BrdIncendius::FightClock _spawn;
    std::vector<SpawnState> _spawns;
    ObjectGuid _hand;
    MechanicHandle _noBehind;
    MechanicHandle _reachSoak;
    uint64 _sweepEndMs = 0;
    uint32 _baseHealth = 0;
    uint32 _steps = 0;
    float _reach = 0.f;
    std::size_t _nextCrumble = 0;
    uint32 _breathCheckMs = 0;
    uint32 _noReachMs = 0;
    uint32 _breathTicks = 0;
    uint32 _sweeps = 0;
    uint32 _fists = 0;
    uint32 _spawned = 0;
    uint32 _arrived = 0;
    uint32 _killed = 0;
    uint8 _lastSpot = kNoSpot;
    bool _preHeld = false;
    bool _sweepCasting = false;
    bool _breathing = false;
    bool _forceBreath = false;
    bool _corpsePlaced = false;
};

// -------------------------------------------------------------------------------------------------------------------
// Spells
// -------------------------------------------------------------------------------------------------------------------

// IN9: item 70621's use (211260). A refusal (CheckCast) keeps the item: Spell::TakeCastItem runs only after a
// successful cast.
class spell_brd_cinder_of_the_firelord : public SpellScript
{
    PrepareSpellScript(spell_brd_cinder_of_the_firelord);

    SpellCastResult CheckCast()
    {
        Player* user = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!user)
            return SPELL_FAILED_BAD_TARGETS;
        CinderRefusal const why = CinderRefusalFor(user);
        if (why == CinderRefusal::None)
            return SPELL_CAST_OK;
        ChatHandler(user->GetSession()).SendNotification(std::string_view(CinderRefusalText(why)));
        return SPELL_FAILED_DONT_REPORT;
    }

    void Toss(SpellEffIndex /*effIndex*/)
    {
        Player* user = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!user || CinderRefusalFor(user) != CinderRefusal::None)
            return;
        TossCinder(user, "item");
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_brd_cinder_of_the_firelord::CheckCast);
        OnEffectHit += SpellEffectFn(spell_brd_cinder_of_the_firelord::Toss, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// IN10 / IN14: the tank's Crushing Fist (211181) and a second of Firelord's Breath (211185): the percent in the
// effect (hundredths, the kit's refflat convention; EffectMiscValueB on heroic) of the target's reference row, times
// Firelord's Will on the caster (the spells ignore caster modifiers, so the aura alone would not reach them).
class spell_brd_lake_scaled_hit : public SpellScript
{
    PrepareSpellScript(spell_brd_lake_scaled_hit);

    void SetDamage(SpellEffIndex effIndex)
    {
        Unit* caster = GetCaster();
        if (!caster || effIndex >= MAX_SPELL_EFFECTS)
            return;
        SpellEffectInfo const& effect = GetSpellInfo()->Effects[effIndex];
        float const pct = DungeonKit::EffectPercent(DungeonKit::EffectShownValue(effect.BasePoints, effect.DieSides),
            effect.MiscValueB, DungeonKit::IsHeroicMap(caster)) * WillOf(caster);
        SetEffectValue(static_cast<int32>(DungeonKit::RefFlatOn(caster, GetHitUnit(), pct)));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_brd_lake_scaled_hit::SetDamage, EFFECT_ALL,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

// -------------------------------------------------------------------------------------------------------------------
// `.dbtest brd lake`
// -------------------------------------------------------------------------------------------------------------------

namespace
{
    Player* GmPlayer(ChatHandler* handler)
    {
        return handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
    }

    // The running hard mode (heroic, the Cinder lit, in combat), or an error.
    LordOfTheLake* ActiveLake(ChatHandler* handler, IncendiusFight** fightOut)
    {
        Creature* boss = BrdTest::FindBoss(handler, NPC_INCENDIUS);
        if (!boss)
            return nullptr;
        auto* fight = boss->IsAIEnabled ? dynamic_cast<IncendiusFight*>(boss->AI()) : nullptr;
        auto* lake = fight ? dynamic_cast<LordOfTheLake*>(fight->ActiveHardMode()) : nullptr;
        if (!lake)
        {
            handler->SendErrorMessage("{}", "Lord of the Lake is not running (heroic, the Cinder lit "
                "(`.dbtest brd lake toss`), Lord Incendius in combat).");
            return nullptr;
        }
        *fightOut = fight;
        return lake;
    }

    bool Done(ChatHandler* handler, bool ok, char const* done, char const* refused)
    {
        if (!ok)
        {
            handler->SendErrorMessage("{}", refused);
            return false;
        }
        handler->PSendSysMessage("Lord of the Lake: {}", done);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowHardModeInfo(handler, "lake", DATA_CINDER_USED, BOSS_LORD_OF_THE_LAKE);
    }

    // `.dbtest brd lake state`: the pull's timers and counts, or the idle pose.
    bool HandleState(ChatHandler* handler)
    {
        Creature* boss = BrdTest::FindBoss(handler, NPC_INCENDIUS);
        if (!boss)
            return false;
        auto* fight = boss->IsAIEnabled ? dynamic_cast<IncendiusFight*>(boss->AI()) : nullptr;
        if (auto* lake = fight ? dynamic_cast<LordOfTheLake*>(fight->ActiveHardMode()) : nullptr)
        {
            handler->PSendSysMessage("Lord of the Lake: {}", lake->TestState(*fight));
            return true;
        }
        LakeState const* st = StateOf(boss);
        handler->PSendSysMessage("Lord of the Lake (idle): cinder={} posed={} intro={} ({}ms) display={} scale={:.1f} "
            "reach={:.1f} at=({:.1f}, {:.1f}, {:.1f}) react={}", CinderLit(boss) ? 1 : 0, st->posed ? 1 : 0,
            st->intro ? 1 : 0, st->introMs, boss->GetDisplayId(), boss->GetObjectScale(), boss->GetCombatReach(),
            boss->GetPositionX(), boss->GetPositionY(), boss->GetPositionZ(),
            static_cast<uint32>(boss->GetReactState()));
        return true;
    }

    // `.dbtest brd lake toss`: the Cinder's success path from where you stand (the item's checks apply; no item used).
    bool HandleToss(ChatHandler* handler)
    {
        Player* gm = GmPlayer(handler);
        if (!gm || !BrdTest::RequireBlackrockDepths(handler))
            return false;
        CinderRefusal const why = CinderRefusalFor(gm);
        if (why != CinderRefusal::None)
        {
            handler->SendErrorMessage("{}", CinderRefusalText(why));
            return false;
        }
        return Done(handler, TossCinder(gm, "dbtest"), "the Cinder is tossed (he yells, jumps and rises in 4.5 s).",
            "The instance refused the Cinder.");
    }

    // `.dbtest brd lake pose`: the giant now (out of combat; the Cinder need not be lit, the idle hook takes him down
    // again within 0.5 s when it is not).
    bool HandlePose(ChatHandler* handler)
    {
        Creature* boss = BrdTest::FindBoss(handler, NPC_INCENDIUS);
        if (!boss)
            return false;
        if (boss->IsEngaged())
        {
            handler->SendErrorMessage("{}", "Lord Incendius is in combat.");
            return false;
        }
        Rise(boss, "dbtest");
        return Done(handler, true, "the giant stands in the lake.", "");
    }

    // `.dbtest brd lake fist`: IN10 on the tank (or on you with `.dbtest brd lake fist me`).
    bool HandleFist(ChatHandler* handler, Optional<std::string> who)
    {
        IncendiusFight* fight = nullptr;
        LordOfTheLake* lake = ActiveLake(handler, &fight);
        if (!lake)
            return false;
        Unit* forced = who && *who == "me" ? GmPlayer(handler) : nullptr;
        return Done(handler, static_cast<bool>(lake->CrushingFist(*fight, forced)), "Crushing Fist marked (3 s).",
            "The Crushing Fist was refused (no tank?).");
    }

    // `.dbtest brd lake sweep [0|1|2]`: IN11 now (0 south-west, 1 middle, 2 north-east; none: random).
    bool HandleSweep(ChatHandler* handler, Optional<uint32> spot)
    {
        IncendiusFight* fight = nullptr;
        LordOfTheLake* lake = ActiveLake(handler, &fight);
        if (!lake)
            return false;
        std::optional<SweepSpot> forced;
        if (spot)
            forced = static_cast<SweepSpot>(std::min<uint32>(*spot, 2));
        return Done(handler, static_cast<bool>(lake->ArmSweep(*fight, forced)), "Arm Sweep cast (4 s).",
            "The Arm Sweep was refused.");
    }

    // `.dbtest brd lake spawn`: IN12's two Lava Spawn now.
    bool HandleSpawn(ChatHandler* handler)
    {
        IncendiusFight* fight = nullptr;
        LordOfTheLake* lake = ActiveLake(handler, &fight);
        if (!lake)
            return false;
        return Done(handler, lake->SpawnLava(*fight) > 0, "two Lava Spawn climb out.",
            "No Lava Spawn appeared (is creature 300795 in the DB?).");
    }

    // `.dbtest brd lake breath`: IN14 at the next check (as if nobody had been in reach for 3 s).
    bool HandleBreath(ChatHandler* handler)
    {
        IncendiusFight* fight = nullptr;
        LordOfTheLake* lake = ActiveLake(handler, &fight);
        if (!lake)
            return false;
        lake->TestBreath();
        return Done(handler, true, "Firelord's Breath at the next check (1 s; one tick when someone is in reach).",
            "");
    }

    // `.dbtest brd lake crumble`: IN13's next timed step now.
    bool HandleCrumble(ChatHandler* handler)
    {
        IncendiusFight* fight = nullptr;
        LordOfTheLake* lake = ActiveLake(handler, &fight);
        if (!lake)
            return false;
        return Done(handler, lake->TestCrumble(*fight), "the next 2 yd of both long edges crumble in 5 s.",
            "Every timed step is already down.");
    }

    // `.dbtest brd lake reach`: are you in his reach (IN14), and the band's middle at the current steps.
    bool HandleReach(ChatHandler* handler)
    {
        Player* gm = GmPlayer(handler);
        Creature* boss = BrdTest::FindBoss(handler, NPC_INCENDIUS);
        if (!gm || !boss)
            return false;
        IncendiusFight* fight = boss->IsAIEnabled ? dynamic_cast<IncendiusFight*>(boss->AI()) : nullptr;
        uint32 const steps = fight ? fight->CrumbleSteps() : 0;
        BrdIncendius::FramePoint const f = BrdIncendius::ToFrame(DungeonKit::PlaneOf(gm));
        Band const soak = SoakLine(steps);
        handler->PSendSysMessage("Lord of the Lake: you are {}in reach (s={:.1f} w={:.1f}; steps={}: the band runs s "
            "{:.0f}..{:.0f}, the edge at w={:.1f}, inner w={:.1f}); the giant's reach {:.1f} (melee range {:.1f}), "
            "{:.1f} yd from you; the tank bot's soak ({:.1f}, {:.1f}) -> ({:.1f}, {:.1f}).",
            InReach(DungeonKit::PlaneOf(gm), steps) ? "" : "NOT ", f.s, f.w, steps, kReachSMin, kReachSMax,
            NearEdgeW(std::clamp(f.s, kReachSMin, kReachSMax), steps),
            ReachInnerW(std::clamp(f.s, kReachSMin, kReachSMax), steps), GiantCombatReach(steps),
            MeleeRangeYd(GiantCombatReach(steps)), gm->GetExactDist(boss), soak.from.x, soak.from.y, soak.to.x,
            soak.to.y);
        return true;
    }

    ChatCommandTable const& LordOfTheLakeTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",    HandleInfo,    SEC_GAMEMASTER, Console::No },
            { "state",   HandleState,   SEC_GAMEMASTER, Console::No },
            { "toss",    HandleToss,    SEC_GAMEMASTER, Console::No },
            { "pose",    HandlePose,    SEC_GAMEMASTER, Console::No },
            { "fist",    HandleFist,    SEC_GAMEMASTER, Console::No },
            { "sweep",   HandleSweep,   SEC_GAMEMASTER, Console::No },
            { "spawn",   HandleSpawn,   SEC_GAMEMASTER, Console::No },
            { "breath",  HandleBreath,  SEC_GAMEMASTER, Console::No },
            { "crumble", HandleCrumble, SEC_GAMEMASTER, Console::No },
            { "reach",   HandleReach,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_brd_incendius_hard_mode()
{
    BrdIncendius::RegisterIncendiusHardMode([](Creature*) { return std::make_unique<LordOfTheLake>(); });
    BrdIncendius::RegisterIncendiusIdleHook([](Creature* boss, uint32 diff) { LakeIdle(boss, diff); });
    RegisterDungeonReworkCreatureAI(npc_brd_lava_spawn, BlackrockDepthsRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brd_lake_hand, BlackrockDepthsRework::kInstanceScriptName);
    RegisterSpellScript(spell_brd_cinder_of_the_firelord);
    RegisterSpellScript(spell_brd_lake_scaled_hit);
    BrdTest::RegisterBoss("lake", LordOfTheLakeTestCommands());
}
