/*
 * mod-dungeon-bosses, Blackrock Spire B3: War Master Voone (9237), "the Axe Master". Build spec SP "War Master Voone"
 * (docs/dungeons/blackrock-spire-rework.md, VO1-VO13), handoff sections 3.4 (rows VO), 3.5 (row B3), 3.8. Replaces the
 * stock boss_warmaster_voone (health-gated stances; Throw Axe's stun, Snap Kick, Uppercut and Pummel retired): the
 * creature template is rebound by apps/dbc-tools source/npcs/blackrock_spire/voone.py. Pure rules: VooneLogic.h.
 *
 *   VO1  Charge out        the pull: yell line 0 and a jump (Berserker Charge's look) from his quarters to the troll
 *                          hall's charge spot. His quarters have one gate, 97 yd of floor from the hall, so he holds
 *                          the spot (rooted) until a player is within 12 yd, then the stances start; while he
 *                          holds, whoever damages him from beyond 12 yd gets an axe thrown at them (R-1 ruling 1)
 *   VO2  Stances           Brawler, Thrasher, War Master in turn, 30 s each (heroic 25 s); yell lines 1 to 3
 *   VO3  Axe Throw         Brawler: every 6 s, from 3 s in, one 4 x 30 yd lane toward a random non-tank's spot (2 at
 *                          6+), 2 s warning; the axe sticks at the lane's end
 *   VO4  Axe Fan           Thrasher: every 10 s, three lanes 30 degrees apart toward a random non-tank (2 fans at 6+)
 *   VO5  Axe Rain          War Master: every 8 s, a 4 yd circle under each of 2 random players (4 at 6+), 2 s flight
 *   VO6  Stuck axe cap     over the cap (6, 8 at 6+; heroic 8, 10) the oldest axes fly back one lane each (2 s)
 *   VO7  Recall            at every stance change (emote line 4, a 3 s cast bar): a 4 yd lane from every stuck axe to
 *                          him, stopping 5 yd short of him (ExcludeSourceEnd), resolving when the axes arrive
 *   VO8  Thrash            Brawler, stock 3391
 *   VO9  Cleave, Mortal    Thrasher, stock 15284 (behind a telegraph-only 1.5 s frontal) and 16856
 *        Strike
 *   VO10 Berserking        War Master: +30% attack speed (SPELL_VO_BERSERKING)
 *   VO11 Chained Axes (H)  every stuck axe stays chained to him: a persistent 2 yd line from him to the axe's Chain
 *                          Anchor (live anchors: it sweeps when he moves), 10% once per chain every 2 s, the beam a
 *                          channel the anchor casts on him; the tank holds him in a Park circle
 *   VO12 War Cry (H)       first 15 s, then every 25 s: a 2.5 s interruptible cast. Landed: an early Recall (1.5 s
 *                          warning) and Berserking for 10 s. Interrupt list entry, priority 3
 *   VO13 Reset             evade or wipe: every stuck axe, anchor and lane goes, he walks back to his quarters
 *   Arena                  BlackrockSpireRework::LeashOptions on VooneLogic.h FightArena() (quarters, hall, the walk)
 *
 * Every timer runs on the AI's own clock, never on BossAI's scheduler (a cast bar pauses that one). Every firing logs
 * one INFO line "brs voone <mechanic> ..." (module.dungeonbosses). Axes land and arrive on that clock too (the lane's
 * warning and the registry's resolve are the same duration); the registry owns the hits.
 */

#include "ArenaGuard.h"
#include "BlackrockSpireKit.h"
#include "BlackrockSpireRework.h"
#include "BlackrockSpireTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "GameObject.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "VooneLogic.h"
#include <algorithm>
#include <cmath>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;
using namespace BrsVoone;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "voone";

    // A stuck axe's gameobject is a safety net long past any stance (the AI removes it when the axe is recalled).
    uint32 constexpr kAxeLifeSec = 240;
    // The chain anchor stands a hand above the floor so its beam does not start in the ground.
    float constexpr kAnchorLiftYd = 0.6f;
    // How far a ground probe may differ from the boss's floor before the point is taken as a hole.
    float constexpr kGroundBandYd = 8.f;

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // The test commands' forced mechanics (`.dbtest brs voone ...`; out of combat the GM stands in for the group).
    enum class TestKind : uint8
    {
        Throw,
        Fan,
        Rain,
        Recall,
        WarCry,
        Axe,
        Clear,
    };
}

// War Master Voone 9237
struct boss_warmaster_voone_rework : public BossAI
{
    explicit boss_warmaster_voone_rework(Creature* creature)
        : BossAI(creature, BOSS_VOONE), _arena(FightArena(), LeashOptions(kBossLogName)) { }

    enum class Phase : uint8
    {
        Idle,       // not in a fight
        Charge,     // engaged; the jump goes on the next tick
        Holding,    // in the hall, waiting for the group
        Fighting,   // the stances run
    };

    // The world objects of one stuck axe (a gameobject, the chain anchor, the heroic chain's line).
    struct AxeObjects
    {
        ObjectGuid object;
        ObjectGuid anchor;
        MechanicHandle chain;
        float facing = 0.f;
    };

