/*
 * mod-dungeon-bosses, Blackrock Depths D7: Pyromancer Loregrain (9024), "Franclorn's last stand". Build spec S2
 * 165-219 (docs/dungeons/blackrock-depths-2-shadowforge-city.md, rulings 37-39 and 91; the moving ward S2 147-156),
 * handoff sections 3.4 / 3.5 / 3.6 / 3.8 rows D7, section 7 #21 and section 8 #18 / #36 (defaults built). Replaces
 * his SmartAI (the four rows are dropped by the S0 SQL rev; the two Twilight Emissaries at his feet, the 15288 addon
 * aura and the texts by rev_loregrain_blackrock_depths.sql): the template is bound by apps/dbc-tools
 * source/npcs/blackrock_depths/loregrain.py. Pure rules: LoregrainLogic.h. Not flex: 5 players.
 *
 *   LG1  Fire Tide      20 s, then every 30 s (heroic 25 s): the yell, the boss emote of the ward's move, a 4 s cast
 *                       bar, and two registry mechanics at the ward's new spot with the ward's radius locked now
 *                       (section 8 #18; the G1 `ward` drill row): a Stack (tag 11) and a Donut from the ward's edge to
 *                       45 yd (tag 12), 30% / 45% x (1 + Fury / 100), at most 75%, Fire, Weakened, the tank on its
 *                       own row (ruling 88). On landing it washes every Molten Splash patch centered outside the ward
 *   LG2  Ward move      the first Fire Tide's warning summons Franclorn's Spirit 9542 at the middle spot (the ward
 *                       forms there, not on the pull: review Q1); each later one shows it at a neighboring spot of
 *                       three; a ward that forms on Loregrain throws him clear
 *   LG3  The ward       6 / 5 yd, -1 yd per living totem (min 2), heroic -1 yd per Wrath (base min 3). Loregrain cannot
 *                       enter it: inside he is thrown clear (a computed jump into the corridor, the spirit's look);
 *                       with his victim inside he walks to its edge (no chase into it) and holds there, and answers
 *                       with Searing Bolt on a victim out of his reach (rule 10)
 *   LG4  Defiling Totem 10 s, then every 15 s (heroic 12 s), at a random spot inside the ward (before the first tide:
 *                       where it will form), at most 3 alive; kill
 *                       order. Each shrinks the ward 1 yd and feeds Fury 2 a second; a kill takes 10 Fury
 *   LG5  Molten Splash  6 s, then every 10 s (heroic 8 s): 2 (heroic 3) random players' spots (the tank included):
 *                       a 4 yd circle, 2 s, 20% / 35%, Fire, Weakened; then a 4 yd patch burns there (4% / 6% a
 *                       second, gap 20 default, no Weakened) until a tide washes it, or for the fight inside the ward
 *   LG6  Fury           a meter on him (stacks 0-100), section LoregrainLogic.h; at 100 a Wrath of Ragnaros
 *   LG7  Wrath          an extra tide with no ward move: 4 s warning normal, 2 s heroic (section 7 #21); Fury to 30;
 *                       heroic, the ward cracks 1 yd for the fight when it lands
 *   LG8  Molten Blast   6 s, then every 12 s: a 2 s Fire kick on a random player within 30 yd (15% / 25% of their
 *                       row); +10 Fury if it lands, -15 if interrupted. Interrupt list
 *   LG9  Fire Ward      5 s, then every 30 s: absorbs 8% of his health from any school (Magic: a purge breaks it);
 *                       +3 Fury a second while it holds, -20 when it breaks or is purged. Purge list
 *   LG10 Flame Shock    9 s, then every 8-21 s: a random player within 20 yd, 6% / 10% and 3% / 5% every 3 s for 12 s
 *                       (Magic). Dispel list (a reward)
 *   Death               the spirit returns to the statue and thanks the group (it stays); totems, patches and stalkers
 *                       go
 *   Arena               BlackrockDepthsRework::LeashOptions on LoregrainArena() (no grips; holds at the edge)
 *
 * Every timer runs on the AI's own clock (ms since the pull). Every firing logs one INFO line "brd loregrain
 * <mechanic> ..." (module.dungeonbosses); the pull line is OnBossPull's.
 */

#include "ArenaGuard.h"
#include "BlackrockDepthsKit.h"
#include "BlackrockDepthsRework.h"
#include "BlackrockDepthsTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "LoregrainLogic.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include <algorithm>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdLoregrain;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;
using DungeonKit::PlaneOf;

namespace
{
    char const* const kBossKey = "loregrain";

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(ms);
    }

    uint32 constexpr kGuardCheckMs = 250;           // the ward's repel and hold
    uint32 constexpr kHoldPointId = 1;              // the walk to the ward's edge (MovePoint id)
    uint32 constexpr kRetryMs = 1000;               // a cast with no target in range tries again
    uint32 constexpr kTotemCorpseMs = 5000;
}

struct boss_pyromancer_loregrain_rework : public BossAI
{
private:
    struct Tide
    {
        bool active = false;
        bool wrath = false;
        uint64 landMs = 0;
        Vec2 center;
        float radius = 0.f;
    };

    struct Splash
    {
        Position at;
        uint64 landMs = 0;
        ObjectGuid stalker;
        bool heroic = false;
    };

    struct Patch
    {
        MechanicHandle handle;
        Vec2 at;
        ObjectGuid stalker;
    };

public:
    explicit boss_pyromancer_loregrain_rework(Creature* creature)
        : BossAI(creature, BOSS_LOREGRAIN), _arena(LoregrainArena(), LeashOptions(kBossKey)) { }

