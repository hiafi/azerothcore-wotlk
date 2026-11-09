/*
 * mod-dungeon-bosses, Stratholme S4: Malor the Zealous (11032), "the Medallion's zealot". Build spec ST 1239-1289
 * (docs/dungeons/stratholme-rework.md), handoff section 3.4 rows MZ and 3.5 row S4. Replaces his SmartAI (Head Crack,
 * the instant Ground Smash, Holy Light, Lay on Hands as a full heal): the creature template is rebound by
 * apps/dbc-tools source/npcs/stratholme/malor_the_zealous.py. Pure rules: MalorLogic.h.
 *
 *   MZ1  The blaze         10 s, then every 30 s: the Medallion stalker (300605, on the strongbox) channels a beam at
 *                          him for 12 s (emote line 1)
 *   MZ2  Light of Faith    the lane from the strongbox to him, 3 yd wide: a telegraph-only Soak the bots read (the
 *                          Unclean claim it first, then the others by fewest Searing Faith stacks); the AI judges it
 *                          itself each second from the players' positions, ignoring line of sight
 *   MZ3  Faith             an unblocked second gives him a stack (heroic two), 10 at most; +5% damage done each; one
 *                          fades every 8 s
 *   MZ4  Searing Faith     a non-tank standing in the lane blocks it and gains a stack a second; Holy damage a second
 *                          per stack (2%, heroic 3%); one stack fades every 2 s once out of the lane
 *   MZ5  Unclean           at each blaze's start, on one random non-tank (heroic two), 8 s (yell line 2); two
 *                          seconds in the lane purify it
 *   MZ6  Judgment          the Unclean aura ran out: 40% (heroic 50%) Holy on the bearer alone
 *   MZ7  Ground Smash      15 s, then every 15 s: a 2 s windup (emote line 3), an 8 yd circle on him, tank included:
 *                          30% + Weakened + a 1 s stun
 *   MZ8  Aftershock        heroic: 1.5 s after the Smash lands, a ring from 8 to 14 yd on him: 30% + Weakened
 *   MZ9  Holy Light        20 s, then every 15 s: a 2.5 s interruptible cast; heals him 1% of his health per Faith
 *                          stack (heroic 3% plus 1% per stack)
 *   MZ10 Miracle           once at 10% health: a 3 s cast he kneels for (yell line 4), not interruptible; heals him 8%
 *                          of his health per Faith stack
 *   Arena                  StratholmeRework::LeashOptions on MalorArena() (no grips; holds at the edge). The tank holds
 *                          him at the dais mouth through a Park circle, so the lane is long enough for blockers to
 *                          stand clear of the Smash
 *
 * Every timer runs on the AI's own clock, never on BossAI's scheduler (a cast bar pauses that one). Every firing logs
 * one INFO line "strat malor <mechanic> ..." (module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "MalorLogic.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "StratholmeKit.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

using namespace Acore::ChatCommands;
using namespace StratholmeRework;
using namespace StratMalor;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "malor";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // Players not under the Unclean aura (the free blockers' lane): everyone who is not a tank.
    BossMechanics::Eligibility CleanNonTanks()
    {
        BossMechanics::Eligibility e;
        e.roles = BossMechanics::Role::Healer | BossMechanics::Role::Damage;
        e.auraSpell = SPELL_MZ_UNCLEAN;
        e.minStacks = 0;
        e.maxStacks = 0;
        return e;
    }

    // Players under the Unclean aura (the Unclean lane): they claim the beam first.
    BossMechanics::Eligibility UncleanBearers()
    {
        BossMechanics::Eligibility e;
        e.roles = BossMechanics::Role::Healer | BossMechanics::Role::Damage;
        e.auraSpell = SPELL_MZ_UNCLEAN;
        e.minStacks = 1;
        e.maxStacks = 255;
        return e;
    }
}

// Malor the Zealous 11032
struct boss_malor_the_zealous_rework : public BossAI
{
    explicit boss_malor_the_zealous_rework(Creature* creature)
        : BossAI(creature, BOSS_MALOR), _arena(MalorArena(), LeashOptions(kBossLogName)) { }

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
        options.bossStateId = BOSS_MALOR;
        Mechanic::BeginEncounter(me, options);

        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        _heroic = IsHeroicMap(me);
        _plan.Reset();
        _blazeNominalMs = kBlaze.first;
        _nextBlazeMs = kBlaze.first;
        SummonStalker();
        Describe(_heroic);
        Mechanic::NoteNextCastIn(me, SPELL_MZ_HOLY_LIGHT, Ms(kHolyLight.first));
        _arena.Engage(me);
        Talk(YELL_MALOR_AGGRO);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f}) stalker={}", _heroic ? 1 : 0, me->GetPositionX(),
                me->GetPositionY(), me->GetPositionZ(), _stalker ? 1 : 0));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);   // DONE (the instance's rule), the encounter ends
        Cleanup();
        Talk(YELL_MALOR_DEATH);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("killer={}", killer ? killer->GetName() : "none"));
    }

    // MZ9 / MZ10: a finished cast heals him by his Faith.
    void OnSpellCast(SpellInfo const* spell) override
    {
        if (spell->Id == SPELL_MZ_HOLY_LIGHT)
            HolyLightLanded();
        else if (spell->Id == SPELL_MZ_MIRACLE)
            MiracleLanded();
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        _plan.Interrupted(_clockMs);
        if (spell->Id == SPELL_MZ_HOLY_LIGHT)
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "holy-light-interrupted",
                Acore::StringFormat("faith={}", DungeonKit::Stacks(me, SPELL_MZ_FAITH)));
        else if (spell->Id == SPELL_MZ_MIRACLE)
            me->ClearEmoteState();
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;

        // The AI's own clock: nothing below waits for a cast bar.
        _clockMs += diff;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        UpdateBlaze();
        UpdateUnclean();
        UpdateHousekeeping();
        if (!me->HasUnitState(UNIT_STATE_CASTING))
            UpdateCasts();
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;

        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The players of the fight
    // ----------------------------------------------------------------------------------------------------------------

    // Every living player on the map (a GM is not a player of the fight).
    std::vector<Player*> AlivePlayers() const
    {
        std::vector<Player*> out;
        Map* map = me->FindMap();
        if (!map)
            return out;
        for (auto const& ref : map->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (player && player->IsAlive() && !player->IsGameMaster())
                out.push_back(player);
        }
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MZ1 The blaze, MZ2 Light of Faith, MZ3 Faith, MZ4 Searing Faith
    // ----------------------------------------------------------------------------------------------------------------

    Creature* Stalker() const
    {
        return _stalker ? ObjectAccessor::GetCreature(*me, _stalker) : nullptr;
    }

    // The invisible Medallion on the strongbox: the beam's source. Summoned at the pull, gone with the fight.
    Creature* SummonStalker()
    {
        if (Creature* stalker = Stalker())
            if (stalker->IsAlive() && stalker->IsInWorld())
                return stalker;
        Creature* stalker = me->SummonCreature(NPC_ST_MEDALLION, kMalorsStrongbox.x, kMalorsStrongbox.y,
            kMalorsStrongbox.z, 0.f, TEMPSUMMON_MANUAL_DESPAWN);
        if (!stalker)
        {
            _stalker = ObjectGuid::Empty;
            return nullptr;
        }
        stalker->SetReactState(REACT_PASSIVE);
        _stalker = stalker->GetGUID();
        return stalker;
    }

    uint32 BlazeAge() const
    {
        return _clockMs > _blaze.startMs ? static_cast<uint32>(_clockMs - _blaze.startMs) : 0;
    }

    uint32 BlazeLeft() const
    {
        return _clockMs < _blaze.endMs ? static_cast<uint32>(_blaze.endMs - _clockMs) : 0;
    }

    BossMechanics::ZoneSpec BeamShape() const
    {
        Position const source(kMalorsStrongbox.x, kMalorsStrongbox.y, kMalorsStrongbox.z, 0.f);
        return BossMechanics::Shapes::Line(BossMechanics::Anchor(source), BossMechanics::Anchor(me), kBeamWidth);
    }

    float BeamLength() const
    {
        return DungeonKit::Distance(kBeamSource, DungeonKit::PlaneOf(me));
    }

    // The lane the Unclean claim (telegraph only: the AI judges the beam itself).
    void RegisterUncleanLane(uint32 leftMs)
    {
        if (_blaze.uncleanLane)
            Mechanic::Cancel(me, _blaze.uncleanLane);
        _blaze.uncleanLane = MechanicHandle();
        if (_unclean.empty() || leftMs <= kBeamRefreshWarnMs + kBlazeTickMs)
            return;
        uint32 const warn = leftMs == kBlazeMs ? kBeamWarnMs : kBeamRefreshWarnMs;
        MechanicRef ref = Mechanic::Soak(me, BeamShape(), static_cast<uint8>(_unclean.size()), Ms(warn));
        ref.Eligible(UncleanBearers()).Persistent(Ms(leftMs - warn), Ms(kBlazeTickMs)).Tag(TAG_BEAM_UNCLEAN);
        _blaze.uncleanLane = ref.Handle();
        _blaze.laneLength = BeamLength();
    }

    // The lane for everyone else: one body, the fewest Searing Faith stacks first (the bots rotate).
    void RegisterFreeLane(uint32 leftMs)
    {
        if (_blaze.freeLane)
            Mechanic::Cancel(me, _blaze.freeLane);
        _blaze.freeLane = MechanicHandle();
        if (leftMs <= kBeamRefreshWarnMs + kBlazeTickMs)
            return;
        uint32 const warn = leftMs == kBlazeMs ? kBeamWarnMs : kBeamRefreshWarnMs;
        BossMechanics::Ordering fewest;
        fewest.auraSpell = SPELL_MZ_SEARING_FAITH;
        fewest.ascending = true;
        fewest.capStacks = kSearingClaimCap;
        MechanicRef ref = Mechanic::Soak(me, BeamShape(), 1, Ms(warn));
        ref.Eligible(CleanNonTanks()).Order(fewest).Persistent(Ms(leftMs - warn), Ms(kBlazeTickMs))
            .Tag(TAG_BEAM_FREE);
        _blaze.freeLane = ref.Handle();
        _blaze.laneLength = BeamLength();
        _blaze.freeOpen = true;
    }

    // `scheduled`: the timeline's; else a `.dbtest` blaze now (the next scheduled one stays). False when it could not
    // start (tried again a second later when scheduled).
    bool StartBlaze(bool scheduled)
    {
        if (_blaze.active)
            return false;
        Creature* stalker = SummonStalker();
        if (!stalker)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "blaze-fail", "no stalker");
            return false;
        }
        bool const heroic = _heroic;
        _blaze = Blaze();
        _blaze.active = true;
        _blaze.startMs = _clockMs;
        _blaze.endMs = _clockMs + kBlazeMs;
        _blaze.nextTickMs = _clockMs + kBlazeTickMs;
        _blaze.scheduled = scheduled;

        Talk(EMOTE_MALOR_MEDALLION);
        stalker->CastSpell(me, SPELL_MZ_BLAZE, TRIGGERED_FULL_MASK);

        // MZ5: the Unclean (non-tanks on his threat list; none when only the tank is left).
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.tankIfAlone = false;
        std::vector<Player*> const bearers = DungeonKit::PickPlayers(me, rule, kUncleanCount(heroic));
        std::string names;
        for (Player* player : bearers)
        {
            if (me->AddAura(SPELL_MZ_UNCLEAN, player))
            {
                UncleanTrack track;
                track.endMs = _clockMs + kUncleanMs;
                _unclean[player->GetGUID()] = track;
                names += " " + player->GetName();
            }
        }
        if (!_unclean.empty())
            Talk(YELL_MALOR_UNCLEAN);

        // MZ2: the Unclean claim the lane first; the others' lane opens when none is left, or 3 s in.
        RegisterUncleanLane(kBlazeMs);
        if (FreeBlockersDue(0, _unclean.size()))
            RegisterFreeLane(kBlazeMs);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "blaze",
            Acore::StringFormat("heroic={} scheduled={} length={:.1f}yd unclean={}{} faith={}", heroic ? 1 : 0,
                scheduled ? 1 : 0, BeamLength(), _unclean.size(), names, DungeonKit::Stacks(me, SPELL_MZ_FAITH)));
        return true;
    }

    void EndBlaze()
    {
        if (!_blaze.active)
            return;
        if (_blaze.uncleanLane)
            Mechanic::Cancel(me, _blaze.uncleanLane);
        if (_blaze.freeLane)
            Mechanic::Cancel(me, _blaze.freeLane);
        if (Creature* stalker = Stalker())
            stalker->InterruptNonMeleeSpells(false);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "blaze-end",
            Acore::StringFormat("faith={} unblocked={}s blocked={}s", DungeonKit::Stacks(me, SPELL_MZ_FAITH),
                _blaze.unblockedTicks, _blaze.blockedTicks));
        _blaze = Blaze();
    }

    void UpdateBlaze()
    {
        if (!_blaze.active)
        {
            if (_clockMs >= _nextBlazeMs)
            {
                if (StartBlaze(true))
                {
                    _blazeNominalMs = NextOnCadence(_blazeNominalMs, _clockMs, kBlaze.every);
                    _nextBlazeMs = _blazeNominalMs;
                }
                else
                    _nextBlazeMs = _clockMs + kCastRetryMs;
            }
            return;
        }
        while (_blaze.active && _clockMs >= _blaze.nextTickMs)
        {
            _blaze.nextTickMs += kBlazeTickMs;
            BlazeTick();
            if (_clockMs >= _blaze.endMs)
            {
                EndBlaze();
                return;
            }
        }
        if (!_blaze.active)
            return;

        // Nobody is Unclean any more: their lane is no longer anybody's to claim.
        if (_blaze.uncleanLane && _unclean.empty())
        {
            Mechanic::Cancel(me, _blaze.uncleanLane);
            _blaze.uncleanLane = MechanicHandle();
        }
        // "Unclean first": the free lane opens once no Unclean player is left (or 3 s in).
        if (!_blaze.freeOpen && FreeBlockersDue(BlazeAge(), _unclean.size()))
            RegisterFreeLane(BlazeLeft());
        // The lanes keep the length they had: re-register when the tank moved him.
        if (_blaze.laneLength > 0.f && BlazeLeft() >= kBeamRefreshMinLeftMs
            && BeamNeedsRefresh(_blaze.laneLength, BeamLength()))
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "beam-refresh",
                Acore::StringFormat("{:.1f}yd -> {:.1f}yd", _blaze.laneLength, BeamLength()));
            if (_blaze.uncleanLane)
                RegisterUncleanLane(BlazeLeft());
            if (_blaze.freeLane)
                RegisterFreeLane(BlazeLeft());
        }
    }

    // One second of the blaze: who is in the lane. Nobody (non-tank): Faith. Otherwise every blocker burns.
    void BlazeTick()
    {
        bool const heroic = _heroic;
        std::vector<Player*> const players = AlivePlayers();
        Unit const* victim = me->GetVictim();
        Vec2 const boss = DungeonKit::PlaneOf(me);
        std::vector<Candidate> candidates;
        candidates.reserve(players.size());
        for (Player const* player : players)
        {
            Candidate c;
            c.id = player->GetGUID().GetRawValue();
            c.pos = DungeonKit::PlaneOf(player);
            c.tank = player == victim;
            candidates.push_back(c);
        }
        std::vector<std::size_t> const blockers = Blockers(kBeamSource, boss, kBeamHalfWidth, candidates);

        // MZ5: seconds in the beam purify the Unclean (the tank is never one).
        for (auto it = _unclean.begin(); it != _unclean.end();)
        {
            Player* player = ObjectAccessor::GetPlayer(*me, it->first);
            bool const inBeam = player && player->IsAlive()
                && InBeam(kBeamSource, boss, kBeamHalfWidth, DungeonKit::PlaneOf(player));
            if (player && UncleanTick(it->second, inBeam))
            {
                player->RemoveAurasDueToSpell(SPELL_MZ_UNCLEAN);
                DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "purified", player->GetName());
                it = _unclean.erase(it);
            }
            else
                ++it;
        }

        if (blockers.empty())
        {
            uint32 const had = DungeonKit::Stacks(me, SPELL_MZ_FAITH);
            uint32 const now = FaithAfter(had, kFaithPerSecond(heroic));
            if (now > had)
                DungeonKit::AddStacks(me, SPELL_MZ_FAITH, static_cast<int32>(now - had), me, kFaithMax);
            ++_blaze.unblockedTicks;
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "faith",
                Acore::StringFormat("unblocked +{} -> {} stacks", now - had, now));
            return;
        }
        ++_blaze.blockedTicks;
        std::string detail;
        for (std::size_t const i : blockers)
        {
            Player* player = players[i];
            uint32 const had = DungeonKit::Stacks(player, SPELL_MZ_SEARING_FAITH);
            uint32 const now = SearingAfter(had);
            if (now > had)
                DungeonKit::AddStacks(player, SPELL_MZ_SEARING_FAITH, static_cast<int32>(now - had), me,
                    kSearingMaxStacks);
            HoldFade(_clockMs, _searingNextMs[player->GetGUID()], kSearingFadeMs);
            me->CastSpell(player, SPELL_MZ_SEARING_LOOK, TRIGGERED_FULL_MASK);
            detail += Acore::StringFormat(" {}:{}", player->GetName(), now);
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "searing",
            Acore::StringFormat("blocked by {} pct={:.0f} stacks{}", blockers.size(), kSearingPct(heroic), detail));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MZ6 Judgment: the Unclean aura ran out
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateUnclean()
    {
        for (auto it = _unclean.begin(); it != _unclean.end();)
        {
            if (!UncleanExpired(it->second, _clockMs))
            {
                ++it;
                continue;
            }
            Player* player = ObjectAccessor::GetPlayer(*me, it->first);
            if (player && player->IsAlive())
            {
                player->RemoveAurasDueToSpell(SPELL_MZ_UNCLEAN);
                me->CastSpell(player, SPELL_MZ_JUDGMENT, TRIGGERED_FULL_MASK);
                DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "judgment",
                    Acore::StringFormat("heroic={} on {} pct={:.0f}", _heroic ? 1 : 0, player->GetName(),
                        kJudgmentPct(_heroic)));
            }
            it = _unclean.erase(it);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The slow tick: Faith and Searing Faith fade, the tank's spot, the Miracle's trigger
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateHousekeeping()
    {
        if (_clockMs < _housekeepMs)
            return;
        _housekeepMs = _clockMs + kHousekeepingMs;

        uint32 const faith = DungeonKit::Stacks(me, SPELL_MZ_FAITH);
        if (uint32 const lost = FadeDue(faith, _clockMs, _faithNextMs, kFaithFadeMs))
        {
            DungeonKit::AddStacks(me, SPELL_MZ_FAITH, -static_cast<int32>(lost), me, kFaithMax);
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "faith-fade",
                Acore::StringFormat("-{} -> {} stacks", lost, faith - lost));
        }
        for (Player* player : AlivePlayers())
        {
            uint32 const stacks = DungeonKit::Stacks(player, SPELL_MZ_SEARING_FAITH);
            auto it = _searingNextMs.find(player->GetGUID());
            if (!stacks)
            {
                if (it != _searingNextMs.end())
                    _searingNextMs.erase(it);
                continue;
            }
            if (uint32 const lost = FadeDue(stacks, _clockMs, _searingNextMs[player->GetGUID()], kSearingFadeMs))
                DungeonKit::AddStacks(player, SPELL_MZ_SEARING_FAITH, -static_cast<int32>(lost), me,
                    kSearingMaxStacks);
        }

        UpdatePark();
        if (MiracleDue(me->GetHealthPct(), _plan.MiracleUsed()))
            _plan.ArmMiracle(_clockMs);
    }

    // The tank holds him at the dais mouth (a Park circle, no marker, the tank only; re-registered before it ends).
    void UpdatePark()
    {
        if (_clockMs + kParkRefreshLeadMs < _parkUntilMs)
            return;
        if (_park)
            Mechanic::Cancel(me, _park);
        BossMechanics::Eligibility tankOnly;
        tankOnly.roles = BossMechanics::Role::Tank;
        Position const spot(kFightSpot.x, kFightSpot.y, kMalorsStrongbox.z, 0.f);
        MechanicRef ref = Mechanic::Circle(me, spot, kParkRadius, Ms(kParkHoldMs));
        ref.Park(me).NoTelegraph().Eligible(tankOnly).Tag(TAG_PARK);
        _park = ref.Handle();
        _parkUntilMs = _clockMs + kParkHoldMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The casts: MZ7, MZ9, MZ10 on one plan
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateCasts()
    {
        std::optional<CastPlan::Cast> const next = _plan.Next(_clockMs);
        if (!next)
            return;
        bool started = false;
        switch (*next)
        {
            case CastPlan::Smash:
                StartSmash();
                started = true;
                break;
            case CastPlan::HolyLight:
                started = StartHolyLight();
                break;
            case CastPlan::Miracle:
                started = StartMiracle();
                break;
        }
        if (started)
            _plan.Started(*next, _clockMs);
        else
            _plan.Refused(*next, _clockMs);
    }

    // MZ7: the bar and emote now, the circle on him; its resolve lands the hit, and on heroic the ring after it.
    void StartSmash()
    {
        bool const heroic = _heroic;
        DungeonKit::CastBar(me, SPELL_MZ_SMASH_BAR, nullptr, EMOTE_MALOR_WARHAMMER);
        MechanicRef ref = Mechanic::Circle(me, me, kSmashRadius, Ms(kSmashCastMs));
        ref.Damage(kSmashPct).TankDamage(kSmashPct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_MZ_SMASH_HIT).Weakened()
            .Rider(SPELL_MZ_STUNNED).Tag(TAG_SMASH);
        if (heroic)
            ref.OnResolve(OnMalor([gen = _generation](boss_malor_the_zealous_rework& ai,
                BossMechanics::ResolveResult const& result)
            {
                if (gen == ai._generation)
                    ai.RegisterAftershock(result.hits.size());
            }));
        Track(ref.Handle());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "smash",
            Acore::StringFormat("heroic={} pct={:.0f} radius={:.0f}", heroic ? 1 : 0, kSmashPct, kSmashRadius));
    }

    // MZ8 (heroic): 1.5 s after the Smash landed, a ring from 8 to 14 yd on him.
    void RegisterAftershock(std::size_t smashHits)
    {
        MechanicRef ref = Mechanic::Donut(me, me, kAftershockInner, kAftershockOuter, Ms(kAftershockWarnMs));
        ref.Damage(kAftershockPct).TankDamage(kAftershockPct).School(SPELL_SCHOOL_NORMAL)
            .Spell(SPELL_MZ_AFTERSHOCK_HIT).Weakened().Tag(TAG_AFTERSHOCK);
        Track(ref.Handle());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "aftershock",
            Acore::StringFormat("pct={:.0f} ring={:.0f}-{:.0f} smashHits={}", kAftershockPct, kAftershockInner,
                kAftershockOuter, smashHits));
    }

    // MZ9: a real cast on the interrupt list; OnSpellCast lands it. False when the cast was refused.
    bool StartHolyLight()
    {
        if (me->CastSpell(me, SPELL_MZ_HOLY_LIGHT, false) != SPELL_CAST_OK)
            return false;
        Mechanic::NoteNextCastIn(me, SPELL_MZ_HOLY_LIGHT, Ms(kHolyLight.every));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "holy-light",
            Acore::StringFormat("cast={}ms faith={}", kHolyLightCastMs, DungeonKit::Stacks(me, SPELL_MZ_FAITH)));
        return true;
    }

    void HolyLightLanded()
    {
        uint32 const faith = DungeonKit::Stacks(me, SPELL_MZ_FAITH);
        float const pct = HolyLightHealPct(_heroic, faith);
        uint32 const amount = HealAmount(me->GetMaxHealth(), pct);
        if (amount)
            me->CastCustomSpell(SPELL_MZ_HOLY_LIGHT_HEAL, SPELLVALUE_BASE_POINT0, static_cast<int32>(amount), me,
                TRIGGERED_FULL_MASK);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "holy-light-landed",
            Acore::StringFormat("faith={} heal={:.0f}% = {}", faith, pct, amount));
    }

    // MZ10: kneeling toward the strongbox, the 3 s cast. False when it was refused (tried again in a second).
    bool StartMiracle()
    {
        if (Creature* stalker = Stalker())
            me->SetFacingToObject(stalker);
        me->SetEmoteState(EMOTE_STATE_KNEEL);
        if (me->CastSpell(me, SPELL_MZ_MIRACLE, false) != SPELL_CAST_OK)
        {
            me->ClearEmoteState();
            return false;
        }
        Talk(YELL_MALOR_STRENGTH);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "miracle",
            Acore::StringFormat("health={:.1f}% faith={}", me->GetHealthPct(),
                DungeonKit::Stacks(me, SPELL_MZ_FAITH)));
        return true;
    }

    void MiracleLanded()
    {
        me->ClearEmoteState();
        if (Unit* victim = me->GetVictim())
            me->SetFacingToObject(victim);
        uint32 const faith = DungeonKit::Stacks(me, SPELL_MZ_FAITH);
        float const pct = MiracleHealPct(faith);
        uint32 const amount = HealAmount(me->GetMaxHealth(), pct);
        if (amount)
            me->CastCustomSpell(SPELL_MZ_MIRACLE_HEAL, SPELLVALUE_BASE_POINT0, static_cast<int32>(amount), me,
                TRIGGERED_FULL_MASK);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "miracle-landed",
            Acore::StringFormat("faith={} heal={:.0f}% = {}", faith, pct, amount));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (ST): interrupt Holy Light (expected on heroic); no kill order, no dispels
    // ----------------------------------------------------------------------------------------------------------------

    void Describe(bool heroic)
    {
        BossMechanics::Descriptor d;
        d.interrupts.emplace_back(NPC_MALOR, SPELL_MZ_HOLY_LIGHT, kHolyLightKickPriority(heroic),
            Ms(kHolyLight.every));
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest strat malor` entry points (`heroic` forces the heroic form on a normal map until the next pull)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Blaze,
        Unclean,
        Smash,
        HolyLight,
        Miracle,
    };

    // An empty string when fired; otherwise why not.
    std::string TestFire(TestMechanic mechanic, bool heroic)
    {
        if (!me->IsEngaged())
            return "Malor must be in combat (the Unclean picks among the players on his threat list).";
        _heroic = heroic;
        if (mechanic == TestMechanic::Blaze)
        {
            if (_blaze.active)
                return "A blaze is running.";
            if (!StartBlaze(false))
                return "The blaze could not start (no stalker).";
            return {};
        }
        if (mechanic == TestMechanic::Unclean)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.tankIfAlone = true;
            Player* player = DungeonKit::PickPlayer(me, rule);
            if (!player)
                return "Nobody on his threat list.";
            if (!me->AddAura(SPELL_MZ_UNCLEAN, player))
                return "The aura could not be applied.";
            UncleanTrack track;
            track.endMs = _clockMs + kUncleanMs;
            _unclean[player->GetGUID()] = track;
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "unclean-test", player->GetName());
            return {};
        }
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return "Malor is casting; try again in a moment.";
        switch (mechanic)
        {
            case TestMechanic::Smash:
                StartSmash();
                _plan.Started(CastPlan::Smash, _clockMs);
                break;
            case TestMechanic::HolyLight:
                if (!StartHolyLight())
                    return "The Holy Light cast was refused (silenced, or still casting).";
                _plan.Started(CastPlan::HolyLight, _clockMs);
                break;
            case TestMechanic::Miracle:
                if (!StartMiracle())
                    return "The Miracle cast was refused.";
                _plan.Started(CastPlan::Miracle, _clockMs);
                break;
            default:
                break;
        }
        return {};
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    // `.dbtest strat malor faith <n>`: n Faith stacks on him (a negative number removes).
    uint32 TestFaith(int32 delta)
    {
        return DungeonKit::AddStacks(me, SPELL_MZ_FAITH, delta, me, kFaithMax);
    }

    // `.dbtest strat malor searing <n>`: n Searing Faith stacks on `player`.
    uint32 TestSearing(Player* player, int32 delta)
    {
        return DungeonKit::AddStacks(player, SPELL_MZ_SEARING_FAITH, delta, me, kSearingMaxStacks);
    }

    std::string TestState() const
    {
        auto due = [this](CastPlan::Cast cast)
        {
            std::optional<uint64> const at = _plan.DueAt(cast);
            return at ? static_cast<int64>(*at / 1000) : int64(-1);
        };
        return Acore::StringFormat("clock={}s heroic={} blaze={} (left {}s) nextBlaze={}s faith={} unclean={} "
            "next smash/holylight/miracle={}/{}/{}s", _clockMs / 1000, _heroic ? 1 : 0, _blaze.active ? 1 : 0,
            BlazeLeft() / 1000, _nextBlazeMs / 1000, DungeonKit::Stacks(me, SPELL_MZ_FAITH), _unclean.size(),
            due(CastPlan::Smash), due(CastPlan::HolyLight), due(CastPlan::Miracle));
    }

private:
    struct Blaze
    {
        bool active = false;
        bool scheduled = false;
        bool freeOpen = false;
        uint64 startMs = 0;
        uint64 endMs = 0;
        uint64 nextTickMs = 0;
        float laneLength = 0.f;
        uint32 unblockedTicks = 0;
        uint32 blockedTicks = 0;
        MechanicHandle uncleanLane;
        MechanicHandle freeLane;
    };

    // Runs `fn(ai, result)` on this boss when a mechanic resolves, if he is still there. Captures the map and the guid
    // only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnMalor(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (result.fizzled || !map)
                return;
            Creature* boss = map->GetCreature(guid);
            if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_malor_the_zealous_rework*>(boss->AI()))
                fn(*ai, result);
        };
    }

    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 64)      // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 32);
    }

    // The pull's state: nothing pending, no beam, no Faith, no Searing Faith or Unclean on anyone (Reset, evade, death,
    // a new pull).
    void Cleanup()
    {
        ++_generation;      // a chained ring of an older pull stops
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        if (_park)
            Mechanic::Cancel(me, _park);
        _park = MechanicHandle();
        EndBlaze();
        _blaze = Blaze();
        if (Creature* stalker = Stalker())
        {
            stalker->InterruptNonMeleeSpells(false);
            stalker->DespawnOrUnsummon();
        }
        _stalker = ObjectGuid::Empty;
        if (Map* map = me->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* player = ref.GetSource())
                {
                    player->RemoveAurasDueToSpell(SPELL_MZ_UNCLEAN);
                    player->RemoveAurasDueToSpell(SPELL_MZ_SEARING_FAITH);
                }
        me->RemoveAurasDueToSpell(SPELL_MZ_FAITH);
        me->ClearEmoteState();
        _unclean.clear();
        _searingNextMs.clear();
        _faithNextMs = 0;
        _plan.Reset();
        _clockMs = 0;
        _blazeNominalMs = 0;
        _nextBlazeMs = 0;
        _parkUntilMs = 0;
        _housekeepMs = 0;
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    CastPlan _plan;
    Blaze _blaze;
    std::unordered_map<ObjectGuid, UncleanTrack> _unclean;
    std::unordered_map<ObjectGuid, uint64> _searingNextMs;
    uint64 _faithNextMs = 0;
    uint64 _clockMs = 0;                        // ms since the pull: every timer of the fight
    uint64 _blazeNominalMs = 0;                 // the planned start of the next blaze (start to start)
    uint64 _nextBlazeMs = 0;
    uint64 _housekeepMs = 0;
    uint64 _parkUntilMs = 0;
    uint32 _generation = 0;
    bool _heroic = false;
    ObjectGuid _stalker;
    MechanicHandle _park;
    std::vector<MechanicHandle> _live;
};

namespace
{
    boss_malor_the_zealous_rework* FindMalorAI(ChatHandler* handler)
    {
        Creature* boss = StratTest::FindBoss(handler, NPC_MALOR);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_malor_the_zealous_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Malor is not running boss_malor_the_zealous_rework (check the "
                "ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_malor_the_zealous_rework::TestMechanic mechanic, Optional<uint32> heroic,
        char const* what)
    {
        boss_malor_the_zealous_rework* ai = FindMalorAI(handler);
        if (!ai)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        std::string const error = ai->TestFire(mechanic, isHeroic);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Malor: {} fired ({}).", what, isHeroic ? "heroic" : "normal");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return StratTest::ShowBossInfo(handler, NPC_MALOR, BOSS_MALOR);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_malor_the_zealous_rework* ai = FindMalorAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Malor: {}", ai->TestState());
        return true;
    }

    bool HandleBlaze(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_malor_the_zealous_rework::TestMechanic::Blaze, heroic,
            "the Medallion's blaze (MZ1-MZ5: the beam, the Unclean, Faith and Searing Faith)");
    }

    bool HandleUnclean(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_malor_the_zealous_rework::TestMechanic::Unclean, heroic,
            "Unclean on a random non-tank (MZ5; Judgment in 8 s unless purified, MZ6)");
    }

    bool HandleSmash(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_malor_the_zealous_rework::TestMechanic::Smash, heroic,
            "Ground Smash (MZ7; heroic: the Aftershock ring after it, MZ8)");
    }

    bool HandleHolyLight(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_malor_the_zealous_rework::TestMechanic::HolyLight, heroic, "Holy Light (MZ9)");
    }

    bool HandleMiracle(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_malor_the_zealous_rework::TestMechanic::Miracle, heroic, "the Miracle (MZ10)");
    }

    // `.dbtest strat malor faith <n>`: n Faith stacks on him (negative removes).
    bool HandleFaith(ChatHandler* handler, int32 delta)
    {
        boss_malor_the_zealous_rework* ai = FindMalorAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Malor: now {} stack(s) of Faith.", ai->TestFaith(delta));
        return true;
    }

    // `.dbtest strat malor searing <n>`: n Searing Faith stacks on the selected player (yourself when none).
    bool HandleSearing(ChatHandler* handler, int32 delta)
    {
        boss_malor_the_zealous_rework* ai = FindMalorAI(handler);
        if (!ai)
            return false;
        Player* player = handler->getSelectedPlayerOrSelf();
        if (!player)
            return false;
        handler->PSendSysMessage("Malor: {} now has {} stack(s) of Searing Faith.", player->GetName(),
            ai->TestSearing(player, delta));
        return true;
    }

    // `.dbtest strat malor <sub> [1]`: the optional 1 forces the heroic form (0 forces normal); default: the map's.
    ChatCommandTable const& MalorTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,         SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,        SEC_GAMEMASTER, Console::No },
            { "blaze",      HandleBlaze,        SEC_GAMEMASTER, Console::No },
            { "unclean",    HandleUnclean,      SEC_GAMEMASTER, Console::No },
            { "smash",      HandleSmash,        SEC_GAMEMASTER, Console::No },
            { "holylight",  HandleHolyLight,    SEC_GAMEMASTER, Console::No },
            { "miracle",    HandleMiracle,      SEC_GAMEMASTER, Console::No },
            { "faith",      HandleFaith,        SEC_GAMEMASTER, Console::No },
            { "searing",    HandleSearing,      SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_malor_the_zealous_rework()
{
    RegisterDungeonReworkCreatureAI(boss_malor_the_zealous_rework, StratholmeRework::kInstanceScriptName);
    StratTest::RegisterBoss("malor", MalorTestCommands());
}
