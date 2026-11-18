/*
 * mod-dungeon-bosses, Blackrock Depths D18: Hurley Blackbreath (9537), his Blackbreath Cronies (9541), the Thunderbrew
 * Lager Kegs (300839) and the Lager Puddles (300840), "Liquid Courage" (ruling 59). Build spec S4 "Hurley Blackbreath"
 * (docs/dungeons/blackrock-depths-4-imperial-seat.md, HU1-HU8; rulings 59-60, 88), handoff sections 3.4 (rows D18),
 * 3.5 (row D18), 3.6, 3.8 (NM: one open hall, the six keg spots), 7 #13 (the Cronies on C++). Replaces his and the
 * Cronies' SmartAI (rev_hurley_blackrock_depths.sql drops 9537's 20 rows and the Cronies' per-guid rows): Hamstring,
 * Drunken Rage and the stock Flame Breath retired, Mortal Strike kept (a copy in his slice). Bound by apps/dbc-tools
 * source/npcs/blackrock_depths/hurley.py. Pure rules: HurleyLogic.h. The bar state machine (GuzzlerLogic.h BarModel,
 * D17) is kept: the keg GOs' SmartAI wakes him (SetData 1,1, KegUsed), nothing else in the bar depends on him.
 *
 *   Wake  hidden, passive and immune to players until the third stock keg GO 164911 is tapped (its SmartAI sends
 *         SetData 1,1): yell 0, he and the Cronies run the stock escort path, then say 1 and ATTACK (the stock quirk,
 *         passive until struck, is fixed). Hidden while every keg GO stands used (a reload: the GOs respawn in 12 h and
 *         the wake is not saved): he wakes at once, at his home, without the yell
 *   HU1  Mortal Strike   5-8 s, then every 8-13 s, on his victim: 20% / 25% of the tank row and -50% healing, 5 s
 *   HU2  Flame Breath    8 s, then every 15 s: a 2 s bar, a 15 yd 60 degree cone down his front (the tank exempt from
 *                        the cone): 30% / 45% + Weakened on the others; the tank in the arc takes 10% / 15% of the
 *                        tank row
 *   HU3  Keg Run         15 s, then every 25 s / 20 s while kegs stand: yell 2, one of the six kegs is marked
 *                        (selectable, the orange ring: the kill order's first) and he walks to it, passive. Smashed
 *                        first: yell 4, a puddle, he turns back. Reached: a 3 s drink (no attacks), then 10% of his
 *                        health, a Liquid Courage stack, emote 3, the keg is gone (no puddle)
 *   HU4  Liquid Courage  +15% damage and +10% attack speed a stack, for the fight
 *   HU5  Lager Puddle    a smashed keg spills a 5 yd puddle for 30 s: inside, Tipsy (-30% speed) and Lager Buzz (+10%
 *                        damage done, 5 s after leaving), once a second. No damage; bots ignore it
 *   HU6  Firewater (H)   his breath ignites every puddle it touches: Burning Lager, 5 yd, 20 s, 8% a second (a
 *                        persistent registry zone); after a drink his next breath is twice as wide
 *   HU7  Rupture (H)     the Cronies' stock bleed, 2 s, then every 11-12 s
 *   HU8  Bottle Toss (H) each Crony, 6 s, then every 12 s: a 3 yd circle on a random player (the tank too, ruling
 *                        88), 1.5 s, 25% + Weakened
 *        The Cronies     Sinister Strike (stock); a Crony pulled pulls him, his pull pulls them; they keep fighting
 *                        while he does; the dead ones come back when he resets after a wipe
 *
 * Every timer runs on the AI's own clock. Every firing logs one INFO line "brd hurley <mechanic> ..."
 * (module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "BlackrockDepthsKit.h"
#include "BlackrockDepthsRework.h"
#include "BlackrockDepthsTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "GameObject.h"
#include "HurleyLogic.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <list>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdHurley;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBoss = "hurley";

    uint32 constexpr POINT_WAKE_FIRST = 1;      // 1..3: the escort path's nodes
    uint32 constexpr POINT_KEG = 10;            // HU3: next to the marked keg
    uint32 constexpr DATA_HURLEY_HEROIC = 3;    // GetData on Hurley's AI: his heroic form (the `.dbtest` override too)
    uint32 constexpr WAKE_WALK = 1;             // SetData(DATA_HURLEY_WAKE, ...) on a Crony: run the path
    uint32 constexpr WAKE_AT_HOME = 2;          // ... or appear at its end at once (the reload case)
    float constexpr kGroundBandYd = 6.f;        // a ground probe further off than this is taken as a hole
    float constexpr kPuddleZBandYd = 4.f;       // a player this far above or below a puddle is not in it
    float constexpr kArriveAttackYd = 40.f;     // on arrival he and the Cronies go for the nearest player this close
    float constexpr kCronyScanYd = 70.f;        // the Cronies around him (they stand within 50 yd of his spawn)

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    void LogHu(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    // HU5: a player in a puddle gets the aura once (its look flashes once) and a fresh duration every tick after.
    void RefreshOrCast(Player* player, uint32 spellId)
    {
        if (Aura* aura = player->GetAura(spellId))
            aura->RefreshDuration();
        else
            player->CastSpell(player, spellId, true);
    }

    float GroundZ(WorldObject const* probe, float x, float y, float refZ)
    {
        float const h = probe->GetMapHeight(x, y, refZ + 2.f);
        if (h <= INVALID_HEIGHT || std::fabs(h - refZ) > kGroundBandYd)
            return refZ;
        return h;
    }

    // The nearest player he (or a Crony) can attack on arrival, else nullptr.
    Player* NearestTarget(Creature* me)
    {
        Player* p = me->SelectNearestPlayer(kArriveAttackYd);
        if (!p || !p->IsAlive() || p->IsGameMaster() || !me->IsValidAttackTarget(p))
            return nullptr;
        return p;
    }

    // The test commands' forced mechanics (`.dbtest brd hurley ...`).
    enum class TestKind : uint8
    {
        Wake,
        KegRun,
        Breath,
        Puddle,
        Ignite,
        Clear,
    };
}

// ---------------------------------------------------------------------------------------------------------------------
// Thunderbrew Lager Keg 300839: a rooted, passive target. Not selectable until Hurley marks it (HU3); its death and
// the drink that drains it are Hurley's (SummonedCreatureDies).
// ---------------------------------------------------------------------------------------------------------------------
struct npc_brd_lager_keg : public ScriptedAI
{
    explicit npc_brd_lager_keg(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
        me->SetControlled(true, UNIT_STATE_ROOT);
        me->ApplySpellImmune(0, IMMUNITY_EFFECT, SPELL_EFFECT_KNOCK_BACK, true);
        me->ApplySpellImmune(0, IMMUNITY_EFFECT, SPELL_EFFECT_KNOCK_BACK_DEST, true);
        me->ApplySpellImmune(0, IMMUNITY_EFFECT, SPELL_EFFECT_PULL_TOWARDS, true);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }

    // A keg stays where it is while Hurley fights (no walk home, no reset of its health).
    void EnterEvadeMode(EvadeReason why) override
    {
        if (TempSummon const* summon = me->ToTempSummon())
            if (Unit* hurley = summon->GetSummonerUnit())
                if (hurley->IsAlive() && hurley->IsEngaged())
                    return;
        ScriptedAI::EnterEvadeMode(why);
    }

    void UpdateAI(uint32 /*diff*/) override { }
};

