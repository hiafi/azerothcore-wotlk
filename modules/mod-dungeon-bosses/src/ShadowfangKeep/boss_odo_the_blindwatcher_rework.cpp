/*
 * mod-dungeon-bosses, Shadowfang Keep: Odo the Blindwatcher (WP-S5). Build spec: SK 904-952 (build spec), SK 816-903
 * (design), OD1-OD8; handoff section 3.5 rows OD, section 3.6 row S5, section 7 #24 (the bell points), section 8 #11
 * (speed_run 0.8 / 0.95 during the Hunt). Replaces Odo's SmartAI 4279 (WP-S5's SQL rev drops it: Call for Help gone,
 * Howling Rage kept here).
 *
 * Odo (normal and heroic):
 *   OD1 The Hunt      first at 10 s, then every 25 s: emote line 0 names a random non-tank (healer included), a 2 s
 *                     howl (cast bar), then he drops the tank and stalks that player for 10 s at 80% of a player's run
 *                     speed (heroic 95%, Relentless Hunt): a 3 yd registry circle on him, persistent with 200 ms
 *                     passes, eligible for the hunted player only; the Hunted debuff on them. The chase is the shared
 *                     Hunt (Hunt.h), the same model as the `sfk-hunt` drill.
 *   OD2 Maul          a pass that holds the hunted player: 3 s stun + 35% of reference health as a bleed over 3 s (no
 *                     Weakened: a DoT, ruling 17). The Hunt ends and he returns to the tank.
 *   OD3 Ring the bell three Alarm Bells (gameobject 301101 at the navmesh report's points, handoff section 7 #24).
 *                     During a Hunt a player who stands under a ready bell for 1 s (2 yd; never the hunted player,
 *                     never the tank) or clicks it (anyone but the hunted player) rings it. The bots get one registry
 *                     Soak (1 body, roles healer and damage, not the hunted) under the ready bell nearest to an
 *                     eligible ringer (the boss data bell rule); if nobody rings, it resolves just before the chase
 *                     ends and the ledger gets a MissedSoak (tag 2). A rung bell is cracked for 40 s (heroic: for the
 *                     rest of the fight, Silenced Bells): not clickable, smoke at the bell.
 *   OD4 Bell landing  the ring ends the Hunt: emote line 1, he bounds to the bell and lands 2 s later; a 6 yd registry
 *                     circle on the bell, 35% Physical + 1 Weakened for anyone inside (the ringer must step clear).
 *   OD5 Deafened      as he lands: damage taken +25% for 5 s.
 *   OD6 Blood Frenzy  heroic: every Maul adds a stack (+20% damage dealt each, no cap; emote line 2): the enrage.
 *   OD7 Howling Rage  stock 7481 / 7483 / 7484 at 70 / 50 / 30% health, once each, interruptible (descriptor
 *                     interrupt list); cast when he is not hunting, bounding or casting.
 * ArenaGuard on his room (OdoArena; DungeonKit::ApplyPlaytestPullRule): a player who leaves the room is teleported back
 * (8 yd toward where they were, else the room's middle); he never chases a victim off the room and evades if dragged
 * off.
 *
 * Every firing logs one INFO line, "sfk odo <mechanic> ...", in module.dungeonbosses. `.sfktest odo <mechanic>` fires
 * one on demand (OdoTestCommands below).
 *
 * Pilot lessons: custom damage spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS (the data); the landing and the Maul
 * deal registry / RefFlat numbers; the bound's landing and the hunt clock run on UpdateAI's diff, never on the BossAI
 * scheduler a cast bar pauses; mechanic emotes are type 41; every hit has an impact (Maul SV 577, landing SV 12083);
 * the bell circle is an outline (NoFillTimer).
 */

#include "ArenaGuard.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "Hunt.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "OdoLogic.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "ShadowfangKeepRework.h"
#include "ShadowfangKeepTestCommand.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <array>
#include <list>
#include <string>
#include <unordered_map>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ShadowfangKeepRework;
using namespace Odo;

namespace
{
    char constexpr kBoss[] = "odo";
    float constexpr kBellSearchYd = 80.f;
    float constexpr kFightRange = 80.f;
    uint32 constexpr kBellTollSound = 9154;     // SoundEntries BellTollKharazhan (handoff section 3.10 gap 16)

