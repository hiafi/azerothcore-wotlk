/*
 * mod-dungeon-bosses, Deadmines: Captain Greenskin and the harpoon rope (WP-B7). Build spec: DM 'Captain Greenskin'
 * Build spec GS1-GS5 (docs/dungeons/deadmines-rework.md); handoff .agents/plans/deadmines-pilot/
 * deadmines-pilot.HANDOFF.md sections 3.4 (GS rows), 3.5 (B7), 3.8 (the deck frame).
 *
 * Replaces SmartAI 647 (stock: Cleave 40505 and Poisoned Harpoon 5208); the patrol (path 793330) and the two formation
 * followers (79334, 79335) stay as data.
 *
 *   GS1 Cleave              stock 40505 on the victim, 1 to 7 s, then every 10 to 15 s
 *   GS2 Fire on My Mark     yell 0 + cast bar, 4 lanes rail to rail on the deck frame (GreenskinLanes::Fire), 2 s,
 *                           40% + Weakened; 8 s, then every 20 s
 *   GS3 Crossfire (H)       with GS2: 2 lanes bow to stern, both axes marked 2.5 s; once per player per volley
 *   GS4 Burning crossing (H) every crossing burns 20 s, 10% Fire per second
 *   GS5 Reel 'Em In         2 s interruptible cast on a random non-tank >= 10 yd (H: two players), emote 1; on the hit
 *                           the stock poison (5208's aura), a rope beam, a click object at the rope's midpoint and a
 *                           RunOut 25 measured from him; after 4 s a target still within 25 yd is hit for 30% +
 *                           Weakened and pulled to his feet (yell 2). Outs: 25 yd away, another player standing on the
 *                           rope 1 s, or a click on the rope object. 12 s, then every 20 s.
 *
 * Also here: GreenskinLanes::Fire / ForgetOwner (GreenskinLanes.h, shared with VanCleef's VC3) and the lane hit's
 * once-per-volley SpellScript, spell_dm_greenskin_lane_hit.
 */

#include "Chat.h"
#include "Creature.h"
#include "DeadminesKit.h"
#include "DeadminesTestCommand.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "GameTime.h"
#include "GreenskinLanes.h"
#include "GreenskinLogic.h"
#include "Log.h"
#include "Map.h"
#include "MotionMaster.h"
#include "MovementTypedefs.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptMgr.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "TemporarySummon.h"
#include <cmath>
#include <list>
#include <mutex>
#include <vector>

using namespace Acore::ChatCommands;
using namespace DeadminesRework;
using namespace Greenskin;

namespace
{
    constexpr char const* kLog = "module.dungeonbosses";

    enum GreenskinEvents : uint32
    {
        EVENT_CLEAVE            = 1,
        EVENT_FIRE_ON_MY_MARK   = 2,
        EVENT_REEL_EM_IN        = 3,
    };

    // DoAction / SetGUID ids (the rope object, the registry's OnHit, `.dmtest greenskin`).
    enum GreenskinActions : int32
    {
        ACTION_REELED           = 1,    // SetGUID(player): the RunOut hit him, reel him in
        ACTION_ROPE_CLICKED     = 2,    // SetGUID(rope object): someone clicked it
        ACTION_TEST_REEL        = 3,    // SetGUID(player): rope him now, no cast (.dmtest greenskin reel)
        ACTION_TEST_VOLLEY      = 4,    // DoAction: this map's volley now (.dmtest greenskin volley)
        ACTION_TEST_CROSSFIRE   = 5,    // DoAction: the heroic volley now, any difficulty (.dmtest greenskin crossfire)
        ACTION_TEST_HARPOON     = 6,    // DoAction: the full Reel 'Em In cast now (.dmtest greenskin harpoon)
    };

    // The rope object lives at most this long (it is removed with its rope; this is the safety net).
    constexpr uint32 kRopeObjectLifeSec = (kRopeMs + kRopeCleanupMs) / 1000 + 3;
    constexpr float kReelSpeedXY = 25.f;
    constexpr float kRopeStandZYd = 6.f;      // standing on the rope: on the same deck level