    void Reset() override
    {
        _Reset();
        Cleanup(false);
        _arena.Reset();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        Cleanup(false);     // a `.dbtest` mechanic out of combat may have left something behind
        me->SetStandState(UNIT_STAND_STATE_STAND);      // he kneels at the statue (creature_addon bytes1 8)
        OnBossPull(me, kBossKey);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_LOREGRAIN;
        Mechanic::BeginEncounter(me, options);

        bool const heroic = IsHeroicMap(me);
        _tidePlannedMs = kTideFirstMs;
        _nextTideMs = kTideFirstMs;
        _totemPlannedMs = kTotemFirstMs;
        _nextTotemMs = kTotemFirstMs;
        _splashPlannedMs = kSplashFirstMs;
        _nextSplashMs = kSplashFirstMs;
        _blastPlannedMs = kMoltenBlastFirstMs;
        _nextBlastMs = kMoltenBlastFirstMs;
        _nextFlameShockMs = kFlameShockFirstMs;
        _nextFireWardMs = kFireWardFirstMs;
        _nextFuryTickMs = kFuryTickMs;
        _wardSpot = kWardSpotFirst;     // the ward forms there at the first Fire Tide (not on the pull: review Q1)
        Describe(heroic);
        Mechanic::NoteNextCastIn(me, SPELL_LG_MOLTEN_BLAST, Ms(kMoltenBlastFirstMs));
        _arena.Engage(me);
        Talk(YELL_LG_PULL);
        Log("engage", Acore::StringFormat("heroic={} ward={:.0f} spirit={}", heroic ? 1 : 0, LiveRadius(heroic),
            Spirit() ? 1 : 0));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup(false);
        _arena.Reset();
        BossAI::EnterEvadeMode(why);
    }