    // VO1 the hold's answer in flight: `player` is hit when the axe arrives.
    struct HoldThrow
    {
        ObjectGuid player;
        uint64 landMs = 0;
    };

    // A throw whose lane is warning: the axe sticks at `at` when it lands.
    struct PendingAxe
    {
        uint64 landMs = 0;
        Vec2 at;
        float z = 0.f;
        float facing = 0.f;
    };

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
        _players = OnBossPull(me, kBossLogName);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_VOONE;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        Talk(YELL_VOONE_PULL);
        _phase = Phase::Charge;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} players={} at=({:.1f}, {:.1f}, {:.1f})", _heroic ? 1 : 0, _players,
                me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);   // DONE (the instance's rule), the encounter ends
        Cleanup();
        Talk(YELL_VOONE_DEATH);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("killer={}", killer ? killer->GetName() : "none"));
    }

    // The chain anchors are never a fight's combatants: no zone-in, no melee.
    void JustSummoned(Creature* summon) override
    {
        if (summon && summon->GetEntry() == NPC_BRS_CHAIN_ANCHOR)
        {
            summons.Summon(summon);
            summon->SetReactState(REACT_PASSIVE);
            return;
        }
        BossAI::JustSummoned(summon);
    }

    // VO12: a finished War Cry lands (an interrupted one never reaches here).
    void OnSpellCast(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_VO_WAR_CRY)
            WarCryLanded();
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_VO_WAR_CRY)
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "war-cry-interrupted",
                Acore::StringFormat("axes={}", _axes.StuckCount()));
    }

    // VO1 (R-1 ruling 1): while he holds, damage from beyond 12 yd is answered with an axe at the attacker's player.
    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        BossAI::DamageTaken(attacker, damage, type, mask);
        if (_phase == Phase::Holding && attacker && damage)
            AnswerRangedHit(attacker);
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        // Axes land and arrive out of combat too (`.dbtest brs voone throw` on an idle boss).
        UpdateWorld();

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        switch (_phase)
        {
            case Phase::Charge:
                StartCharge();
                return;
            case Phase::Holding:
                UpdateHold();
                return;
            case Phase::Fighting:
                UpdateFight();
                break;
            default:
                return;
        }

        if (!me->HasUnitState(UNIT_STATE_CASTING))
            DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VO1 The charge out, and the hold until the group arrives
    // ----------------------------------------------------------------------------------------------------------------

    void StartCharge()
    {
        Position const dest = ChargeSpot();
        me->GetMotionMaster()->Clear();
        me->StopMoving();
        DungeonKit::JumpTo(me, dest, kChargeSpeedXY, kChargeMinSpeedZ, SPELL_VO_CHARGE, me);
        _phase = Phase::Holding;
        _holdStartMs = _clockMs;
        _rooted = false;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "charge",
            Acore::StringFormat("to=({:.1f}, {:.1f}, {:.1f}) from=({:.1f}, {:.1f})", dest.GetPositionX(),
                dest.GetPositionY(), dest.GetPositionZ(), me->GetPositionX(), me->GetPositionY()));
    }

    // He faces back toward his quarters, the way the group comes from.
    Position ChargeSpot() const
    {
        float const facing = DungeonKit::BearingTo({ kVooneChargeSpot.x, kVooneChargeSpot.y },
            { kVooneSpawn.x, kVooneSpawn.y });
        return Position(kVooneChargeSpot.x, kVooneChargeSpot.y, kVooneChargeSpot.z, facing);
    }

    float NearestPlayerYd() const
    {
        float nearest = 1000.f;
        Map* map = me->FindMap();
        if (!map)
            return nearest;
        for (auto const& ref : map->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (player && player->IsAlive() && !player->IsGameMaster())
                nearest = std::min(nearest, me->GetExactDist2d(player));
        }
        return nearest;
    }

    void UpdateHold()
    {
        uint32 const held = static_cast<uint32>(_clockMs - _holdStartMs);
        if (!_rooted && held >= kChargeLandMs)
        {
            me->SetControlled(true, UNIT_STATE_ROOT);
            _rooted = true;
        }
        if (!HoldReleased(NearestPlayerYd(), held))
            return;
        EndHold(held);
    }

    void EndHold(uint32 heldMs)
    {
        if (_rooted)
            me->SetControlled(false, UNIT_STATE_ROOT);
        _rooted = false;
        if (Unit* victim = me->GetVictim())
            me->GetMotionMaster()->MoveChase(victim);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "hold-end",
            Acore::StringFormat("held={}ms nearest={:.1f}yd", heldMs, NearestPlayerYd()));
        BeginFight();
    }

    // One axe at the player behind `attacker` (a pet, totem or DoT counts as its player; the distance is the damaging
    // unit's), at most one per player every kHoldThrowEveryMs; the hit lands when the axe arrives (UpdateHoldThrows).
    void AnswerRangedHit(Unit* attacker)
    {
        Player* player = attacker->GetCharmerOrOwnerPlayerOrPlayerItself();
        if (!player || !player->IsAlive() || player->IsGameMaster() || !player->IsInMap(me))
            return;
        float const attackerYd = me->GetExactDist2d(attacker);
        if (!HoldThrowAnswers(attackerYd))
            return;
        auto const last = _holdThrowAt.find(player->GetGUID());
        if (!HoldThrowReady(_clockMs, last != _holdThrowAt.end() ? std::optional<uint64>(last->second) : std::nullopt))
            return;
        _holdThrowAt[player->GetGUID()] = _clockMs;
        float const playerYd = me->GetExactDist(player);
        me->CastSpell(player->GetPositionX(), player->GetPositionY(), player->GetPositionZ(), SPELL_VO_AXE_FLIGHT,
            true);
        _holdThrows.push_back({ player->GetGUID(), _clockMs + HoldThrowFlightMs(playerYd) });
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "hold-throw",
            Acore::StringFormat("target={} attacker={} at={:.1f}yd pct={:.0f}", player->GetName(), attacker->GetName(),
                attackerYd, kHoldThrowPct(_heroic)));
    }

    // The hold's axes that arrived: the single-target hit (no Weakened), through the registry.
    void UpdateHoldThrows()
    {
        for (auto it = _holdThrows.begin(); it != _holdThrows.end();)
        {
            if (_clockMs < it->landMs)
            {
                ++it;
                continue;
            }
            DungeonKit::RegistryHitSpec spec;
            spec.pct = kHoldThrowPct(_heroic);
            spec.school = SPELL_SCHOOL_NORMAL;
            spec.spellId = SPELL_VO_AXE_THROW;
            spec.weakened = false;
            spec.tag = TAG_VO_HOLD_THROW;
            Track(DungeonKit::RegistryHit(me, GuidSet{ it->player }, spec));
            it = _holdThrows.erase(it);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VO2 The stances
    // ----------------------------------------------------------------------------------------------------------------

    void BeginFight()
    {
        _phase = Phase::Fighting;
        _stance.Start(_clockMs, _heroic);
        _warCryDueMs = _clockMs + kWarCryFirstMs;
        if (_heroic)
            Mechanic::NoteNextCastIn(me, SPELL_VO_WAR_CRY, Ms(kWarCryFirstMs));
        EnterStance(false);
    }

    void EnterStance(bool recall)
    {
        Stance const stance = _stance.Current();
        Talk(static_cast<uint8>(YELL_VOONE_BRAWLER + static_cast<uint8>(stance)));
        _thrash.Disarm();
        _mortal.Disarm();
        _cleave.Disarm();
        _cleaveResolveMs = 0;
        uint64 const start = _stance.StartMs();
        switch (stance)
        {
            case Stance::Brawler:
                _thrash.Arm(start + kThrashBeat.first);
                break;
            case Stance::Thrasher:
                _mortal.Arm(start + kMortalStrikeBeat.first);
                _cleave.Arm(start + kCleaveBeat.first);
                break;
            case Stance::WarMaster:
                break;
        }
        // VO10: War Master wears Berserking for the stance; the other stances shed the stance's share.
        if (stance == Stance::WarMaster)
            _berserk.SetStance(_stance.EndMs());
        else
            _berserk.ClearStance();
        ApplyBerserk();
        if (_heroic)
            RegisterPark();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "stance",
            Acore::StringFormat("{} length={}ms axes={} change={}", StanceName(stance), _stance.LengthMs(),
                _axes.StuckCount(), _stance.Changes()));
        // VO7: the stance change calls every stuck axe home.
        if (recall)
        {
            std::vector<uint32> const ids = _axes.StuckIds();
            if (!ids.empty())
            {
                DungeonKit::CastBar(me, SPELL_VO_RECALL_BAR, nullptr, EMOTE_VOONE_RECALL);
                StartRecall(ids, kRecallWarnMs, "stance");
            }
        }
    }

    void UpdateFight()
    {
        if (_stance.Advance(_clockMs))
            EnterStance(true);

        if (_stance.ThrowDue(_clockMs))
        {
            Throw(_stance.Current());
            _stance.ThrowFired();
        }
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;

        // VO12: the heroic War Cry, an interruptible cast the descriptor names.
        if (_heroic && _clockMs >= _warCryDueMs && StartWarCry())
            return;

        // VO8 / VO9: the stock casts, on the stock timers from the stance's start.
        if (_thrash.Due(_clockMs))
        {
            DoCastSelf(SPELL_VO_THRASH);
            _thrash.Fired(_clockMs, kThrashBeat.every);
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "thrash");
        }
        if (_mortal.Due(_clockMs))
        {
            DoCastVictim(SPELL_VO_MORTAL_STRIKE);
            _mortal.Fired(_clockMs, kMortalStrikeBeat.every);
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "mortal-strike");
        }
        if (_cleave.Due(_clockMs) && !_cleaveResolveMs)
            StartCleave();
        if (_cleaveResolveMs && _clockMs >= _cleaveResolveMs)
        {
            _cleaveResolveMs = 0;
            DoCastVictim(SPELL_VO_CLEAVE);
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "cleave");
        }
    }

    // VO9: the cone is drawn first (telegraph only: nobody is hit by it), then the stock Cleave goes at his victim.
    void StartCleave()
    {
        MechanicRef ref = Mechanic::Cone(me, me, kCleaveConeDeg, kCleaveConeYd, Ms(kCleaveWarnMs),
            BossMechanics::TankExempt::Yes);
        ref.Tag(TAG_VO_CLEAVE);
        Track(ref.Handle());
        _cleave.Fired(_clockMs, kCleaveBeat.every);
        _cleaveResolveMs = _clockMs + kCleaveWarnMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VO3 / VO4 / VO5 The throws, VO6 the cap
    // ----------------------------------------------------------------------------------------------------------------

    // The players a throw aims at: random non-tanks (the tank when he is alone); the rain takes anyone. Out of combat
    // (a test) the GM that fired it stands in.
    std::vector<Player*> PickTargets(uint32 count, bool nonTank)
    {
        std::vector<Player*> out;
        if (me->IsEngaged())
        {
            DungeonKit::PickRule rule;
            rule.nonTank = nonTank;
            rule.tankIfAlone = true;
            out = DungeonKit::PickPlayers(me, rule, count);
        }
        else if (Player* gm = ObjectAccessor::GetPlayer(*me, _testPlayer))
            out.push_back(gm);
        return out;
    }

    float GroundZ(Vec2 at, float refZ) const
    {
        float const h = me->GetMapHeight(at.x, at.y, refZ + 2.f);
        if (h <= INVALID_HEIGHT || std::fabs(h - refZ) > kGroundBandYd)
            return refZ;
        return h;
    }

    void Throw(Stance stance)
    {
        switch (stance)
        {
            case Stance::Brawler:
                ThrowLanes();
                break;
            case Stance::Thrasher:
                ThrowFans();
                break;
            case Stance::WarMaster:
                ThrowRain();
                break;
        }
    }

    // One lane of a throw: 4 yd wide, up to 30 yd long from him along `facing`, the axe sticking at its end.
    void ThrowLane(float facing, uint32 spellId, uint32 tag, char const* what)
    {
        Vec2 const from = DungeonKit::PlaneOf(me);
        float const z = me->GetPositionZ();
        float const length = LaneLength(_arena.GetArena().RayToEdge(from, z, facing));
        Vec2 const end = DungeonKit::Advance(from, facing, length);
        float const endZ = GroundZ(end, z);

        BossMechanics::Anchor const start(Position(from.x, from.y, z, facing));
        BossMechanics::Anchor const stop(Position(end.x, end.y, endZ, facing));
        MechanicRef ref = Mechanic::Line(me, start, stop, kLaneWidth, Ms(kThrowWarnMs));
        ref.Damage(kAxePct(_heroic)).Weakened().Spell(spellId).Tag(tag);
        Track(ref.Handle());
        me->CastSpell(end.x, end.y, endZ, SPELL_VO_AXE_FLIGHT, true);
        _pending.push_back({ _clockMs + kThrowWarnMs, end, endZ, facing });
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, what,
            Acore::StringFormat("facing={:.2f} length={:.1f} end=({:.1f}, {:.1f}) pct={:.0f}", facing, length, end.x,
                end.y, kAxePct(_heroic)));
    }

    // VO3 Brawler: one lane (two at 6+) toward each pick's spot.
    void ThrowLanes()
    {
        std::vector<Player*> const picks = PickTargets(kThrowLanes.At(_players), true);
        if (picks.empty())
            return;
        MakeRoom(static_cast<uint32>(picks.size()));
        Vec2 const from = DungeonKit::PlaneOf(me);
        for (Player* player : picks)
            ThrowLane(LaneFacing(from, DungeonKit::PlaneOf(player), me->GetOrientation()), SPELL_VO_AXE_THROW,
                TAG_VO_AXE_THROW, "axe-throw");
    }

    // VO4 Thrasher: a fan of three lanes 30 degrees apart toward each pick (one fan, two at 6+).
    void ThrowFans()
    {
        std::vector<Player*> const picks = PickTargets(kFanCount.At(_players), true);
        if (picks.empty())
            return;
        MakeRoom(static_cast<uint32>(picks.size()) * kFanLanes);
        Vec2 const from = DungeonKit::PlaneOf(me);
        for (Player* player : picks)
        {
            float const base = LaneFacing(from, DungeonKit::PlaneOf(player), me->GetOrientation());
            for (float const facing : FanFacings(base))
                ThrowLane(facing, SPELL_VO_AXE_FAN, TAG_VO_AXE_FAN, "axe-fan");
        }
    }

    // VO5 War Master: a 4 yd circle under each pick (two, four at 6+); an axe sticks in each.
    void ThrowRain()
    {
        std::vector<Player*> const picks = PickTargets(kRainCount.At(_players), false);
        if (picks.empty())
            return;
        MakeRoom(static_cast<uint32>(picks.size()));
        for (Player* player : picks)
        {
            Vec2 const at = DungeonKit::PlaneOf(player);
            float const z = player->GetPositionZ();
            MechanicRef ref = Mechanic::Circle(me, BossMechanics::Anchor(Position(at.x, at.y, z, 0.f)), kRainRadius,
                Ms(kThrowWarnMs));
            ref.Damage(kAxePct(_heroic)).Weakened().Spell(SPELL_VO_AXE_RAIN).Tag(TAG_VO_AXE_RAIN);
            Track(ref.Handle());
            me->CastSpell(at.x, at.y, z, SPELL_VO_AXE_FLIGHT, true);
            _pending.push_back({ _clockMs + kThrowWarnMs, at, z, me->GetOrientation() });
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "axe-rain",
                Acore::StringFormat("target={} at=({:.1f}, {:.1f}) pct={:.0f}", player->GetName(), at.x, at.y,
                    kAxePct(_heroic)));
        }
    }

    // VO6: before `incoming` more axes land, the oldest stuck ones fly back so the floor stays at the cap.
    void MakeRoom(uint32 incoming)
    {
        uint32 const cap = StuckCap(_heroic, _players);
        uint32 const n = CapRecalls(_axes.StuckCount(), static_cast<uint32>(_pending.size()), incoming, cap);
        if (!n)
            return;
        std::vector<uint32> ids = _axes.StuckIds();
        ids.resize(std::min<std::size_t>(ids.size(), n));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "cap",
            Acore::StringFormat("cap={} stuck={} pending={} incoming={} recalled={}", cap, _axes.StuckCount(),
                _pending.size(), incoming, ids.size()));
        StartRecall(ids, kCapRecallWarnMs, "cap");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The stuck axes: landing, VO11 the chain, VO7 the recall
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateWorld()
    {
        if (!_holdThrows.empty())
            UpdateHoldThrows();
        if (!_pending.empty())
        {
            std::vector<PendingAxe> due;
            for (auto it = _pending.begin(); it != _pending.end();)
            {
                if (_clockMs >= it->landMs)
                {
                    due.push_back(*it);
                    it = _pending.erase(it);
                }
                else
                    ++it;
            }
            for (PendingAxe const& axe : due)
                LandAxe(axe.at, axe.z, axe.facing);
        }
        if (_axes.Count())
            for (StuckAxe const& axe : _axes.TakeArrived(_clockMs))
                RemoveAxe(axe);
        if (_berserkApplied && !_berserk.Active(_clockMs))
            ApplyBerserk();
    }

    // The axe sticks: its gameobject, the chain anchor (which draws the heroic beam and flies the axe home), and on
    // heroic the chain's persistent line.
    uint32 LandAxe(Vec2 at, float z, float facing)
    {
        uint32 const id = _axes.Add(at, z, _clockMs);
        AxeObjects objects;
        objects.facing = facing;
        if (GameObject* go = me->SummonGameObject(GO_BRS_STUCK_AXE, at.x, at.y, z, facing, 0.f, 0.f,
            std::sin(facing * 0.5f), std::cos(facing * 0.5f), kAxeLifeSec))
            objects.object = go->GetGUID();
        if (Creature* anchor = me->SummonCreature(NPC_BRS_CHAIN_ANCHOR, at.x, at.y, z + kAnchorLiftYd, facing,
            TEMPSUMMON_MANUAL_DESPAWN))
            objects.anchor = anchor->GetGUID();
        _objects[id] = objects;
        if (_heroic)
            StartChain(id);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "axe-stuck",
            Acore::StringFormat("id={} at=({:.1f}, {:.1f}, {:.1f}) stuck={} object={} anchor={} chain={}", id, at.x,
                at.y, z, _axes.StuckCount(), !objects.object.IsEmpty(), !objects.anchor.IsEmpty(),
                _objects[id].chain.IsValid()));
        return id;
    }

    // VO11: the beam (the anchor channels it on him) and the persistent line from him to the anchor. Both ends are
    // live, so the line sweeps when he moves. Registered once per axe; safe to call on an axe that has one.
    void StartChain(uint32 id)
    {
        auto it = _objects.find(id);
        if (it == _objects.end() || it->second.chain.IsValid())
            return;
        Creature* anchor = ObjectAccessor::GetCreature(*me, it->second.anchor);
        if (!anchor)
            return;
        anchor->CastSpell(me, SPELL_VO_CHAINED_AXE, true);
        MechanicRef ref = Mechanic::Line(me, BossMechanics::Anchor(me), BossMechanics::Anchor(anchor), kChainWidth,
            Ms(kChainWarnMs));
        ref.Persistent(Ms(kChainLifeMs), Ms(kChainTickMs)).Damage(kChainPct).Weakened()
            .Spell(SPELL_VO_CHAIN_HIT).Tag(TAG_VO_CHAINS);
        if (kChainExcludeSourceEnd > 0.f)
            ref.ExcludeSourceEnd(kChainExcludeSourceEnd);
        it->second.chain = ref.Handle();
    }

    // VO7: a lane from him to each of `ids`, 4 yd wide, the 5 yd at his side excluded, resolving when the axes arrive
    // (the warning is the flight). Each axe's anchor throws the look home.
    void StartRecall(std::vector<uint32> const& ids, uint32 warnMs, char const* why)
    {
        uint32 sent = 0;
        for (uint32 const id : ids)
        {
            StuckAxe const* axe = _axes.Find(id);
            if (!axe || axe->recalling)
                continue;
            BossMechanics::Anchor const to(Position(axe->at.x, axe->at.y, axe->z, 0.f));
            MechanicRef ref = Mechanic::Line(me, BossMechanics::Anchor(me), to, kRecallWidth, Ms(warnMs));
            ref.Damage(kRecallPct(_heroic)).Weakened().Spell(SPELL_VO_RECALL_HIT).Tag(TAG_VO_RECALL)
                .ExcludeSourceEnd(kRecallExcludeSourceEnd);
            Track(ref.Handle());
            _axes.MarkRecall(id, _clockMs + warnMs);
            auto it = _objects.find(id);
            if (it != _objects.end())
                if (Creature* anchor = ObjectAccessor::GetCreature(*me, it->second.anchor))
                    anchor->CastSpell(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ() + 1.f,
                        SPELL_VO_AXE_RETURN, true);
            ++sent;
        }
        if (sent)
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "recall",
                Acore::StringFormat("why={} axes={} warn={}ms pct={:.0f} exclude={:.0f}", why, sent, warnMs,
                    kRecallPct(_heroic), kRecallExcludeSourceEnd));
    }

    // The axe arrived: its gameobject, anchor and chain go.
    void RemoveAxe(StuckAxe const& axe)
    {
        auto it = _objects.find(axe.id);
        if (it == _objects.end())
            return;
        DropObjects(it->second);
        _objects.erase(it);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "axe-home",
            Acore::StringFormat("id={} stuck={} total={}", axe.id, _axes.StuckCount(), _axes.Count()));
    }

    void DropObjects(AxeObjects& objects)
    {
        if (objects.chain.IsValid())
            Mechanic::Cancel(me, objects.chain);
        objects.chain = MechanicHandle();
        if (Creature* anchor = ObjectAccessor::GetCreature(*me, objects.anchor))
        {
            anchor->InterruptNonMeleeSpells(true);
            anchor->DespawnOrUnsummon();
        }
        objects.anchor.Clear();
        if (GameObject* go = ObjectAccessor::GetGameObject(*me, objects.object))
        {
            if (go->GetOwnerGUID() == me->GetGUID())
                me->RemoveGameObject(go, true);
            else
                go->DespawnOrUnsummon();
        }
        objects.object.Clear();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VO12 War Cry, VO10 Berserking
    // ----------------------------------------------------------------------------------------------------------------

    // False when the cast was refused (he is casting; tried again on the next tick).
    bool StartWarCry()
    {
        if (me->CastSpell(me, SPELL_VO_WAR_CRY, false) != SPELL_CAST_OK)
            return false;
        _warCryDueMs = _clockMs + kWarCryEveryMs;
        Mechanic::NoteNextCastIn(me, SPELL_VO_WAR_CRY, Ms(kWarCryEveryMs));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "war-cry",
            Acore::StringFormat("cast={}ms axes={}", kWarCryCastMs, _axes.StuckCount()));
        return true;
    }

    // The cry landed: every chain yanks taut (the early Recall, 1.5 s warning) and Berserking runs for 10 s.
    void WarCryLanded()
    {
        std::vector<uint32> const ids = _axes.StuckIds();
        if (!ids.empty())
        {
            Talk(EMOTE_VOONE_RECALL);
            StartRecall(ids, kEarlyRecallWarnMs, "war-cry");
        }
        _berserk.SetCry(_clockMs + kWarCryBerserkMs);
        ApplyBerserk();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "war-cry-landed",
            Acore::StringFormat("axes={} berserk={}ms", ids.size(), _berserk.RemainingMs(_clockMs)));
    }

    // Berserking runs while either source does: the aura carries the time left of the later one.
    void ApplyBerserk()
    {
        me->RemoveAurasDueToSpell(SPELL_VO_BERSERKING);
        uint32 const left = _berserk.RemainingMs(_clockMs);
        _berserkApplied = left > 0;
        if (!left)
            return;
        me->CastSpell(me, SPELL_VO_BERSERKING, true);
        DungeonKit::ShortenAura(me, SPELL_VO_BERSERKING, me->GetGUID(), Ms(left));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The bots (descriptor) and the heroic tank hold
    // ----------------------------------------------------------------------------------------------------------------

    // Kill order: the boss only. Interrupt list: War Cry (heroic, expected). Dispel list: none.
    void Describe()
    {
        BossMechanics::Descriptor d;
        if (_heroic)
            d.interrupts.emplace_back(NPC_VOONE, SPELL_VO_WAR_CRY, kWarCryKickPriority, Ms(kWarCryEveryMs));
        Mechanic::Describe(me, std::move(d));
    }

    // VO11 for the bots: the chains sweep when he moves, so the tank holds him where he stands (a hidden tank-only
    // Park circle, renewed at every stance).
    void RegisterPark()
    {
        if (_park.IsValid())
            Mechanic::Cancel(me, _park);
        BossMechanics::Eligibility tankOnly;
        tankOnly.roles = BossMechanics::Role::Tank;
        MechanicRef ref = Mechanic::Circle(me, BossMechanics::Anchor(me->GetPosition()), kParkRadius,
            Ms(_stance.LengthMs()));
        ref.Park(me).NoTelegraph().Eligible(tankOnly).Tag(TAG_VO_PARK);
        _park = ref.Handle();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The fight's state: lanes in flight, cleanup
    // ----------------------------------------------------------------------------------------------------------------

    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 96)      // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 48);
    }

    // VO13: nothing pending, no axe, no lane, no Berserking, not rooted (Reset, evade, death, a new pull).
    void Cleanup()
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        if (_park.IsValid())
            Mechanic::Cancel(me, _park);
        _park = MechanicHandle();
        for (auto& entry : _objects)
            DropObjects(entry.second);
        _objects.clear();
        _axes.Clear();
        _pending.clear();
        _holdThrows.clear();
        _holdThrowAt.clear();
        if (_rooted)
            me->SetControlled(false, UNIT_STATE_ROOT);
        _rooted = false;
        _berserk.Clear();
        _berserkApplied = false;
        me->RemoveAurasDueToSpell(SPELL_VO_BERSERKING);
        _arena.Reset();
        _phase = Phase::Idle;
        _warCryDueMs = StanceClock::kNever;
        _cleaveResolveMs = 0;
        _thrash.Disarm();
        _mortal.Disarm();
        _cleave.Disarm();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brs voone` entry points
    // ----------------------------------------------------------------------------------------------------------------

    // An empty string when fired; otherwise why not. `gm` stands in for the group out of combat.
    std::string TestFire(TestKind kind, Player* gm)
    {
        _testPlayer = gm ? gm->GetGUID() : ObjectGuid::Empty;
        if (!me->IsEngaged() && !_players)
            _players = 5;
        switch (kind)
        {
            case TestKind::Throw:
                ThrowLanes();
                break;
            case TestKind::Fan:
                ThrowFans();
                break;
            case TestKind::Rain:
                ThrowRain();
                break;
            case TestKind::Recall:
            {
                std::vector<uint32> const ids = _axes.StuckIds();
                if (ids.empty())
                    return "No stuck axe (throw some first).";
                DungeonKit::CastBar(me, SPELL_VO_RECALL_BAR, nullptr, EMOTE_VOONE_RECALL);
                StartRecall(ids, kRecallWarnMs, "test");
                break;
            }
            case TestKind::WarCry:
                if (me->HasUnitState(UNIT_STATE_CASTING))
                    return "He is casting; try again in a moment.";
                if (me->CastSpell(me, SPELL_VO_WAR_CRY, false) != SPELL_CAST_OK)
                    return "The War Cry cast was refused.";
                break;
            case TestKind::Axe:
            {
                if (!gm)
                    return "No player.";
                MakeRoom(1);
                LandAxe(DungeonKit::PlaneOf(gm), gm->GetPositionZ(), gm->GetOrientation());
                break;
            }
            case TestKind::Clear:
                Cleanup();
                break;
        }
        return {};
    }

    // `.dbtest brs voone stance <0-2>`: the stance clock jumps to `stance` now (the fight must be running).
    std::string TestStance(uint32 stance)
    {
        if (_phase != Phase::Fighting)
            return "The stances run only in a fight (after the charge and the hold).";
        if (stance >= kStanceCount)
            return "Stance 0 Brawler, 1 Thrasher, 2 War Master.";
        while (static_cast<uint32>(_stance.Current()) != stance)
            _stance.Advance(_stance.EndMs());
        EnterStance(true);
        return {};
    }

    // `.dbtest brs voone charge`: the jump to the hall now (in combat the hold and the stances follow).
    std::string TestCharge()
    {
        if (!me->IsEngaged())
        {
            DungeonKit::JumpTo(me, ChargeSpot(), kChargeSpeedXY, kChargeMinSpeedZ, SPELL_VO_CHARGE, me);
            return {};
        }
        _phase = Phase::Charge;
        return {};
    }

    // `.dbtest brs voone heroic <0|1>`: the heroic form on a normal map (and back) until the next pull; chains start
    // on the axes already stuck.
    void TestHeroic(bool heroic)
    {
        _heroic = heroic;
        if (!_heroic)
            return;
        for (StuckAxe const& axe : _axes.All())
            StartChain(axe.id);
    }

    std::string TestState() const
    {
        char const* phase = _phase == Phase::Idle ? "idle" : (_phase == Phase::Charge ? "charge"
            : (_phase == Phase::Holding ? "holding" : "fighting"));
        uint64 const left = _stance.EndMs() > _clockMs ? (_stance.EndMs() - _clockMs) / 1000 : 0;
        return Acore::StringFormat("phase={} heroic={} players={} clock={}s stance={} (ends in {}s, {} changes) "
            "stuck={} recalling={} pending={} cap={} berserk={}ms", phase, _heroic ? 1 : 0, _players, _clockMs / 1000,
            StanceName(_stance.Current()), left, _stance.Changes(), _axes.StuckCount(),
            _axes.Count() - _axes.StuckCount(), _pending.size(), StuckCap(_heroic, _players),
            _berserk.RemainingMs(_clockMs));
    }

private:
    DungeonKit::ArenaGuard _arena;
    Phase _phase = Phase::Idle;
    bool _heroic = false;
    uint8 _players = 0;             // the flex count held at the pull (5..10)
    uint64 _clockMs = 0;            // the AI's own clock: nothing here waits for a cast bar
    uint64 _holdStartMs = 0;
    bool _rooted = false;
    StanceClock _stance;
    BeatClock _thrash;
    BeatClock _mortal;
    BeatClock _cleave;
    uint64 _cleaveResolveMs = 0;
    uint64 _warCryDueMs = StanceClock::kNever;
    BerserkClock _berserk;
    bool _berserkApplied = false;
    AxeBook _axes;
    std::unordered_map<uint32, AxeObjects> _objects;
    std::vector<PendingAxe> _pending;
    std::vector<HoldThrow> _holdThrows;
    std::unordered_map<ObjectGuid, uint64> _holdThrowAt;   // VO1 the hold: each player's last axe
    std::vector<MechanicHandle> _live;
    MechanicHandle _park;
    ObjectGuid _testPlayer;
};

namespace
{
    boss_warmaster_voone_rework* VooneAI(ChatHandler* handler)
    {
        Creature* boss = BrsTest::FindBoss(handler, NPC_VOONE);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_warmaster_voone_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("War Master Voone does not run the reworked script.");
        return ai;
    }

    bool Reply(ChatHandler* handler, std::string const& error, char const* ok)
    {
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->SendSysMessage(ok);
        return true;
    }

    bool Fire(ChatHandler* handler, TestKind kind, char const* ok)
    {
        auto* ai = VooneAI(handler);
        if (!ai)
            return false;
        return Reply(handler, ai->TestFire(kind, handler->GetPlayer()), ok);
    }

    // `.dbtest brs voone info`
    bool HandleInfo(ChatHandler* handler)
    {
        return BrsTest::ShowBossInfo(handler, NPC_VOONE, BOSS_VOONE);
    }

    // `.dbtest brs voone state`
    bool HandleState(ChatHandler* handler)
    {
        auto* ai = VooneAI(handler);
        if (!ai)
            return false;
        handler->SendSysMessage(ai->TestState());
        return true;
    }

    // `.dbtest brs voone throw`: VO3's lane(s) at the group (out of combat: at you).
    bool HandleThrow(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Throw, "Axe Throw: a lane toward a random non-tank (you, out of combat).");
    }

    // `.dbtest brs voone fan`: VO4's fan(s).
    bool HandleFan(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Fan, "Axe Fan: three lanes toward a random non-tank (you, out of combat).");
    }

    // `.dbtest brs voone rain`: VO5's circles.
    bool HandleRain(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Rain, "Axe Rain: a circle under each pick (you, out of combat).");
    }

    // `.dbtest brs voone recall`: VO7 now, every stuck axe, the 3 s warning.
    bool HandleRecall(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Recall, "Recall: every stuck axe flies home (3 s warning).");
    }

    // `.dbtest brs voone warcry`: VO12's 2.5 s cast now (heroic: the interrupt list names it).
    bool HandleWarCry(ChatHandler* handler)
    {
        return Fire(handler, TestKind::WarCry, "War Cry: the cast started (landed: an early Recall and Berserking).");
    }

    // `.dbtest brs voone axe`: an axe sticks at your feet now (the cap makes room first).
    bool HandleAxe(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Axe, "A stuck axe lands at your feet.");
    }

    // `.dbtest brs voone clear`: every axe, anchor and lane goes.
    bool HandleClear(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Clear, "Cleared: no axe, anchor or lane left.");
    }

    // `.dbtest brs voone stance <0|1|2>`
    bool HandleStance(ChatHandler* handler, uint32 stance)
    {
        auto* ai = VooneAI(handler);
        if (!ai)
            return false;
        return Reply(handler, ai->TestStance(stance), "Stance changed (the Recall of the stuck axes started).");
    }

    // `.dbtest brs voone charge`
    bool HandleCharge(ChatHandler* handler)
    {
        auto* ai = VooneAI(handler);
        if (!ai)
            return false;
        return Reply(handler, ai->TestCharge(), "Charge: he jumps to the hall's charge spot.");
    }

    // `.dbtest brs voone heroic [0|1]`
    bool HandleHeroic(ChatHandler* handler, Optional<uint32> on)
    {
        auto* ai = VooneAI(handler);
        if (!ai)
            return false;
        ai->TestHeroic(!on || *on != 0);
        handler->SendSysMessage("The heroic form is set until the next pull.");
        return true;
    }

    ChatCommandTable const& VooneTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",   HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",  HandleState,    SEC_GAMEMASTER, Console::No },
            { "throw",  HandleThrow,    SEC_GAMEMASTER, Console::No },
            { "fan",    HandleFan,      SEC_GAMEMASTER, Console::No },
            { "rain",   HandleRain,     SEC_GAMEMASTER, Console::No },
            { "recall", HandleRecall,   SEC_GAMEMASTER, Console::No },
            { "warcry", HandleWarCry,   SEC_GAMEMASTER, Console::No },
            { "axe",    HandleAxe,      SEC_GAMEMASTER, Console::No },
            { "clear",  HandleClear,    SEC_GAMEMASTER, Console::No },
            { "stance", HandleStance,   SEC_GAMEMASTER, Console::No },
            { "charge", HandleCharge,   SEC_GAMEMASTER, Console::No },
            { "heroic", HandleHeroic,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_warmaster_voone_rework()
{
    RegisterDungeonReworkCreatureAI(boss_warmaster_voone_rework, BlackrockSpireRework::kInstanceScriptName);
    BrsTest::RegisterBoss("voone", VooneTestCommands());
}
