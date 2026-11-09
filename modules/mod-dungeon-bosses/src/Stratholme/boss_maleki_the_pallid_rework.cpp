/*
 * mod-dungeon-bosses, Stratholme S12: Maleki the Pallid (10438), normal and heroic. Build spec: ST 3160-3211 (build
 * spec), ST 2915-3159 (design: "he corrupts, then he feeds", rulings 48-50), MK1-MK6; handoff section 3.4 rows MK,
 * section 3.5 row S12, section 3.6, section 3.8. Replaces SmartAI 10438 (Frostbolt 17503 kept in C++; Ice Tomb 16869
 * and Drain Life 17238 reworked below; Banshee Curse 16867 retired; the death's instance data 3 is the instance's own
 * write now): WP-S12's SQL rev drops the five rows. Bound by apps/dbc-tools
 * source/npcs/stratholme/maleki_the_pallid.py.
 *
 *   MK1 Icy Death     5 s, then every 12 s: a random non-tank without it (else the fewest stacks) gains a stack of the
 *                     frost corruption (206665, Magic, emote line 1); it grows a stack every 6 s (heroic 4 s). Each
 *                     stack: 1% Frost every 2 s and a 10% slow. Bots: dispel it only with no ally within 8 yd and not
 *                     during the Eye (X1's DispelEntry `when`); carriers at 2+ stacks keep 8 yd from allies outside
 *                     the Eye (a rolling self-keyed RunOut, never resolved).
 *   MK2 Shatter       a dispel (spell_st_maleki_icy_death: every stack goes at once) or a snapped Siphon bursts the
 *                     stacks in an 8 yd registry circle on the carrier (spared): 7% / 8% Frost per stack and a 2 s
 *                     root (206668), no Weakened (ruling 50). Heroic: each non-tank ally hit gains a stack (Frostbite).
 *   MK3 The Siphon    15 s, then every 20 s on the grid: the carrier with the most stacks (none: skipped); a 2 s cast
 *                     (emote line 2) then a 5 s channel tether, both kickable (a reward, priority 1). Each second it
 *                     eats a stack: 6% / 8% Shadow to the carrier, 2% / 3% of his health to him. The carrier 12 yd
 *                     from their spot at the cast's start snaps it, and the stacks left shatter out there. Bots: a
 *                     telegraph-only 12 yd circle on that spot, for the carrier only; the Eye's hit leaves the
 *                     carrier out while it runs (the Siphon wins), the carrier's storm ticks go through RegistryHit.
 *   MK4 Ice Tomb      Icy Death at 5 stacks: the carrier freezes in an Ice Tomb 300584 (8k / 12k; emote line 4), held
 *                     by the kit's HoldInUnit (206673, a stun) for at most 8 s; each second 3% / 4% Shadow to the
 *                     prisoner and 1% / 1.5% of his health to him. Bots: the tomb first (BreakOut).
 *   MK5 The Eye       27 s, then every 30 s: yell line 3 and a 3 s marker on an 8 yd / 6 yd eye 10 to 14 yd from him
 *                     toward the plaza (PickFloorSpot; the eye stalker 300585 anchors it), then a 6 s storm: 10% /
 *                     15% Frost a second outside the eye, Weakened once per player (a hidden registry donut out to 60
 *                     yd; the drawn donut is a Decoy at the 0.25 ratio, 8 / 32 and 6 / 24). He channels the storm
 *                     (206677) when he is free. Heroic: the eye drifts 1.5 yd/s, turning back at the first wall or
 *                     his arena's edge. The falling ice is six storm stalkers (206678) in a ring outside the eye.
 *   MK6 Frostbolt     stock 17503 on the tank every 2.9 to 3.7 s; it waits for his mechanic casts.
 *   Arena             MalekiArena() with LeashOptions (no grips; holds at the edge, evades after 10 s with nobody on
 *                     it).
 *
 * Casts never overlap: the Siphon waits while he channels the storm, the Eye's marker is not a cast (the Siphon's cast
 * may run under it), and the storm runs on its timer even while he channels a Siphon (the build spec's collision every
 * 60 s: at 55 s the Siphon lands as the eye is marked). Every timer runs on the AI's own clock (MalekiLogic.h
 * Timeline), never on BossAI's scheduler that a cast bar pauses. Every firing logs one INFO line "strat maleki
 * <mechanic> ..." (module.dungeonbosses); `.dbtest strat maleki <mechanic>` fires one.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "InstanceScript.h"
#include "MalekiLogic.h"
#include "Map.h"
#include "MechanicRegistry.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "Spell.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StratholmeKit.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <string>
#include <unordered_map>
#include <vector>

using namespace Acore::ChatCommands;
using namespace StratholmeRework;
using namespace StratMaleki;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;

namespace
{
    char const* const kBossLogName = "maleki";
    uint8 constexpr kSchoolFrost = 4;               // SPELL_SCHOOL_FROST
    float constexpr kStormZTolerance = 8.f;         // the walkway (z 134-136) above the plaza (z 130-132)
    float constexpr kEyeArenaMarginYd = 2.f;        // the drifting eye turns back this far inside his arena's edge

    // The floor under a point (a summon stands on it); falls back to the given height.
    float FloorZ(WorldObject const* ref, float x, float y, float z, bool* found = nullptr)
    {
        float const floor = ref->GetMapHeight(x, y, z + 3.f);
        bool const ok = floor > INVALID_HEIGHT + 1.f && std::fabs(floor - z) <= 5.f;
        if (found)
            *found = ok;
        return ok ? floor : z;
    }

    // The engine rebuilds max health from the create health (the Ravenian's and the Deadmines hard mode's helper).
    void SetCreatureHealth(Creature* creature, uint32 health)
    {
        creature->SetCreateHealth(health);
        creature->SetStatFlatModifier(UNIT_MOD_HEALTH, BASE_VALUE, static_cast<float>(health));
        creature->UpdateMaxHealth();
        creature->SetHealth(creature->GetMaxHealth());
    }

    uint32 RandBelow(uint32 n)
    {
        return n ? urand(0, n - 1) : 0;
    }
}

// Maleki the Pallid 10438
struct boss_maleki_the_pallid_rework : public BossAI
{
    explicit boss_maleki_the_pallid_rework(Creature* creature)
        : BossAI(creature, BOSS_MALEKI), _arenaShape(MalekiArena()), _arena(MalekiArena(), LeashOptions(kBossLogName))
    {
    }

    void Reset() override
    {
        _Reset();
        Cleanup();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);       // DoZoneInCombat, BOSS_MALEKI IN_PROGRESS
        if (!me->IsEngaged())
            return;     // BossAI evaded

        Cleanup();      // a `.dbtest strat maleki` mechanic out of combat may have left something behind
        _heroic = DungeonKit::IsHeroicMap(me);
        _engaged = true;

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_MALEKI;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        RefreshCurseRunOut();
        Talk(YELL_MALEKI_AGGRO);
        Log("engage", Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f})", _heroic ? 1 : 0,
            me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Log("evade", Acore::StringFormat("reason={}", uint32(why)));
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Talk(YELL_MALEKI_DEATH);
        Cleanup();
        BossAI::JustDied(killer);   // BOSS_MALEKI DONE: the instance writes DATA_ZIGGURAT3 and opens door 175381
        Log("death");
    }

    // His summons are the tombs and the eye and storm stalkers: never zoned into combat (the tomb is passive and
    // rooted; the stalkers are helpers).
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    // A kick (or a silence) on the Siphon's cast or channel ends it with the stacks kept (MK3); his own stops are
    // guarded by _ownInterrupt.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (_ownInterrupt || !spell || _siphon.stage == SiphonStage::Idle)
            return;
        if (spell->Id == SPELL_MK_SIPHON_CAST || spell->Id == SPELL_MK_SIPHON_CHANNEL)
            EndSiphon("interrupted", false);
    }

    void UpdateAI(uint32 diff) override
    {
        // Out of combat too: a `.dbtest` tomb still lets go.
        _holds.Update(me, diff);
        UpdateTombs(diff);

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_engaged)
            return;

        // The fight clock moves every tick, cast bar or not (the Pilot's lesson).
        _timeline.Advance(diff);
        UpdateCurses(diff);
        UpdateSiphon(diff);
        UpdateEye();
        if (!_engaged || !me->IsAlive())
            return;

        _runOutMs += diff;
        if (_runOutMs >= kRunOutRefreshMs && _timeline.eye == EyeStage::Idle)
            RefreshCurseRunOut();

        if (_timeline.CurseDue())
            IcyDeath(nullptr, 1);

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;

        // The Siphon waits while he channels (the storm, a Frostbolt); its grid keeps the next one on time.
        if (_siphon.stage == SiphonStage::Idle && _timeline.SiphonDue())
        {
            StartSiphon(nullptr);
            if (me->HasUnitState(UNIT_STATE_CASTING))
                return;
        }

        if (_timeline.FrostboltDue() && _timeline.FrostboltClear(_siphon.stage != SiphonStage::Idle))
            Frostbolt();
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ---- MK1 Icy Death ----------------------------------------------------------------------------------------------

    // `forced`: that player with `stacks` stacks (`.dbtest`), else the timeline's pick with one stack.
    bool IcyDeath(Player* forced, uint32 stacks)
    {
        Player* target = forced ? forced : PickCurse();
        if (!target)
        {
            if (!forced)
                _timeline.CurseRetry();
            return false;
        }
        if (!forced)
            _timeline.CurseDone();
        me->CastSpell(target, SPELL_MK_ICY_DEATH_LOOK, true);
        Talk(EMOTE_MALEKI_CURSE, target);
        uint32 const now = AddCurse(target, int32(std::max<uint32>(1, stacks)), "curse");
        Log("icy-death", Acore::StringFormat("target={} stacks={} heroic={}", target->GetName(), now,
            _heroic ? 1 : 0));
        return true;
    }

    Player* PickCurse()
    {
        std::vector<Player*> players = FightPlayers();
        std::vector<Candidate> candidates = Candidates(players);
        std::optional<std::size_t> const pick = PickCurseTarget(candidates, RandBelow);
        return pick ? players[*pick] : nullptr;
    }

    // Adds `delta` stacks from him; a new carrier starts its growth clock; 5 freezes (MK4). Returns the stacks now.
    uint32 AddCurse(Player* player, int32 delta, char const* why)
    {
        if (!player || !player->IsAlive() || _holds.IsHeld(player->GetGUID()))
            return 0;
        uint32 const now = DungeonKit::AddStacks(player, SPELL_MK_ICY_DEATH, delta, me, kCurseMaxStacks);
        if (!now)
        {
            _clocks.erase(player->GetGUID());
            return 0;
        }
        _clocks.try_emplace(player->GetGUID());
        if (delta > 1 || std::string(why) != "curse")
            Log("icy-death-stack", Acore::StringFormat("player={} delta={} now={} why={}", player->GetName(), delta,
                now, why));
        if (Freezes(now))
        {
            Freeze(player);
            return 0;
        }
        return now;
    }

    // Each carrier's clock: a stack every 6 s / 4 s; a carrier whose aura went (eaten, frozen, dead, a class
    // immunity) is forgotten.
    void UpdateCurses(uint32 diff)
    {
        std::vector<std::pair<ObjectGuid, uint32>> grow;
        for (auto it = _clocks.begin(); it != _clocks.end();)
        {
            Player* player = ObjectAccessor::GetPlayer(*me, it->first);
            if (!player || !player->IsAlive() || !DungeonKit::Stacks(player, SPELL_MK_ICY_DEATH))
            {
                it = _clocks.erase(it);
                continue;
            }
            if (uint32 const grown = it->second.Advance(diff, _heroic))
                grow.emplace_back(it->first, grown);
            ++it;
        }
        for (auto const& [guid, grown] : grow)
            if (Player* player = ObjectAccessor::GetPlayer(*me, guid))
                AddCurse(player, int32(grown), "grow");
    }

    // MK1 bots: carriers at 2+ stacks keep 8 yd from the others (a RunOut keyed on the aura), outside the Eye. No
    // telegraph (the humans read their debuff); replaced before it resolves, so it never hits.
    void RefreshCurseRunOut()
    {
        _runOutMs = 0;
        if (_curseRunOut)
            Mechanic::Cancel(me, _curseRunOut);
        MechanicRef ref = Mechanic::RunOut(me, nullptr, kCurseSpreadRadius, Milliseconds(kRunOutWarnMs));
        ref.SelfTrigger(SPELL_MK_ICY_DEATH, kCurseSpreadAt).NoTelegraph().Tag(TAG_ICY_DEATH);
        _curseRunOut = ref.Handle();
    }

    void SuspendCurseRunOut()
    {
        if (_curseRunOut)
            Mechanic::Cancel(me, _curseRunOut);
        _curseRunOut = {};
    }

    // ---- MK2 Shatter ------------------------------------------------------------------------------------------------

    // A player dispelled Icy Death (spell_st_maleki_icy_death took every stack at once).
    void OnCurseDispelled(Player* carrier, uint32 stacks, Unit* dispeller)
    {
        if (!carrier)
            return;
        _clocks.erase(carrier->GetGUID());
        if (_siphon.stage != SiphonStage::Idle && _siphon.carrier == carrier->GetGUID())
            EndSiphon("dispelled", false);
        if (!_engaged)
        {
            Log("shatter-skipped", Acore::StringFormat("player={} stacks={} (not engaged)", carrier->GetName(),
                stacks));
            return;
        }
        Shatter(carrier, stacks, "dispel", dispeller);
    }

    void Shatter(Player* carrier, uint32 stacks, char const* why, Unit* dispeller = nullptr)
    {
        if (!carrier || !stacks)
            return;
        bool const heroic = _engaged ? _heroic : DungeonKit::IsHeroicMap(me);
        float const pct = ShatterPct(stacks, heroic);
        MechanicRef ref = Mechanic::Circle(me, carrier, kShatterRadius, Milliseconds(kShatterWarnMs));
        ref.Damage(pct).Spell(SPELL_MK_SHATTER).Rider(SPELL_MK_SHATTER_ROOT).Tag(TAG_SHATTER);
        if (uint32 const frostbite = kFrostbiteStacks(heroic))
            ref.OnHit(OnFrostbite(frostbite));
        Track(ref.Handle());
        // The self-cure gap (X1): a bot curing itself skips DispelEntry::when; `self` and `near` measure it.
        uint32 near = 0;
        for (Player* p : FightPlayers())
            if (p != carrier && p->GetExactDist2d(carrier) <= kShatterRadius)
                ++near;
        Log("shatter", Acore::StringFormat("carrier={} stacks={} pct={:.0f} why={} by={} self={} near={} heroic={}",
            carrier->GetName(), stacks, pct, why, dispeller ? dispeller->GetName() : std::string("-"),
            dispeller == carrier ? 1 : 0, near, heroic ? 1 : 0));
    }

    // Heroic Frostbite: each ally the nova hits gains `stacks` of Icy Death (never the tank, never a prisoner).
    // Captures the map and guid only, never a Unit*.
    std::function<void(Unit*)> OnFrostbite(uint32 stacks)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, stacks](Unit* hit)
        {
            Player* player = hit ? hit->ToPlayer() : nullptr;
            Creature* maleki = map ? map->GetCreature(guid) : nullptr;
            if (!player || !maleki || !maleki->IsAlive() || !maleki->IsAIEnabled)
                return;
            if (maleki->GetVictim() == player)
                return;
            if (auto* ai = dynamic_cast<boss_maleki_the_pallid_rework*>(maleki->AI()))
            {
                maleki->CastSpell(player, SPELL_MK_FROSTBITE_LOOK, true);
                ai->AddCurse(player, int32(stacks), "frostbite");
            }
        };
    }

    // ---- MK3 The Siphon ---------------------------------------------------------------------------------------------

    enum class SiphonStage : uint8
    {
        Idle,
        Cast,
        Channel,
    };

    struct SiphonState
    {
        SiphonStage stage = SiphonStage::Idle;
        ObjectGuid carrier;
        Position spot;
        uint32 ms = 0;              // in the current stage
        uint32 snapMs = 0;
        uint32 eatMs = 0;
        uint32 eaten = 0;
        MechanicHandle zone;
    };

    // `forced`: that player (`.dbtest`), else the carrier with the most stacks. False: nobody (skipped).
    bool StartSiphon(Player* forced)
    {
        Player* carrier = forced;
        if (!carrier)
        {
            std::vector<Player*> players = FightPlayers();
            std::vector<Candidate> candidates = Candidates(players);
            std::optional<std::size_t> const pick = PickSiphonCarrier(candidates, RandBelow);
            carrier = pick ? players[*pick] : nullptr;
            _timeline.SiphonDone();
        }
        if (_timeline.nextSiphon > _timeline.now)
            Mechanic::NoteNextCastIn(me, SPELL_MK_SIPHON_CAST, Milliseconds(_timeline.nextSiphon - _timeline.now));
        if (!carrier)
        {
            Log("siphon-skip", "no carrier");
            return false;
        }
        SpellCastResult const result = me->CastSpell(carrier, SPELL_MK_SIPHON_CAST, false);
        if (result != SPELL_CAST_OK)
        {
            Log("siphon-fail", Acore::StringFormat("carrier={} result={}", carrier->GetName(), uint32(result)));
            return false;
        }
        Talk(EMOTE_MALEKI_STAFF, carrier);
        _siphon = SiphonState{};
        _siphon.stage = SiphonStage::Cast;
        _siphon.carrier = carrier->GetGUID();
        _siphon.spot = carrier->GetPosition();

        // Bots: the carrier gets out of a 12 yd circle on their spot (the cast, then the channel). Telegraph-only, for
        // the carrier alone; an outline until the channel starts (a range cue), then the tether's reach.
        BossMechanics::Eligibility onlyCarrier;
        onlyCarrier.carriers.insert(carrier->GetGUID());
        MechanicRef ref = Mechanic::Circle(me, _siphon.spot, kSiphonSnapYd, Milliseconds(kSiphonCastMs));
        ref.Persistent(Milliseconds(kSiphonChannelMs), Milliseconds(kSiphonSnapCheckMs * 2)).Eligible(onlyCarrier)
            .NoFillTimer().Color(BossMechanics::Color::Purple).Tag(TAG_SIPHON);
        _siphon.zone = ref.Handle();

        // The Siphon wins over the Eye: while it runs, the Eye's hit leaves the carrier out (their storm ticks are the
        // script's).
        if (_timeline.eye != EyeStage::Idle)
        {
            _eyeExcluded.insert(carrier->GetGUID());
            RegisterEyeHit();
        }
        Log("siphon", Acore::StringFormat("carrier={} stacks={} spot=({:.1f}, {:.1f}) eye={}", carrier->GetName(),
            DungeonKit::Stacks(carrier, SPELL_MK_ICY_DEATH), _siphon.spot.GetPositionX(), _siphon.spot.GetPositionY(),
            uint32(_timeline.eye)));
        return true;
    }

    void UpdateSiphon(uint32 diff)
    {
        if (_siphon.stage == SiphonStage::Idle)
            return;
        Player* carrier = ObjectAccessor::GetPlayer(*me, _siphon.carrier);
        if (!carrier || !carrier->IsAlive() || !carrier->IsInWorld() || _holds.IsHeld(_siphon.carrier))
        {
            EndSiphon("carrier gone", false);
            return;
        }
        _siphon.ms += diff;
        _siphon.snapMs += diff;
        if (_siphon.snapMs >= kSiphonSnapCheckMs)
        {
            _siphon.snapMs = 0;
            Vec2 const spot{ _siphon.spot.GetPositionX(), _siphon.spot.GetPositionY() };
            if (SiphonSnaps(spot, DungeonKit::PlaneOf(carrier)))
            {
                EndSiphon("snap", true);
                return;
            }
        }

        if (_siphon.stage == SiphonStage::Cast)
        {
            if (_siphon.ms < kSiphonCastMs)
                return;
            // The cast ends: the tether (a real channel, kickable).
            _ownInterrupt = true;
            if (Spell* bar = me->GetCurrentSpell(CURRENT_GENERIC_SPELL))
                if (bar->GetSpellInfo()->Id == SPELL_MK_SIPHON_CAST && bar->getState() != SPELL_STATE_FINISHED)
                    me->InterruptSpell(CURRENT_GENERIC_SPELL, false);
            _ownInterrupt = false;
            SpellCastResult const result = me->CastSpell(carrier, SPELL_MK_SIPHON_CHANNEL, false);
            if (result != SPELL_CAST_OK)
            {
                Log("siphon-fail", Acore::StringFormat("carrier={} channel result={}", carrier->GetName(),
                    uint32(result)));
                EndSiphon("channel refused", false);
                return;
            }
            _siphon.stage = SiphonStage::Channel;
            _siphon.ms = 0;
            _siphon.eatMs = 0;
            return;
        }

        // The channel: a stack a second.
        _siphon.eatMs += diff;
        while (_siphon.eatMs >= kSiphonEatMs && _siphon.stage == SiphonStage::Channel)
        {
            _siphon.eatMs -= kSiphonEatMs;
            if (!EatStack(carrier))
                return;
        }
        if (_siphon.stage == SiphonStage::Channel && _siphon.ms >= kSiphonChannelMs)
            EndSiphon("done", false);
    }

    // One stack eaten: the carrier's hit and his heal. False when the Siphon ended (nothing left).
    bool EatStack(Player* carrier)
    {
        uint32 const had = DungeonKit::Stacks(carrier, SPELL_MK_ICY_DEATH);
        if (!had)
        {
            EndSiphon("nothing left", false);
            return false;
        }
        uint32 const left = DungeonKit::AddStacks(carrier, SPELL_MK_ICY_DEATH, -1, me, kCurseMaxStacks);
        ++_siphon.eaten;
        me->CastSpell(carrier, SPELL_MK_SIPHON_DRAIN, true);
        uint32 const heal = PctOf(me->GetMaxHealth(), kSiphonHealPct(_heroic));
        if (heal)
            me->CastCustomSpell(SPELL_MK_SIPHON_HEAL, SPELLVALUE_BASE_POINT0, int32(heal), me, true);
        Log("siphon-eat", Acore::StringFormat("carrier={} left={} heal={} health={}", carrier->GetName(), left, heal,
            me->GetHealth()));
        if (!left)
        {
            _clocks.erase(carrier->GetGUID());
            EndSiphon("eaten", false);
            return false;
        }
        return true;
    }

    // `snap`: the stacks left shatter at the carrier (MK2); otherwise they stay (a kick) or are gone (eaten).
    void EndSiphon(char const* why, bool snap)
    {
        if (_siphon.stage == SiphonStage::Idle)
            return;
        SiphonState const ended = _siphon;
        _siphon = SiphonState{};

        // A kick lands here from inside Unit::InterruptSpell (OnSpellFailed): its spell is already finished, so only a
        // live cast or channel is stopped.
        _ownInterrupt = true;
        if (Spell* bar = me->GetCurrentSpell(CURRENT_GENERIC_SPELL))
            if (bar->GetSpellInfo()->Id == SPELL_MK_SIPHON_CAST && bar->getState() != SPELL_STATE_FINISHED)
                me->InterruptSpell(CURRENT_GENERIC_SPELL, false);
        if (Spell* channel = me->GetCurrentSpell(CURRENT_CHANNELED_SPELL))
            if (channel->GetSpellInfo()->Id == SPELL_MK_SIPHON_CHANNEL && channel->getState() != SPELL_STATE_FINISHED)
                me->InterruptSpell(CURRENT_CHANNELED_SPELL, true);
        _ownInterrupt = false;
        if (ended.zone)
            Mechanic::Cancel(me, ended.zone);

        Player* carrier = ObjectAccessor::GetPlayer(*me, ended.carrier);
        uint32 const left = carrier ? DungeonKit::Stacks(carrier, SPELL_MK_ICY_DEATH) : 0;
        if (carrier)
            carrier->RemoveAurasDueToSpell(SPELL_MK_SIPHON_CHANNEL, me->GetGUID());
        if (snap && carrier && left)
        {
            carrier->RemoveAurasDueToSpell(SPELL_MK_ICY_DEATH, me->GetGUID());
            _clocks.erase(ended.carrier);
            Shatter(carrier, left, "snap");
        }
        Log("siphon-end", Acore::StringFormat("why={} carrier={} eaten={} left={} stage={} health={}", why,
            carrier ? carrier->GetName() : ended.carrier.ToString(), ended.eaten, snap ? 0 : left,
            uint32(ended.stage), me->GetHealth()));

        // The carrier is back under the Eye's hit.
        if (_eyeExcluded.erase(ended.carrier) && _timeline.eye != EyeStage::Idle)
            RegisterEyeHit();
    }

    // ---- MK4 Ice Tomb -----------------------------------------------------------------------------------------------

    struct Tomb
    {
        ObjectGuid tomb;
        ObjectGuid player;
        uint32 tickMs = 0;
    };

    void Freeze(Player* player)
    {
        player->RemoveAurasDueToSpell(SPELL_MK_ICY_DEATH);
        _clocks.erase(player->GetGUID());
        if (_siphon.stage != SiphonStage::Idle && _siphon.carrier == player->GetGUID())
            EndSiphon("frozen", false);

        bool const heroic = _engaged ? _heroic : DungeonKit::IsHeroicMap(me);
        Creature* tomb = me->SummonCreature(NPC_ST_ICE_TOMB, player->GetPosition(), TEMPSUMMON_MANUAL_DESPAWN);
        if (!tomb)
        {
            Log("tomb-fail", Acore::StringFormat("player={} (no tomb)", player->GetName()));
            return;
        }
        me->CastSpell(player, SPELL_MK_ICE_TOMB_LOOK, true);
        SetCreatureHealth(tomb, kTombHealth(heroic));
        tomb->SetReactState(REACT_PASSIVE);
        tomb->SetFacingTo(player->GetOrientation());

        DungeonKit::HoldSpec spec;
        spec.holdSpell = SPELL_MK_ICE_TOMB_HOLD;
        spec.maxHold = Milliseconds(kTombMaxMs);
        spec.onRelease = OnTombReleased();
        if (!_holds.Hold(tomb, player, spec))
        {
            tomb->DespawnOrUnsummon();
            Log("tomb-fail", Acore::StringFormat("player={} (hold refused)", player->GetName()));
            return;
        }
        Mechanic::TrackUnit(me, tomb);
        BossMechanics::Registry::GetOrCreate(me->GetMap()).NoteHeld(me->GetGUID(), tomb->GetGUID(),
            player->GetGUID(), SPELL_MK_ICE_TOMB_HOLD);
        _tombs.push_back({ tomb->GetGUID(), player->GetGUID(), 0 });
        Talk(EMOTE_MALEKI_FROZEN, player);
        Log("tomb", Acore::StringFormat("player={} health={} heroic={}", player->GetName(), tomb->GetMaxHealth(),
            heroic ? 1 : 0));
    }

    // The kit's release callback (capture the map and guid only): broken, melted, the prisoner gone or the fight
    // over.
    std::function<void(ObjectGuid, ObjectGuid, DungeonKit::HoldEnd)> OnTombReleased()
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid](ObjectGuid holder, ObjectGuid held, DungeonKit::HoldEnd why)
        {
            Creature* maleki = map ? map->GetCreature(guid) : nullptr;
            if (!maleki || !maleki->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_maleki_the_pallid_rework*>(maleki->AI()))
                ai->TombReleased(holder, held, why);
        };
    }

    void TombReleased(ObjectGuid holder, ObjectGuid held, DungeonKit::HoldEnd why)
    {
        if (Creature* tomb = me->GetMap()->GetCreature(holder))
            tomb->DespawnOrUnsummon();
        std::erase_if(_tombs, [held](Tomb const& t) { return t.player == held; });
        Player* player = ObjectAccessor::GetPlayer(*me, held);
        Log("tomb-end", Acore::StringFormat("player={} why={}", player ? player->GetName() : held.ToString(),
            DungeonKit::HoldEndName(why)));
    }

    // Each second a tomb stands (in the fight): the prisoner's drain and his heal. A prisoner freed some other way (a
    // Divine Shield took the hold) is let go.
    void UpdateTombs(uint32 diff)
    {
        std::vector<ObjectGuid> freed;
        std::vector<ObjectGuid> drain;
        for (Tomb& t : _tombs)
        {
            t.tickMs += diff;
            if (t.tickMs < kTombTickMs)
                continue;
            t.tickMs -= kTombTickMs;
            Player* player = ObjectAccessor::GetPlayer(*me, t.player);
            if (!player || !player->IsAlive())
                continue;       // the kit lets go on its next check
            if (!player->HasAura(SPELL_MK_ICE_TOMB_HOLD))
                freed.push_back(t.player);
            else if (_engaged)
                drain.push_back(t.player);
        }
        for (ObjectGuid const& guid : freed)
            _holds.Release(me, guid);
        for (ObjectGuid const& guid : drain)
        {
            Player* player = ObjectAccessor::GetPlayer(*me, guid);
            if (!player)
                continue;
            me->CastSpell(player, SPELL_MK_ICE_TOMB_DRAIN, true);
            uint32 const heal = PctOf(me->GetMaxHealth(), kTombHealPct(_heroic));
            if (heal)
                me->CastCustomSpell(SPELL_MK_ICE_TOMB_HEAL, SPELLVALUE_BASE_POINT0, int32(heal), me, true);
        }
    }

    // ---- MK5 The Eye of the Blizzard --------------------------------------------------------------------------------

    // `scheduled`: the timeline's; else a `.dbtest` Eye now (the next scheduled one stays). `heroic`: the drifting 6 yd
    // eye and the heroic numbers.
    bool StartEye(bool scheduled, bool heroic)
    {
        if (_timeline.eye != EyeStage::Idle)
            return false;
        Position const spot = PickEyeSpot();
        Creature* eye = me->SummonCreature(NPC_ST_EYE, spot, TEMPSUMMON_TIMED_DESPAWN,
            kEyeMarkerMs + kEyeStormMs + 2000);
        if (scheduled)
            _timeline.EyeMarked();
        else
        {
            _timeline.eye = EyeStage::Marker;
            _timeline.eyeAt = _timeline.now;
        }
        if (!eye)
        {
            Log("eye-fail", "no eye stalker");
            _timeline.EyeOver();
            return false;
        }
        eye->SetReactState(REACT_PASSIVE);
        _eye = EyeState{};
        _eye.stalker = eye->GetGUID();
        _eye.heroic = heroic;
        _eye.radius = kEyeRadius(heroic);
        _eye.start = eye->GetPosition();

        Talk(YELL_MALEKI_COLD);
        Mechanic::SetPhase(me, kPhaseEye);
        SuspendCurseRunOut();
        if (_siphon.stage != SiphonStage::Idle)
            _eyeExcluded.insert(_siphon.carrier);

        // The drawn eye: a Decoy donut (humans read it; bots never see it) at the 0.25 ratio, so the hole shows.
        MechanicRef drawn = Mechanic::Donut(me, eye, _eye.radius, EyeDrawnOuter(_eye.radius),
            Milliseconds(kEyeMarkerMs));
        drawn.Persistent(Milliseconds(kEyeStormMs), Milliseconds(kEyeTickMs)).ZTolerance(kStormZTolerance).Decoy()
            .Tag(TAG_EYE_DRAWN);
        _eye.drawn = drawn.Handle();
        RegisterEyeHit();
        Log("eye", Acore::StringFormat("at=({:.1f}, {:.1f}, {:.1f}) from_boss={:.1f} radius={:.0f} heroic={} "
            "scheduled={}", spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(), me->GetExactDist2d(&spot),
            _eye.radius, heroic ? 1 : 0, scheduled ? 1 : 0));
        return true;
    }

    // 10 to 14 yd from him toward his plaza, on its floor (navmesh-reachable, inside his arena); the measured centres
    // (StratholmeRework.h kMalekiEyeCenters) are the fallback.
    Position PickEyeSpot()
    {
        Vec2 const plaza = ArenaCenter();
        DungeonKit::FloorSpotRules rules;
        rules.near = EyeAim(DungeonKit::PlaneOf(me), plaza, kMalekiSpawn.o);
        rules.minRange = 0.f;
        rules.maxRange = kEyeAimSlackYd;
        rules.tries = 24;
        rules.bestEffort = true;
        DungeonKit::FloorProbe probe;
        probe.z = me->GetPositionZ();
        probe.zBand = 6.f;
        probe.probeUp = 3.f;
        probe.reachable = true;
        std::vector<Vec2> fixed;
        for (Point3 const& c : kMalekiEyeCenters)
            fixed.push_back(c.XY());
        if (std::optional<Position> spot = DungeonKit::PickFloorSpot(me, &_arenaShape, rules, probe, fixed))
            return *spot;
        Point3 const& c = kMalekiEyeCenters[0];
        return Position(c.x, c.y, c.z, 0.f);
    }

    // The real hit: a hidden donut out to 60 yd on the eye stalker, 10% / 15% a second, Weakened once per player;
    // registered at the marker and again whenever the Siphon's carrier leaves it or comes back (the rest of the marker
    // and the storm, on the storm's 1 s rhythm).
    void RegisterEyeHit()
    {
        if (_eye.hit)
            Mechanic::Cancel(me, _eye.hit);
        _eye.hit = {};
        Creature* eye = me->GetMap()->GetCreature(_eye.stalker);
        if (!eye || _timeline.eye == EyeStage::Idle)
            return;

        uint32 warn = 0;
        uint32 life = 0;
        uint32 const left = _timeline.EyeLeftMs();
        if (_timeline.eye == EyeStage::Marker)
        {
            warn = std::max<uint32>(1, left);
            life = kEyeStormMs;
        }
        else
        {
            uint32 const into = kEyeStormMs - left;
            warn = kEyeTickMs - into % kEyeTickMs;
            if (warn >= left)
                return;
            life = left - warn;
        }

        BossMechanics::Eligibility who;
        if (!_eyeExcluded.empty())
        {
            for (Player* p : FightPlayers())
                if (!_eyeExcluded.count(p->GetGUID()))
                    who.carriers.insert(p->GetGUID());
            if (who.carriers.empty())
                return;     // nobody but the carrier: the script's ticks are the storm
        }
        MechanicRef ref = Mechanic::Donut(me, eye, _eye.radius, kEyeStormReachYd, Milliseconds(warn));
        ref.Persistent(Milliseconds(life), Milliseconds(kEyeTickMs)).Damage(kEyeStormPct(_eye.heroic))
            .Spell(SPELL_MK_EYE_STORM).WeakenedOncePerPlayer().ZTolerance(kStormZTolerance).NoTelegraph()
            .Tag(TAG_EYE);
        if (!who.carriers.empty())
            ref.Eligible(who);
        _eye.hit = ref.Handle();
    }

    void UpdateEye()
    {
        if (_timeline.EyeDue())
            StartEye(true, _heroic);
        if (_timeline.StormDue())
            StartStorm();
        if (_timeline.eye == EyeStage::Storm)
        {
            uint32 const into = _timeline.now - _timeline.eyeAt;
            while (_eye.nextTickMs < kEyeStormMs && into >= _eye.nextTickMs)
            {
                CarrierStormTick();
                _eye.nextTickMs += kEyeTickMs;
            }
            UpdateDrift(into);
        }
        if (_timeline.StormOver())
            EndEye();
    }

    void StartStorm()
    {
        _timeline.StormStarted();
        _eye.nextTickMs = 0;
        Creature* eye = me->GetMap()->GetCreature(_eye.stalker);
        Vec2 const center = eye ? DungeonKit::PlaneOf(eye) : Vec2{ _eye.start.GetPositionX(),
            _eye.start.GetPositionY() };
        float const z = eye ? eye->GetPositionZ() : _eye.start.GetPositionZ();

        // The falling ice: storm stalkers in a ring outside every spot the eye can cover.
        uint32 looks = 0;
        Vec2 const arenaCenter = ArenaCenter();
        for (Vec2 const& p : StormLookRing(center, kStormLookRingYd(_eye.heroic), kStormLookCount,
            frand(0.f, DungeonKit::kTwoPi)))
        {
            if (DungeonKit::Distance(p, arenaCenter) > ArenaRadius() + 3.f)
                continue;
            bool floor = false;
            float const fz = FloorZ(me, p.x, p.y, z, &floor);
            if (!floor)
                continue;
            if (Creature* look = me->SummonCreature(NPC_ST_EYE, p.x, p.y, fz, 0.f, TEMPSUMMON_TIMED_DESPAWN,
                kEyeStormMs + 500))
            {
                look->SetReactState(REACT_PASSIVE);
                look->CastSpell(look, SPELL_MK_EYE_STORM_LOOK, true);
                ++looks;
            }
        }

        // He channels the storm when he is free (a Siphon or a Frostbolt in progress keeps its cast).
        bool channel = false;
        if (!me->HasUnitState(UNIT_STATE_CASTING))
            channel = me->CastSpell(me, SPELL_MK_EYE_CHANNEL, false) == SPELL_CAST_OK;

        if (_eye.heroic && eye)
            StartDrift(eye);
        Log("eye-storm", Acore::StringFormat("looks={} channel={} excluded={} heroic={}", looks, channel ? 1 : 0,
            _eyeExcluded.size(), _eye.heroic ? 1 : 0));
    }

    // The Siphon's carrier, left out of the Eye's hit while the Siphon runs: their own storm ticks when outside the
    // eye (the build spec's collision: "runs out into the storm"), Weakened once.
    void CarrierStormTick()
    {
        if (_eyeExcluded.empty())
            return;
        Creature* eye = me->GetMap()->GetCreature(_eye.stalker);
        if (!eye)
            return;
        for (ObjectGuid const& guid : _eyeExcluded)
        {
            Player* player = ObjectAccessor::GetPlayer(*me, guid);
            if (!player || !player->IsAlive() || _holds.IsHeld(guid))
                continue;
            if (player->GetExactDist2d(eye) <= _eye.radius)
                continue;
            DungeonKit::RegistryHitSpec spec;
            spec.pct = kEyeStormPct(_eye.heroic);
            spec.school = kSchoolFrost;
            spec.spellId = SPELL_MK_EYE_STORM;
            spec.weakened = _eye.carrierWeakened.insert(guid).second;
            spec.tag = TAG_EYE_CARRIER;
            Track(DungeonKit::RegistryHit(me, GuidSet{ guid }, spec));
            Log("eye-carrier-tick", Acore::StringFormat("player={} weakened={}", player->GetName(),
                spec.weakened ? 1 : 0));
        }
    }

    // Heroic: 1.5 yd/s in one direction, turning back at the first wall or his arena's edge (MalekiLogic.h
    // EyeDriftLegs).
    void StartDrift(Creature* eye)
    {
        float const bearing = frand(0.f, DungeonKit::kTwoPi);
        DriftLegs const legs = EyeDriftLegs(FreeYd(eye, bearing, kEyeDriftYd));
        _eye.driftBearing = bearing;
        _eye.driftBack = legs.back;
        _eye.turnAtMs = uint32(legs.forward / kEyeDriftSpeed * 1000.f);
        if (legs.forward > 0.f)
            MoveEye(eye, bearing, legs.forward);
        else
            TurnEyeBack(eye);
        Log("eye-drift", Acore::StringFormat("bearing={:.0f} forward={:.1f} back={:.1f}", bearing * 180.f
            / DungeonKit::kPi, legs.forward, legs.back));
    }

    // The turn comes on the storm's clock (the forward leg's length at 1.5 yd/s), not on the spline: a spline
    // launched this tick may not have started yet.
    void UpdateDrift(uint32 intoStormMs)
    {
        if (!_eye.heroic || _eye.driftBack <= 0.f || intoStormMs < _eye.turnAtMs)
            return;
        if (Creature* eye = me->GetMap()->GetCreature(_eye.stalker))
            TurnEyeBack(eye);
        else
            _eye.driftBack = 0.f;
    }

    void TurnEyeBack(Creature* eye)
    {
        float const back = _eye.driftBack;
        _eye.driftBack = 0.f;
        float const bearing = std::fmod(_eye.driftBearing + DungeonKit::kPi, DungeonKit::kTwoPi);
        float const free = std::min(back, FreeYd(eye, bearing, back));
        if (free > 0.f)
            MoveEye(eye, bearing, free);
    }

    // Free floor ahead of the eye stalker: the first wall on the way, and never past his arena's edge.
    float FreeYd(Creature* eye, float bearing, float want)
    {
        Vec2 const from = DungeonKit::PlaneOf(eye);
        Vec2 const to = DungeonKit::Advance(from, bearing, want);
        Position const hit = eye->GetFirstCollisionPosition(eye->GetPositionX(), eye->GetPositionY(),
            eye->GetPositionZ(), to.x, to.y);
        float const wall = DungeonKit::Distance(from, Vec2{ hit.GetPositionX(), hit.GetPositionY() });
        float const edge = RayLeavesCircle(from, bearing, ArenaCenter(), ArenaRadius() - kEyeArenaMarginYd);
        return std::max(0.f, std::min({ want, wall, edge }));
    }

    void MoveEye(Creature* eye, float bearing, float yd)
    {
        Vec2 const end = DungeonKit::Advance(DungeonKit::PlaneOf(eye), bearing, yd);
        float const z = FloorZ(eye, end.x, end.y, eye->GetPositionZ());
        eye->GetMotionMaster()->MovePoint(1, Position(end.x, end.y, z, bearing), FORCED_MOVEMENT_NONE,
            kEyeDriftSpeed, false);
    }

    void EndEye()
    {
        _timeline.EyeOver();
        Mechanic::SetPhase(me, 0);
        if (_eye.hit)
            Mechanic::Cancel(me, _eye.hit);
        if (_eye.drawn)
            Mechanic::Cancel(me, _eye.drawn);
        if (Creature* eye = me->GetMap()->GetCreature(_eye.stalker))
            eye->DespawnOrUnsummon();
        _eye = EyeState{};
        _eyeExcluded.clear();
        RefreshCurseRunOut();
        Log("eye-end");
    }

    // ---- MK6 Frostbolt ----------------------------------------------------------------------------------------------

    void Frostbolt()
    {
        _timeline.FrostboltDone(urand(kFrostboltMinMs, kFrostboltMaxMs));
        if (Unit* victim = me->GetVictim())
            me->CastSpell(victim, SPELL_FROSTBOLT_MALEKI, false);
    }

    // ---- `.dbtest strat maleki` entry points ------------------------------------------------------------------------

    bool Engaged() const
    {
        return _engaged;
    }

    bool CastingNow() const
    {
        return me->HasUnitState(UNIT_STATE_CASTING);
    }

    void TestCurse(Player* target, uint32 stacks)
    {
        _heroic = _engaged ? _heroic : DungeonKit::IsHeroicMap(me);
        IcyDeath(target, stacks);
    }

    // A dispel's shatter on demand: the target's stacks (at least one) burst as if dispelled.
    void TestShatter(Player* target)
    {
        uint32 const stacks = std::max<uint32>(1, DungeonKit::Stacks(target, SPELL_MK_ICY_DEATH));
        target->RemoveAurasDueToSpell(SPELL_MK_ICY_DEATH);
        _clocks.erase(target->GetGUID());
        Shatter(target, stacks, "test", target);
    }

    bool TestSiphon(Player* target)
    {
        if (!DungeonKit::Stacks(target, SPELL_MK_ICY_DEATH))
            AddCurse(target, 2, "test");
        return StartSiphon(target);
    }

    void TestTomb(Player* target)
    {
        Freeze(target);
    }

    bool TestEye(bool heroic)
    {
        return StartEye(false, heroic);
    }

    std::string TestState()
    {
        std::string out = Acore::StringFormat("engaged={} heroic={} t={}ms next curse/siphon/eye={}/{}/{}ms eye={} "
            "siphon={} tombs={} excluded={}", _engaged ? 1 : 0, _heroic ? 1 : 0, _timeline.now, _timeline.nextCurse,
            _timeline.nextSiphon, _timeline.nextEye, uint32(_timeline.eye), uint32(_siphon.stage), _tombs.size(),
            _eyeExcluded.size());
        for (Player* p : FightPlayers())
            out += Acore::StringFormat("\n  {}: icy death {} held {}", p->GetName(),
                DungeonKit::Stacks(p, SPELL_MK_ICY_DEATH), _holds.IsHeld(p->GetGUID()) ? 1 : 0);
        return out;
    }

private:
    struct EyeState
    {
        ObjectGuid stalker;
        Position start;
        float radius = 8.f;
        bool heroic = false;
        MechanicHandle drawn;
        MechanicHandle hit;
        uint32 nextTickMs = 0;          // into the storm
        GuidSet carrierWeakened;
        float driftBearing = 0.f;
        float driftBack = 0.f;
        uint32 turnAtMs = 0;            // into the storm: the forward leg's end
    };

    // MalekiArena() is one circle (StratholmeRework.h): the eye's aim and the drift's edge.
    Vec2 ArenaCenter() const
    {
        return _arenaShape.Empty() ? kMalekiEyeCenters[0].XY() : _arenaShape.regions.front().center;
    }

    float ArenaRadius() const
    {
        return _arenaShape.Empty() ? 25.f : _arenaShape.regions.front().radius;
    }

    void Log(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, mechanic, detail);
    }

    void Track(MechanicHandle handle)
    {
        if (handle)
            _live.push_back(handle);
    }

    // Boss data (build spec): kick the Siphon (a reward); dispel Icy Death under the spacing condition (a reward on
    // normal, expected on heroic: a higher priority); kill order the Ice Tomb, then him.
    void Describe()
    {
        using BossMechanics::Condition;
        BossMechanics::Descriptor d;
        d.interrupts.emplace_back(NPC_MALEKI, SPELL_MK_SIPHON_CAST, kSiphonKickPriority,
            Milliseconds(kSiphonEveryMs));
        d.interrupts.emplace_back(NPC_MALEKI, SPELL_MK_SIPHON_CHANNEL, kSiphonKickPriority,
            Milliseconds(kSiphonEveryMs));
        d.dispels.emplace_back(SPELL_MK_ICY_DEATH, kDispelPriority(_heroic), false, Milliseconds(0),
            Condition::AllOf({ Condition::Not(Condition::NearPlayer(kDispelSpacingYd)),
                Condition::Not(Condition::Phase(kPhaseEye)) }));
        d.targets.push_back(BossMechanics::TargetEntry(NPC_ST_ICE_TOMB, kTombTargetPriority).BreakOut());
        Mechanic::Describe(me, std::move(d));
        Mechanic::NoteNextCastIn(me, SPELL_MK_SIPHON_CAST, Milliseconds(kSiphonFirstMs));
    }

    // The players of the pull: alive, not GMs, in combat with him or on his arena.
    std::vector<Player*> FightPlayers()
    {
        std::vector<Player*> out;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player || !player->IsAlive() || player->IsGameMaster() || !player->IsInWorld())
                continue;
            if (!me->IsInCombatWith(player) && !_arena.Contains(player))
                continue;
            out.push_back(player);
        }
        return out;
    }

    std::vector<Candidate> Candidates(std::vector<Player*> const& players)
    {
        std::vector<Candidate> out;
        out.reserve(players.size());
        Unit const* victim = me->GetVictim();
        for (Player* p : players)
            out.push_back({ p->GetGUID().GetRawValue(), DungeonKit::Stacks(p, SPELL_MK_ICY_DEATH), p == victim,
                _holds.IsHeld(p->GetGUID()) });
        return out;
    }

    // The pull's state, gone: every mechanic, the tombs and stalkers, every aura of the fight.
    void Cleanup()
    {
        if (_siphon.stage != SiphonStage::Idle)
            EndSiphon("cleanup", false);
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        for (MechanicHandle const& handle : { _curseRunOut, _eye.hit, _eye.drawn })
            if (handle)
                Mechanic::Cancel(me, handle);
        _curseRunOut = {};
        _holds.Clear(me);
        _tombs.clear();
        summons.DespawnAll();
        _clocks.clear();
        _eye = EyeState{};
        _eyeExcluded.clear();
        _siphon = SiphonState{};
        _timeline = Timeline{};
        _runOutMs = 0;
        _engaged = false;
        _arena.Reset();
        if (instance)
            for (uint32 spell : { uint32(SPELL_MK_ICY_DEATH), uint32(SPELL_MK_SIPHON_CHANNEL),
                uint32(SPELL_MK_ICE_TOMB_HOLD), uint32(SPELL_MK_SHATTER_ROOT) })
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
    }

    DungeonKit::Arena _arenaShape;
    DungeonKit::ArenaGuard _arena;
    Timeline _timeline;
    DungeonKit::HoldInUnit _holds;
    std::vector<Tomb> _tombs;
    std::unordered_map<ObjectGuid, CurseClock> _clocks;
    SiphonState _siphon;
    EyeState _eye;
    GuidSet _eyeExcluded;           // the Siphon's carrier while it runs under the Eye
    std::vector<MechanicHandle> _live;
    MechanicHandle _curseRunOut;
    uint32 _runOutMs = 0;
    bool _heroic = false;
    bool _engaged = false;
    bool _ownInterrupt = false;
};

// MK1 Icy Death 206665: a dispel takes every stack at once (stock removes one) and shatters them (MK2) around the
// carrier. The tomb, the Siphon eating the last stack, a death or a class immunity remove it without a dispel, so
// without a nova.
class spell_st_maleki_icy_death : public AuraScript
{
    PrepareAuraScript(spell_st_maleki_icy_death);

    void TakeEveryStack(DispelInfo* dispelInfo)
    {
        _stacks = GetStackAmount();
        dispelInfo->SetRemovedCharges(std::max<uint8>(1, _stacks));
    }

    void ShatterOnDispel(DispelInfo* dispelInfo)
    {
        Player* carrier = GetUnitOwner() ? GetUnitOwner()->ToPlayer() : nullptr;
        Creature* maleki = GetCaster() ? GetCaster()->ToCreature() : nullptr;
        if (!carrier || !maleki || !maleki->IsAlive() || !maleki->IsAIEnabled)
            return;
        if (auto* ai = dynamic_cast<boss_maleki_the_pallid_rework*>(maleki->AI()))
            ai->OnCurseDispelled(carrier, _stacks, dispelInfo->GetDispeller());
    }

    void Register() override
    {
        OnDispel += AuraDispelFn(spell_st_maleki_icy_death::TakeEveryStack);
        AfterDispel += AuraDispelFn(spell_st_maleki_icy_death::ShatterOnDispel);
    }

    uint8 _stacks = 0;
};

// Ice Tomb 300584 (MK4): rooted, passive, never walks home or heals; Maleki's HoldInUnit holds its prisoner and lets
// go when it dies, and despawns it.
struct npc_st_ice_tomb : public ScriptedAI
{
    explicit npc_st_ice_tomb(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
        me->SetControlled(true, UNIT_STATE_ROOT);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void EnterEvadeMode(EvadeReason /*why*/) override { }
    void UpdateAI(uint32 /*diff*/) override { }
};

