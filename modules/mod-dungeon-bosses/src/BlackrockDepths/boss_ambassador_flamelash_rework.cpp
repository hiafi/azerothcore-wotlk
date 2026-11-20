/*
 * mod-dungeon-bosses, Blackrock Depths D20: Ambassador Flamelash (9156), "Firelands Portals" (ruling 70), with his
 * Portal Anchors (300842) and the Burning Spirits (9178). Build spec: docs/dungeons/blackrock-depths-4-imperial-seat.md
 * "Ambassador Flamelash" (S4 740-783, FL1-FL5; rulings 70-71, 88), handoff sections 3.4, 3.5 row D20, 3.6, 3.8 (NM: the
 * chamber and the seven rune spots), 3.10. Replaces the stock boss_ambassador_flamelash and npc_burning_spirit (still
 * registered, unbound by apps/dbc-tools source/npcs/blackrock_depths/flamelash.py once wave 2 binds): the four endless
 * summon chains are gone. Pure rules: FlamelashLogic.h. Wave 2: the three AIs register only once kWave2Bound flips.
 *
 *   FL1 Fire Blast   on his victim at 2 s, then every 7 s: Fire, 15% (heroic 20%) of the tank row
 *   FL2 Portals      at 10 s, then every 30 s (heroic 20 s): one of the seven runes (never the one that opened last,
 *                    never one with an anchor up) opens a Portal Anchor (yell line 1); it spills a Burning Spirit every
 *                    3 s (heroic 2 s) until it is destroyed. The spirits march on him (about 6 s from every rune)
 *   FL3 Burning      each spirit that reaches him adds a stack: +10% damage, +5% size, 10 at most, 30 s refreshed
 *       Spirit       by every arrival, and the spirit is gone. Slows, roots and stuns hold a spirit back
 *   FL4 Kindling     at 15 s, then every 25 s (heroic 20 s): an 8 s channel on a random player other than the tank
 *                    (emote line 2), not interruptible. Every second everyone else within 8 yd (heroic 10 yd) of the
 *                    target burns 8% (12%) of their row, the target 3% (5%). A registry RunOut tells the bots
 *   FL5 Burning      heroic: a 4 yd patch under the Kindled player every 2 s, up to 4 a channel, 15 s, 8% a second
 *       Trail
 *
 * His stack raises his damage: the aura raises his melee, and the percents of his own spells (they ignore caster
 * modifiers, rule 2) are multiplied by FlamelashLogic.h DamageScale (Fire Blast, Kindling's ticks, the registry percent
 * of a trail patch at registration). The anchors and the spirits never fight: they are passive, and the boss runs
 * their clocks (the spill, the arrival, the cap). Boss data for the bots: kill order Portal Anchor, Burning Spirit,
 * Flamelash; the tank's Spot in the chamber's center; Kindling a RunOut; the trail a persistent Zone. No interrupt or
 * dispel list. Every timer runs on the AI's own clock. Every firing logs one INFO line "brd flamelash <mechanic> ..."
 * (module.dungeonbosses); `.dbtest brd flamelash ...` fires one mechanic on demand.
 */

