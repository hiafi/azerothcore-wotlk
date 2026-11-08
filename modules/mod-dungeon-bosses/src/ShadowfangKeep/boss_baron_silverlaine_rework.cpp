/*
 * mod-dungeon-bosses, Shadowfang Keep: Baron Silverlaine (WP-S3). Build spec: SK 578-621 (build spec), SK 483-577
 * (design), BS1-BS8; handoff section 3.5 rows BS, section 3.6 row S3. User ruling (handoff section 10, section 7 #21):
 * the echoes come on timers, not at health thresholds.
 *
 * Replaces SmartAI 3887 (the aggro yell, kept here; Veil of Shadow 7068 on the tank, replaced by Accursed Veil).
 *
 *   BS1 Echoes        at 15 s, then every 25 s, in the build spec's kill order (Rethilgore, Razorclaw, Odo, round
 *                     again): a spectral worgen bursts into the hall (yell 1-3). Normal: one alive at a time (a due
 *                     echo waits), each fades after 12 s once its move is done. Heroic (Lingering Echoes): they never
 *                     fade, several live together, a due echo whose kind is alive gives its turn to the next.
 *   BS2/BS3 Echo of Rethilgore   Rethilgore's Soul Drain (SoulDrain.h): channel on a random non-tank, 5% Shadow per
 *                     2 s tick, one Soul Fragment per tick near the drained player (1-body pickup, 6 s): caught, it
 *                     heals the drained player 5%; missed, it streaks to Silverlaine and heals him 3% of his max
 *                     health. Six fragments per echo at most (18%). The drain lasts 12 s on both difficulties
 *                     (user ruling 2026-11-07); a heroic echo then melees until killed.
 *   BS4 Echo of Razorclaw        Razorclaw's Meat Hook (MeatHook.h, HookFor(false)): on arrival, then every 5 s; three
 *                     at most on normal, until killed on heroic; 35% + 1 Weakened, dragged to the echo.
 *   BS5 Echo of Odo   Odo's Hunt (Hunt.h, kEchoHunt): a 2 s howl, then 8 s at 80% of run speed on a random
 *                     non-tank; a catch is a 1.5 s stun and 20% over 1.5 s (205947). One hunt, then it melees.
 *   BS6 Accursed Veil a real 1.5 s interruptible cast on a random non-tank, at 6 s then every 20 s: Curse, 12 s, 3%
 *                     Shadow per 2 s, healing received -50%. Every 2 s a fresh 4 yd Spread around every cursed player;
 *                     anyone else inside catches it with their own 12 s, the tank included.
 *   BS7 The Night Ends (heroic)  at 10% health, once: every echo not alive returns at once (yell 4).
 *   BS8 Melee         stock (DamageModifier 1.7, 2.0 s).
 *
 * The echoes' mechanics register on Silverlaine's encounter (the registry owner), so bots read them as his; the
 * fragment pickups live in his AI, so a fragment outlives the echo that dropped it. Arena: DungeonKit::ArenaGuard on
 * SilverlaineArena() (the alcove and the hall).
 *
 * Every firing logs one "sfk silverlaine <mechanic>" line (module.dungeonbosses, INFO). `.sfktest silverlaine ...`
 * fires one mechanic on demand.
 */

#include "ArenaGuard.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "Hunt.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MeatHook.h"
#include "MechanicRegistry.h"
#include "ObjectAccessor.h"
#include "OdoLogic.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "ShadowfangKeepRework.h"
#include "ShadowfangKeepTestCommand.h"
#include "SilverlaineLogic.h"
#include "SoulDrain.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <array>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ShadowfangKeepRework;
using namespace Silverlaine;

namespace
{
    char constexpr kBoss[] = "silverlaine";