namespace
{
    boss_maleki_the_pallid_rework* FindMalekiAI(ChatHandler* handler)
    {
        Creature* boss = StratTest::FindBoss(handler, NPC_MALEKI);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_maleki_the_pallid_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Maleki is not running boss_maleki_the_pallid_rework (check the "
                "ScriptName).");
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
        return StratTest::ShowBossInfo(handler, NPC_MALEKI, BOSS_MALEKI);
    }

    // `.dbtest strat maleki state`: the clock, the stages and every fight player's Icy Death.
    bool HandleState(ChatHandler* handler)
    {
        boss_maleki_the_pallid_rework* ai = FindMalekiAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Maleki: {}", ai->TestState());
        return true;
    }

    // `.dbtest strat maleki curse [n]`: Icy Death on the selected player (or you), n stacks (default 1; 5 freezes:
    // MK1, MK4).
    bool HandleCurse(ChatHandler* handler, Optional<uint32> stacks)
    {
        boss_maleki_the_pallid_rework* ai = FindMalekiAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        uint32 const n = std::clamp<uint32>(stacks.value_or(1), 1, kCurseMaxStacks);
        ai->TestCurse(target, n);
        handler->PSendSysMessage("Maleki: Icy Death x{} on {} (MK1{}).", n, target->GetName(),
            n >= kCurseMaxStacks ? ", MK4 the tomb" : "");
        return true;
    }

