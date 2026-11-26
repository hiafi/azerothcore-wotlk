/*
 * mod-dungeon-bosses, Zul'Farrak D2: Antu'sul (8127) and his Servants (8156), normal and heroic. Build spec: SP 733-807
 * (AS1-AS11), design SP 534-732 (theme Stoneflesh, rulings 13-16); handoff section 3.5 row D2, sections 3.6, 3.8, 3.10,
 * section 7 #9 A (the bots' Calcify rule), #25 A (he wakes by himself) and #28 A (the chamber fight). Replaces SmartAI
 * 8127 and 8156 (dropped by rev_skeleton_zul_farrak.sql): Chain Lightning 16006, Earthgrab Totem 8376, Healing Ward
 * 11899, Healing Wave of Antu'sul 11895, Antu'sul's Minion 11894 and the Servant's Petrify 11020 are retired (their new
 * forms below); Earth Shock 15501 is cast as it is. Bound by apps/dbc-tools source/npcs/zul_farrak/antusul.py; numbers
 * in AntusulLogic.h, health in ZulFarrakRework.h Health.
 *
 *   Wake         area trigger 1447 (a 30 yd sphere at the den mouth, its SmartAI kept) and DC's wake hook send
 *                SetData(1, 1): he engages the nearest player (a player on his floor first, the stock "Start
 *                Attacking" radius 100) and charges out of the dead end, so the fight lands in the chamber (#28 A).
 *   AS1 Servants one on the pull, then one every 25 s / 20 s, at most 3 alive (a rise at the cap is skipped), on a
 *                kServantRisePoints spot clear of him (AntusulLogic.h PickRisePoint); yell line 2 for every rise after
 *                the pull's, line 0 the first time three are alive. Stationary, passive, no melee.
 *   AS2 Gaze     each Servant stares at a random player on his floor (tank included) for 6 s, a Calcify stack every
 *                2 s / 1.5 s, then a new target 2 s later (GazeClock). A stun, fear or polymorph on the Servant ends
 *                it; the 2 s wait runs again once it lets go. The beam (213891) is a look: the stacks run on his clock.
 *   AS3 Calcify  213890, Magic, 6 stacks, 30 s, refreshed by each stack: -5% damage taken and -7% speed a stack. A
 *                dispel takes every stack and shatters them (spell_zf_antusul_calcify). Bots: only a lone carrier at
 *                4+ stacks, never the tank on heroic while he has Stoneflesh (the descriptor).
 *   AS4 Earth    stock 15501 on his victim, 3 s then every 9 to 11 s, triggered (a kicked Nature school never
 *       Shock    refuses it), +1 Calcify.
 *   AS5 Petrify  the sixth stack: the stacks go, a 2 s stun (213892) and a 6 yd registry circle on the statue (the
 *                crack's shrapnel, 6 stacks: 36% / 54%, no Weakened); at 2 s the crack: 25% / 35% to the statue.
 *                Heroic: a crack within 6 yd of his edge strips a Stoneflesh stack.
 *   AS6 Bolt     a 2.5 s / 2 s Physical bar (not kickable) on a random player with Calcify (anyone if nobody), 6 s
 *                then every 10-12 s / 8-10 s; a 6 yd circle on the target for the bar (no damage: the warning).
 *                Landed: 15% / 25% Nature to the target (cut by its own stone), then its stacks shatter (AS7).
 *   AS7 Shatter  a bolt's or a dispel's shrapnel: a 6 yd registry circle on the carrier (never hit by it), 6% / 9%
 *                Physical a stack, Weakened up to 5 stacks; heroic stone dust: +2 Calcify on everyone hit (applied on
 *                the next tick, never inside the registry's resolve).
 *   AS8 Shock-   a 3 s Physical bar (emote line 3) 20 s then every 20 s / 18 s; 50% / 70% Nature to everyone on his
 *       wave     floor, cut 10% a Calcify stack (AntusulLogic.h ShockwaveScriptPct makes up for Calcify's own 5%):
 *                one RegistryHit per stack count.
 *   AS9 Heal     Healing Wave of Antu'sul, a 3 s / 2 s Nature cast (kickable, the interrupt list) 15 s then every
 *                20-25 s: 4% / 8% of his health.
 *   AS10 Stone-  heroic: 3 stacks on him at the pull (-10% taken each), never returning. Bots: a persistent Stack at
 *        flesh   him for 5+ stack carriers while he has a stack (the tank stands there anyway).
 *   AS11         stock melee (DamageModifier 4.25).
 *   Arena        DenArena() (the throat, the chamber and the tail) with LeashOptions; every pick and hit is filtered
 *                by it (rule 5).
 *
 * Casts never overlap: the three bars wait until he is free (the Shockwave first), Earth Shock and the rises fire
 * whatever he casts. Every timer runs on the AI's own clock (AntusulLogic.h Timeline). Every firing logs one INFO line
 * "zf-build antusul <mechanic> ..."; `.dbtest zf antusul <mechanic>` fires one.
 */

#include "AntusulLogic.h"
#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MechanicRegistry.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "Spell.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ZulFarrakKit.h"
#include "ZulFarrakRework.h"
#include "ZulFarrakTestCommand.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <map>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ZulFarrakRework;
using namespace ZfAntusul;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;

namespace
{
    char const* const kBossKey = "antusul";
    uint8 constexpr kSchoolPhysical = 0;            // SPELL_SCHOOL_NORMAL
    uint8 constexpr kSchoolNature = 3;              // SPELL_SCHOOL_NATURE

    // The floor under a point (a Servant stands on it); falls back to the given height.
    float FloorZ(WorldObject const* ref, float x, float y, float z)
    {
        float const floor = ref->GetMapHeight(x, y, z + 3.f);
        return floor > INVALID_HEIGHT + 1.f && std::fabs(floor - z) <= 5.f ? floor : z;
    }

    uint32 RandBelow(uint32 n)
    {
        return n ? urand(0, n - 1) : 0;
    }

    // AS2: a Servant held by a stun, a fear or a polymorph (any confuse) stops its gaze.
    bool ServantHeld(Unit const* servant)
    {
        return servant->HasUnitState(UNIT_STATE_STUNNED | UNIT_STATE_CONFUSED | UNIT_STATE_FLEEING);
    }