// ---------------------------------------------------------------------------------------------------------------------
// Hurley Blackbreath 9537
// ---------------------------------------------------------------------------------------------------------------------
struct boss_hurley_blackbreath_rework : public BossAI
{
    explicit boss_hurley_blackbreath_rework(Creature* creature)
        : BossAI(creature, BOSS_HURLEY), _arena(GuzzlerLowerArena(), LeashOptions(kBoss)) { }

    // HU5 / HU6: one spilled keg.
    struct Puddle
    {
        ObjectGuid stalker;
        Position at;
        uint64 expiresAtMs = 0;
        bool burning = false;
        MechanicHandle zone;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Engine hooks
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();       // despawns the kegs and the puddles (BossAI summons)
        Cleanup();
        if (_awake)
            ShowAwake();
        else
            Hide();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded
        if (_wakeStep)
            Arrive(true);   // struck on the way down: the walk ends here
        StartFight(who);
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        LogHu("evade", Acore::StringFormat("reason={} kegs={} stacks={}", uint32(why), _run.Left(), _run.stacks));
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    // After a wipe the Cronies come back with him (they spawn here only; a dead one would sit out for 12 h).
    void JustReachedHome() override
    {
        BossAI::JustReachedHome();
        uint32 revived = 0;
        for (Creature* crony : Cronies(false))
            if (!crony->IsAlive())
            {
                crony->Respawn(true);
                ++revived;
            }
        if (revived)
            LogHu("cronies-respawned", Acore::StringFormat("count={}", revived));
    }

    void JustDied(Unit* killer) override
    {
        Talk(SAY_HURLEY_DEATH);
        Cleanup();
        BossAI::JustDied(killer);   // the kegs and the puddles go with him
        LogHu("death", Acore::StringFormat("killer={} stacks={} smashed={}", killer ? killer->GetName() : "none",
            _run.stacks, _run.smashed));
    }

    // Kegs and puddles are tracked, never zoned into combat: an unmarked keg is out of everyone's fight (the marked
    // one joins it, HU3), a puddle is a look.
    void JustSummoned(Creature* summon) override
    {
        if (summon && (summon->GetEntry() == NPC_BRD_LAGER_KEG || summon->GetEntry() == NPC_BRD_LAGER_PUDDLE))
        {
            summons.Summon(summon);
            return;
        }
        BossAI::JustSummoned(summon);
    }

    void SummonedCreatureDies(Creature* summon, Unit* killer) override
    {
        if (summon && summon->GetEntry() == NPC_BRD_LAGER_KEG)
            KegDied(summon, killer);
    }

    // The third stock keg GO (its SmartAI, SET_DATA 1,1) wakes him (GuzzlerLogic.h BarModel::KegUsed -> Awake).
    void SetData(uint32 type, uint32 value) override
    {
        if (type == DATA_HURLEY_WAKE && value == DATA_HURLEY_WAKE_VALUE && !_awake)
            Wake(true, "kegs");
    }

    uint32 GetData(uint32 type) const override
    {
        if (type == DATA_HURLEY_AWAKE)
            return _awake ? 1 : 0;
        if (type == DATA_HURLEY_HEROIC)
            return Heroic() ? 1 : 0;
        return 0;
    }

    // HU3: while he walks to a keg or drinks, nothing turns him (the leash's switch, a hit).
    void AttackStart(Unit* who) override
    {
        if (_run.phase != LurchPhase::None)
            return;
        BossAI::AttackStart(who);
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type != POINT_MOTION_TYPE)
            return;
        if (id >= POINT_WAKE_FIRST && id < POINT_WAKE_FIRST + kWakePath.size() && _wakeStep)
        {
            uint32 const next = id - POINT_WAKE_FIRST + 1;
            if (next < kWakePath.size())
                MoveWake(next);
            else
                Arrive(true);
        }
        else if (id == POINT_KEG && _run.phase == LurchPhase::Walking)
            ReachKeg("arrived");
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        UpdatePuddles();        // out of combat too (`.dbtest` puddles)
        if (!_awake)
        {
            WakeCheck();
            return;
        }

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_fighting)
            return;

        RunKegRun();
        RunTimers();
        if (_run.phase == LurchPhase::None && !me->HasUnitState(UNIT_STATE_CASTING))
            DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The wake-up
    // ----------------------------------------------------------------------------------------------------------------

    void Hide()
    {
        _wakeStep = 0;
        me->SetVisible(false);
        me->SetReactState(REACT_PASSIVE);
        me->SetImmuneToPC(true);
    }

    void ShowAwake()
    {
        me->SetVisible(true);
        me->SetImmuneToPC(false);
        me->SetReactState(REACT_AGGRESSIVE);
    }

    // `walk`: the stock run down the escort path with the yell; else (the reload case) at home at once.
    void Wake(bool walk, char const* why)
    {
        _awake = true;
        me->SetVisible(true);
        me->SetImmuneToPC(false);
        for (Creature* crony : Cronies(true))
            if (crony->IsAIEnabled && crony->AI())
                crony->AI()->SetData(DATA_HURLEY_WAKE, walk ? WAKE_WALK : WAKE_AT_HOME);
        LogHu("wake", Acore::StringFormat("why={} walk={}", why, walk ? 1 : 0));
        if (walk)
        {
            Talk(SAY_HURLEY_WAKE);
            me->SetReactState(REACT_PASSIVE);   // until the path's end (a hit ends it early: JustEngagedWith)
            MoveWake(0);
            return;
        }
        Point3 const& home = kWakePath.back();
        me->NearTeleportTo(home.x, home.y, home.z, me->GetOrientation());
        Arrive(false);
    }