    // A move that found its caster busy (a cast bar) tries again this soon.
    uint32 constexpr kBusyRetryMs = 250;
    // An echo's corpse stays this long.
    uint32 constexpr kEchoCorpseMs = 5000;

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    void LogBs(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    uint32 RandomBelow(uint32 n)
    {
        return n ? urand(0, n - 1) : 0;
    }

    // A live registry mechanic (not finished, not cancelled).
    bool Live(Map const* map, BossMechanics::MechanicHandle handle)
    {
        BossMechanics::Registry const* registry = handle ? Mechanic::Read(map) : nullptr;
        BossMechanics::ActiveMechanic const* m = registry ? registry->Find(handle.id) : nullptr;
        return m && !m->finished && !m->cancelled;
    }

    std::optional<EchoKind> ParseEcho(std::string const& arg)
    {
        if (arg == "rethilgore" || arg == "r" || arg == "1")
            return EchoKind::Rethilgore;
        if (arg == "razorclaw" || arg == "c" || arg == "2")
            return EchoKind::Razorclaw;
        if (arg == "odo" || arg == "o" || arg == "3")
            return EchoKind::Odo;
        return std::nullopt;
    }

    // The hall's arena guard (handoff section 3.2 #1, PT1 item 2): the kit's defaults.
    DungeonKit::ArenaGuardOptions HallGuardOptions()
    {
        DungeonKit::ArenaGuardOptions o;
        // A unit in combat with another live boss is left to that boss: no two guards grip it to and fro (R2 S-2).
        o.skipGrip = DungeonKit::SkipEngagedWithOtherBoss(ShadowfangKeepRework::IsSfkBossEntry);
        o.logPrefix = "sfk silverlaine arena";
        return o;
    }

    // The Echo of Odo's hunt spells: Odo's howl, Hunted and catch (S5, shared as is), this slice's lighter Maul.
    SfkHunt::HuntSpells EchoHuntSpells()
    {
        return { Odo::SPELL_ODO_HUNT_HOWL, Odo::SPELL_ODO_HUNTED, Odo::SPELL_ODO_MAUL_HIT, SPELL_ECHO_MAUL };
    }
}

// Baron Silverlaine 3887
struct boss_baron_silverlaine_rework : public BossAI
{
    explicit boss_baron_silverlaine_rework(Creature* creature) : BossAI(creature, BOSS_SILVERLAINE),
        _hall(SilverlaineArena()), _arena(SilverlaineArena(), HallGuardOptions()) { }

    // ---------------------------------------------------------------------------------------------------------------
    // Encounter
    // ---------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        BossAI::Reset();
        Cleanup();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded
        Talk(YELL_SILVERLAINE_AGGRO);

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_SILVERLAINE;
        Mechanic::BeginEncounter(me, options);
        Describe();