    SfkHunt::HuntSpells OdoHuntSpells()
    {
        return { SPELL_ODO_HUNT_HOWL, SPELL_ODO_HUNTED, SPELL_ODO_MAUL_HIT, SPELL_ODO_MAUL };
    }

    Position BellPosition(std::size_t bell)
    {
        Point3 const& p = kBellSpots[bell];
        return Position(p.x, p.y, p.z);
    }

    DungeonKit::ArenaGuardOptions OdoArenaOptions()
    {
        DungeonKit::ArenaGuardOptions o;
        // A unit in combat with another live boss is left to that boss: no two guards grip it to and fro (R2 S-2).
        o.skipGrip = DungeonKit::SkipEngagedWithOtherBoss(ShadowfangKeepRework::IsSfkBossEntry);
        DungeonKit::ApplyPlaytestPullRule(o);
        o.logPrefix = "sfk odo arena";
        // A Hunt chases its player: a hunted player who runs out of the door is gripped back after the grace (1.5 s),
        // and Odo, a few yards behind, may step past the door meanwhile. He leashes only after 3 s off the room.
        o.bossGraceMs = 3000;
        o.landing = [](Creature const* boss, Unit const* unit)
        {
            Vec2 const p = GripLanding(DungeonKit::PlaneOf(boss), boss->GetPositionZ(), DungeonKit::PlaneOf(unit));
            return DungeonKit::ToPosition(p, boss->GetPositionZ());
        };
        return o;
    }

    std::string NameOf(Unit const* u)
    {
        return u ? u->GetName() : std::string("none");
    }

    void LogOdo(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }
}

// Odo the Blindwatcher 4279
struct boss_odo_the_blindwatcher_rework : public BossAI
{
    explicit boss_odo_the_blindwatcher_rework(Creature* creature) : BossAI(creature, BOSS_ODO)
    {
        _dwell.fill(DungeonKit::DwellTracker(kBellDwellMs));
    }