    // The once-per-volley memory of every owner on every map (map threads run in parallel: one lock).
    std::mutex sVolleyLock;
    Greenskin::VolleyMemory sVolleys;

    uint64 NowMs()
    {
        return static_cast<uint64>(GameTime::GetGameTimeMS().count());
    }

    Vec2 PlaneOf(WorldObject const* o)
    {
        return { o->GetPositionX(), o->GetPositionY() };
    }
}

// ------------------------------------------------------------------------------------------------------------------
// GreenskinLanes (GreenskinLanes.h)
// ------------------------------------------------------------------------------------------------------------------
namespace GreenskinLanes
{
    Volley Fire(Unit* owner, Greenskin::LaneVolley const& spec)
    {
        Volley out;
        if (!owner || !owner->IsInWorld() || !spec.Lanes())
            return out;
        Map* map = owner->GetMap();
        Milliseconds const warn(spec.warnMs);
        {
            BossMechanics::LaneBuilder lanes = Mechanic::RoomFrame(owner, DeadminesKit::DeckFrame());
            out.laneSet = lanes.Id();
            if (spec.across)
                lanes.Lanes(BossMechanics::Axis::Y, { spec.across, spec.width, spec.minGap }, warn);
            if (spec.along)
                lanes.Lanes(BossMechanics::Axis::X, { spec.along, spec.width, spec.minGap }, warn);

            BossMechanics::Registry const* reg = BossMechanics::Registry::Get(map);
            if (BossMechanics::LaneSet const* set = reg ? reg->FindLaneSet(lanes.Id()) : nullptr)
            {
                std::vector<uint32> const ids = set->lanes;
                std::vector<BossMechanics::LaneRect> const rects = set->rects;
                for (std::size_t i = 0; i < ids.size() && i < rects.size(); ++i)
                {
                    bool const acrossLane = rects[i].axis == BossMechanics::Axis::Y;
                    BossMechanics::MechanicRef lane(map, ids[i], false);    // the builder commits it
                    lane.Damage(spec.lanePct).Weakened()
                        .Spell(acrossLane ? SPELL_FIRE_ON_MY_MARK_HIT : SPELL_CROSSFIRE_HIT)
                        .Tag(acrossLane ? spec.acrossTag : spec.alongTag);
                    (acrossLane ? out.across : out.along).push_back({ ids[i] });
                }
            }

            if (spec.Crossings())
            {
                lanes.BurnCrossings(Milliseconds(spec.burnMs), Milliseconds(spec.burnTickMs), spec.burnPct);
                if (BossMechanics::LaneSet const* set = reg ? reg->FindLaneSet(lanes.Id()) : nullptr)
                {
                    std::vector<uint32> const cells = set->cells;
                    for (uint32 id : cells)
                    {
                        BossMechanics::MechanicRef cell(map, id, false);
                        cell.School(SPELL_SCHOOL_FIRE).Spell(SPELL_BURNING_DECK).Rider(SPELL_DM_STANDING_IN_IT)
                            .Tag(spec.cellTag);
                        out.cells.push_back({ id });
                    }
                }
            }
        }   // the builder commits every lane and cell here
        return out;
    }

    void ForgetOwner(Unit const* owner)
    {
        if (!owner)
            return;
        std::lock_guard<std::mutex> guard(sVolleyLock);
        sVolleys.Forget(owner->GetGUID().GetRawValue());
    }
}

// 205340 Fire on My Mark, 205341 Crossfire (with spell_boss_mechanics_resolve): a unit an earlier lane of the same
// volley already hit is dropped from this lane's targets (ruling 15: "a player where two lanes cross is hit once per
// volley"). The registry casts every lane of a volley on one tick, each cast hitting inside its CastSpell call, with
// the volley's owner as the original caster; the memory is keyed by that owner (Greenskin, or VanCleef for VC3).
class spell_dm_greenskin_lane_hit : public SpellScript
{
    PrepareSpellScript(spell_dm_greenskin_lane_hit);