        Cleanup();      // a `.sfktest` mechanic out of combat may have left something behind
        _arena.Engage(me);
        ScheduleVeil(kVeilFirstMs);
        LogBs("engage", Acore::StringFormat("heroic={} veilFirst={}ms echoFirst={}ms", Heroic() ? 1 : 0, kVeilFirstMs,
            kEchoFirstMs));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
        LogBs("evade");
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);   // despawns the echoes (his summons)
        Cleanup();
        LogBs("death");
    }

    // His looks (fragment wisps, streaks) never join the fight; the echoes zone in themselves (npc_sfk_echo).
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
        if (KindOfEntry(summon->GetEntry()))
            Mechanic::TrackUnit(me, summon);
    }

    void SummonedCreatureDies(Creature* summon, Unit* killer) override
    {
        if (std::optional<EchoKind> const kind = KindOfEntry(summon->GetEntry()))
            LogBs("echo-killed", Acore::StringFormat("echo={} killer={} heroic={}", EchoName(*kind),
                killer ? killer->GetName() : "?", Heroic() ? 1 : 0));
    }

    // BS7 (heroic): the hit that takes him to 10% or below brings back every echo not alive, once.
    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        BossAI::DamageTaken(attacker, damage, type, mask);
        if (!me->IsEngaged() || !damage || !me->GetMaxHealth() || damage >= me->GetHealth())
            return;
        float const pct = 100.f * float(me->GetHealth() - damage) / float(me->GetMaxHealth());
        if (NightEndsDue(Heroic(), _nightEnded, pct))
            NightEnds();
    }

    // The real Veil cast finished (a pulse's copy lands through OnHit, triggered, with no target noted).
    void OnSpellCast(SpellInfo const* spell) override
    {
        BossAI::OnSpellCast(spell);
        if (spell->Id != SPELL_ACCURSED_VEIL || !_veilTarget)
            return;
        Player* target = ObjectAccessor::GetPlayer(*me, _veilTarget);
        _veilTarget.Clear();
        LogBs("accursed-veil-landed", Acore::StringFormat("target={}", target ? target->GetName() : "?"));
        EnsurePulse();
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (spell->Id != SPELL_ACCURSED_VEIL || !_veilTarget)
            return;
        _veilTarget.Clear();
        LogBs("accursed-veil-interrupted");
    }

    void UpdateAI(uint32 diff) override
    {
        // The Veil's cadence and pulses and the fragment pickups run every update, also while he casts (a cast bar
        // never pauses them) and out of combat (for .sfktest).
        _timers.Update(diff);
        _pickups.Update(me, diff);

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // pulled off his hall: evading

        // A failed summon (its creature rows missing) skips that turn rather than retrying every update (R1 N-3).
        if (std::optional<EchoKind> const due = _echoes.Update(diff, AliveMask(), Heroic()))
        {
            SpawnEcho(*due, "timer");
            _echoes.Summoned(*due);
        }

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ---------------------------------------------------------------------------------------------------------------
    // Mechanics (public: the echoes and the .sfktest subcommands call them)
    // ---------------------------------------------------------------------------------------------------------------

    // BS1: `kind` bursts into the hall; his yell names it. False when the summon failed.
    bool SpawnEcho(EchoKind kind, char const* why)
    {
        Vec2 const at = EchoSpawn(kind);
        float z = me->GetMapHeight(at.x, at.y, kSilverlaineSpawn.z + 2.f);
        if (z <= INVALID_HEIGHT + 1.f)
            z = kSilverlaineSpawn.z;
        Position const pos(at.x, at.y, z, DungeonKit::BearingTo(at, DungeonKit::PlaneOf(me)));
        TempSummon* echo = me->SummonCreature(EchoEntry(kind), pos, TEMPSUMMON_CORPSE_TIMED_DESPAWN, kEchoCorpseMs);
        if (!echo)
        {
            LogBs("echo-summon-failed", Acore::StringFormat("echo={}", EchoName(kind)));
            return false;
        }
        _echoGuids[static_cast<std::size_t>(kind)] = echo->GetGUID();
        Talk(EchoYell(kind));
        LogBs("echo", Acore::StringFormat("echo={} why={} heroic={} at=({:.1f}, {:.1f}) alive={}", EchoName(kind),
            why, Heroic() ? 1 : 0, at.x, at.y, AliveMask()));
        return true;
    }

    // BS7: every echo not alive returns at once.
    void NightEnds()
    {
        _nightEnded = true;
        Talk(YELL_SILVERLAINE_NIGHT_ENDS);
        std::vector<EchoKind> const returns = NightEndsReturns(AliveMask());
        for (EchoKind const kind : returns)
            SpawnEcho(kind, "night-ends");
        LogBs("night-ends", Acore::StringFormat("returned={}", returns.size()));
    }

    // BS6: the 1.5 s cast on `forced` (a .sfktest caller), else a random non-tank. False when it did not start.
    bool CastVeil(Player* forced = nullptr)
    {
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return false;
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.maxRange = kVeilRange;
            rule.requireLos = true;
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!target)
        {
            LogBs("accursed-veil", "skipped=no-target");
            return false;
        }
        if (me->CastSpell(target, SPELL_ACCURSED_VEIL, false) != SPELL_CAST_OK)
        {
            LogBs("accursed-veil", "skipped=cast-failed target=" + target->GetName());
            return false;
        }
        _veilTarget = target->GetGUID();
        LogBs("accursed-veil", Acore::StringFormat("target={} cast={}ms", target->GetName(), kVeilCastMs));
        return true;
    }

    // BS3: a Soul Fragment near `drained` for the Echo of Rethilgore `echo` (a free point on a 4.5 yd ring, inside the
    // hall). False when every point is taken.
    bool EchoFragment(Creature* echo, Player* drained)
    {
        if (!drained)
            return false;
        float const z = drained->GetPositionZ();
        std::vector<Vec2> const points = EchoFragmentPoints(DungeonKit::PlaneOf(drained), z, _hall);
        std::optional<std::size_t> const pick = Rethilgore::PickFreePoint(points, OccupiedPoints(),
            kEchoFragmentMinGap, RandomBelow);
        if (!pick)
        {
            LogBs("echo-fragment-skipped", Acore::StringFormat("drained={}: no free point", drained->GetName()));
            return false;
        }
        Vec2 const at = points[*pick];
        uint32 const key = _nextFragmentKey++;
        ObjectGuid const owner = drained->GetGUID();

        DungeonKit::PickupSpec spec;
        spec.radius = kEchoFragmentRadius;
        spec.life = Ms(kEchoFragmentLifeMs);
        spec.who.roles = BossMechanics::Role::Healer | BossMechanics::Role::Damage;
        spec.who.carriers = PlayersExcept(owner);
        spec.count = 1;
        spec.color = BossMechanics::Color::Blue;
        spec.visualEntry = NPC_SFK_SOUL_FRAGMENT;
        spec.tag = kTagEchoFragment;
        spec.onPick = [this, key, at, z, owner](Player* taker) { FragmentCaught(key, at, z, owner, taker); };
        spec.onExpire = [this, key, at, z]() { FragmentMissed(key, at, z); };
        if (!_pickups.Add(me, DungeonKit::ToPosition(at, z), std::move(spec)))
            return false;
        _fragments.push_back({ key, at });
        LogBs("echo-fragment", Acore::StringFormat("echo={} drained={} at=({:.1f}, {:.1f})",
            echo ? echo->GetGUID().ToString() : "?", drained->GetName(), at.x, at.y));
        return true;
    }

    // Registry handles made on his encounter (the pulses, the echoes' hook lines): cancelled with his cleanup.
    void Track(BossMechanics::MechanicHandle handle)
    {
        if (!handle)
            return;
        Map const* map = me->GetMap();
        std::erase_if(_live, [map](BossMechanics::MechanicHandle const& h) { return !Live(map, h); });
        _live.push_back(handle);
    }

    std::string StateText() const
    {
        return Acore::StringFormat("next echo {} in {} ms, alive mask {}, night ended {}, fragments {}, veil pulse {}",
            EchoName(_echoes.NextKind()), _echoes.UntilMs(), AliveMask(), _nightEnded ? 1 : 0, _fragments.size(),
            _pulsing ? 1 : 0);
    }

    uint8 AliveMask() const
    {
        uint8 mask = 0;
        for (std::size_t i = 0; i < kEchoKinds; ++i)
            if (Creature const* echo = _echoGuids[i] ? me->GetMap()->GetCreature(_echoGuids[i]) : nullptr)
                if (echo->IsAlive())
                    mask |= Bit(EchoKind(i));
        return mask;
    }

    bool Heroic() const
    {
        return DungeonKit::IsHeroicMap(me);
    }