    void Reset() override
    {
        StopAll();
        _Reset();
        ResetFight();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);   // zone in, ScheduleTasks, IN_PROGRESS

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_ODO;
        Mechanic::BeginEncounter(me, options);
        Describe();
        ResetFight();
        _arena.Engage(me);
        LogOdo("engage", Acore::StringFormat("heroic={} bells={}", DungeonKit::IsHeroicMap(me) ? 1 : 0, BellsFound()));
    }

    // The Hunt cadence rides `_cadence`, not BossAI's `scheduler`: its validator pauses while he casts, which would
    // stretch the 25 s cadence by every howl and Howling Rage (Pilot R1 S-2; R1 N-1).
    void ScheduleTasks() override
    {
        _cadence.Schedule(kHuntFirst, [this](TaskContext ctx)
        {
            if (Busy())
            {
                ctx.Repeat(kBusyRetry);
                return;
            }
            StartHunt();
            ctx.Repeat(kHuntEvery);
        });
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        StopAll();
        ResetFight();
        _EnterEvadeMode(why);
    }

    void JustDied(Unit* /*killer*/) override
    {
        StopAll();
        _JustDied();
        RestoreBells();
        LogOdo("died");
    }

    void DamageTaken(Unit* /*attacker*/, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*mask*/) override
    {
        uint64 const health = me->GetHealth();
        uint64 const left = health > damage ? health - damage : 0;
        if (me->GetMaxHealth())
            _howls.OnHealth(static_cast<float>(left) * 100.f / static_cast<float>(me->GetMaxHealth()));
    }

    void UpdateAI(uint32 diff) override
    {
        // Out of combat too: a `.sfktest` hunt or bound runs without a pull.
        UpdateHunt(diff);
        UpdateBound(diff);

        if (!UpdateVictim())
            return;

        UpdateClock(diff);
        if (!_arena.Update(me, diff))
            return;
        _cadence.Update(diff);

        if (me->HasUnitState(UNIT_STATE_CASTING) || _hunt.Active() || _bounding)
            return;
        if (TryHowl())
            return;
        DoMeleeAttackIfReady();
    }

    // ---- mechanics (also called by `.sfktest`) ---------------------------------------------------------------------

    // OD1: a Hunt on `forced` (a `.sfktest` caller), else a random non-tank. False when nobody qualifies.
    bool StartHunt(Player* forced = nullptr)
    {
        bool const heroic = DungeonKit::IsHeroicMap(me);
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.maxRange = kHuntPickRange;
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!target)
        {
            LogOdo("hunt", "skipped=no-target");
            return false;
        }
        SfkHunt::HuntTuning const tuning = SfkHunt::OdoHunt(heroic);
        if (!_hunt.Start(me, me, target, tuning, OdoHuntSpells(), kHuntTag(heroic)))
        {
            LogOdo("hunt", "skipped=refused target=" + target->GetName());
            return false;
        }
        _huntTarget = target->GetGUID();
        for (DungeonKit::DwellTracker& d : _dwell)
            d.Clear();
        _pollMs = 0;
        Talk(EMOTE_ODO_HUNT, target);
        RegisterBellSoak(target, tuning);
        LogOdo("hunt", Acore::StringFormat("target={} heroic={} rate={:.2f} bells_ready={} soak_bell={}",
            target->GetName(), heroic ? 1 : 0, SfkHunt::RunRate(tuning.ratePct), _bells.ReadyCount(_fightMs),
            _bellSoakIdx < kBellCount ? int(_bellSoakIdx) + 1 : 0));
        return true;
    }

    // OD3 + OD4: `bell` rings. Outside a Hunt, or on a cracked bell, nothing happens unless `force` (`.sfktest`).
    bool RingBell(std::size_t bell, Player* ringer, bool byClick, bool force = false)
    {
        if (bell >= kBellCount)
            return false;
        bool const ready = _bells.IsReady(bell, _fightMs);
        if (!force && (!_hunt.Active() || !ready))
            return false;
        bool const heroic = DungeonKit::IsHeroicMap(me);
        if (ready)
            _bells.Ring(bell, _fightMs, kBellCrackMs(heroic));
        CancelBellSoak();
        for (DungeonKit::DwellTracker& d : _dwell)
            d.Clear();

        if (GameObject* go = Bell(bell))
        {
            go->UseDoorOrButton(0, false, ringer);
            go->PlayDirectSound(kBellTollSound);
        }
        else
            me->PlayDirectSound(kBellTollSound);
        CrackLook(bell, true);
        if (ringer && ringer->IsAlive())
            ringer->CastSpell(ringer, SPELL_ODO_BELL_RING, true);

        Player const* hunted = ObjectAccessor::GetPlayer(*me, _huntTarget);
        _hunt.Stop(me, false);      // he breaks off: no chase, the bound follows
        LogOdo("bell", Acore::StringFormat("bell={} ringer={} click={} hunted={} cracked={} ready_left={}", bell + 1,
            NameOf(ringer), byClick ? 1 : 0, NameOf(hunted), heroic ? "fight" : "40s", _bells.ReadyCount(_fightMs)));
        Bound(bell);
        return true;
    }

    // A click on the bell gameobject (go_sfk_alarm_bell).
    void OnBellClicked(Player* player, GameObject* go)
    {
        std::optional<std::size_t> const bell = NearestBellSpot(DungeonKit::PlaneOf(go));
        if (!bell || !player)
            return;
        if (!CanRing(player->GetGUID() == _hunt.Target(), player == me->GetVictim(), true))
            return;
        RingBell(*bell, player, true);
    }

    // OD6 (heroic): one more stack of Blood Frenzy.
    void BloodFrenzy()
    {
        uint32 const stacks = DungeonKit::AddStacks(me, SPELL_ODO_BLOOD_FRENZY, 1, me, 0);
        Talk(EMOTE_ODO_FRENZY);
        LogOdo("frenzy", Acore::StringFormat("stacks={} damage_done_pct={:.0f}", stacks, stacks * kBloodFrenzyPct));
    }

    void StopHunt()
    {
        if (!_hunt.Active())
            return;
        _hunt.Stop(me, true);
        CancelBellSoak();
        LogOdo("hunt-end", "reason=stopped target=" + NameOf(ObjectAccessor::GetPlayer(*me, _huntTarget)));
    }

    BellBoard const& Bells() const { return _bells; }
    uint64 FightMs() const { return _fightMs; }