    uint64 OwnerKey()
    {
        Unit* owner = GetOriginalCaster();
        return owner ? owner->GetGUID().GetRawValue() : 0;
    }

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        uint64 const owner = OwnerKey();
        if (!owner)
            return;
        uint64 const now = NowMs();
        std::lock_guard<std::mutex> guard(sVolleyLock);
        targets.remove_if([owner, now](WorldObject* obj)
        {
            return obj && sVolleys.AlreadyHit(owner, obj->GetGUID().GetRawValue(), now);
        });
    }

    void RecordHit()
    {
        uint64 const owner = OwnerKey();
        Unit* target = GetHitUnit();
        if (!owner || !target)
            return;
        std::lock_guard<std::mutex> guard(sVolleyLock);
        sVolleys.Record(owner, target->GetGUID().GetRawValue(), NowMs());
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_dm_greenskin_lane_hit::FilterTargets, EFFECT_0,
            TARGET_UNIT_SRC_AREA_ENEMY);
        AfterHit += SpellHitFn(spell_dm_greenskin_lane_hit::RecordHit);
    }
};

// Captain Greenskin 647
struct boss_captain_greenskin_rework : public BossAI
{
    explicit boss_captain_greenskin_rework(Creature* creature) : BossAI(creature, BOSS_CAPTAIN_GREENSKIN) { }

    struct Rope
    {
        ObjectGuid target;
        ObjectGuid anchor;                      // the invisible unit channeling the beam (kNpcRopeAnchor)
        ObjectGuid object;                      // the click object at the midpoint (GO_DM_HARPOON_ROPE)
        BossMechanics::MechanicHandle runOut;
        Vec2 objectAt;
        uint32 ageMs = 0;
        Greenskin::RopeStanders standers;
        bool done = false;
    };

    void Reset() override
    {
        ClearRopes();
        _Reset();
        GreenskinLanes::ForgetOwner(me);
        _reelYellCooldownMs = 0;
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        Talk(YELL_GREENSKIN_AGGRO);

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_CAPTAIN_GREENSKIN;
        Mechanic::BeginEncounter(me, options);

        // Kill order: Greenskin (the boss rule). No interrupt list (Reel 'Em In's cast is a reward); the harpoon's
        // poison is the healers' Poison dispel.
        BossMechanics::Descriptor descriptor;
        descriptor.dispels.emplace_back(SPELL_POISONED_HARPOON, 1);
        Mechanic::Describe(me, std::move(descriptor));

        events.ScheduleEvent(EVENT_CLEAVE, Milliseconds(kCleaveFirstMinMs), Milliseconds(kCleaveFirstMaxMs));
        events.ScheduleEvent(EVENT_FIRE_ON_MY_MARK, Milliseconds(kFireFirstMs));
        events.ScheduleEvent(EVENT_REEL_EM_IN, Milliseconds(kReelFirstMs));
        LOG_INFO(kLog, "dm-pilot greenskin engage heroic={}", DeadminesKit::IsHeroicMap(me));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        ClearRopes();
        GreenskinLanes::ForgetOwner(me);
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        ClearRopes();
        GreenskinLanes::ForgetOwner(me);
        BossAI::JustDied(killer);
        LOG_INFO(kLog, "dm-pilot greenskin died");
    }

    void JustSummoned(Creature* summon) override
    {
        if (summon->GetEntry() == kNpcRopeAnchor)
        {
            // Not a combatant: never zoned into combat; it follows him and channels the rope.
            summons.Summon(summon);
            summon->SetReactState(REACT_PASSIVE);
            return;
        }
        BossAI::JustSummoned(summon);
    }