private:
    struct FragmentEntry
    {
        uint32 key = 0;
        Vec2 at;
    };

    void Describe()
    {
        BossMechanics::Descriptor d;
        // Boss data (build spec): echoes first, then Silverlaine; kick and cure Accursed Veil.
        for (EchoKind const kind : kKillOrder)
            d.targets.emplace_back(EchoEntry(kind), 1, BossMechanics::Who::Dps);
        d.interrupts.emplace_back(NPC_SILVERLAINE, SPELL_ACCURSED_VEIL, 2, Ms(kVeilEveryMs));
        d.dispels.emplace_back(SPELL_ACCURSED_VEIL, 1);
        d.ignores.push_back(BossMechanics::IgnoreEntry(NPC_SFK_SOUL_FRAGMENT));
        Mechanic::Describe(me, std::move(d));
    }

    void ScheduleVeil(uint32 inMs)
    {
        Mechanic::NoteNextCastIn(me, SPELL_ACCURSED_VEIL, Ms(inMs));
        _timers.Schedule(Ms(inMs), [this](TaskContext ctx)
        {
            if (!me->IsEngaged())
                return;
            if (!CastVeil())
            {
                ctx.Repeat(Ms(kVeilRetryMs));
                return;
            }
            Mechanic::NoteNextCastIn(me, SPELL_ACCURSED_VEIL, Ms(kVeilEveryMs));
            ctx.Repeat(Ms(kVeilEveryMs));
        });
    }

    // BS6's pulse: every 2 s while anyone carries the curse, a fresh 4 yd Spread around every cursed player (carriers
    // read at the resolve: a cured player no longer spreads it). A hit copies the curse onto an uncursed player.
    void EnsurePulse()
    {
        if (_pulsing)
            return;
        _pulsing = true;
        Pulse();
        _timers.Schedule(Ms(kVeilPulseMs), [this](TaskContext ctx)
        {
            if (!Pulse())
            {
                _pulsing = false;
                return;
            }
            ctx.Repeat(Ms(kVeilPulseMs));
        });
    }

    // One pulse; false when nobody is cursed (the pulse stops).
    bool Pulse()
    {
        uint32 cursed = 0;
        for (auto const& ref : me->GetMap()->GetPlayers())
            if (Player const* player = ref.GetSource())
                if (player->IsAlive() && player->HasAura(SPELL_ACCURSED_VEIL))
                    ++cursed;
        if (!cursed)
            return false;

        Map* map = me->GetMap();
        ObjectGuid const bossGuid = me->GetGUID();
        BossMechanics::MechanicRef ref = Mechanic::Spread(me, kVeilSpreadYd, Ms(kVeilWarnMs));
        ref.SelfTrigger(SPELL_ACCURSED_VEIL, 1).School(SPELL_SCHOOL_SHADOW).Spell(SPELL_ACCURSED_VEIL_SPREAD)
            .Tag(kTagAccursedVeil);
        ref.OnHit([map, bossGuid](Unit* hit)
        {
            Player* player = hit ? hit->ToPlayer() : nullptr;
            Creature* boss = map ? map->GetCreature(bossGuid) : nullptr;
            if (!boss || !boss->IsAlive() || !player || !player->IsAlive())
                return;
            if (!VeilCatches(true, player->HasAura(SPELL_ACCURSED_VEIL)))
                return;
            boss->CastSpell(player, SPELL_ACCURSED_VEIL, TRIGGERED_FULL_MASK);
            DungeonKit::LogMechanic(kLogDungeon, kBoss, "accursed-veil-caught",
                Acore::StringFormat("player={}", player->GetName()));
        });
        Track(ref.Handle());
        return true;
    }

    // BS3 caught: the soul returns to the drained player (the streak and 5% of the reference row).
    void FragmentCaught(uint32 key, Vec2 at, float z, ObjectGuid owner, Player* taker)
    {
        ForgetFragment(key);
        Player* soulOwner = ObjectAccessor::GetPlayer(*me, owner);
        int32 const amount = SoulDrain::ReturnSoul(me, DungeonKit::ToPosition(at, z), soulOwner);
        if (!amount)
            return;
        LogBs("echo-fragment-caught", Acore::StringFormat("catcher={} owner={} heal={}",
            taker ? taker->GetName() : "?", soulOwner->GetName(), amount));
    }

    // BS3 missed: it streaks to him and heals him 3% of his max health (Rethilgore's Soul Feast 205917, his number).
    void FragmentMissed(uint32 key, Vec2 at, float z)
    {
        ForgetFragment(key);
        if (!me->IsAlive() || !me->IsInCombat())
            return;
        SoulDrain::Streak(me, DungeonKit::ToPosition(at, z), me);
        int32 const amount = static_cast<int32>(me->CountPctFromMaxHealth(static_cast<int32>(kEchoFeastPct)));
        me->CastCustomSpell(Rethilgore::SPELL_SOUL_FEAST, SPELLVALUE_BASE_POINT0, amount, me, true);
        LogBs("echo-fragment-missed", Acore::StringFormat("heal={}", amount));
    }

    void ForgetFragment(uint32 key)
    {
        std::erase_if(_fragments, [key](FragmentEntry const& f) { return f.key == key; });
    }

    std::vector<Vec2> OccupiedPoints() const
    {
        std::vector<Vec2> out;
        for (FragmentEntry const& f : _fragments)
            out.push_back(f.at);
        return out;
    }

    // The players alive in the map other than `except` (a fragment's catchers: the drained player cannot catch it).
    GuidSet PlayersExcept(ObjectGuid except) const
    {
        GuidSet out;
        for (auto const& ref : me->GetMap()->GetPlayers())
            if (Player* player = ref.GetSource())
                if (player->IsAlive() && !player->IsGameMaster() && player->GetGUID() != except)
                    out.insert(player->GetGUID());
        return out;
    }

    // The pull's state: no curse, no fragment, nothing pending, the echo clock back to 15 s (Reset, evade, death, a
    // new pull). The echoes themselves go with his summons.
    void Cleanup()
    {
        _timers.CancelAll();
        _pulsing = false;
        _veilTarget.Clear();
        _pickups.Clear(me);
        _fragments.clear();
        for (BossMechanics::MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        MeatHook::Forget(me);
        if (me->IsInWorld())
            for (auto const& ref : me->GetMap()->GetPlayers())
                if (Player* player = ref.GetSource())
                {
                    player->RemoveAurasDueToSpell(SPELL_ACCURSED_VEIL, me->GetGUID());
                    for (ObjectGuid const& echo : _echoGuids)
                        if (echo)
                            player->RemoveAurasDueToSpell(Odo::SPELL_ODO_HUNTED, echo);
                }
        _echoGuids.fill(ObjectGuid::Empty);
        _echoes.Start();
        _nightEnded = false;
        _arena.Reset();
    }

    DungeonKit::Arena _hall;                    // the fragments' points stay inside it
    DungeonKit::ArenaGuard _arena;
    DungeonKit::Pickups _pickups;
    TaskScheduler _timers;                      // the Veil's cadence and pulse (never paused by a cast)
    EchoClock _echoes;
    std::array<ObjectGuid, kEchoKinds> _echoGuids{};
    std::vector<FragmentEntry> _fragments;
    std::vector<BossMechanics::MechanicHandle> _live;
    ObjectGuid _veilTarget;                     // the real cast's target while it casts
    uint32 _nextFragmentKey = 1;
    bool _nightEnded = false;
    bool _pulsing = false;
};

