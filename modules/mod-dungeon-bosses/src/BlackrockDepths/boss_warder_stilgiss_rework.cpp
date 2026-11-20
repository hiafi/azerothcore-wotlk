/*
 * mod-dungeon-bosses, Blackrock Depths D8: Warder Stilgiss (9041) and Verek (9042), "The Antiquarian of Blackrock
 * City". Build spec SP 353-407 (docs/dungeons/blackrock-depths-2-shadowforge-city.md, rulings 40, 41 and 88), handoff
 * section 3.4 rows D8 and section 3.5 row D8. Replaces their SmartAI (the rows are dropped by the S0 SQL rev): the
 * creature templates are bound by apps/dbc-tools source/npcs/blackrock_depths/stilgiss_verek.py. One encounter, one
 * slot (BOSS_STILGISS_VEREK, 6): the INSTANCE sets it DONE once both are dead (OnUnitDeath, whoever dies last), which
 * is what starts the Vault; neither AI writes the slot. Pure rules: StilgissVerekLogic.h.
 *
 *   Pull           either one pulls both (DoZoneInCombat in 45 yd and AttackStart on the partner); either one evading
 *                  sends the other home
 *   Verek          melee, held by the tank (the descriptor: TargetEntry MainTank): Curse of Blood on his victim 3-5 s
 *                  in, then every 30-45 s (+10% physical damage taken, 30 s, a Curse); Enrage once below 30% (the
 *                  stock spell and emote)
 *   Stilgiss       no melee, no chase: he walks the rim from coffer to coffer. Frost Armor (stock) out of combat;
 *                  Frostbolt (his copy) at a random player, interruptible; Frost Nova when 2 or more players are
 *                  within 10 yd (a 1.5 s bar, 10 yd, 2 s root)
 *   SV1  Coffers   8 s, then every 25 s (heroic 20 s): he walks to a Relic Coffer door (never the last one), opens it
 *                  for 2 s (the door plays its animation only), then draws a random artifact: no repeats until all
 *                  five are out; he keeps the last 2 (heroic 3), the oldest dropped. An artifact's first use is 3 s
 *                  after its draw
 *   SV2  Eye       every 10 s: a 4 yd line from him through a random player to the wall (2 s marker), 25% / 40% +
 *                  Weakened
 *   SV3  Bindings  every 15 s: two random players (the tank included) chained for 8 s; while more than 8 yd apart
 *                  both take 4% / 6% a second. The registry Stacks (one on each, eligible: the other) are the
 *                  telegraph and the bots' job; the script ticks
 *   SV4  Magma     every 15 s: a 2.5 s bar, then the 4-9 yd band round him, 30% / 45% + Weakened
 *   SV5  Wand      every 12 s: three 3 yd lines across the hall (2 s marker), 20% / 35% + Weakened
 *   SV6  Blood     every 15 s: a 3 yd pool where a random player stood (2 s marker), then 30 s, 4% / 6% a second;
 *                  Verek heals 2% of his health a second while he stands in one (never Stilgiss)
 *   Boss data      kill order Stilgiss (the main tank holds Verek); Frostbolt on the interrupt list (a reward); Curse
 *                  of Blood on the dispel list (a reward); Verek's Enrage on the purge list
 *   Arena          BlackrockDepthsRework::LeashOptions on BlackVaultArena() (no grips) for both units
 *
 * Every timer runs on the AI's own clock; casts and the walk go through the kit's CastQueue (nothing overlaps). Every
 * firing logs one INFO line "brd stilgiss <mechanic> ..." (module.dungeonbosses). Lambdas the registry keeps capture
 * the map and guids only. The Bindings chain and the Black Blood patch use the shared stalker NPC_BRD_STALKER and are
 * only a look: the fight plays without them when the stalker is not declared yet.
 */

#include "ArenaGuard.h"
#include "BlackrockDepthsKit.h"
#include "BlackrockDepthsRework.h"
#include "BlackrockDepthsTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFlow.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "StilgissVerekLogic.h"
#include "StringFormat.h"
#include <algorithm>
#include <array>
#include <functional>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdStilgissVerek;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossKey = "stilgiss";
    char const* const kVerekKey = "verek";
    float constexpr kPullZoneYd = 45.f;                 // the hall and its entrance: nobody from another wing
    float constexpr kPlayerZBandYd = 6.f;               // the registry's own height band for a circle

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // The hall's walls for the bots' planned spots: inside the rim's smallest radius (12.2 yd), on its floor.
    BossMechanics::SpotBounds HallBounds()
    {
        BossMechanics::SpotBounds bounds;
        bounds.Circle(Position(kVaultCenter.x, kVaultCenter.y, -50.f, 0.f), 12.f, -54.f, -46.f);
        return bounds;
    }

    // The other half of the encounter: `guidKey` is kGuidVerek or kGuidBossBase + BOSS_STILGISS_VEREK.
    Creature* PartnerOf(Creature* me, uint32 guidKey)
    {
        InstanceScript* instance = me ? me->GetInstanceScript() : nullptr;
        if (!instance)
            return nullptr;
        ObjectGuid const guid = instance->GetGuidData(guidKey);
        return guid ? ObjectAccessor::GetCreature(*me, guid) : nullptr;
    }

    // Pulling either pulls both: the partner, if alive and not fighting yet, turns on `who` and takes the players of
    // the hall onto its threat list.
    void PullPartner(Creature* me, uint32 guidKey, Unit* who)
    {
        Creature* partner = PartnerOf(me, guidKey);
        if (!partner || !partner->IsAlive() || partner->IsInCombat() || !partner->AI())
            return;
        if (who)
            partner->AI()->AttackStart(who);
        partner->AI()->DoZoneInCombat(partner, kPullZoneYd);
    }

    // Either one evading sends the other home (the fight is one encounter).
    void EvadePartner(Creature* me, uint32 guidKey, CreatureAI::EvadeReason why)
    {
        Creature* partner = PartnerOf(me, guidKey);
        if (partner && partner->IsAlive() && partner->IsInCombat() && partner->AI())
            partner->AI()->EnterEvadeMode(why);
    }

    // R-1-A m7: the encounter's slot is IN_PROGRESS while either one fights (Map::CannotEnter, the combat-res guard
    // and the Feign Death drop read it); DONE stays the instance's (both dead). F-1a's DATA_STILGISS_VEREK_FIGHT does
    // the write. The reset waits for the partner: the second Reset after a wipe is the one that clears the slot.
    void MarkFightStarted(Creature* me)
    {
        if (InstanceScript* instance = me->GetInstanceScript())
            if (instance->GetBossState(BOSS_STILGISS_VEREK) == NOT_STARTED)
                instance->SetData(DATA_STILGISS_VEREK_FIGHT, 1);
    }

    void MarkFightReset(Creature* me, uint32 partnerKey)
    {
        Creature* partner = PartnerOf(me, partnerKey);
        if (partner && partner->IsAlive() && partner->IsInCombat())
            return;
        if (InstanceScript* instance = me->GetInstanceScript())
            if (instance->GetBossState(BOSS_STILGISS_VEREK) == IN_PROGRESS)
                instance->SetData(DATA_STILGISS_VEREK_FIGHT, 0);
    }

    // Every player of the map within `yd` of `at` on the plane (and one floor), alive, never a game master.
    uint32 PlayersWithin(Creature const* center, float yd)
    {
        uint32 n = 0;
        if (Map const* map = center->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player const* player = ref.GetSource())
                    if (player->IsAlive() && !player->IsGameMaster() && center->GetExactDist2d(player) <= yd
                        && std::fabs(player->GetPositionZ() - center->GetPositionZ()) <= kPlayerZBandYd)
                        ++n;
        return n;
    }
}