    void MoveWake(uint32 step)
    {
        _wakeStep = step + 1;
        Point3 const& node = kWakePath[step];
        me->GetMotionMaster()->MovePoint(POINT_WAKE_FIRST + step, node.x, node.y, node.z, FORCED_MOVEMENT_RUN);
    }

    // The path's end: home here, aggressive, and the stock line; he attacks the nearest player (the quirk fixed).
    void Arrive(bool say)
    {
        _wakeStep = 0;
        me->SetHomePosition(me->GetPosition());
        me->SetReactState(REACT_AGGRESSIVE);
        if (!say)
            return;
        Talk(SAY_HURLEY_ARRIVE);
        if (!me->IsEngaged())
            if (Player* target = NearestTarget(me))
                AttackStart(target);
    }

    // Hidden: every stock keg GO there and none standing means they were used before a reload.
    void WakeCheck()
    {
        if (_clockMs < _wakeCheckAtMs)
            return;
        _wakeCheckAtMs = _clockMs + kWakeCheckMs;
        std::list<GameObject*> kegs;
        me->GetGameObjectListWithEntryInGrid(kegs, GO_THUNDERBREW_LAGER_KEG, kKegGoScanYd);
        uint32 standing = 0;
        for (GameObject* keg : kegs)
            if (keg->isSpawned())
                ++standing;
        if (WakeFromUsedKegs(static_cast<uint32>(kegs.size()), standing))
            Wake(false, "kegs-used");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The pull, the Cronies, the kegs
    // ----------------------------------------------------------------------------------------------------------------

    void StartFight(Unit* who)
    {
        if (!_heroicForced)
            _heroic = IsHeroicMap(me);
        _heroicForced = false;
        OnBossPull(me, kBoss);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_HURLEY;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);
        _fighting = true;
        _run = KegRun();
        _wideBreath = false;
        _kegRunAtMs = _clockMs + kKegRunFirstMs;
        _breathAtMs = _clockMs + kBreathFirstMs;
        _mortalStrikeAtMs = _clockMs + urand(kMortalStrikeFirstMinMs, kMortalStrikeFirstMaxMs);
        Mechanic::NoteNextCastIn(me, SPELL_HU_FLAME_BREATH_BAR, Ms(kBreathFirstMs));

        uint32 const kegs = SummonKegs();
        uint32 cronies = 0;
        for (Creature* crony : Cronies(true))
        {
            ++cronies;
            Mechanic::TrackUnit(me, crony);
            if (crony->IsInCombat() || !crony->IsAIEnabled || !crony->AI())
                continue;
            if (who && crony->IsValidAttackTarget(who))
                crony->AI()->AttackStart(who);
            else
                DoZoneInCombat(crony);
        }
        Describe();
        LogHu("engage", Acore::StringFormat("heroic={} kegs={} cronies={}", Heroic() ? 1 : 0, kegs, cronies));
    }

    // The six kegs on their spots (unselectable, out of combat until marked).
    uint32 SummonKegs()
    {
        DespawnKegs();
        uint32 count = 0;
        for (uint8 i = 0; i < kKegCount; ++i)
        {
            Point3 const& spot = kKegSpots[i];
            float const z = GroundZ(me, spot.x, spot.y, spot.z);
            float const facing = DungeonKit::BearingTo(spot.XY(), DungeonKit::PlaneOf(me));
            if (Creature* keg = me->SummonCreature(NPC_BRD_LAGER_KEG, spot.x, spot.y, z, facing,
                TEMPSUMMON_MANUAL_DESPAWN))
            {
                _kegs[i] = keg->GetGUID();
                ++count;
            }
            else
                _run.Died(i);   // no keg on this spot: never a lurch to it
        }
        return count;
    }

    Creature* Keg(int8 index) const
    {
        if (index < 0 || index >= int8(kKegCount) || _kegs[index].IsEmpty())
            return nullptr;
        Creature* keg = ObjectAccessor::GetCreature(*me, _kegs[index]);
        return keg && keg->IsAlive() ? keg : nullptr;
    }

    int8 KegIndex(ObjectGuid guid) const
    {
        for (uint8 i = 0; i < kKegCount; ++i)
            if (_kegs[i] == guid)
                return static_cast<int8>(i);
        return -1;
    }

    void DespawnKegs()
    {
        for (ObjectGuid& guid : _kegs)
        {
            if (!guid.IsEmpty())
                if (Creature* keg = ObjectAccessor::GetCreature(*me, guid))
                    keg->DespawnOrUnsummon();
            guid.Clear();
        }
    }