private:
    bool Busy() const
    {
        return _hunt.Active() || _bounding || me->HasUnitState(UNIT_STATE_CASTING);
    }

    void Describe()
    {
        BossMechanics::Descriptor d;
        for (uint32 const spell : kHowlSpells)
            d.interrupts.push_back({ NPC_ODO, spell, 1 });
        Mechanic::Describe(me, std::move(d));
    }

    void ResetFight()
    {
        _bells.Reset();
        _howls.Reset();
        _fightMs = 0;
        _pollMs = 0;
        for (DungeonKit::DwellTracker& d : _dwell)
            d.Clear();
        FindBells();
        RestoreBells();
    }

    // Ends everything in flight: the Hunt cadence, the hunt (no chase), the bell soak, the bound.
    void StopAll()
    {
        _cadence.CancelAll();
        _hunt.Stop(me, false);
        CancelBellSoak();
        _bounding = false;
        _landMs = 0;
        me->SetCombatMovement(true);
        _arena.Reset();
    }

    void UpdateHunt(uint32 diff)
    {
        if (!_hunt.Active())
            return;
        SfkHunt::HuntEnd const end = _hunt.Update(me, diff);
        if (end != SfkHunt::HuntEnd::None)
        {
            OnHuntEnded(end);
            return;
        }
        PollBells(diff);
    }

    void OnHuntEnded(SfkHunt::HuntEnd end)
    {
        CancelBellSoak();
        Player const* target = ObjectAccessor::GetPlayer(*me, _huntTarget);
        LogOdo("hunt-end", Acore::StringFormat("reason={} target={}", SfkHunt::HuntEndName(end), NameOf(target)));
        if (end != SfkHunt::HuntEnd::Caught)
            return;
        LogOdo("maul", Acore::StringFormat("target={} pct={:.0f} stun_ms={}", NameOf(target), kMaulPct, kMaulMs));
        if (DungeonKit::IsHeroicMap(me))
            BloodFrenzy();
    }

    // The bots' job (the boss data bell rule): one Soak under the ready bell nearest to an eligible ringer.
    void RegisterBellSoak(Player* hunted, SfkHunt::HuntTuning const& tuning)
    {
        std::array<bool, kBellCount> const ready = _bells.Ready(_fightMs);
        Unit const* tank = me->GetVictim();
        GuidSet carriers;
        std::vector<Vec2> ringers;
        for (Player* p : FightPlayers())
        {
            if (p == hunted)
                continue;
            carriers.insert(p->GetGUID());
            if (CanRing(false, p == tank, false))
                ringers.push_back(DungeonKit::PlaneOf(p));
        }
        std::optional<std::size_t> const bell = ChooseBell(ready, ringers);
        if (!bell || carriers.empty())
            return;
        BossMechanics::Eligibility eligibility;
        eligibility.roles = BossMechanics::Role::Healer | BossMechanics::Role::Damage;
        eligibility.carriers = carriers;
        uint32 const total = SfkHunt::TotalMs(tuning);
        uint32 const window = total > kBellSoakEarlyMs ? total - kBellSoakEarlyMs : total;
        BossMechanics::MechanicRef ref = Mechanic::Soak(me, BellPosition(*bell), kBellRadius, 1, Milliseconds(window));
        ref.Eligible(eligibility).NoFillTimer().Tag(TAG_BELL);
        _bellSoak = ref.Handle();
        _bellSoakIdx = *bell;
    }

    void CancelBellSoak()
    {
        if (_bellSoak)
            Mechanic::Cancel(me, _bellSoak);
        _bellSoak = {};
        _bellSoakIdx = kBellCount;
    }

    // OD3: 1 s under a ready bell rings it (every 250 ms; anyone but the hunted player and the tank).
    void PollBells(uint32 diff)
    {
        _pollMs += diff;
        if (_pollMs < kBellPollMs)
            return;
        uint32 const elapsed = _pollMs;
        _pollMs = 0;
        ObjectGuid const hunted = _hunt.Target();
        Unit const* tank = me->GetVictim();
        std::vector<Player*> const players = FightPlayers();
        for (std::size_t i = 0; i < kBellCount; ++i)
        {
            if (!_bells.IsReady(i, _fightMs))
            {
                _dwell[i].Clear();
                continue;
            }
            Position const at = BellPosition(i);
            std::vector<uint64> inside;
            std::unordered_map<uint64, Player*> byId;
            for (Player* p : players)
            {
                if (!DungeonKit::InPickupRange(p->GetExactDist2d(&at), p->GetPositionZ() - at.GetPositionZ(),
                        kBellRadius, kBellZBand))
                    continue;
                if (!CanRing(p->GetGUID() == hunted, p == tank, false))
                    continue;
                inside.push_back(p->GetGUID().GetRawValue());
                byId[p->GetGUID().GetRawValue()] = p;
            }
            if (uint64 const taker = _dwell[i].Update(inside, elapsed))
            {
                RingBell(i, byId[taker], false);
                return;
            }
        }
    }

    // OD4: the bound to the bell, the landing circle (it resolves as he lands), Deafened on landing (UpdateBound).
    void Bound(std::size_t bell)
    {
        Position const at = BellPosition(bell);
        float const dist = me->GetExactDist2d(&at);
        Talk(EMOTE_ODO_BELL);
        me->CastSpell(me, SPELL_ODO_BOUND, true);
        Mechanic::Circle(me, at, kLandingRadius, kLandingWarn).Damage(kLandingPct).Spell(SPELL_ODO_BELL_LANDING)
            .Weakened().Tag(TAG_LANDING);
        me->GetMotionMaster()->MoveJump(at, BoundSpeedXY(dist), kBoundSpeedZ);
        _bounding = true;
        _landMs = static_cast<uint32>(kLandingWarn.count());
        LogOdo("bound", Acore::StringFormat("bell={} dist={:.1f} landing_pct={:.0f} radius={:.0f}", bell + 1, dist,
            kLandingPct, kLandingRadius));
    }

    void UpdateBound(uint32 diff)
    {
        if (!_bounding)
            return;
        if (diff < _landMs)
        {
            _landMs -= diff;
            return;
        }
        _landMs = 0;
        _bounding = false;
        me->CastSpell(me, SPELL_ODO_DEAFENED, true);
        LogOdo("deafened", Acore::StringFormat("ms={} damage_taken_pct={:.0f}", kDeafenedMs, kDeafenedPct));
        if (me->IsCombatMovementAllowed())
            if (Unit* victim = me->GetVictim())
                me->GetMotionMaster()->MoveChase(victim);
    }

    // OD7: the next due Howling Rage, when he is free.
    bool TryHowl()
    {
        std::optional<std::size_t> const next = _howls.Next();
        if (!next)
            return false;
        if (me->CastSpell(me, kHowlSpells[*next], false) != SPELL_CAST_OK)
            return false;
        _howls.MarkCast(*next);
        LogOdo("howling-rage", Acore::StringFormat("threshold={} spell={}", kHowlThresholdPct[*next],
            kHowlSpells[*next]));
        return true;
    }

    // The fight clock (the bells' cracked timers) and the normal bells coming back.
    void UpdateClock(uint32 diff)
    {
        uint64 const before = _fightMs;
        _fightMs += diff;
        for (std::size_t const bell : _bells.Recovered(before, _fightMs))
        {
            CrackLook(bell, false);
            LogOdo("bell-ready", Acore::StringFormat("bell={}", bell + 1));
        }
    }

    // Alive, non-GM players on his map within the fight's reach.
    std::vector<Player*> FightPlayers() const
    {
        std::vector<Player*> out;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* p = ref.GetSource();
            if (p && p->IsInWorld() && p->IsAlive() && !p->IsGameMaster() && me->GetExactDist2d(p) <= kFightRange)
                out.push_back(p);
        }
        return out;
    }

    // ---- the bell gameobjects --------------------------------------------------------------------------------------

    void FindBells()
    {
        std::list<GameObject*> gos;
        me->GetGameObjectListWithEntryInGrid(gos, GO_SFK_ALARM_BELL, kBellSearchYd);
        for (GameObject* go : gos)
            if (std::optional<std::size_t> const bell = NearestBellSpot(DungeonKit::PlaneOf(go)))
                _bellGo[*bell] = go->GetGUID();
    }

    uint32 BellsFound() const
    {
        uint32 n = 0;
        for (ObjectGuid const& g : _bellGo)
            n += g.IsEmpty() ? 0 : 1;
        return n;
    }

    GameObject* Bell(std::size_t bell)
    {
        if (bell >= kBellCount)
            return nullptr;
        if (_bellGo[bell].IsEmpty())
            FindBells();
        return _bellGo[bell].IsEmpty() ? nullptr : me->GetMap()->GetGameObject(_bellGo[bell]);
    }

    // A cracked bell: not clickable, smoke from a stalker at its foot (the visual stalker 300516, summoned by the bell
    // itself so it never joins his summons or the fight). A ready bell: clickable, no smoke.
    void CrackLook(std::size_t bell, bool cracked)
    {
        GameObject* go = Bell(bell);
        if (Creature* smoke = _smoke[bell].IsEmpty() ? nullptr : me->GetMap()->GetCreature(_smoke[bell]))
            smoke->DespawnOrUnsummon();
        _smoke[bell].Clear();
        if (!go)
            return;
        if (!cracked)
        {
            go->RemoveGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
            return;
        }
        go->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        if (TempSummon* stalker = go->SummonCreature(NPC_SFK_STRIKE_STALKER, BellPosition(bell),
                TEMPSUMMON_MANUAL_DESPAWN))
        {
            stalker->SetReactState(REACT_PASSIVE);
            stalker->CastSpell(stalker, SPELL_ODO_CRACKED_BELL, true);
            _smoke[bell] = stalker->GetGUID();
        }
    }

    void RestoreBells()
    {
        for (std::size_t i = 0; i < kBellCount; ++i)
            CrackLook(i, false);
    }

    DungeonKit::ArenaGuard _arena{ OdoArena(), OdoArenaOptions() };
    SfkHunt::Hunt _hunt;
    TaskScheduler _cadence;                     // the Hunt cadence (never paused by a cast)
    ObjectGuid _huntTarget;
    BellBoard _bells;
    HowlTracker _howls;
    std::array<DungeonKit::DwellTracker, kBellCount> _dwell;
    std::array<ObjectGuid, kBellCount> _bellGo;
    std::array<ObjectGuid, kBellCount> _smoke;
    BossMechanics::MechanicHandle _bellSoak;
    std::size_t _bellSoakIdx = kBellCount;
    uint64 _fightMs = 0;
    uint32 _pollMs = 0;
    bool _bounding = false;
    uint32 _landMs = 0;
};