    // `.dbtest strat maleki shatter`: the selected player's (or your) stacks burst as if dispelled (MK2).
    bool HandleShatter(ChatHandler* handler)
    {
        boss_maleki_the_pallid_rework* ai = FindMalekiAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        ai->TestShatter(target);
        handler->PSendSysMessage("Maleki: Shatter on {} (MK2).", target->GetName());
        return true;
    }

    // `.dbtest strat maleki siphon`: the Siphon on the selected player (or you; 2 stacks first if none). Pull him
    // first (MK3).
    bool HandleSiphon(ChatHandler* handler)
    {
        boss_maleki_the_pallid_rework* ai = FindMalekiAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        if (!ai->Engaged() || ai->CastingNow())
        {
            handler->SendErrorMessage("{}", "Maleki must be in combat and not casting.");
            return false;
        }
        if (!ai->TestSiphon(target))
        {
            handler->SendErrorMessage("{}", "Maleki: the Siphon was refused (see the log).");
            return false;
        }
        handler->PSendSysMessage("Maleki: the Siphon on {} (MK3).", target->GetName());
        return true;
    }

    // `.dbtest strat maleki tomb`: the selected player (or you) freezes in an Ice Tomb (MK4).
    bool HandleTomb(ChatHandler* handler)
    {
        boss_maleki_the_pallid_rework* ai = FindMalekiAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        ai->TestTomb(target);
        handler->PSendSysMessage("Maleki: Ice Tomb on {} (MK4).", target->GetName());
        return true;
    }