// Stilgiss: a ScriptedAI on the slot's registry encounter (the instance writes BOSS_STILGISS_VEREK, and BossAI would
// close it at his own death while Verek stands).
struct boss_warder_stilgiss_rework : public ScriptedAI
{
private:
    enum QueueIds : uint32
    {
        Q_COFFER    = 1,
        Q_NOVA      = 2,
        Q_MAGMA     = 3,
        Q_FROSTBOLT = 4,
    };

    enum class CofferState : uint8
    {
        Idle,
        Walking,
        Opening,
    };

    static uint32 constexpr kPointCoffer = 1;
    static uint32 constexpr kRetryMs = 1000;
    static uint8 constexpr kCofferPriority = 3;
    static uint8 constexpr kMechanicPriority = 2;
    static uint8 constexpr kFillerPriority = 0;

    struct Pool
    {
        Position at;
        uint64 startMs = 0;
        ObjectGuid look;
    };

    struct Pair
    {
        bool active = false;
        ObjectGuid a;
        ObjectGuid b;
        uint64 startMs = 0;
        uint64 nextTickMs = 0;
        uint32 ticks = 0;
        uint32 hurtTicks = 0;
        ObjectGuid helper;
        std::vector<MechanicHandle> stacks;
    };

public:
    explicit boss_warder_stilgiss_rework(Creature* creature)
        : ScriptedAI(creature), _arena(BlackVaultArena(), LeashOptions(kBossKey)), _hall(BlackVaultArena()) { }

    void Reset() override
    {
        ScriptedAI::Reset();
        me->SetCombatMovement(false);
        Cleanup();
        _arena.Reset();
        _frostArmorMs = 0;
        MarkFightReset(me, kGuidVerek);
    }

    // He never chases and never swings: a victim change must not cancel his walk to a coffer (ScriptedAI's no-move
    // AttackStart parks the movement every time).
    void AttackStart(Unit* who) override
    {
        if (who)
            me->Attack(who, false);
    }

    void JustEngagedWith(Unit* who) override
    {
        ScriptedAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;

        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        OnBossPull(me, kBossKey);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_STILGISS_VEREK;
        Mechanic::BeginEncounter(me, options);
        MarkFightStarted(me);

        _heroic = IsHeroicMap(me);
        DoZoneInCombat(me, kPullZoneYd);
        PullPartner(me, kGuidVerek, who);
        _arena.Engage(me);
        ScheduleFight();
        Describe();
        Talk(YELL_ST_PULL);
        Log("engage", Acore::StringFormat("heroic={} coffer={}s every={}s active={}", _heroic ? 1 : 0,
            kCofferFirstMs / 1000, kCofferEveryMs(_heroic) / 1000, kMaxActive(_heroic)));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        _arena.Reset();
        ScriptedAI::EnterEvadeMode(why);
        EvadePartner(me, kGuidVerek, why);
    }

    void JustDied(Unit* killer) override
    {
        ScriptedAI::JustDied(killer);
        Cleanup();
        _arena.Reset();
        Talk(YELL_ST_DEATH);
        Log("death", Acore::StringFormat("killer={}", killer ? killer->GetName() : "none"));
    }