// The Alarm Bell 301101 (go_sfk_alarm_bell): a click rings it during a Hunt (OD3); standing under it is Odo's poll.
// The script owns the bell: the stock goober use never runs.
struct go_sfk_alarm_bell : public GameObjectAI
{
    explicit go_sfk_alarm_bell(GameObject* go) : GameObjectAI(go) { }

    bool GossipHello(Player* player, bool /*reportUse*/) override
    {
        InstanceScript* instance = me->GetInstanceScript();
        Creature* odo = instance ? instance->GetCreature(DATA_ODO_GUID) : nullptr;
        if (odo && odo->IsAlive() && odo->IsAIEnabled)
            if (auto* ai = dynamic_cast<boss_odo_the_blindwatcher_rework*>(odo->AI()))
                ai->OnBellClicked(player, me);
        return true;
    }
};

namespace
{
    boss_odo_the_blindwatcher_rework* FindOdo(ChatHandler* handler)
    {
        Creature* boss = SfkTest::FindBoss(handler, NPC_ODO);
        if (!boss)
            return nullptr;
        auto* ai = dynamic_cast<boss_odo_the_blindwatcher_rework*>(boss->AI());
        if (!ai)
            handler->SendErrorMessage(
                "Odo is not running boss_odo_the_blindwatcher_rework (instance script not bound?).");
        return ai;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return SfkTest::ShowBossInfo(handler, NPC_ODO, BOSS_ODO);
    }