    bool IsStatue(Unit const* player)
    {
        return player->HasAura(SPELL_AS_PETRIFIED);
    }
}

// Antu'sul 8127
struct boss_antusul_rework : public BossAI
{
    explicit boss_antusul_rework(Creature* creature)
        : BossAI(creature, BOSS_ANTUSUL), _arena(DenArena(), LeashOptions(kBossKey))
    {
    }

    void Reset() override
    {
        _Reset();
        Cleanup();
    }

    // Section 7 #25 A: area trigger 1447's SmartAI (and DC's wake hook) sends SetData(1, 1).
    void SetData(uint32 type, uint32 data) override
    {
        if (type == kWakeDataId && data == kWakeDataValue)
            Wake("trigger");
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);       // DoZoneInCombat, BOSS_ANTUSUL IN_PROGRESS
        if (!me->IsEngaged())
            return;     // BossAI evaded

        Cleanup();      // a `.dbtest zf antusul` mechanic out of combat may have left something behind
        _heroic = DungeonKit::IsHeroicMap(me);
        _engaged = true;

        OnBossPull(me, kBossKey);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_ANTUSUL;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        Talk(YELL_AGGRO);
        if (_heroic)
        {
            DungeonKit::AddStacks(me, SPELL_AS_STONEFLESH, int32(Tune::kStonefleshStacks), me,
                Tune::kStonefleshStacks);
            RegisterStonefleshStack();
        }
        Log("engage", Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f}) stoneflesh={}", _heroic ? 1 : 0,
            me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), DungeonKit::Stacks(me, SPELL_AS_STONEFLESH)));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Log("evade", Acore::StringFormat("reason={}", uint32(why)));
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Cleanup();
        BossAI::JustDied(killer);   // BOSS_ANTUSUL DONE
        Log("death");
    }

    // The Servants: in the fight at once, units of his encounter (the bots' kill order), despawned with his summons.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
        if (_engaged)
            DoZoneInCombat(summon);
        Mechanic::TrackUnit(me, summon);
    }

    // AS9: a kick (or a silence) on Healing Wave: the reward is the heal lost and his Nature school locked.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (spell && (spell->Id == SPELL_AS_HEALING_WAVE || spell->Id == SPELL_AS_HEALING_WAVE_H))
            Log("heal-kicked", Acore::StringFormat("health={}", me->GetHealth()));
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

        // The fight clock moves every tick, cast bar or not (the Pilot's lesson).
        _timeline.Advance(diff);
        ApplyStoneDust();
        UpdateStatues();
        UpdateServants(diff);
        UpdateLandings();
        if (!_engaged || !me->IsAlive())
            return;
        UpdateStonefleshStack(diff);

        if (_timeline.RiseDue())
            RiseServant(false);
        if (_timeline.EarthShockDue())
            EarthShock();

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        StartDueBar();
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ---- the wake (section 7 #25 A, #28 A) -----------------------------------------------------------------------

    bool Wake(char const* why)
    {
        if (!me->IsAlive() || me->IsInCombat() || me->IsInEvadeMode() || _engaged)
            return false;
        Player* target = WakeTarget();
        if (!target)
        {
            Log("wake-skip", Acore::StringFormat("why={} (nobody within {:.0f} yd)", why, Tune::kWakeRangeYd));
            return false;
        }
        Log("wake", Acore::StringFormat("why={} target={} distance={:.1f} on_floor={}", why, target->GetName(),
            me->GetExactDist2d(target), _arena.Contains(target) ? 1 : 0));
        me->EngageWithTarget(target);
        AttackStart(target);
        return true;
    }

    // The nearest living player within the stock radius, one on his floor first.
    Player* WakeTarget()
    {
        Player* best = nullptr;
        bool bestOnFloor = false;
        float bestDist = 0.f;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player || !player->IsAlive() || player->IsGameMaster() || !player->IsInWorld())
                continue;
            float const dist = me->GetExactDist(player);
            if (dist > Tune::kWakeRangeYd)
                continue;
            bool const onFloor = _arena.Contains(player);
            if (!best || (onFloor && !bestOnFloor) || (onFloor == bestOnFloor && dist < bestDist))
            {
                best = player;
                bestOnFloor = onFloor;
                bestDist = dist;
            }
        }
        return best;
    }

    // ---- AS3 Calcify, AS5 Petrified ------------------------------------------------------------------------------

    // Adds `n` stacks from him (a gaze, Earth Shock, stone dust, a `.dbtest`); the sixth petrifies. Returns the stacks
    // now (0: none, or petrified).
    uint32 AddCalcify(Player* player, uint32 n, char const* why)
    {
        if (!player || !player->IsAlive() || !n || IsStatue(player))
            return 0;
        uint32 const now = DungeonKit::AddStacks(player, SPELL_AS_CALCIFY, int32(n), me, Tune::kCalcifyMaxStacks);
        if (n > 1 || std::string(why) != "gaze")
            Log("calcify", Acore::StringFormat("player={} delta={} now={} why={}", player->GetName(), n, now, why));
        if (now >= Tune::kCalcifyMaxStacks)
        {
            Petrify(player, why);
            return 0;
        }
        return now;
    }

    // AS5: the statue: the stacks go, the 2 s stun, the 6 yd circle of the crack's shrapnel (6 stacks).
    void Petrify(Player* player, char const* why)
    {
        player->RemoveAurasDueToSpell(SPELL_AS_CALCIFY);
        me->CastSpell(player, SPELL_AS_PETRIFIED, true);
        bool const heroic = Heroic();
        float const pct = ShatterPct(Tune::kCalcifyMaxStacks, heroic);
        MechanicRef ref = Mechanic::Circle(me, player, Tune::kShatterRadius, Milliseconds(Tune::kPetrifyMs));
        ref.Damage(pct).TankDamage(pct).Spell(SPELL_AS_SHATTER).Within(AntusulFloorBounds()).Tag(TAG_PETRIFY);
        if (Tune::kStoneDustStacks(heroic))
            ref.OnHit(OnStoneDust());
        Track(ref.Handle());
        _statues.push_back({ player->GetGUID(), _timeline.now + Tune::kPetrifyMs });
        Log("petrify", Acore::StringFormat("player={} why={} shrapnel={:.0f} tank={} heroic={}", player->GetName(),
            why, pct, me->GetVictim() == player ? 1 : 0, heroic ? 1 : 0));
    }

    // The crack, 2 s after the petrify: the hit on the statue; heroic, a crack within reach of him strips Stoneflesh.
    void UpdateStatues()
    {
        std::vector<ObjectGuid> due;
        for (auto it = _statues.begin(); it != _statues.end();)
        {
            if (_timeline.now < it->crackAt)
            {
                ++it;
                continue;
            }
            due.push_back(it->player);
            it = _statues.erase(it);
        }
        for (ObjectGuid const& guid : due)
            Crack(ObjectAccessor::GetPlayer(*me, guid));
    }

    void Crack(Player* player)
    {
        if (!player)
            return;
        player->RemoveAurasDueToSpell(SPELL_AS_PETRIFIED);
        if (!player->IsAlive())
            return;
        bool const heroic = Heroic();
        DungeonKit::RegistryHitSpec spec;
        spec.pct = Tune::kCrackPct(heroic);
        spec.tankPct = Tune::kCrackPct(heroic);
        spec.school = kSchoolPhysical;
        spec.spellId = SPELL_AS_CRACK;
        spec.weakened = false;      // the 2 s stun is the cost (SP AS5)
        spec.tag = TAG_CRACK;
        Track(DungeonKit::RegistryHit(me, GuidSet{ player->GetGUID() }, spec));
        float const dist = me->GetExactDist2d(player);
        uint32 stoneflesh = DungeonKit::Stacks(me, SPELL_AS_STONEFLESH);
        bool stripped = false;
        if (heroic && stoneflesh && CrackReachesHim(dist, me->GetCombatReach()))
        {
            stoneflesh = DungeonKit::AddStacks(me, SPELL_AS_STONEFLESH, -1, me, Tune::kStonefleshStacks);
            stripped = true;
            if (!stoneflesh)
                StopStonefleshStack();
        }
        Log("crack", Acore::StringFormat("player={} pct={:.0f} distance={:.1f} stripped={} stoneflesh={}",
            player->GetName(), spec.pct, dist, stripped ? 1 : 0, stoneflesh));
    }

    // ---- AS7 Shatter ---------------------------------------------------------------------------------------------

    // A player dispelled Calcify (spell_zf_antusul_calcify took every stack at once).
    void OnCalcifyDispelled(Player* carrier, uint32 stacks, Unit* dispeller)
    {
        if (!carrier)
            return;
        if (!_engaged)
        {
            Log("shatter-skipped", Acore::StringFormat("player={} stacks={} (not engaged)", carrier->GetName(),
                stacks));
            return;
        }
        Shatter(carrier, stacks, "dispel", dispeller);
    }

    // The shrapnel of `stacks` on everyone within 6 yd of the carrier (never the carrier: a circle anchored on a
    // player never hits that player).
    void Shatter(Player* carrier, uint32 stacks, char const* why, Unit* dispeller = nullptr)
    {
        if (!carrier || !stacks)
            return;
        bool const heroic = Heroic();
        float const pct = ShatterPct(stacks, heroic);
        MechanicRef ref = Mechanic::Circle(me, carrier, Tune::kShatterRadius, Milliseconds(Tune::kShatterWarnMs));
        ref.Damage(pct).TankDamage(pct).Spell(SPELL_AS_SHATTER).Within(AntusulFloorBounds()).Tag(TAG_SHATTER);
        if (ShatterWeakened(stacks))
            ref.Weakened();
        if (Tune::kStoneDustStacks(heroic))
            ref.OnHit(OnStoneDust());
        Track(ref.Handle());
        // The self-cure gap (Maleki's X1): a bot curing itself skips DispelEntry::when; `self` and `near` measure it.
        uint32 near = 0;
        for (Player* p : FloorPlayers())
            if (p != carrier && p->GetExactDist2d(carrier) <= Tune::kShatterRadius)
                ++near;
        Log("shatter", Acore::StringFormat("carrier={} stacks={} pct={:.0f} why={} by={} self={} near={} heroic={}",
            carrier->GetName(), stacks, pct, why, dispeller ? dispeller->GetName() : std::string("-"),
            dispeller == carrier ? 1 : 0, near, heroic ? 1 : 0));
    }

    // Heroic stone dust: everyone the shrapnel hits gains 2 Calcify, on his next tick (never inside the registry's
    // resolve: a sixth stack would petrify and register a circle there). Captures the map and guid only.
    std::function<void(Unit*)> OnStoneDust()
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid](Unit* hit)
        {
            Player* player = hit ? hit->ToPlayer() : nullptr;
            Creature* antusul = map ? map->GetCreature(guid) : nullptr;
            if (!player || !antusul || !antusul->IsAlive() || !antusul->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_antusul_rework*>(antusul->AI()))
                ai->_dust.push_back(player->GetGUID());
        };
    }

    void ApplyStoneDust()
    {
        if (_dust.empty())
            return;
        std::vector<ObjectGuid> const dust = std::move(_dust);
        _dust.clear();
        uint32 const stacks = Tune::kStoneDustStacks(Heroic());
        for (ObjectGuid const& guid : dust)
            AddCalcify(ObjectAccessor::GetPlayer(*me, guid), stacks, "dust");
    }

    // ---- AS1 Servants, AS2 the gaze ------------------------------------------------------------------------------

    struct ServantState
    {
        ObjectGuid servant;
        ObjectGuid target;
        GazeClock clock;
    };

    // `forced`: a `.dbtest` rise (the grid stays). False: the cap, or no free point.
    bool RiseServant(bool forced)
    {
        if (!forced)
            _timeline.RiseDone(Heroic());
        PruneServants();
        if (_servants.size() >= Tune::kServantCap)
        {
            Log("rise-skip", Acore::StringFormat("alive={} (the cap)", _servants.size()));
            return false;
        }
        std::vector<Vec2> points;
        for (Point3 const& p : kServantRisePoints)
            points.push_back(p.XY());
        std::vector<Vec2> taken;
        for (ServantState const& s : _servants)
            if (Creature* servant = me->GetMap()->GetCreature(s.servant))
                taken.push_back(DungeonKit::PlaneOf(servant));
        std::optional<std::size_t> const pick = PickRisePoint(points, taken, DungeonKit::PlaneOf(me), RandBelow);
        if (!pick)
        {
            Log("rise-skip", "no free point");
            return false;
        }
        Point3 const& at = kServantRisePoints[*pick];
        float const z = FloorZ(me, at.x, at.y, at.z);
        float const facing = DungeonKit::BearingTo(at.XY(), DungeonKit::PlaneOf(me));
        Creature* servant = me->SummonCreature(NPC_ANTUSUL_SERVANT, at.x, at.y, z, facing,
            TEMPSUMMON_CORPSE_TIMED_DESPAWN, Tune::kServantCorpseMs);
        if (!servant)
        {
            Log("rise-fail", Acore::StringFormat("point={}", *pick));
            return false;
        }
        servant->CastSpell(servant, SPELL_AS_SERVANT_RISE, true);
        _servants.push_back({ servant->GetGUID(), ObjectGuid::Empty, GazeClock{} });
        ++_rises;
        if (!_broodYelled && _servants.size() >= Tune::kServantCap)
        {
            Talk(YELL_BROOD);
            _broodYelled = true;
        }
        else if (_rises > 1)
            Talk(YELL_RISE);
        Log("rise", Acore::StringFormat("point={} at=({:.1f}, {:.1f}, {:.1f}) alive={} rises={} forced={}", *pick,
            at.x, at.y, z, _servants.size(), _rises, forced ? 1 : 0));
        return true;
    }

    void PruneServants()
    {
        std::erase_if(_servants, [this](ServantState const& s)
        {
            Creature* servant = me->GetMap()->GetCreature(s.servant);
            return !servant || !servant->IsAlive();
        });
    }

    void UpdateServants(uint32 diff)
    {
        bool const heroic = Heroic();
        for (std::size_t i = 0; i < _servants.size(); ++i)
        {
            ServantState& s = _servants[i];
            Creature* servant = me->GetMap()->GetCreature(s.servant);
            if (!servant || !servant->IsAlive())
            {
                if (s.clock.stage == GazeStage::Gaze)
                    EndGaze(s, servant, "servant dead");
                continue;
            }
            if (ServantHeld(servant))
            {
                if (s.clock.stage == GazeStage::Gaze)
                    EndGaze(s, servant, "held");
                s.clock.Held();
                continue;
            }
            if (s.clock.stage == GazeStage::Gaze)
            {
                Player* target = ObjectAccessor::GetPlayer(*me, s.target);
                if (!target || !target->IsAlive() || IsStatue(target) || !_arena.Contains(target))
                {
                    EndGaze(s, servant, "target gone");
                    continue;
                }
                bool ended = false;
                uint32 const laid = s.clock.Tick(diff, heroic, ended);
                for (uint32 n = 0; n < laid; ++n)
                    AddCalcify(target, 1, "gaze");
                if (ended)
                    EndGaze(s, servant, "done");
                continue;
            }
            if (s.clock.Advance(diff))
                StartGaze(s, servant);
        }
        PruneServants();
    }

    void StartGaze(ServantState& s, Creature* servant)
    {
        std::vector<Player*> players = FloorPlayers();
        std::erase_if(players, [](Player* p) { return IsStatue(p); });
        if (players.empty())
        {
            s.clock.waitMs = Tune::kRetryMs;
            return;
        }
        Player* target = players[RandBelow(uint32(players.size()))];
        s.target = target->GetGUID();
        s.clock.Start();
        servant->SetFacingToObject(target);
        SpellCastResult const result = servant->CastSpell(target, SPELL_AS_GAZE, false);
        Log("gaze", Acore::StringFormat("servant={} target={} stacks={} beam={} tank={}", s.servant.GetCounter(),
            target->GetName(), DungeonKit::Stacks(target, SPELL_AS_CALCIFY), uint32(result),
            me->GetVictim() == target ? 1 : 0));
    }

    // The beam stops with the gaze (it is a look; the stacks are the clock's).
    void EndGaze(ServantState& s, Creature* servant, char const* why)
    {
        if (servant)
            if (Spell* channel = servant->GetCurrentSpell(CURRENT_CHANNELED_SPELL))
                if (channel->GetSpellInfo()->Id == SPELL_AS_GAZE && channel->getState() != SPELL_STATE_FINISHED)
                    servant->InterruptSpell(CURRENT_CHANNELED_SPELL, true);
        if (Player* target = ObjectAccessor::GetPlayer(*me, s.target))
            target->RemoveAurasDueToSpell(SPELL_AS_GAZE, s.servant);
        if (std::string(why) != "done")
            Log("gaze-end", Acore::StringFormat("servant={} why={} laid={}", s.servant.GetCounter(), why,
                s.clock.ticks));
        s.target.Clear();
        s.clock.Stop();
    }

    // ---- AS4 Earth Shock -----------------------------------------------------------------------------------------

    void EarthShock()
    {
        Unit* victim = me->GetVictim();
        if (!victim || me->GetExactDist(victim) > Tune::kEarthShockRangeYd + me->GetCombatReach())
        {
            _timeline.EarthShockRetry();
            return;
        }
        _timeline.EarthShockDone(urand(Tune::kEarthShockMinMs, Tune::kEarthShockMaxMs));
        me->CastSpell(victim, SPELL_EARTH_SHOCK, true);
        uint32 const now = AddCalcify(victim->ToPlayer(), Tune::kEarthShockStacks, "earth-shock");
        Log("earth-shock", Acore::StringFormat("target={} stacks={}", victim->GetName(), now));
    }

    // ---- the bars: AS8 Shockwave, AS6 Shatterbolt, AS9 Healing Wave ----------------------------------------------

    bool BarPending() const
    {
        return _bolt.landAt || _shockwaveAt;
    }

    void StartDueBar()
    {
        if (BarPending())
            return;
        bool const heroic = Heroic();
        Bar const bar = _timeline.DueBar();
        switch (bar)
        {
            case Bar::Shockwave:
                StartShockwave();
                _timeline.BarDone(bar, Tune::kShockwaveEveryMs(heroic));
                break;
            case Bar::Bolt:
                if (StartBolt(nullptr))
                    _timeline.BarDone(bar, urand(Tune::kBoltMinMs(heroic), Tune::kBoltMaxMs(heroic)));
                else
                    _timeline.BarRetry(bar);
                break;
            case Bar::Heal:
                if (StartHeal())
                    _timeline.BarDone(bar, urand(Tune::kHealMinMs, Tune::kHealMaxMs));
                else
                    _timeline.BarRetry(bar);
                Mechanic::NoteNextCastIn(me, HealSpell(), Milliseconds(_timeline.InMs(Bar::Heal)));
                break;
            default:
                break;
        }
    }

    // AS8: the bar and the emote; the hit lands at the bar's end (UpdateLandings).
    void StartShockwave()
    {
        DungeonKit::CastBar(me, SPELL_AS_SHOCKWAVE_BAR, nullptr, EMOTE_SHOCKWAVE);
        _shockwaveAt = _timeline.now + Tune::kShockwaveCastMs;
        Log("shockwave-cast", Acore::StringFormat("heroic={}", Heroic() ? 1 : 0));
    }

    // Everyone on his floor, one RegistryHit per Calcify count (the per-stack cut, ShockwaveScriptPct).
    void LandShockwave()
    {
        _shockwaveAt = 0;
        bool const heroic = Heroic();
        me->CastSpell(me, SPELL_AS_SHOCKWAVE_LOOK, true);
        std::map<uint32, GuidSet> byStacks;
        for (Player* p : FloorPlayers())
            byStacks[std::min(DungeonKit::Stacks(p, SPELL_AS_CALCIFY), Tune::kCalcifyMaxStacks)].insert(p->GetGUID());
        std::string detail;
        for (auto const& [stacks, players] : byStacks)
        {
            DungeonKit::RegistryHitSpec spec;
            spec.pct = ShockwaveScriptPct(stacks, heroic);
            spec.tankPct = spec.pct;
            spec.school = kSchoolNature;
            spec.spellId = SPELL_AS_SHOCKWAVE_HIT;
            spec.weakened = false;      // unavoidable
            spec.tag = TAG_SHOCKWAVE;
            Track(DungeonKit::RegistryHit(me, players, spec));
            detail += Acore::StringFormat(" {}x{}={:.0f}%", players.size(), stacks, ShockwaveNetPct(stacks, heroic));
        }
        Log("shockwave", Acore::StringFormat("heroic={}{}", heroic ? 1 : 0, detail));
    }

    // AS6: `forced` (a `.dbtest`), else a random player with Calcify on his floor (anyone if nobody has a stack).
    bool StartBolt(Player* forced)
    {
        Player* target = forced ? forced : PickBoltTarget();
        if (!target)
            return false;
        bool const heroic = Heroic();
        uint32 const cast = Tune::kBoltCastMs(heroic);
        DungeonKit::CastBar(me, heroic ? SPELL_AS_SHATTERBOLT_BAR_H : SPELL_AS_SHATTERBOLT_BAR, nullptr);
        // The warning: a 6 yd circle on the target for the bar (no damage: the shrapnel registers at the landing with
        // the stacks the target has then). The target is never counted (a circle anchored on a player).
        MechanicRef ref = Mechanic::Circle(me, target, Tune::kShatterRadius, Milliseconds(cast));
        ref.Within(AntusulFloorBounds()).Tag(TAG_BOLT);
        Track(ref.Handle());
        _bolt.target = target->GetGUID();
        _bolt.landAt = _timeline.now + cast;
        Log("bolt-cast", Acore::StringFormat("target={} stacks={} tank={} heroic={}", target->GetName(),
            DungeonKit::Stacks(target, SPELL_AS_CALCIFY), me->GetVictim() == target ? 1 : 0, heroic ? 1 : 0));
        return true;
    }

    Player* PickBoltTarget()
    {
        std::vector<Player*> players = FloorPlayers();
        std::erase_if(players, [](Player* p) { return IsStatue(p); });
        std::vector<Player*> stone;
        for (Player* p : players)
            if (DungeonKit::Stacks(p, SPELL_AS_CALCIFY))
                stone.push_back(p);
        std::vector<Player*> const& pool = stone.empty() ? players : stone;
        return pool.empty() ? nullptr : pool[RandBelow(uint32(pool.size()))];
    }

    // The bolt lands: its hit on the target (cut by the target's stone here: the stacks go before the registry lands
    // it), then the stacks shatter.
    void LandBolt()
    {
        ObjectGuid const guid = _bolt.target;
        _bolt = BoltState{};
        Player* target = ObjectAccessor::GetPlayer(*me, guid);
        if (!target || !target->IsAlive() || !target->IsInWorld())
        {
            Log("bolt-miss", "target gone");
            return;
        }
        bool const heroic = Heroic();
        uint32 const stacks = DungeonKit::Stacks(target, SPELL_AS_CALCIFY);
        me->CastSpell(target, SPELL_AS_SHATTERBOLT_LOOK, true);
        DungeonKit::RegistryHitSpec spec;
        spec.pct = BoltPct(stacks, heroic);
        spec.tankPct = spec.pct;
        spec.school = kSchoolNature;
        spec.spellId = SPELL_AS_SHATTERBOLT_HIT;
        spec.weakened = false;      // no penalty on the target (SP AS6)
        spec.tag = TAG_BOLT_HIT;
        Track(DungeonKit::RegistryHit(me, GuidSet{ guid }, spec));
        Log("bolt", Acore::StringFormat("target={} stacks={} pct={:.1f}", target->GetName(), stacks, spec.pct));
        if (stacks)
        {
            target->RemoveAurasDueToSpell(SPELL_AS_CALCIFY);
            Shatter(target, stacks, "bolt");
        }
    }

    // AS9: a real cast (kickable); the amount is set at its start.
    bool StartHeal()
    {
        bool const heroic = Heroic();
        uint32 const amount = PctOf(me->GetMaxHealth(), Tune::kHealPct(heroic));
        SpellCastResult const result = me->CastCustomSpell(HealSpell(), SPELLVALUE_BASE_POINT0, int32(amount), me,
            false);
        if (result != SPELL_CAST_OK)
        {
            Log("heal-fail", Acore::StringFormat("result={} (a locked Nature school after a kick refuses it)",
                uint32(result)));
            return false;
        }
        Log("heal", Acore::StringFormat("amount={} health={} heroic={}", amount, me->GetHealth(), heroic ? 1 : 0));
        return true;
    }

    uint32 HealSpell() const
    {
        return Heroic() ? SPELL_AS_HEALING_WAVE_H : SPELL_AS_HEALING_WAVE;
    }

    void UpdateLandings()
    {
        if (_shockwaveAt && _timeline.now >= _shockwaveAt)
            LandShockwave();
        if (_bolt.landAt && _timeline.now >= _bolt.landAt)
            LandBolt();
    }

    // ---- AS10 Stoneflesh (heroic) --------------------------------------------------------------------------------

    // Bots: a carrier at 5+ Calcify walks to him (the tank stands there anyway). Hidden from players (they read their
    // own stacks); judged every second, no damage.
    void RegisterStonefleshStack()
    {
        StopStonefleshStack();
        if (!DungeonKit::Stacks(me, SPELL_AS_STONEFLESH))
            return;
        BossMechanics::Eligibility carriers;
        carriers.auraSpell = SPELL_AS_CALCIFY;
        carriers.minStacks = Tune::kStonefleshCarrierStacks;
        carriers.playersOnly = true;
        MechanicRef ref = Mechanic::Stack(me, me, me->GetCombatReach() + Tune::kStonefleshStackYd,
            Milliseconds(Tune::kStonefleshStackWarnMs));
        ref.Persistent(Milliseconds(Tune::kStonefleshStackBlockMs), Milliseconds(Tune::kStonefleshStackTickMs))
            .Eligible(carriers).NoTelegraph().Within(AntusulFloorBounds()).Tag(TAG_STONEFLESH);
        _stonefleshStack = ref.Handle();
        _stonefleshStackMs = 0;
    }

    void StopStonefleshStack()
    {
        if (_stonefleshStack)
            Mechanic::Cancel(me, _stonefleshStack);
        _stonefleshStack = {};
        _stonefleshStackMs = 0;
    }

    // A block is renewed a tick before it ends, while he still has a stack.
    void UpdateStonefleshStack(uint32 diff)
    {
        if (!_stonefleshStack)
            return;
        _stonefleshStackMs += diff;
        if (_stonefleshStackMs + Tune::kStonefleshStackTickMs >= Tune::kStonefleshStackWarnMs
            + Tune::kStonefleshStackBlockMs)
            RegisterStonefleshStack();
    }

    // ---- `.dbtest zf antusul` entry points -----------------------------------------------------------------------

    bool Engaged() const
    {
        return _engaged;
    }

    bool CastingNow() const
    {
        return me->HasUnitState(UNIT_STATE_CASTING) || BarPending();
    }

    bool TestWake()
    {
        return Wake("dbtest");
    }

    bool TestRise()
    {
        return RiseServant(true);
    }

    uint32 TestCalcify(Player* target, uint32 n)
    {
        return AddCalcify(target, n, "test");
    }

    // A dispel's shatter on demand: the target's stacks (at least one) burst as if dispelled.
    void TestShatter(Player* target)
    {
        uint32 const stacks = std::max<uint32>(1, DungeonKit::Stacks(target, SPELL_AS_CALCIFY));
        target->RemoveAurasDueToSpell(SPELL_AS_CALCIFY);
        Shatter(target, stacks, "test", target);
    }

    bool TestBolt(Player* target)
    {
        return StartBolt(target);
    }

    void TestShockwave()
    {
        StartShockwave();
    }

    bool TestHeal()
    {
        return StartHeal();
    }

    void TestPetrify(Player* target)
    {
        Petrify(target, "test");
    }

    std::string TestState()
    {
        std::string out = Acore::StringFormat("engaged={} heroic={} t={}ms next rise/shock/bolt/heal/wave="
            "{}/{}/{}/{}/{}ms servants={} rises={} statues={} stoneflesh={} bolt={} wave={}", _engaged ? 1 : 0,
            _heroic ? 1 : 0, _timeline.now, _timeline.nextRise, _timeline.nextEarthShock, _timeline.nextBolt,
            _timeline.nextHeal, _timeline.nextShockwave, _servants.size(), _rises, _statues.size(),
            DungeonKit::Stacks(me, SPELL_AS_STONEFLESH), _bolt.landAt, _shockwaveAt);
        for (ServantState const& s : _servants)
        {
            Player* target = ObjectAccessor::GetPlayer(*me, s.target);
            out += Acore::StringFormat("\n  servant {}: {} {}", s.servant.GetCounter(),
                s.clock.stage == GazeStage::Gaze ? "gazing at" : "waiting", target ? target->GetName() : "-");
        }
        for (Player* p : FloorPlayers())
            out += Acore::StringFormat("\n  {}: calcify {} statue {}", p->GetName(),
                DungeonKit::Stacks(p, SPELL_AS_CALCIFY), IsStatue(p) ? 1 : 0);
        return out;
    }