    // A cast bar of his kicked or cancelled: the queue's hold ends with it (rule 13). Only Frostbolt can be.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        ScriptedAI::OnSpellFailed(spell);
        if (spell && spell->Id == SPELL_SV_FROSTBOLT && me->IsInCombat())
        {
            _queue.Interrupted(_clockMs);
            Log("frostbolt-interrupted", "reward");
        }
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type == POINT_MOTION_TYPE && id == kPointCoffer && _coffer == CofferState::Walking)
            BeginOpening("arrived", false);
    }

    void UpdateAI(uint32 diff) override
    {
        if (!me->IsInCombat())
        {
            MaintainFrostArmor(diff);
            return;
        }
        if (!UpdateVictim())
            return;

        _clockMs += diff;
        if (!_arena.Update(me, diff))
            return;     // off his hall, or nobody on it for 10 s: evading

        UpdateCoffer();
        UpdateArtifacts();
        UpdateBindings();
        UpdatePools();
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        RunQueue();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The timeline
    // ----------------------------------------------------------------------------------------------------------------

    void ScheduleFight()
    {
        _clockMs = 0;
        _cofferPlannedMs = kCofferFirstMs;
        _queue.Reset();
        _queue.Schedule(Q_COFFER, kCofferFirstMs, kCofferPriority);
        _queue.Schedule(Q_NOVA, kNovaFirstMs, kMechanicPriority);
        _queue.Schedule(Q_FROSTBOLT, 0, kFillerPriority);
    }

    // The queue's one cast at a time: the coffer walk, the Nova, the Magma bar, then the filler Frostbolt.
    void RunQueue()
    {
        std::optional<uint32> const next = _queue.Next(_clockMs);
        if (!next)
            return;
        switch (*next)
        {
            case Q_COFFER:
                StartCoffer();
                return;
            case Q_NOVA:
                RunNova();
                return;
            case Q_MAGMA:
                if (_held.Has(Artifact::Magma))
                    StartMagma();
                else
                    _queue.Cancel(Q_MAGMA);
                return;
            case Q_FROSTBOLT:
                RunFrostbolt();
                return;
            default:
                _queue.Cancel(*next);
                return;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // SV1 The coffer engine
    // ----------------------------------------------------------------------------------------------------------------

    // The queue's coffer turn: walk to a door (never the last one), then open it. The next turn is a cadence from this
    // one's planned start.
    void StartCoffer()
    {
        _cofferPlannedMs = NextDue(_cofferPlannedMs, kCofferEveryMs(_heroic), _clockMs);
        _queue.Started(Q_COFFER, _clockMs, 0);
        _queue.Schedule(Q_COFFER, _cofferPlannedMs, kCofferPriority);
        _queue.SetBusy(true);

        _door = static_cast<int>(NextDoor(_door, urand(0, 255)));
        Point3 const stand = StandPointFor(kCofferDoors[static_cast<std::size_t>(_door)]);
        _coffer = CofferState::Walking;
        _cofferStartMs = _clockMs;
        me->GetMotionMaster()->MovePoint(kPointCoffer, stand.x, stand.y, stand.z);
        Log("coffer-walk", Acore::StringFormat("door={} entry={} stand=({:.1f}, {:.1f}) next={}s", _door,
            kCofferDoorEntries[static_cast<std::size_t>(_door)], stand.x, stand.y, _cofferPlannedMs / 1000));
    }

    void UpdateCoffer()
    {
        if (_coffer == CofferState::Walking && _clockMs - _cofferStartMs > kWalkTimeoutMs)
            BeginOpening("timeout", true);
        else if (_coffer == CofferState::Opening && _clockMs >= _openEndMs)
            FinishOpening();
    }

    // At the door (or after the walk timed out): the 2 s opening. The door plays its animation only: its state, lock
    // and loot never change (SP "Implementation").
    void BeginOpening(char const* why, bool cutWalk)
    {
        _coffer = CofferState::Opening;
        _openEndMs = _clockMs + kOpenMs;
        if (cutWalk)
            me->GetMotionMaster()->Clear();     // never from MovementInform: the walk is over there already
        me->StopMoving();
        if (_door >= 0)
        {
            if (GameObject* door = me->FindNearestGameObject(kCofferDoorEntries[static_cast<std::size_t>(_door)],
                10.f))
                door->SendCustomAnim(0);
        }
        DungeonKit::CastBar(me, SPELL_SV_OPEN_COFFER);
        Log("coffer-open", Acore::StringFormat("why={} door={}", why, _door));
    }

    void FinishOpening()
    {
        _coffer = CofferState::Idle;
        _queue.SetBusy(false);
        DrawArtifact(std::nullopt);
    }

    // The draw: a random artifact, none twice until all five are out; the oldest of the held ones is dropped past the
    // cap. `forced` is a `.dbtest` draw of one artifact.
    void DrawArtifact(std::optional<Artifact> forced)
    {
        Draw draw = DrawNext(_held.drawnMask, _held.ActiveMask(), urand(0, 255));
        if (forced)
            draw = { *forced, static_cast<std::uint8_t>(_held.drawnMask | BitOf(*forced)) };
        _held.drawnMask = draw.drawnMask;
        if (_held.Has(draw.artifact))
        {
            _nextMs[Index(draw.artifact)] = _clockMs + kFirstAfterDrawMs;    // a forced repeat: its clock restarts
        }
        else
        {
            std::optional<Artifact> const dropped = _held.Add(draw.artifact, kMaxActive(_heroic));
            _nextMs[Index(draw.artifact)] = _clockMs + kFirstAfterDrawMs;
            if (dropped)
                ArtifactDropped(*dropped);
        }
        Talk(EmoteOf(draw.artifact));
        std::string held;
        for (std::uint8_t i = 0; i < _held.count; ++i)
            held += Acore::StringFormat("{}{}", i ? "," : "", ArtifactName(_held.kinds[i]));
        Log("draw", Acore::StringFormat("artifact={} held=[{}] cycle={:05b} first={}s", ArtifactName(draw.artifact),
            held, _held.drawnMask, kFirstAfterDrawMs / 1000));
    }

    void ArtifactDropped(Artifact dropped)
    {
        if (dropped == Artifact::Magma)
            _queue.Cancel(Q_MAGMA);
        Log("dropped", Acore::StringFormat("artifact={}", ArtifactName(dropped)));
    }

    static std::size_t Index(Artifact a) { return static_cast<std::size_t>(a); }

    // ----------------------------------------------------------------------------------------------------------------
    // The artifacts' timers: each fires on its own cadence from 3 s after its draw
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateArtifacts()
    {
        for (std::uint8_t i = 0; i < _held.count; ++i)
        {
            Artifact const artifact = _held.kinds[i];
            uint64& next = _nextMs[Index(artifact)];
            if (_clockMs < next)
                continue;
            if (artifact == Artifact::Magma)
            {
                // The bar goes through the queue (it holds his walk and his other casts); the next turn counts from
                // this one's planned start.
                if (!_queue.Queued(Q_MAGMA))
                {
                    _queue.Schedule(Q_MAGMA, _clockMs, kMechanicPriority);
                    next = NextDue(next, ArtifactEveryMs(artifact), _clockMs);
                }
                continue;
            }
            if (Fire(artifact))
                next = NextDue(next, ArtifactEveryMs(artifact), _clockMs);
            else
                next = _clockMs + kRetryMs;
        }
    }

    // One use of an artifact now. False: nobody to aim it at (tried again in a second).
    bool Fire(Artifact artifact)
    {
        switch (artifact)
        {
            case Artifact::Eye:         return FireEye();
            case Artifact::Bindings:    return FireBindings();
            case Artifact::Wand:        return FireWand();
            case Artifact::BlackBlood:  return FireBlood();
            case Artifact::Magma:
                StartMagma();
                return true;
        }
        return false;
    }

    // A pick among every player of the fight, the tank included (ruling 88).
    DungeonKit::PickRule AnyPlayer() const
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        return rule;
    }

    // ---- SV2 Eye of Kajal -----------------------------------------------------------------------------------------

    bool FireEye()
    {
        Player* target = DungeonKit::PickPlayer(me, AnyPlayer());
        if (!target)
            return false;
        float const pct = kEyePct(_heroic);
        DungeonKit::LineStrikeSpec spec;
        spec.width = kEyeWidth;
        spec.overrun = kEyeOverrunYd;
        spec.warn = Ms(kEyeWarnMs);
        spec.pct = pct;
        spec.tankPct = pct;
        spec.school = SPELL_SCHOOL_SHADOW;
        spec.spellId = SPELL_SV_EYE_HIT;
        spec.weakened = true;
        spec.tag = TAG_SV_EYE;
        spec.clip = &_hall;
        DungeonKit::LineStrikeResult const result = DungeonKit::LineStrike(me, me, target, spec);
        Track(result.handle);
        Log("eye", Acore::StringFormat("heroic={} pct={:.0f} target={} length={:.1f}{}", _heroic ? 1 : 0, pct,
            target->GetName(), result.length, result.clipped ? " clipped" : ""));
        return result.handle.IsValid();
    }

    // ---- SV3 Black Steel Bindings ---------------------------------------------------------------------------------

    bool FireBindings()
    {
        if (_pair.active)
            return false;
        std::vector<Player*> const picks = DungeonKit::PickPlayers(me, AnyPlayer(), 2);
        if (picks.size() < 2)
            return false;
        StartPair(picks[0], picks[1]);
        return true;
    }

    // The pair: the debuff on both, a held registry Stack on each of them (the other must keep within 8 yd: only the
    // carrier is eligible, the telegraph and the bots' job; the script ticks, as the Drakkisath brands), the chain
    // look.
    void StartPair(Player* a, Player* b)
    {
        EndPair("replaced");
        _pair = Pair();
        _pair.active = true;
        _pair.a = a->GetGUID();
        _pair.b = b->GetGUID();
        _pair.startMs = _clockMs;
        _pair.nextTickMs = _clockMs + kBindingsTickMs;
        for (Player* player : { a, b })
            me->AddAura(SPELL_SV_BINDINGS, player);
        using Carry = std::pair<Player*, Player*>;
        for (auto const& [carrier, other] : { Carry{ a, b }, Carry{ b, a } })
        {
            BossMechanics::Eligibility who;
            who.carriers.insert(carrier->GetGUID());
            MechanicRef ref = Mechanic::Stack(me, other, kBindingsRangeYd, Ms(kBindingsStackMs));
            ref.Eligible(who).Within(HallBounds()).Tag(TAG_SV_BINDINGS);
            MechanicHandle const handle = ref.Handle();
            Track(handle);
            if (handle)
                _pair.stacks.push_back(handle);
        }
        // The chain: a stalker follows `a` and channels at `b` (a player's own channel would stop him casting).
        if (Creature* helper = me->SummonCreature(NPC_BRD_STALKER, a->GetPosition(), TEMPSUMMON_MANUAL_DESPAWN))
        {
            helper->SetReactState(REACT_PASSIVE);
            helper->GetMotionMaster()->MoveFollow(a, 0.f, 0.f);
            helper->CastSpell(b, SPELL_SV_BINDINGS_CHAIN, true);
            _pair.helper = helper->GetGUID();
        }
        Log("bindings", Acore::StringFormat("heroic={} pct={:.0f}/s a={} b={} apart={:.1f} chain={}", _heroic ? 1 : 0,
            kBindingsPct(_heroic), a->GetName(), b->GetName(), a->GetExactDist2d(b), _pair.helper ? 1 : 0));
    }

    // Every second: both of the pair are hurt while apart; the pair ends at 8 s or when either is gone.
    void UpdateBindings()
    {
        if (!_pair.active)
            return;
        Player* a = ObjectAccessor::GetPlayer(*me, _pair.a);
        Player* b = ObjectAccessor::GetPlayer(*me, _pair.b);
        if (!a || !b || !a->IsAlive() || !b->IsAlive() || a->GetMap() != me->GetMap() || b->GetMap() != me->GetMap())
        {
            EndPair("lost");
            return;
        }
        while (_pair.active && _clockMs >= _pair.nextTickMs && _pair.nextTickMs <= _pair.startMs + kBindingsMs)
        {
            _pair.nextTickMs += kBindingsTickMs;
            ++_pair.ticks;
            if (BindingsApart(DungeonKit::PlaneOf(a), a->GetPositionZ(), DungeonKit::PlaneOf(b), b->GetPositionZ()))
            {
                ++_pair.hurtTicks;
                me->CastSpell(a, SPELL_SV_BINDINGS_TICK, true);
                me->CastSpell(b, SPELL_SV_BINDINGS_TICK, true);
            }
        }
        if (_clockMs >= _pair.startMs + kBindingsMs)
            EndPair("done");
    }

    void EndPair(char const* why)
    {
        if (!_pair.active)
            return;
        for (MechanicHandle const& handle : _pair.stacks)
            Mechanic::Cancel(me, handle);
        for (ObjectGuid const& guid : { _pair.a, _pair.b })
            if (Player* player = ObjectAccessor::GetPlayer(*me, guid))
                player->RemoveAurasDueToSpell(SPELL_SV_BINDINGS);
        if (Creature* helper = ObjectAccessor::GetCreature(*me, _pair.helper))
            helper->DespawnOrUnsummon();
        Log("bindings-end", Acore::StringFormat("why={} ticks={} hurt={}", why, _pair.ticks, _pair.hurtTicks));
        _pair = Pair();
    }

    // ---- SV4 Magma Forged Band ------------------------------------------------------------------------------------

    // The 2.5 s bar (the queue's, Fire), the donut round him registered beside it.
    void StartMagma()
    {
        float const pct = kMagmaPct(_heroic);
        _queue.Started(Q_MAGMA, _clockMs, kMagmaCastMs);
        DungeonKit::CastBar(me, SPELL_SV_MAGMA_CAST);
        MechanicRef ref = Mechanic::Donut(me, me, kMagmaInnerYd, kMagmaOuterYd, Ms(kMagmaCastMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_FIRE).Spell(SPELL_SV_MAGMA_HIT).Weakened()
            .Within(HallBounds()).Tag(TAG_SV_MAGMA);
        ref.OnResolve(OnSv([](boss_warder_stilgiss_rework& ai, BossMechanics::ResolveResult const& result)
        {
            ai.Log("magma-landed", Acore::StringFormat("hits={}", result.hits.size()));
        }));
        Track(ref.Handle());
        Log("magma", Acore::StringFormat("heroic={} pct={:.0f} band={:.0f}-{:.0f}", _heroic ? 1 : 0, pct,
            kMagmaInnerYd, kMagmaOuterYd));
    }

    // ---- SV5 Wand of Eternal Light --------------------------------------------------------------------------------

    bool FireWand()
    {
        float const pct = kWandPct(_heroic);
        std::array<float, kWandLines> offsets{};
        for (float& offset : offsets)
            offset = frand(-kWandMaxOffsetYd, kWandMaxOffsetYd);
        std::array<Chord, kWandLines> const chords = WandChords(frand(0.f, DungeonKit::kPi), offsets);
        float const z = me->GetPositionZ();
        for (Chord const& chord : chords)
        {
            Position const from(chord.from.x, chord.from.y, z, 0.f);
            Position const to(chord.to.x, chord.to.y, z, 0.f);
            MechanicRef ref = Mechanic::Line(me, from, to, kWandWidth, Ms(kWandWarnMs));
            ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_HOLY).Spell(SPELL_SV_WAND_HIT).Weakened()
                .Within(HallBounds()).Tag(TAG_SV_WAND);
            Track(ref.Handle());
        }
        Log("wand", Acore::StringFormat("heroic={} pct={:.0f} lines={} width={:.0f}", _heroic ? 1 : 0, pct,
            kWandLines, kWandWidth));
        return true;
    }

    // ---- SV6 Black Blood of the Tormented -------------------------------------------------------------------------

    // A pool where a random player stands now (the marker is the 2 s warning: he walks off it), then 30 s of 4% / 6%.
    bool FireBlood()
    {
        Player* target = DungeonKit::PickPlayer(me, AnyPlayer());
        if (!target)
            return false;
        PlacePool(target->GetPosition());
        Log("blood", Acore::StringFormat("heroic={} pct={:.0f}/s target={} at=({:.1f}, {:.1f}) pools={}",
            _heroic ? 1 : 0, kBloodPct(_heroic), target->GetName(), target->GetPositionX(), target->GetPositionY(),
            _pools.size()));
        return true;
    }

    void PlacePool(Position const& at)
    {
        float const pct = kBloodPct(_heroic);
        MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::Circle(at, kBloodRadiusYd), Ms(kBloodWarnMs));
        ref.Persistent(Ms(kBloodLifeMs), Ms(kBloodTickMs)).Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_SHADOW)
            .Spell(SPELL_SV_BLOOD_HIT).Within(HallBounds()).Tag(TAG_SV_BLOOD);
        Track(ref.Handle());
        Pool pool;
        pool.at = at;
        pool.startMs = _clockMs;
        if (Creature* look = me->SummonCreature(NPC_BRD_STALKER, at, TEMPSUMMON_MANUAL_DESPAWN))
        {
            look->SetReactState(REACT_PASSIVE);
            look->CastSpell(look, SPELL_SV_BLOOD_LOOK, true);
            pool.look = look->GetGUID();
        }
        _pools.push_back(pool);
    }

    // The pools: an expired one goes (and its patch with it); every second Verek heals 2% while he stands in a live
    // one. Never Stilgiss (designer).
    void UpdatePools()
    {
        if (_pools.empty())
        {
            _verekInPool = false;
            return;
        }
        std::erase_if(_pools, [this](Pool const& pool)
        {
            if (_clockMs < pool.startMs + kBloodWarnMs + kBloodLifeMs)
                return false;
            if (Creature* look = ObjectAccessor::GetCreature(*me, pool.look))
                look->DespawnOrUnsummon();
            return true;
        });
        if (_clockMs < _nextHealMs)
            return;
        _nextHealMs = _clockMs + kBloodTickMs;
        Creature* verek = PartnerOf(me, kGuidVerek);
        bool inPool = false;
        if (verek && verek->IsAlive() && verek->IsInCombat())
            for (Pool const& pool : _pools)
                if (BloodLive(pool.startMs, _clockMs) && InBloodPool(Vec2{ pool.at.GetPositionX(),
                    pool.at.GetPositionY() }, pool.at.GetPositionZ(), DungeonKit::PlaneOf(verek),
                    verek->GetPositionZ()))
                {
                    inPool = true;
                    break;
                }
        if (inPool)
        {
            me->CastSpell(verek, SPELL_SV_BLOOD_HEAL, true);
            ++_healTicks;
        }
        if (inPool != _verekInPool)
        {
            _verekInPool = inPool;
            Log(inPool ? "blood-heal-begins" : "blood-heal-ends", Acore::StringFormat("ticks={} pct={:.0f}/s",
                _healTicks, kBloodHealPct));
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // SV7 Frost Nova, SV8 Frostbolt
    // ----------------------------------------------------------------------------------------------------------------

    // The queue's nova turn: when 2 or more players are within 10 yd of him; else look again in a second.
    void RunNova()
    {
        if (!NovaWanted(PlayersWithin(me, kNovaRadiusYd)))
        {
            _queue.Schedule(Q_NOVA, _clockMs + kRetryMs, kMechanicPriority);
            return;
        }
        StartNova();
    }

    void StartNova()
    {
        float const pct = kNovaPct(_heroic);
        _queue.Started(Q_NOVA, _clockMs, kNovaCastMs);
        _queue.Schedule(Q_NOVA, _clockMs + kNovaEveryMs, kMechanicPriority);
        DungeonKit::CastBar(me, SPELL_SV_NOVA_CAST);
        MechanicRef ref = Mechanic::Circle(me, me, kNovaRadiusYd, Ms(kNovaCastMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_FROST).Spell(SPELL_SV_NOVA_HIT)
            .Rider(SPELL_SV_NOVA_ROOT).Within(HallBounds()).Tag(TAG_SV_NOVA);
        ref.OnResolve(OnSv([](boss_warder_stilgiss_rework& ai, BossMechanics::ResolveResult const& result)
        {
            ai.Log("nova-landed", Acore::StringFormat("hits={}", result.hits.size()));
        }));
        Track(ref.Handle());
        Log("nova", Acore::StringFormat("heroic={} pct={:.0f} radius={:.0f} root={}s", _heroic ? 1 : 0, pct,
            kNovaRadiusYd, kNovaRootMs / 1000));
    }

    // The filler: a bolt at a random player in line of sight, the next one 2.4 to 3.8 s after this one started.
    void RunFrostbolt()
    {
        DungeonKit::PickRule rule = AnyPlayer();
        rule.requireLos = true;
        rule.maxRange = 40.f;
        Player* target = DungeonKit::PickPlayer(me, rule);
        if (!target)
        {
            _queue.Schedule(Q_FROSTBOLT, _clockMs + kRetryMs, kFillerPriority);
            return;
        }
        // R-1-A m6: a refused bolt (the Frost school locked by a kick, sight, range) holds nothing: the queue stays
        // free for the coffer walk, the Nova and the Magma bar, and the log and the bots' note skip it.
        if (me->CastSpell(target, SPELL_SV_FROSTBOLT, false) != SPELL_CAST_OK)
        {
            _queue.Schedule(Q_FROSTBOLT, _clockMs + kRetryMs, kFillerPriority);
            return;
        }
        _queue.Started(Q_FROSTBOLT, _clockMs, kFrostboltCastMs, false);
        _queue.Schedule(Q_FROSTBOLT, _clockMs + urand(kFrostboltGapMinMs, kFrostboltGapMaxMs), kFillerPriority);
        Mechanic::NoteNextCastIn(me, SPELL_SV_FROSTBOLT, Ms(kFrostboltGapMaxMs));
        Log("frostbolt", Acore::StringFormat("heroic={} pct={:.0f} target={}", _heroic ? 1 : 0,
            kFrostboltPct(_heroic), target->GetName()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (SP): the main tank holds Verek, everyone else Stilgiss (the owner, priority 0, kill order first);
    // Frostbolt is a reward to kick, Curse of Blood a reward to dispel, Verek's Enrage the purge.
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        BossMechanics::Descriptor d;
        d.targets.emplace_back(NPC_VEREK, 1, BossMechanics::Who::MainTank);
        d.targets.emplace_back(NPC_VEREK, -1, BossMechanics::Who::Dps);
        d.interrupts.emplace_back(NPC_STILGISS, SPELL_SV_FROSTBOLT, 1, Ms(kFrostboltGapMaxMs));
        d.dispels.emplace_back(SPELL_SV_CURSE_OF_BLOOD, 1);
        d.purges.emplace_back(NPC_VEREK, SPELL_STOCK_ENRAGE, 1);
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Out of combat: Frost Armor (the stock SmartAI row: every 1,800 s, aura not present)
    // ----------------------------------------------------------------------------------------------------------------

    void MaintainFrostArmor(uint32 diff)
    {
        _frostArmorMs = _frostArmorMs > diff ? _frostArmorMs - diff : 0;
        if (_frostArmorMs)
            return;
        _frostArmorMs = 2000;
        if (me->IsAlive() && !me->IsInEvadeMode() && !me->HasAura(SPELL_STOCK_FROST_ARMOR))
            DoCast(me, SPELL_STOCK_FROST_ARMOR, true);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brd stilgiss <mechanic>` entry points (a mechanic out of combat needs players on his threat list)
    // ----------------------------------------------------------------------------------------------------------------

    // An empty string when fired; otherwise why not.
    std::string TestFight() const
    {
        if (!me->IsInCombat())
            return "Stilgiss must be in combat (the picks are the players on his threat list; a GM is skipped).";
        return {};
    }

    std::string TestDraw(std::optional<Artifact> which)
    {
        if (std::string const why = TestFight(); !why.empty())
            return why;
        DrawArtifact(which);
        return {};
    }

    std::string TestCoffer()
    {
        if (std::string const why = TestFight(); !why.empty())
            return why;
        if (_coffer != CofferState::Idle)
            return "He is already at a coffer.";
        StartCoffer();
        return {};
    }

    std::string TestFire(Artifact artifact)
    {
        if (std::string const why = TestFight(); !why.empty())
            return why;
        if (artifact == Artifact::Bindings && _pair.active)
            return "A pair is chained already (8 s).";
        if (!Fire(artifact))
            return "Nobody in the fight to aim it at (a GM does not count; Bindings needs two players).";
        return {};
    }

    std::string TestNova()
    {
        if (std::string const why = TestFight(); !why.empty())
            return why;
        StartNova();
        return {};
    }

    std::string TestFrostbolt()
    {
        if (std::string const why = TestFight(); !why.empty())
            return why;
        RunFrostbolt();
        return {};
    }

    std::string TestState() const
    {
        std::string held;
        for (std::uint8_t i = 0; i < _held.count; ++i)
            held += Acore::StringFormat("{}{}@{}s", i ? " " : "", ArtifactName(_held.kinds[i]),
                _nextMs[Index(_held.kinds[i])] / 1000);
        char const* coffer = _coffer == CofferState::Idle ? "idle" : (_coffer == CofferState::Walking ? "walking" :
            "opening");
        return Acore::StringFormat("clock={}s heroic={} coffer={} door={} next={}s held=[{}] cycle={:05b} pair={} "
            "pools={} queued={} verekInPool={}", _clockMs / 1000, _heroic ? 1 : 0, coffer, _door,
            _cofferPlannedMs / 1000, held, _held.drawnMask, _pair.active ? 1 : 0, _pools.size(), _queue.Size(),
            _verekInPool ? 1 : 0);
    }

private:
    // Runs `fn(ai, result)` on this boss when a mechanic resolves, if he is still there and it is the same pull.
    // Captures the map and the guid only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnSv(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        uint32 const generation = _generation;
        return [map, guid, generation, fn](BossMechanics::ResolveResult const& result)
        {
            if (result.fizzled || !map)
                return;
            Creature* boss = map->GetCreature(guid);
            if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_warder_stilgiss_rework*>(boss->AI()))
                if (ai->_generation == generation)
                    fn(*ai, result);
        };
    }

    void Log(char const* mechanic, std::string const& detail = {}) const
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossKey, mechanic, detail);
    }

    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 96)      // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 48);
    }

    // The pull's state: nothing pending, no chain on anyone, no pool or helper left, nothing held (Reset, evade, death,
    // a new pull). Rule 6: every aura the fight applied, every helper, every registry handle.
    void Cleanup()
    {
        ++_generation;      // a resolve callback of an older pull stops
        EndPair("cleanup");
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        for (Pool const& pool : _pools)
            if (Creature* look = ObjectAccessor::GetCreature(*me, pool.look))
                look->DespawnOrUnsummon();
        _pools.clear();
        if (Map* map = me->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* player = ref.GetSource())
                    for (uint32 spell : { SPELL_SV_BINDINGS, SPELL_SV_BINDINGS_CHAIN, SPELL_SV_FROSTBOLT,
                        SPELL_SV_NOVA_ROOT })
                        player->RemoveAurasDueToSpell(spell);
        _queue.Reset();
        _held.Clear();
        _nextMs.fill(0);
        _coffer = CofferState::Idle;
        _door = -1;
        _clockMs = 0;
        _cofferPlannedMs = 0;
        _cofferStartMs = 0;
        _openEndMs = 0;
        _nextHealMs = 0;
        _healTicks = 0;
        _verekInPool = false;
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::Arena _hall;                    // the Eye's line stops at its wall
    DungeonKit::CastQueue _queue;
    Collection _held;
    Pair _pair;
    std::vector<Pool> _pools;
    std::vector<MechanicHandle> _live;
    std::array<uint64, kArtifactCount> _nextMs{};   // the next use of each artifact (a held one)
    CofferState _coffer = CofferState::Idle;
    uint64 _clockMs = 0;                        // ms since the pull: every timer of the fight
    uint64 _cofferPlannedMs = 0;                // the planned start of the next coffer turn (start to start)
    uint64 _cofferStartMs = 0;
    uint64 _openEndMs = 0;
    uint64 _nextHealMs = 0;
    uint32 _generation = 0;
    uint32 _healTicks = 0;
    uint32 _frostArmorMs = 0;
    int _door = -1;                             // the door of the last coffer turn
    bool _heroic = false;
    bool _verekInPool = false;
};

// Verek: the guard dog. Melee, held by the tank; Curse of Blood and Enrage (both stock beats, the curse changed).
struct npc_verek_rework : public ScriptedAI
{
public:
    explicit npc_verek_rework(Creature* creature)
        : ScriptedAI(creature), _arena(BlackVaultArena(), LeashOptions(kVerekKey)) { }

    void Reset() override
    {
        ScriptedAI::Reset();
        Cleanup();
        _arena.Reset();
        MarkFightReset(me, kGuidBossBase + BOSS_STILGISS_VEREK);
    }

    void JustEngagedWith(Unit* who) override
    {
        ScriptedAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;
        Cleanup();
        MarkFightStarted(me);
        DoZoneInCombat(me, kPullZoneYd);
        PullPartner(me, kGuidBossBase + BOSS_STILGISS_VEREK, who);
        _arena.Engage(me);
        _nextCurseMs = urand(kCurseFirstMinMs, kCurseFirstMaxMs);
        Log("engage", Acore::StringFormat("curse={}ms", _nextCurseMs));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        _arena.Reset();
        ScriptedAI::EnterEvadeMode(why);
        EvadePartner(me, kGuidBossBase + BOSS_STILGISS_VEREK, why);
    }

    void JustDied(Unit* killer) override
    {
        ScriptedAI::JustDied(killer);
        Cleanup();
        _arena.Reset();
        Log("death", Acore::StringFormat("killer={}", killer ? killer->GetName() : "none"));
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;
        _clockMs += diff;
        if (!_arena.Update(me, diff))
            return;     // off the hall, or nobody on it for 10 s: evading

        if (EnrageDue(me->GetHealthPct(), _enraged))
            Enrage("health");
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (_clockMs >= _nextCurseMs)
            CastCurse();
        DoMeleeAttackIfReady();
    }

    // SV9: the curse on his victim (the tank: nobody else is in his reach while the tank holds him).
    void CastCurse()
    {
        Unit* victim = me->GetVictim();
        if (!victim)
        {
            _nextCurseMs = _clockMs + 1000;
            return;
        }
        if (me->CastSpell(victim, SPELL_SV_CURSE_OF_BLOOD, false) != SPELL_CAST_OK)
        {
            _nextCurseMs = _clockMs + 1000;     // out of reach or silenced: tried again in a second
            return;
        }
        _nextCurseMs = _clockMs + urand(kCurseEveryMinMs, kCurseEveryMaxMs);
        Log("curse", Acore::StringFormat("target={} next={}s", victim->GetName(), _nextCurseMs / 1000));
    }

    // SV10: the stock Enrage once, with its stock emote (boss emote 41 now).
    void Enrage(char const* why)
    {
        _enraged = true;
        DoCast(me, SPELL_STOCK_ENRAGE, true);
        Talk(EMOTE_VK_ENRAGE);
        Log("enrage", Acore::StringFormat("why={} health={:.1f}", why, me->GetHealthPct()));
    }

    // `.dbtest brd stilgiss curse / enrage`
    std::string TestCurse()
    {
        if (!me->IsInCombat() || !me->GetVictim())
            return "Verek must be in combat with a victim.";
        CastCurse();
        return {};
    }

    std::string TestEnrage()
    {
        if (!me->IsInCombat())
            return "Verek must be in combat.";
        if (_enraged)
            return "He is enraged already (once a pull).";
        Enrage("test");
        return {};
    }

private:
    void Log(char const* mechanic, std::string const& detail = {}) const
    {
        DungeonKit::LogMechanic(kLogDungeon, kVerekKey, mechanic, detail);
    }

    // Rule 6: the curse on the players is not left behind by a reset, an evade or his death.
    void Cleanup()
    {
        if (Map* map = me->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* player = ref.GetSource())
                    player->RemoveAurasDueToSpell(SPELL_SV_CURSE_OF_BLOOD, me->GetGUID());
        _clockMs = 0;
        _nextCurseMs = 0;
        _enraged = false;
    }

    DungeonKit::ArenaGuard _arena;
    uint64 _clockMs = 0;
    uint64 _nextCurseMs = 0;
    bool _enraged = false;
};

namespace
{
    boss_warder_stilgiss_rework* FindStilgissAI(ChatHandler* handler)
    {
        Creature* boss = BrdTest::FindBoss(handler, NPC_STILGISS);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_warder_stilgiss_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Warder Stilgiss is not running boss_warder_stilgiss_rework (check the "
                "ScriptName).");
        return ai;
    }

    npc_verek_rework* FindVerekAI(ChatHandler* handler)
    {
        Creature* boss = BrdTest::FindBoss(handler, NPC_VEREK);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<npc_verek_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Verek is not running npc_verek_rework (check the ScriptName).");
        return ai;
    }

    bool Finish(ChatHandler* handler, std::string const& error, char const* what)
    {
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Stilgiss: {} fired ({}).", what,
            IsHeroicMap(handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr) ? "heroic" : "normal");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowBossInfo(handler, NPC_STILGISS, BOSS_STILGISS_VEREK);
    }

    bool HandleInfoVerek(ChatHandler* handler)
    {
        return BrdTest::ShowBossInfo(handler, NPC_VEREK, BOSS_STILGISS_VEREK);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_warder_stilgiss_rework* ai = FindStilgissAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Stilgiss: {}", ai->TestState());
        return true;
    }

    // `.dbtest brd stilgiss draw [1-5]`: the next artifact now (1 eye, 2 bindings, 3 magma, 4 wand, 5 blood).
    bool HandleDraw(ChatHandler* handler, Optional<uint32> which)
    {
        boss_warder_stilgiss_rework* ai = FindStilgissAI(handler);
        if (!ai)
            return false;
        std::optional<Artifact> pick;
        if (which)
        {
            if (*which < 1 || *which > kArtifactCount)
            {
                handler->SendErrorMessage("{}", "Artifact 1-5: eye, bindings, magma, wand, blood.");
                return false;
            }
            pick = static_cast<Artifact>(*which - 1);
        }
        return Finish(handler, ai->TestDraw(pick), "a draw (SV1)");
    }

    bool HandleCoffer(ChatHandler* handler)
    {
        boss_warder_stilgiss_rework* ai = FindStilgissAI(handler);
        return ai && Finish(handler, ai->TestCoffer(), "the coffer walk (SV1; the draw follows the opening)");
    }

    bool FireArtifact(ChatHandler* handler, Artifact artifact, char const* what)
    {
        boss_warder_stilgiss_rework* ai = FindStilgissAI(handler);
        return ai && Finish(handler, ai->TestFire(artifact), what);
    }

    bool HandleEye(ChatHandler* handler)
    {
        return FireArtifact(handler, Artifact::Eye, "Eye of Kajal now (SV2)");
    }

    bool HandleBindings(ChatHandler* handler)
    {
        return FireArtifact(handler, Artifact::Bindings, "Black Steel Bindings now (SV3; needs two players)");
    }

    bool HandleMagma(ChatHandler* handler)
    {
        return FireArtifact(handler, Artifact::Magma, "Magma Forged Band now (SV4)");
    }

    bool HandleWand(ChatHandler* handler)
    {
        return FireArtifact(handler, Artifact::Wand, "Wand of Eternal Light now (SV5)");
    }

    bool HandleBlood(ChatHandler* handler)
    {
        return FireArtifact(handler, Artifact::BlackBlood, "Black Blood now (SV6)");
    }

    bool HandleNova(ChatHandler* handler)
    {
        boss_warder_stilgiss_rework* ai = FindStilgissAI(handler);
        return ai && Finish(handler, ai->TestNova(), "Frost Nova now (SV7)");
    }

    bool HandleFrostbolt(ChatHandler* handler)
    {
        boss_warder_stilgiss_rework* ai = FindStilgissAI(handler);
        return ai && Finish(handler, ai->TestFrostbolt(), "Frostbolt now (SV8)");
    }

    bool HandleCurse(ChatHandler* handler)
    {
        npc_verek_rework* ai = FindVerekAI(handler);
        return ai && Finish(handler, ai->TestCurse(), "Verek's Curse of Blood now (SV9)");
    }

    bool HandleEnrage(ChatHandler* handler)
    {
        npc_verek_rework* ai = FindVerekAI(handler);
        return ai && Finish(handler, ai->TestEnrage(), "Verek's Enrage now (SV10)");
    }

    ChatCommandTable const& BossWarderStilgissTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,         SEC_GAMEMASTER, Console::No },
            { "verek",      HandleInfoVerek,    SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,        SEC_GAMEMASTER, Console::No },
            { "draw",       HandleDraw,         SEC_GAMEMASTER, Console::No },
            { "coffer",     HandleCoffer,       SEC_GAMEMASTER, Console::No },
            { "eye",        HandleEye,          SEC_GAMEMASTER, Console::No },
            { "bindings",   HandleBindings,     SEC_GAMEMASTER, Console::No },
            { "magma",      HandleMagma,        SEC_GAMEMASTER, Console::No },
            { "wand",       HandleWand,         SEC_GAMEMASTER, Console::No },
            { "blood",      HandleBlood,        SEC_GAMEMASTER, Console::No },
            { "nova",       HandleNova,         SEC_GAMEMASTER, Console::No },
            { "frostbolt",  HandleFrostbolt,    SEC_GAMEMASTER, Console::No },
            { "curse",      HandleCurse,        SEC_GAMEMASTER, Console::No },
            { "enrage",     HandleEnrage,       SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_warder_stilgiss_rework()
{
    RegisterDungeonReworkCreatureAI(boss_warder_stilgiss_rework, BlackrockDepthsRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_verek_rework, BlackrockDepthsRework::kInstanceScriptName);
    BrdTest::RegisterBoss("stilgiss", BossWarderStilgissTestCommands());
}