#include "ArenaGuard.h"
#include "BlackrockDepthsKit.h"
#include "BlackrockDepthsRework.h"
#include "BlackrockDepthsTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "FlamelashLogic.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ThreatManager.h"
#include <algorithm>
#include <cmath>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdFlamelash;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBoss = "flamelash";

    // How long a dead spirit or anchor lies before it goes (the corpse of an anchor is the destroyed portal).
    uint32 constexpr kSpiritCorpseMs = 4000;
    uint32 constexpr kAnchorCorpseMs = 3000;
    uint32 constexpr kArrivalVanishMs = 400;

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // A player the fight acts on: in the world, alive, not a game master.
    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    // The generic stalker 300796 (the trail patches' look) is the orchestrator's template: without it the look is
    // skipped, never an error line per patch (the registry's ring is the telegraph either way).
    bool StalkerExists()
    {
        return sObjectMgr->GetCreatureTemplate(NPC_BRD_STALKER) != nullptr;
    }

    // The floor under a point: the map's height within 4 yd of `refZ`, else `refZ`.
    float GroundZ(WorldObject const* probe, float x, float y, float refZ)
    {
        float const h = probe->GetMapHeight(x, y, refZ + 2.f);
        if (h <= INVALID_HEIGHT || std::fabs(h - refZ) > 4.f)
            return refZ;
        return h;
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// Burning Spirit 9178: it only marches (the boss owns the clock, the arrival and the cap), re-aimed every half second
// so a slow, a root or a stun holds it back. Passive: it never attacks, and nothing here evades.
// ---------------------------------------------------------------------------------------------------------------------
struct npc_burning_spirit_rework : public ScriptedAI
{
    explicit npc_burning_spirit_rework(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }

    // Never a walk home or a despawn of its own: the boss's reset and death despawn every summon.
    void EnterEvadeMode(EvadeReason /*why*/) override { }

    // The boss starts the march: `speed` yd/s toward him.
    void March(ObjectGuid boss, float speed)
    {
        _boss = boss;
        _speed = speed;
        _marching = true;
        _aimMs = 0;
        Aim();
    }

    void UpdateAI(uint32 diff) override
    {
        if (!_marching)
            return;
        _aimMs += diff;
        if (_aimMs < kSpiritReaimMs)
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
        Creature* boss = ObjectAccessor::GetCreature(*me, _boss);
        if (!boss || !boss->IsAlive())
            return;
        // A slow on the spirit cuts its march (its run speed rate against the template's).
        float rate = 1.f;
        if (CreatureTemplate const* t = me->GetCreatureTemplate())
            if (t->speed_run > 0.f)
                rate = std::clamp(me->GetSpeedRate(MOVE_RUN) / t->speed_run, 0.1f, 1.5f);
        me->GetMotionMaster()->MovePoint(1, boss->GetPositionX(), boss->GetPositionY(), boss->GetPositionZ(),
            FORCED_MOVEMENT_RUN, _speed * rate);
    }

    ObjectGuid _boss;
    float _speed = kSpiritMaxSpeed;
    uint32 _aimMs = 0;
    bool _marching = false;
};

// ---------------------------------------------------------------------------------------------------------------------
// Portal Anchor 300842: a stationary add on a rune. Passive, no melee; the boss spills its spirits.
// ---------------------------------------------------------------------------------------------------------------------
struct npc_brd_portal_anchor_rework : public ScriptedAI
{
    explicit npc_brd_portal_anchor_rework(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void EnterEvadeMode(EvadeReason /*why*/) override { }
    void UpdateAI(uint32 /*diff*/) override { }
};

// ---------------------------------------------------------------------------------------------------------------------
// Ambassador Flamelash 9156
// ---------------------------------------------------------------------------------------------------------------------
struct boss_ambassador_flamelash_rework : public BossAI
{
    explicit boss_ambassador_flamelash_rework(Creature* creature)
        : BossAI(creature, BOSS_FLAMELASH), _arena(FightArena(), LeashOptions(kBoss)) { }

private:
    struct AnchorState
    {
        ObjectGuid guid;
        std::size_t rune = 0;
        uint64 nextSpillMs = 0;
        uint32 spilled = 0;
    };

    struct KindlingState
    {
        bool active = false;
        ObjectGuid target;
        uint64 startedMs = 0;
        uint32 ticks = 0;
        uint32 hits = 0;
        uint32 trails = 0;
        MechanicHandle handle;
    };

public:

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

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
        if (!_heroicForced)
            _heroic = IsHeroicMap(me);
        _heroicForced = false;
        OnBossPull(me, kBoss);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_FLAMELASH;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        Talk(SAY_PULL);

        _fighting = true;
        _blastClock.Start(_clockMs, kFireBlastFirstMs);
        _portalClock.Start(_clockMs, kPortalFirstMs(_heroic));
        _kindlingClock.Start(_clockMs, kKindlingFirstMs);
        _nextTankSpotMs = _clockMs;
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "engage",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f}) portals={}s/{}s kindling={}s/{}s",
                _heroic ? 1 : 0, me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(),
                kPortalFirstMs(_heroic) / 1000, kPortalEveryMs(_heroic) / 1000, kKindlingFirstMs / 1000,
                kKindlingEveryMs(_heroic) / 1000));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        Talk(SAY_DEATH);
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "death",
            Acore::StringFormat("portals={} anchors-destroyed={} spirits={} arrived={} killed={} kindlings={} "
                "stacks={} killer={}", _portals, _anchorsDestroyed, _spiritsSpilled, _spiritsArrived, _spiritsKilled,
                _kindlings, Stacks(), killer ? killer->GetName() : std::string("none")));
        Cleanup();
    }

    // The anchors, the spirits and the stalkers are his summons (they go with his reset and death) but never zone into
    // his fight: the boss adds the players to their threat itself (at 0).
    void JustSummoned(Creature* summon) override
    {
        if (!summon)
            return;
        summons.Summon(summon);
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        // These also run out of combat: a `.dbtest` portal on an idle boss still spills and marches.
        UpdateAnchors();
        PollSpirits();
        UpdateKindling();
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_fighting)
            return;

        RunBeats();
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;     // Kindling's channel: no swing while it lasts
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The beats
    // ----------------------------------------------------------------------------------------------------------------

    void RunBeats()
    {
        // The instants are triggered: they never wait for a cast and never break Kindling's channel.
        if (_blastClock.Due(_clockMs))
        {
            if (CastFireBlast())
                _blastClock.Fired(_clockMs, kFireBlastEveryMs);
            else
                _blastClock.Start(_clockMs, kFireBlastRetryMs);
        }
        if (_portalClock.Due(_clockMs))
        {
            if (OpenPortal(-1))
                _portalClock.Fired(_clockMs, kPortalEveryMs(_heroic));
            else
                _portalClock.Start(_clockMs, kPortalRetryMs);
        }
        if (_kindlingClock.Due(_clockMs) && !_kindling.active)
        {
            if (StartKindling(nullptr))
                _kindlingClock.Fired(_clockMs, kKindlingEveryMs(_heroic));
            else
                _kindlingClock.Start(_clockMs, kKindlingRetryMs);    // casting, or nobody to pick: try shortly
        }
        if (_clockMs >= _nextTankSpotMs)
        {
            PostTankSpot();
            _nextTankSpotMs = _clockMs + kTankSpotMs;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // FL1 Fire Blast
    // ----------------------------------------------------------------------------------------------------------------

    bool CastFireBlast()
    {
        Unit* victim = me->GetVictim();
        if (!victim || !me->IsWithinDist(victim, kFireBlastRangeYd))
            return false;
        me->CastSpell(victim, SPELL_FL_FIRE_BLAST, true);
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "fire-blast",
            Acore::StringFormat("target={} pct={:.1f} stacks={}", victim->GetName(),
                ScaledPct(SPELL_FL_FIRE_BLAST, _heroic, Stacks()), Stacks()));
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // FL2 Firelands Portals: the anchors
    // ----------------------------------------------------------------------------------------------------------------

    // The runes with an anchor up now (bit per rune).
    uint32 BusyMask() const
    {
        uint32 mask = 0;
        for (AnchorState const& a : _anchors)
            mask |= 1u << a.rune;
        return mask;
    }

    // Opens the next rune (`forced` >= 0: that one, a test). False: every rune has an anchor up, the summon was
    // refused, or the forced rune is busy.
    bool OpenPortal(int forced)
    {
        uint32 const busy = BusyMask();
        std::optional<std::size_t> pick;
        if (forced >= 0)
        {
            if (static_cast<std::size_t>(forced) >= kRuneCount || (busy & (1u << forced)))
            {
                DungeonKit::LogMechanic(kLogDungeon, kBoss, "portal-refused",
                    Acore::StringFormat("rune={} busy={:#x}", forced, busy));
                return false;
            }
            pick = static_cast<std::size_t>(forced);
        }
        else
            pick = PickRune(_lastRune, busy, [](uint32 n) { return n ? urand(0, n - 1) : 0u; });
        if (!pick)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBoss, "portal-none",
                Acore::StringFormat("anchors={} every rune has an anchor up", _anchors.size()));
            return false;
        }

        Rune const& rune = kRunes[*pick];
        float const z = GroundZ(me, rune.x, rune.y, rune.z);
        float const facing = DungeonKit::BearingTo({ rune.x, rune.y }, kChamberCenter);
        TempSummon* anchor = me->SummonCreature(NPC_BRD_PORTAL_ANCHOR, Position(rune.x, rune.y, z, facing),
            TEMPSUMMON_CORPSE_TIMED_DESPAWN, kAnchorCorpseMs);
        if (!anchor)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBoss, "portal-refused",
                Acore::StringFormat("rune={} the anchor was not created", *pick));
            return false;
        }
        anchor->SetReactState(REACT_PASSIVE);
        Mechanic::TrackUnit(me, anchor);
        AddFightThreat(anchor);
        anchor->CastSpell(anchor, SPELL_FL_PORTAL, true);
        TurnRune(*pick, true);
        _anchors.push_back({ anchor->GetGUID(), *pick, _clockMs + kSpillEveryMs(_heroic), 0 });
        _lastRune = static_cast<int>(*pick);
        ++_portals;
        Talk(SAY_PORTAL);
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "portal",
            Acore::StringFormat("rune={} range={:.1f} at=({:.1f}, {:.1f}, {:.1f}) anchors={} spill={}s", *pick,
                RuneRange(*pick), rune.x, rune.y, z, _anchors.size(), kSpillEveryMs(_heroic) / 1000));
        return true;
    }

    // Each anchor: gone (destroyed or despawned) or due to spill.
    void UpdateAnchors()
    {
        Map* map = me->GetMap();
        if (!map)
            return;
        for (auto it = _anchors.begin(); it != _anchors.end();)
        {
            Creature* anchor = map->GetCreature(it->guid);
            if (!anchor || !anchor->IsAlive())
            {
                AnchorDown(*it, anchor);
                it = _anchors.erase(it);
                continue;
            }
            if (_clockMs >= it->nextSpillMs)
            {
                SpillSpirit(*it, anchor);
                it->nextSpillMs = _clockMs + kSpillEveryMs(_heroic);
            }
            ++it;
        }
    }

    void AnchorDown(AnchorState const& state, Creature* anchor)
    {
        ++_anchorsDestroyed;
        TurnRune(state.rune, false);
        if (anchor)
            anchor->DespawnOrUnsummon(Ms(1500));
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "anchor-destroyed",
            Acore::StringFormat("rune={} spilled={} anchors-left={}", state.rune, state.spilled,
                _anchors.empty() ? 0 : _anchors.size() - 1));
    }

    // The rune's cosmetic object burns while its anchor stands (the stock Doodad_DarkIronDwarfRune buttons).
    void TurnRune(std::size_t index, bool on)
    {
        if (index >= kRuneCount)
            return;
        if (GameObject* rune = me->FindNearestGameObject(kRunes[index].goEntry, 200.f))
            rune->SetGoState(on ? GO_STATE_ACTIVE : GO_STATE_READY);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // FL2 / FL3 the Burning Spirits
    // ----------------------------------------------------------------------------------------------------------------

    void SpillSpirit(AnchorState& state, Creature* anchor)
    {
        PruneSpirits();
        if (!CanSpill(static_cast<uint32>(_spirits.size()), _heroic))
        {
            DungeonKit::LogMechanic(kLogDungeon, kBoss, "spirit-capped",
                Acore::StringFormat("rune={} alive={} cap={}", state.rune, _spirits.size(), kSpiritCap(_heroic)));
            return;
        }
        TempSummon* spirit = me->SummonCreature(NPC_BURNING_SPIRIT, anchor->GetPosition(),
            TEMPSUMMON_CORPSE_TIMED_DESPAWN, kSpiritCorpseMs);
        if (!spirit)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBoss, "spirit-refused",
                Acore::StringFormat("rune={} the spirit was not created", state.rune));
            return;
        }
        spirit->SetReactState(REACT_PASSIVE);
        Mechanic::TrackUnit(me, spirit);
        AddFightThreat(spirit);
        float const range = anchor->GetExactDist2d(me);
        float const speed = SpiritSpeed(range);
        if (auto* ai = dynamic_cast<npc_burning_spirit_rework*>(spirit->AI()))
            ai->March(me->GetGUID(), speed);
        _spirits.push_back(spirit->GetGUID());
        ++state.spilled;
        ++_spiritsSpilled;
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "spirit",
            Acore::StringFormat("rune={} range={:.1f} speed={:.2f} eta={:.1f}s alive={}", state.rune, range, speed,
                speed > 0.f ? range / speed : 0.f, _spirits.size()));
    }

    // Spirits the map still has alive; the dead (killed by the group) are counted once.
    void PruneSpirits()
    {
        Map* map = me->GetMap();
        for (auto it = _spirits.begin(); it != _spirits.end();)
        {
            Creature* spirit = map ? map->GetCreature(*it) : nullptr;
            if (spirit && spirit->IsAlive())
            {
                ++it;
                continue;
            }
            if (spirit)
            {
                ++_spiritsKilled;
                DungeonKit::LogMechanic(kLogDungeon, kBoss, "spirit-killed",
                    Acore::StringFormat("killed={}", _spiritsKilled));
            }
            it = _spirits.erase(it);
        }
    }

    // Each spirit within his reach has arrived: his stack, the spirit goes.
    void PollSpirits()
    {
        Map* map = me->GetMap();
        if (!map || !me->IsAlive() || _spirits.empty())
            return;
        PruneSpirits();
        for (auto it = _spirits.begin(); it != _spirits.end();)
        {
            Creature* spirit = map->GetCreature(*it);
            if (spirit && Arrived(spirit->GetExactDist2d(me), me->GetCombatReach()))
            {
                Arrive(spirit);
                it = _spirits.erase(it);
                continue;
            }
            ++it;
        }
    }

    void Arrive(Creature* spirit)
    {
        uint32 const before = Stacks();
        uint32 const stacks = DungeonKit::AddStacks(me, SPELL_FL_BURNING_SPIRIT,
            static_cast<int32>(StacksAfterArrival(before)) - static_cast<int32>(before), me, kStackCap);
        me->CastSpell(me, SPELL_FL_ARRIVAL_LOOK, true);
        spirit->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        spirit->SetUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
        spirit->DespawnOrUnsummon(Ms(kArrivalVanishMs));
        ++_spiritsArrived;
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "arrive",
            Acore::StringFormat("stacks={} damage=x{:.1f} size=x{:.2f} arrived={}", stacks, DamageScale(stacks),
                SizeScale(stacks), _spiritsArrived));
    }

    uint32 Stacks() const
    {
        return DungeonKit::Stacks(me, SPELL_FL_BURNING_SPIRIT);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // FL4 Kindling
    // ----------------------------------------------------------------------------------------------------------------

    bool StartKindling(Player* forced)
    {
        if (_kindling.active || me->HasUnitState(UNIT_STATE_CASTING))
            return false;
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.tankIfAlone = true;
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!target)
            return false;
        SpellCastResult const result = me->CastSpell(target, SPELL_FL_KINDLING, false);
        if (result != SPELL_CAST_OK)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBoss, "kindling-failed",
                Acore::StringFormat("target={} result={}", target->GetName(), static_cast<uint32>(result)));
            return false;
        }
        me->CastSpell(target, SPELL_FL_KINDLED, true);
        Talk(EMOTE_KINDLING, target);
        // Telegraph only (the script ticks): everyone else keeps their distance from the target for the whole channel.
        MechanicRef ref = Mechanic::RunOut(me, target, kKindlingRadius(_heroic), Ms(kKindlingMs));
        ref.Tag(TAG_FL_KINDLING);
        _kindling = KindlingState();
        _kindling.active = true;
        _kindling.target = target->GetGUID();
        _kindling.startedMs = _clockMs;
        _kindling.handle = ref.Handle();
        ++_kindlings;
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "kindling",
            Acore::StringFormat("target={} radius={:.0f} others={:.1f}% self={:.1f}% stacks={} tank={}",
                target->GetName(), kKindlingRadius(_heroic),
                ScaledPct(SPELL_FL_KINDLING_BURN, _heroic, Stacks()),
                ScaledPct(SPELL_FL_KINDLING_SELF, _heroic, Stacks()), Stacks(),
                target == me->GetVictim() ? 1 : 0));
        return true;
    }

    // The ticks of the channel on the AI's clock; the channel's end (or its target's) ends them.
    void UpdateKindling()
    {
        if (!_kindling.active)
            return;
        Player* target = ObjectAccessor::GetPlayer(*me, _kindling.target);
        if (!CountsAsPlayer(target) || !me->IsAlive())
        {
            EndKindling("target-gone");
            return;
        }
        if (_clockMs >= _kindling.startedMs + kKindlingStartGraceMs
            && !me->FindCurrentSpellBySpellId(SPELL_FL_KINDLING))
        {
            EndKindling("channel-ended");
            return;
        }
        while (_kindling.ticks < kKindlingTicks
            && _clockMs >= _kindling.startedMs + (_kindling.ticks + 1) * kKindlingTickMs)
        {
            ++_kindling.ticks;
            KindlingTick(target);
        }
        if (_kindling.ticks >= kKindlingTicks)
            EndKindling("done");
    }

    // Every other player of the fight within reach of the target burns, the target burns less, and on heroic a trail
    // patch forms under them every second tick.
    void KindlingTick(Player* target)
    {
        uint32 hits = 0;
        for (Player* player : FightPlayers())
        {
            if (player == target)
                continue;
            if (!InKindling(player->GetExactDist2d(target), player->GetPositionZ() - target->GetPositionZ(), _heroic))
                continue;
            me->CastSpell(player, SPELL_FL_KINDLING_BURN, true);
            ++hits;
        }
        me->CastSpell(target, SPELL_FL_KINDLING_SELF, true);
        _kindling.hits += hits;
        bool trail = false;
        if (TrailOnTick(_kindling.ticks, _heroic, _kindling.trails))
        {
            PlaceTrail(target->GetPosition());
            ++_kindling.trails;
            trail = true;
        }
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "kindling-tick",
            Acore::StringFormat("tick={} hits={} trail={}", _kindling.ticks, hits, trail ? 1 : 0));
    }

    void EndKindling(char const* how)
    {
        if (!_kindling.active)
            return;
        KindlingState const state = _kindling;
        _kindling = KindlingState();
        if (state.handle)
            Mechanic::Cancel(me, state.handle);
        if (me->FindCurrentSpellBySpellId(SPELL_FL_KINDLING))
            me->InterruptNonMeleeSpells(false, SPELL_FL_KINDLING);
        if (Player* target = ObjectAccessor::GetPlayer(*me, state.target))
            target->RemoveAurasDueToSpell(SPELL_FL_KINDLED);
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "kindling-end",
            Acore::StringFormat("how={} ticks={} hits={} trails={}", how, state.ticks, state.hits, state.trails));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // FL5 Burning Trail (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    // A 4 yd patch at `at` for 15 s: a persistent registry Zone (the damage, the bots' hazard) under a stalker's lava
    // look. The registry percent is set here, so his stack at the patch's creation is the one it keeps.
    void PlaceTrail(Position const& where)
    {
        // On the floor, whatever the carrier was doing (a jump) when the patch formed.
        Position const at(where.GetPositionX(), where.GetPositionY(),
            GroundZ(me, where.GetPositionX(), where.GetPositionY(), where.GetPositionZ()), 0.f);
        float const pct = ScaledPct(SPELL_FL_TRAIL, _heroic, Stacks());
        MechanicRef ref = Mechanic::Circle(me, at, kTrailRadius, Ms(kTrailWarnMs));
        ref.Persistent(Ms(kTrailLifeMs - kTrailWarnMs), Ms(kTrailTickMs)).Damage(pct).TankDamage(pct)
            .School(SPELL_SCHOOL_FIRE).Spell(SPELL_FL_TRAIL).NoFillTimer().Tag(TAG_FL_TRAIL);
        Track(ref.Handle());
        bool look = false;
        if (StalkerExists())
            if (TempSummon* stalker = me->SummonCreature(NPC_BRD_STALKER, at, TEMPSUMMON_TIMED_DESPAWN, kTrailLifeMs))
            {
                stalker->CastSpell(stalker, SPELL_FL_TRAIL_LOOK, true);
                look = true;
            }
        ++_trails;
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "trail",
            Acore::StringFormat("at=({:.1f}, {:.1f}, {:.1f}) pct={:.1f}/s look={} patches={}", at.GetPositionX(),
                at.GetPositionY(), at.GetPositionZ(), pct, look ? 1 : 0, _trails));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (S4 "Bots")
    // ----------------------------------------------------------------------------------------------------------------

    // Kill order: Portal Anchor, Burning Spirit, Flamelash. No interrupt or dispel list. Kindling is a RunOut, the
    // trail a persistent Zone (both registry mechanics), the tank has a Spot in the chamber's center.
    // Roles (spec): melee catch spirits near him (4, above the anchor), ranged run to the anchor. A ranged DPS skips a
    // spirit already within kSpiritLateYd of him. The tank lists both adds below the boss, so it keeps Flamelash and
    // its stock assist stands down (MechanicTargetRules lowerListed).
    void Describe()
    {
        using BossMechanics::Condition;
        using BossMechanics::TargetEntry;
        using BossMechanics::Who;
        BossMechanics::Descriptor d;
        d.targets.push_back(TargetEntry(NPC_BURNING_SPIRIT, 4, Who::Melee).AoeOk());
        d.targets.push_back(TargetEntry(NPC_BRD_PORTAL_ANCHOR, 3, Who::Dps));
        d.targets.push_back(TargetEntry(NPC_BURNING_SPIRIT, 2, Who::Ranged,
            Condition::Not(Condition::NearUnit(NPC_FLAMELASH, kSpiritLateYd))).AoeOk());
        d.targets.push_back(TargetEntry(NPC_BURNING_SPIRIT, -1, Who::Tank));
        d.targets.push_back(TargetEntry(NPC_BRD_PORTAL_ANCHOR, -1, Who::Tank));
        Mechanic::Describe(me, std::move(d));
    }

    // The main tank's Spot in the chamber's center (bots only: no marker), re-posted every kTankSpotMs. The spirits
    // then arrive from every rune at about the same range.
    void PostTankSpot()
    {
        Unit* victim = me->GetVictim();
        Player* tank = victim ? victim->ToPlayer() : nullptr;
        if (!CountsAsPlayer(tank))
            return;
        std::unordered_map<ObjectGuid, Position> spots;
        spots[tank->GetGUID()] = Position(kChamberCenter.x, kChamberCenter.y,
            GroundZ(me, kChamberCenter.x, kChamberCenter.y, kChamberZ), 0.f);
        MechanicRef ref = Mechanic::Spot(me, spots, Ms(kTankSpotMs), kTankSpotRadius);
        ref.NoTelegraph().Tag(TAG_FL_TANK_SPOT);
        Track(ref.Handle());
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brd flamelash` entry points (the numbers are the map's difficulty; `heroic` forces the form)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Portal,
        Spirit,
        Kindling,
        Trail,
        Stack,
        Blast,
        Clear,
    };

    // An empty string when fired; otherwise why not. `who` is the GM's selected player (or the GM), `n` a count.
    std::string TestFire(TestMechanic mechanic, Player* who, int n)
    {
        switch (mechanic)
        {
            case TestMechanic::Portal:
                if (!OpenPortal(n))
                    return "No portal opened (see the log: the rune is busy, or every rune has an anchor up).";
                break;
            case TestMechanic::Spirit:
            {
                UpdateAnchors();
                if (_anchors.empty())
                    return "No anchor is up (`.dbtest brd flamelash portal` first).";
                Creature* anchor = me->GetMap()->GetCreature(_anchors.front().guid);
                if (!anchor)
                    return "The anchor is gone.";
                SpillSpirit(_anchors.front(), anchor);
                break;
            }
            case TestMechanic::Kindling:
                if (!me->IsEngaged())
                    return "Flamelash must be in combat (the picks read his threat list, the mechanics his encounter).";
                if (_kindling.active || me->HasUnitState(UNIT_STATE_CASTING))
                    return "He is casting already.";
                if (!CountsAsPlayer(who))
                    return "No living player without GM mode selected (`.gm off`).";
                if (!StartKindling(who))
                    return "Kindling did not start (see the log).";
                break;
            case TestMechanic::Trail:
                if (!who)
                    return "No player to put a patch under.";
                PlaceTrail(who->GetPosition());
                break;
            case TestMechanic::Stack:
            {
                uint32 const before = Stacks();
                uint32 const to = static_cast<uint32>(std::clamp<int>(static_cast<int>(before) + (n ? n : 1), 0,
                    static_cast<int>(kStackCap)));
                DungeonKit::AddStacks(me, SPELL_FL_BURNING_SPIRIT, static_cast<int32>(to) - static_cast<int32>(before),
                    me, kStackCap);
                break;
            }
            case TestMechanic::Blast:
                if (!me->GetVictim())
                    return "No victim to blast.";
                CastFireBlast();
                break;
            case TestMechanic::Clear:
                Cleanup();
                break;
        }
        return {};
    }

    // `.dbtest brd flamelash heroic <0|1>`: the heroic form on a normal map (and back) until the end of the next pull.
    void TestHeroic(bool heroic)
    {
        _heroic = heroic;
        _heroicForced = true;
    }

    bool HeroicNow() const { return _heroic; }

    std::string TestState() const
    {
        auto left = [this](BeatClock const& c) -> std::string
        {
            return c.On() ? std::to_string(c.DueMs() > _clockMs ? (c.DueMs() - _clockMs) / 1000 : 0) + "s" : "-";
        };
        return Acore::StringFormat("clock={}s heroic={} fighting={} stacks={} anchors={} spirits={} portal={} "
            "kindling={} blast={} kindling-active={} portals={} destroyed={} spilled={} arrived={} killed={} "
            "kindlings={} trails={} live={} summons={}", _clockMs / 1000, _heroic ? 1 : 0, _fighting ? 1 : 0, Stacks(),
            _anchors.size(), _spirits.size(), left(_portalClock), left(_kindlingClock), left(_blastClock),
            _kindling.active ? 1 : 0, _portals, _anchorsDestroyed, _spiritsSpilled, _spiritsArrived, _spiritsKilled,
            _kindlings, _trails, _live.size(), summons.size());
    }

private:
    // The players on his threat list the fight acts on.
    std::vector<Player*> FightPlayers() const
    {
        std::vector<Player*> out;
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
        {
            Unit* unit = ref->GetVictim();
            Player* player = unit ? unit->ToPlayer() : nullptr;
            if (!CountsAsPlayer(player) || !player->IsInMap(me))
                continue;
            out.push_back(player);
        }
        return out;
    }

    // Everyone in the fight on `add`'s threat list at 0, so bots and the group see it in combat; it never attacks.
    void AddFightThreat(Creature* add)
    {
        for (Player* player : FightPlayers())
            add->GetThreatMgr().AddThreat(player, 0.f, nullptr, true, true);
    }

    // A mechanic of the fight (the trail patches, the tank's Spot, a kindling's run-out): kept to cancel it on a reset.
    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 64)      // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 32);
    }

    // The pull's state: no anchor, spirit, stalker or rune burning, nothing registered, no stack on him, no mark on a
    // player (Reset, evade, death, a new pull).
    void Cleanup()
    {
        _kindling = KindlingState();
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        if (me->FindCurrentSpellBySpellId(SPELL_FL_KINDLING))
            me->InterruptNonMeleeSpells(false, SPELL_FL_KINDLING);
        for (std::size_t i = 0; i < kRuneCount; ++i)
            TurnRune(i, false);     // every rune back to the stock "ready" (a dead or reset fight leaves none burning)
        _anchors.clear();
        _spirits.clear();
        summons.DespawnAll();
        _clockMs = 0;
        _blastClock.Stop();
        _portalClock.Stop();
        _kindlingClock.Stop();
        _nextTankSpotMs = 0;
        _lastRune = -1;
        _fighting = false;
        _portals = 0;
        _anchorsDestroyed = 0;
        _spiritsSpilled = 0;
        _spiritsArrived = 0;
        _spiritsKilled = 0;
        _kindlings = 0;
        _trails = 0;
        _arena.Reset();
        me->RemoveAurasDueToSpell(SPELL_FL_BURNING_SPIRIT);
        if (instance)
        {
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_FL_KINDLED);
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_FL_KINDLING);
        }
    }

    DungeonKit::ArenaGuard _arena;
    BeatClock _blastClock;
    BeatClock _portalClock;
    BeatClock _kindlingClock;
    KindlingState _kindling;
    std::vector<AnchorState> _anchors;
    std::vector<ObjectGuid> _spirits;
    std::vector<MechanicHandle> _live;
    uint64 _clockMs = 0;            // ms since the reset: every timer of the fight
    uint64 _nextTankSpotMs = 0;
    int _lastRune = -1;
    uint32 _portals = 0;
    uint32 _anchorsDestroyed = 0;
    uint32 _spiritsSpilled = 0;
    uint32 _spiritsArrived = 0;
    uint32 _spiritsKilled = 0;
    uint32 _kindlings = 0;
    uint32 _trails = 0;
    bool _heroic = false;
    bool _heroicForced = false;     // `.dbtest ... heroic`: kept through the next pull
    bool _fighting = false;
};

namespace
{
    boss_ambassador_flamelash_rework* FindFlamelashAI(ChatHandler* handler)
    {
        Creature* boss = BrdTest::FindBoss(handler, NPC_FLAMELASH);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_ambassador_flamelash_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Flamelash is not running boss_ambassador_flamelash_rework (check the "
                "ScriptName, and that wave 2 is bound).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_ambassador_flamelash_rework::TestMechanic mechanic, char const* what,
        int n = 0)
    {
        boss_ambassador_flamelash_rework* ai = FindFlamelashAI(handler);
        if (!ai)
            return false;
        Player* who = handler->GetSession() ? handler->getSelectedPlayerOrSelf() : nullptr;
        std::string const error = ai->TestFire(mechanic, who, n);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Flamelash: {} fired ({}).", what, ai->HeroicNow() ? "heroic numbers" :
            "normal numbers");
        return true;
    }

    // `.dbtest brd flamelash info`
    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowBossInfo(handler, NPC_FLAMELASH, BOSS_FLAMELASH);
    }

    // `.dbtest brd flamelash state`: his clocks and what stands.
    bool HandleState(ChatHandler* handler)
    {
        boss_ambassador_flamelash_rework* ai = FindFlamelashAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Flamelash: {}", ai->TestState());
        return true;
    }

    // `.dbtest brd flamelash portal [rune 0-6]`: FL2 now (a random free rune, never the last one).
    bool HandlePortal(ChatHandler* handler, Optional<uint32> rune)
    {
        return Fire(handler, boss_ambassador_flamelash_rework::TestMechanic::Portal,
            "Firelands Portal (FL2: an anchor on a rune, a spirit every 3 s, 2 s heroic)",
            rune ? static_cast<int>(*rune) : -1);
    }

    // `.dbtest brd flamelash spirit`: one Burning Spirit from the first anchor, now.
    bool HandleSpirit(ChatHandler* handler)
    {
        return Fire(handler, boss_ambassador_flamelash_rework::TestMechanic::Spirit,
            "Burning Spirit (FL3: it marches on him and adds a stack)");
    }

    // `.dbtest brd flamelash kindling`: FL4 on the selected player (Flamelash in combat).
    bool HandleKindling(ChatHandler* handler)
    {
        return Fire(handler, boss_ambassador_flamelash_rework::TestMechanic::Kindling,
            "Kindling (FL4: an 8 s channel; everyone else within 8 yd, 10 heroic, burns every second)");
    }

    // `.dbtest brd flamelash trail`: FL5, a Burning Trail patch under the selected player (any difficulty).
    bool HandleTrail(ChatHandler* handler)
    {
        return Fire(handler, boss_ambassador_flamelash_rework::TestMechanic::Trail,
            "Burning Trail (FL5: a 4 yd patch for 15 s, any difficulty)");
    }

    // `.dbtest brd flamelash stack [n]`: n more Burning Spirit stacks (10 at most; negative removes).
    bool HandleStack(ChatHandler* handler, Optional<int32> count)
    {
        return Fire(handler, boss_ambassador_flamelash_rework::TestMechanic::Stack,
            "Burning Spirit stacks (FL3: +10% damage and +5% size each)", count.value_or(1));
    }

    // `.dbtest brd flamelash blast`: FL1 now, on his victim.
    bool HandleBlast(ChatHandler* handler)
    {
        return Fire(handler, boss_ambassador_flamelash_rework::TestMechanic::Blast, "Fire Blast (FL1)");
    }

    // `.dbtest brd flamelash clear`: every anchor, spirit, patch and stack goes.
    bool HandleClear(ChatHandler* handler)
    {
        return Fire(handler, boss_ambassador_flamelash_rework::TestMechanic::Clear, "clear");
    }

    // `.dbtest brd flamelash heroic [0|1]`
    bool HandleHeroic(ChatHandler* handler, Optional<uint32> on)
    {
        boss_ambassador_flamelash_rework* ai = FindFlamelashAI(handler);
        if (!ai)
            return false;
        ai->TestHeroic(!on || *on != 0);
        handler->SendSysMessage("The heroic form is set until the end of the next pull.");
        return true;
    }

    ChatCommandTable const& BossAmbassadorFlamelashTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",    HandleState,    SEC_GAMEMASTER, Console::No },
            { "portal",   HandlePortal,   SEC_GAMEMASTER, Console::No },
            { "spirit",   HandleSpirit,   SEC_GAMEMASTER, Console::No },
            { "kindling", HandleKindling, SEC_GAMEMASTER, Console::No },
            { "trail",    HandleTrail,    SEC_GAMEMASTER, Console::No },
            { "stack",    HandleStack,    SEC_GAMEMASTER, Console::No },
            { "blast",    HandleBlast,    SEC_GAMEMASTER, Console::No },
            { "clear",    HandleClear,    SEC_GAMEMASTER, Console::No },
            { "heroic",   HandleHeroic,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

// His own damage: a percent of the reference row (the tank row on the tank) times his Burning Spirit stack, set at
// launch (FlamelashLogic.h ScaledPct; the spells ignore caster modifiers, rule 2). Fire Blast and both Kindling ticks.
class spell_brd_flamelash_damage : public SpellScript
{
    PrepareSpellScript(spell_brd_flamelash_damage);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;
        float const pct = ScaledPct(GetSpellInfo()->Id, IsHeroicMap(caster),
            DungeonKit::Stacks(caster, SPELL_FL_BURNING_SPIRIT));
        SetEffectValue(static_cast<int32>(DungeonKit::RefFlatOn(caster, GetHitUnit(), pct)));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_brd_flamelash_damage::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

void AddSC_boss_ambassador_flamelash_rework()
{
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_ambassador_flamelash_rework, BlackrockDepthsRework::kInstanceScriptName);
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_burning_spirit_rework, BlackrockDepthsRework::kInstanceScriptName);
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_brd_portal_anchor_rework, BlackrockDepthsRework::kInstanceScriptName);
    RegisterSpellScript(spell_brd_flamelash_damage);
    BrdTest::RegisterBoss("flamelash", BossAmbassadorFlamelashTestCommands());
}