namespace
{
    boss_baron_silverlaine_rework* SilverlaineAIOf(Creature* boss)
    {
        return boss && boss->IsAlive() && boss->IsAIEnabled ? dynamic_cast<boss_baron_silverlaine_rework*>(boss->AI())
            : nullptr;
    }
}

// The echoes 300503 / 300504 / 300505 (BS1-BS5): spectral, stunnable kit adds summoned by Silverlaine. Each runs its
// boss's mechanic on Silverlaine's encounter, melees when it has nothing else to do, and fades after 12 s on normal
// (once its move is done); on heroic it acts until killed.
struct npc_sfk_echo : public ScriptedAI
{
    explicit npc_sfk_echo(Creature* creature) : ScriptedAI(creature), _hall(SilverlaineArena()),
        _kind(KindOfEntry(creature->GetEntry()).value_or(EchoKind::Rethilgore)) { }

    void Reset() override { }

    void IsSummonedBy(WorldObject* summoner) override
    {
        _boss = summoner ? summoner->GetGUID() : ObjectGuid::Empty;
        _heroic = DungeonKit::IsHeroicMap(me);
        _lifeMs = kEchoLifeMs(_heroic);
        me->CastSpell(me, SPELL_SPECTRAL_ECHO, true);
        me->CastSpell(me, SPELL_ECHO_ARRIVAL, true);
        DoZoneInCombat();
        switch (_kind)
        {
            case EchoKind::Rethilgore:
                StartDrain();
                break;
            case EchoKind::Razorclaw:
                ScheduleHook(0);
                break;
            case EchoKind::Odo:
                ScheduleHunt(0);
                break;
        }
    }