    void SpellHitTarget(Unit* target, SpellInfo const* spell) override
    {
        if (!spell || spell->Id != SPELL_REEL_EM_IN)
            return;
        // The harpoon landed (the cast was not interrupted): rope every target picked for it.
        std::vector<ObjectGuid> const pending = std::move(_pendingHarpoon);
        _pendingHarpoon.clear();
        for (ObjectGuid const& guid : pending)
            if (Player* player = ObjectAccessor::GetPlayer(*me, guid))
                StartRope(player);
        if (pending.empty() && target && target->IsPlayer())
            StartRope(target->ToPlayer());
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (spell && spell->Id == SPELL_REEL_EM_IN && !_pendingHarpoon.empty())
        {
            LOG_INFO(kLog, "dm-pilot greenskin reel-em-in interrupted targets={}", _pendingHarpoon.size());
            _pendingHarpoon.clear();
        }
    }

    void SetGUID(ObjectGuid const& guid, int32 id) override
    {
        switch (id)
        {
            case ACTION_REELED:
                Reel(guid);
                break;
            case ACTION_ROPE_CLICKED:
                for (Rope& rope : _ropes)
                {
                    if (rope.done || rope.object != guid)
                        continue;
                    Mechanic::Cancel(me, rope.runOut);
                    EndRope(rope, RopeEnd::Clicked);
                }
                break;
            case ACTION_TEST_REEL:
                if (Player* player = ObjectAccessor::GetPlayer(*me, guid))
                    StartRope(player);
                break;
            default:
                break;
        }
    }

    void DoAction(int32 action) override
    {
        switch (action)
        {
            case ACTION_TEST_VOLLEY:
                FireOnMyMark(DeadminesKit::IsHeroicMap(me));
                break;
            case ACTION_TEST_CROSSFIRE:
                FireOnMyMark(true);
                break;
            case ACTION_TEST_HARPOON:
                CastReelEmIn();
                break;
            default:
                break;
        }
    }

    void UpdateAI(uint32 diff) override
    {
        // Ropes run out of combat too (`.dmtest greenskin reel` on a patrolling Greenskin).
        UpdateRopes(diff);
        _reelYellCooldownMs = _reelYellCooldownMs > diff ? _reelYellCooldownMs - diff : 0;

        if (!UpdateVictim())
            return;

        events.Update(diff);
        if (me->IsActionPreventedByCasting())
            return;

        while (uint32 const eventId = events.ExecuteEvent())
        {
            ExecuteEvent(eventId);
            if (me->IsActionPreventedByCasting())
                return;
        }

        DoMeleeAttackIfReady();
    }

    void ExecuteEvent(uint32 eventId) override
    {
        switch (eventId)
        {
            case EVENT_CLEAVE:
                DoCastVictim(SPELL_CLEAVE);
                LOG_INFO(kLog, "dm-pilot greenskin cleave");
                events.ScheduleEvent(EVENT_CLEAVE, Milliseconds(kCleaveMinMs), Milliseconds(kCleaveMaxMs));
                break;
            case EVENT_FIRE_ON_MY_MARK:
                FireOnMyMark(DeadminesKit::IsHeroicMap(me));
                events.ScheduleEvent(EVENT_FIRE_ON_MY_MARK, Milliseconds(kFireEveryMs));
                break;
            case EVENT_REEL_EM_IN:
                events.ScheduleEvent(EVENT_REEL_EM_IN,
                    Milliseconds(CastReelEmIn() ? kReelEveryMs : kRetryNoTargetMs));
                break;
            default:
                break;
        }
    }

private:
    // GS2 (+ GS3, GS4 with `heroic`): yell 0, the cast bar naming it, the lanes.
    void FireOnMyMark(bool heroic)
    {
        DeadminesKit::CastBar(me, heroic ? SPELL_CROSSFIRE_CAST : SPELL_FIRE_ON_MY_MARK_CAST, nullptr,
            YELL_GREENSKIN_FIRE_ON_MY_MARK);
        LaneVolley const spec = kFireOnMyMark(heroic);
        GreenskinLanes::Volley const volley = GreenskinLanes::Fire(me, spec);
        LOG_INFO(kLog, "dm-pilot greenskin fire-on-my-mark heroic={} lanes={} warn={}ms", heroic, volley.across.size(),
            spec.warnMs);
        if (spec.along)
            LOG_INFO(kLog, "dm-pilot greenskin crossfire lanes={}", volley.along.size());
        if (spec.Crossings())
            LOG_INFO(kLog, "dm-pilot greenskin burning-crossings cells={}", volley.cells.size());
    }