    // The Cronies around him (the alive ones with `aliveOnly`).
    std::vector<Creature*> Cronies(bool aliveOnly) const
    {
        std::list<Creature*> found;
        me->GetCreatureListWithEntryInGrid(found, NPC_BLACKBREATH_CRONY, kCronyScanYd);
        std::vector<Creature*> out;
        for (Creature* crony : found)
            if (!aliveOnly || crony->IsAlive())
                out.push_back(crony);
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Timers
    // ----------------------------------------------------------------------------------------------------------------

    void RunTimers()
    {
        if (_run.phase != LurchPhase::None || me->HasUnitState(UNIT_STATE_CASTING))
            return;     // he walks or drinks (HU3): the breath and the strike wait

        if (_clockMs >= _breathAtMs)
        {
            if (FlameBreath("timer"))
                _breathAtMs = _clockMs + kBreathEveryMs;
            else
                _breathAtMs = _clockMs + kRetryMs;
            return;
        }

        if (_clockMs >= _mortalStrikeAtMs)
            _mortalStrikeAtMs = _clockMs + (MortalStrike() ? urand(kMortalStrikeEveryMinMs, kMortalStrikeEveryMaxMs)
                : kRetryMs);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HU1 Mortal Strike
    // ----------------------------------------------------------------------------------------------------------------

    bool MortalStrike()
    {
        Unit* victim = me->GetVictim();
        if (!victim || !me->IsWithinMeleeRange(victim, kMeleeRangeYd))
            return false;
        me->CastSpell(victim, SPELL_HU_MORTAL_STRIKE, true);
        LogHu("mortal-strike", Acore::StringFormat("target={} pct={:.0f}", victim->GetName(),
            kMortalStrikePct(Heroic())));
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HU2 Flame Breath, HU6 Firewater
    // ----------------------------------------------------------------------------------------------------------------

    // A 2 s bar, then the cone down his front (his victim exempt; the tank's own hit at the resolve). False when he
    // has nobody to breathe at.
    bool FlameBreath(char const* why)
    {
        Unit* victim = me->GetVictim();
        if (!victim)
            return false;
        bool const heroic = Heroic();
        float const angle = BreathAngleDeg(heroic, _wideBreath);
        bool const wide = heroic && _wideBreath;
        _wideBreath = false;
        me->SetFacingToObject(victim);
        DungeonKit::CastBar(me, SPELL_HU_FLAME_BREATH_BAR);
        MechanicRef ref = Mechanic::Cone(me, me, angle, kBreathLengthYd, Ms(kBreathCastMs),
            BossMechanics::TankExempt::Yes);
        ref.Damage(kBreathPct(heroic)).School(SPELL_SCHOOL_FIRE).Spell(SPELL_HU_FLAME_BREATH).Weakened()
            .Tag(TAG_HU_FLAME_BREATH);
        Map* map = me->GetMap();
        ObjectGuid const self = me->GetGUID();
        ref.OnResolve([map, self, angle](BossMechanics::ResolveResult const& r)
        {
            Creature* hurley = map ? map->GetCreature(self) : nullptr;
            if (r.fizzled || !hurley || !hurley->IsAlive() || !hurley->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_hurley_blackbreath_rework*>(hurley->AI()))
                ai->BreathLanded(angle, r.hits.size());
        });
        Track(ref.Handle());
        Mechanic::NoteNextCastIn(me, SPELL_HU_FLAME_BREATH_BAR, Ms(kBreathEveryMs));
        LogHu("breath", Acore::StringFormat("why={} angle={:.0f} wide={} pct={:.0f} tank={:.0f}", why, angle,
            wide ? 1 : 0, kBreathPct(heroic), kBreathTankPct(heroic)));
        return true;
    }

    // The resolve: the look, the tank's own hit when he stands in the arc, and on heroic every puddle it touches burns.
    void BreathLanded(float angle, std::size_t hits)
    {
        me->CastSpell(me, SPELL_HU_FLAME_BREATH_LOOK, true);
        Vec2 const apex = DungeonKit::PlaneOf(me);
        float const facing = me->GetOrientation();
        bool tankHit = false;
        if (Unit* tank = me->GetVictim())
            if (tank->IsAlive() && CircleInCone(apex, facing, angle, kBreathLengthYd, DungeonKit::PlaneOf(tank),
                tank->GetCombatReach()))
            {
                me->CastSpell(tank, SPELL_HU_FLAME_BREATH_TANK, true);
                tankHit = true;
            }
        uint32 ignited = 0;
        if (Heroic())
            for (Puddle& puddle : _puddles)
                if (!puddle.burning && CircleInCone(apex, facing, angle, kBreathLengthYd,
                    Vec2{ puddle.at.GetPositionX(), puddle.at.GetPositionY() }, kPuddleRadius))
                {
                    Ignite(puddle);
                    ++ignited;
                }
        LogHu("breath-landed", Acore::StringFormat("hits={} tank={} ignited={}", hits, tankHit ? 1 : 0, ignited));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HU3 / HU4 the Keg Run
    // ----------------------------------------------------------------------------------------------------------------

    void RunKegRun()
    {
        switch (_run.phase)
        {
            case LurchPhase::Walking:
                if (_clockMs >= _lurchDeadlineMs)
                {
                    // Not there in time (a path he cannot finish): close enough, he drinks; else he gives up.
                    Creature* keg = Keg(_run.marked);
                    if (keg && me->GetExactDist2d(keg) <= kKegStandOffYd + 3.f)
                        ReachKeg("deadline");
                    else
                    {
                        _run.GiveUp();
                        LogHu("lurch-gave-up", Acore::StringFormat("keg={}", int32(_run.marked) + 1));
                        BackToTank();
                    }
                }
                return;
            case LurchPhase::Drinking:
                if (_clockMs >= _drinkEndMs)
                    FinishDrink();
                return;
            case LurchPhase::None:
                break;
        }
        if (!_run.CanStart() || _clockMs < _kegRunAtMs || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (StartLurch("timer"))
            _kegRunAtMs = _clockMs + kKegRunEveryMs(Heroic());
        else
            _kegRunAtMs = _clockMs + kRetryMs;
    }

    // Yell 2, mark a keg (or the one he gave up on), walk to it. False when no keg can be reached now.
    bool StartLurch(char const* why)
    {
        int8 index = _run.Pending();
        bool const again = index >= 0;
        if (!again)
            index = PickKeg(_run.alive, urand(0, 1023));
        Creature* keg = Keg(index);
        if (!keg)
        {
            if (index >= 0)
                _run.Died(static_cast<uint8>(index));   // gone without a death we saw: drop the spot
            return false;
        }
        if (!(again ? _run.Restart() : _run.Start(static_cast<uint8>(index))))
            return false;

        Talk(SAY_HURLEY_THIRSTY);
        if (!again)
        {
            keg->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
            keg->CastSpell(keg, SPELL_HU_KEG_MARK, true);
            DoZoneInCombat(keg);
            Mechanic::TrackUnit(me, keg);
        }
        me->SetReactState(REACT_PASSIVE);
        me->AttackStop();
        me->InterruptNonMeleeSpells(false);
        Vec2 const to = ApproachPoint(DungeonKit::PlaneOf(me), DungeonKit::PlaneOf(keg), kKegStandOffYd);
        float const distance = DungeonKit::Distance(DungeonKit::PlaneOf(me), to);
        float const z = GroundZ(me, to.x, to.y, keg->GetPositionZ());
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MovePoint(POINT_KEG, to.x, to.y, z, FORCED_MOVEMENT_WALK);
        _lurchDeadlineMs = _clockMs + LurchDeadlineMs(distance);
        LogHu("keg-run", Acore::StringFormat("why={} keg={} again={} distance={:.1f} kegs={} stacks={}", why,
            int32(index) + 1, again ? 1 : 0, distance, _run.Left(), _run.stacks));
        return true;
    }

    // He stands by the marked keg: a 3 s drink (the bar is the look; the clock decides, so a refused bar changes
    // nothing).
    void ReachKeg(char const* why)
    {
        if (!_run.Arrived())
            return;
        me->GetMotionMaster()->Clear();
        me->StopMoving();
        if (Creature* keg = Keg(_run.marked))
            me->SetFacingToObject(keg);
        me->CastSpell(me, SPELL_HU_DRINK, false);
        _drinkEndMs = _clockMs + kDrinkMs;
        LogHu("drink", Acore::StringFormat("why={} keg={}", why, int32(_run.marked) + 1));
    }

    // The drink ran its 3 s: 10% of his health, a stack, the keg drained (gone, no puddle).
    void FinishDrink()
    {
        int8 const index = _run.marked;
        if (!_run.DrinkDone())
            return;
        uint32 const heal = me->CountPctFromMaxHealth(kDrinkHealPct);
        if (SpellInfo const* info = sSpellMgr->GetSpellInfo(SPELL_HU_DRINK))
        {
            HealInfo healInfo(me, me, heal, info, info->GetSchoolMask());
            me->HealBySpell(healInfo);
        }
        uint32 const stacks = DungeonKit::AddStacks(me, SPELL_HU_LIQUID_COURAGE, 1, me, kKegCount);
        me->CastSpell(me, SPELL_HU_COURAGE_FLASH, true);
        Talk(EMOTE_HURLEY_DRINK);
        if (Creature* keg = Keg(index))
            keg->DespawnOrUnsummon();
        if (index >= 0)
            _kegs[index].Clear();
        _wideBreath = true;     // HU6 heroic: the next breath is twice as wide
        LogHu("drank", Acore::StringFormat("keg={} heal={} stacks={} health={:.0f}% kegs={}", int32(index) + 1, heal,
            stacks, me->GetHealthPct(), _run.Left()));
        BackToTank();
    }

    // A keg died: the marked one in time turns him back (yell 4); every smashed keg spills a puddle.
    void KegDied(Creature* keg, Unit* killer)
    {
        int8 const index = KegIndex(keg->GetGUID());
        if (index < 0)
            return;
        bool const drinking = _run.phase == LurchPhase::Drinking;
        KegEnd const end = _run.Died(static_cast<uint8>(index));
        _kegs[index].Clear();
        if (end == KegEnd::Ignored)
            return;
        SpillPuddle(keg->GetPosition());
        if (end == KegEnd::Smashed)
        {
            if (drinking)
                me->InterruptNonMeleeSpells(false);
            Talk(SAY_HURLEY_KEG_SMASHED);
            BackToTank();
        }
        LogHu(end == KegEnd::Smashed ? "keg-smashed" : "keg-spilled", Acore::StringFormat(
            "keg={} killer={} during={} kegs={}", int32(index) + 1, killer ? killer->GetName() : "none",
            drinking ? "drink" : "walk", _run.Left()));
    }

    void BackToTank()
    {
        me->SetReactState(REACT_AGGRESSIVE);
        if (!me->IsEngaged())
            return;
        me->GetMotionMaster()->Clear();
        if (Unit* target = me->SelectVictim())
        {
            BossAI::AttackStart(target);
            me->GetMotionMaster()->MoveChase(target);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HU5 / HU6 the puddles
    // ----------------------------------------------------------------------------------------------------------------

    void SpillPuddle(Position const& at)
    {
        Puddle puddle;
        puddle.at = at;
        puddle.expiresAtMs = _clockMs + kPuddleLifeMs;
        if (TempSummon* stalker = me->SummonCreature(NPC_BRD_LAGER_PUDDLE, at, TEMPSUMMON_TIMED_DESPAWN,
            kPuddleLifeMs + kBurningLagerMs))
        {
            stalker->CastSpell(stalker, SPELL_HU_LAGER_PUDDLE, true);
            puddle.stalker = stalker->GetGUID();
        }
        _puddles.push_back(puddle);
        LogHu("puddle", Acore::StringFormat("at=({:.1f}, {:.1f}) look={} puddles={}", at.GetPositionX(),
            at.GetPositionY(), puddle.stalker.IsEmpty() ? 0 : 1, _puddles.size()));
    }

    // HU6: the puddle burns for 20 s (a persistent registry zone; no buff while it burns), then it is gone.
    void Ignite(Puddle& puddle)
    {
        puddle.burning = true;
        puddle.expiresAtMs = _clockMs + kBurningLagerMs;
        if (Creature* stalker = ObjectAccessor::GetCreature(*me, puddle.stalker))
        {
            stalker->RemoveAurasDueToSpell(SPELL_HU_LAGER_PUDDLE);
            stalker->CastSpell(stalker, SPELL_HU_BURNING_LAGER_LOOK, true);
        }
        MechanicRef ref = Mechanic::Circle(me, puddle.at, kPuddleRadius, Ms(kBurningLagerTickMs));
        ref.Persistent(Ms(kBurningLagerMs - kBurningLagerTickMs), Ms(kBurningLagerTickMs)).Damage(kBurningLagerPct)
            .TankDamage(kBurningLagerPct).School(SPELL_SCHOOL_FIRE).Spell(SPELL_HU_BURNING_LAGER).NoFillTimer()
            .Tag(TAG_HU_BURNING_LAGER);
        puddle.zone = ref.Handle();
        Track(puddle.zone);
        LogHu("firewater", Acore::StringFormat("at=({:.1f}, {:.1f}) pct={:.0f}/s", puddle.at.GetPositionX(),
            puddle.at.GetPositionY(), kBurningLagerPct));
    }

    // Once a second: Tipsy and Lager Buzz on every player in an amber puddle; expired puddles go.
    void UpdatePuddles()
    {
        if (_puddles.empty() || _clockMs < _puddleTickAtMs)
            return;
        _puddleTickAtMs = _clockMs + kPuddleTickMs;
        Map* map = me->GetMap();
        for (auto it = _puddles.begin(); it != _puddles.end();)
        {
            if (_clockMs >= it->expiresAtMs)
            {
                RemovePuddle(*it);
                it = _puddles.erase(it);
                continue;
            }
            if (!it->burning && map)
                for (auto const& ref : map->GetPlayers())
                {
                    Player* player = ref.GetSource();
                    if (!player || !player->IsAlive() || player->IsGameMaster())
                        continue;
                    if (std::fabs(player->GetPositionZ() - it->at.GetPositionZ()) > kPuddleZBandYd
                        || player->GetExactDist2d(it->at.GetPositionX(), it->at.GetPositionY()) > kPuddleRadius)
                        continue;
                    RefreshOrCast(player, SPELL_HU_TIPSY);
                    RefreshOrCast(player, SPELL_HU_LAGER_BUZZ);
                }
            ++it;
        }
    }

    void RemovePuddle(Puddle const& puddle)
    {
        if (puddle.zone)
            Mechanic::Cancel(me, puddle.zone);
        if (!puddle.stalker.IsEmpty())
            if (Creature* stalker = ObjectAccessor::GetCreature(*me, puddle.stalker))
                stalker->DespawnOrUnsummon();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The descriptor, state
    // ----------------------------------------------------------------------------------------------------------------

    // Kill order: the marked keg (the only selectable one), the Cronies (cleave), then him (0). No interrupt (the
    // breath and the drink cannot be kicked), no dispel, no purge (Liquid Courage is not purgeable).
    void Describe()
    {
        BossMechanics::Descriptor d;
        d.targets.push_back(BossMechanics::TargetEntry(NPC_BRD_LAGER_KEG, kKegPriority, BossMechanics::Who::Dps,
            BossMechanics::Condition::HasAura(SPELL_HU_KEG_MARK)));
        d.targets.push_back(BossMechanics::TargetEntry(NPC_BLACKBREATH_CRONY, kCronyPriority,
            BossMechanics::Who::Dps).AoeOk());
        Mechanic::Describe(me, std::move(d));
    }

    bool Heroic() const
    {
        return _heroic;
    }

    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 64)      // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 32);
    }

    // Nothing pending, no keg, no puddle, every aura of the fight gone, his react state back (Reset, evade, death).
    void Cleanup()
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        for (Puddle const& puddle : _puddles)
            RemovePuddle(puddle);
        _puddles.clear();
        DespawnKegs();
        _run = KegRun();
        _fighting = false;
        _wideBreath = false;
        _kegRunAtMs = 0;
        _breathAtMs = 0;
        _mortalStrikeAtMs = 0;
        _lurchDeadlineMs = 0;
        _drinkEndMs = 0;
        me->RemoveAurasDueToSpell(SPELL_HU_LIQUID_COURAGE);
        if (_awake && me->IsAlive())
            me->SetReactState(REACT_AGGRESSIVE);
        if (instance)
            for (uint32 const spell : { uint32(SPELL_HU_MORTAL_STRIKE), uint32(SPELL_HU_TIPSY),
                uint32(SPELL_HU_LAGER_BUZZ), SPELL_STOCK_RUPTURE })
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
        _arena.Reset();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brd hurley` entry points
    // ----------------------------------------------------------------------------------------------------------------
public:
    // An empty string when fired; otherwise why not.
    std::string TestFire(TestKind kind, Player* gm)
    {
        switch (kind)
        {
            case TestKind::Wake:
                if (_awake)
                    return "He is awake already.";
                Wake(true, "test");
                break;
            case TestKind::KegRun:
                if (!_fighting)
                    return "Pull him first (the kegs come with the pull).";
                if (!_run.CanStart() || me->HasUnitState(UNIT_STATE_CASTING))
                    return "He is busy (a lurch, a drink or a cast), or no keg is left.";
                if (!StartLurch("test"))
                    return "No keg he can reach.";
                break;
            case TestKind::Breath:
                if (!_fighting)
                    return "Pull him first.";
                if (_run.phase != LurchPhase::None || me->HasUnitState(UNIT_STATE_CASTING))
                    return "He is busy; try again in a moment.";
                if (!FlameBreath("test"))
                    return "He has nobody to breathe at.";
                break;
            case TestKind::Puddle:
                if (!gm)
                    return "Run it in game.";
                SpillPuddle(gm->GetPosition());
                break;
            case TestKind::Ignite:
            {
                uint32 n = 0;
                for (Puddle& puddle : _puddles)
                    if (!puddle.burning)
                    {
                        Ignite(puddle);
                        ++n;
                    }
                if (!n)
                    return "No amber puddle to ignite.";
                break;
            }
            case TestKind::Clear:
                Cleanup();
                break;
        }
        return {};
    }

    // `.dbtest brd hurley heroic <0|1>`: the heroic form on a normal map (and back) until the end of the next pull.
    void TestHeroic(bool heroic)
    {
        _heroic = heroic;
        _heroicForced = true;
    }

    std::string TestState() const
    {
        auto left = [this](uint64 at) -> std::string
        {
            return at ? std::to_string(at > _clockMs ? (at - _clockMs) / 1000 : 0) + "s" : "-";
        };
        char const* phase = _run.phase == LurchPhase::Walking ? "walking"
            : (_run.phase == LurchPhase::Drinking ? "drinking" : "fighting");
        return Acore::StringFormat("hurley awake={} heroic={} fighting={} phase={} marked={} kegs={} stacks={} "
            "smashed={} wide={} kegrun={} breath={} strike={} puddles={}", _awake ? 1 : 0, Heroic() ? 1 : 0,
            _fighting ? 1 : 0, phase, int32(_run.marked) + 1, _run.Left(), _run.stacks, _run.smashed,
            _wideBreath ? 1 : 0, left(_kegRunAtMs), left(_breathAtMs), left(_mortalStrikeAtMs), _puddles.size());
    }

private:
    static constexpr int8 kKegPriority = 3;     // the marked keg first
    static constexpr int8 kCronyPriority = 2;   // then the Cronies, then him (0)

    DungeonKit::ArenaGuard _arena;
    bool _awake = false;            // the wake ran (not saved: the keg GOs' state stands in for it, WakeCheck)
    uint32 _wakeStep = 0;           // 1..3 while he runs the escort path
    bool _heroic = false;
    bool _heroicForced = false;     // `.dbtest ... heroic`: kept through the next pull
    bool _fighting = false;
    bool _wideBreath = false;       // HU6: a drink since the last breath
    uint64 _clockMs = 0;            // the AI's own clock
    uint64 _wakeCheckAtMs = 0;
    uint64 _kegRunAtMs = 0;         // HU3
    uint64 _breathAtMs = 0;         // HU2
    uint64 _mortalStrikeAtMs = 0;   // HU1
    uint64 _lurchDeadlineMs = 0;
    uint64 _drinkEndMs = 0;
    uint64 _puddleTickAtMs = 0;
    KegRun _run;
    std::array<ObjectGuid, kKegCount> _kegs;
    std::vector<Puddle> _puddles;
    std::vector<MechanicHandle> _live;
};

// ---------------------------------------------------------------------------------------------------------------------
// Blackbreath Crony 9541 (three spawns, here only): hidden with him, the run down the path, Sinister Strike; on heroic
// the stock Rupture and Bottle Toss (HU7, HU8). Section 7 #13: C++ instead of the stock per-guid SmartAI.
// ---------------------------------------------------------------------------------------------------------------------
struct npc_blackbreath_crony_rework : public ScriptedAI
{
    explicit npc_blackbreath_crony_rework(Creature* creature)
        : ScriptedAI(creature), _instance(creature->GetInstanceScript()) { }

    void Reset() override
    {
        _strikeAtMs = 0;
        _ruptureAtMs = 0;
        _tossAtMs = 0;
        _wakeStep = 0;
        if (HurleyAwake())
        {
            ShowAwake();
            // Respawned after a wipe (its home is its spawn again): straight to its place by him.
            float x, y, z;
            me->GetRespawnPosition(x, y, z);
            if (me->GetHomePosition().GetExactDist2d(x, y) < 1.f)
                ToPathEnd();
        }
        else
            Hide();
    }

    void SetData(uint32 type, uint32 value) override
    {
        if (type != DATA_HURLEY_WAKE || !_hidden)
            return;
        ShowAwake();
        if (value == WAKE_WALK)
        {
            me->SetReactState(REACT_PASSIVE);
            MoveWake(0);
        }
        else
            ToPathEnd();
    }

    // A Crony pulled pulls him (and so the others); struck on the way down, its walk ends here.
    void JustEngagedWith(Unit* who) override
    {
        if (_wakeStep)
            Arrive(false);
        _strikeAtMs = _clockMs + urand(kSinisterStrikeFirstMinMs, kSinisterStrikeFirstMaxMs);
        _ruptureAtMs = _clockMs + kRuptureFirstMs;
        _tossAtMs = _clockMs + kBottleTossFirstMs;
        if (Creature* hurley = Hurley())
            if (hurley->IsAlive() && !hurley->IsInCombat() && hurley->IsAIEnabled && who
                && hurley->IsValidAttackTarget(who))
                hurley->AI()->AttackStart(who);
    }

    // While Hurley fights, a Crony never walks home on its own: back into his fight.
    void EnterEvadeMode(EvadeReason why) override
    {
        if (Creature* hurley = Hurley())
            if (hurley->IsAlive() && hurley->IsEngaged())
            {
                DoZoneInCombat();
                if (me->IsEngaged())
                    return;
            }
        ScriptedAI::EnterEvadeMode(why);
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type != POINT_MOTION_TYPE || !_wakeStep || id < POINT_WAKE_FIRST
            || id >= POINT_WAKE_FIRST + kWakePath.size())
            return;
        uint32 const next = id - POINT_WAKE_FIRST + 1;
        if (next < kWakePath.size())
            MoveWake(next);
        else
            Arrive(true);
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        if (!UpdateVictim())
            return;
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;

        Unit* victim = me->GetVictim();
        bool const heroic = Heroic();
        if (_clockMs >= _strikeAtMs)
        {
            if (victim && me->IsWithinMeleeRange(victim, kMeleeRangeYd))
            {
                me->CastSpell(victim, SPELL_STOCK_SINISTER_STRIKE, false);
                _strikeAtMs = _clockMs + urand(kSinisterStrikeEveryMinMs, kSinisterStrikeEveryMaxMs);
            }
            else
                _strikeAtMs = _clockMs + kRetryMs;
        }
        if (heroic && _clockMs >= _ruptureAtMs)
        {
            if (victim && me->IsWithinMeleeRange(victim, kMeleeRangeYd))
            {
                me->CastSpell(victim, SPELL_STOCK_RUPTURE, false);
                _ruptureAtMs = _clockMs + urand(kRuptureEveryMinMs, kRuptureEveryMaxMs);
            }
            else
                _ruptureAtMs = _clockMs + kRetryMs;
        }
        if (heroic && _clockMs >= _tossAtMs)
            _tossAtMs = _clockMs + (BottleToss("timer") ? kBottleTossEveryMs : kRetryMs);
        DoMeleeAttackIfReady();
    }

    // HU8: a 3 yd circle on a random player of this Crony's fight (the tank too, ruling 88), 1.5 s, owned by Hurley
    // (bot shapes belong to the boss in combat with the group: without him, no toss).
    bool BottleToss(char const* why)
    {
        Creature* hurley = Hurley();
        if (!hurley || !hurley->IsAlive() || !hurley->IsEngaged())
            return false;
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        Player* target = DungeonKit::PickPlayer(me, rule);
        if (!target)
            return false;
        Position const spot(target->GetPositionX(), target->GetPositionY(), target->GetPositionZ(), 0.f);
        MechanicRef ref = Mechanic::Circle(hurley, BossMechanics::Anchor(spot), kBottleRadius, Ms(kBottleTossWarnMs));
        ref.Damage(kBottleTossPct).TankDamage(kBottleTossPct).Weakened().Spell(SPELL_HU_BOTTLE_TOSS)
            .Tag(TAG_HU_BOTTLE_TOSS);
        if (!ref.IsValid())
            return false;
        me->CastSpell(spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(), SPELL_HU_BOTTLE_TOSS_LOOK, true);
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "bottle-toss", Acore::StringFormat("why={} crony={} target={} "
            "pct={:.0f}", why, me->GetGUID().GetCounter(), target->GetName(), kBottleTossPct));
        return true;
    }

private:
    Creature* Hurley() const
    {
        if (_instance)
        {
            ObjectGuid const guid = _instance->GetGuidData(kGuidBossBase + BOSS_HURLEY);
            if (Creature* hurley = guid.IsEmpty() ? nullptr : ObjectAccessor::GetCreature(*me, guid))
                return hurley;
        }
        return me->FindNearestCreature(NPC_HURLEY, kCronyScanYd, false);
    }

    bool HurleyAwake() const
    {
        Creature* hurley = Hurley();
        return hurley && hurley->IsAIEnabled && hurley->AI() && hurley->AI()->GetData(DATA_HURLEY_AWAKE);
    }

    bool Heroic() const
    {
        Creature* hurley = Hurley();
        if (hurley && hurley->IsAIEnabled && hurley->AI())
            return hurley->AI()->GetData(DATA_HURLEY_HEROIC) != 0;
        return IsHeroicMap(me);
    }

    void Hide()
    {
        _hidden = true;
        me->SetVisible(false);
        me->SetReactState(REACT_PASSIVE);
        me->SetImmuneToPC(true);
    }

    void ShowAwake()
    {
        _hidden = false;
        me->SetVisible(true);
        me->SetImmuneToPC(false);
        me->SetReactState(REACT_AGGRESSIVE);
    }

    Point3 Node(uint32 step) const
    {
        float x, y, z;
        me->GetRespawnPosition(x, y, z);
        return CronyNode(kWakePath[step], Point3{ x, y, z }, kHurleySpawn);
    }

    void MoveWake(uint32 step)
    {
        _wakeStep = step + 1;
        Point3 const node = Node(step);
        float const z = GroundZ(me, node.x, node.y, node.z);
        me->GetMotionMaster()->MovePoint(POINT_WAKE_FIRST + step, node.x, node.y, z, FORCED_MOVEMENT_RUN);
    }

    // The reload case (and a respawn after a wipe): at the path's end at once.
    void ToPathEnd()
    {
        Point3 const node = Node(kWakePath.size() - 1);
        float const z = GroundZ(me, node.x, node.y, node.z);
        me->NearTeleportTo(node.x, node.y, z, me->GetOrientation());
        Arrive(false);
    }

    void Arrive(bool attack)
    {
        _wakeStep = 0;
        me->SetHomePosition(me->GetPosition());
        me->SetReactState(REACT_AGGRESSIVE);
        if (attack && !me->IsEngaged())
            if (Player* target = NearestTarget(me))
                AttackStart(target);
    }

    InstanceScript* _instance = nullptr;
    bool _hidden = false;
    uint32 _wakeStep = 0;
    uint64 _clockMs = 0;
    uint64 _strikeAtMs = 0;
    uint64 _ruptureAtMs = 0;
    uint64 _tossAtMs = 0;
};

namespace
{
    boss_hurley_blackbreath_rework* HurleyAI(ChatHandler* handler)
    {
        Creature* boss = BrdTest::FindBoss(handler, NPC_HURLEY);
        auto* ai = boss && boss->IsAIEnabled ? dynamic_cast<boss_hurley_blackbreath_rework*>(boss->AI()) : nullptr;
        if (!ai && boss)
            handler->SendErrorMessage("{} does not run the reworked script.", boss->GetName());
        return ai;
    }

    bool Fire(ChatHandler* handler, TestKind kind, char const* ok)
    {
        boss_hurley_blackbreath_rework* ai = HurleyAI(handler);
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

    // `.dbtest brd hurley info`
    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowBossInfo(handler, NPC_HURLEY, BOSS_HURLEY);
    }

    // `.dbtest brd hurley state`: his clocks, the Keg Run, the puddles.
    bool HandleState(ChatHandler* handler)
    {
        boss_hurley_blackbreath_rework* ai = HurleyAI(handler);
        if (!ai)
            return false;
        handler->SendSysMessage(ai->TestState());
        return true;
    }

    // `.dbtest brd hurley wake`: the kegs' wake-up without tapping them (the yell, the run, the attack).
    bool HandleWake(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Wake, "Hurley wakes: he and the Cronies run down and attack.");
    }

    // `.dbtest brd hurley kegrun`: HU3 now (in combat).
    bool HandleKegRun(ChatHandler* handler)
    {
        return Fire(handler, TestKind::KegRun, "Keg Run: a keg is marked and he walks to it (smash it first).");
    }

    // `.dbtest brd hurley breath`: HU2 now (in combat; heroic: puddles in the cone ignite).
    bool HandleBreath(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Breath, "Flame Breath: a 2 s bar, then the cone down his front.");
    }

    // `.dbtest brd hurley puddle`: HU5 at your feet (30 s).
    bool HandlePuddle(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Puddle, "A Lager Puddle at your feet (Tipsy and Lager Buzz, 30 s).");
    }

    // `.dbtest brd hurley ignite`: HU6 on every amber puddle.
    bool HandleIgnite(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Ignite, "Firewater: every amber puddle burns (20 s).");
    }

    // `.dbtest brd hurley bottle`: HU8 from the nearest Crony (in combat, Hurley engaged).
    bool HandleBottle(ChatHandler* handler)
    {
        if (!BrdTest::RequireBlackrockDepths(handler))
            return false;
        Player* gm = handler->GetPlayer();
        Creature* crony = gm ? gm->FindNearestCreature(NPC_BLACKBREATH_CRONY, 100.f, true) : nullptr;
        auto* ai = crony && crony->IsAIEnabled ? dynamic_cast<npc_blackbreath_crony_rework*>(crony->AI()) : nullptr;
        if (!ai)
        {
            handler->SendErrorMessage("No living Blackbreath Crony on the reworked script within 100 yd.");
            return false;
        }
        if (!ai->BottleToss("test"))
        {
            handler->SendErrorMessage("No toss: Hurley must be alive and fighting, and the Crony needs a target.");
            return false;
        }
        handler->SendSysMessage("Bottle Toss: a 3 yd circle on a player of its fight (1.5 s).");
        return true;
    }

    // `.dbtest brd hurley clear`: every zone, keg and puddle goes.
    bool HandleClear(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Clear, "Cleared.");
    }

    // `.dbtest brd hurley heroic [0|1]`
    bool HandleHeroic(ChatHandler* handler, Optional<uint32> on)
    {
        boss_hurley_blackbreath_rework* ai = HurleyAI(handler);
        if (!ai)
            return false;
        ai->TestHeroic(!on || *on != 0);
        handler->SendSysMessage("The heroic form is set until the end of the next pull.");
        return true;
    }

    ChatCommandTable const& BossHurleyBlackbreathTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",   HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",  HandleState,    SEC_GAMEMASTER, Console::No },
            { "wake",   HandleWake,     SEC_GAMEMASTER, Console::No },
            { "kegrun", HandleKegRun,   SEC_GAMEMASTER, Console::No },
            { "breath", HandleBreath,   SEC_GAMEMASTER, Console::No },
            { "puddle", HandlePuddle,   SEC_GAMEMASTER, Console::No },
            { "ignite", HandleIgnite,   SEC_GAMEMASTER, Console::No },
            { "bottle", HandleBottle,   SEC_GAMEMASTER, Console::No },
            { "clear",  HandleClear,    SEC_GAMEMASTER, Console::No },
            { "heroic", HandleHeroic,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_hurley_blackbreath_rework()
{
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_hurley_blackbreath_rework, BlackrockDepthsRework::kInstanceScriptName);
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_blackbreath_crony_rework, BlackrockDepthsRework::kInstanceScriptName);
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_brd_lager_keg, BlackrockDepthsRework::kInstanceScriptName);
    BrdTest::RegisterBoss("hurley", BossHurleyBlackbreathTestCommands());
}