    void JustDied(Unit* /*killer*/) override
    {
        StopMove();
    }

    void UpdateAI(uint32 diff) override
    {
        Creature* boss = Boss();
        if (!boss || !boss->IsAlive())
        {
            StopMove();
            me->DespawnOrUnsummon();
            return;
        }
        // Its move's cadence, the drain and the hunt run every update (a cast bar never pauses them).
        _ageMs += diff;
        _timers.Update(diff);
        if (_hunt.Active())
        {
            SfkHunt::HuntEnd const end = _hunt.Update(me, diff);
            if (end != SfkHunt::HuntEnd::None)
                DungeonKit::LogMechanic(kLogDungeon, kBoss, "echo-hunt-end", SfkHunt::HuntEndName(end));
        }
        if (_kind == EchoKind::Rethilgore)
            if (Player* drained = Drained())
                SoulDrain::StartChannel(me, drained);

        if (EchoFades(_ageMs, _lifeMs, Busy()))
        {
            Fade();
            return;
        }

        if (_hunt.Active() || !UpdateVictim())
            return;
        if (me->HasUnitState(UNIT_STATE_CASTING) && !SoulDrain::Channeling(me))
            return;
        DoMeleeAttackIfReady();     // the drain allows melee (ALLOW_ACTION_DURING_CHANNEL); a cast bar does not
    }

private:
    Creature* Boss() const
    {
        return _boss ? me->GetMap()->GetCreature(_boss) : nullptr;
    }

    boss_baron_silverlaine_rework* BossAIPtr() const
    {
        return SilverlaineAIOf(Boss());
    }

    // A random non-tank of Silverlaine's fight (his threat list; the tank is his victim).
    Player* PickTarget() const
    {
        Creature* boss = Boss();
        if (!boss)
            return nullptr;
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.maxRange = kEchoPickRange;
        return DungeonKit::PickPlayer(boss, rule);
    }

    // Its move is still under way: a hook line in flight or its cast bar, or the hunt.
    bool Busy() const
    {
        if (_hunt.Active())
            return true;
        for (BossMechanics::MechanicHandle const& h : _lines)
            if (Live(me->GetMap(), h))
                return true;
        return me->HasUnitState(UNIT_STATE_CASTING) && !SoulDrain::Channeling(me);
    }

    // Killing it (or its fade) ends its move early: no drain, no hook line, no hunt.
    void StopMove()
    {
        _timers.CancelAll();
        SoulDrain::StopChannel(me);
        _drained.Clear();
        if (Creature* boss = Boss())
            for (BossMechanics::MechanicHandle const& h : _lines)
                Mechanic::Cancel(boss, h);
        _lines.clear();
        _hunt.Stop(me, false);
    }

