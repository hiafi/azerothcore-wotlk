/*
 * mod-dungeon-bosses, Blackrock Spire B10: Pyroguard Emberseer (9816), "The Furnace, with Bind Him Again's escalation"
 * (SP 2523-2790, EM1-EM10, rulings 50-54; handoff section 3.4 rows EM, 3.5 row B10, 3.6, 3.8, section 10 "Rolling
 * front rulings (2026-11-15)"). Replaces the stock boss_pyroguard_emberseer and npc_blackhand_incarcerator (Fire Nova,
 * Flame Buffet, Pyroblast, the 3 s growth trigger, the Incarcerators' flee); bound by apps/dbc-tools
 * source/npcs/blackrock_spire/emberseer.py. Pure rules: EmberseerLogic.h.
 *
 * The cage protocol is the stock script's (boss_pyroguard_emberseer.cpp at 3da6e3019, the AzerothCore team and its
 * contributors), re-implemented here: the instance's altar event 4884 calls this AI's SetData(1, 1); the Incarcerators
 * channel Encage Emberseer onto him while he waits, turn on the group when the altar is used, and are respawned 5 s
 * after a wipe; his Out door is the instance's door data (open once he is DONE: SP implementation note 4).
 *
 *   EM1  The Cage      the altar: the 7 Incarcerators engage (the In door and the hall doors close); he grows a stack
 *                      every 5 s in the cage, capped at 8, and breaks free when the last one dies, keeping his stacks
 *                      (line 2; line 3 and the engage 2 s later). No living Incarcerator in combat for 3 s: a wipe
 *   EM2  The nova      every 15 s (heroic 12 s), the first erupting 8 s after the engage: a 7 yd + 0.3 yd a stack
 *                      circle on the spot he stood when the pulse began, 2.5 s warning, 30% + Weakened, the tank too
 *   EM3  The rings     with the nova: 1 / 2 / 3 rings (heroic 2 / 3 / 4) by stacks, rolling cone fronts (300 / 315
 *                      degrees, 4 yd band, 8 yd/s to 45 yd); ruling 1: ring 1's random slice shown 5 s ahead from the
 *                      nova's edge; ruling 2: rings 2-4 from the apex, 2 s (heroic 1.5 s) apart, each slice turned 45
 *                      (heroic 60) degrees clockwise and shown as the ring before it launches; the bot tank leads him
 *                      into each slice (FrontSafe); 30% + Weakened
 *   EM4  Growth        a stack every 6 s (heroic 4 s) to 20: +5% size (stock 16049), +3% (heroic +4%) damage, +0.3 yd
 *                      on the nova, Furnace Heat every 3 s (0.5% + 0.1% a stack); line 0 at 7, line 1 at 14
 *   EM5  Full Strength at 20 stacks (line 6): Supernova every 6 s, 50% to everyone; ends below 20
 *   EM6  Binding Posts every second pulse from the first: 2 posts (4 at 6+) smolder at its nova warning (line 4),
 *                      flare once its last ring has passed 21 yd: a 3 yd Soak for 8 s (anyone but his current target;
 *                      heroic: not Seared); each held post fires: -2 stacks (1 at 6+) and the beam onto him for 2 s.
 *                      The next pulse waits until its first ring cannot reach 15 yd before the posts fire
 *   EM7  Searing Bond  heroic: 4% a second on a flared post; the firing leaves the holders Seared for 40 s
 *   EM8  Unstable      heroic: 2 other posts (3 at 6+) erupt as the binding posts fire: 6 yd, 8 s warning from the
 *                      flare, 30% + Weakened (line 7)
 *   EM9  Pyroblast     at 12 s, then every 20 s: the 6 s cast at a random non-tank (interruptible: the descriptor's
 *                      list, priority 2 / 3); landed 40% / 50% plus a burn, and +1 / +2 stacks (line 5)
 *   EM10 Reset         evade or wipe: stacks, posts, fronts, debuffs and helpers go; the Incarcerators respawn and
 *                      re-cage him 5 s later; the In door and the hall doors open (the Out door stays door data)
 *
 * Every hit he deals is raised by his stacks (DamageMult): the nova, the rings, Supernova and Pyroblast; Furnace Heat
 * has its own stack rule; the posts' fire (Searing Bond, the eruptions) is fixed. Every timer runs on the AI's own
 * clock (the fronts on the kit's FrontDirector), never on BossAI's paused scheduler. Every firing logs one INFO line
 * "brs emberseer <mechanic> ..." (module.dungeonbosses); `.dbtest brs emberseer ...` fires one mechanic on demand.
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
#include "DungeonKitFronts.h"
#include "EmberseerLogic.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <array>
#include <functional>
#include <list>
#include <optional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;
using namespace BrsEmberseer;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "emberseer";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // Where bots may plan to stand: his hall (handoff section 3.8), the dais included.
    BossMechanics::SpotBounds HallBounds()
    {
        BossMechanics::SpotBounds bounds;
        bounds.Rect(kHallMinX, kHallMinY, kHallMaxX, kHallMaxY, kHallMinZ, kHallMaxZ);
        return bounds;
    }

    std::string Where(Position const& p)
    {
        return Acore::StringFormat("({:.1f}, {:.1f}, {:.1f})", p.GetPositionX(), p.GetPositionY(), p.GetPositionZ());
    }

    // The cage's In door and the hall doors (stock: closed while the Incarcerators fight, open again on a reset or
    // his death). They open only once the Dragonspire room is done (the instance's rune check owns them before that).
    void SetCageDoors(InstanceScript* instance, bool open)
    {
        if (!instance)
            return;
        if (open && instance->GetBossState(BOSS_DRAGONSPIRE_ROOM) != DONE)
            return;
        for (uint32 entry : { uint32(GO_EMBERSEER_IN), uint32(GO_EMBERSEER_DOORS) })
            if (GameObject* door = instance->GetGameObject(entry))
                door->SetGoState(open ? GO_STATE_ACTIVE : GO_STATE_READY);
    }
}

// Pyroguard Emberseer 9816
struct boss_pyroguard_emberseer_rework : public BossAI
{
    enum class Phase : uint8
    {
        Idle,       // caged, waiting for the altar
        Cage,       // the Incarcerators fight; he grows in the cage (EM1)
        Freeing,    // the last one died: the 2 s break-free scene
        Fight,      // engaged
    };

    explicit boss_pyroguard_emberseer_rework(Creature* creature)
        : BossAI(creature, BOSS_EMBERSEER), _arena(EmberseerArena(), LeashOptions(kBossLogName)) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();
        Cleanup();
        CageLook();
        SetCageDoors(instance, true);
        // Stock: 5 s after a reset (and the spawn) the dead Incarcerators respawn and every one channels onto him.
        Later(kRecageMs, [this]() { Recage(); });
    }

    // EM1: the altar (the instance's event 4884) starts the cage.
    void SetData(uint32 type, uint32 data) override
    {
        if (type == DATA_ALTAR && data == DATA_ALTAR_USED)
            StartCage();
    }

    // An Incarcerator died (npc_blackhand_incarcerator_rework::JustDied).
    void DoAction(int32 action) override
    {
        if (action == ACTION_INCARCERATOR_DIED && _phase == Phase::Cage && LivingIncarcerators() == 0)
            BreakFree();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded
        StartFight();
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("stacks={} pulses={} posts={} pyroblasts={}/{} supernovas={} killer={}", _stacks,
            _pulseIndex, _postsHeld, _pyroLanded, _pyroCast, _supernovas, killer ? killer->GetName() : "none"));
        Cleanup();
        // Stock: the seven runes of his hall go to ready and the cage doors open; the Out door is door data (DONE).
        for (uint32 entry : kEmberseerRunes)
            if (GameObject* rune = instance ? instance->GetGameObject(entry) : nullptr)
                rune->SetGoState(GO_STATE_READY);
        SetCageDoors(instance, true);
    }

    // The posts and the look stalkers are props: never zoned into combat (BossAI::JustSummoned would).
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    // EM9: a Pyroblast that lands feeds him (spell_brs_emberseer_stacked_hit's hit: R-2 m-3, not the completed cast,
    // so one into an immunity or onto a target that died in flight feeds nothing; the hit and the burn are the
    // spell's own).
    void PyroblastLanded()
    {
        if (_phase != Phase::Fight)
            return;
        ++_pyroLanded;
        uint32 const before = _stacks;
        SetStacks(_stacks + kPyroblastFeeds(_heroic), "pyroblast");
        Talk(TEXT_DRAWS_FLAMES);
        Log("pyroblast-landed", Acore::StringFormat("stacks={}->{}", before, _stacks));
    }

    // EM9 kicked (no hold of his to end: the pulse is not a cast).
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (spell && spell->Id == SPELL_EM_PYROBLAST)
            Log("pyroblast-stopped", Acore::StringFormat("stacks={}", _stacks));
    }

    void UpdateAI(uint32 diff) override
    {
        // The AI's own clock: the cage runs out of combat, the fronts and the posts during casts.
        _clockMs += diff;
        UpdateLater();
        _fronts.Update(me, diff);
        if (_phase == Phase::Cage)
            UpdateCage(diff);
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his hall, or nobody on it for 10 s: evading

        UpdateFight();
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EM1 The Cage
    // ----------------------------------------------------------------------------------------------------------------

    // Caged and out of reach until he breaks free (the template's NOT_SELECTABLE and IMMUNE_TO_PC, the stock state).
    void CageLook()
    {
        me->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->SetImmuneToPC(true);
        if (!me->HasAura(SPELL_ENCAGED_EMBERSEER))
            me->AddAura(SPELL_ENCAGED_EMBERSEER, me);
    }

    std::vector<Creature*> Incarcerators()
    {
        std::list<Creature*> found;
        me->GetCreatureListWithEntryInGrid(found, NPC_BLACKHAND_INCARCERATOR, kIncarceratorFindYd);
        return { found.begin(), found.end() };
    }

    uint32 LivingIncarcerators()
    {
        uint32 n = 0;
        for (Creature* c : Incarcerators())
            if (c->IsAlive())
                ++n;
        return n;
    }

    // 5 s after a reset: the dead Incarcerators respawn and every one goes back to its channel.
    void Recage()
    {
        if (_phase != Phase::Idle || !me->IsAlive() || me->IsEngaged())
            return;
        if (instance && instance->GetBossState(BOSS_EMBERSEER) == DONE)
            return;
        uint32 const respawned = RespawnIncarcerators();
        CageLook();
        if (respawned)
            Log("recage", Acore::StringFormat("respawned={}", respawned));
    }

    // The dead Incarcerators respawn and every one goes back to its channel; returns how many respawned.
    uint32 RespawnIncarcerators()
    {
        uint32 respawned = 0;
        for (Creature* c : Incarcerators())
        {
            if (!c->IsAlive())
            {
                c->Respawn();
                ++respawned;
            }
            if (c->IsAIEnabled && c->AI())
                c->AI()->SetData(INCARCERATOR_DATA, INCARCERATOR_CHANNEL);
        }
        return respawned;
    }

    void StartCage()
    {
        if (_phase != Phase::Idle || !me->IsAlive())
            return;
        if (instance && instance->GetBossState(BOSS_EMBERSEER) == DONE)
            return;
        Cleanup();      // drops a pending Recage too: the altar within 5 s of a wipe does its work now (R-2 m-2)
        if (uint32 const respawned = RespawnIncarcerators())
            Log("recage", Acore::StringFormat("respawned={} at-altar", respawned));
        _phase = Phase::Cage;
        _heroic = IsHeroicMap(me);
        if (instance)
            instance->SetBossState(BOSS_EMBERSEER, IN_PROGRESS);
        SetCageDoors(instance, false);
        CageLook();
        me->CastSpell(me, SPELL_FREEZE_ANIM, true);
        uint32 engaged = 0;
        for (Creature* c : Incarcerators())
            if (c->IsAlive() && c->IsAIEnabled && c->AI())
            {
                c->AI()->SetData(INCARCERATOR_DATA, INCARCERATOR_ENGAGE);
                ++engaged;
            }
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_EMBERSEER;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _nextCageGrowMs = _clockMs + kCageGrowMs;
        _cageQuietMs = 0;
        _cagePollMs = 0;
        Log("cage", Acore::StringFormat("incarcerators={} heroic={}", engaged, _heroic ? 1 : 0));
        if (engaged == 0)
            BreakFree();    // nobody left to hold him (a `.dbtest` after the adds died)
    }

    void UpdateCage(uint32 diff)
    {
        while (_clockMs >= _nextCageGrowMs)
        {
            _nextCageGrowMs += kCageGrowMs;
            if (_stacks < kCageMaxStacks)
                SetStacks(_stacks + 1, "cage");
        }
        _cagePollMs += diff;
        if (_cagePollMs < kCagePollMs)
            return;
        uint32 const dt = _cagePollMs;
        _cagePollMs = 0;
        uint32 alive = 0;
        uint32 fighting = 0;
        for (Creature* c : Incarcerators())
            if (c->IsAlive())
            {
                ++alive;
                if (c->IsEngaged())
                    ++fighting;
            }
        if (alive == 0)
        {
            BreakFree();
            return;
        }
        _cageQuietMs = fighting ? 0 : _cageQuietMs + dt;
        if (_cageQuietMs >= kCageWipeMs)
            CageFailed();
    }

    // The group wiped (or left) while the Incarcerators lived: back to the start, re-caged 5 s later.
    void CageFailed()
    {
        Log("cage-failed", Acore::StringFormat("stacks={}", _stacks));
        Cleanup();
        Mechanic::EndEncounter(me);
        if (instance && instance->GetBossState(BOSS_EMBERSEER) != DONE)
            instance->SetBossState(BOSS_EMBERSEER, NOT_STARTED);
        SetCageDoors(instance, true);
        CageLook();
        Later(kRecageMs, [this]() { Recage(); });
    }

    // The last Incarcerator died: the emote now, the yell and the engage 2 s later; he keeps his stacks.
    void BreakFree()
    {
        if (_phase != Phase::Cage)
            return;
        _phase = Phase::Freeing;
        me->RemoveAurasDueToSpell(SPELL_ENCAGED_EMBERSEER);
        me->RemoveAurasDueToSpell(SPELL_FREEZE_ANIM);
        Talk(TEXT_BREAKS_FREE);
        Log("break-free", Acore::StringFormat("stacks={}", _stacks));
        Later(kBreakFreeEngageMs, [this]()
        {
            if (_phase != Phase::Freeing)
                return;
            Talk(TEXT_THANK_YOU);
            me->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
            me->SetImmuneToPC(false);
            DoZoneInCombat();
            if (!me->IsEngaged())
            {
                Log("break-free-alone", "nobody in the hall");
                CageFailed();
            }
        });
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The fight
    // ----------------------------------------------------------------------------------------------------------------

    void StartFight()
    {
        if (_phase == Phase::Fight)
            return;
        bool const fromCage = _phase == Phase::Freeing;
        _phase = Phase::Fight;
        _players = OnBossPull(me, kBossLogName);
        _heroic = IsHeroicMap(me);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_EMBERSEER;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        me->RemoveAurasDueToSpell(SPELL_ENCAGED_EMBERSEER);
        me->RemoveAurasDueToSpell(SPELL_FREEZE_ANIM);
        SummonPosts();
        _nextGrowMs = _clockMs + kGrowEveryMs(_heroic);
        _nextHeatMs = _clockMs + kHeatEveryMs;
        _nextPulseDueMs = _clockMs + kFirstPulseStartMs;
        _nextPyroMs = _clockMs + kPyroblastFirstMs;
        _pulseIndex = 0;
        Log("engage", Acore::StringFormat("heroic={} players={} stacks={} cage={} pulse@{}s pyroblast@{}s posts={} "
            "at={}", _heroic ? 1 : 0, _players, _stacks, fromCage ? 1 : 0, kFirstPulseStartMs / 1000,
            kPyroblastFirstMs / 1000, _postCount, Where(me->GetPosition())));
    }

    void UpdateFight()
    {
        if (_phase != Phase::Fight)
            return;
        while (_clockMs >= _nextGrowMs)
        {
            _nextGrowMs += kGrowEveryMs(_heroic);
            if (_stacks < kFullStrengthStacks)
                SetStacks(_stacks + 1, "grow");
        }
        while (_clockMs >= _nextHeatMs)
        {
            _nextHeatMs += kHeatEveryMs;
            FurnaceHeat();
        }
        UpdatePosts();
        if (_clockMs >= HeldPulseStart(_nextPulseDueMs, _fireAtMs, PulseSpec(_stacks, _heroic, 0.f)))
            StartPulse();
        if (_stacks >= kFullStrengthStacks && _clockMs >= _nextSupernovaMs)
        {
            _nextSupernovaMs = _clockMs + kSupernovaEveryMs;
            Supernova();
        }
        if (_clockMs >= _nextPyroMs && !me->HasUnitState(UNIT_STATE_CASTING))
        {
            _nextPyroMs = _clockMs + kPyroblastEveryMs;
            CastPyroblast(false);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EM4 / EM5 Growth
    // ----------------------------------------------------------------------------------------------------------------

    // His stacks to `n` (0..20): the stock growth aura (size) and the damage aura move together; lines 0 and 1 at 7 and
    // 14 on the way up; Full Strength on and off at 20.
    void SetStacks(uint32 n, char const* why)
    {
        n = ClampStacks(n);
        uint32 const before = _stacks;
        _stacks = n;
        uint32 const damageAura = _heroic ? SPELL_EM_GROWTH_DAMAGE_H : SPELL_EM_GROWTH_DAMAGE;
        for (uint32 aura : { SPELL_EMBERSEER_GROWING, damageAura })
        {
            int32 const delta = int32(n) - int32(DungeonKit::Stacks(me, aura, me->GetGUID()));
            if (delta)
                DungeonKit::AddStacks(me, aura, delta, me, kFullStrengthStacks);
        }
        if (n == before)
            return;
        if (std::optional<uint8> const line = StrengthLine(before, n))
            Talk(*line);
        if (before < kFullStrengthStacks && n >= kFullStrengthStacks)
        {
            Talk(TEXT_FULL_STRENGTH);
            me->CastSpell(me, SPELL_EM_FULL_STRENGTH, true);
            _nextSupernovaMs = _clockMs + kSupernovaEveryMs;
            Log("full-strength", Acore::StringFormat("why={} next-supernova@{}s", why, kSupernovaEveryMs / 1000));
        }
        else if (before >= kFullStrengthStacks && n < kFullStrengthStacks)
            Log("full-strength-ends", Acore::StringFormat("stacks={} why={}", n, why));
        Log("stacks", Acore::StringFormat("{}->{} why={} rings={} nova={:.1f}yd mult={:.2f}", before, n, why,
            RingsFor(n, _heroic), NovaRadius(n), DamageMult(n, _heroic)));
    }

    // Every 3 s, everyone in the fight: 0.5% + 0.1% a stack (the spell script reads his stacks).
    void FurnaceHeat()
    {
        for (Player* player : FightPlayers())
            me->CastSpell(player, SPELL_EM_FURNACE_HEAT, true);
    }

    // EM5: 50% (raised by his stacks) to everyone, unavoidable: a registry hit, no Weakened.
    void Supernova()
    {
        me->CastSpell(me, SPELL_EM_FULL_STRENGTH, true);
        GuidSet targets;
        for (Player* player : FightPlayers())
            targets.insert(player->GetGUID());
        DungeonKit::RegistryHitSpec spec;
        spec.pct = HitPct(SPELL_EM_SUPERNOVA, _stacks, _heroic);
        spec.tankPct = spec.pct;
        spec.school = SPELL_SCHOOL_FIRE;
        spec.spellId = SPELL_EM_SUPERNOVA;
        spec.weakened = false;
        spec.tag = TAG_SUPERNOVA;
        DungeonKit::RegistryHit(me, targets, spec);
        ++_supernovas;
        Log("supernova", Acore::StringFormat("stacks={} pct={:.1f} players={}", _stacks, spec.pct, targets.size()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EM2 / EM3 Furnace Pulse
    // ----------------------------------------------------------------------------------------------------------------

    // One pulse: anchored where he stands now (ruling 1: ring 1's slice is shown 5 s ahead, so the spot is fixed 5 s
    // before the eruption); the nova registers at 2.5 s; the rings as the kit's ring sequence.
    void StartPulse()
    {
        uint32 const index = _pulseIndex;
        float const first = frand(-DungeonKit::kPi, DungeonKit::kPi);
        Fronts::RingSequenceSpec const plan = PulseSpec(_stacks, _heroic, first);
        std::vector<Fronts::RingStep> const steps = Fronts::PlanRings(plan);
        Position const apex = me->GetPosition();
        bool const posts = IsPostPulse(index) && _postCount == kPostCount;

        // A look stalker on the apex for the nova's burst and each ring's launch.
        ObjectGuid stalker;
        uint32 const life = Fronts::SequenceOverMs(steps) + 2000;
        if (TempSummon* s = me->SummonCreature(NPC_BRS_STALKER, apex, TEMPSUMMON_TIMED_DESPAWN, life))
            stalker = s->GetGUID();

        float const nova = plan.startYd;
        DungeonKit::RingSequence rs;
        rs.plan = plan;
        rs.safeSlot = true;                         // the bot tank leads him into each slice
        rs.safeUntilYd = nova + kSafeExtraYd;
        rs.within = HallBounds();
        rs.cueMs = kNovaCueMs;
        rs.onCue = [this, nova, posts, stalker](Position const& at)
        {
            Nova(at, nova, stalker);
            if (posts)
                Smolder();
        };
        rs.decorate = [this](MechanicRef& ref, uint32 /*index*/)
        {
            float const pct = HitPct(SPELL_EM_RING, _stacks, _heroic);
            ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_FIRE).Spell(SPELL_EM_RING).Weakened().Tag(TAG_RING);
        };
        rs.onLaunch = [this, stalker](uint32 ring, Position const& at)
        {
            if (Creature* s = me->GetMap()->GetCreature(stalker))
                s->CastSpell(s, SPELL_EM_RING_LAUNCH, true);
            Log("ring", Acore::StringFormat("ring={} slice={:.0f}deg at={}", ring + 1,
                at.GetOrientation() * 180.f / DungeonKit::kPi, Where(at)));
        };
        rs.dungeon = kLogDungeon;
        rs.boss = kBossLogName;
        uint32 const id = _fronts.StartRings(me, apex, rs);
        ++_pulseIndex;
        _nextPulseDueMs = _clockMs + kPulseEveryMs(_heroic);
        if (!id)
        {
            if (Creature* s = me->GetMap()->GetCreature(stalker))
                s->DespawnOrUnsummon();
            Log("pulse-refused", Acore::StringFormat("index={} stacks={}", index, _stacks));
            return;
        }
        if (posts)
        {
            _flareAtMs = _clockMs + PostFlareMs(steps, plan);
            _fireAtMs = _clockMs + PostFireMs(steps, plan);
        }
        Log("pulse", Acore::StringFormat("index={} stacks={} rings={} nova={:.1f}yd slice={:.0f}deg apex={} posts={} "
            "flare@{} fire@{}", index, _stacks, plan.rings, nova, first * 180.f / DungeonKit::kPi, Where(apex),
            posts ? 1 : 0, posts ? PostFlareMs(steps, plan) : 0, posts ? PostFireMs(steps, plan) : 0));
    }

    // EM2: his body flares, the circle on the pulse's spot erupts 2.5 s later (as ring 1 launches).
    void Nova(Position const& at, float radius, ObjectGuid stalker)
    {
        me->CastSpell(me, SPELL_EM_BODY_FLARE, true);
        float const pct = HitPct(SPELL_EM_NOVA, _stacks, _heroic);
        MechanicRef ref = Mechanic::Circle(me, at, radius, Ms(kNovaWarnMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_FIRE).Spell(SPELL_EM_NOVA).Weakened().Within(HallBounds())
            .Tag(TAG_NOVA);
        ref.OnResolve(OnBoss([stalker](boss_pyroguard_emberseer_rework& ai, BossMechanics::ResolveResult const& r)
        {
            if (Creature* s = ai.me->GetMap()->GetCreature(stalker))
                s->CastSpell(s, SPELL_EM_FIRE_NOVA_BURST, true);
            ai.Log("nova-lands", Acore::StringFormat("hits={}", r.hits.size()));
        }));
        Log("nova", Acore::StringFormat("r={:.1f} pct={:.1f} at={}", radius, pct, Where(at)));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EM6 / EM7 / EM8 Binding Posts
    // ----------------------------------------------------------------------------------------------------------------

    struct Post
    {
        ObjectGuid unit;
        Position at;
    };

    void SummonPosts()
    {
        _postCount = 0;
        for (std::size_t i = 0; i < kPostCount; ++i)
        {
            Vec2 const p = kEmberseerPosts[i];
            float z = me->GetMapHeight(p.x, p.y, kPostZ + 2.f);
            if (z < INVALID_HEIGHT + 1.f || std::fabs(z - kPostZ) > 3.f)
                z = kPostZ;
            Position const at(p.x, p.y, z, 0.f);
            _posts[i].at = at;
            _posts[i].unit.Clear();
            if (TempSummon* post = me->SummonCreature(NPC_BRS_BINDING_POST, at, TEMPSUMMON_MANUAL_DESPAWN))
            {
                _posts[i].unit = post->GetGUID();
                ++_postCount;
            }
        }
        if (_postCount != kPostCount)
            Log("posts-missing", Acore::StringFormat("summoned={} of {}", _postCount, kPostCount));
    }

    Creature* PostUnit(std::size_t i)
    {
        return i < kPostCount ? me->GetMap()->GetCreature(_posts[i].unit) : nullptr;
    }

    // At a post pulse's nova warning: the picks smolder (line 4); the unstable ones (heroic) are picked now too, shown
    // at the flare.
    void Smolder()
    {
        if (_postCount != kPostCount)
            return;
        auto rand = [](uint32 n) { return urand(0, n - 1); };
        _pick = PickPosts(kBindingPosts.At(_players), _heroic ? kUnstablePosts.At(_players) : 0u, rand);
        std::string which;
        for (uint8 i : _pick.bind)
        {
            if (Creature* post = PostUnit(i))
                post->CastSpell(post, SPELL_EM_SMOLDER, true);
            which += (which.empty() ? "" : ",") + std::to_string(i + 1);
        }
        Talk(TEXT_POSTS_SMOLDER);
        Log("smolder", Acore::StringFormat("posts={} unstable={}", which, _pick.unstable.size()));
    }

    // The eligible holders: anyone in the fight but his current target (lesson 3: the second tank stays eligible).
    BossMechanics::Eligibility PostEligibility()
    {
        BossMechanics::Eligibility who;
        who.playersOnly = true;
        Unit* victim = me->GetVictim();
        for (Player* player : FightPlayers())
            if (player != victim)
                who.carriers.insert(player->GetGUID());
        if (who.carriers.empty())
            who.carriers.insert(me->GetGUID());     // R-2 n-2: nobody but his target (empty would mean everyone)
        if (_heroic)
        {
            who.auraSpell = SPELL_EM_SEARED;    // EM7: a Seared player cannot fire a post
            who.maxStacks = 0;
        }
        return who;
    }

    void UpdatePosts()
    {
        if (_flareAtMs && _clockMs >= *_flareAtMs)
        {
            _flareAtMs.reset();
            Flare();
        }
        if (_searingUntilMs && _clockMs >= _nextSearingMs)
        {
            _nextSearingMs += kSearingTickMs;
            SearingTick();
            if (_clockMs >= *_searingUntilMs)
                _searingUntilMs.reset();
        }
        if (_fireAtMs && _clockMs >= *_fireAtMs + 1000)
            _fireAtMs.reset();      // the Soaks resolved at fire time; the next pulse stops waiting on it
    }

    // The window: a column on each binding post, a 3 yd Soak for 8 s; heroic: the erupting posts' circles (line 7) and
    // Searing Bond's ticks.
    void Flare()
    {
        if (_pick.bind.empty())
            return;
        BossMechanics::Eligibility const who = PostEligibility();
        _flareHeld = 0;
        _flareSoaks.clear();
        uint32 const gen = _generation;
        for (uint8 i : _pick.bind)
        {
            if (Creature* post = PostUnit(i))
            {
                post->RemoveAurasDueToSpell(SPELL_EM_SMOLDER);
                post->CastSpell(post, SPELL_EM_FLARE_COLUMN, true);
                ObjectGuid const guid = post->GetGUID();
                Later(kPostColumnRecastMs, [this, guid, gen]()
                {
                    if (gen != _generation)
                        return;
                    if (Creature* p = me->GetMap()->GetCreature(guid))
                        p->CastSpell(p, SPELL_EM_FLARE_COLUMN, true);
                });
            }
            MechanicRef ref = Mechanic::Soak(me, _posts[i].at, kPostSoakYd, 1, Ms(kPostWindowMs));
            ref.Eligible(who).OneClaimPerBot().MissedSoak(BossMechanics::MissedSoakMode::Never).Within(HallBounds())
                .Tag(TAG_POST);
            GuidSet const carriers = who.carriers;
            ref.OnResolve(OnBoss([i, carriers](boss_pyroguard_emberseer_rework& ai,
                BossMechanics::ResolveResult const& r)
            {
                ai.PostFired(i, r, carriers);
            }));
            _flareSoaks.push_back(ref.Handle());
        }
        for (uint8 i : _pick.unstable)
        {
            float const pct = kUnstablePct(_heroic);
            MechanicRef ref = Mechanic::Circle(me, _posts[i].at, kUnstableYd, Ms(kPostWindowMs));
            ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_FIRE).Spell(SPELL_EM_UNSTABLE_POST).Weakened()
                .Within(HallBounds()).Tag(TAG_UNSTABLE);
            ref.OnResolve(OnBoss([i](boss_pyroguard_emberseer_rework& ai, BossMechanics::ResolveResult const& r)
            {
                if (Creature* post = ai.PostUnit(i))
                    post->CastSpell(post, SPELL_EM_FIRE_NOVA_BURST, true);
                ai.Log("unstable-erupts", Acore::StringFormat("post={} hits={}", i + 1, r.hits.size()));
            }));
            _flareSoaks.push_back(ref.Handle());
        }
        if (!_pick.unstable.empty())
            Talk(TEXT_UNSTABLE_POSTS);
        if (_heroic)
        {
            _nextSearingMs = _clockMs + kSearingTickMs;
            _searingUntilMs = _clockMs + kPostWindowMs;
        }
        Log("flare", Acore::StringFormat("posts={} unstable={} eligible={} heroic={}", _pick.bind.size(),
            _pick.unstable.size(), who.carriers.size(), _heroic ? 1 : 0));
    }

    // EM7: once a second through the window, everyone standing on a flared post burns.
    void SearingTick()
    {
        uint32 burned = 0;
        for (std::size_t k = 0; k < _pick.bind.size() && k < _flareSoaks.size(); ++k)
        {
            MechanicHandle const h = _flareSoaks[k];
            for (Player* player : FightPlayers())
                if (Mechanic::Contains(me, h, player))
                {
                    me->CastSpell(player, SPELL_EM_SEARING_BOND, true);
                    me->CastSpell(player, SPELL_EM_SEARING_STATE, true);
                    ++burned;
                }
        }
        if (burned)
            Log("searing-bond", Acore::StringFormat("burned={}", burned));
    }

    // A binding post's window ended: held (an eligible player inside) it fires: stacks off, the beam, heroic Seared.
    void PostFired(uint8 i, BossMechanics::ResolveResult const& r, GuidSet const& carriers)
    {
        bool const held = r.count >= 1;
        if (!held)
        {
            Log("post-missed", Acore::StringFormat("post={} inside={}", i + 1, r.hits.size()));
            return;
        }
        ++_flareHeld;
        ++_postsHeld;
        uint32 const before = _stacks;
        uint32 const loss = PostLoss(1, _players);
        SetStacks(_stacks > loss ? _stacks - loss : 0, "post");
        if (Creature* post = PostUnit(i))
            post->CastSpell(me, SPELL_EM_ENCAGE_BEAM, true);
        uint32 seared = 0;
        if (_heroic)
            for (ObjectGuid const& guid : r.hits)
            {
                if (!carriers.empty() && !carriers.count(guid))
                    continue;
                Player* player = ObjectAccessor::GetPlayer(*me, guid);
                if (!player || !player->IsAlive() || player->HasAura(SPELL_EM_SEARED))
                    continue;
                me->CastSpell(player, SPELL_EM_SEARED, true);
                ++seared;
            }
        Log("post-fires", Acore::StringFormat("post={} holders={} stacks={}->{} seared={}", i + 1, r.count, before,
            _stacks, seared));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EM9 Pyroblast
    // ----------------------------------------------------------------------------------------------------------------

    // `test`: a solo tester may be the target. True: the cast started.
    bool CastPyroblast(bool test)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.tankIfAlone = test;
        Player* target = DungeonKit::PickPlayer(me, rule);
        if (!target)
        {
            Log("pyroblast-skipped", "no non-tank");
            return false;
        }
        me->CastSpell(target, SPELL_EM_PYROBLAST, false);
        Mechanic::NoteNextCastIn(me, SPELL_EM_PYROBLAST, Ms(kPyroblastEveryMs));
        ++_pyroCast;
        Log("pyroblast", Acore::StringFormat("target={} stacks={} pct={:.1f}{}", target->GetName(), _stacks,
            HitPct(SPELL_EM_PYROBLAST, _stacks, _heroic), test ? " test" : ""));
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data: kill the Incarcerators first, kick Pyroblast (normal a reward, heroic expected)
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        BossMechanics::Descriptor d;
        d.interrupts.emplace_back(NPC_EMBERSEER, SPELL_EM_PYROBLAST, kPyroblastKickPriority(_heroic),
            Ms(kPyroblastEveryMs));
        d.targets.emplace_back(NPC_BLACKHAND_INCARCERATOR, 1);
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brs emberseer` entry points
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Cage,
        Free,
        Pulse,
        Posts,
        Grow,
        Shrink,
        Pyroblast,
        FullStrength,
        Heat,
    };

    // An empty string when fired; otherwise why not.
    std::string TestFire(TestMechanic mechanic)
    {
        bool const fight = _phase == Phase::Fight && me->IsEngaged();
        switch (mechanic)
        {
            case TestMechanic::Cage:
                if (_phase != Phase::Idle)
                    return "The cage is already running (or he is free).";
                StartCage();
                return {};
            case TestMechanic::Free:
            {
                if (_phase != Phase::Cage)
                    return "Use the altar (or `.dbtest brs emberseer cage`) first.";
                uint32 killed = 0;
                for (Creature* c : Incarcerators())
                    if (c->IsAlive())
                    {
                        Unit::Kill(me, c);
                        ++killed;
                    }
                if (_phase == Phase::Cage)
                    BreakFree();
                Log("test-free", Acore::StringFormat("killed={}", killed));
                return {};
            }
            case TestMechanic::Grow:
                SetStacks(_stacks + 1, "test");
                return {};
            case TestMechanic::Shrink:
                SetStacks(_stacks > 2 ? _stacks - 2 : 0, "test");
                return {};
            default:
                break;
        }
        if (!fight)
            return "Emberseer must be free and in combat (the pulse, the posts and the rest run only in the fight).";
        switch (mechanic)
        {
            case TestMechanic::Pulse:
                _nextPulseDueMs = _clockMs;
                _fireAtMs.reset();
                StartPulse();
                break;
            case TestMechanic::Posts:
                if (_postCount != kPostCount)
                    return "The posts are missing (see the `posts-missing` log line).";
                Smolder();
                Flare();
                _fireAtMs = _clockMs + kPostWindowMs;
                break;
            case TestMechanic::Pyroblast:
                if (!CastPyroblast(true))
                    return "No player to aim Pyroblast at.";
                break;
            case TestMechanic::FullStrength:
                SetStacks(kFullStrengthStacks, "test");
                break;
            case TestMechanic::Heat:
                FurnaceHeat();
                break;
            default:
                break;
        }
        return {};
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        static char const* const phases[] = { "idle", "cage", "freeing", "fight" };
        return Acore::StringFormat("phase={} clock={}s players={} heroic={} stacks={} rings={} nova={:.1f}yd "
            "mult={:.2f} pulses={} next-pulse@{}s flare@{} fire@{} posts={}/{} held={} pyroblasts={}/{} supernovas={} "
            "fronts={}", phases[static_cast<uint8>(_phase)], _clockMs / 1000, _players, _heroic ? 1 : 0, _stacks,
            RingsFor(_stacks, _heroic), NovaRadius(_stacks), DamageMult(_stacks, _heroic), _pulseIndex,
            _nextPulseDueMs / 1000, _flareAtMs ? std::to_string(*_flareAtMs / 1000) + "s" : std::string("-"),
            _fireAtMs ? std::to_string(*_fireAtMs / 1000) + "s" : std::string("-"), _postCount, kPostCount,
            _postsHeld, _pyroLanded, _pyroCast, _supernovas, _fronts.Active() ? 1 : 0);
    }

    void Log(char const* mechanic, std::string const& detail = {}) const
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, mechanic, detail);
    }

private:
    struct Pending
    {
        uint64 dueMs = 0;
        std::function<void()> fn;
    };

    // A resolve callback that finds his AI again (never a captured `this`: the registry may outlive it), for this
    // pull only.
    template <class Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnBoss(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        uint32 const gen = _generation;
        return [map, guid, gen, fn](BossMechanics::ResolveResult const& result)
        {
            if (result.fizzled || !map)
                return;
            Creature* boss = map->GetCreature(guid);
            if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
                return;
            auto* ai = dynamic_cast<boss_pyroguard_emberseer_rework*>(boss->AI());
            if (ai && ai->_generation == gen)
                fn(*ai, result);
        };
    }

    // The players the fight counts: on his threat list, alive, in the world, not game masters.
    std::vector<Player*> FightPlayers()
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        rule.maxRange = 300.f;
        return DungeonKit::PickPlayers(me, rule, 40);
    }

    // `fn` after `delayMs` on the AI's own clock (in or out of combat); a Cleanup drops what is pending.
    void Later(uint32 delayMs, std::function<void()> fn)
    {
        _later.push_back({ _clockMs + delayMs, std::move(fn) });
    }

    void UpdateLater()
    {
        if (_later.empty())
            return;
        std::vector<Pending> due;
        for (auto it = _later.begin(); it != _later.end();)
        {
            if (_clockMs >= it->dueMs)
            {
                due.push_back(std::move(*it));
                it = _later.erase(it);
            }
            else
                ++it;
        }
        for (Pending& p : due)
            p.fn();
    }

    // The pull's state: no stacks, fronts, posts, stalkers, debuffs or pending callback (Reset, evade, death, a cage
    // that failed, a new cage). Wipe rule 4: his debuffs leave the players, his helpers despawn.
    void Cleanup()
    {
        ++_generation;          // callbacks of an older pull stop
        _fronts.Clear(me);
        for (MechanicHandle const& h : _flareSoaks)
            Mechanic::Cancel(me, h);
        _flareSoaks.clear();
        summons.DespawnAll();
        _later.clear();
        if (me->HasUnitState(UNIT_STATE_CASTING))
            me->InterruptNonMeleeSpells(false);
        for (uint32 aura : { SPELL_EMBERSEER_GROWING, uint32(SPELL_EM_GROWTH_DAMAGE), uint32(SPELL_EM_GROWTH_DAMAGE_H),
                 SPELL_FREEZE_ANIM })
            me->RemoveAurasDueToSpell(aura);
        if (Map* map = me->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* p = ref.GetSource())
                    for (uint32 aura : { SPELL_EM_SEARED, SPELL_EM_SEARING_STATE, SPELL_EM_PYROBLAST })
                        p->RemoveAurasDueToSpell(aura, me->GetGUID());
        _phase = Phase::Idle;
        _stacks = 0;
        _players = 0;
        _pulseIndex = 0;
        _postCount = 0;
        _postsHeld = 0;
        _flareHeld = 0;
        _pyroCast = 0;
        _pyroLanded = 0;
        _supernovas = 0;
        _pick = {};
        _flareAtMs.reset();
        _fireAtMs.reset();
        _searingUntilMs.reset();
        _nextSearingMs = 0;
        _nextCageGrowMs = 0;
        _cageQuietMs = 0;
        _cagePollMs = 0;
        _nextGrowMs = 0;
        _nextHeatMs = 0;
        _nextPulseDueMs = 0;
        _nextPyroMs = 0;
        _nextSupernovaMs = 0;
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::FrontDirector _fronts;
    std::array<Post, kPostCount> _posts{};
    std::vector<MechanicHandle> _flareSoaks;    // the binding posts' Soaks (in _pick.bind order), then the eruptions
    PostPick _pick;
    std::vector<Pending> _later;
    std::optional<uint64> _flareAtMs;
    std::optional<uint64> _fireAtMs;            // the posts fire then: the next pulse waits on it (EM6)
    std::optional<uint64> _searingUntilMs;
    uint64 _clockMs = 0;                        // ms on the AI's own clock: every timer of the fight
    uint64 _nextSearingMs = 0;
    uint64 _nextCageGrowMs = 0;
    uint64 _nextGrowMs = 0;
    uint64 _nextHeatMs = 0;
    uint64 _nextPulseDueMs = 0;
    uint64 _nextPyroMs = 0;
    uint64 _nextSupernovaMs = 0;
    uint32 _cageQuietMs = 0;
    uint32 _cagePollMs = 0;
    uint32 _generation = 0;
    uint32 _stacks = 0;
    uint32 _pulseIndex = 0;
    uint32 _postCount = 0;                      // posts summoned this pull (7: the posts run)
    uint32 _postsHeld = 0;
    uint32 _flareHeld = 0;
    uint32 _pyroCast = 0;
    uint32 _pyroLanded = 0;
    uint32 _supernovas = 0;
    uint8 _players = 0;                         // the flex count held at the pull (5..10)
    bool _heroic = false;
    Phase _phase = Phase::Idle;
};

// Blackhand Incarcerator 10316 (rebound from the stock npc_blackhand_incarcerator): the cage prelude without the flee.
// Out of the fight it channels Encage Emberseer onto him from its post, immune to everyone; the altar (his SetData)
// turns it on the group; Strike every 14-23 s; its death tells him (the last one frees him).
struct npc_blackhand_incarcerator_rework : public ScriptedAI
{
    explicit npc_blackhand_incarcerator_rework(Creature* creature)
        : ScriptedAI(creature), _instance(creature->GetInstanceScript()) { }

    void Reset() override
    {
        _strikeMs = 0;
        // While his cage runs (the boss state IN_PROGRESS) an Incarcerator that evaded stays attackable.
        bool const cage = _instance && _instance->GetBossState(BOSS_EMBERSEER) == IN_PROGRESS;
        me->SetImmuneToAll(!cage);
        _channelInMs = cage ? 0 : 1000;
    }

    void SetData(uint32 type, uint32 value) override
    {
        if (type != INCARCERATOR_DATA)
            return;
        if (value == INCARCERATOR_ENGAGE)
        {
            _channelInMs = 0;
            me->SetImmuneToAll(false);
            me->InterruptSpell(CURRENT_CHANNELED_SPELL);
            DoZoneInCombat();
        }
        else if (value == INCARCERATOR_CHANNEL && !me->IsEngaged())
        {
            // Back on its post after a failed cage: out of reach again until the altar is used.
            me->SetImmuneToAll(true);
            _channelInMs = 1000;
        }
    }

    void JustEngagedWith(Unit* /*who*/) override
    {
        // Stock: CallForHelp ignores units without line of sight, so the others are zoned in by hand.
        std::list<Creature*> others;
        me->GetCreatureListWithEntryInGrid(others, NPC_BLACKHAND_INCARCERATOR, 60.f);
        for (Creature* c : others)
            if (c != me && c->IsAlive() && !c->IsEngaged())
                c->SetInCombatWithZone();
        _strikeMs = urand(8000, 16000);
    }

    void JustDied(Unit* /*killer*/) override
    {
        if (Creature* emberseer = _instance ? _instance->GetCreature(BOSS_EMBERSEER) : nullptr)
            if (emberseer->IsAIEnabled && emberseer->AI())
                emberseer->AI()->DoAction(ACTION_INCARCERATOR_DIED);
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
        {
            if (_channelInMs && (_channelInMs <= diff || (_channelInMs -= diff) == 0))
            {
                _channelInMs = 0;
                Channel();
            }
            return;
        }
        if (_strikeMs <= diff)
        {
            DoCastVictim(SPELL_INCARCERATOR_STRIKE, true);
            _strikeMs = urand(14000, 23000);
        }
        else
            _strikeMs -= diff;
        DoMeleeAttackIfReady();
    }

private:
    // Stock: from its home spot, Encage Emberseer onto him while he is caged.
    void Channel()
    {
        if (me->GetPositionX() != me->GetHomePosition().GetPositionX() || me->HasAura(SPELL_ENCAGE_CHANNEL)
            || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        Creature* emberseer = _instance ? _instance->GetCreature(BOSS_EMBERSEER) : nullptr;
        if (emberseer && emberseer->IsAlive() && emberseer->HasAura(SPELL_ENCAGED_EMBERSEER))
            DoCast(emberseer, SPELL_ENCAGE_CHANNEL);
    }

    InstanceScript* _instance;
    uint32 _strikeMs = 0;
    uint32 _channelInMs = 0;
};

// Binding Post (300730): an invisible prop at an Incarcerator's spot that carries the smolder, the column, the beam
// and the eruption.
struct npc_brs_binding_post : public NullCreatureAI
{
    explicit npc_brs_binding_post(Creature* creature) : NullCreatureAI(creature) { }
};

// Furnace Heat (EM4) and Pyroblast's hit (EM9): a percent of the reference row (the tank row on the tank) read from
// his stacks at launch (EmberseerLogic.h HitPct). Pyroblast's burn is the kit's spell_dungeon_refflat_periodic.
class spell_brs_emberseer_stacked_hit : public SpellScript
{
    PrepareSpellScript(spell_brs_emberseer_stacked_hit);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;
        uint32 const stacks = DungeonKit::Stacks(caster, SPELL_EMBERSEER_GROWING, caster->GetGUID());
        float const pct = HitPct(GetSpellInfo()->Id, stacks, IsHeroicMap(caster));
        SetEffectValue(static_cast<int32>(DungeonKit::RefFlatOn(caster, GetHitUnit(), pct)));
    }

    // EM9: a Pyroblast that lands feeds him (a hit only: an immune target or one that died in flight is no hit).
    void Feed(SpellEffIndex /*effIndex*/)
    {
        if (GetSpellInfo()->Id != SPELL_EM_PYROBLAST)
            return;
        Creature* boss = GetCaster() ? GetCaster()->ToCreature() : nullptr;
        if (boss && boss->IsAIEnabled)
            if (auto* ai = dynamic_cast<boss_pyroguard_emberseer_rework*>(boss->AI()))
                ai->PyroblastLanded();
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_brs_emberseer_stacked_hit::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
        OnEffectHitTarget += SpellEffectFn(spell_brs_emberseer_stacked_hit::Feed, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

namespace
{
    boss_pyroguard_emberseer_rework* FindEmberseerAI(ChatHandler* handler)
    {
        Creature* boss = BrsTest::FindBoss(handler, NPC_EMBERSEER);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_pyroguard_emberseer_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Emberseer is not running boss_pyroguard_emberseer_rework (check the "
                "ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_pyroguard_emberseer_rework::TestMechanic mechanic, char const* what)
    {
        boss_pyroguard_emberseer_rework* ai = FindEmberseerAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestFire(mechanic);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Pyroguard Emberseer: {} fired ({}).", what,
            ai->HeroicMap() ? "heroic numbers" : "normal numbers");
        return true;
    }

    using TM = boss_pyroguard_emberseer_rework::TestMechanic;

    bool HandleInfo(ChatHandler* handler)
    {
        return BrsTest::ShowBossInfo(handler, NPC_EMBERSEER, BOSS_EMBERSEER);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_pyroguard_emberseer_rework* ai = FindEmberseerAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Pyroguard Emberseer: {}", ai->TestState());
        return true;
    }

    bool HandleCage(ChatHandler* handler)
    {
        return Fire(handler, TM::Cage, "the cage (EM1, as the altar)");
    }

    bool HandleFree(ChatHandler* handler)
    {
        return Fire(handler, TM::Free, "the break free (EM1: the Incarcerators die)");
    }

    bool HandlePulse(ChatHandler* handler)
    {
        return Fire(handler, TM::Pulse, "a Furnace Pulse (EM2 nova + EM3 rings, 5 s ahead)");
    }

    bool HandlePosts(ChatHandler* handler)
    {
        return Fire(handler, TM::Posts, "the binding posts (EM6, heroic EM7 / EM8: smolder and flare now)");
    }

    bool HandleGrow(ChatHandler* handler)
    {
        return Fire(handler, TM::Grow, "a stack (EM4)");
    }

    bool HandleShrink(ChatHandler* handler)
    {
        return Fire(handler, TM::Shrink, "two stacks off (a held post, EM6)");
    }

    bool HandlePyroblast(ChatHandler* handler)
    {
        return Fire(handler, TM::Pyroblast, "Pyroblast (EM9; `.gm off` to be picked)");
    }

    bool HandleFullStrength(ChatHandler* handler)
    {
        return Fire(handler, TM::FullStrength, "Full Strength (EM5: 20 stacks, Supernova every 6 s)");
    }

    bool HandleHeat(ChatHandler* handler)
    {
        return Fire(handler, TM::Heat, "Furnace Heat (EM4)");
    }

    // `.dbtest brs emberseer <sub>`: the numbers are the map's difficulty.
    ChatCommandTable const& EmberseerTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",         HandleInfo,         SEC_GAMEMASTER, Console::No },
            { "state",        HandleState,        SEC_GAMEMASTER, Console::No },
            { "cage",         HandleCage,         SEC_GAMEMASTER, Console::No },
            { "free",         HandleFree,         SEC_GAMEMASTER, Console::No },
            { "pulse",        HandlePulse,        SEC_GAMEMASTER, Console::No },
            { "posts",        HandlePosts,        SEC_GAMEMASTER, Console::No },
            { "grow",         HandleGrow,         SEC_GAMEMASTER, Console::No },
            { "shrink",       HandleShrink,       SEC_GAMEMASTER, Console::No },
            { "pyroblast",    HandlePyroblast,    SEC_GAMEMASTER, Console::No },
            { "fullstrength", HandleFullStrength, SEC_GAMEMASTER, Console::No },
            { "heat",         HandleHeat,         SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_pyroguard_emberseer_rework()
{
    // The boss and the Incarcerators bind only once wave 2 does (an unbound registered name logs "not assigned" at
    // boot); the post and the spell script are declared now, so they register now.
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_pyroguard_emberseer_rework, BlackrockSpireRework::kInstanceScriptName);
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_blackhand_incarcerator_rework, BlackrockSpireRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brs_binding_post, BlackrockSpireRework::kInstanceScriptName);
    RegisterSpellScript(spell_brs_emberseer_stacked_hit);
    BrsTest::RegisterBoss("emberseer", EmberseerTestCommands());
}