    // GS5: pick the targets, emote each, start the 2 s cast on the first. False when nobody can be harpooned.
    bool CastReelEmIn()
    {
        _pendingHarpoon.clear();
        bool const heroic = DeadminesKit::IsHeroicMap(me);
        Unit const* tank = me->GetVictim();
        std::vector<Player*> players;
        std::vector<HarpoonCandidate> candidates;
        auto consider = [&](Player* player)
        {
            if (!player || !player->IsAlive() || !player->IsInWorld()
                || std::find(players.begin(), players.end(), player) != players.end())
                return;
            candidates.push_back({ players.size(), me->GetExactDist2d(player), player == tank });
            players.push_back(player);
        };
        if (me->IsEngaged())
        {
            for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
                if (Unit* victim = ref->GetVictim())
                    consider(victim->ToPlayer());
        }
        else
        {
            // `.dmtest greenskin harpoon` out of combat: everyone on the map
            for (auto const& ref : me->GetMap()->GetPlayers())
                consider(ref.GetSource());
        }

        std::vector<uint64> const picks = PickHarpoonTargets(candidates, kHarpoonCount(heroic),
            [](uint32 n) { return n ? urand(0, n - 1) : 0u; });
        if (picks.empty())
        {
            LOG_INFO(kLog, "dm-pilot greenskin reel-em-in no-target");
            return false;
        }

        Player* first = nullptr;
        for (uint64 index : picks)
        {
            Player* player = players[index];
            _pendingHarpoon.push_back(player->GetGUID());
            if (!first)
                first = player;
        }
        SpellCastResult const result = me->CastSpell(first, SPELL_REEL_EM_IN, false);
        LOG_INFO(kLog, "dm-pilot greenskin reel-em-in cast targets={} result={}", picks.size(),
            static_cast<uint32>(result));
        if (result != SPELL_CAST_OK)
            _pendingHarpoon.clear();
        return true;
    }

    Rope* FindRope(ObjectGuid const& target)
    {
        for (Rope& rope : _ropes)
            if (!rope.done && rope.target == target)
                return &rope;
        return nullptr;
    }

    void StartRope(Player* target)
    {
        if (!target || !target->IsAlive() || FindRope(target->GetGUID()))
            return;
        bool const heroic = DeadminesKit::IsHeroicMap(me);
        // The emote on the hit, not at the cast's start: an interrupted Reel 'Em In announces nothing.
        Talk(EMOTE_GREENSKIN_HARPOON, target);

        // the stock poison (5208's periodic aura; the stock id, so DD scales it on heroic)
        me->AddAura(SPELL_POISONED_HARPOON, target);

        Rope rope;
        rope.target = target->GetGUID();

        // the rope beam: channeled at the target by an invisible unit that follows him
        if (Creature* anchor = me->SummonCreature(kNpcRopeAnchor, me->GetPosition(), TEMPSUMMON_TIMED_DESPAWN,
            kRopeMs + kRopeCleanupMs + 2000))
        {
            anchor->GetMotionMaster()->MoveFollow(me, 0.f, 0.f);
            anchor->CastSpell(target, SPELL_HARPOONED, true);
            rope.anchor = anchor->GetGUID();
        }

        // the click object at the midpoint
        Vec2 const mid = RopeMidpoint(PlaneOf(me), PlaneOf(target));
        rope.object = SummonRopeObject(mid, (me->GetPositionZ() + target->GetPositionZ()) * 0.5f,
            me->GetAngle(target));
        rope.objectAt = mid;

        // the reel: a RunOut 25 measured from him; the registry hits a target still within 25 yd after 4 s, and its
        // OnHit reels him in (guids only in the lambda).
        Map* map = me->GetMap();
        ObjectGuid const ownerGuid = me->GetGUID();
        rope.runOut = Mechanic::RunOut(me, target, kSnapYd, Milliseconds(kRopeMs))
            .From(BossMechanics::MeasuredFrom::Owner).Damage(kReelPct(heroic)).Weakened().Spell(SPELL_REEL_HIT)
            .Tag(TAG_REEL_EM_IN)
            .OnHit([map, ownerGuid](Unit* hit)
            {
                if (!hit || !map)
                    return;
                if (Creature* boss = map->GetCreature(ownerGuid))
                    if (boss->IsAIEnabled && boss->AI())
                        boss->AI()->SetGUID(hit->GetGUID(), ACTION_REELED);
            });

        LOG_INFO(kLog, "dm-pilot greenskin reel-em-in harpoon target={} dist={:.1f} rope={} object={} runout={}",
            target->GetName(), me->GetExactDist2d(target), !rope.anchor.IsEmpty(), !rope.object.IsEmpty(),
            rope.runOut.IsValid());
        _ropes.push_back(std::move(rope));
    }