    // `.sfktest odo hunt`: one Hunt on the selected player, else the GM (`.gm off`: the registry skips game masters).
    bool HandleHunt(ChatHandler* handler)
    {
        boss_odo_the_blindwatcher_rework* ai = FindOdo(handler);
        if (!ai)
            return false;
        Player* target = handler->getSelectedPlayerOrSelf();
        if (!target || !ai->StartHunt(target))
        {
            handler->SendErrorMessage("No Hunt started (no target, or the registry refused it).");
            return false;
        }
        handler->PSendSysMessage("Hunt on {}: 2 s howl, then 10 s at {}% run speed.", target->GetName(),
            SfkHunt::OdoHunt(DungeonKit::IsHeroicMap(target)).ratePct);
        return true;
    }

    // `.sfktest odo bell <1-3>`: rings that bell now, as the GM (even outside a Hunt, even cracked): the bound, the
    // landing and Deafened follow.
    bool HandleBell(ChatHandler* handler, uint32 bell)
    {
        boss_odo_the_blindwatcher_rework* ai = FindOdo(handler);
        if (!ai)
            return false;
        if (bell < 1 || bell > kBellCount)
        {
            handler->SendErrorMessage("Bell 1, 2 or 3 (1 by Odo, 2 mid-room, 3 in the far alcove).");
            return false;
        }
        ai->RingBell(bell - 1, handler->GetPlayer(), true, true);
        handler->PSendSysMessage("Bell {} rung.", bell);
        return true;
    }