    void Fade()
    {
        StopMove();
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "echo-faded", Acore::StringFormat("echo={} age={}ms",
            EchoName(_kind), _ageMs));
        me->DespawnOrUnsummon();
    }

    // ---- BS2 / BS3 Echo of Rethilgore -------------------------------------------------------------------------------

    Player* Drained() const
    {
        Player* player = _drained ? ObjectAccessor::GetPlayer(*me, _drained) : nullptr;
        return player && player->IsAlive() && player->IsInMap(me) ? player : nullptr;
    }

    // The drain on a random non-tank (again when the drained player dies or leaves), its 2 s ticks.
    void StartDrain()
    {
        PickDrained();
        _timers.Schedule(Ms(kEchoDrainTickMs), [this](TaskContext ctx)
        {
            DrainTick();
            if (EchoDrainGoesOn(++_drainTicks))
                ctx.Repeat(Ms(kEchoDrainTickMs));
            else
                EndDrain();
        });
    }

    // The 12 s cap (user ruling): the channel ends; a heroic echo goes on meleeing until killed.
    void EndDrain()
    {
        SoulDrain::StopChannel(me);
        _drained.Clear();
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "echo-soul-drain-end", Acore::StringFormat("ticks={} heroic={}",
            _drainTicks, _heroic ? 1 : 0));
    }

    Player* PickDrained()
    {
        Player* target = PickTarget();
        if (!target)
        {
            _drained.Clear();
            return nullptr;
        }
        _drained = target->GetGUID();
        Talk(EMOTE_ECHO_MOVE, target);
        SoulDrain::StartChannel(me, target);
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "echo-soul-drain", "drained=" + target->GetName());
        return target;
    }

    // BS2: 5% Shadow on the drained player; BS3: a fragment near them while the echo's six last.
    void DrainTick()
    {
        Player* drained = Drained();
        if (!drained)
            drained = PickDrained();
        if (!drained)
            return;
        SoulDrain::Tick(me, drained);
        if (!EchoFragmentOnTick(_fragments))
            return;
        if (boss_baron_silverlaine_rework* boss = BossAIPtr())
            if (boss->EchoFragment(me, drained))
                ++_fragments;
    }

    // ---- BS4 Echo of Razorclaw --------------------------------------------------------------------------------------

    void ScheduleHook(uint32 inMs)
    {
        _timers.Schedule(Ms(inMs), [this](TaskContext ctx)
        {
            if (!EchoMayHook(_heroic, _hooks))
                return;
            if (me->HasUnitState(UNIT_STATE_CASTING))
            {
                ctx.Repeat(Ms(kBusyRetryMs));
                return;
            }
            ctx.Repeat(Ms(ThrowHook() ? kEchoHookEveryMs : kEchoHookRetryMs));
        });
    }

    // One Meat Hook (Razorclaw's normal RC1) from the echo, its line on Silverlaine's encounter. False when nobody
    // stood 8+ yd away.
    bool ThrowHook()
    {
        Creature* boss = Boss();
        if (!boss)
            return false;
        MeatHook::ThrowSpec spec;
        spec.tuning = EchoHook();
        spec.clip = &_hall;
        spec.emote = EMOTE_ECHO_MOVE;
        spec.logBoss = kBoss;
        spec.logMechanic = "echo-meat-hook";
        MeatHook::ThrowResult const thrown = MeatHook::Throw(me, spec, boss);
        if (!thrown)
            return false;
        ++_hooks;
        boss_baron_silverlaine_rework* ai = BossAIPtr();
        for (BossMechanics::MechanicHandle const& h : thrown.lines)
        {
            _lines.push_back(h);
            if (ai)
                ai->Track(h);
        }
        return true;
    }

    // ---- BS5 Echo of Odo --------------------------------------------------------------------------------------------

    void ScheduleHunt(uint32 inMs)
    {
        _timers.Schedule(Ms(inMs), [this](TaskContext ctx)
        {
            if (me->HasUnitState(UNIT_STATE_CASTING) || !StartHunt())
                ctx.Repeat(Ms(kEchoHuntRetryMs));
        });
    }

    // One Hunt on a random non-tank (S5's chase, its circle on Silverlaine's encounter). False when nobody qualifies.
    bool StartHunt()
    {
        Creature* boss = Boss();
        Player* target = PickTarget();
        if (!boss || !target)
            return false;
        if (!_hunt.Start(boss, me, target, kEchoHunt, EchoHuntSpells(), kTagEchoHunt))
            return false;
        Talk(EMOTE_ECHO_MOVE, target);
        DungeonKit::LogMechanic(kLogDungeon, kBoss, "echo-hunt", Acore::StringFormat(
            "target={} rate={:.0f}% chase={}ms", target->GetName(), kEchoHunt.ratePct, kEchoHunt.chaseMs));
        return true;
    }

    DungeonKit::Arena _hall;                    // the hook lines stop at its walls
    EchoKind _kind;
    ObjectGuid _boss;
    ObjectGuid _drained;
    TaskScheduler _timers;                      // its move's cadence (never paused by a cast)
    SfkHunt::Hunt _hunt;
    std::vector<BossMechanics::MechanicHandle> _lines;
    uint32 _ageMs = 0;
    uint32 _lifeMs = 0;
    uint32 _fragments = 0;
    uint32 _drainTicks = 0;
    uint32 _hooks = 0;
    bool _heroic = false;
};