private:
    struct Statue
    {
        ObjectGuid player;
        uint32 crackAt = 0;
    };

    struct BoltState
    {
        ObjectGuid target;
        uint32 landAt = 0;          // 0: no bolt in the air
    };

    bool Heroic() const
    {
        return _engaged ? _heroic : DungeonKit::IsHeroicMap(me);
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

    // The players of his floor: alive, in the world, not GMs, on DenArena with its z band (rule 5: every pick and
    // hit; a corpse runner is never picked).
    std::vector<Player*> FloorPlayers()
    {
        std::vector<Player*> out;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player || !player->IsAlive() || player->IsGameMaster() || !player->IsInWorld())
                continue;
            if (!_arena.Contains(player))
                continue;
            out.push_back(player);
        }
        return out;
    }

    // Boss data (SP "Boss data", section 7 #9 A): kick Healing Wave; cure Calcify only on a lone carrier at 4+ stacks
    // (heroic: never the tank while he has Stoneflesh); Servants first.
    void Describe()
    {
        using BossMechanics::Condition;
        BossMechanics::Descriptor d;
        d.interrupts.emplace_back(NPC_ANTUSUL, HealSpell(), Tune::kHealKickPriority, Milliseconds(Tune::kHealMinMs));
        std::vector<Condition> when;
        when.push_back(Condition::Not(Condition::NearPlayer(Tune::kDispelSpacingYd)));
        when.push_back(Condition::Custom([](Unit const* unit)
        {
            return unit && DungeonKit::Stacks(unit, SPELL_AS_CALCIFY) >= Tune::kDispelMinStacks;
        }));
        if (_heroic)
        {
            // Captures his guid only (Condition::Custom's contract), resolved through the carrier's map.
            ObjectGuid const guid = me->GetGUID();
            when.push_back(Condition::Custom([guid](Unit const* unit)
            {
                if (!unit)
                    return false;
                Creature* antusul = ObjectAccessor::GetCreature(*unit, guid);
                if (!antusul || !antusul->HasAura(SPELL_AS_STONEFLESH))
                    return true;
                return antusul->GetVictim() != unit;
            }));
        }
        d.dispels.emplace_back(SPELL_AS_CALCIFY, Tune::kDispelPriority, false, Milliseconds(0),
            Condition::AllOf(std::move(when)));
        d.targets.push_back(BossMechanics::TargetEntry(NPC_ANTUSUL_SERVANT, Tune::kServantTargetPriority,
            BossMechanics::Who::Dps));
        Mechanic::Describe(me, std::move(d));
        Mechanic::NoteNextCastIn(me, HealSpell(), Milliseconds(Tune::kHealFirstMs));
    }

    // The pull's state, gone (RB-1): every mechanic, the Servants and their beams, the statues, every aura of the
    // fight on the players and his Stoneflesh, the clock and the latches.
    void Cleanup()
    {
        for (ServantState& s : _servants)
            if (s.clock.stage == GazeStage::Gaze)
                EndGaze(s, me->GetMap()->GetCreature(s.servant), "cleanup");
        _servants.clear();
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        StopStonefleshStack();
        summons.DespawnAll();
        _statues.clear();
        _dust.clear();
        _bolt = BoltState{};
        _shockwaveAt = 0;
        _timeline = Timeline{};
        _rises = 0;
        _broodYelled = false;
        _engaged = false;
        _arena.Reset();
        me->RemoveAurasDueToSpell(SPELL_AS_STONEFLESH);
        if (instance)
            for (uint32 spell : { uint32(SPELL_AS_CALCIFY), uint32(SPELL_AS_PETRIFIED), uint32(SPELL_AS_GAZE) })
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
    }

    DungeonKit::ArenaGuard _arena;
    Timeline _timeline;
    std::vector<ServantState> _servants;
    std::vector<Statue> _statues;
    std::vector<ObjectGuid> _dust;
    std::vector<MechanicHandle> _live;
    BoltState _bolt;
    uint32 _shockwaveAt = 0;        // 0: no Shockwave bar running
    MechanicHandle _stonefleshStack;
    uint32 _stonefleshStackMs = 0;
    uint32 _rises = 0;
    bool _broodYelled = false;
    bool _heroic = false;
    bool _engaged = false;
};