    // `.sfktest odo bells`: the three bells' state.
    bool HandleBells(ChatHandler* handler)
    {
        boss_odo_the_blindwatcher_rework* ai = FindOdo(handler);
        if (!ai)
            return false;
        for (std::size_t i = 0; i < kBellCount; ++i)
        {
            Point3 const& p = kBellSpots[i];
            handler->PSendSysMessage("Bell {} at ({:.1f}, {:.1f}, {:.1f}): {}", i + 1, p.x, p.y, p.z,
                ai->Bells().IsReady(i, ai->FightMs()) ? "ready"
                : ai->Bells().CrackedForGood(i) ? "cracked for the fight" : "cracked");
        }
        return true;
    }

    // `.sfktest odo stop`: ends the current Hunt (no catch).
    bool HandleStop(ChatHandler* handler)
    {
        boss_odo_the_blindwatcher_rework* ai = FindOdo(handler);
        if (!ai)
            return false;
        ai->StopHunt();
        return true;
    }

    // `.sfktest odo maul`: the Maul (stun + bleed) on the selected player, else the GM.
    bool HandleMaul(ChatHandler* handler)
    {
        Creature* boss = SfkTest::FindBoss(handler, NPC_ODO);
        Player* target = handler->getSelectedPlayerOrSelf();
        if (!boss || !target)
            return false;
        boss->CastSpell(target, SPELL_ODO_MAUL, true);
        handler->PSendSysMessage("Maul on {}: 3 s stun, 35% of reference health over 3 s.", target->GetName());
        return true;
    }

    // `.sfktest odo frenzy`: one Blood Frenzy stack (the heroic enrage).
    bool HandleFrenzy(ChatHandler* handler)
    {
        boss_odo_the_blindwatcher_rework* ai = FindOdo(handler);
        if (!ai)
            return false;
        ai->BloodFrenzy();
        return true;
    }

    // `.sfktest odo deafen`: Deafened on Odo (5 s, damage taken +25%).
    bool HandleDeafen(ChatHandler* handler)
    {
        Creature* boss = SfkTest::FindBoss(handler, NPC_ODO);
        if (!boss)
            return false;
        boss->CastSpell(boss, SPELL_ODO_DEAFENED, true);
        return true;
    }

    // `.sfktest odo howl <1-3>`: the stock Howling Rage of that threshold (70 / 50 / 30%), interruptible.
    bool HandleHowl(ChatHandler* handler, uint32 which)
    {
        Creature* boss = SfkTest::FindBoss(handler, NPC_ODO);
        if (!boss)
            return false;
        if (which < 1 || which > kHowlSpells.size())
        {
            handler->SendErrorMessage("Howling Rage 1, 2 or 3 (70, 50, 30%).");
            return false;
        }
        boss->CastSpell(boss, kHowlSpells[which - 1], false);
        return true;
    }

    ChatCommandTable const& OdoTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
            { "hunt", HandleHunt, SEC_GAMEMASTER, Console::No },
            { "bell", HandleBell, SEC_GAMEMASTER, Console::No },
            { "bells", HandleBells, SEC_GAMEMASTER, Console::No },
            { "stop", HandleStop, SEC_GAMEMASTER, Console::No },
            { "maul", HandleMaul, SEC_GAMEMASTER, Console::No },
            { "frenzy", HandleFrenzy, SEC_GAMEMASTER, Console::No },
            { "deafen", HandleDeafen, SEC_GAMEMASTER, Console::No },
            { "howl", HandleHowl, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_odo_the_blindwatcher_rework()
{
    RegisterDungeonReworkCreatureAI(boss_odo_the_blindwatcher_rework, ShadowfangKeepRework::kInstanceScriptName);
    RegisterDungeonReworkGameObjectAI(go_sfk_alarm_bell, ShadowfangKeepRework::kInstanceScriptName);
    SfkHunt::AddSC_sfk_hunt();      // spell_sfk_hunt_maul (Odo's Maul and the Echo of Odo's)
    SfkTest::RegisterBoss("odo", OdoTestCommands());
}