    ObjectGuid SummonRopeObject(Vec2 at, float z, float angle)
    {
        float ground = me->GetMapHeight(at.x, at.y, z + 2.f);
        if (ground <= INVALID_HEIGHT)
            ground = z;
        GameObject* go = me->SummonGameObject(GO_DM_HARPOON_ROPE, at.x, at.y, ground, angle, 0.f, 0.f,
            std::sin(angle * 0.5f), std::cos(angle * 0.5f), kRopeObjectLifeSec);
        return go ? go->GetGUID() : ObjectGuid::Empty;
    }

    void RemoveRopeObject(Rope& rope)
    {
        if (rope.object.IsEmpty())
            return;
        if (GameObject* go = ObjectAccessor::GetGameObject(*me, rope.object))
        {
            if (go->GetOwnerGUID() == me->GetGUID())
                me->RemoveGameObject(go, true);
            else
                go->DespawnOrUnsummon();
        }
        rope.object.Clear();
    }

    void EndRope(Rope& rope, RopeEnd end, Player const* by = nullptr)
    {
        if (rope.done)
            return;
        rope.done = true;
        Player* target = ObjectAccessor::GetPlayer(*me, rope.target);
        if (target)
            target->RemoveAurasDueToSpell(SPELL_HARPOONED);
        if (Creature* anchor = ObjectAccessor::GetCreature(*me, rope.anchor))
        {
            anchor->InterruptNonMeleeSpells(true);
            anchor->DespawnOrUnsummon();
        }
        RemoveRopeObject(rope);
        rope.standers.Clear();
        LOG_INFO(kLog, "dm-pilot greenskin reel-em-in {} target={} by={}", RopeEndName(end),
            target ? target->GetName() : rope.target.ToString(), by ? by->GetName() : "-");
    }

    void ClearRopes()
    {
        for (Rope& rope : _ropes)
        {
            Mechanic::Cancel(me, rope.runOut);
            EndRope(rope, RopeEnd::Lost);
        }
        _ropes.clear();
        _pendingHarpoon.clear();
    }

    // The RunOut hit `guid` (still within 25 yd after 4 s): pull him to the front of the boss. The 30% and the
    // Weakened stack are the RunOut's own (SPELL_REEL_HIT).
    void Reel(ObjectGuid const& guid)
    {
        Player* player = ObjectAccessor::GetPlayer(*me, guid);
        if (player && player->IsAlive())
        {
            // Mirrors Spell::EffectPullTowards (AzerothCore): a jump whose arc lands at the destination.
            Vec2 const dest = ReelDestination(PlaneOf(me), me->GetOrientation());
            float const z = me->GetPositionZ() + 0.5f;
            float const dist = DeadminesKit::Distance(PlaneOf(player), dest);
            float const speedZ = static_cast<float>(dist / kReelSpeedXY * 0.5 * Movement::gravity);
            player->GetMotionMaster()->MoveJump(dest.x, dest.y, z, kReelSpeedXY, speedZ);
            sScriptMgr->AnticheatSetUnderACKmount(player);
        }
        if (!_reelYellCooldownMs)
        {
            Talk(YELL_GREENSKIN_REEL);
            _reelYellCooldownMs = kReelYellCooldownMs;
        }
        if (Rope* rope = FindRope(guid))
            EndRope(*rope, RopeEnd::Reeled);
        else
            LOG_INFO(kLog, "dm-pilot greenskin reel-em-in reeled target={} (no rope)", guid.ToString());
    }

