/*
 * mod-dungeon-bosses, Blackrock Depths D21: The Seven (Anger'rel 9035, Seeth'rel 9038, Dope'rel 9040, Gloom'rel 9037,
 * Vile'rel 9036, Hate'rel 9034, Doom'rel 9039), "seven bitter ghosts sharing one doom, taking turns to haunt you in
 * their own foul moods". Build spec S4 "The Seven" (docs/dungeons/blackrock-depths-4-imperial-seat.md, TS1-TS10;
 * rulings 72-74, 88, 90, 91), handoff sections 3.4 (rows D21), 3.5, 3.6, 3.9 (the `loner` row), 3.11 #4 (the shared
 * pool), section 7 #18. ONE AI on all seven entries (boss_the_seven_rework), bound by apps/dbc-tools
 * source/npcs/blackrock_depths/the_seven.py; it replaces the stock boss_gloomrel / boss_doomrel (their gossip handlers
 * are here) and the SmartAI of 9034, 9035, 9036, 9038, 9040 (dropped by rev_the_seven_blackrock_depths.sql). Pure rules
 * (the rotation, Gather Doom, the kits, the picks): TheSevenLogic.h; the pool's home in the instance: TheSevenFight.h.
 *
 *   Start      Doom'rel's gossip (menu 1947 option 0, then 1950 "Continue..."): his stock line, TYPE_TOMB_OF_SEVEN
 *              IN_PROGRESS (the instance shuts both doors), and all seven rise at once: hostile, in combat, on one
 *              shared health pool (DungeonKit::SharedHealthPool, held by the instance). Gloom'rel's gossip (Smelt Dark
 *              Iron 1952, the Spectral Chalice 1953) stays as stock
 *   TS1        the rotation (section 7 #18): Anger'rel corporeal alone for 0-20 s, then every 20 s the next ghost rises
 *              and the one corporeal longest fades, so two are corporeal at a time, each for 40 s, and Doom'rel rises
 *              at 120 s. A shade (Incorporeal: -90% damage taken) goes back to its post, passive, its threat wiped, but
 *              stays selectable and in combat. A rising ghost yells, leaves its post and fights with its kit. The
 *              bots' kill order skips shades (TargetEntry LacksAura + an Attacks hold)
 *   TS2        Gather Doom: a corporeal ghost casts it 3 s after it rises, then every 8 s (heroic 2 s casts every 6 s);
 *              three landed casts fill its energy and it casts its mood (a 3 s Physical bar nobody can kick). At most
 *              one mood per turn; a fade waits for a mood bar (and Vile'rel's channel, and Anger'rel's charges) in
 *              progress. A kick or a silence stops that cast's energy
 *   TS3-TS9    the moods: Furious Charge (a 10 yd Stack round Anger'rel, three charges at the farthest player beyond
 *              10 yd), Seething Cold (an anchorless Stack, Cluster(2), loners ticked), Dopey Haze (HoldStill, a
 *              stumble a second of movement), Gloom (healing -50%, Gloom'rel +50% damage), Vile Communion (a kickable
 *              6 s channel healing the pool), Hatred (a Spread a second for 8 s), Doom (1 / 2 RunOuts, 10 yd)
 *   TS10       the kept kits (TheSevenLogic.h kKit), Frost Nova (2 s root) and Gouge (2 s, anyone) copies
 *   End        the pool at 0 kills all seven in one tick (the kit's death tick, the emptier as the killer): seven
 *              deaths finish the Tomb in the instance (doors open, the Chest of The Seven). Any ghost evading, or no
 *              ghost in combat for 15 s (the stock reset), wipes all seven: back to their posts, friendly, the pool
 *              full, the Tomb NOT_STARTED (the entrance opens), Doom'rel's gossip back
 *
 * Doom'rel conducts: the rotation clock, the registry encounter (bossStateId BOSS_THE_SEVEN) and the descriptor live on
 * him (he never dies before the others), and every ghost registers its moods with him as the owner. Every timer runs on
 * the AI's own clock; every firing logs one INFO line "brd seven <mechanic> ..." (module.dungeonbosses). Lambdas the
 * registry keeps capture the map and guids only.
 */