    // `.dbtest strat maleki eye [1]`: the Eye now; 1 = the heroic form (6 yd, drifting), 0 = normal; default the
    // map's. Pull him first (MK5).
    bool HandleEye(ChatHandler* handler, Optional<uint32> heroic)
    {
        boss_maleki_the_pallid_rework* ai = FindMalekiAI(handler);
        if (!ai)
            return false;
        if (!ai->Engaged())
        {
            handler->SendErrorMessage("{}", "Maleki must be in combat.");
            return false;
        }
        Creature* boss = StratTest::FindBoss(handler, NPC_MALEKI);
        bool const isHeroic = heroic ? *heroic != 0 : (boss && DungeonKit::IsHeroicMap(boss));
        if (!ai->TestEye(isHeroic))
        {
            handler->SendErrorMessage("{}", "Maleki: an Eye is already up.");
            return false;
        }
        handler->PSendSysMessage("Maleki: the Eye of the Blizzard ({}) (MK5).", isHeroic ? "heroic, drifting"
            : "normal");
        return true;
    }

    ChatCommandTable const& MalekiTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",    HandleInfo,    SEC_GAMEMASTER, Console::No },
            { "state",   HandleState,   SEC_GAMEMASTER, Console::No },
            { "curse",   HandleCurse,   SEC_GAMEMASTER, Console::No },
            { "shatter", HandleShatter, SEC_GAMEMASTER, Console::No },
            { "siphon",  HandleSiphon,  SEC_GAMEMASTER, Console::No },
            { "tomb",    HandleTomb,    SEC_GAMEMASTER, Console::No },
            { "eye",     HandleEye,     SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_maleki_the_pallid_rework()
{
    RegisterDungeonReworkCreatureAI(boss_maleki_the_pallid_rework, StratholmeRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_st_ice_tomb, StratholmeRework::kInstanceScriptName);
    RegisterSpellScript(spell_st_maleki_icy_death);
    StratTest::RegisterBoss("maleki", MalekiTestCommands());
}