// Servant of Antu'sul 8156 (no spawn: Antu'sul's summons). Stationary, passive, no melee: a kill target. Antu'sul's AI
// runs its gaze (UpdateServants); a stun, fear or polymorph on it stops the gaze there.
struct npc_antusul_servant_rework : public ScriptedAI
{
    explicit npc_antusul_servant_rework(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
        me->SetControlled(true, UNIT_STATE_ROOT);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }

    // Nobody left to fight: it goes (despawns on reset, SP Build spec).
    void EnterEvadeMode(EvadeReason /*why*/) override
    {
        me->DespawnOrUnsummon();
    }

    void UpdateAI(uint32 /*diff*/) override { }
};

// AS3 Calcify 213890: a dispel takes every stack at once (stock removes one) and shatters them (AS7) around the
// carrier. A bolt, a petrify, the 30 s running out, a death or a class immunity remove it without a dispel, so without
// this.
class spell_zf_antusul_calcify : public AuraScript
{
    PrepareAuraScript(spell_zf_antusul_calcify);

    void TakeEveryStack(DispelInfo* dispelInfo)
    {
        _stacks = GetStackAmount();
        dispelInfo->SetRemovedCharges(std::max<uint8>(1, _stacks));
    }

    void ShatterOnDispel(DispelInfo* dispelInfo)
    {
        Player* carrier = GetUnitOwner() ? GetUnitOwner()->ToPlayer() : nullptr;
        Creature* antusul = GetCaster() ? GetCaster()->ToCreature() : nullptr;
        if (!carrier || !antusul || !antusul->IsAlive() || !antusul->IsAIEnabled)
            return;
        if (auto* ai = dynamic_cast<boss_antusul_rework*>(antusul->AI()))
            ai->OnCalcifyDispelled(carrier, _stacks, dispelInfo->GetDispeller());
    }