#include "ArenaGuard.h"
#include "BlackrockDepthsKit.h"
#include "BlackrockDepthsRework.h"
#include "BlackrockDepthsTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Containers.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitPool.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MechanicWeakened.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "ScriptedGossip.h"
#include "Spell.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TheSevenFight.h"
#include "TheSevenLogic.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <functional>
#include <map>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdTheSeven;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBoss = "seven";
    float constexpr kRoomYd = 150.f;                    // the tomb is about 95 x 120 yd: every ghost reaches the room
    uint32 constexpr kPointPost = 1;                    // a fading ghost's walk back to its post
    uint32 constexpr kArmorCheckMs = 2000;
    uint32 constexpr kKitRetryMs = 1000;
    uint32 constexpr kMoodTickMs = 1000;                // Seething Cold, Dopey Haze, Hatred: a beat a second
    uint32 constexpr kChaliceRespawnSecs = 5 * 60;      // stock boss_gloomrel: the Spectral Chalice for 5 minutes

    // Gossip (stock boss_tomb_of_seven.cpp): Gloom'rel's two "Continue..." menus, Doom'rel's challenge.
    uint32 constexpr kGossipGloomrelSmelt = 1952;
    uint32 constexpr kGossipGloomrelChalice = 1953;
    uint32 constexpr kGossipDoomrelContinue = 1950;

    // Everything the fight leaves on a player, removed at every end (rule 6).
    std::array<uint32, 13> constexpr kPlayerAuras{ { SPELL_TS_SEETHING_COLD, SPELL_TS_DOPEY_HAZE, SPELL_TS_GLOOM,
        SPELL_TS_HATRED_MARK, SPELL_TS_DOOM, SPELL_TS_DOOM_RING, SPELL_TS_FROSTBOLT, SPELL_TS_CONE_OF_COLD,
        SPELL_TS_FROST_NOVA, SPELL_TS_RUPTURE, SPELL_TS_GOUGE, SPELL_TS_IMMOLATE, SPELL_STOCK_SUNDER_ARMOR } };

    // ... and on a ghost.
    std::array<uint32, 3> constexpr kGhostAuras{ { SPELL_TS_INCORPOREAL, SPELL_TS_GATHERED_DOOM,
        SPELL_TS_RECKLESSNESS } };

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(ms);
    }

    void LogTs(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    Body BodyOf(WorldObject const* o)
    {
        return { o->GetGUID().GetRawValue(), o->GetPositionX(), o->GetPositionY(), o->GetPositionZ() };
    }

    // The floor under a point: the map's height within 6 yd of `refZ`, else `refZ`.
    float GroundZ(WorldObject const* probe, float x, float y, float refZ)
    {
        float const h = probe->GetMapHeight(x, y, refZ + 2.f);
        if (h <= INVALID_HEIGHT || std::fabs(h - refZ) > 6.f)
            return refZ;
        return h;
    }

    char const* PhaseName(uint8 phase)
    {
        switch (phase)
        {
            case 1:  return "shade";
            case 2:  return "corporeal";
            default: return "idle";
        }
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// One AI on all seven ghosts. Each runs its own kit, Gather Doom and mood; Doom'rel also conducts (kConductor).
// ---------------------------------------------------------------------------------------------------------------------
struct boss_the_seven_rework : public ScriptedAI
{
private:
    enum class Phase : uint8
    {
        Idle,           // before the challenge, after a wipe: friendly at its post
        Shade,          // in the fight, incorporeal at its post
        Corporeal,      // in the fight, fighting with its kit
    };

    // The ghost's mood in progress (TS3-TS9): the bar, then its effect on the AI's clock.
    struct MoodState
    {
        bool casting = false;               // the 3 s bar
        bool effect = false;                // the effect runs
        uint64 endMs = 0;                   // ... until here (ticks and charges done by then)
        std::vector<MechanicHandle> handles;
        // TS3 Furious Charge
        uint32 chargesLeft = 0;
        uint64 nextChargeMs = 0;
        uint32 chargesPending = 0;          // lines shown, the charge not run yet
        // TS4 / TS5 / TS8 a beat a second
        uint32 ticksLeft = 0;
        uint64 nextTickMs = 0;
        std::map<ObjectGuid, Body> samples; // TS5: where each player stood at the last beat
        // TS7 Vile Communion
        bool vilePending = false;           // the channel cast, not started yet
        bool vileChannel = false;
        uint64 vileStartMs = 0;
        uint32 vileTicks = 0;
        bool vileLook = false;
    };

public:
    explicit boss_the_seven_rework(Creature* creature)
        : ScriptedAI(creature), _ghost(GhostOf(creature->GetEntry()).value_or(GHOST_ANGERREL)),
          _arena(TheSevenArena(), LeashOptions(kBoss)) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Engine hooks
    // ----------------------------------------------------------------------------------------------------------------

    // Spawn, and the end of every evade: friendly and untouchable at its post (stock), Doom'rel's challenge open again
    // unless the Tomb is done.
    void Reset() override
    {
        ClearGhost();
        _inWipe = false;
        if (!me->IsAlive())
            return;
        me->SetFaction(kFactionFriend);
        me->SetImmuneToPC(true);
        me->SetReactState(REACT_AGGRESSIVE);
        if (IsConductor())
            me->ReplaceAllNpcFlags(TombState() == DONE ? UNIT_NPC_FLAG_NONE : UNIT_NPC_FLAG_GOSSIP);
    }

    // A shade never attacks: only a corporeal ghost picks a victim.
    void AttackStart(Unit* who) override
    {
        if (_phase != Phase::Corporeal)
            return;
        ScriptedAI::AttackStart(who);
    }

    // Any ghost evading ends the attempt for all seven (KT-D2: "one ghost evades -> all reset" is D21's rule).
    void EnterEvadeMode(EvadeReason why) override
    {
        if (_inWipe || _phase == Phase::Idle)
        {
            ScriptedAI::EnterEvadeMode(why);
            return;
        }
        LogTs("evade", Acore::StringFormat("ghost={} reason={}", Key(), uint32(why)));
        WipeAll(why);
    }

    void JustDied(Unit* killer) override
    {
        bool const fought = _phase != Phase::Idle;
        ClearGhost();
        if (IsConductor() && fought)
            EncounterEnded(true);
        LogTs("death", Acore::StringFormat("ghost={} killer={}", Key(),
            killer ? killer->GetName() : std::string("none")));
    }

    // The shared pool (KT-D2): every hit on a ghost comes off the pool (a cleave once per cast), every heal goes in.
    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask /*mask*/) override
    {
        if (DungeonKit::SharedHealthPool* pool = Pool())
            pool->DamageTaken(me, attacker, damage, type);
    }

    void HealReceived(Unit* healer, uint32& heal) override
    {
        if (DungeonKit::SharedHealthPool* pool = Pool())
            pool->HealReceived(me, healer, heal);
    }

    // Gloom'rel's two options (stock boss_gloomrel) and Doom'rel's challenge (stock boss_doomrel).
    void sGossipSelect(Player* player, uint32 menuId, uint32 gossipListId) override
    {
        if (!player || gossipListId != 0)
            return;
        switch (menuId)
        {
            case kGossipGloomrelSmelt:
                CloseGossipMenuFor(player);
                player->CastSpell(player, SPELL_STOCK_LEARN_SMELT, false);
                break;
            case kGossipGloomrelChalice:
                CloseGossipMenuFor(player);
                if (InstanceScript* instance = me->GetInstanceScript())
                    instance->DoRespawnGameObject(instance->GetGuidData(DATA_GO_CHALICE), kChaliceRespawnSecs);
                break;
            case kGossipDoomrelContinue:
                CloseGossipMenuFor(player);
                if (IsConductor())
                    StartChallenge(player);
                break;
            default:
                break;
        }
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type == POINT_MOTION_TYPE && id == kPointPost && _phase == Phase::Shade)
            me->SetFacingTo(me->GetHomePosition().GetOrientation());
    }

    // A cast that went off: Gather Doom landed (energy), a mood bar ended (the mood), Vile Communion's channel began.
    void OnSpellCast(SpellInfo const* spell) override
    {
        if (!spell)
            return;
        uint32 const id = spell->Id;
        if (id == SPELL_TS_GATHER_DOOM || id == SPELL_TS_GATHER_DOOM_HEROIC)
            GatherLands();
        else if (id == kMoodCast[_ghost] && _mood.casting)
        {
            _mood.casting = false;
            BeginMoodEffect();
        }
        else if (id == SPELL_TS_VILE_COMMUNION)
        {
            _mood.vilePending = false;
            _mood.vileChannel = true;
            _mood.vileStartMs = _clockMs;
            _mood.vileTicks = 0;
            _mood.vileLook = false;
            LogTs("vile-communion-channel", Acore::StringFormat("heroic={} pct={:.1f}", _heroic ? 1 : 0,
                kVileHealPct(_heroic)));
        }
    }

    // An interrupted cast ends what it started (rule 13): Gather Doom gives no energy, Vile Communion heals no more.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (!spell)
            return;
        uint32 const id = spell->Id;
        if (id == SPELL_TS_GATHER_DOOM || id == SPELL_TS_GATHER_DOOM_HEROIC)
        {
            bool const was = _turn.Gathering();
            _turn.GatherInterrupted();
            if (was && _phase == Phase::Corporeal)
                LogTs("gather-doom-interrupted", Acore::StringFormat("ghost={} energy={}", Key(), _turn.Energy()));
        }
        else if (id == kMoodCast[_ghost] && _mood.casting)
        {
            _mood.casting = false;
            CancelMoodHandles();
            LogTs("mood-broken", Acore::StringFormat("ghost={} mood={}", Key(), kMoodKeys[_ghost]));
        }
        else if (id == SPELL_TS_VILE_COMMUNION && (_mood.vileChannel || _mood.vilePending))
        {
            _mood.vileChannel = false;
            _mood.vilePending = false;
            LogTs("vile-communion-interrupted", Acore::StringFormat("ticks={} of {}", _mood.vileTicks, kVileTicks));
        }
    }

    void OnChannelFinished(SpellInfo const* spell) override
    {
        if (!spell || spell->Id != SPELL_TS_VILE_COMMUNION || !_mood.vileChannel)
            return;
        while (_mood.vileTicks < kVileTicks)
            VileTick();
        _mood.vileChannel = false;
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        if (DungeonKit::SharedHealthPool* pool = Pool())
            pool->Update(me);           // the mirror; once the pool is empty, the death tick kills all seven
        if (!me->IsAlive())
            return;
        if (IsConductor())
            Conduct(diff);
        if (_phase == Phase::Idle)
        {
            MaintainArmor(diff);
            return;
        }

        RunMood();                      // a mood unleashed runs its course, even after a fade
        if (_phase == Phase::Shade)
        {
            UpdateVictim();             // passive: keeps no victim, evades once out of combat
            return;
        }

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;                     // off the tomb, or nobody on it for 10 s: evading
        if (_fadePending && !MoodHoldsFade())
        {
            BecomeShade(false);
            return;
        }
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (StartMood() || StartGather())
            return;
        RunKit();
        if (!me->HasUnitState(UNIT_STATE_CASTING))
            DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The challenge, the rotation, the wipe (Doom'rel conducts)
    // ----------------------------------------------------------------------------------------------------------------

    // Doom'rel's "Continue...": his stock line, the Tomb IN_PROGRESS (doors shut), all seven rise.
    void StartChallenge(Player* challenger)
    {
        if (!IsConductor() || _fighting || !me->IsAlive())
            return;
        uint32 const state = TombState();
        if (state == DONE || state == IN_PROGRESS)
            return;
        // Right after a wipe the others still walk home (evading): they could not join; ask again in a moment.
        for (uint8 g = 0; g < kGhostCount; ++g)
            if (Creature* ghost = GhostUnit(g))
                if (ghost->IsAlive() && ghost->IsInEvadeMode())
                {
                    LogTs("challenge-refused", Acore::StringFormat("{} is still going home", kGhostKeys[g]));
                    return;
                }
        me->RemoveNpcFlag(UNIT_NPC_FLAG_GOSSIP);
        Talk(SAY_DOOMREL_CHALLENGE);
        if (InstanceScript* instance = me->GetInstanceScript())
            instance->SetData(TYPE_TOMB_OF_SEVEN, IN_PROGRESS);
        StartFight(challenger);
    }

    // All seven join at once: hostile, in combat, on the pool; Anger'rel rises alone (step 0).
    void StartFight(Player* challenger)
    {
        if (!_heroicForced)
            _heroic = IsHeroicMap(me);
        _heroicForced = false;
        _fighting = true;
        _fightStartMs = _clockMs;
        _oocMs = 0;

        std::array<Creature*, kGhostCount> ghosts{};
        for (uint8 g = 0; g < kGhostCount; ++g)
            ghosts[g] = GhostUnit(g);

        DungeonKit::SharedHealthPool* pool = Pool();
        if (pool)
            pool->ClearMembers();
        else
            LogTs("pool-missing", "the instance holds no shared pool (TheSevenFight.h PoolHost): seven health bars");
        for (Creature* ghost : ghosts)
        {
            if (!ghost)
                continue;
            ghost->SetFaction(kFactionDarkIronDwarves);
            ghost->SetImmuneToPC(false);
            if (pool)
                pool->Add(ghost);
        }
        for (Creature* ghost : ghosts)
            if (boss_the_seven_rework* ai = AIOf(ghost))
                ai->Join(_heroic);
        if (pool)
            pool->Engage(me);

        OnBossPull(me, kBoss);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_THE_SEVEN;
        Mechanic::BeginEncounter(me, options);
        _registered = true;
        for (Creature* ghost : ghosts)
            if (ghost && ghost != me)
                Mechanic::TrackUnit(me, ghost);
        Describe();

        _rotation.Start();
        RunRotation();
        LogTs("engage", Acore::StringFormat("heroic={} challenger={} ghosts={} pool={}", _heroic ? 1 : 0,
            challenger ? challenger->GetName() : std::string("none"),
            std::count_if(ghosts.begin(), ghosts.end(), [](Creature* c) { return c != nullptr; }),
            pool ? pool->Max() : 0));
    }

    // Boss data (S4 "Boss data"): the kill order by rank, corporeal only (a shade is skipped and never attacked); the
    // interrupt list Vile Communion first, then Gather Doom by the same rank; the kits' own casts never kicked (the
    // bots keep their kicks for the list); Frost Nova's root a dispel reward.
    void Describe()
    {
        using BossMechanics::Condition;
        using BossMechanics::Who;
        BossMechanics::Descriptor d;
        for (uint8 g = 0; g < kGhostCount; ++g)
        {
            Ghost const ghost = static_cast<Ghost>(g);
            uint32 const entry = EntryOf(ghost);
            d.targets.emplace_back(entry, KillPriority(ghost), Who::Dps, Condition::LacksAura(SPELL_TS_INCORPOREAL));
            d.targets.emplace_back(entry, KillPriority(ghost), Who::Tank, Condition::LacksAura(SPELL_TS_INCORPOREAL));
            d.interrupts.emplace_back(entry, SPELL_TS_GATHER_DOOM, GatherKickPriority(ghost),
                Ms(kGatherEveryMs.normal));
            d.interrupts.emplace_back(entry, SPELL_TS_GATHER_DOOM_HEROIC, GatherKickPriority(ghost),
                Ms(kGatherEveryMs.heroic));
        }
        d.interrupts.emplace_back(NPC_VILEREL, SPELL_TS_VILE_COMMUNION, kVileCommunionKick);
        d.interrupts.emplace_back(NPC_SEETHREL, SPELL_TS_FROSTBOLT, 0);
        d.interrupts.emplace_back(NPC_VILEREL, SPELL_TS_MIND_BLAST, 0);
        d.interrupts.emplace_back(NPC_HATEREL, SPELL_TS_SHADOW_BOLT, 0);
        d.interrupts.emplace_back(NPC_DOOMREL, SPELL_TS_SHADOW_BOLT_VOLLEY, 0);
        d.interrupts.emplace_back(NPC_DOOMREL, SPELL_TS_IMMOLATE, 0);
        d.dispels.emplace_back(SPELL_TS_FROST_NOVA, kDispelFrostNova);
        d.holds.push_back(BossMechanics::HoldEntry::Attacks(0, SPELL_TS_INCORPOREAL));
        Mechanic::Describe(me, std::move(d));
    }

    // The steps due now (fades before rises).
    void RunRotation()
    {
        uint64 const elapsed = _clockMs - _fightStartMs;
        while (std::optional<RotationStep> step = _rotation.Due(elapsed))
        {
            std::string detail = Acore::StringFormat("step={} t={}s", _rotation.Next() - 1, elapsed / 1000);
            if (step->fade)
            {
                if (boss_the_seven_rework* ai = GhostAI(*step->fade))
                    ai->Fade();
                detail += Acore::StringFormat(" fade={}", kGhostKeys[*step->fade]);
            }
            if (step->rise)
            {
                if (boss_the_seven_rework* ai = GhostAI(*step->rise))
                    ai->Rise();
                detail += Acore::StringFormat(" rise={}", kGhostKeys[*step->rise]);
            }
            LogTs("rotation", detail);
        }
    }

    // The conductor's beat: the rotation, and the stock 15 s reset (no ghost in combat for 15 s ends the attempt).
    void Conduct(uint32 diff)
    {
        if (!_fighting)
            return;
        RunRotation();
        bool anyInCombat = false;
        for (uint8 g = 0; g < kGhostCount && !anyInCombat; ++g)
            if (Creature* ghost = GhostUnit(g))
                anyInCombat = ghost->IsAlive() && ghost->IsInCombat();
        if (anyInCombat)
        {
            _oocMs = 0;
            return;
        }
        _oocMs += diff;
        if (_oocMs < kTombResetMs)
            return;
        LogTs("reset", "no ghost in combat for 15 s");
        WipeAll(EVADE_REASON_NO_HOSTILES);
    }

    // The attempt ends for all seven: each ghost cleans up and evades home (Reset makes it friendly), the pool fills,
    // the players lose the fight's auras, the Tomb goes back to NOT_STARTED (the instance opens the entrance).
    void WipeAll(EvadeReason why)
    {
        _inWipe = true;
        LogTs("wipe", Acore::StringFormat("by={} reason={}", Key(), uint32(why)));
        for (uint8 g = 0; g < kGhostCount; ++g)
            if (g != _ghost)
                if (boss_the_seven_rework* ai = GhostAI(g))
                    ai->WipeOne();
        EncounterEnded(false);
        ClearGhost();
        ScriptedAI::EnterEvadeMode(why);
    }

    void WipeOne()
    {
        if (_inWipe)
            return;
        _inWipe = true;
        ClearGhost();
        ScriptedAI::EnterEvadeMode(EVADE_REASON_OTHER);
    }

    // The encounter-wide end: the pool (a wipe fills it; a kill leaves it dead), the players' auras, the Tomb, the
    // conductor's clock and registry encounter.
    void EncounterEnded(bool killed)
    {
        if (!killed)
            if (DungeonKit::SharedHealthPool* pool = Pool())
                pool->Reset();
        if (InstanceScript* instance = me->GetInstanceScript())
        {
            for (uint32 spell : kPlayerAuras)
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
            if (!killed && instance->GetData(TYPE_TOMB_OF_SEVEN) == IN_PROGRESS)
                instance->SetData(TYPE_TOMB_OF_SEVEN, NOT_STARTED);
        }
        if (boss_the_seven_rework* conductor = GhostAI(kConductor))
            conductor->StopConducting();
    }

    void StopConducting()
    {
        _fighting = false;
        _rotation.Stop();
        _oocMs = 0;
        if (_registered)
        {
            Mechanic::EndEncounter(me);
            _registered = false;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TS1 joining, rising, fading
    // ----------------------------------------------------------------------------------------------------------------

    // The challenge: every ghost starts as a shade at its post, in combat with the room; step 0 raises Anger'rel.
    void Join(bool heroic)
    {
        _heroic = heroic;
        _inWipe = false;
        _mood = MoodState{};
        _turn = GhostTurn{};
        _phase = Phase::Shade;
        BecomeShade(true);
        DoZoneInCombat(me, kRoomYd);
    }

    // The rising ghost yells, leaves its post and fights: a fresh turn (energy 0, Gather Doom in 3 s), its kit.
    void Rise()
    {
        if (!me->IsAlive() || _phase == Phase::Idle)
            return;
        _phase = Phase::Corporeal;
        _fadePending = false;
        me->RemoveAurasDueToSpell(SPELL_TS_INCORPOREAL);
        me->RemoveAurasDueToSpell(SPELL_TS_GATHERED_DOOM);
        me->SetReactState(REACT_AGGRESSIVE);
        _turn.Rise(_clockMs, _heroic);
        StartKit();
        if (uint32 const armor = ArmorOf(_ghost))
            if (!me->HasAura(armor))
                me->CastSpell(me, armor, true);
        Talk(RiseText(_ghost));
        _arena.Engage(me);
        Unit* target = SelectTarget(SelectTargetMethod::MaxThreat, 0, 0.f, true);
        if (!target)
            target = me->SelectNearestPlayer(kRoomYd);
        if (target)
            AttackStart(target);
        LogTs("rise", Acore::StringFormat("ghost={} heroic={} target={}", Key(), _heroic ? 1 : 0,
            target ? target->GetName() : std::string("none")));
    }

    // The ghost corporeal longest fades; a mood bar, Vile Communion's channel or Anger'rel's charges in progress hold
    // the fade until they end.
    void Fade()
    {
        if (!me->IsAlive() || _phase != Phase::Corporeal)
            return;
        if (MoodHoldsFade())
        {
            _fadePending = true;
            LogTs("fade-held", Acore::StringFormat("ghost={} mood={}", Key(), kMoodKeys[_ghost]));
            return;
        }
        BecomeShade(false);
    }

    // A shade: Incorporeal (-90% damage taken), passive, its threat wiped, back at its post; selectable and still in
    // combat (section 7 #18).
    void BecomeShade(bool quiet)
    {
        _phase = Phase::Shade;
        _fadePending = false;
        _turn.Fade();
        if (me->HasUnitState(UNIT_STATE_CASTING))
            me->InterruptNonMeleeSpells(false);
        me->RemoveAurasDueToSpell(SPELL_TS_GATHERED_DOOM);
        me->AttackStop();
        me->SetReactState(REACT_PASSIVE);
        me->GetThreatMgr().ResetAllThreat();
        me->CastSpell(me, SPELL_TS_INCORPOREAL, true);
        if (!quiet)
            me->CastSpell(me, SPELL_TS_FADE_LOOK, true);
        me->GetMotionMaster()->MovePoint(kPointPost, me->GetHomePosition());
        _arena.Reset();
        if (!quiet)
            LogTs("fade", Acore::StringFormat("ghost={}", Key()));
    }

    bool MoodHoldsFade() const
    {
        return _mood.casting || _mood.vilePending || _mood.vileChannel || _mood.chargesLeft > 0
            || _mood.chargesPending > 0;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TS2 Gather Doom
    // ----------------------------------------------------------------------------------------------------------------

    bool StartGather()
    {
        if (!_turn.GatherDue(_clockMs))
            return false;
        uint32 const spell = _heroic ? SPELL_TS_GATHER_DOOM_HEROIC : SPELL_TS_GATHER_DOOM;
        _turn.GatherStarted(_clockMs);      // before the cast: a cast that lands at once must find it started
        if (me->CastSpell(me, spell, false) != SPELL_CAST_OK)
        {
            _turn.GatherRefused(_clockMs);  // a silence or a lockout: a blocked cast, the next on the cadence
            LogTs("gather-doom-refused", Acore::StringFormat("ghost={}", Key()));
            return false;
        }
        Mechanic::NoteNextCastIn(me, spell, Ms(kGatherEveryMs(_heroic)));
        LogTs("gather-doom", Acore::StringFormat("ghost={} energy={} cast={}ms", Key(), _turn.Energy(),
            _turn.CastMs()));
        return true;
    }

    void GatherLands()
    {
        bool const full = _turn.GatherLanded();
        DungeonKit::AddStacks(me, SPELL_TS_GATHERED_DOOM, 1, me, kEnergyFull);
        LogTs("gather-doom-landed", Acore::StringFormat("ghost={} energy={}{}", Key(), _turn.Energy(),
            full ? " full" : ""));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TS3-TS9 the moods
    // ----------------------------------------------------------------------------------------------------------------

    // Full energy: the 3 s bar (Physical, not interruptible), the mood line, and the registry shapes whose warning
    // the bar is.
    bool StartMood()
    {
        if (!_turn.MoodDue())
            return false;
        _mood = MoodState{};
        _mood.casting = true;
        if (me->CastSpell(me, kMoodCast[_ghost], false) != SPELL_CAST_OK)
        {
            _mood.casting = false;
            return false;
        }
        _turn.MoodStarted();
        me->RemoveAurasDueToSpell(SPELL_TS_GATHERED_DOOM);
        Talk(MoodText(_ghost));
        RegisterMoodWarning();
        LogTs(kMoodKeys[_ghost], Acore::StringFormat("ghost={} heroic={} bar={}ms", Key(), _heroic ? 1 : 0,
            kMoodCastMs));
        return true;
    }

    // The shapes that use the bar as their warning (owner: the conductor; anchored on this ghost).
    void RegisterMoodWarning()
    {
        Creature* owner = Owner();
        switch (MoodOf(_ghost))
        {
            case Mood::FuriousCharge:
            {
                // TS3: collapse within 10 yd of Anger'rel for the 9 s of charges (the bots' job; the lines hit).
                MechanicRef ref = Mechanic::Stack(owner, me, kChargeSafeYd, Ms(kMoodCastMs));
                ref.Persistent(Ms(kChargeLifeMs), Ms(kMoodTickMs)).Tag(TAG_TS_FURIOUS_STACK);
                TrackMood(ref.Handle());
                break;
            }
            case Mood::SeethingCold:
            {
                // TS4: G2's `loner` row exactly: an anchorless Stack, Cluster(2), 6 yd, 10 s, judged every second.
                MechanicRef ref = Mechanic::Stack(owner, me, kColdRadiusYd, Ms(kMoodCastMs));
                ref.Cluster(static_cast<uint8>(kColdMinOthers)).Persistent(Ms(kColdLifeMs), Ms(kColdTickMs))
                    .Tag(TAG_TS_SEETHING_COLD);
                TrackMood(ref.Handle());
                break;
            }
            case Mood::DopeyHaze:
            {
                // TS5: nobody moves for 6 s from the bar's end.
                MechanicRef ref = Mechanic::HoldStill(owner, GuidSet(), Ms(kHazeLifeMs), Ms(kMoodCastMs));
                ref.Tolerance(kHazeToleranceYd).Tag(TAG_TS_DOPEY_HAZE);
                TrackMood(ref.Handle());
                break;
            }
            case Mood::Hatred:
                RegisterHatred(kMoodCastMs);        // TS8: the first of eight, landing as the bar ends
                break;
            default:
                break;
        }
    }

    // The bar ended: the mood itself.
    void BeginMoodEffect()
    {
        uint64 const now = _clockMs;
        _mood.effect = true;
        switch (MoodOf(_ghost))
        {
            case Mood::FuriousCharge:
                _mood.chargesLeft = kChargeCount;
                _mood.nextChargeMs = now;
                _mood.endMs = now + kChargeLifeMs;
                break;
            case Mood::SeethingCold:
                _mood.ticksLeft = kColdTicks;
                _mood.nextTickMs = now;
                _mood.endMs = now + kColdLifeMs;
                break;
            case Mood::DopeyHaze:
                me->CastSpell(me, SPELL_TS_DOPEY_HAZE, true);
                SampleAll();
                _mood.ticksLeft = kHazeTicks;
                _mood.nextTickMs = now + kHazeTickMs;
                _mood.endMs = now + kHazeLifeMs;
                break;
            case Mood::Gloom:
                me->CastSpell(me, SPELL_TS_GLOOM, true);
                me->CastSpell(me, SPELL_TS_RECKLESSNESS, true);
                _mood.endMs = now + kGloomMs;
                break;
            case Mood::VileCommunion:
                _mood.vilePending = true;
                if (me->CastSpell(me, SPELL_TS_VILE_COMMUNION, false) != SPELL_CAST_OK)
                {
                    _mood.vilePending = false;
                    LogTs("vile-communion-refused");
                }
                if (_mood.vileChannel)
                    _mood.vilePending = false;      // the channel began inside the cast call
                _mood.endMs = now + kVileChannelMs;
                break;
            case Mood::Hatred:
                me->CastSpell(me, SPELL_TS_HATRED_MARK, true);
                _mood.ticksLeft = kHatredTicks - 1;     // the first Spread was registered with the bar
                _mood.nextTickMs = now;
                _mood.endMs = now + kHatredLifeMs;
                break;
            case Mood::Doom:
                StartDoom();
                _mood.endMs = now + kDoomMarkMs;
                break;
        }
        LogTs(Acore::StringFormat("{}-unleashed", kMoodKeys[_ghost]).c_str(), Acore::StringFormat("ghost={}",
            Key()));
    }

    // Every update while a mood runs (also as a shade): its beats on the AI's clock.
    void RunMood()
    {
        uint64 const now = _clockMs;
        while (_mood.chargesLeft && now >= _mood.nextChargeMs)
        {
            --_mood.chargesLeft;
            _mood.nextChargeMs += kChargeEveryMs;
            ChargeRound();
        }
        while (_mood.ticksLeft && now >= _mood.nextTickMs)
        {
            --_mood.ticksLeft;
            _mood.nextTickMs += kMoodTickMs;
            MoodBeat();
        }
        if (_mood.vileChannel)
            VileBeat(now);
        if (_mood.effect && now >= _mood.endMs && !_mood.ticksLeft && !_mood.chargesLeft && !_mood.chargesPending
            && !_mood.vileChannel && !_mood.vilePending)
        {
            _mood.effect = false;
            LogTs(Acore::StringFormat("{}-ends", kMoodKeys[_ghost]).c_str(), Acore::StringFormat("ghost={}",
                Key()));
        }
    }

    void MoodBeat()
    {
        switch (MoodOf(_ghost))
        {
            case Mood::SeethingCold:
                ColdBeat();
                break;
            case Mood::DopeyHaze:
                HazeBeat();
                break;
            case Mood::Hatred:
                RegisterHatred(kHatredTickMs);
                break;
            default:
                break;
        }
    }

    // TS3: a charge at the farthest player beyond 10 yd (a 3 yd line from him to 2 yd past them, shown 1 s, then the
    // charge), or a harmless stomp when everyone stands close.
    void ChargeRound()
    {
        if (_phase != Phase::Corporeal)
            return;
        std::vector<Player*> const players = FightPlayers();
        std::vector<Body> bodies;
        for (Player* p : players)
            bodies.push_back(BodyOf(p));
        Body const from = BodyOf(me);
        std::optional<std::size_t> const pick = FarthestBeyond(from, bodies, kChargeSafeYd);
        if (!pick)
        {
            me->CastSpell(me, SPELL_TS_FURIOUS_STOMP, true);
            LogTs("furious-charge-stomp", "nobody beyond 10 yd");
            return;
        }
        Player* target = players[*pick];
        Body const end = ChargeEnd(from, bodies[*pick]);
        Position const fromPos = me->GetPosition();
        Position const to(end.x, end.y, GroundZ(me, end.x, end.y, end.z), 0.f);
        float const pct = kChargePct(_heroic);
        MechanicRef ref = Mechanic::Line(Owner(), fromPos, to, kChargeWidthYd, Ms(kChargeWarnMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_TS_FURIOUS_CHARGE).Weakened()
            .Tag(TAG_TS_FURIOUS_CHARGE)
            .OnResolve(OnGhost([to](boss_the_seven_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai.ChargeLands(to, r);
            }));
        if (!ref.IsValid())
        {
            LogTs("furious-charge-refused", target->GetName());
            return;
        }
        ++_mood.chargesPending;
        TrackMood(ref.Handle());
        LogTs("furious-charge", Acore::StringFormat("heroic={} on={} dist={:.1f} pct={:.0f}", _heroic ? 1 : 0,
            target->GetName(), PlaneDistance(from, bodies[*pick]), pct));
    }

    void ChargeLands(Position const& to, BossMechanics::ResolveResult const& r)
    {
        if (_mood.chargesPending)
            --_mood.chargesPending;
        if (r.fizzled || !me->IsAlive() || _phase != Phase::Corporeal)
            return;
        me->GetMotionMaster()->MoveCharge(to.GetPositionX(), to.GetPositionY(), to.GetPositionZ(), kChargeSpeed);
        me->CastSpell(to.GetPositionX(), to.GetPositionY(), to.GetPositionZ(), SPELL_TS_FURIOUS_CHARGE_LOOK, true);
        LogTs("furious-charge-lands", Acore::StringFormat("hits={}", r.hits.size()));
    }

    // TS4: every player with fewer than 2 others within 6 yd takes the tick (the registry's Cluster(2) rule).
    void ColdBeat()
    {
        std::vector<Player*> const players = FightPlayers();
        std::vector<Body> bodies;
        for (Player* p : players)
            bodies.push_back(BodyOf(p));
        std::vector<std::size_t> const loners = Loners(bodies, kColdRadiusYd, kColdMinOthers);
        for (std::size_t i : loners)
            me->CastSpell(players[i], SPELL_TS_SEETHING_COLD, true);
        LogTs("seething-cold-tick", Acore::StringFormat("loners={} of {}", loners.size(), players.size()));
    }

    // TS5: where everyone stands as the haze begins.
    void SampleAll()
    {
        _mood.samples.clear();
        for (Player* p : FightPlayers())
            _mood.samples[p->GetGUID()] = BodyOf(p);
    }

    // TS5: whoever moved since the last beat stumbles (a hit and a Weakened).
    void HazeBeat()
    {
        uint32 stumbles = 0;
        for (Player* p : FightPlayers())
        {
            Body const now = BodyOf(p);
            auto it = _mood.samples.find(p->GetGUID());
            if (it != _mood.samples.end() && Stumbled(it->second, now))
            {
                me->CastSpell(p, SPELL_TS_STUMBLE, true);
                BossMechanics::Weakened::AddStack(p);
                ++stumbles;
            }
            _mood.samples[p->GetGUID()] = now;
        }
        LogTs("dopey-haze-tick", Acore::StringFormat("stumbles={}", stumbles));
    }

    // TS8: one Spread, landing `warnMs` from now: every player within 6 yd of another takes 5% / 8% (the tank too).
    void RegisterHatred(uint32 warnMs)
    {
        float const pct = kHatredPct(_heroic);
        MechanicRef ref = Mechanic::Spread(Owner(), kHatredRadiusYd, Ms(warnMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_SHADOW).Spell(SPELL_TS_HATRED).Tag(TAG_TS_HATRED);
        TrackMood(ref.Handle());
    }

    // TS7: a sixth of the heal a second while the channel lasts; the hands again at 3 s.
    void VileBeat(uint64 now)
    {
        Spell const* channel = me->GetCurrentSpell(CURRENT_CHANNELED_SPELL);
        if (!channel || channel->GetSpellInfo()->Id != SPELL_TS_VILE_COMMUNION)
        {
            _mood.vileChannel = false;          // ended without a hook (a despawn, a death): nothing more to heal
            return;
        }
        while (_mood.vileTicks < kVileTicks && now >= _mood.vileStartMs + (_mood.vileTicks + 1) * kVileTickMs)
            VileTick();
        if (!_mood.vileLook && now >= _mood.vileStartMs + kVileLookAtMs)
        {
            _mood.vileLook = true;
            me->CastSpell(me, SPELL_TS_VILE_COMMUNION_LOOK, true);
        }
    }

    void VileTick()
    {
        ++_mood.vileTicks;
        float const pct = VileTickPct(_heroic);
        uint32 gain = 0;
        if (DungeonKit::SharedHealthPool* pool = Pool())
            gain = pool->RestorePct(me, pct);
        LogTs("vile-communion-tick", Acore::StringFormat("tick={} pct={:.2f} gain={}", _mood.vileTicks, pct, gain));
    }

    // TS9: 1 (heroic 2) random players of the fight, the tank included (ruling 88), marked for 6 s; then the RunOut
    // blasts the others within 10 yd (the registry) and the doomed themselves (the script, 211547).
    void StartDoom()
    {
        std::vector<Player*> players = FightPlayers();
        Acore::Containers::RandomShuffle(players);
        uint32 const marks = std::min<uint32>(kDoomMarks(_heroic), static_cast<uint32>(players.size()));
        GuidSet marked;
        std::string names;
        for (uint32 i = 0; i < marks; ++i)
        {
            Player* p = players[i];
            marked.insert(p->GetGUID());
            me->CastSpell(p, SPELL_TS_DOOM, true);
            me->CastSpell(p, SPELL_TS_DOOM_RING, true);
            names += (names.empty() ? "" : ",") + p->GetName();
        }
        if (marked.empty())
            return;
        float const pct = kDoomOthersPct(_heroic);
        MechanicRef ref = Mechanic::RunOut(Owner(), nullptr, kDoomRadiusYd, Ms(kDoomMarkMs));
        ref.Targets(marked).Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_SHADOW).Spell(SPELL_TS_DOOM_BLAST)
            .Weakened().Tag(TAG_TS_DOOM)
            .OnResolve(OnGhost([marked](boss_the_seven_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai.DoomLands(marked, r);
            }));
        TrackMood(ref.Handle());
        LogTs("doom-marks", Acore::StringFormat("heroic={} on={} pct={:.0f}", _heroic ? 1 : 0, names, pct));
    }

    void DoomLands(GuidSet const& marked, BossMechanics::ResolveResult const& r)
    {
        uint32 blasted = 0;
        for (ObjectGuid const& guid : marked)
            if (Player* p = ObjectAccessor::GetPlayer(*me, guid))
                if (p->IsAlive() && p->IsInWorld())
                {
                    me->CastSpell(p, SPELL_TS_DOOM_BLAST_SELF, true);
                    ++blasted;
                }
        LogTs("doom-blast", Acore::StringFormat("doomed={} others={}", blasted, r.hits.size()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TS10 the kit (TheSevenLogic.h kKit): one cast at a time, never one that would run into a Gather Doom
    // ----------------------------------------------------------------------------------------------------------------

    void StartKit()
    {
        for (std::size_t i = 0; i < kKit.size(); ++i)
            if (kKit[i].ghost == _ghost)
                _kitNext[i] = _clockMs + urand(kKit[i].firstMinMs, kKit[i].firstMaxMs);
    }

    void RunKit()
    {
        for (std::size_t i = 0; i < kKit.size(); ++i)
        {
            KitRow const& row = kKit[i];
            if (row.ghost != _ghost || _clockMs < _kitNext[i] || !_turn.KitCastFits(_clockMs, row.castMs))
                continue;
            Unit* target = KitTargetOf(row);
            if (!target || me->CastSpell(target, row.spell, false) != SPELL_CAST_OK)
            {
                _kitNext[i] = _clockMs + kKitRetryMs;
                continue;
            }
            _kitNext[i] = _clockMs + urand(row.everyMinMs, row.everyMaxMs);
            if (me->HasUnitState(UNIT_STATE_CASTING))
                return;
        }
    }

    Unit* KitTargetOf(KitRow const& row)
    {
        switch (row.target)
        {
            case KitTarget::Victim:
                return me->GetVictim();
            case KitTarget::VictimBehind:
            {
                Unit* victim = me->GetVictim();
                return victim && !victim->HasInArc(float(M_PI), me) ? victim : nullptr;
            }
            case KitTarget::Self:
                return me;
            case KitTarget::Random:
                return SelectTarget(SelectTargetMethod::Random, 0, 0.f, true);
        }
        return nullptr;
    }

    // Out of combat (stock): Seeth'rel keeps Frost Armor, Doom'rel Demon Armor.
    void MaintainArmor(uint32 diff)
    {
        _armorMs = _armorMs > diff ? _armorMs - diff : 0;
        if (_armorMs)
            return;
        _armorMs = kArmorCheckMs;
        uint32 const armor = ArmorOf(_ghost);
        if (armor && !me->IsInEvadeMode() && !me->IsInCombat() && !me->HasAura(armor))
            me->CastSpell(me, armor, true);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // State
    // ----------------------------------------------------------------------------------------------------------------

    bool IsConductor() const { return _ghost == kConductor; }

    std::string Key() const { return kGhostKeys[_ghost]; }

    uint32 TombState() const
    {
        InstanceScript* instance = me->GetInstanceScript();
        return instance ? instance->GetData(TYPE_TOMB_OF_SEVEN) : uint32(NOT_STARTED);
    }

    // The pool, from the instance every time (never a cached pointer: KT-D2).
    DungeonKit::SharedHealthPool* Pool() const
    {
        return PoolOf(me->GetInstanceScript());
    }

    // A ghost by its rotation index: the instance's guid when it holds the pool, else the nearest of that entry.
    Creature* GhostUnit(uint8 ghost) const
    {
        if (ghost == _ghost)
            return me;
        if (PoolHost* host = HostOf(me->GetInstanceScript()))
            if (ObjectGuid const guid = host->TheSevenGuid(ghost))
                if (Creature* c = ObjectAccessor::GetCreature(*me, guid))
                    return c;
        return me->FindNearestCreature(EntryOf(static_cast<Ghost>(ghost)), kRoomYd, true);
    }

    static boss_the_seven_rework* AIOf(Creature* c)
    {
        if (!c || !c->IsAlive() || !c->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_the_seven_rework*>(c->AI());
    }

    boss_the_seven_rework* GhostAI(uint8 ghost) const
    {
        return AIOf(GhostUnit(ghost));
    }

    // The registry owner of every shape of the fight: the conductor (alive until the death tick), else this ghost.
    Creature* Owner() const
    {
        Creature* conductor = GhostUnit(kConductor);
        return conductor && conductor->IsAlive() ? conductor : me;
    }

    // The players of the fight: on the tomb's floor, alive, never a game master.
    std::vector<Player*> FightPlayers() const
    {
        std::vector<Player*> out;
        Map* map = me->GetMap();
        if (!map)
            return out;
        for (auto const& ref : map->GetPlayers())
            if (Player* p = ref.GetSource())
                if (p->IsInWorld() && p->IsAlive() && !p->IsGameMaster() && _arena.Contains(p))
                    out.push_back(p);
        return out;
    }

    // Runs `fn(ai, result)` on this ghost when a mechanic resolves, if it is still there (map and guid only).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnGhost(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (!map)
                return;
            if (boss_the_seven_rework* ai = AIOf(map->GetCreature(guid)))
                fn(*ai, result);
        };
    }

    void TrackMood(MechanicHandle handle)
    {
        if (handle)
            _mood.handles.push_back(handle);
    }

    void CancelMoodHandles()
    {
        for (MechanicHandle const& handle : _mood.handles)
            Mechanic::Cancel(me, handle);
        _mood.handles.clear();
    }

    // This ghost's state back to the start (Reset, a wipe, death): every shape it registered cancelled, its fight
    // auras gone, its turn and mood cleared; the conductor's clock and registry encounter too.
    void ClearGhost()
    {
        CancelMoodHandles();
        if (me->IsAlive())
        {
            if (me->HasUnitState(UNIT_STATE_CASTING))
                me->InterruptNonMeleeSpells(false);
            for (uint32 aura : kGhostAuras)
                me->RemoveAurasDueToSpell(aura);
        }
        _mood = MoodState{};
        _turn = GhostTurn{};
        _phase = Phase::Idle;
        _fadePending = false;
        _arena.Reset();
        if (IsConductor())
            StopConducting();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brd seven` entry points
    // ----------------------------------------------------------------------------------------------------------------
public:
    std::string GhostLine() const
    {
        return Acore::StringFormat("{} {} energy={} mood={} gathering={} fade-held={}", Key(),
            PhaseName(static_cast<uint8>(_phase)), _turn.Energy(), _turn.MoodSpent() ? "spent" : "-",
            _turn.Gathering() ? 1 : 0, _fadePending ? 1 : 0);
    }

    std::vector<std::string> TestState() const
    {
        std::vector<std::string> lines;
        DungeonKit::SharedHealthPool const* pool = Pool();
        lines.push_back(Acore::StringFormat("seven heroic={} fighting={} t={}s next-step={} pool={}/{} tomb={}",
            _heroic ? 1 : 0, _fighting ? 1 : 0, _fighting ? (_clockMs - _fightStartMs) / 1000 : 0, _rotation.Next(),
            pool ? pool->Current() : 0, pool ? pool->Max() : 0, TombState()));
        for (uint8 g = 0; g < kGhostCount; ++g)
            if (boss_the_seven_rework* ai = GhostAI(g))
                lines.push_back(ai->GhostLine());
            else
                lines.push_back(Acore::StringFormat("{} missing or dead", kGhostKeys[g]));
        return lines;
    }

    // `.dbtest brd seven start`: Doom'rel's challenge, the GM as the challenger (`.gm off` to be fought).
    std::string TestStart(Player* gm)
    {
        if (_fighting)
            return "The Seven are already fighting.";
        if (TombState() != NOT_STARTED)
            return "The Tomb is not NOT_STARTED (done, or an attempt in progress).";
        StartChallenge(gm);
        return _fighting ? std::string() : std::string("The challenge did not start.");
    }

    // `.dbtest brd seven step`: the next rotation step now (the clock moves forward to it).
    std::string TestStep()
    {
        if (!_fighting)
            return "The Seven are not fighting (`.dbtest brd seven start`).";
        uint64 const due = StepTimeMs(_rotation.Next());
        uint64 const elapsed = _clockMs - _fightStartMs;
        if (due > elapsed)
            _fightStartMs -= due - elapsed;
        RunRotation();
        return {};
    }

    // `.dbtest brd seven mood <ghost>`: that ghost's energy full now (it must be corporeal).
    std::string TestMood()
    {
        if (_phase != Phase::Corporeal)
            return Key() + " is not corporeal (`.dbtest brd seven step` until it rises).";
        _turn.ForceFull();
        return {};
    }

    std::string TestWipe()
    {
        if (_phase == Phase::Idle)
            return Key() + " is not fighting.";
        WipeAll(EVADE_REASON_OTHER);
        return {};
    }

    // `.dbtest brd seven heroic <0|1>`: the heroic form on a normal map until the next pull ends.
    void TestHeroic(bool heroic)
    {
        _heroic = heroic;
        _heroicForced = true;
    }

private:
    Ghost const _ghost;
    DungeonKit::ArenaGuard _arena;
    Phase _phase = Phase::Idle;
    bool _heroic = false;
    bool _inWipe = false;                   // this ghost is evading as part of a wipe (no second wipe from it)
    bool _fadePending = false;              // the rotation faded it while a mood held it corporeal
    uint64 _clockMs = 0;                    // the AI's own clock
    GhostTurn _turn;                        // TS2
    std::array<uint64, kKit.size()> _kitNext{};
    MoodState _mood;                        // TS3-TS9
    uint32 _armorMs = 0;
    // The conductor (Doom'rel) only
    bool _fighting = false;
    bool _heroicForced = false;             // `.dbtest ... heroic`: kept through the next pull
    bool _registered = false;               // the registry encounter (bossStateId BOSS_THE_SEVEN) is ours
    uint64 _fightStartMs = 0;
    uint32 _oocMs = 0;                      // no ghost in combat for this long
    Rotation _rotation;                     // TS1
};

namespace
{
    boss_the_seven_rework* SevenAI(ChatHandler* handler, uint32 entry)
    {
        Creature* ghost = BrdTest::FindBoss(handler, entry);
        auto* ai = ghost && ghost->IsAIEnabled ? dynamic_cast<boss_the_seven_rework*>(ghost->AI()) : nullptr;
        if (!ai && ghost)
            handler->SendErrorMessage("{} does not run the reworked script.", ghost->GetName());
        return ai;
    }

    bool Report(ChatHandler* handler, std::string const& error, char const* ok)
    {
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->SendSysMessage(ok);
        return true;
    }

    // `.dbtest brd seven info`
    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowBossInfo(handler, NPC_DOOMREL, BOSS_THE_SEVEN);
    }

    // `.dbtest brd seven state`: the rotation, the pool and each ghost's phase, energy and mood.
    bool HandleState(ChatHandler* handler)
    {
        boss_the_seven_rework* ai = SevenAI(handler, NPC_DOOMREL);
        if (!ai)
            return false;
        for (std::string const& line : ai->TestState())
            handler->SendSysMessage(line);
        return true;
    }

    // `.dbtest brd seven start`: Doom'rel's challenge now.
    bool HandleStart(ChatHandler* handler)
    {
        boss_the_seven_rework* ai = SevenAI(handler, NPC_DOOMREL);
        return ai && Report(handler, ai->TestStart(handler->GetPlayer()),
            "The Seven rise: Anger'rel corporeal, the others shades; the pool is shared.");
    }

    // `.dbtest brd seven step`: the next rotation step now.
    bool HandleStep(ChatHandler* handler)
    {
        boss_the_seven_rework* ai = SevenAI(handler, NPC_DOOMREL);
        return ai && Report(handler, ai->TestStep(), "The next ghost rises (and the one corporeal longest fades).");
    }

    // `.dbtest brd seven mood <angerrel|seethrel|doperel|gloomrel|vilerel|haterel|doomrel>`: its energy full now.
    bool HandleMood(ChatHandler* handler, Optional<std::string> who)
    {
        if (!who)
        {
            handler->SendErrorMessage("Name a ghost: angerrel, seethrel, doperel, gloomrel, vilerel, haterel, "
                "doomrel.");
            return false;
        }
        for (uint8 g = 0; g < kGhostCount; ++g)
            if (*who == kGhostKeys[g])
            {
                boss_the_seven_rework* ai = SevenAI(handler, EntryOf(static_cast<Ghost>(g)));
                return ai && Report(handler, ai->TestMood(), "Its energy is full: the mood bar starts.");
            }
        handler->SendErrorMessage("No ghost named {}.", *who);
        return false;
    }

    // `.dbtest brd seven wipe`: the attempt ends for all seven.
    bool HandleWipe(ChatHandler* handler)
    {
        boss_the_seven_rework* ai = SevenAI(handler, NPC_DOOMREL);
        return ai && Report(handler, ai->TestWipe(), "Wiped: the Seven go back to their posts, friendly.");
    }

    // `.dbtest brd seven heroic [0|1]`
    bool HandleHeroic(ChatHandler* handler, Optional<uint32> on)
    {
        boss_the_seven_rework* ai = SevenAI(handler, NPC_DOOMREL);
        if (!ai)
            return false;
        ai->TestHeroic(!on || *on != 0);
        handler->SendSysMessage("The heroic form is set until the end of the next pull.");
        return true;
    }

    ChatCommandTable const& BossTheSevenTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",   HandleInfo,   SEC_GAMEMASTER, Console::No },
            { "state",  HandleState,  SEC_GAMEMASTER, Console::No },
            { "start",  HandleStart,  SEC_GAMEMASTER, Console::No },
            { "step",   HandleStep,   SEC_GAMEMASTER, Console::No },
            { "mood",   HandleMood,   SEC_GAMEMASTER, Console::No },
            { "wipe",   HandleWipe,   SEC_GAMEMASTER, Console::No },
            { "heroic", HandleHeroic, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_the_seven_rework()
{
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_the_seven_rework, BlackrockDepthsRework::kInstanceScriptName);
    BrdTest::RegisterBoss("seven", BossTheSevenTestCommands());
}