    void UpdateRopes(uint32 diff)
    {
        if (_ropes.empty())
            return;
        Map::PlayerList const& players = me->GetMap()->GetPlayers();
        for (Rope& rope : _ropes)
        {
            if (rope.done)
                continue;
            rope.ageMs += diff;
            Player* target = ObjectAccessor::GetPlayer(*me, rope.target);
            if (!target || !target->IsAlive() || !target->IsInMap(me))
            {
                Mechanic::Cancel(me, rope.runOut);
                EndRope(rope, RopeEnd::Lost);
                continue;
            }
            if (rope.ageMs > kRopeMs + kRopeCleanupMs)
            {
                EndRope(rope, RopeEnd::Expired);
                continue;
            }
            if (rope.ageMs > kRopeMs)
                continue;   // resolving: the reel (OnHit) or the cleanup ends it

            // out 1: the target got 25 yd away
            if (RopeSnapped(me->GetExactDist2d(target)))
            {
                Mechanic::Cancel(me, rope.runOut);
                EndRope(rope, RopeEnd::Snapped);
                continue;
            }

            // out 2: another player stood on the rope for 1 s
            Vec2 const boss = PlaneOf(me);
            Vec2 const end = PlaneOf(target);
            float const ropeZ = (me->GetPositionZ() + target->GetPositionZ()) * 0.5f;
            Player const* cutter = nullptr;
            for (auto const& ref : players)
            {
                Player* player = ref.GetSource();
                if (!player || player == target || !player->IsAlive())
                    continue;
                bool const on = std::fabs(player->GetPositionZ() - ropeZ) <= kRopeStandZYd
                    && StandsOnRope(boss, end, PlaneOf(player));
                if (rope.standers.Update(player->GetGUID().GetRawValue(), on, diff))
                {
                    cutter = player;
                    break;
                }
            }
            if (cutter)
            {
                Mechanic::Cancel(me, rope.runOut);
                EndRope(rope, RopeEnd::Stood, cutter);
                continue;
            }

            // out 3 is the click (ACTION_ROPE_CLICKED); keep the object at the rope's midpoint
            Vec2 const mid = RopeMidpoint(boss, end);
            if (RopeObjectNeedsMove(rope.objectAt, mid))
            {
                RemoveRopeObject(rope);
                rope.object = SummonRopeObject(mid, ropeZ, me->GetAngle(target));
                rope.objectAt = mid;
            }
        }
        _ropes.erase(std::remove_if(_ropes.begin(), _ropes.end(), [](Rope const& rope) { return rope.done; }),
            _ropes.end());
    }

    std::vector<Rope> _ropes;
    std::vector<ObjectGuid> _pendingHarpoon;
    uint32 _reelYellCooldownMs = 0;
};

// harpoon rope gameobject 301001: a click cuts the rope it marks (GS5, out 3)
struct go_dm_harpoon_rope : public GameObjectAI
{
    explicit go_dm_harpoon_rope(GameObject* go) : GameObjectAI(go) { }