    void Register() override
    {
        OnDispel += AuraDispelFn(spell_zf_antusul_calcify::TakeEveryStack);
        AfterDispel += AuraDispelFn(spell_zf_antusul_calcify::ShatterOnDispel);
    }

    uint8 _stacks = 0;
};

namespace
{
    boss_antusul_rework* FindAntusulAI(ChatHandler* handler)
    {
        Creature* boss = ZfTest::FindBoss(handler, NPC_ANTUSUL);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_antusul_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Antu'sul is not running boss_antusul_rework (check the ScriptName).");
        return ai;
    }

    // The engaged AI, else an error (the mechanics run on the fight's clock).
    boss_antusul_rework* EngagedAI(ChatHandler* handler)
    {
        boss_antusul_rework* ai = FindAntusulAI(handler);
        if (ai && !ai->Engaged())
        {
            handler->SendErrorMessage("{}", "Antu'sul must be in combat (`.dbtest zf antusul wake`, or pull him).");
            return nullptr;
        }
        return ai;
    }

    // The selected player, else the GM.
    Player* TestTarget(ChatHandler* handler)
    {
        if (Player* selected = handler->getSelectedPlayer())
            return selected;
        return handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return ZfTest::ShowBossInfo(handler, NPC_ANTUSUL, BOSS_ANTUSUL);
    }