// 205945 Accursed Veil (BS6): each 2 s tick of the curse is 3% of the reference non-tank row (the caster's map),
// Shadow; the spell ignores caster modifiers, so only the target's own reductions count.
class spell_sfk_silverlaine_accursed_veil : public AuraScript
{
    PrepareAuraScript(spell_sfk_silverlaine_accursed_veil);

    void CalcAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        amount = static_cast<int32>(DungeonKit::RefFlat(GetCaster(), kVeilTickPct));
        canBeRecalculated = false;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_sfk_silverlaine_accursed_veil::CalcAmount, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE);
    }
};

namespace
{
    boss_baron_silverlaine_rework* SilverlaineAI(ChatHandler* handler)
    {
        Creature* boss = SfkTest::FindBoss(handler, NPC_SILVERLAINE);
        if (!boss)
            return nullptr;
        boss_baron_silverlaine_rework* ai = CAST_AI(boss_baron_silverlaine_rework, boss->AI());
        if (!ai)
            handler->SendErrorMessage("Silverlaine does not run boss_baron_silverlaine_rework (is the instance bound "
                "to {}?).", kInstanceScriptName);
        return ai;
    }

    // `.sfktest silverlaine info`
    bool HandleInfo(ChatHandler* handler)
    {
        return SfkTest::ShowBossInfo(handler, NPC_SILVERLAINE, BOSS_SILVERLAINE);
    }

    // `.sfktest silverlaine state`: the echo clock, the echoes alive, fragments and the Veil's pulse.
    bool HandleState(ChatHandler* handler)
    {
        boss_baron_silverlaine_rework* ai = SilverlaineAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("{}", ai->StateText());
        return true;
    }

    // `.sfktest silverlaine echo <rethilgore|razorclaw|odo>`: that echo now (the clock is not touched). Its mechanic
    // picks from Silverlaine's threat list: pull him first.
    bool HandleEcho(ChatHandler* handler, std::string kind)
    {
        boss_baron_silverlaine_rework* ai = SilverlaineAI(handler);
        if (!ai)
            return false;
        std::optional<EchoKind> const which = ParseEcho(kind);
        if (!which)
        {
            handler->SendErrorMessage("Echo: rethilgore, razorclaw or odo.");
            return false;
        }
        return ai->SpawnEcho(*which, "test");
    }

    // `.sfktest silverlaine veil`: Accursed Veil on the selected player, else the GM (the real 1.5 s cast).
    bool HandleVeil(ChatHandler* handler)
    {
        boss_baron_silverlaine_rework* ai = SilverlaineAI(handler);
        if (!ai)
            return false;
        return ai->CastVeil(handler->getSelectedPlayerOrSelf());
    }

    // `.sfktest silverlaine nightends`: The Night Ends now (any difficulty).
    bool HandleNightEnds(ChatHandler* handler)
    {
        boss_baron_silverlaine_rework* ai = SilverlaineAI(handler);
        if (!ai)
            return false;
        ai->NightEnds();
        return true;
    }

    ChatCommandTable const& SilverlaineTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",      HandleInfo,      SEC_GAMEMASTER, Console::No },
            { "state",     HandleState,     SEC_GAMEMASTER, Console::No },
            { "echo",      HandleEcho,      SEC_GAMEMASTER, Console::No },
            { "veil",      HandleVeil,      SEC_GAMEMASTER, Console::No },
            { "nightends", HandleNightEnds, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_baron_silverlaine_rework()
{
    RegisterDungeonReworkCreatureAI(boss_baron_silverlaine_rework, ShadowfangKeepRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sfk_echo, ShadowfangKeepRework::kInstanceScriptName);
    RegisterSpellScript(spell_sfk_silverlaine_accursed_veil);
    SfkTest::RegisterBoss("silverlaine", SilverlaineTestCommands());
}