    bool GossipHello(Player* player, bool /*reportUse*/) override
    {
        Unit* owner = me->GetOwner();
        Creature* boss = owner ? owner->ToCreature() : nullptr;
        if (!boss)
            boss = me->FindNearestCreature(NPC_CAPTAIN_GREENSKIN, 60.f);
        LOG_INFO(kLog, "dm-pilot greenskin rope-click player={} boss={}", player ? player->GetName() : "-",
            boss != nullptr);
        if (boss && boss->IsAIEnabled && boss->AI())
            boss->AI()->SetGUID(me->GetGUID(), ACTION_ROPE_CLICKED);
        return true;    // handled: no loot, no spell
    }
};

namespace
{
    Creature* FindGreenskin(ChatHandler* handler)
    {
        Creature* boss = DeadminesTest::FindBoss(handler, NPC_CAPTAIN_GREENSKIN);
        if (boss && !(boss->IsAIEnabled && boss->AI()))
        {
            handler->SendErrorMessage("Captain Greenskin has no AI.");
            return nullptr;
        }
        return boss;
    }

    // `.dmtest greenskin info`
    bool HandleInfo(ChatHandler* handler)
    {
        return DeadminesTest::ShowBossInfo(handler, NPC_CAPTAIN_GREENSKIN, BOSS_CAPTAIN_GREENSKIN);
    }

    // `.dmtest greenskin volley`: GS2 on normal, GS2 + GS3 + GS4 on heroic, now.
    bool HandleVolley(ChatHandler* handler)
    {
        Creature* boss = FindGreenskin(handler);
        if (!boss)
            return false;
        boss->AI()->DoAction(ACTION_TEST_VOLLEY);
        handler->SendSysMessage("Fire on My Mark: this map's volley fired on the deck frame.");
        return true;
    }

    // `.dmtest greenskin crossfire`: the heroic grid (4 + 2 lanes, burning crossings) on any difficulty.
    bool HandleCrossfire(ChatHandler* handler)
    {
        Creature* boss = FindGreenskin(handler);
        if (!boss)
            return false;
        boss->AI()->DoAction(ACTION_TEST_CROSSFIRE);
        handler->SendSysMessage("Crossfire: the heroic volley fired on the deck frame.");
        return true;
    }

    // `.dmtest greenskin harpoon`: GS5's cast now (random non-tank picks; out of combat: anyone on the map).
    bool HandleHarpoon(ChatHandler* handler)
    {
        Creature* boss = FindGreenskin(handler);
        if (!boss)
            return false;
        boss->AI()->DoAction(ACTION_TEST_HARPOON);
        handler->SendSysMessage("Reel 'Em In: cast started (see the server log for the targets).");
        return true;
    }

    // `.dmtest greenskin reel`: rope the selected player (else you) now, no cast. Turn GM mode off (.gm off): the
    // registry never hits a game master, so the reel would not land.
    bool HandleReel(ChatHandler* handler)
    {
        Creature* boss = FindGreenskin(handler);
        if (!boss)
            return false;
        Player* target = handler->getSelectedPlayerOrSelf();
        if (!target)
        {
            handler->SendErrorMessage("Select a player (or none, for yourself).");
            return false;
        }
        boss->AI()->SetGUID(target->GetGUID(), ACTION_TEST_REEL);
        handler->PSendSysMessage("Reel 'Em In: {} roped for 4 s (snap at 25 yd, stand on the rope 1 s, or click it).",
            target->GetName());
        return true;
    }

    ChatCommandTable const& GreenskinTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,         SEC_GAMEMASTER, Console::No },
            { "volley",     HandleVolley,       SEC_GAMEMASTER, Console::No },
            { "crossfire",  HandleCrossfire,    SEC_GAMEMASTER, Console::No },
            { "harpoon",    HandleHarpoon,      SEC_GAMEMASTER, Console::No },
            { "reel",       HandleReel,         SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_captain_greenskin_rework()
{
    RegisterDeadminesReworkCreatureAI(boss_captain_greenskin_rework);
    RegisterDeadminesReworkGameObjectAI(go_dm_harpoon_rope);
    RegisterSpellScript(spell_dm_greenskin_lane_hit);
    DeadminesTest::RegisterBoss("greenskin", GreenskinTestCommands());
}