    // `.dbtest zf antusul state`: the clock, the Servants and every floor player's Calcify.
    bool HandleState(ChatHandler* handler)
    {
        boss_antusul_rework* ai = FindAntusulAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Antu'sul: {}", ai->TestState());
        return true;
    }

    // `.dbtest zf antusul wake`: area trigger 1447's SetData(1, 1), as DC's hook sends it (GMs are never his target:
    // `.gm off` first).
    bool HandleWake(ChatHandler* handler)
    {
        boss_antusul_rework* ai = FindAntusulAI(handler);
        if (!ai)
            return false;
        if (!ai->TestWake())
        {
            handler->SendErrorMessage("{}", "Antu'sul did not wake (in combat, evading, dead, or no player within "
                "100 yd: see the log).");
            return false;
        }
        handler->PSendSysMessage("{}", "Antu'sul: awake (SetData(1, 1)).");
        return true;
    }

    // `.dbtest zf antusul rise`: a Servant now (AS1; the cap holds).
    bool HandleRise(ChatHandler* handler)
    {
        boss_antusul_rework* ai = EngagedAI(handler);
        if (!ai)
            return false;
        if (!ai->TestRise())
        {
            handler->SendErrorMessage("{}", "Antu'sul: no Servant (three alive, or no free point).");
            return false;
        }
        handler->PSendSysMessage("{}", "Antu'sul: a Servant rises (AS1).");
        return true;
    }

