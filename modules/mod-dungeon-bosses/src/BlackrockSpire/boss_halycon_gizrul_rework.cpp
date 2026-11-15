/*
 * mod-dungeon-bosses, Blackrock Spire B7: Halycon (10220) and Gizrul the Slavener (10268), one encounter (ruling 4),
 * "the pair at once" (ruling 44). Build spec SP "Halycon and Gizrul" (docs/dungeons/blackrock-spire-rework.md,
 * HG1-HG11; rulings 45-46, tank swap at 10 rulings 62-64), handoff sections 3.4 (rows HG), 3.5 (row B7), 3.8 (NM 7).
 * Replaces the stock boss_halycon (Rend 13738 and the one-off Thrash 3391 retired; Gizrul summoned on her death) and
 * Gizrul's SmartAI (Fatal Bite, Infected Bite, Frenzy retired; WP-S0's SQL rev drops the rows). Both entries run this
 * one script, bound by apps/dbc-tools source/npcs/blackrock_spire/halycon_gizrul.py. Pure rules: HalyconGizrulLogic.h.
 *
 *   HG1  The pair         the pull: Halycon howls (emote 1) and summons Gizrul at his stock spawn on the level above;
 *                         sprinting (+100% speed, 10 s), not attackable, he runs path 402450 to the den's mouth (about
 *                         81 yd, 4 s) and engages on her tank
 *   HG2  Savage Charge    Gizrul, on arrival then every 18 s: the farthest non-tank (two at 6+, 1 s apart), a 3 s paw
 *                         (cast bar, emote 0), a 5 x 30 yd line (or to the wall) through the target's spot, then the
 *                         dash along it; 30% / 40% + Weakened + a Rabies stack
 *   HG3  Pack Pounce      Halycon: an 8 yd circle at the line's end, drawn with the line (SP's reading); she leaps
 *                         1.5 s after the charge ends; 25% / 30% + Weakened. Normal: the first line only; heroic every
 *                         line
 *   HG4  Thrash           Halycon, 10 s then every 20 s: a 2 s crouch (cast bar, emote 2), an 8 yd ring on her, tank
 *                         exempt; 25% / 30% + Weakened
 *   HG5  Rabid Froth      Gizrul, 20 s from the pull then every 20 s: a 2 s head shake (cast bar, emote 1), a 10 yd
 *                         ring on him, tank exempt; 20% / 25% Nature + Weakened + a Rabies stack
 *   HG6  Rabies           the Disease: Gizrul's bite every 8 s (from 8 s after he arrives), the charge and the froth
 *                         add a stack; 30 s, up to 5; 1% / 1.5% per stack every 3 s (1.5 s under Pack Fury); a
 *                         dispel reward
 *   HG7  Call of the Pack Halycon, 15 s then every 25 s: a 3 s interruptible howl (emote 3). Landed: Pack Fury on both
 *                         wolves (+25% damage, 15 s, every timer above runs 1.5 times as fast); heroic: a permanent
 *                         Bloodied Pack stack on both (+10% damage, up to 5)
 *   HG8  Grief            the first death: the survivor gains Grief (+25% / 40% damage) and the partner's half: a lone
 *                         Gizrul howls Call of the Pack himself (emote 3), a lone Halycon charges herself (emote 4) and
 *                         Thrashes where the charge ends instead of pouncing
 *   HG9  Rabid Trail (H)  each charge line stays soaked for 12 s (a persistent 5 yd line, a Rabies stack every 2 s
 *                         inside, Weakened once per trail per player), with the Deadmines goo puddles every 8 yd
 *   HG10 Reset            evade or wipe: Gizrul despawns (alive or dead), a Halycon who fell first respawns, both boss
 *                         states go back to NOT_STARTED and both encounter credits are cleared; trails and Bloodied
 *                         Pack go with them
 *   HG11 Torn Hide        10 players only: each wolf's bite every 6 s (4 s under Pack Fury) stacks Torn Hide on its own
 *                         target, +10% damage taken from that wolf per stack; 15 s (10 s under Pack Fury, R-1 ruling
 *                         2: it falls off before the other tank needs to take the wolf back); it holds on the wolf's
 *                         target while the wolf cannot bite (away, casting); the bots trade wolves at 3 stacks
 *                         (TauntSwapEntry per wolf, the assist tank picks up Gizrul)
 *
 * The encounter. Each wolf is a BossAI on its own slot (Halycon BOSS_HALYCON 7, Gizrul BOSS_GIZRUL 6) and owns its own
 * registry encounter (its mechanics, bound to its boss state). The descriptor (kill order, interrupt, dispel, the taunt
 * swap) lives on Halycon's encounter with Gizrul tracked into it (Mechanic::TrackUnit); after her death it moves to
 * Gizrul's. Gizrul is Halycon's summon outside BossAI's summon list (her death does not despawn him). The first wolf to
 * fall does not set its boss state DONE (a wipe brings the pair back); the second one's death sets both DONE, so
 * DungeonEncounter 273 and 274 both stand when the pair is dead (section 7 #17: two rows kept). The engine credits each
 * row at that wolf's own kill; a wipe after the first death clears that credit again, and every pull clears a credit
 * whose boss state is not DONE.
 *
 * Every timer runs on the AI's own clock, never on BossAI's scheduler (a cast bar pauses that one). Every firing logs
 * one INFO line "brs <halycon|gizrul> <mechanic> ..." (module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "BlackrockSpireKit.h"
#include "BlackrockSpireRework.h"
#include "BlackrockSpireTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DBCStructure.h"
#include "DungeonKit.h"
#include "DungeonKitFlex.h"
#include "HalyconGizrulLogic.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <array>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;
using namespace BrsHalyconGizrul;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kHalyconKey = "halycon";
    char const* const kGizrulKey = "gizrul";

    // How far a ground probe may differ from the wolf's floor before the point is taken as a hole.
    float constexpr kGroundBandYd = 6.f;
    float constexpr kDenFloorZ = 64.41f;            // the den's mouth [db: waypoint_data 402450 point 6]
    float constexpr kChargeMinSpeed = 10.f;         // yd/s: a short line still takes about kChargeTravelMs
    float constexpr kLeapMinSpeedXY = 4.f;
    float constexpr kLeapMinSpeedZ = 6.f;
    uint32 constexpr kChargePointId = 1;            // MoveCharge id

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // Halycon writes BOSS_HALYCON, Gizrul BOSS_GIZRUL (one script on both entries).
    uint32 BossStateOf(uint32 entry)
    {
        return entry == NPC_GIZRUL ? BOSS_GIZRUL : BOSS_HALYCON;
    }

    uint32 BossStateOf(Creature const* creature)
    {
        return BossStateOf(creature->GetEntry());
    }

    bool HasFury(Unit const* unit)
    {
        return unit && unit->HasAura(SPELL_HG_PACK_FURY);
    }

    // The bit of the DungeonEncounter row credited by killing `entry` on `map` (0: none).
    uint32 EncounterBitOf(Map const* map, uint32 entry)
    {
        if (!map)
            return 0;
        DungeonEncounterList const* list = sObjectMgr->GetDungeonEncounterList(map->GetId(), map->GetDifficulty());
        if (!list)
            return 0;
        for (DungeonEncounter const* encounter : *list)
            if (encounter && encounter->creditType == ENCOUNTER_CREDIT_KILL_CREATURE
                && encounter->creditEntry == entry && encounter->dbcEntry)
                return 1u << encounter->dbcEntry->encounterIndex;
        return 0;
    }

    // HG10: a wolf killed in an attempt that failed must not keep its DungeonEncounter credit.
    void ClearEncounterCredit(InstanceScript* instance, uint32 entry, char const* why)
    {
        if (!instance)
            return;
        uint32 const bit = EncounterBitOf(instance->instance, entry);
        uint32 const mask = instance->GetCompletedEncounterMask();
        if (!bit || !(mask & bit))
            return;
        instance->SetCompletedEncountersMask(mask & ~bit, true);
        DungeonKit::LogMechanic(kLogDungeon, entry == NPC_GIZRUL ? kGizrulKey : kHalyconKey, "credit-cleared",
            Acore::StringFormat("why={} bit=0x{:x} mask=0x{:x}", why, bit, mask & ~bit));
    }

    // The test commands' forced mechanics (`.dbtest brs halycon ...`; out of combat the GM stands in for the group).
    enum class TestKind : uint8
    {
        Charge,
        Thrash,
        Froth,
        Call,
        Trail,
        TornHide,
        Clear,
    };
}

// Halycon 10220 and Gizrul the Slavener 10268
struct boss_halycon_gizrul_rework : public BossAI
{
    explicit boss_halycon_gizrul_rework(Creature* creature)
        : BossAI(creature, BossStateOf(creature)), _bossState(BossStateOf(creature)),
          _gizrul(creature->GetEntry() == NPC_GIZRUL),
          _arena(HalyconGizrulArena(), LeashOptions(creature->GetEntry() == NPC_GIZRUL ? kGizrulKey : kHalyconKey))
    { }

    enum class Phase : uint8
    {
        Idle,       // not in a fight
        Running,    // Gizrul: the run in from his level (not attackable)
        Fighting,
    };

    // One Savage Charge in progress (the charger's own: Gizrul, or a lone Halycon).
    struct ChargeRun
    {
        bool active = false;
        uint64 startMs = 0;
        uint32 lines = 0;
        float z = 0.f;
        std::array<ObjectGuid, 2> targets{};
        std::array<Vec2, 2> from{};
        std::array<Vec2, 2> end{};
        std::array<bool, 2> registered{ { false, false } };
        std::array<bool, 2> dashed{ { false, false } };
        std::array<bool, 2> pounce{ { false, false } };
        bool thrashAtEnd = false;       // a lone Halycon: Thrash where it ends (HG8)
        bool thrashed = false;
    };

    // One of Halycon's pounces (HG3): the circle is registered; she takes off at leapMs and lands at landMs.
    struct PendingPounce
    {
        uint64 leapMs = 0;
        uint64 landMs = 0;
        Position at;
        MechanicHandle circle;
        bool leapt = false;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Engine hooks
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();
        Cleanup();
        if (!_gizrul)
            DespawnGizrul("reset");
    }

    void JustEngagedWith(Unit* who) override
    {
        if (_gizrul && _phase == Phase::Running)
            return;     // not attackable on his run: only Arrive engages him
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded
        StartFight();
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        if (_evading)
            return;
        _evading = true;
        ResetPair("evade");
        if (_despawned)
        {
            // Gizrul: the reset chain (Halycon's evade or Reset) already despawned him (R-1-B m4).
            _evading = false;
            return;
        }
        BossAI::EnterEvadeMode(why);
        _evading = false;
        if (_gizrul)
            me->DespawnOrUnsummon();
    }

    void JustDied(Unit* killer) override
    {
        // The partner still fights (or Gizrul is still on his run in): this is the first death.
        Creature* partner = Partner();
        auto* partnerAI = AIOf(partner);
        bool const partnerUp = partner && partner->IsAlive()
            && (partner->IsEngaged() || (partnerAI && partnerAI->_phase == Phase::Running));
        if (partnerUp)
            FirstDeath(partner);
        else
            PairDown(killer);
    }

    void JustSummoned(Creature* summon) override
    {
        // Gizrul is the pair's other half, never a BossAI summon (her death must not despawn him).
        if (summon && summon->GetEntry() == NPC_GIZRUL)
        {
            _partner = summon->GetGUID();
            return;
        }
        BossAI::JustSummoned(summon);
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (_gizrul && _phase == Phase::Running && type == WAYPOINT_MOTION_TYPE)
            _runNode = std::max(_runNode, id + 1);
    }

    // HG7: a finished howl lands (an interrupted one never reaches here).
    void OnSpellCast(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_HG_CALL_OF_THE_PACK)
            CallLanded();
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_HG_CALL_OF_THE_PACK)
            Log("call-interrupted");
    }

    // HG11: every hit of this wolf on a target carrying its Torn Hide is 10% harder per stack.
    void DamageDealt(Unit* victim, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*mask*/) override
    {
        if (!victim || !damage)
            return;
        if (uint32 const stacks = DungeonKit::Stacks(victim, SPELL_HG_TORN_HIDE, me->GetGUID()))
            damage = TornHideDamage(damage, stacks);
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        UpdateLooks();
        if (_phase == Phase::Running)
        {
            UpdateRun();
            return;
        }
        // Pounces and charges also run out of combat (`.dbtest` on an idle boss).
        UpdatePounces();
        UpdateCharge();

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off the arena, or nobody on it for 10 s: evading
        if (_phase != Phase::Fighting)
            return;

        bool const fury = HasFury(me);
        AdvanceTimers(diff, fury);
        RunTimers(fury);
        if (_tornHide.Armed())
            HoldTornHide(diff);

        if (!Busy())
            DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HG1 The pull and Gizrul's run in
    // ----------------------------------------------------------------------------------------------------------------

    void StartFight()
    {
        _heroic = IsHeroicMap(me);
        _players = OnBossPull(me, Key());
        BossMechanics::EncounterOptions options;
        options.bossStateId = _bossState;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);
        _phase = Phase::Fighting;
        _lone = false;
        bool const tankSwap = DungeonKit::Flex::TankSwapOn(_players);
        if (tankSwap)
            _tornHide.Arm(kTornHideBiteFirstMs);

        if (!_gizrul)
        {
            // Stale credits from an attempt that ended badly (a restart mid-fight) go first.
            for (uint32 const entry : { static_cast<uint32>(NPC_HALYCON), static_cast<uint32>(NPC_GIZRUL) })
                if (instance && instance->GetBossState(BossStateOf(entry)) != DONE)
                    ClearEncounterCredit(instance, entry, "pull");
            Talk(EMOTE_HALYCON_PULL);
            _thrash.Arm(kThrashFirstMs);
            _call.Arm(kCallFirstMs);
            Mechanic::NoteNextCastIn(me, SPELL_HG_CALL_OF_THE_PACK, Ms(kCallFirstMs));
            SummonGizrul();
            Describe();
            Log("engage", Acore::StringFormat("heroic={} players={} tankswap={}", _heroic ? 1 : 0, _players,
                tankSwap ? 1 : 0));
            return;
        }

        // Gizrul: he opens with a Savage Charge; the froth keeps its place 20 s after the pull (his clock started at
        // the pull, when she summoned him).
        _charge.Arm(0);
        uint64 const sincePull = _clockMs;
        _froth.Arm(sincePull + kFrothMinFirstMs < kFrothFirstMs ? static_cast<uint32>(kFrothFirstMs - sincePull)
            : kFrothMinFirstMs);
        _rabiesBite.Arm(kRabiesBiteFirstMs);
        Creature* halycon = Partner();
        if (halycon && halycon->IsAlive() && halycon->IsEngaged())
        {
            Mechanic::TrackUnit(halycon, me);
            if (auto* ai = AIOf(halycon))
                ai->Describe();
        }
        else
            BecomeLone(halycon ? AIOf(halycon) : nullptr);
        Log("engage", Acore::StringFormat("heroic={} players={} tankswap={} since-pull={}ms lone={}", _heroic ? 1 : 0,
            _players, tankSwap ? 1 : 0, sincePull, _lone ? 1 : 0));
    }

    float SpawnFacing() const
    {
        return DungeonKit::BearingTo(kGizrulSpawn.XY(), Vec2{ -166.797f, -381.557f });
    }

    // Halycon summons him at his stock spawn; he runs in at once.
    void SummonGizrul()
    {
        DespawnGizrul("new pull");
        Creature* gizrul = me->SummonCreature(NPC_GIZRUL, kGizrulSpawn.x, kGizrulSpawn.y, kGizrulSpawn.z,
            SpawnFacing(), TEMPSUMMON_MANUAL_DESPAWN);
        if (!gizrul)
        {
            Log("gizrul-summon-failed");
            return;
        }
        _partner = gizrul->GetGUID();
        if (auto* ai = AIOf(gizrul))
            ai->StartRun(me);
    }

    void StartRun(Creature* halycon)
    {
        _partner = halycon ? halycon->GetGUID() : ObjectGuid::Empty;
        _phase = Phase::Running;
        _runStartMs = _clockMs;
        _runNode = 0;
        me->SetReactState(REACT_PASSIVE);
        me->SetUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
        me->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->CastSpell(me, SPELL_HG_SPRINT, true);
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MoveWaypoint(kGizrulPath, false);
        Log("run", Acore::StringFormat("from=({:.1f}, {:.1f}, {:.1f}) path={}", me->GetPositionX(),
            me->GetPositionY(), me->GetPositionZ(), kGizrulPath));
    }

    void UpdateRun()
    {
        uint64 const ran = _clockMs - _runStartMs;
        bool const there = me->GetExactDist2d(kHalyconDenMouth.x, kHalyconDenMouth.y) <= kArriveYd;
        if (!there && ran < kGizrulRunTimeoutMs)
            return;
        Arrive(there ? "path" : "timeout", static_cast<uint32>(ran));
    }

    // At the den's mouth: he joins the fight on Halycon's tank (or alone, if she already fell).
    void Arrive(char const* how, uint32 ranMs)
    {
        if (!me->IsWithinDist2d(kHalyconDenMouth.x, kHalyconDenMouth.y, kArriveYd + 1.f))
            me->NearTeleportTo(kHalyconDenMouth.x, kHalyconDenMouth.y, kDenFloorZ, me->GetOrientation());
        _phase = Phase::Idle;
        me->RemoveUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
        me->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->SetReactState(REACT_AGGRESSIVE);
        me->GetMotionMaster()->Clear();
        Log("arrive", Acore::StringFormat("how={} ran={}ms node={} at=({:.1f}, {:.1f})", how, ranMs, _runNode,
            me->GetPositionX(), me->GetPositionY()));

        Creature* halycon = Partner();
        if (halycon && halycon->IsAlive() && !halycon->IsEngaged())
        {
            Log("arrive-no-fight");
            me->DespawnOrUnsummon();
            return;
        }
        if (halycon && halycon->IsAlive())
            if (Unit* tank = halycon->GetVictim())
            {
                me->GetThreatMgr().AddThreat(tank, 1.f);
                AttackStart(tank);
            }
        DoZoneInCombat();
        // Engaged during the run (JustEngagedWith returned early then): the engine does not call it again, so the
        // fight starts here (R-1-B n4).
        if (me->IsEngaged() && _phase != Phase::Fighting)
            if (Unit* victim = me->GetVictim())
                JustEngagedWith(victim);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The pair: deaths, Grief, the descriptor
    // ----------------------------------------------------------------------------------------------------------------

    // HG8: the first wolf falls. Its boss state stays IN_PROGRESS (a wipe brings the pair back).
    void FirstDeath(Creature* partner)
    {
        Talk(_gizrul ? uint8(EMOTE_GIZRUL_GRIEF) : uint8(EMOTE_HALYCON_GRIEF));
        HandOver(partner);
        Cleanup();
        events.Reset();
        Log("death", Acore::StringFormat("first=1 partner-health={:.0f}%", partner->GetHealthPct()));
    }

    // The second wolf falls: the encounter is over, both boss states DONE (both DungeonEncounter rows stand: each
    // was credited at its own kill).
    void PairDown(Unit* killer)
    {
        BossAI::JustDied(killer);   // this wolf DONE, the encounter ends
        if (instance)
        {
            uint32 const other = _gizrul ? BOSS_HALYCON : BOSS_GIZRUL;
            if (instance->GetBossState(other) != DONE)
                instance->SetBossState(other, DONE);
            instance->SaveToDB();
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_HG_RABIES);    // no Disease ticks past the fight
        }
        Cleanup();
        Log("death", Acore::StringFormat("first=0 killer={}", killer ? killer->GetName() : "none"));
    }

    // The partner takes over this wolf's half (its timer as it stood) and grieves.
    void HandOver(Creature* partner)
    {
        auto* ai = AIOf(partner);
        if (!ai || ai->_phase == Phase::Running)
            return;     // Gizrul still on his run: he grieves when he arrives (StartFight)
        // Gizrul's charge goes to a lone Halycon, Halycon's howl to a lone Gizrul (fight time left, at least 3 s).
        std::int64_t const left = _gizrul ? _charge.Left() : _call.Left();
        ai->BecomeLone(this, left == Cooldown::kNever ? 0 : static_cast<uint32>(left));
    }

    void BecomeLone(boss_halycon_gizrul_rework* fallen, uint32 adoptMs = 0)
    {
        if (_lone)
            return;
        _lone = true;
        uint32 const at = std::max<uint32>(adoptMs, 3000);
        if (_gizrul)
        {
            _call.Arm(at);
            Mechanic::NoteNextCastIn(me, SPELL_HG_CALL_OF_THE_PACK, Ms(at));
        }
        else
        {
            _charge.Arm(at);
            CancelPounces();
        }
        CastSpellExtraArgs args(true);
        args.AddSpellBP0(kGriefDamagePct(_heroic));
        me->CastSpell(me, SPELL_HG_GRIEF, args);
        Describe();
        Log("grief", Acore::StringFormat("damage={}% adopt={}ms fallen={}", kGriefDamagePct(_heroic), at,
            fallen ? 1 : 0));
    }

    // Kill order: the wolf with more health left, within 5% (KillTogether both ways). Interrupt list: Call of the Pack
    // (Halycon; Gizrul under Grief), priority 3 heroic (expected), 2 normal (a reward). Dispel list: Rabies (a reward).
    // Taunt swap (10 players): a TauntSwapEntry per living wolf at 3 Torn Hide stacks (per caster: each wolf counts
    // its own), and the assist tank picks up Gizrul.
    void Describe()
    {
        BossMechanics::Descriptor d;
        Creature* partner = Partner();
        bool const pair = !_lone && partner && partner->IsAlive() && partner->IsEngaged();
        uint8 const priority = _heroic ? kCallKickPriorityHeroic : kCallKickPriorityNormal;
        if (!_gizrul || _lone)
            d.interrupts.emplace_back(me->GetEntry(), SPELL_HG_CALL_OF_THE_PACK, priority, Ms(kCallEveryMs));
        d.dispels.emplace_back(SPELL_HG_RABIES, 1);
        if (pair)
        {
            d.targets.push_back(BossMechanics::TargetEntry(NPC_HALYCON, 2).KillTogether(NPC_GIZRUL, kKillTogetherPct));
            d.targets.push_back(BossMechanics::TargetEntry(NPC_GIZRUL, 2).KillTogether(NPC_HALYCON, kKillTogetherPct));
        }
        if (DungeonKit::Flex::TankSwapOn(_players))
        {
            d.tauntSwaps.emplace_back(me->GetEntry(), SPELL_HG_TORN_HIDE, kTornHideSwapAt);
            if (pair)
            {
                d.tauntSwaps.emplace_back(partner->GetEntry(), SPELL_HG_TORN_HIDE, kTornHideSwapAt);
                d.targets.emplace_back(NPC_GIZRUL, 1, BossMechanics::Who::AssistTank);
            }
        }
        Mechanic::Describe(me, std::move(d));
    }

    // HG10: the attempt is over. Both reset: Gizrul despawns (alive or dead), a Halycon who fell first respawns, the
    // boss states go back and a credit taken this attempt is cleared.
    void ResetPair(char const* why)
    {
        Cleanup();
        Creature* partner = Partner();
        if (_gizrul)
        {
            if (partner && partner->IsAlive() && partner->IsEngaged() && partner->IsAIEnabled && partner->AI())
                partner->AI()->EnterEvadeMode(CreatureAI::EVADE_REASON_OTHER);
            else if (partner && !partner->IsAlive())
            {
                partner->Respawn(true);
                Log("halycon-respawn", why);
            }
            if (instance && instance->GetBossState(BOSS_HALYCON) != DONE)
            {
                instance->SetBossState(BOSS_HALYCON, NOT_STARTED);
                ClearEncounterCredit(instance, NPC_HALYCON, why);
            }
        }
        else
        {
            DespawnGizrul(why);
            if (instance && instance->GetBossState(BOSS_GIZRUL) != DONE)
            {
                instance->SetBossState(BOSS_GIZRUL, NOT_STARTED);
                ClearEncounterCredit(instance, NPC_GIZRUL, why);
            }
        }
        if (instance && instance->GetBossState(_bossState) != DONE)
            ClearEncounterCredit(instance, me->GetEntry(), why);
        if (instance)
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_HG_RABIES);
        Log("reset", why);
    }

    void DespawnGizrul(char const* why)
    {
        if (_gizrul)
            return;
        Creature* gizrul = Partner();
        _partner.Clear();
        if (!gizrul)
            return;
        if (auto* ai = AIOf(gizrul))
        {
            if (gizrul->IsAlive())
                ai->Cleanup();
            ai->_despawned = true;
        }
        gizrul->DespawnOrUnsummon();
        Log("gizrul-despawn", why);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Timers
    // ----------------------------------------------------------------------------------------------------------------

    void AdvanceTimers(uint32 diff, bool fury)
    {
        _thrash.Advance(diff, fury);
        _froth.Advance(diff, fury);
        _charge.Advance(diff, fury);
        _rabiesBite.Advance(diff, fury);
        _tornHide.Advance(diff, fury);
        _call.Advance(diff, false);     // Call of the Pack makes the fury; it does not speed itself up
    }

    void RunTimers(bool fury)
    {
        bool const casting = me->HasUnitState(UNIT_STATE_CASTING);
        bool const moving = _run.active || PounceBusy();

        // HG2 Gizrul (or a lone Halycon)
        if (_charge.Due() && !casting && !moving && !LeapSoon(kPawMs))
        {
            if (!StartCharge())
                _charge.Arm(kRetryMs);
            return;
        }
        // HG7 Halycon (or a lone Gizrul)
        if (_call.Due() && !casting && !moving && !LeapSoon(kCallCastMs + kPounceClearMs))
        {
            if (!StartCall())
                _call.Arm(kRetryMs);
            return;
        }
        // HG4 Halycon
        if (_thrash.Due() && !casting && !moving && !LeapSoon(kThrashWarnMs + kPounceClearMs))
        {
            StartThrash("timer");
            _thrash.Arm(kThrashEveryMs);
            return;
        }
        // HG5 Gizrul
        if (_froth.Due() && !casting && !moving)
        {
            StartFroth();
            _froth.Arm(kFrothEveryMs);
            return;
        }
        Unit* victim = me->GetVictim();
        bool const canBite = CanBite(victim);
        // HG6 Gizrul's bite
        if (_rabiesBite.Due() && canBite)
        {
            me->CastSpell(victim, SPELL_HG_RABIES, true);
            _rabiesBite.Arm(kRabiesBiteEveryMs);
            Log("rabies-bite", Acore::StringFormat("on={} stacks={}", victim->GetName(),
                DungeonKit::Stacks(victim, SPELL_HG_RABIES, me->GetGUID())));
        }
        // HG11 Torn Hide (10 players)
        if (_tornHide.Due() && canBite)
            TornHideBite(victim, fury);
    }

    // A bite needs the wolf free (no charge, pounce or cast bar) and its target in reach.
    bool CanBite(Unit* victim) const
    {
        return victim && !Busy() && me->IsWithinDist(victim, kTornHideBiteYd);
    }

    // A move that keeps the wolf off its melee (a charge, a pounce, a cast bar).
    bool Busy() const
    {
        return _run.active || PounceBusy() || me->HasUnitState(UNIT_STATE_CASTING);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HG2 Savage Charge, HG3 Pack Pounce, HG9 Rabid Trail
    // ----------------------------------------------------------------------------------------------------------------

    // The farthest non-tanks (never either wolf's tank); out of combat the GM stands in.
    std::vector<Player*> PickChargeTargets(uint32 count)
    {
        std::vector<Player*> out;
        if (!me->IsEngaged())
        {
            if (Player* gm = ObjectAccessor::GetPlayer(*me, _testPlayer))
                out.push_back(gm);
            return out;
        }
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.tankIfAlone = true;
        rule.farthest = true;
        if (Creature* partner = Partner())
            if (partner->IsAlive())
                if (Unit* other = partner->GetVictim())
                    if (other != me->GetVictim())
                        rule.exclude.push_back(other->GetGUID().GetRawValue());
        for (uint32 i = 0; i < count; ++i)
        {
            Player* pick = DungeonKit::PickPlayer(me, rule);
            if (!pick)
                break;
            out.push_back(pick);
            rule.exclude.push_back(pick->GetGUID().GetRawValue());
        }
        return out;
    }

    float GroundZ(Vec2 at, float refZ) const
    {
        float const h = me->GetMapHeight(at.x, at.y, refZ + 2.f);
        if (h <= INVALID_HEIGHT || std::fabs(h - refZ) > kGroundBandYd)
            return refZ;
        return h;
    }

    // False when nobody can be charged (tried again shortly).
    bool StartCharge()
    {
        std::vector<Player*> const picks = PickChargeTargets(kChargeLines.At(_players));
        if (picks.empty())
            return false;
        _run = ChargeRun();
        _run.active = true;
        _run.startMs = _clockMs;
        _run.lines = static_cast<uint32>(std::min<std::size_t>(picks.size(), 2));
        _run.z = me->GetPositionZ();
        for (uint32 i = 0; i < _run.lines; ++i)
            _run.targets[i] = picks[i]->GetGUID();
        _run.thrashAtEnd = !_gizrul;
        me->GetMotionMaster()->Clear();
        me->StopMoving();
        DungeonKit::CastBar(me, SPELL_HG_CHARGE_BAR);
        _charge.Arm(kChargeEveryMs);
        RegisterLine(0);
        return true;
    }

    void RegisterLine(uint32 i)
    {
        _run.registered[i] = true;
        Unit* target = ObjectAccessor::GetUnit(*me, _run.targets[i]);
        Vec2 const from = i == 0 ? DungeonKit::PlaneOf(me) : _run.end[i - 1];
        float aimAt = me->GetOrientation();
        if (target && DungeonKit::Distance(from, DungeonKit::PlaneOf(target)) > 0.5f)
            aimAt = DungeonKit::BearingTo(from, DungeonKit::PlaneOf(target));
        ChargeAim const aim = AimCharge(_arena.GetArena(), from, _run.z, aimAt);
        float const facing = aim.facing;
        float const length = aim.length;
        Vec2 const end = DungeonKit::Advance(from, facing, length);
        float const endZ = GroundZ(end, _run.z);
        _run.from[i] = from;
        _run.end[i] = end;

        BossMechanics::Anchor const start(Position(from.x, from.y, _run.z, facing));
        BossMechanics::Anchor const stop(Position(end.x, end.y, endZ, facing));
        MechanicRef ref = Mechanic::Line(me, start, stop, kChargeWidth, Ms(kPawMs));
        ref.Damage(kChargePct(_heroic)).Weakened().Rider(SPELL_HG_RABIES).Spell(SPELL_HG_SAVAGE_CHARGE)
            .Tag(TAG_HG_CHARGE);
        Track(ref.Handle());
        if (i == 0)
            me->SetFacingTo(facing);
        if (target)
            Talk(_gizrul ? uint8(EMOTE_GIZRUL_CHARGE) : uint8(EMOTE_HALYCON_CHARGE), target);

        // HG3: Halycon's circle at the line's end, drawn with the line.
        if (_gizrul && PounceOn(i, _heroic))
            if (Creature* halycon = Partner())
                if (auto* ai = AIOf(halycon))
                    _run.pounce[i] = ai->QueuePounce(Position(end.x, end.y, endZ, facing),
                        ChargePlan::PounceWarnMs());

        Log("charge", Acore::StringFormat("line={} target={} from=({:.1f}, {:.1f}) end=({:.1f}, {:.1f}) length={:.1f} "
            "pct={:.0f} pounce={}", i, target ? target->GetName() : "none", from.x, from.y, end.x, end.y, length,
            kChargePct(_heroic), _run.pounce[i] ? 1 : 0));
    }

    void UpdateCharge()
    {
        if (!_run.active)
            return;
        uint64 const t = _clockMs - _run.startMs;
        if (_run.lines > 1 && !_run.registered[1] && t >= ChargePlan::RegisterMs(1))
        {
            if (ObjectAccessor::GetUnit(*me, _run.targets[1]))
                RegisterLine(1);
            else
                _run.lines = 1;     // the second target left: one line
        }
        for (uint32 i = 0; i < _run.lines; ++i)
            if (_run.registered[i] && !_run.dashed[i] && t >= ChargePlan::ResolveMs(i))
                Dash(i);
        uint32 const last = _run.lines ? _run.lines - 1 : 0;
        if (_run.thrashAtEnd && !_run.thrashed && _run.dashed[last] && t >= ChargePlan::ArriveMs(last))
        {
            _run.thrashed = true;
            StartThrash("charge-end");
        }
        bool const allDashed = _run.lines && _run.dashed[last];
        if (!allDashed || t < ChargePlan::ReturnMs(_run.lines, _run.pounce[last]))
            return;
        if (_run.thrashAtEnd && me->HasUnitState(UNIT_STATE_CASTING))
            return;     // a lone Halycon finishes her Thrash first
        EndCharge();
    }

    // Line i resolves now (the registry's hit): he dashes along it; on heroic it stays soaked (HG9).
    void Dash(uint32 i)
    {
        _run.dashed[i] = true;
        Vec2 const end = _run.end[i];
        float const endZ = GroundZ(end, _run.z);
        float const length = DungeonKit::Distance(DungeonKit::PlaneOf(me), end);
        float const speed = std::max(kChargeMinSpeed, length * 1000.f / static_cast<float>(kChargeTravelMs));
        me->InterruptNonMeleeSpells(false);
        me->GetMotionMaster()->Clear();
        me->CastSpell(me, SPELL_HG_CHARGE_LOOK, true);
        me->GetMotionMaster()->MoveCharge(end.x, end.y, endZ, speed, kChargePointId);
        if (_heroic)
            StartTrail(_run.from[i], end, _run.z);
    }

    void EndCharge()
    {
        _run.active = false;
        if (Unit* victim = me->GetVictim())
            me->GetMotionMaster()->MoveChase(victim);
        Log("charge-end", Acore::StringFormat("lines={} at=({:.1f}, {:.1f})", _run.lines, me->GetPositionX(),
            me->GetPositionY()));
    }

    // HG9 (heroic): the line stays soaked for 12 s: a persistent 5 yd line, a Rabies stack every 2 s inside (the
    // first tick 2 s after the charge), Weakened once per trail per player (section 7 #25), the goo puddles.
    void StartTrail(Vec2 a, Vec2 b, float z)
    {
        float const facing = DungeonKit::BearingTo(a, b);
        BossMechanics::Anchor const start(Position(a.x, a.y, z, facing));
        BossMechanics::Anchor const stop(Position(b.x, b.y, GroundZ(b, z), facing));
        MechanicRef ref = Mechanic::Line(me, start, stop, kTrailWidth, Ms(kTrailTickMs));
        ref.Persistent(Ms(kTrailMs - kTrailTickMs), Ms(kTrailTickMs)).Rider(SPELL_HG_RABIES).WeakenedOncePerPlayer()
            .Spell(SPELL_HG_RABID_TRAIL).Color(BossMechanics::Color::Green).NoFillTimer().Tag(TAG_HG_TRAIL);
        Track(ref.Handle());
        uint32 puddles = 0;
        for (Vec2 const& p : TrailPuddles(a, b))
        {
            me->CastSpell(p.x, p.y, GroundZ(p, z), SPELL_HG_TRAIL_PUDDLE, true);
            ++puddles;
        }
        Log("trail", Acore::StringFormat("from=({:.1f}, {:.1f}) to=({:.1f}, {:.1f}) length={:.1f} puddles={}", a.x, a.y,
            b.x, b.y, DungeonKit::Distance(a, b), puddles));
    }

    // HG3 (Halycon): the circle at `at` lands in `landInMs`; she takes off kLeapMs before. False when she cannot
    // pounce (dead, not fighting, alone).
    bool QueuePounce(Position const& at, uint32 landInMs)
    {
        if (_gizrul || _lone || !me->IsAlive() || (!me->IsEngaged() && _testPlayer.IsEmpty()))
            return false;
        MechanicRef ref = Mechanic::Circle(me, BossMechanics::Anchor(at), kPounceRadius, Ms(landInMs));
        ref.Damage(kPouncePct(_heroic)).Weakened().Spell(SPELL_HG_PACK_POUNCE).Tag(TAG_HG_POUNCE);
        PendingPounce p;
        p.landMs = _clockMs + landInMs;
        p.leapMs = p.landMs - std::min<uint32>(kLeapMs, landInMs);
        p.at = at;
        p.circle = ref.Handle();
        Track(p.circle);
        _pounces.push_back(p);
        Log("pounce", Acore::StringFormat("at=({:.1f}, {:.1f}) land={}ms pct={:.0f}", at.GetPositionX(),
            at.GetPositionY(), landInMs, kPouncePct(_heroic)));
        return true;
    }

    void UpdatePounces()
    {
        if (_pounces.empty())
        {
            if (_pounceRecoverMs && _clockMs >= _pounceRecoverMs)
            {
                _pounceRecoverMs = 0;
                if (!_run.active && me->IsEngaged())
                    if (Unit* victim = me->GetVictim())
                        me->GetMotionMaster()->MoveChase(victim);
            }
            return;
        }
        for (auto it = _pounces.begin(); it != _pounces.end();)
        {
            if (!it->leapt && _clockMs >= it->leapMs)
                Leap(*it);
            if (it->leapt && _clockMs >= it->landMs)
            {
                me->CastSpell(me, SPELL_HG_MAUL_LOOK, true);
                _pounceRecoverMs = it->landMs + kPounceRecoverMs;
                it = _pounces.erase(it);
            }
            else
                ++it;
        }
    }

    void Leap(PendingPounce& p)
    {
        p.leapt = true;
        if (me->HasUnitState(UNIT_STATE_CASTING))
        {
            me->InterruptNonMeleeSpells(false);     // never by design (LeapSoon holds her casts); logged if it happens
            Log("pounce-broke-cast");
        }
        me->GetMotionMaster()->Clear();
        me->StopMoving();
        float const dist = me->GetExactDist2d(p.at.GetPositionX(), p.at.GetPositionY());
        uint64 const flightMs = p.landMs > _clockMs ? p.landMs - _clockMs : 1;
        float const speedXY = std::max(kLeapMinSpeedXY, dist * 1000.f / static_cast<float>(flightMs));
        DungeonKit::JumpTo(me, p.at, speedXY, kLeapMinSpeedZ, SPELL_HG_LEAP_LOOK, me);
    }

    bool PounceBusy() const
    {
        if (_pounceRecoverMs && _clockMs < _pounceRecoverMs)
            return true;
        for (PendingPounce const& p : _pounces)
            if (p.leapt)
                return true;
        return false;
    }

    // One of her pounces takes off within `windowMs`.
    bool LeapSoon(uint32 windowMs) const
    {
        for (PendingPounce const& p : _pounces)
            if (!p.leapt && p.leapMs <= _clockMs + windowMs)
                return true;
        return false;
    }

    void CancelPounces()
    {
        for (PendingPounce const& p : _pounces)
            if (p.circle.IsValid())
                Mechanic::Cancel(me, p.circle);
        _pounces.clear();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HG4 Thrash, HG5 Rabid Froth
    // ----------------------------------------------------------------------------------------------------------------

    void StartThrash(char const* why)
    {
        me->StopMoving();       // the chase pauses while the cast bar runs
        DungeonKit::CastBar(me, SPELL_HG_THRASH_BAR, nullptr, EMOTE_HALYCON_THRASH);
        MechanicRef ref = Mechanic::Circle(me, BossMechanics::Anchor(me), kThrashRadius, Ms(kThrashWarnMs));
        ref.TankExempt().Damage(kThrashPct(_heroic)).Weakened().Spell(SPELL_HG_THRASH).Tag(TAG_HG_THRASH);
        Track(ref.Handle());
        _whirlAtMs = _clockMs + kThrashWarnMs;
        Log("thrash", Acore::StringFormat("why={} pct={:.0f}", why, kThrashPct(_heroic)));
    }

    void StartFroth()
    {
        me->StopMoving();
        DungeonKit::CastBar(me, SPELL_HG_FROTH_BAR, nullptr, EMOTE_GIZRUL_FROTH);
        MechanicRef ref = Mechanic::Circle(me, BossMechanics::Anchor(me), kFrothRadius, Ms(kFrothWarnMs));
        ref.TankExempt().Damage(kFrothPct(_heroic)).Weakened().Rider(SPELL_HG_RABIES).Spell(SPELL_HG_RABID_FROTH)
            .Tag(TAG_HG_FROTH);
        Track(ref.Handle());
        _frothAtMs = _clockMs + kFrothWarnMs;
        Log("froth", Acore::StringFormat("pct={:.0f}", kFrothPct(_heroic)));
    }

    // The ring's look plays when it resolves (the AI's clock; the registry owns the hit).
    void UpdateLooks()
    {
        if (_whirlAtMs && _clockMs >= _whirlAtMs)
        {
            _whirlAtMs = 0;
            me->CastSpell(me, SPELL_HG_WHIRL_LOOK, true);
        }
        if (_frothAtMs && _clockMs >= _frothAtMs)
        {
            _frothAtMs = 0;
            me->CastSpell(me, SPELL_HG_FROTH_LOOK, true);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HG7 Call of the Pack, HG11 Torn Hide
    // ----------------------------------------------------------------------------------------------------------------

    // False when the cast was refused (tried again shortly).
    bool StartCall()
    {
        if (me->CastSpell(me, SPELL_HG_CALL_OF_THE_PACK, false) != SPELL_CAST_OK)
            return false;
        Talk(_gizrul ? uint8(EMOTE_GIZRUL_CALL) : uint8(EMOTE_HALYCON_CALL));
        _call.Arm(kCallEveryMs);
        Mechanic::NoteNextCastIn(me, SPELL_HG_CALL_OF_THE_PACK, Ms(kCallEveryMs));
        Log("call", Acore::StringFormat("cast={}ms lone={}", kCallCastMs, _lone ? 1 : 0));
        return true;
    }

    // The howl landed: Pack Fury on both wolves (a lone wolf: itself); heroic, a Bloodied Pack stack on each.
    void CallLanded()
    {
        std::vector<Creature*> wolves{ me };
        if (!_lone)
            if (Creature* partner = Partner())
                if (partner->IsAlive() && partner->IsEngaged())
                    wolves.push_back(partner);
        uint32 bloodied = 0;
        for (Creature* wolf : wolves)
        {
            wolf->CastSpell(wolf, SPELL_HG_PACK_FURY, true);
            if (_heroic)
                bloodied = DungeonKit::AddStacks(wolf, SPELL_HG_BLOODIED_PACK, 1, wolf, kBloodiedPackMax);
        }
        Log("call-landed", Acore::StringFormat("wolves={} fury={}ms bloodied={}", wolves.size(), kPackFuryMs,
            bloodied));
    }

    // HG11: this wolf's Torn Hide on its current target holds while the wolf cannot bite it (a charge, a pounce, the
    // run back, a cast bar, out of reach), so the stacks build at the bite rate whatever the downtime (R-1 ruling 2,
    // HalyconGizrulLogic.h). Applied a second at a time; a new target drops what the old one had banked.
    void HoldTornHide(uint32 diff)
    {
        Unit* victim = me->GetVictim();
        ObjectGuid const on = victim ? victim->GetGUID() : ObjectGuid::Empty;
        if (on != _tornHideHeldOn)
        {
            _tornHideHeldOn = on;
            _tornHideHeldMs = 0;
        }
        if (!victim)
            return;
        bool const holding = !CanBite(victim);
        if (holding)
            _tornHideHeldMs += diff;
        if (!_tornHideHeldMs)
            return;
        Aura* aura = victim->GetAura(SPELL_HG_TORN_HIDE, me->GetGUID());
        if (!aura)
        {
            _tornHideHeldMs = 0;
            return;
        }
        if (holding && !TornHideHoldDue(_tornHideHeldMs, aura->GetDuration()))
            return;
        DungeonKit::ShortenAura(victim, SPELL_HG_TORN_HIDE, me->GetGUID(),
            Milliseconds(aura->GetDuration() + static_cast<int32>(_tornHideHeldMs)));
        _tornHideHeldMs = 0;
    }

    // HG11: a stack on this wolf's own target; the duration follows the bite rate (HalyconGizrulLogic.h).
    void TornHideBite(Unit* victim, bool fury)
    {
        uint32 const stacks = DungeonKit::AddStacks(victim, SPELL_HG_TORN_HIDE, 1, me, kTornHideMax);
        DungeonKit::ShortenAura(victim, SPELL_HG_TORN_HIDE, me->GetGUID(), Ms(TornHideMs(fury)));
        if (victim->GetGUID() == _tornHideHeldOn)
            _tornHideHeldMs = 0;    // the bite sets the duration afresh
        _tornHide.Arm(kTornHideBiteEveryMs);
        Log("torn-hide", Acore::StringFormat("on={} stacks={} lasts={}ms fury={}", victim->GetName(), stacks,
            TornHideMs(fury), fury ? 1 : 0));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // State
    // ----------------------------------------------------------------------------------------------------------------

    char const* Key() const
    {
        return _gizrul ? kGizrulKey : kHalyconKey;
    }

    void Log(char const* mechanic, std::string const& detail = {}) const
    {
        DungeonKit::LogMechanic(kLogDungeon, Key(), mechanic, detail);
    }

    Creature* Partner() const
    {
        if (!_partner.IsEmpty())
            if (Creature* c = ObjectAccessor::GetCreature(*me, _partner))
                return c;
        if (!instance)
            return nullptr;
        if (_gizrul)
            return instance->GetCreature(BOSS_HALYCON);
        return ObjectAccessor::GetCreature(*me, instance->GetGuidData(BOSS_GIZRUL));
    }

    static boss_halycon_gizrul_rework* AIOf(Creature* creature)
    {
        if (!creature || !creature->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_halycon_gizrul_rework*>(creature->AI());
    }

    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 96)      // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 48);
    }

    // Nothing pending, no line, no pounce, no trail, no fury (Reset, evade, death, a new pull).
    void Cleanup()
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        _pounces.clear();
        _pounceRecoverMs = 0;
        _run = ChargeRun();
        _whirlAtMs = 0;
        _frothAtMs = 0;
        _thrash.Disarm();
        _froth.Disarm();
        _charge.Disarm();
        _rabiesBite.Disarm();
        _tornHide.Disarm();
        _tornHideHeldOn.Clear();
        _tornHideHeldMs = 0;
        _call.Disarm();
        _lone = false;
        while (me->RemoveDynObject(SPELL_HG_TRAIL_PUDDLE))
            ;
        for (uint32 const spell : { SPELL_HG_PACK_FURY, SPELL_HG_BLOODIED_PACK, SPELL_HG_GRIEF, SPELL_HG_SPRINT })
            me->RemoveAurasDueToSpell(spell);
        // This wolf's Torn Hide goes with it (the other wolf's stacks stay: the bots count per caster).
        if (Map* map = me->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* player = ref.GetSource())
                    player->RemoveAurasDueToSpell(SPELL_HG_TORN_HIDE, me->GetGUID());
        _arena.Reset();
        if (_phase != Phase::Running)
            _phase = Phase::Idle;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brs halycon` entry points
    // ----------------------------------------------------------------------------------------------------------------
public:
    bool IsGizrul() const { return _gizrul; }

    // An empty string when fired; otherwise why not. `gm` stands in for the group out of combat.
    std::string TestFire(TestKind kind, Player* gm)
    {
        _testPlayer = gm ? gm->GetGUID() : ObjectGuid::Empty;
        if (!me->IsEngaged() && !_players)
            _players = 5;
        switch (kind)
        {
            case TestKind::Charge:
                if (_run.active)
                    return "A charge is already running.";
                if (!StartCharge())
                    return "Nobody to charge.";
                break;
            case TestKind::Thrash:
                StartThrash("test");
                break;
            case TestKind::Froth:
                StartFroth();
                break;
            case TestKind::Call:
                if (me->HasUnitState(UNIT_STATE_CASTING))
                    return "Busy casting; try again in a moment.";
                if (!StartCall())
                    return "The howl was refused.";
                break;
            case TestKind::Trail:
            {
                if (!gm)
                    return "No player.";
                Vec2 const from = DungeonKit::PlaneOf(me);
                Vec2 const to = DungeonKit::PlaneOf(gm);
                ChargeAim const aim = AimCharge(_arena.GetArena(), from, me->GetPositionZ(),
                    DungeonKit::BearingTo(from, to));
                StartTrail(from, DungeonKit::Advance(from, aim.facing, aim.length), me->GetPositionZ());
                break;
            }
            case TestKind::TornHide:
            {
                Unit* target = gm ? (gm->GetSelectedPlayer() ? static_cast<Unit*>(gm->GetSelectedPlayer())
                    : static_cast<Unit*>(gm)) : nullptr;
                if (!target)
                    return "No player.";
                TornHideBite(target, HasFury(me));
                break;
            }
            case TestKind::Clear:
                Cleanup();
                break;
        }
        return {};
    }

    // `.dbtest brs halycon heroic <0|1>`: the heroic form on a normal map (and back) until the next pull.
    void TestHeroic(bool heroic)
    {
        _heroic = heroic;
    }

    std::string TestState() const
    {
        char const* phase = _phase == Phase::Idle ? "idle" : (_phase == Phase::Running ? "running" : "fighting");
        auto left = [](Cooldown const& c) -> std::string
        {
            return c.Armed() ? std::to_string(c.Left() / 1000) + "s" : "-";
        };
        return Acore::StringFormat("{} phase={} heroic={} players={} lone={} fury={} bloodied={} clock={}s "
            "charge={} call={} thrash={} froth={} bite={} tornhide={} charging={} pounces={}", Key(), phase,
            _heroic ? 1 : 0, _players, _lone ? 1 : 0, HasFury(me) ? 1 : 0,
            DungeonKit::Stacks(me, SPELL_HG_BLOODIED_PACK), _clockMs / 1000, left(_charge), left(_call),
            left(_thrash), left(_froth), left(_rabiesBite), left(_tornHide), _run.active ? 1 : 0, _pounces.size());
    }

private:
    uint32 const _bossState;    // BOSS_HALYCON or BOSS_GIZRUL, by entry
    bool const _gizrul;
    DungeonKit::ArenaGuard _arena;
    Phase _phase = Phase::Idle;
    bool _heroic = false;
    bool _lone = false;         // HG8: the partner fell
    bool _evading = false;
    uint8 _players = 0;         // the flex count held at the pull (5..10)
    uint64 _clockMs = 0;        // the AI's own clock: nothing here waits for a cast bar
    ObjectGuid _partner;
    uint64 _runStartMs = 0;
    uint32 _runNode = 0;
    Cooldown _thrash;           // HG4 Halycon
    Cooldown _call;             // HG7 Halycon, a lone Gizrul
    Cooldown _charge;           // HG2 Gizrul, a lone Halycon
    Cooldown _froth;            // HG5 Gizrul
    Cooldown _rabiesBite;       // HG6 Gizrul
    Cooldown _tornHide;         // HG11 both, 10 players
    ObjectGuid _tornHideHeldOn; // HG11 the target whose Torn Hide is held while this wolf cannot bite
    uint32 _tornHideHeldMs = 0;
    bool _despawned = false;    // Gizrul: DespawnGizrul ran (his evade stops there)
    ChargeRun _run;
    std::vector<PendingPounce> _pounces;
    uint64 _pounceRecoverMs = 0;
    uint64 _whirlAtMs = 0;
    uint64 _frothAtMs = 0;
    std::vector<MechanicHandle> _live;
    ObjectGuid _testPlayer;
};

// 210215 Rabies (HG6): the amount per stack is the kit's spell_dungeon_refflat_periodic (1% / 1.5% of the reference
// row in the effect's hundredths, the engine multiplies by the stacks). The aura ticks every 1.5 s; this script skips
// every other tick unless its caster wears Pack Fury (so every 3 s, every 1.5 s under the fury). A Disease dispel
// clears every stack (the dispel list's reward; Smolderweb's Venom precedent), not one.
class spell_brs_hg_rabies : public AuraScript
{
    PrepareAuraScript(spell_brs_hg_rabies);

    // The script's own tick count: the engine's tick number restarts at every new stack (R-1-B M2).
    void OnPeriodic(AuraEffect const* /*aurEff*/)
    {
        if (!_ticker.Next(HasFury(GetCaster())))
            PreventDefaultAction();
    }

    void ClearAllStacks(DispelInfo* dispelInfo)
    {
        dispelInfo->SetRemovedCharges(std::max<uint8>(1, GetStackAmount()));
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_brs_hg_rabies::OnPeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE);
        OnDispel += AuraDispelFn(spell_brs_hg_rabies::ClearAllStacks);
    }

    RabiesTicker _ticker;
};

namespace
{
    // The wolf a command acts on: Gizrul for his moves when he is up, else Halycon (out of combat she stands in for
    // him: a lone charge ends in a Thrash).
    boss_halycon_gizrul_rework* WolfAI(ChatHandler* handler, uint32 entry, bool quiet = false)
    {
        Creature* wolf = BrsTest::FindBoss(handler, entry);
        auto* ai = wolf && wolf->IsAIEnabled ? dynamic_cast<boss_halycon_gizrul_rework*>(wolf->AI()) : nullptr;
        if (!ai && !quiet && wolf)
            handler->SendErrorMessage("{} does not run the reworked script.", wolf->GetName());
        return ai;
    }

    boss_halycon_gizrul_rework* GizrulOrHalycon(ChatHandler* handler)
    {
        if (auto* ai = WolfAI(handler, NPC_GIZRUL, true))
            return ai;
        return WolfAI(handler, NPC_HALYCON);
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

    bool Fire(ChatHandler* handler, boss_halycon_gizrul_rework* ai, TestKind kind, char const* ok)
    {
        if (!ai)
            return false;
        return Reply(handler, ai->TestFire(kind, handler->GetPlayer()), ok);
    }

    // `.dbtest brs halycon info` / `gizrul`
    bool HandleInfo(ChatHandler* handler)
    {
        return BrsTest::ShowBossInfo(handler, NPC_HALYCON, BOSS_HALYCON);
    }

    bool HandleInfoGizrul(ChatHandler* handler)
    {
        return BrsTest::ShowBossInfo(handler, NPC_GIZRUL, BOSS_GIZRUL);
    }

    // `.dbtest brs halycon state`: both wolves' clocks.
    bool HandleState(ChatHandler* handler)
    {
        bool any = false;
        for (uint32 const entry : { static_cast<uint32>(NPC_HALYCON), static_cast<uint32>(NPC_GIZRUL) })
            if (auto* ai = WolfAI(handler, entry, true))
            {
                handler->SendSysMessage(ai->TestState());
                any = true;
            }
        if (!any)
            handler->SendErrorMessage("Neither wolf is here.");
        return any;
    }

    // `.dbtest brs halycon charge`: HG2 now (Gizrul, else a lone-style Halycon; out of combat at you).
    bool HandleCharge(ChatHandler* handler)
    {
        return Fire(handler, GizrulOrHalycon(handler), TestKind::Charge,
            "Savage Charge: a 3 s paw, then the line (out of combat: at you).");
    }

    // `.dbtest brs halycon thrash`: HG4 now.
    bool HandleThrash(ChatHandler* handler)
    {
        return Fire(handler, WolfAI(handler, NPC_HALYCON), TestKind::Thrash, "Thrash: the 8 yd ring, 2 s.");
    }

    // `.dbtest brs halycon froth`: HG5 now (Gizrul).
    bool HandleFroth(ChatHandler* handler)
    {
        return Fire(handler, WolfAI(handler, NPC_GIZRUL), TestKind::Froth, "Rabid Froth: the 10 yd ring, 2 s.");
    }

    // `.dbtest brs halycon call`: HG7's 3 s howl now (Halycon).
    bool HandleCall(ChatHandler* handler)
    {
        return Fire(handler, WolfAI(handler, NPC_HALYCON), TestKind::Call,
            "Call of the Pack: the 3 s howl started (landed: Pack Fury).");
    }

    // `.dbtest brs halycon trail`: HG9's trail from the wolf through you.
    bool HandleTrail(ChatHandler* handler)
    {
        return Fire(handler, GizrulOrHalycon(handler), TestKind::Trail, "Rabid Trail: 12 s, a stack every 2 s.");
    }

    // `.dbtest brs halycon tornhide`: an HG11 stack from Halycon on the selected player (or you).
    bool HandleTornHide(ChatHandler* handler)
    {
        return Fire(handler, WolfAI(handler, NPC_HALYCON), TestKind::TornHide, "Torn Hide: one stack.");
    }

    // `.dbtest brs halycon clear`: every line, circle, trail and fury goes (both wolves).
    bool HandleClear(ChatHandler* handler)
    {
        bool any = false;
        for (uint32 const entry : { static_cast<uint32>(NPC_HALYCON), static_cast<uint32>(NPC_GIZRUL) })
            if (auto* ai = WolfAI(handler, entry, true))
                any = Fire(handler, ai, TestKind::Clear, "Cleared.") || any;
        return any;
    }

    // `.dbtest brs halycon heroic [0|1]`
    bool HandleHeroic(ChatHandler* handler, Optional<uint32> on)
    {
        bool any = false;
        for (uint32 const entry : { static_cast<uint32>(NPC_HALYCON), static_cast<uint32>(NPC_GIZRUL) })
            if (auto* ai = WolfAI(handler, entry, true))
            {
                ai->TestHeroic(!on || *on != 0);
                any = true;
            }
        if (any)
            handler->SendSysMessage("The heroic form is set until the next pull.");
        return any;
    }

    ChatCommandTable const& HalyconGizrulTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,         SEC_GAMEMASTER, Console::No },
            { "gizrul",     HandleInfoGizrul,   SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,        SEC_GAMEMASTER, Console::No },
            { "charge",     HandleCharge,       SEC_GAMEMASTER, Console::No },
            { "thrash",     HandleThrash,       SEC_GAMEMASTER, Console::No },
            { "froth",      HandleFroth,        SEC_GAMEMASTER, Console::No },
            { "call",       HandleCall,         SEC_GAMEMASTER, Console::No },
            { "trail",      HandleTrail,        SEC_GAMEMASTER, Console::No },
            { "tornhide",   HandleTornHide,     SEC_GAMEMASTER, Console::No },
            { "clear",      HandleClear,        SEC_GAMEMASTER, Console::No },
            { "heroic",     HandleHeroic,       SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_halycon_gizrul_rework()
{
    RegisterDungeonReworkCreatureAI(boss_halycon_gizrul_rework, BlackrockSpireRework::kInstanceScriptName);
    RegisterSpellScript(spell_brs_hg_rabies);
    BrsTest::RegisterBoss("halycon", HalyconGizrulTestCommands());
}