    // A new victim inside the ward (a taunt while he holds, a threat swap): no chase into it; the ward guard walks
    // him to its edge and holds him there (R-1-A m4).
    void AttackStart(Unit* who) override
    {
        if (who && me->IsEngaged() && InWard(who))
        {
            AttackStartNoMove(who);
            return;
        }
        BossAI::AttackStart(who);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);       // the totems and the patch stalkers go with the summon list
        Talk(YELL_LG_DEATH);
        Cleanup(true);
        _arena.Reset();
        SpiritThanks();
        Log("death", Acore::StringFormat("killer={}", killer ? killer->GetName() : "none"));
    }

    // The spirit stays out of the summon list (BossAI despawns that list on death; the spirit stays for its line).
    // The stalkers join it but not the fight; the totems join both.
    void JustSummoned(Creature* summon) override
    {
        if (!summon)
            return;
        switch (summon->GetEntry())
        {
            case NPC_FRANCLORNS_SPIRIT:
                return;     // SummonSpirit sets it up (also when a dead boss summons it for its line)
            case NPC_BRD_STALKER:
                summons.Summon(summon);
                summon->SetReactState(REACT_PASSIVE);
                return;
            case NPC_BRD_DEFILING_TOTEM:
                BossAI::JustSummoned(summon);       // the summon list and the fight (DoZoneInCombat)
                summon->SetReactState(REACT_PASSIVE);
                summon->SetControlled(true, UNIT_STATE_ROOT);
                summon->CastSpell(summon, SPELL_LG_DEFILING_PRESENCE, true);
                return;
            default:
                BossAI::JustSummoned(summon);
                return;
        }
    }

    // LG4: a totem killed takes 10 Fury (and gives the ward its yard back: LiveRadius counts the living ones).
    void SummonedCreatureDies(Creature* summon, Unit* killer) override
    {
        if (!summon || summon->GetEntry() != NPC_BRD_DEFILING_TOTEM || !me->IsEngaged())
            return;
        AddFury(kFuryTotemKilled, "totem-killed",
            Acore::StringFormat("killer={} totems={}", killer ? killer->GetName() : "none", LivingTotems()));
    }

    // LG8: a landed Molten Blast feeds 10 Fury.
    void SpellHitTarget(Unit* target, SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_LG_MOLTEN_BLAST && me->IsEngaged())
            AddFury(kFuryBlastLanded, "blast-landed",
                Acore::StringFormat("target={}", target ? target->GetName() : "none"));
    }

    // LG8: an interrupted Molten Blast takes 15 Fury (never one the script cancelled itself).
    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (!spell || spell->Id != SPELL_LG_MOLTEN_BLAST || _selfInterrupt || !me->IsAlive() || !me->IsEngaged())
            return;
        AddFury(kFuryBlastInterrupted, "blast-interrupted");
    }

    void UpdateAI(uint32 diff) override
    {
        // The AI's own clock: every timer of the fight.
        _clockMs += diff;
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        bool const heroic = IsHeroicMap(me);
        UpdateFury();
        UpdateFireWardState();
        UpdateTide(heroic);
        UpdateSplashes();
        UpdateTotems(heroic);
        UpdateWardGuard(heroic, diff);

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        UpdateCasts(heroic);
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LG2 / LG3 Franclorn's Spirit and the ward
    // ----------------------------------------------------------------------------------------------------------------

    Creature* Spirit() const
    {
        Creature* spirit = _spirit ? ObjectAccessor::GetCreature(*me, _spirit) : nullptr;
        return spirit && spirit->IsAlive() ? spirit : nullptr;
    }

    // Ward spot `index` on the floor (the mesh's height under it), facing up the corridor.
    Position SpotPosition(uint8 index) const
    {
        Point3 const& spot = kWardSpots[std::min<std::size_t>(index, kWardSpotCount - 1)];
        float z = spot.z + 1.f;
        me->UpdateAllowedPositionZ(spot.x, spot.y, z);
        return Position(spot.x, spot.y, z, std::atan2(kCorridorAxis.y, kCorridorAxis.x));
    }

    Creature* SummonSpirit(uint8 index)
    {
        if (Creature* old = Spirit())
            old->DespawnOrUnsummon();
        _wardSpot = index;
        Creature* spirit = me->SummonCreature(NPC_FRANCLORNS_SPIRIT, SpotPosition(index), TEMPSUMMON_MANUAL_DESPAWN);
        _spirit = spirit ? spirit->GetGUID() : ObjectGuid::Empty;
        if (!spirit)
        {
            Log("spirit-fail", Acore::StringFormat("spot={}", index));
            return nullptr;
        }
        // The ward's anchor: not selectable, not attackable, passive, rooted (the script moves it).
        spirit->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        spirit->SetUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
        spirit->SetReactState(REACT_PASSIVE);
        spirit->SetControlled(true, UNIT_STATE_ROOT);
        return spirit;
    }

    Creature* EnsureSpirit()
    {
        if (Creature* spirit = Spirit())
            return spirit;
        return SummonSpirit(_wardSpot);
    }

    void MoveSpirit(uint8 index)
    {
        _wardSpot = index;
        Position pos = SpotPosition(index);
        if (Creature* spirit = Spirit())
            spirit->NearTeleportTo(pos);
        else
            SummonSpirit(index);
    }

    void DespawnSpirit()
    {
        if (Creature* spirit = Spirit())
            spirit->DespawnOrUnsummon();
        _spirit.Clear();
    }

    Vec2 WardCenter() const
    {
        if (Creature* spirit = Spirit())
            return PlaneOf(spirit);
        return kWardSpots[_wardSpot].XY();
    }

    float LiveRadius(bool heroic)
    {
        return WardRadius(heroic, LivingTotems(), _cracks);
    }

    // Death: the spirit returns to the statue and thanks the group; it stays (the summon list never had it).
    void SpiritThanks()
    {
        Creature* spirit = Spirit();
        if (!spirit)
            spirit = SummonSpirit(kWardSpotAtPull);
        if (!spirit)
            return;
        MoveSpirit(kWardSpotAtPull);
        if (spirit->IsAIEnabled && spirit->AI())
            spirit->AI()->Talk(SAY_FRANCLORN_THANKS);
        Log("spirit-thanks");
    }

    // The ward's victim test: `unit` stands inside the ward (none before the first tide forms it).
    bool InWard(Unit const* unit)
    {
        if (!unit || !Spirit())
            return false;
        return DungeonKit::Distance(PlaneOf(unit), WardCenter()) < LiveRadius(IsHeroicMap(me));
    }

    bool InRepelJump() const
    {
        return me->GetMotionMaster()->GetCurrentMovementGeneratorType() == EFFECT_MOTION_TYPE;
    }

    // LG3: inside the ward he is thrown clear; with his victim inside, he walks to its edge (never a chase into it) and
    // holds there (and answers out of reach). R-1-A M2 / m4: only the jump itself is skipped, so the pass after the
    // landing already judges him; a chase started by a taunt during the hold is stopped again.
    void UpdateWardGuard(bool heroic, uint32 diff)
    {
        _guardCheckMs += diff;
        if (_guardCheckMs < kGuardCheckMs)
            return;
        _guardCheckMs = 0;
        if (!Spirit())
            return;
        if (InRepelJump())
            return;                 // in the air (a Clear would cut the jump)
        Vec2 const center = WardCenter();
        float const radius = LiveRadius(heroic);
        float const dist = DungeonKit::Distance(PlaneOf(me), center);
        if (RepelDue(dist, radius))
        {
            if (_clockMs >= _repelReadyMs && !me->HasUnitState(UNIT_STATE_CASTING))
                Repel(center, radius, "inside");
            return;
        }
        if (_arena.Holding())
        {
            _wardHold = false;      // the arena guard holds him (his victim left the corridor)
            _wardApproach = false;
            return;
        }
        Unit* victim = me->GetVictim();
        float const victimDist = victim ? DungeonKit::Distance(PlaneOf(victim), center) : 0.f;
        if (!victim || victimDist >= radius)
        {
            // His victim is out of the ward: back to the chase.
            MovementGeneratorType const motion = me->GetMotionMaster()->GetCurrentMovementGeneratorType();
            if (victim && (_wardHold || _wardApproach || motion == IDLE_MOTION_TYPE))
                me->GetMotionMaster()->MoveChase(victim);
            if (_wardHold)
                Log("hold-ended");
            _wardHold = false;
            _wardApproach = false;
            return;
        }
        if (HoldAtEdge(dist, victimDist, radius))
        {
            _wardApproach = false;
            MovementGeneratorType const motion = me->GetMotionMaster()->GetCurrentMovementGeneratorType();
            if (!_wardHold || motion == CHASE_MOTION_TYPE)
            {
                me->GetMotionMaster()->Clear(false);
                me->StopMoving();
                if (!_wardHold)
                    Log("hold", Acore::StringFormat("victim={} ward={:.0f}", victim->GetName(), radius));
                _wardHold = true;
            }
            if (!me->HasInArc(float(M_PI) / 4.f, victim))
                me->SetFacingToObject(victim);
            if (!me->IsWithinMeleeRange(victim) && _clockMs >= _nextBoltMs && !me->HasUnitState(UNIT_STATE_CASTING))
            {
                _nextBoltMs = _clockMs + kSearingBoltEveryMs;
                me->CastSpell(victim, SPELL_LG_SEARING_BOLT, true);
                Log("searing-bolt", Acore::StringFormat("victim={}", victim->GetName()));
            }
            return;
        }
        // His victim inside, he farther out than the hold band: walk to the edge on his side.
        _wardHold = false;
        Vec2 const spot = HoldSpot(center, PlaneOf(me), radius);
        bool const walking = me->GetMotionMaster()->GetCurrentMovementGeneratorType() == POINT_MOTION_TYPE;
        if (_wardApproach && walking && DungeonKit::Distance(spot, _holdSpot) < 1.f)
            return;
        _wardApproach = true;
        _holdSpot = spot;
        float z = me->GetPositionZ() + 1.f;
        me->UpdateAllowedPositionZ(spot.x, spot.y, z);
        me->GetMotionMaster()->Clear(false);
        me->GetMotionMaster()->MovePoint(kHoldPointId, spot.x, spot.y, z);
    }

    // The spirit throws him clear of the ward: a jump to a computed spot in the corridor (LoregrainLogic.h). With his
    // victim inside the ward he lands idle (the guard walks him to the edge); otherwise he chases on landing.
    void Repel(Vec2 center, float radius, char const* why)
    {
        Vec2 const land = RepelLanding(center, PlaneOf(me), radius);
        float z = me->GetPositionZ() + 1.f;
        me->UpdateAllowedPositionZ(land.x, land.y, z);
        _repelReadyMs = _clockMs + kRepelCooldownMs;
        _wardHold = false;
        _wardApproach = false;
        Unit* victim = me->GetVictim();
        me->GetMotionMaster()->Clear(false);
        if (victim && DungeonKit::Distance(PlaneOf(victim), center) >= radius)
            me->GetMotionMaster()->MoveChase(victim);
        DungeonKit::JumpTo(me, Position(land.x, land.y, z, me->GetOrientation()), kRepelJumpSpeedXY,
            kRepelJumpMinSpeedZ, SPELL_LG_WARD_REPEL, Spirit());
        Log("repel", Acore::StringFormat("why={} ward={:.0f} land=({:.1f}, {:.1f})", why, radius, land.x, land.y));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LG1 Fire Tide, LG7 Wrath of Ragnaros
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateTide(bool heroic)
    {
        if (_tide.active)
        {
            if (_clockMs >= _tide.landMs)
                TideLands(heroic);
            return;
        }
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;     // a Molten Blast finishes first (the casts wait for a due tide, so this is rare)
        if (_wrathPending)
        {
            if (_clockMs >= TideStartAfter(_clockMs, _lastTideLandMs))
                StartTide(heroic, true);
            return;
        }
        if (_clockMs >= TideStartAfter(_nextTideMs, _lastTideLandMs))
        {
            StartTide(heroic, false);
            _tidePlannedMs = NextPlanned(_tidePlannedMs, kTideEveryMs(heroic), _clockMs);
            _nextTideMs = _tidePlannedMs;
        }
    }

    // The next moment a tide starts (the casts keep clear of it).
    uint64 NextTideStartMs() const
    {
        if (_tide.active)
            return _tide.landMs;
        if (_wrathPending)
            return TideStartAfter(_clockMs, _lastTideLandMs);
        return TideStartAfter(_nextTideMs, _lastTideLandMs);
    }

    void StartTide(bool heroic, bool wrath)
    {
        if (!wrath && _wardFormed)
            MoveSpirit(NextWardSpot(_wardSpot, urand(0, 1) == 1));
        else
            EnsureSpirit();     // the first tide (or a Wrath before it) forms the ward at kWardSpotFirst
        _wardFormed = true;
        Position const at = SpotPosition(_wardSpot);
        Vec2 const center{ at.GetPositionX(), at.GetPositionY() };
        float const radius = LiveRadius(heroic);
        uint32 const fury = _fury;
        float const pct = TidePct(heroic, fury);
        uint32 const warn = wrath ? kWrathWarnMs(heroic) : kTideWarnMs;

        MechanicRef stack = Mechanic::Stack(me, at, radius, Ms(warn));
        stack.Tag(TAG_LG_WARD);
        Track(stack.Handle());
        MechanicRef donut = Mechanic::Donut(me, at, radius, kTideOuterYd, Ms(warn));
        donut.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_FIRE)
            .Spell(wrath ? SPELL_LG_WRATH_HIT : SPELL_LG_TIDE_HIT).Weakened().Tag(TAG_LG_TIDE);
        Track(donut.Handle());

        _tide.active = true;
        _tide.wrath = wrath;
        _tide.landMs = _clockMs + warn;
        _tide.center = center;
        _tide.radius = radius;

        // S2 156: a ward that forms on him throws him clear at once (no cast bar then: he is in the air).
        bool const thrown = RepelDue(DungeonKit::Distance(PlaneOf(me), center), radius);
        if (thrown)
            Repel(center, radius, "ward-formed");
        if (wrath)
        {
            _wrathPending = false;
            SetFury(kFuryAfterWrath);
            Talk(YELL_LG_WRATH);
        }
        else
        {
            Talk(YELL_LG_TIDE);
            Talk(EMOTE_LG_WARD_MOVE);
        }
        if (!thrown)
            me->CastSpell(me, wrath ? (heroic ? SPELL_LG_WRATH_CAST_H : SPELL_LG_WRATH_CAST_N) : SPELL_LG_TIDE_CAST,
                false);
        Log(wrath ? "wrath" : "tide", Acore::StringFormat("heroic={} spot={} ward={:.0f} totems={} cracks={} fury={} "
            "pct={:.1f} warn={}ms", heroic ? 1 : 0, _wardSpot, radius, LivingTotems(), _cracks, fury, pct, warn));
    }

    void TideLands(bool heroic)
    {
        uint32 washed = 0;
        for (auto it = _patches.begin(); it != _patches.end();)
        {
            if (Sheltered(it->at, _tide.center, _tide.radius))
            {
                ++it;
                continue;
            }
            Mechanic::Cancel(me, it->handle);
            DespawnStalker(it->stalker);
            it = _patches.erase(it);
            ++washed;
        }
        if (_tide.wrath && heroic)
        {
            ++_cracks;
            Log("ward-cracked", Acore::StringFormat("cracks={} base={:.0f}", _cracks, WardRadius(true, 0, _cracks)));
        }
        _lastTideLandMs = _clockMs;
        Log(_tide.wrath ? "wrath-landed" : "tide-landed", Acore::StringFormat("washed={} sheltered={}", washed,
            _patches.size()));
        _tide = Tide();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LG6 Fury of Ragnaros
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateFury()
    {
        while (_clockMs >= _nextFuryTickMs)
        {
            _nextFuryTickMs += kFuryTickMs;
            SetFury(FuryAfterSecond(_fury, me->HasAura(SPELL_LG_FIRE_WARD), LivingTotems()));
        }
        if (WrathDue(_fury) && !_wrathPending && !(_tide.active && _tide.wrath))
        {
            _wrathPending = true;
            Log("wrath-due", Acore::StringFormat("fury={}", _fury));
        }
    }

    // The meter and its stacks on him (no stack at 0).
    void SetFury(uint32 value)
    {
        _fury = std::min(value, kFuryMax);
        int32 const shown = int32(DungeonKit::Stacks(me, SPELL_LG_FURY, me->GetGUID()));
        if (shown != int32(_fury))
            DungeonKit::AddStacks(me, SPELL_LG_FURY, int32(_fury) - shown, me, kFuryMax);
    }

    void AddFury(int32 delta, char const* why, std::string const& detail = {})
    {
        uint32 const before = _fury;
        SetFury(FuryAdd(_fury, delta));
        Log(why, Acore::StringFormat("fury={}->{}{}{}", before, _fury, detail.empty() ? "" : " ", detail));
    }

    // LG9: a Fire Ward gone early was broken or purged (-20 Fury); one that ran out was not.
    void UpdateFireWardState()
    {
        bool const up = me->HasAura(SPELL_LG_FIRE_WARD);
        if (_fireWardUp && !up && _clockMs + kFireWardExpirySlackMs < _fireWardEndsMs)
            AddFury(kFuryWardBroken, "fire-ward-broken", Acore::StringFormat("left={}ms",
                _fireWardEndsMs - _clockMs));
        _fireWardUp = up;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LG4 Defiling Totem
    // ----------------------------------------------------------------------------------------------------------------

    uint32 LivingTotems()
    {
        uint32 alive = 0;
        for (auto it = _totems.begin(); it != _totems.end();)
        {
            Creature* totem = ObjectAccessor::GetCreature(*me, *it);
            if (!totem || !totem->IsAlive())
            {
                it = _totems.erase(it);
                continue;
            }
            ++alive;
            ++it;
        }
        return alive;
    }

    void UpdateTotems(bool heroic)
    {
        if (_clockMs < _nextTotemMs)
            return;
        PlantTotem(heroic);
        _totemPlannedMs = NextPlanned(_totemPlannedMs, kTotemEveryMs(heroic), _clockMs);
        _nextTotemMs = _totemPlannedMs;
    }

    // An empty string when planted; otherwise why not.
    std::string PlantTotem(bool heroic)
    {
        uint32 const alive = LivingTotems();
        if (alive >= kTotemCap)
        {
            Log("totem-skipped", Acore::StringFormat("alive={}", alive));
            return "Three Defiling Totems already stand.";
        }
        if (_wardFormed && !EnsureSpirit())
            return "Franclorn's Spirit could not be summoned.";
        Vec2 const center = WardCenter();       // before the first tide: where the ward will form
        float const radius = LiveRadius(heroic);
        Vec2 const spot = TotemSpot(center, radius, frand(0.f, 1.f), frand(0.f, 1.f));
        float z = SpotPosition(_wardSpot).GetPositionZ() + 1.f;
        me->UpdateAllowedPositionZ(spot.x, spot.y, z);
        Creature* totem = me->SummonCreature(NPC_BRD_DEFILING_TOTEM, Position(spot.x, spot.y, z, frand(0.f, 6.28f)),
            TEMPSUMMON_CORPSE_TIMED_DESPAWN, kTotemCorpseMs);
        if (!totem)
        {
            Log("totem-fail");
            return "The Defiling Totem could not be summoned (is creature 300792 declared?).";
        }
        _totems.push_back(totem->GetGUID());
        Log("totem", Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}) alive={} ward={:.0f}", heroic ? 1 : 0, spot.x,
            spot.y, alive + 1, LiveRadius(heroic)));
        return {};
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LG5 Molten Splash
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateSplashes()
    {
        bool const heroic = IsHeroicMap(me);
        for (auto it = _splashes.begin(); it != _splashes.end();)
        {
            if (_clockMs < it->landMs)
            {
                ++it;
                continue;
            }
            PlacePatch(*it);
            it = _splashes.erase(it);
        }
        if (_clockMs < _nextSplashMs)
            return;
        StartSplashes(heroic);
        _splashPlannedMs = NextPlanned(_splashPlannedMs, kSplashEveryMs(heroic), _clockMs);
        _nextSplashMs = _splashPlannedMs;
    }

    // An empty string when fired; otherwise why not.
    std::string StartSplashes(bool heroic)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;       // ruling 88: the tank too
        std::vector<Player*> const picks = DungeonKit::PickPlayers(me, rule, kSplashCount(heroic));
        if (picks.empty())
            return "Nobody in the fight to splash (a GM does not count).";
        float const pct = kSplashPct(heroic);
        std::string who;
        for (Player* player : picks)
        {
            Position const at = player->GetPosition();
            MechanicRef ref = Mechanic::Circle(me, at, kSplashRadiusYd, Ms(kSplashWarnMs));
            ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_FIRE).Spell(SPELL_LG_SPLASH_HIT).Weakened()
                .Tag(TAG_LG_SPLASH);
            Track(ref.Handle());
            Splash splash;
            splash.at = at;
            splash.landMs = _clockMs + kSplashWarnMs;
            splash.heroic = heroic;
            if (Creature* stalker = SummonStalker(at))
            {
                splash.stalker = stalker->GetGUID();
                me->CastSpell(stalker, SPELL_LG_SPLASH_LOB, true);
            }
            _splashes.push_back(splash);
            who += Acore::StringFormat(" {}", player->GetName());
        }
        Log("splash", Acore::StringFormat("heroic={} pct={:.0f} r={:.0f} targets{}", heroic ? 1 : 0, pct,
            kSplashRadiusYd, who));
        return {};
    }

    // The patch where the splash landed: 4 yd, a tick a second from a second after the landing, until a tide washes
    // it (or for the fight, sheltered in the ward). No Weakened: a lingering patch never applies it.
    void PlacePatch(Splash const& splash)
    {
        float const pct = kPatchPct(splash.heroic);
        MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::Circle(splash.at, kPatchRadiusYd),
            Ms(kPatchTickMs));
        ref.Persistent(Ms(kPatchLifeMs), Ms(kPatchTickMs)).Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_FIRE)
            .Spell(SPELL_LG_PATCH_HIT).NoFillTimer().Tag(TAG_LG_PATCH);
        Patch patch;
        patch.handle = ref.Handle();
        patch.at = { splash.at.GetPositionX(), splash.at.GetPositionY() };
        patch.stalker = splash.stalker;
        if (Creature* stalker = splash.stalker ? ObjectAccessor::GetCreature(*me, splash.stalker) : nullptr)
            stalker->CastSpell(stalker, SPELL_LG_PATCH_LOOK, true);
        _patches.push_back(patch);
        Log("patch", Acore::StringFormat("at=({:.1f}, {:.1f}) pct={:.0f}/s patches={}", patch.at.x, patch.at.y, pct,
            _patches.size()));
    }

    // The look's carrier (the shared stalker 300796): nothing when its template is missing (the marker still shows).
    Creature* SummonStalker(Position const& at)
    {
        return me->SummonCreature(NPC_BRD_STALKER, at, TEMPSUMMON_MANUAL_DESPAWN);
    }

    void DespawnStalker(ObjectGuid guid)
    {
        if (Creature* stalker = guid ? ObjectAccessor::GetCreature(*me, guid) : nullptr)
            stalker->DespawnOrUnsummon();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LG8 Molten Blast, LG9 Fire Ward, LG10 Flame Shock
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateCasts(bool heroic)
    {
        if (_clockMs >= _nextFireWardMs)
        {
            CastFireWard();
            _nextFireWardMs += kFireWardEveryMs;
            if (_nextFireWardMs <= _clockMs)
                _nextFireWardMs = _clockMs + kFireWardEveryMs;
        }
        bool const tideClear = _tide.active || !CastBlocksTide(_clockMs, kMoltenBlastCastMs, NextTideStartMs());
        if (_clockMs >= _nextBlastMs && tideClear)
        {
            if (CastMoltenBlast(heroic))
            {
                _blastPlannedMs = NextPlanned(_blastPlannedMs, kMoltenBlastEveryMs, _clockMs);
                _nextBlastMs = _blastPlannedMs;
                Mechanic::NoteNextCastIn(me, SPELL_LG_MOLTEN_BLAST, Ms(_nextBlastMs - _clockMs));
                return;     // casting now
            }
            _nextBlastMs = _clockMs + kRetryMs;
        }
        if (_clockMs >= _nextFlameShockMs)
            _nextFlameShockMs = _clockMs + (CastFlameShock() ? urand(kFlameShockMinMs, kFlameShockMaxMs) : kRetryMs);
    }

    void CastFireWard()
    {
        int32 const absorb = FireWardAbsorb(me->GetMaxHealth());
        me->CastCustomSpell(me, SPELL_LG_FIRE_WARD, &absorb, nullptr, nullptr, true);
        _fireWardEndsMs = _clockMs + kFireWardMs;
        _fireWardUp = me->HasAura(SPELL_LG_FIRE_WARD);
        Log("fire-ward", Acore::StringFormat("absorb={} up={}", absorb, _fireWardUp ? 1 : 0));
    }

    bool CastMoltenBlast(bool heroic)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        rule.maxRange = kMoltenBlastRangeYd;
        rule.requireLos = true;
        Player* target = DungeonKit::PickPlayer(me, rule);
        if (!target)
            return false;
        me->CastSpell(target, SPELL_LG_MOLTEN_BLAST, false);
        Log("molten-blast", Acore::StringFormat("heroic={} target={} pct={:.0f}", heroic ? 1 : 0, target->GetName(),
            kMoltenBlastPct(heroic)));
        return true;
    }

    bool CastFlameShock()
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        rule.maxRange = kFlameShockRangeYd;
        rule.requireLos = true;
        Player* target = DungeonKit::PickPlayer(me, rule);
        if (!target)
            return false;
        me->CastSpell(target, SPELL_LG_FLAME_SHOCK, false);
        Log("flame-shock", Acore::StringFormat("target={}", target->GetName()));
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (S2 "Boss data"): kill order the Defiling Totems; interrupt Molten Blast (a reward on normal, expected
    // on heroic); purge Fire Ward; dispel Flame Shock (a reward). The Stack at each tide is the registry's.
    // ----------------------------------------------------------------------------------------------------------------

    void Describe(bool heroic)
    {
        BossMechanics::Descriptor d;
        d.targets.push_back(BossMechanics::TargetEntry(NPC_BRD_DEFILING_TOTEM, 2, BossMechanics::Who::Dps).AoeOk());
        d.interrupts.emplace_back(NPC_LOREGRAIN, SPELL_LG_MOLTEN_BLAST, heroic ? 3 : 2, Ms(kMoltenBlastEveryMs));
        d.purges.emplace_back(NPC_LOREGRAIN, SPELL_LG_FIRE_WARD, 2);
        d.dispels.emplace_back(SPELL_LG_FLAME_SHOCK, 1);
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brd loregrain` entry points
    // ----------------------------------------------------------------------------------------------------------------

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestTide(bool wrath)
    {
        if (!me->IsEngaged())
            return "Loregrain must be in combat (the tide is his encounter's mechanic).";
        if (_tide.active)
            return "A tide is already coming.";
        if (wrath)
        {
            SetFury(kFuryMax);
            _wrathPending = true;
            _lastTideLandMs = 0;
            return {};
        }
        _nextTideMs = _clockMs;
        _lastTideLandMs = 0;
        return {};
    }

    std::string TestWardMove()
    {
        if (!me->IsEngaged())
            return "Loregrain must be in combat (the spirit is summoned at the first tide).";
        if (_wardFormed)
            MoveSpirit(NextWardSpot(_wardSpot, urand(0, 1) == 1));
        else
            EnsureSpirit();
        _wardFormed = true;
        Log("ward-moved", Acore::StringFormat("spot={} (test)", _wardSpot));
        return {};
    }

    std::string TestTotem()
    {
        if (!me->IsEngaged())
            return "Loregrain must be in combat (the totem joins his fight).";
        return PlantTotem(HeroicMap());
    }

    std::string TestSplash()
    {
        if (!me->IsEngaged())
            return "Loregrain must be in combat (the splash picks among the players in the fight).";
        return StartSplashes(HeroicMap());
    }

    std::string TestFury(uint32 value)
    {
        if (!me->IsEngaged())
            return "Loregrain must be in combat.";
        uint32 const before = _fury;
        SetFury(value);
        Log("fury-set", Acore::StringFormat("fury={}->{} (test)", before, _fury));
        return {};
    }

    std::string TestFireWard()
    {
        if (!me->IsEngaged())
            return "Loregrain must be in combat.";
        CastFireWard();
        return {};
    }

    std::string TestBlast()
    {
        if (!me->IsEngaged())
            return "Loregrain must be in combat.";
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return "He is casting; try again in a moment.";
        return CastMoltenBlast(HeroicMap()) ? std::string() : "Nobody within 30 yd in his sight.";
    }

    std::string TestState()
    {
        bool const heroic = HeroicMap();
        std::string tide = "none";
        if (_tide.active)
            tide = Acore::StringFormat("{} lands in {}ms, ward {:.0f} yd", _tide.wrath ? "wrath" : "tide",
                _tide.landMs - _clockMs, _tide.radius);
        return Acore::StringFormat("clock={}s fury={} wrathPending={} ward: spot={} radius={:.0f} cracks={} spirit={} "
            "| tide=[{}] nextTide={}s | totems={} nextTotem={}s | splashes={} patches={} nextSplash={}s | "
            "fireWard={} nextBlast={}s | hold={} tracked={}", _clockMs / 1000, _fury, _wrathPending ? 1 : 0, _wardSpot,
            LiveRadius(heroic), _cracks, Spirit() ? 1 : 0, tide, _nextTideMs / 1000, LivingTotems(),
            _nextTotemMs / 1000, _splashes.size(), _patches.size(), _nextSplashMs / 1000, _fireWardUp ? 1 : 0,
            _nextBlastMs / 1000, _wardHold ? 1 : 0, _live.size());
    }

private:
    void Log(char const* what, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossKey, what, detail);
    }

    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 96)      // the oldest ones resolved long ago (the patches keep their own handles)
            _live.erase(_live.begin(), _live.begin() + 48);
    }

    // The pull's state: nothing pending, no totem, patch, stalker or aura of the fight left (reset, evade, death, a new
    // pull). `keepSpirit`: the death keeps the spirit for its line.
    void Cleanup(bool keepSpirit)
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        for (Patch const& patch : _patches)
        {
            Mechanic::Cancel(me, patch.handle);
            DespawnStalker(patch.stalker);
        }
        _patches.clear();
        for (Splash const& splash : _splashes)
            DespawnStalker(splash.stalker);
        _splashes.clear();
        for (ObjectGuid const& guid : _totems)
            if (Creature* totem = ObjectAccessor::GetCreature(*me, guid))
                totem->DespawnOrUnsummon();
        _totems.clear();
        if (me->IsAlive())
        {
            _selfInterrupt = true;
            me->InterruptNonMeleeSpells(false);
            _selfInterrupt = false;
        }
        me->RemoveAurasDueToSpell(SPELL_LG_FURY);
        me->RemoveAurasDueToSpell(SPELL_LG_FIRE_WARD);
        if (Map* map = me->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* player = ref.GetSource())
                    player->RemoveAurasDueToSpell(SPELL_LG_FLAME_SHOCK, me->GetGUID());
        if (!keepSpirit)
            DespawnSpirit();
        _tide = Tide();
        _clockMs = 0;
        _fury = 0;
        _cracks = 0;
        _wardSpot = kWardSpotAtPull;
        _wrathPending = false;
        _wardFormed = false;
        _wardHold = false;
        _wardApproach = false;
        _holdSpot = Vec2{};
        _fireWardUp = false;
        _fireWardEndsMs = 0;
        _lastTideLandMs = 0;
        _nextTideMs = _tidePlannedMs = 0;
        _nextTotemMs = _totemPlannedMs = 0;
        _nextSplashMs = _splashPlannedMs = 0;
        _nextBlastMs = _blastPlannedMs = 0;
        _nextFlameShockMs = 0;
        _nextFireWardMs = 0;
        _nextFuryTickMs = 0;
        _nextBoltMs = 0;
        _repelReadyMs = 0;
        _guardCheckMs = 0;
    }

    DungeonKit::ArenaGuard _arena;
    Tide _tide;
    std::vector<Splash> _splashes;
    std::vector<Patch> _patches;
    std::vector<ObjectGuid> _totems;
    std::vector<MechanicHandle> _live;
    ObjectGuid _spirit;
    uint64 _clockMs = 0;                        // ms since the pull: every timer of the fight
    uint64 _nextTideMs = 0;
    uint64 _tidePlannedMs = 0;
    uint64 _lastTideLandMs = 0;
    uint64 _nextTotemMs = 0;
    uint64 _totemPlannedMs = 0;
    uint64 _nextSplashMs = 0;
    uint64 _splashPlannedMs = 0;
    uint64 _nextBlastMs = 0;
    uint64 _blastPlannedMs = 0;
    uint64 _nextFlameShockMs = 0;
    uint64 _nextFireWardMs = 0;
    uint64 _fireWardEndsMs = 0;
    uint64 _nextFuryTickMs = 0;
    uint64 _nextBoltMs = 0;
    uint64 _repelReadyMs = 0;
    uint32 _guardCheckMs = 0;
    uint32 _fury = 0;
    uint32 _cracks = 0;                         // heroic: the Wraths that landed
    uint8 _wardSpot = kWardSpotAtPull;
    Vec2 _holdSpot;                             // the edge spot he walks to (his victim in the ward)
    bool _wrathPending = false;
    bool _wardFormed = false;                   // the first tide formed the ward (or a test did)
    bool _wardHold = false;
    bool _wardApproach = false;                 // walking to _holdSpot
    bool _fireWardUp = false;
    bool _selfInterrupt = false;
};

// The Defiling Totem 300792: rooted where the boss planted it, never attacks, never evades (it stays in the fight
// until it dies or the boss despawns it). Its tooltip aura is cast by the boss script on the summon.
struct npc_brd_defiling_totem : public NullCreatureAI
{
    explicit npc_brd_defiling_totem(Creature* creature) : NullCreatureAI(creature) { }
};

namespace
{
    boss_pyromancer_loregrain_rework* FindLoregrainAI(ChatHandler* handler)
    {
        Creature* boss = BrdTest::FindBoss(handler, NPC_LOREGRAIN);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_pyromancer_loregrain_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Loregrain is not running boss_pyromancer_loregrain_rework (check the "
                "ScriptName).");
        return ai;
    }

    bool Finish(ChatHandler* handler, std::string const& error, char const* what)
    {
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Loregrain: {}.", what);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowBossInfo(handler, NPC_LOREGRAIN, BOSS_LOREGRAIN);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_pyromancer_loregrain_rework* ai = FindLoregrainAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Loregrain: {}", ai->TestState());
        return true;
    }

    bool HandleTide(ChatHandler* handler)
    {
        boss_pyromancer_loregrain_rework* ai = FindLoregrainAI(handler);
        return ai && Finish(handler, ai->TestTide(false), "a Fire Tide starts now (LG1, the ward moves: LG2)");
    }

    bool HandleWrath(ChatHandler* handler)
    {
        boss_pyromancer_loregrain_rework* ai = FindLoregrainAI(handler);
        return ai && Finish(handler, ai->TestTide(true), "Fury set to 100: Wrath of Ragnaros starts now (LG7)");
    }

    bool HandleWard(ChatHandler* handler)
    {
        boss_pyromancer_loregrain_rework* ai = FindLoregrainAI(handler);
        return ai && Finish(handler, ai->TestWardMove(), "the spirit moved to a neighboring spot (LG2, no tide)");
    }

    bool HandleTotem(ChatHandler* handler)
    {
        boss_pyromancer_loregrain_rework* ai = FindLoregrainAI(handler);
        return ai && Finish(handler, ai->TestTotem(), "a Defiling Totem planted in the ward (LG4)");
    }

    bool HandleSplash(ChatHandler* handler)
    {
        boss_pyromancer_loregrain_rework* ai = FindLoregrainAI(handler);
        return ai && Finish(handler, ai->TestSplash(), "Molten Splash now (LG5)");
    }

    bool HandleFury(ChatHandler* handler, uint32 value)
    {
        boss_pyromancer_loregrain_rework* ai = FindLoregrainAI(handler);
        return ai && Finish(handler, ai->TestFury(value), "Fury set (LG6; 100 fires the Wrath)");
    }

    bool HandleFireWard(ChatHandler* handler)
    {
        boss_pyromancer_loregrain_rework* ai = FindLoregrainAI(handler);
        return ai && Finish(handler, ai->TestFireWard(), "Fire Ward cast (LG9)");
    }

    bool HandleBlast(ChatHandler* handler)
    {
        boss_pyromancer_loregrain_rework* ai = FindLoregrainAI(handler);
        return ai && Finish(handler, ai->TestBlast(), "Molten Blast cast (LG8)");
    }

    ChatCommandTable const& BossPyromancerLoregrainTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,    SEC_GAMEMASTER, Console::No },
            { "tide",       HandleTide,     SEC_GAMEMASTER, Console::No },
            { "wrath",      HandleWrath,    SEC_GAMEMASTER, Console::No },
            { "ward",       HandleWard,     SEC_GAMEMASTER, Console::No },
            { "totem",      HandleTotem,    SEC_GAMEMASTER, Console::No },
            { "splash",     HandleSplash,   SEC_GAMEMASTER, Console::No },
            { "fury",       HandleFury,     SEC_GAMEMASTER, Console::No },
            { "fireward",   HandleFireWard, SEC_GAMEMASTER, Console::No },
            { "blast",      HandleBlast,    SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_pyromancer_loregrain_rework()
{
    RegisterDungeonReworkCreatureAI(boss_pyromancer_loregrain_rework, BlackrockDepthsRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brd_defiling_totem, BlackrockDepthsRework::kInstanceScriptName);
    BrdTest::RegisterBoss("loregrain", BossPyromancerLoregrainTestCommands());
}