    // `.dbtest zf antusul calcify [n]`: n Calcify stacks (default 1) on the selected player (or you); a sixth
    // petrifies (AS3, AS5).
    bool HandleCalcify(ChatHandler* handler, Optional<uint32> stacks)
    {
        boss_antusul_rework* ai = EngagedAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        uint32 const n = std::clamp<uint32>(stacks.value_or(1), 1, Tune::kCalcifyMaxStacks);
        uint32 const now = ai->TestCalcify(target, n);
        handler->PSendSysMessage("Antu'sul: Calcify +{} on {}: {} (AS3{}).", n, target->GetName(), now,
            now ? "" : ", AS5 petrified");
        return true;
    }

    // `.dbtest zf antusul shatter`: the selected player's (or your) stacks burst as if dispelled (AS7).
    bool HandleShatter(ChatHandler* handler)
    {
        boss_antusul_rework* ai = EngagedAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        ai->TestShatter(target);
        handler->PSendSysMessage("Antu'sul: Shatter on {} (AS7).", target->GetName());
        return true;
    }

    // `.dbtest zf antusul petrify`: the selected player (or you) turns to stone (AS5; heroic: a crack in reach of him
    // strips Stoneflesh).
    bool HandlePetrify(ChatHandler* handler)
    {
        boss_antusul_rework* ai = EngagedAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        ai->TestPetrify(target);
        handler->PSendSysMessage("Antu'sul: {} petrified (AS5).", target->GetName());
        return true;
    }

