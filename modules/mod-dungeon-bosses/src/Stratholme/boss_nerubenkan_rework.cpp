/*
 * mod-dungeon-bosses, Stratholme S11: Nerub'enkan (10437), "The Web" (ruling 44). Build spec ST 2859-2911
 * (docs/dungeons/stratholme-rework.md, the whole "Nerub'enkan" section), handoff sections 3.4 rows NE, 3.5 row S11,
 * 3.6 and 3.8. Replaces stock SmartAI 10437 (Encasing Webs 4962, Pierce Armor 6016, Crypt Scarabs 31602, Raise Undead
 * Scarab 17235, the ziggurat write on death: data/sql/updates/pending_db_world/rev_nerubenkan_stratholme.sql drops
 * it); bound by apps/dbc-tools source/npcs/stratholme/nerubenkan.py. Pure rules: NerubenkanLogic.h.
 *
 *   NE1  Web Spray     8 s, then every 15 s: a random non-tank (emote line 1, the 3 s mark 206645); a 5 yd circle
 *                      follows them 3 s (DungeonKit::FollowThenLand), with X2's drop spot rule for a carrier bot:
 *                      onto an old web (enterable, MaxDwell 1.2 s, under the 2 s Stuck timer), else the plaza's edge,
 *                      away from the group. The glob missile (206646, look only) homes on them to arrive on time
 *   NE2  Glob landing  where they stand: the carrier 15% (206647, the kit's percent spell, not avoidable), anyone
 *                      else within 5 yd 25% / 30% Nature + Weakened (206648, the registry)
 *   NE3  Web patch     5 / 7 yd for the whole fight (DungeonKit::PuddleField, merge rule: a glob whose centre lands
 *                      in an old web makes none). A new web counts 1 s after it lands. Inside: slowed 50% (206649)
 *                      from 1 s, Stuck after 2 s (RegistryHit: Weakened + the 2 s root 206650), then 3 s immune. A
 *                      patch stalker (300583) carries the web look (206651 / 206652)
 *   NE4  Cocoon        15 s, then every 25 s: a 2 s cast (206653, emote line 2) at a random non-tank, healer included;
 *                      a Web Cocoon (300582, 8k / 12k) wraps them (DungeonKit::HoldInUnit: the stun 206654 and the
 *                      damage immunity 206655). Kill order: the cocoon first
 *   NE5  Hatch         unbroken after 8 / 6 s: it splits open (206659), frees the player and hatches 3 Undead Scarabs
 *                      10876 (2k / 2.5k, stock melee and Poison Proc; at most 6 alive on normal)
 *   NE6  Skitter       22 s, then every 30 s, when a web exists: the web farthest from him within 30 yd (on his
 *                      arena); an 8 yd circle there for 2 s (emote line 3), he leaps onto it (1 s flight) and bursts,
 *                      30% / 40% Nature + Weakened (206656; looks 206657, 206660), then goes back to the tank
 *   NE7  Brood Call    heroic, 30 s, then every 30 s: a 2.5 s cast (206658, not interruptible, yell line 4), then every
 *                      web hatches 2 Undead Scarabs, no cap
 *   NE8  Pierce Armor  stock 6016 on the tank: 1 s, then every 12 to 15 s
 *   Arena              StratholmeRework::LeashOptions on NerubenkanArena() (no grips; holds at the edge, evades when
 *                      dragged off). His ziggurat (DATA_ZIGGURAT2) opens on his death: the instance's.
 *
 * Every timer runs on the AI's own clock, never on BossAI's scheduler (a cast bar pauses that one): the webs, the
 * holds, the glob missiles, the Skitter leap and the Brood Call keep running through his casts. His casts go through a
 * DungeonKit::CastQueue: they never overlap (a Cocoon and a Brood Call due together: the second waits). Every firing
 * logs one INFO line "strat nerubenkan <mechanic> ..." (module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "Map.h"
#include "MotionMaster.h"
#include "NerubenkanLogic.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "StratholmeKit.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

using namespace Acore::ChatCommands;
using namespace StratholmeRework;
using namespace StratNerubenkan;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "nerubenkan";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    float Rand01()
    {
        return std::min(0.9999f, static_cast<float>(rand_norm()));
    }

    bool CountsAsPlayer(Player const* p)
    {
        return p && p->IsInWorld() && p->IsAlive() && !p->IsGameMaster();
    }
}

// Nerub'enkan 10437
struct boss_nerubenkan_rework : public BossAI
{
    explicit boss_nerubenkan_rework(Creature* creature)
        : BossAI(creature, BOSS_NERUBENKAN), _arena(NerubenkanArena(), LeashOptions(kBossLogName)),
        _webs(Ms(kWebTickMs)) { }

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

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_NERUBENKAN;
        Mechanic::BeginEncounter(me, options);
        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        Describe();
        _arena.Engage(me);

        bool const heroic = IsHeroicMap(me);
        _nextSprayMs = kWebSprayFirstMs;
        _nextPierceMs = kPierceFirstMs;
        _queue.Schedule(CAST_COCOON, kCocoonFirstMs, kPriorityCocoon);
        _queue.Schedule(CAST_SKITTER, kSkitterFirstMs, kPrioritySkitter);
        if (heroic)
            _queue.Schedule(CAST_BROOD_CALL, kBroodFirstMs, kPriorityBrood);
        Talk(YELL_NERUBENKAN_AGGRO);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f})", heroic ? 1 : 0, me->GetPositionX(),
                me->GetPositionY(), me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Talk(YELL_NERUBENKAN_DEATH);
        BossAI::JustDied(killer);   // DONE (the instance opens his ziggurat), the summons despawn, the encounter ends
        std::size_t const webs = _webList.size();
        Cleanup();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("webs={} killer={}", webs, killer ? killer->GetName() : "none"));
    }

    // The patch stalkers are props: never zoned into combat (BossAI::JustSummoned would). The cocoons and scarabs are.
    void JustSummoned(Creature* summon) override
    {
        if (summon->GetEntry() == NPC_ST_WEB_PATCH)
        {
            summons.Summon(summon);
            return;
        }
        BossAI::JustSummoned(summon);
    }

    void UpdateAI(uint32 diff) override
    {
        _holds.Update(me, diff);    // a hold ends with its cocoon even out of combat

        if (!UpdateVictim())
            return;

        // The AI's own clock: nothing below waits for a cast bar.
        _clockMs += diff;
        bool const heroic = IsHeroicMap(me);
        _webs.Update(me, diff, [this](Player* player, uint32 msInside) { OnWebTick(player, msInside); });
        UpdateSprays();
        UpdateCocoonCast(heroic);
        UpdateBroodCall(heroic);
        UpdateSkitter();

        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        if (_clockMs >= _nextSprayMs)
        {
            _nextSprayMs = _clockMs + kWebSprayEveryMs;
            StartWebSpray(heroic, nullptr);
        }

        StartQueuedCast(heroic);

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;

        if (_clockMs >= _nextPierceMs)
        {
            Unit* victim = me->GetVictim();
            if (victim && me->IsWithinMeleeRange(victim) && me->CastSpell(victim, SPELL_PIERCE_ARMOR) == SPELL_CAST_OK)
                _nextPierceMs = _clockMs + urand(kPierceEveryMinMs, kPierceEveryMaxMs);
            else
                _nextPierceMs = _clockMs + kPierceRetryMs;
        }

        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The cast queue: Cocoon, Skitter, Brood Call never overlap
    // ----------------------------------------------------------------------------------------------------------------

    void StartQueuedCast(bool heroic)
    {
        if (me->HasUnitState(UNIT_STATE_CASTING) || _skitter)
            return;
        std::optional<uint32> const next = _queue.Next(_clockMs);
        if (!next)
            return;
        switch (*next)
        {
            case CAST_COCOON:
                _queue.Started(CAST_COCOON, _clockMs, kCocoonCastMs);
                _queue.Schedule(CAST_COCOON, _clockMs + kCocoonEveryMs, kPriorityCocoon);
                if (!StartCocoon(heroic, false))
                    _queue.Interrupted(_clockMs);   // nobody to wrap: no cast, the turn passes
                break;
            case CAST_SKITTER:
                if (!StartSkitter(heroic))
                {
                    _queue.Schedule(CAST_SKITTER, _clockMs + kSkitterRetryMs, kPrioritySkitter);  // no web yet
                    break;
                }
                _queue.Started(CAST_SKITTER, _clockMs, kSkitterWarnMs);
                _queue.Schedule(CAST_SKITTER, _clockMs + kSkitterEveryMs, kPrioritySkitter);
                break;
            case CAST_BROOD_CALL:
                _queue.Started(CAST_BROOD_CALL, _clockMs, kBroodCastMs);
                _queue.Schedule(CAST_BROOD_CALL, _clockMs + kBroodEveryMs, kPriorityBrood);
                StartBroodCall();
                break;
            default:
                _queue.Cancel(*next);
                break;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // NE1 / NE2 Web Spray and the glob
    // ----------------------------------------------------------------------------------------------------------------

    struct Spray
    {
        ObjectGuid target;
        uint64 landAt = 0;
        MechanicHandle handle;
        bool launched = false;
    };

    // The players a new pick must skip: wrapped in a cocoon, already carrying a glob, about to be wrapped.
    GuidSet Busy() const
    {
        GuidSet busy;
        for (Spray const& s : _sprays)
            busy.insert(s.target);
        for (auto const& [held, holder] : _cocoons)
            busy.insert(held);
        if (_cocoonCast)
            busy.insert(_cocoonCast->target);
        return busy;
    }

    Player* PickNonTank(bool tankIfAlone) const
    {
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.tankIfAlone = tankIfAlone;
        DungeonKit::ExcludeGuids(rule, Busy());
        return DungeonKit::PickPlayer(me, rule);
    }

    // `forced`: a test's target (else a random non-tank; a solo tank when nobody else is there).
    bool StartWebSpray(bool heroic, Player* forced)
    {
        Player* target = forced ? forced : PickNonTank(true);
        if (!target)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "web-spray-skipped", "no target");
            return false;
        }

        DungeonKit::ImpactSpec impact;
        impact.pct = kGlobSplashPct(heroic);
        impact.school = SPELL_SCHOOL_NATURE;
        impact.spellId = SPELL_NE_GLOB_SPLASH;
        impact.weakened = true;
        impact.tag = TAG_GLOB;

        Map* map = me->GetMap();
        ObjectGuid const bossGuid = me->GetGUID();
        ObjectGuid const targetGuid = target->GetGUID();
        uint32 const gen = _generation;
        MechanicRef ref = DungeonKit::FollowThenLand(me, target, kGlobRadius, Ms(kWebSprayWarnMs), impact,
            [map, bossGuid, targetGuid, gen, heroic](Creature* /*owner*/, Position const& spot,
                BossMechanics::ResolveResult const& result)
            {
                if (result.fizzled)
                    return;
                if (boss_nerubenkan_rework* ai = AIOf(map, bossGuid, gen))
                    ai->GlobLanded(targetGuid, spot, heroic, result.hits.size());
            });
        if (!ref.IsValid())
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "web-spray-refused", target->GetName());
            return false;
        }
        ref.DropSpot(DropRule());
        MechanicHandle const handle = ref.Handle();

        Talk(EMOTE_NERUBENKAN_WEB, target);
        me->CastSpell(target, SPELL_NE_WEB_SPRAY, true);
        _sprays.push_back({ targetGuid, _clockMs + kWebSprayWarnMs, handle, false });
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "web-spray",
            Acore::StringFormat("heroic={} target={} webs={}", heroic ? 1 : 0, target->GetName(), _webList.size()));
        return true;
    }

    // X2's drop spot rule for the carrier bot: onto an old web (it may step in MaxDwell before the landing), else the
    // plaza's edge, away from the group (the arena circle is the room).
    BossMechanics::DropSpotRule DropRule() const
    {
        Arena const arena = NerubenkanArena();
        Vec2 const c = arena.regions.front().center;
        BossMechanics::DropSpotRule rule;
        rule.Room(Position(c.x, c.y, kNerubenkanPlazaZ), arena.regions.front().radius).Edge().Away()
            .MaxDwell(Ms(kDropMaxDwellMs));
        for (Web const& web : _webList)
            rule.Prefer(web.center, web.radius, web.zoneId);
        return rule;
    }

    // The glob missile (look only), launched so it reaches the carrier as the circle resolves.
    void UpdateSprays()
    {
        for (auto it = _sprays.begin(); it != _sprays.end();)
        {
            if (_clockMs > it->landAt + 2000)
            {
                it = _sprays.erase(it);     // the landing never came (the carrier died or left)
                continue;
            }
            if (!it->launched)
            {
                Player* target = ObjectAccessor::GetPlayer(*me, it->target);
                if (!CountsAsPlayer(target) || !target->IsInMap(me))
                    it->launched = true;
                else if (_clockMs >= GlobLaunchAt(it->landAt, me->GetExactDist2d(target)))
                {
                    me->CastSpell(target, SPELL_NE_GLOB_MISSILE, true);
                    it->launched = true;
                }
            }
            ++it;
        }
    }

    void GlobLanded(ObjectGuid targetGuid, Position const& spot, bool heroic, std::size_t splashHits)
    {
        _sprays.erase(std::remove_if(_sprays.begin(), _sprays.end(), [targetGuid](Spray const& s)
        {
            return s.target == targetGuid;
        }), _sprays.end());
        Player* carrier = ObjectAccessor::GetPlayer(*me, targetGuid);
        bool const carrierHit = CountsAsPlayer(carrier) && carrier->IsInMap(me);
        if (carrierHit)
        {
            me->CastSpell(carrier, SPELL_NE_GLOB_HIT, true);
            carrier->RemoveAurasDueToSpell(SPELL_NE_WEB_SPRAY, me->GetGUID());
        }
        AddWeb(spot, heroic, "glob");
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "glob-lands",
            Acore::StringFormat("at=({:.1f}, {:.1f}, {:.1f}) carrier={} splash={}", spot.GetPositionX(),
                spot.GetPositionY(), spot.GetPositionZ(), carrierHit ? carrier->GetName() : "gone", splashHits));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // NE3 the webs
    // ----------------------------------------------------------------------------------------------------------------

    struct Web
    {
        uint32 puddleId = 0;
        Position center;
        float radius = 0.f;
        uint32 zoneId = 0;      // the PuddleField zone's mechanic id (X2: an enterable preferred spot)
        ObjectGuid stalker;
    };

    // A web at `spot` (the merge rule: its centre inside an old web adds nothing). `why`: the log's reason.
    void AddWeb(Position const& spot, bool heroic, char const* why)
    {
        DungeonKit::PuddleSpec spec;
        spec.radius = kWebRadius(heroic);
        spec.armAfter = Ms(kWebArmMs);
        spec.merge = true;
        spec.tag = TAG_WEB;
        DungeonKit::PuddleSet::AddResult const added = _webs.Add(me, spot, spec);
        if (!added.id)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "web-refused", why);
            return;
        }
        if (added.merged)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "web-merged",
                Acore::StringFormat("{} into={} webs={}", why, added.id, _webList.size()));
            return;
        }
        Web web;
        web.puddleId = added.id;
        web.center = spot;
        web.radius = spec.radius;
        web.zoneId = WebZoneId(spot);
        if (TempSummon* stalker = me->SummonCreature(NPC_ST_WEB_PATCH, spot, TEMPSUMMON_MANUAL_DESPAWN))
        {
            stalker->CastSpell(stalker, heroic ? SPELL_NE_WEB_LOOK_7 : SPELL_NE_WEB_LOOK_5, true);
            web.stalker = stalker->GetGUID();
        }
        _webList.push_back(web);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "web",
            Acore::StringFormat("{} id={} at=({:.1f}, {:.1f}) r={:.0f} webs={} floor={:.0f}", why, added.id,
                spot.GetPositionX(), spot.GetPositionY(), spec.radius, _webList.size(), _webs.CoveredArea(0.5f)));
    }

    // The registry id of the web zone PuddleField registered at `center` (its telegraph-only persistent Zone, tagged
    // TAG_WEB): X2's DropSpotRule::Prefer needs it to let a carrier bot step into that web. 0: not found (the web is
    // then a plain preferred spot).
    uint32 WebZoneId(Position const& center) const
    {
        BossMechanics::Registry const* reg = Mechanic::Read(me->GetMap());
        if (!reg)
            return 0;
        uint32 found = 0;
        ObjectGuid const owner = me->GetGUID();
        reg->ForEachActive(Milliseconds(0), [&found, &owner, &center](BossMechanics::ActiveMechanic const& m)
        {
            if (m.owner != owner || m.tag != TAG_WEB || m.anchor.IsUnit() || m.id <= found)
                return;
            if (std::fabs(m.anchor.point.GetPositionX() - center.GetPositionX()) < 0.05f
                && std::fabs(m.anchor.point.GetPositionY() - center.GetPositionY()) < 0.05f)
                found = m.id;
        });
        return found;
    }

    // Once per tick (250 ms) for each player inside the union of armed webs, with their time inside.
    void OnWebTick(Player* player, uint32 msInside)
    {
        if (_cocoons.count(player->GetGUID()))
            return;     // wrapped: immune, and not walking anywhere
        if (SlowDue(msInside))
        {
            Aura const* slow = player->GetAura(SPELL_NE_STICKY_WEB, me->GetGUID());
            if (!slow || slow->GetDuration() < int32(kSlowRefreshBelowMs))
                me->CastSpell(player, SPELL_NE_STICKY_WEB, true);
        }
        uint64& immuneUntil = _stuckImmuneUntil[player->GetGUID()];
        if (!StuckDue(msInside, _clockMs, immuneUntil))
            return;
        immuneUntil = StuckImmuneUntil(_clockMs);
        DungeonKit::RegistryHitSpec spec;
        spec.pct = 0.f;
        spec.weakened = true;
        spec.rider = SPELL_NE_STUCK;
        spec.tag = TAG_STUCK;
        GuidSet target;
        target.insert(player->GetGUID());
        DungeonKit::RegistryHit(me, target, spec);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "stuck",
            Acore::StringFormat("{} inside={}ms", player->GetName(), msInside));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // NE4 / NE5 Cocoon and the hatch
    // ----------------------------------------------------------------------------------------------------------------

    struct CocoonCast
    {
        ObjectGuid target;
        uint64 wrapAt = 0;
        bool heroic = false;
    };

    // `test`: a solo tester may be the target.
    bool StartCocoon(bool heroic, bool test)
    {
        Player* target = PickNonTank(test);
        if (!target)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "cocoon-skipped", "no non-tank");
            return false;
        }
        DungeonKit::CastBar(me, SPELL_NE_COCOON_CAST, target, EMOTE_NERUBENKAN_COCOON, target);
        _cocoonCast = CocoonCast{ target->GetGUID(), _clockMs + kCocoonCastMs, heroic };
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "cocoon-cast",
            Acore::StringFormat("heroic={} target={}", heroic ? 1 : 0, target->GetName()));
        return true;
    }

    void UpdateCocoonCast(bool /*heroic*/)
    {
        if (!_cocoonCast || _clockMs < _cocoonCast->wrapAt)
            return;
        CocoonCast const cast = *_cocoonCast;
        _cocoonCast.reset();
        Wrap(cast.target, cast.heroic);
    }

    void Wrap(ObjectGuid targetGuid, bool heroic)
    {
        Player* target = ObjectAccessor::GetPlayer(*me, targetGuid);
        if (!CountsAsPlayer(target) || !target->IsInMap(me) || _holds.IsHeld(targetGuid))
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "cocoon-missed", "target gone or already held");
            return;
        }
        TempSummon* cocoon = me->SummonCreature(NPC_ST_WEB_COCOON, target->GetPosition(),
            TEMPSUMMON_CORPSE_TIMED_DESPAWN, 3000);
        if (!cocoon)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "cocoon-failed", "summon refused");
            return;
        }
        Mechanic::TrackUnit(me, cocoon);

        Map* map = me->GetMap();
        ObjectGuid const bossGuid = me->GetGUID();
        uint32 const gen = _generation;
        DungeonKit::HoldSpec spec;
        spec.holdSpell = SPELL_NE_COCOON_HOLD;
        spec.immuneSpell = SPELL_NE_COCOONED;
        spec.maxHold = Ms(kCocoonHoldMs(heroic));
        spec.onRelease = [map, bossGuid, gen, heroic](ObjectGuid holder, ObjectGuid held, DungeonKit::HoldEnd why)
        {
            if (boss_nerubenkan_rework* ai = AIOf(map, bossGuid, gen))
                ai->CocoonReleased(holder, held, why, heroic);
            else if (Creature* c = map ? map->GetCreature(holder) : nullptr)
                c->DespawnOrUnsummon();     // the fight is over: the cocoon goes, no hatch
        };
        if (!_holds.Hold(cocoon, target, std::move(spec)))
        {
            cocoon->DespawnOrUnsummon();
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "cocoon-failed", "hold refused");
            return;
        }
        _cocoons[targetGuid] = cocoon->GetGUID();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "cocoon",
            Acore::StringFormat("heroic={} held={} health={} hatchIn={}ms", heroic ? 1 : 0, target->GetName(),
                cocoon->GetMaxHealth(), kCocoonHoldMs(heroic)));
    }

    void CocoonReleased(ObjectGuid holder, ObjectGuid held, DungeonKit::HoldEnd why, bool heroic)
    {
        _cocoons.erase(held);
        Creature* cocoon = me->GetMap()->GetCreature(holder);
        if (why == DungeonKit::HoldEnd::Timeout && cocoon && cocoon->IsAlive())
        {
            Position const at = cocoon->GetPosition();
            cocoon->CastSpell(cocoon, SPELL_NE_COCOON_SPLITS, true);
            cocoon->DespawnOrUnsummon(1s);
            uint32 const n = HatchSize(heroic, ScarabsAlive());
            SummonScarabs(at, n, heroic);
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "hatch",
                Acore::StringFormat("heroic={} scarabs={} alive={}", heroic ? 1 : 0, n, ScarabsAlive()));
            return;
        }
        if (cocoon && cocoon->IsAlive())
            cocoon->DespawnOrUnsummon();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName,
            why == DungeonKit::HoldEnd::HolderGone ? "cocoon-broken" : "cocoon-released",
            DungeonKit::HoldEndName(why));
    }

    uint32 ScarabsAlive() const
    {
        uint32 n = 0;
        for (ObjectGuid const& guid : summons)
            if (Creature const* c = me->GetMap()->GetCreature(guid))
                if (c->GetEntry() == NPC_UNDEAD_SCARAB && c->IsAlive())
                    ++n;
        return n;
    }

    // `n` scarabs round `at`; each goes for the nearest player (stock 10876: melee and its Poison Proc reset row).
    void SummonScarabs(Position const& at, uint32 n, bool /*heroic*/)
    {
        if (!n)
            return;
        std::vector<Position> spots;
        for (Vec2 const& p : ScarabSpots({ at.GetPositionX(), at.GetPositionY() }, n, Rand01() * DungeonKit::kTwoPi))
        {
            float z = me->GetMapHeight(p.x, p.y, at.GetPositionZ() + 2.f);
            if (z <= INVALID_HEIGHT + 1.f || std::fabs(z - at.GetPositionZ()) > 3.f)
                z = at.GetPositionZ();
            spots.emplace_back(p.x, p.y, z, Rand01() * DungeonKit::kTwoPi);
        }
        DungeonKit::WaveSpec spec;
        spec.entry = NPC_UNDEAD_SCARAB;   // health: the normal row (2k) or its heroic template (2.5k), data
        spec.type = TEMPSUMMON_CORPSE_TIMED_DESPAWN;
        spec.despawn = 5s;
        spec.onSummon = [](Creature* add)
        {
            Player* nearest = nullptr;
            float best = 0.f;
            for (auto const& ref : add->GetMap()->GetPlayers())
            {
                Player* p = ref.GetSource();
                if (!CountsAsPlayer(p))
                    continue;
                float const d = add->GetExactDist2d(p);
                if (!nearest || d < best)
                {
                    nearest = p;
                    best = d;
                }
            }
            if (nearest && add->IsAIEnabled)
            {
                add->AddThreat(nearest, 100.f);
                add->AI()->AttackStart(nearest);
            }
        };
        DungeonKit::SummonWave(me, spec, spots, summons);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // NE6 Skitter
    // ----------------------------------------------------------------------------------------------------------------

    struct Skitter
    {
        Position spot;
        uint64 jumpAt = 0;
        uint64 doneAt = 0;
        MechanicHandle handle;
        bool jumped = false;
    };

    // False when no web qualifies (no leap before the first web, nor onto a web off his arena or beyond 30 yd).
    bool StartSkitter(bool heroic)
    {
        Arena const arena = NerubenkanArena();
        std::vector<Web const*> onArena;
        std::vector<Vec2> centers;
        for (Web const& web : _webList)
            if (arena.Contains({ web.center.GetPositionX(), web.center.GetPositionY() }, web.center.GetPositionZ()))
            {
                onArena.push_back(&web);
                centers.push_back({ web.center.GetPositionX(), web.center.GetPositionY() });
            }
        std::optional<std::size_t> const pick = PickSkitterPatch(DungeonKit::PlaneOf(me), centers,
            [](Vec2) { return true; });
        if (!pick)
            return false;
        Position const spot = onArena[*pick]->center;

        MechanicRef ref = Mechanic::Circle(me, spot, kSkitterRadius, Ms(kSkitterWarnMs));
        ref.Damage(kSkitterPct(heroic)).School(SPELL_SCHOOL_NATURE).Weakened().Spell(SPELL_NE_SKITTER_BURST)
            .Tag(TAG_SKITTER);
        Map* map = me->GetMap();
        ObjectGuid const bossGuid = me->GetGUID();
        uint32 const gen = _generation;
        ref.OnResolve([map, bossGuid, gen](BossMechanics::ResolveResult const& result)
        {
            if (result.fizzled)
                return;
            if (boss_nerubenkan_rework* ai = AIOf(map, bossGuid, gen))
                ai->SkitterLanded(result.hits.size());
        });
        _skitter = Skitter{ spot, _clockMs + kSkitterWarnMs - kSkitterFlightMs, _clockMs + kSkitterWarnMs + 1000,
            ref.Handle(), false };
        Talk(EMOTE_NERUBENKAN_SKITTER);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "skitter",
            Acore::StringFormat("heroic={} to=({:.1f}, {:.1f}) dist={:.1f} webs={}", heroic ? 1 : 0,
                spot.GetPositionX(), spot.GetPositionY(), me->GetExactDist2d(spot), _webList.size()));
        return true;
    }

    // The leap: 1 s before the burst, so he lands as it resolves. The chase resumes by itself after the jump.
    void UpdateSkitter()
    {
        if (!_skitter)
            return;
        if (!_skitter->jumped && _clockMs >= _skitter->jumpAt)
        {
            _skitter->jumped = true;
            me->InterruptNonMeleeSpells(false);
            float const dist = me->GetExactDist2d(_skitter->spot);
            DungeonKit::JumpTo(me, _skitter->spot, SkitterJumpSpeed(dist));
        }
        if (_clockMs >= _skitter->doneAt)
            _skitter.reset();       // a resolve that never came (cancelled): free the queue
    }

    void SkitterLanded(std::size_t hits)
    {
        me->CastSpell(me, SPELL_NE_SKITTER_LANDING, true);
        me->CastSpell(me, SPELL_NE_POISON_BURST, true);
        _skitter.reset();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "skitter-lands",
            Acore::StringFormat("at=({:.1f}, {:.1f}) hits={}", me->GetPositionX(), me->GetPositionY(), hits));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // NE7 Brood Call (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    void StartBroodCall()
    {
        DungeonKit::CastBar(me, SPELL_NE_BROOD_CALL, nullptr, YELL_NERUBENKAN_BROOD_CALL);
        _broodAt = _clockMs + kBroodCastMs;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "brood-call-cast",
            Acore::StringFormat("webs={}", _webList.size()));
    }

    void UpdateBroodCall(bool heroic)
    {
        if (!_broodAt || _clockMs < *_broodAt)
            return;
        _broodAt.reset();
        for (Web const& web : _webList)
            SummonScarabs(web.center, kBroodPerPatch, heroic);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "brood-call",
            Acore::StringFormat("webs={} scarabs={} alive={}", _webList.size(), BroodCallCount(_webList.size()),
                ScarabsAlive()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (ST): kill order Web Cocoon, then Undead Scarab, then him; no interrupts, no dispels
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        using BossMechanics::TargetEntry;
        using BossMechanics::Who;
        BossMechanics::Descriptor d;
        d.targets.push_back(TargetEntry(NPC_ST_WEB_COCOON, 3, Who::Dps).BreakOut());
        d.targets.push_back(TargetEntry(NPC_UNDEAD_SCARAB, 2, Who::Dps).AoeOk());
        d.targets.emplace_back(NPC_NERUBENKAN, 0, Who::Any);
        d.ignores.emplace_back(NPC_ST_WEB_PATCH);
        // Neither cast is a kick (both are uninterruptible): priority 0 = never kick.
        d.interrupts.emplace_back(NPC_NERUBENKAN, SPELL_NE_COCOON_CAST, 0);
        d.interrupts.emplace_back(NPC_NERUBENKAN, SPELL_NE_BROOD_CALL, 0);
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest strat nerubenkan` entry points (`heroic` forces the heroic form on a normal map)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Spray,
        Cocoon,
        Skitter,
        Brood,
    };

    // An empty string when fired; otherwise why not.
    std::string TestFire(TestMechanic mechanic, bool heroic)
    {
        if (!me->IsEngaged())
            return "Nerub'enkan must be in combat (the webs, holds and timers run only in the fight).";
        if (me->HasUnitState(UNIT_STATE_CASTING) || _skitter || _cocoonCast || _broodAt)
            return "Nerub'enkan is casting or leaping; try again in a moment.";
        switch (mechanic)
        {
            case TestMechanic::Spray:
                if (!StartWebSpray(heroic, nullptr))
                    return "No target for Web Spray.";
                break;
            case TestMechanic::Cocoon:
                if (!StartCocoon(heroic, true))
                    return "No target for the Cocoon.";
                _queue.Started(CAST_COCOON, _clockMs, kCocoonCastMs, false);
                _queue.Schedule(CAST_COCOON, _clockMs + kCocoonEveryMs, kPriorityCocoon);
                break;
            case TestMechanic::Skitter:
                if (!StartSkitter(heroic))
                    return "No web within 30 yd of him on his arena (try `web` first).";
                _queue.Started(CAST_SKITTER, _clockMs, kSkitterWarnMs, false);
                _queue.Schedule(CAST_SKITTER, _clockMs + kSkitterEveryMs, kPrioritySkitter);
                break;
            case TestMechanic::Brood:
                StartBroodCall();
                _queue.Started(CAST_BROOD_CALL, _clockMs, kBroodCastMs, false);
                if (IsHeroicMap(me))
                    _queue.Schedule(CAST_BROOD_CALL, _clockMs + kBroodEveryMs, kPriorityBrood);
                break;
        }
        return {};
    }

    // A web under `at` (the GM's spot): the patch, the merge rule and the clock, without a glob.
    std::string TestWeb(Position const& at, bool heroic)
    {
        if (!me->IsEngaged())
            return "Nerub'enkan must be in combat (the webs are cleared with the fight).";
        AddWeb(at, heroic, "test");
        return {};
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        std::string webs;
        for (Web const& web : _webList)
            webs += Acore::StringFormat(" [{} ({:.1f}, {:.1f}) r={:.0f} zone={}]", web.puddleId,
                web.center.GetPositionX(), web.center.GetPositionY(), web.radius, web.zoneId);
        auto at = [this](uint32 id)
        {
            std::optional<uint64> const due = _queue.DueAt(id);
            return due ? Acore::StringFormat("{}s", int64(*due / 1000)) : std::string("-");
        };
        return Acore::StringFormat("clock={}s spray@{}s cocoon@{} skitter@{} brood@{} pierce@{}s held={} scarabs={} "
            "inside={} floor={:.0f} sq yd webs={}{}", _clockMs / 1000, _nextSprayMs / 1000, at(CAST_COCOON),
            at(CAST_SKITTER), at(CAST_BROOD_CALL), _nextPierceMs / 1000, _cocoons.size(), ScarabsAlive(),
            _webs.Inside().size(), _webs.CoveredArea(0.5f), _webList.size(), webs);
    }

private:
    // The live AI of this boss on `map`, if it is still the same pull (`gen`). Captures in the registry's and the
    // kit's callbacks are the map and guids only (never a Unit*).
    static boss_nerubenkan_rework* AIOf(Map* map, ObjectGuid bossGuid, uint32 gen)
    {
        Creature* boss = map ? map->GetCreature(bossGuid) : nullptr;
        if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
            return nullptr;
        auto* ai = dynamic_cast<boss_nerubenkan_rework*>(boss->AI());
        return ai && ai->_generation == gen ? ai : nullptr;
    }

    // The pull's state: no webs, holds, sprays, leaps or pending casts (Reset, evade, death, a new pull).
    void Cleanup()
    {
        ++_generation;      // callbacks of an older pull stop
        for (Spray const& s : _sprays)
            Mechanic::Cancel(me, s.handle);
        _sprays.clear();
        if (_skitter)
            Mechanic::Cancel(me, _skitter->handle);
        _skitter.reset();
        _holds.Clear(me);   // frees every wrapped player (their onRelease despawns the cocoons: a new generation)
        _cocoons.clear();
        _webs.Clear(me);
        _webList.clear();
        summons.DespawnEntry(NPC_ST_WEB_PATCH);
        summons.DespawnEntry(NPC_ST_WEB_COCOON);
        _cocoonCast.reset();
        _broodAt.reset();
        _stuckImmuneUntil.clear();
        _queue.Reset();
        _clockMs = 0;
        _nextSprayMs = kWebSprayFirstMs;
        _nextPierceMs = kPierceFirstMs;
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::PuddleField _webs;
    DungeonKit::HoldInUnit _holds;
    DungeonKit::CastQueue _queue;
    uint64 _clockMs = 0;                        // ms since the pull: every timer of the fight
    uint64 _nextSprayMs = kWebSprayFirstMs;
    uint64 _nextPierceMs = kPierceFirstMs;
    uint32 _generation = 0;
    std::vector<Spray> _sprays;
    std::vector<Web> _webList;
    std::unordered_map<ObjectGuid, ObjectGuid> _cocoons;     // held player -> cocoon
    std::unordered_map<ObjectGuid, uint64> _stuckImmuneUntil;
    std::optional<CocoonCast> _cocoonCast;
    std::optional<uint64> _broodAt;
    std::optional<Skitter> _skitter;
};

// The Web Cocoon (300582): a rooted, attackable shell round a wrapped player; it never fights. Killing it frees the
// player (HoldInUnit sees the holder die); unbroken, the boss splits it open (NE5).
struct npc_st_web_cocoon : public NullCreatureAI
{
    explicit npc_st_web_cocoon(Creature* creature) : NullCreatureAI(creature) { }

    void InitializeAI() override
    {
        me->SetReactState(REACT_PASSIVE);
        me->SetControlled(true, UNIT_STATE_ROOT);
    }
};

// The web patch stalker (300583): an invisible prop that carries the web's look (206651 / 206652).
struct npc_st_web_patch : public NullCreatureAI
{
    explicit npc_st_web_patch(Creature* creature) : NullCreatureAI(creature) { }
};

namespace
{
    boss_nerubenkan_rework* FindNerubenkanAI(ChatHandler* handler)
    {
        Creature* boss = StratTest::FindBoss(handler, NPC_NERUBENKAN);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_nerubenkan_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}",
                "Nerub'enkan is not running boss_nerubenkan_rework (check the ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_nerubenkan_rework::TestMechanic mechanic, Optional<uint32> heroic,
        char const* what)
    {
        boss_nerubenkan_rework* ai = FindNerubenkanAI(handler);
        if (!ai)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        std::string const error = ai->TestFire(mechanic, isHeroic);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Nerub'enkan: {} fired ({}).", what, isHeroic ? "heroic" : "normal");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return StratTest::ShowBossInfo(handler, NPC_NERUBENKAN, BOSS_NERUBENKAN);
    }

    bool HandleSpray(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_nerubenkan_rework::TestMechanic::Spray, heroic,
            "Web Spray (NE1, the glob NE2 and its web NE3)");
    }

    bool HandleCocoon(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_nerubenkan_rework::TestMechanic::Cocoon, heroic,
            "Cocoon (NE4; unbroken: the hatch NE5)");
    }

    bool HandleSkitter(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_nerubenkan_rework::TestMechanic::Skitter, heroic, "Skitter (NE6)");
    }

    bool HandleBrood(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_nerubenkan_rework::TestMechanic::Brood, heroic, "Brood Call (NE7)");
    }

    // `.dbtest strat nerubenkan web [1]`: a web under the GM (heroic size with 1).
    bool HandleWeb(ChatHandler* handler, Optional<uint32> heroic)
    {
        boss_nerubenkan_rework* ai = FindNerubenkanAI(handler);
        Player* gm = handler->GetPlayer();
        if (!ai || !gm)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        std::string const error = ai->TestWeb(gm->GetPosition(), isHeroic);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Nerub'enkan: a web under you ({}).", isHeroic ? "heroic, 7 yd" : "normal, 5 yd");
        return true;
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_nerubenkan_rework* ai = FindNerubenkanAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Nerub'enkan: {}", ai->TestState());
        return true;
    }

    // `.dbtest strat nerubenkan <sub> [1]`: the optional 1 forces the heroic form (0 forces normal); default: the
    // map's.
    ChatCommandTable const& NerubenkanTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",    HandleInfo,    SEC_GAMEMASTER, Console::No },
            { "state",   HandleState,   SEC_GAMEMASTER, Console::No },
            { "spray",   HandleSpray,   SEC_GAMEMASTER, Console::No },
            { "web",     HandleWeb,     SEC_GAMEMASTER, Console::No },
            { "cocoon",  HandleCocoon,  SEC_GAMEMASTER, Console::No },
            { "skitter", HandleSkitter, SEC_GAMEMASTER, Console::No },
            { "brood",   HandleBrood,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_nerubenkan_rework()
{
    RegisterDungeonReworkCreatureAI(boss_nerubenkan_rework, StratholmeRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_st_web_cocoon, StratholmeRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_st_web_patch, StratholmeRework::kInstanceScriptName);
    StratTest::RegisterBoss("nerubenkan", NerubenkanTestCommands());
}