    // `.dbtest zf antusul bolt`: Shatterbolt on the selected player (or you) (AS6). He must be free.
    bool HandleBolt(ChatHandler* handler)
    {
        boss_antusul_rework* ai = EngagedAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        if (ai->CastingNow() || !ai->TestBolt(target))
        {
            handler->SendErrorMessage("{}", "Antu'sul is casting (or a bar is landing): try again.");
            return false;
        }
        handler->PSendSysMessage("Antu'sul: Shatterbolt on {} (AS6).", target->GetName());
        return true;
    }

    // `.dbtest zf antusul shockwave`: Earthen Shockwave now (AS8). He must be free.
    bool HandleShockwave(ChatHandler* handler)
    {
        boss_antusul_rework* ai = EngagedAI(handler);
        if (!ai)
            return false;
        if (ai->CastingNow())
        {
            handler->SendErrorMessage("{}", "Antu'sul is casting (or a bar is landing): try again.");
            return false;
        }
        ai->TestShockwave();
        handler->PSendSysMessage("{}", "Antu'sul: Earthen Shockwave (AS8).");
        return true;
    }

    // `.dbtest zf antusul heal`: Healing Wave of Antu'sul now (AS9; kick it). He must be free.
    bool HandleHeal(ChatHandler* handler)
    {
        boss_antusul_rework* ai = EngagedAI(handler);
        if (!ai)
            return false;
        if (ai->CastingNow() || !ai->TestHeal())
        {
            handler->SendErrorMessage("{}", "Antu'sul: the heal was refused (casting, or his Nature school locked).");
            return false;
        }
        handler->PSendSysMessage("{}", "Antu'sul: Healing Wave of Antu'sul (AS9).");
        return true;
    }

    ChatCommandTable const& AntusulTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",      HandleInfo,      SEC_GAMEMASTER, Console::No },
            { "state",     HandleState,     SEC_GAMEMASTER, Console::No },
            { "wake",      HandleWake,      SEC_GAMEMASTER, Console::No },
            { "rise",      HandleRise,      SEC_GAMEMASTER, Console::No },
            { "calcify",   HandleCalcify,   SEC_GAMEMASTER, Console::No },
            { "shatter",   HandleShatter,   SEC_GAMEMASTER, Console::No },
            { "petrify",   HandlePetrify,   SEC_GAMEMASTER, Console::No },
            { "bolt",      HandleBolt,      SEC_GAMEMASTER, Console::No },
            { "shockwave", HandleShockwave, SEC_GAMEMASTER, Console::No },
            { "heal",      HandleHeal,      SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_antusul_rework()
{
    RegisterDungeonReworkCreatureAI(boss_antusul_rework, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_antusul_servant_rework, ZulFarrakRework::kInstanceScriptName);
    RegisterSpellScript(spell_zf_antusul_calcify);
    ZfTest::RegisterBoss("antusul", AntusulTestCommands());
}
