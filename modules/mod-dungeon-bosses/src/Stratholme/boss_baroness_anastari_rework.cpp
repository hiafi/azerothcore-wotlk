/*
 * mod-dungeon-bosses, Stratholme S10: Baroness Anastari (10436), "the death omen". Build spec ST 2630-2677
 * (docs/dungeons/stratholme-rework.md), handoff section 3.4 rows BA and 3.5 row S10. Replaces the stock C++ boss
 * boss_baroness_anastari (the Possess loop, Banshee Curse and Silence are gone; Banshee Wail 16565 on the tank stays):
 * the creature template is rebound by apps/dbc-tools source/npcs/stratholme/baroness_anastari.py, which unbinds the
 * stock script. Pure rules: BaronessLogic.h.
 *
 * Her ziggurat (TYPE_ZIGGURAT1, door 175380) is the instance's: her boss state going DONE opens it (S0).
 *
 *   BA1  The Keening        6 s, then every 30 s: the player with the fewest allies within 10 yd (ties: farthest from
 *                           her, then random; the tank is eligible, Death's Echo is not looked at) gets Keened (206625)
 *                           for 6 s (heroic 5 s), emote line 1, her keening sound. A registry Stack (6 yd) on the
 *                           doomed
 *                           for players without Death's Echo; Echo holders other than the doomed get a hidden
 *                           telegraph-only circle on the same spot, so their bots keep out of it
 *   BA2  Death Knell        when Keened ends (or the doomed dies): 90% (heroic 100%) of the row split evenly among the
 *                           doomed and every player within 6 yd, each share x (1 + that player's Death's Echo stacks)
 *                           (206626, Shadow, no Weakened); then each player hit gains a Death's Echo stack
 *   BA3  Death's Echo       206627: +100% Death Knell damage taken per stack, 45 s, refreshed by each stack, no cap
 *   BA4  Wail of the Banshee 16 s, then every 20 s: a 3 s cast (206628, emote line 2), a registry circle of 12 yd on
 *                           her:
 *                           45% (heroic 50%) Shadow + Terrified (206630, 2 s fear); no Weakened
 *   BA5  The Wail's echo    heroic: 2 s after BA4 lands, a registry donut 8 / 32 yd on her: 40% + Terrified (206631)
 *   BA6  Horrifying Visage  12 s, then every 20 s: a 2 s cast (heroic 1.5 s, emote line 3): she turns to a random
 *                           non-tank and a registry cone (60 degrees, 30 yd) is fixed at that spot at the cast start:
 *                           30% (heroic 35%) Shadow + 1 Weakened + Terrified; heroic: two cones at two players
 *   BA7  Lament for the Living heroic: 21 s, then every 30 s: a 2.5 s interruptible cast (206635, yell line 4);
 *                           finished, it gives every player a Death's Echo stack
 *   BA8  Banshee Wail       stock 16565 on the tank, 1.5 s every 4 s, waits for her mechanic casts (CastPlan)
 *   Arena                   StratholmeRework::LeashOptions on BaronessArena() (no grips; holds at the edge)
 *
 * Every timer runs on the AI's own clock, never on BossAI's scheduler (a cast bar pauses that one). Every firing logs
 * one INFO line "strat baroness <mechanic> ..." (module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "BaronessLogic.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
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
#include <vector>

using namespace Acore::ChatCommands;
using namespace StratholmeRework;
using namespace StratBaroness;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "baroness";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // Players without Death's Echo (the Stack on the doomed: they join).
    BossMechanics::Eligibility WithoutEcho()
    {
        BossMechanics::Eligibility e;
        e.auraSpell = SPELL_BA_DEATHS_ECHO;
        e.minStacks = 0;
        e.maxStacks = 0;
        return e;
    }

    // These Echo holders (and only them) keep out of the doomed's circle.
    BossMechanics::Eligibility EchoHolders(GuidSet const& holders)
    {
        BossMechanics::Eligibility e;
        e.carriers = holders;
        e.auraSpell = SPELL_BA_DEATHS_ECHO;
        e.minStacks = 1;
        e.maxStacks = 255;
        return e;
    }
}

// Baroness Anastari 10436
struct boss_baroness_anastari_rework : public BossAI
{
    explicit boss_baroness_anastari_rework(Creature* creature)
        : BossAI(creature, BOSS_BARONESS), _arena(BaronessArena(), LeashOptions(kBossLogName)) { }

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
        options.bossStateId = BOSS_BARONESS;
        Mechanic::BeginEncounter(me, options);

        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        bool const heroic = IsHeroicMap(me);
        _plan.Reset(heroic);
        _keenNominalMs = kKeen.first;
        _nextKeenMs = kKeen.first;
        Describe(heroic);
        if (heroic)
            Mechanic::NoteNextCastIn(me, SPELL_BA_LAMENT, Ms(kLament.first));
        _arena.Engage(me);
        Talk(YELL_BARONESS_AGGRO);
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
        BossAI::JustDied(killer);   // DONE (her ziggurat's door, the instance's rule), the encounter ends
        Cleanup();
        Talk(YELL_BARONESS_DEATH);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("killer={}", killer ? killer->GetName() : "none"));
    }

    // BA7: the lament finished (a Death's Echo stack on everyone) or was stopped. BA4 / BA6: a cast that ended early
    // frees her for the next one.
    void OnSpellCast(SpellInfo const* spell) override
    {
        if (spell->Id == SPELL_BA_LAMENT)
            LamentLanded();
        // She turned to a player for the Visage: back to her victim.
        else if (spell->Id == SPELL_BA_VISAGE_BAR || spell->Id == SPELL_BA_VISAGE_BAR_HEROIC)
            if (Unit* victim = me->GetVictim())
                me->SetFacingToObject(victim);
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        _plan.Interrupted(_clockMs);
        if (spell->Id == SPELL_BA_LAMENT)
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "lament-interrupted");
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;

        // The AI's own clock: nothing below waits for a cast bar.
        _clockMs += diff;
        if (!_arena.Update(me, diff))
            return;     // off her arena, or nobody on it for 10 s: evading

        UpdateKeening();
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

    // The players the Keening may doom: alive, in combat, within her fight range.
    std::vector<Player*> FightPlayers() const
    {
        std::vector<Player*> out;
        for (Player* player : AlivePlayers())
            if (player->IsInCombat() && me->GetExactDist(player) <= kFightRange)
                out.push_back(player);
        return out;
    }

    Candidate ToCandidate(Player const* player) const
    {
        Candidate c;
        c.id = player->GetGUID().GetRawValue();
        c.pos = { player->GetPositionX(), player->GetPositionY() };
        c.z = player->GetPositionZ();
        c.distToBoss = me->GetExactDist2d(player);
        return c;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BA1 The Keening, BA2 Death Knell, BA3 Death's Echo
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateKeening()
    {
        if (_keen.active)
        {
            Player* doomed = ObjectAccessor::GetPlayer(*me, _keen.doomed);
            bool const alive = doomed && doomed->IsAlive();
            if (alive)
                _keen.lastPos = doomed->GetPosition();
            // The omen ends with the aura's time, or with the doomed (the Knell still lands where they fell).
            if (!alive || _clockMs >= _keen.endMs)
                ResolveKnell(_keen.heroic);
            return;
        }
        if (_clockMs >= _nextKeenMs)
            StartKeen(IsHeroicMap(me));
    }

    // False when nobody can be doomed (tried again in a second).
    bool StartKeen(bool heroic)
    {
        if (_keen.active)
            return false;
        std::vector<Player*> const players = FightPlayers();
        std::vector<Candidate> candidates;
        candidates.reserve(players.size());
        for (Player const* player : players)
            candidates.push_back(ToCandidate(player));
        std::optional<std::size_t> const pick = PickIsolated(candidates, kIsolationRadius, kIsolationZBand,
            std::min(0.9999f, static_cast<float>(rand_norm())));
        if (!pick)
        {
            _nextKeenMs = _clockMs + kCastRetryMs;
            return false;
        }
        Player* doomed = players[*pick];
        uint32 const ms = kKeenMs(heroic);

        // The cadence counts from the planned time, not from a retry.
        _keenNominalMs += kKeen.every;
        _nextKeenMs = std::max<uint64>(_keenNominalMs, _clockMs + 1);

        if (Aura* aura = me->AddAura(SPELL_BA_KEENED, doomed))
        {
            aura->SetMaxDuration(static_cast<int32>(ms));
            aura->SetDuration(static_cast<int32>(ms));
        }
        _keen.active = true;
        _keen.heroic = heroic;
        _keen.doomed = doomed->GetGUID();
        _keen.endMs = _clockMs + ms;
        _keen.lastPos = doomed->GetPosition();
        Talk(EMOTE_BARONESS_KEEN, doomed);
        me->PlayDistanceSound(kSoundKeening);

        // The players without Echo join the doomed's 6 yd; the Echo holders (not the doomed) keep out of them. The
        // second is a telegraph-only circle with no marker: bots read it, humans see the one green disc.
        MechanicRef stack = Mechanic::Stack(me, doomed, kKnellRadius, Ms(ms));
        stack.Eligible(WithoutEcho()).Tag(TAG_KEEN_STACK);
        _keen.stack = stack.Handle();
        GuidSet holders;
        for (Player* player : AlivePlayers())
            if (player != doomed && DungeonKit::Stacks(player, SPELL_BA_DEATHS_ECHO) > 0)
                holders.insert(player->GetGUID());
        if (!holders.empty())
        {
            MechanicRef avoid = Mechanic::Circle(me, doomed, kKnellRadius, Ms(ms));
            avoid.Eligible(EchoHolders(holders)).NoTelegraph().Tag(TAG_KEEN_AVOID);
            _keen.avoid = avoid.Handle();
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "keen",
            Acore::StringFormat("heroic={} doomed={} allies={} echo={} ms={} holders={}", heroic ? 1 : 0,
                doomed->GetName(), AlliesNear(candidates, *pick, kIsolationRadius, kIsolationZBand),
                DungeonKit::Stacks(doomed, SPELL_BA_DEATHS_ECHO), ms, holders.size()));
        return true;
    }

    // The Death Knell where the doomed stands (or fell): the doomed and every player within 6 yd share it.
    void ResolveKnell(bool heroic)
    {
        if (!_keen.active)
            return;
        Player* doomed = ObjectAccessor::GetPlayer(*me, _keen.doomed);
        bool const doomedAlive = doomed && doomed->IsAlive();
        Position const center = doomedAlive ? doomed->GetPosition() : _keen.lastPos;
        if (_keen.stack)
            Mechanic::Cancel(me, _keen.stack);
        if (_keen.avoid)
            Mechanic::Cancel(me, _keen.avoid);
        if (doomed)
            doomed->RemoveAurasDueToSpell(SPELL_BA_KEENED);
        _keen = Keen();

        std::vector<Player*> const players = AlivePlayers();
        std::vector<Candidate> candidates;
        candidates.reserve(players.size());
        for (Player const* player : players)
            candidates.push_back(ToCandidate(player));
        std::vector<std::size_t> const inside = KnellInside(candidates, { center.GetPositionX(),
            center.GetPositionY() }, center.GetPositionZ(), kKnellRadius, kKnellZBand);
        if (inside.empty())
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death-knell",
                Acore::StringFormat("heroic={} nobody inside at=({:.1f}, {:.1f})", heroic ? 1 : 0,
                    center.GetPositionX(), center.GetPositionY()));
            return;
        }

        // The shares read the Echo stacks before this Knell adds its own.
        std::vector<Unit*> takers;
        takers.reserve(inside.size());
        for (std::size_t const i : inside)
            takers.push_back(players[i]);
        std::vector<std::pair<ObjectGuid, uint32>> const shares = DungeonKit::WeightedShares(me, takers,
            kKnellPct(heroic), SPELL_BA_DEATHS_ECHO, kEchoPerStack);
        std::string detail;
        for (std::size_t i = 0; i < takers.size() && i < shares.size(); ++i)
        {
            Unit* taker = takers[i];
            uint32 const stacks = DungeonKit::Stacks(taker, SPELL_BA_DEATHS_ECHO);
            detail += Acore::StringFormat(" {}:{}x{}", taker->GetName(), shares[i].second, stacks);
            if (shares[i].second)
                me->CastCustomSpell(SPELL_BA_DEATH_KNELL, SPELLVALUE_BASE_POINT0, static_cast<int32>(shares[i].second),
                    taker, TRIGGERED_FULL_MASK);
        }
        for (Unit* taker : takers)
            if (taker->IsAlive())
                DungeonKit::AddStacks(taker, SPELL_BA_DEATHS_ECHO, 1, me);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death-knell",
            Acore::StringFormat("heroic={} doomed={} alive={} takers={} shares(name:dmg x stacks){}", heroic ? 1 : 0,
                doomed ? doomed->GetName() : "none", doomedAlive ? 1 : 0, takers.size(), detail));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The casts: BA4, BA6, BA7, BA8 on one plan
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateCasts()
    {
        std::optional<CastPlan::Cast> const next = _plan.Next(_clockMs);
        if (!next)
            return;
        bool const heroic = _plan.Heroic();
        bool started = false;
        switch (*next)
        {
            case CastPlan::Wail:
                StartWail(heroic);
                started = true;
                break;
            case CastPlan::Visage:
                started = StartVisage(heroic);
                break;
            case CastPlan::Lament:
                started = StartLament();
                break;
            case CastPlan::BansheeWail:
                started = StartBansheeWail();
                break;
        }
        if (started)
            _plan.Started(*next, _clockMs);
        else
            _plan.Refused(*next, _clockMs);
    }

    // BA4: the bar and emote now, the ring on her; its resolve lands the hit, and on heroic the donut after it.
    void StartWail(bool heroic)
    {
        DungeonKit::CastBar(me, SPELL_BA_WAIL_BAR, nullptr, EMOTE_BARONESS_WAIL);
        MechanicRef ref = Mechanic::Circle(me, me, kWailRadius, Ms(kWailCastMs));
        ref.Damage(kWailPct(heroic)).TankDamage(kWailPct(heroic)).School(SPELL_SCHOOL_SHADOW)
            .Spell(SPELL_BA_WAIL_HIT).Rider(SPELL_BA_TERRIFIED).Tag(TAG_WAIL);
        if (heroic)
            ref.OnResolve(OnBaroness([gen = _generation](boss_baroness_anastari_rework& ai,
                BossMechanics::ResolveResult const& result)
            {
                if (gen == ai._generation)
                    ai.RegisterWailEcho(result.hits.size());
            }));
        Track(ref.Handle());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "wail",
            Acore::StringFormat("heroic={} pct={:.0f} radius={:.0f}", heroic ? 1 : 0, kWailPct(heroic), kWailRadius));
    }

    // BA5 (heroic): 2 s after the Wail landed, everyone beyond 8 yd from her.
    void RegisterWailEcho(std::size_t wailHits)
    {
        MechanicRef ref = Mechanic::Donut(me, me, kWailEchoInner, kWailEchoOuter, Ms(kWailEchoWarnMs));
        ref.Damage(kWailEchoPct).TankDamage(kWailEchoPct).School(SPELL_SCHOOL_SHADOW).Spell(SPELL_BA_WAIL_ECHO_HIT)
            .Rider(SPELL_BA_TERRIFIED).Tag(TAG_WAIL_ECHO);
        Track(ref.Handle());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "wail-echo",
            Acore::StringFormat("pct={:.0f} donut={:.0f}-{:.0f} wailHits={}", kWailEchoPct, kWailEchoInner,
                kWailEchoOuter, wailHits));
    }

    // BA6: she turns to a random non-tank and lifts her veil; the cone is fixed at that spot at the cast start (heroic:
    // a second cone at a second player). False when no player can be aimed at.
    bool StartVisage(bool heroic)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.tankIfAlone = true;        // a tank-only group is still aimed at
        Player* first = DungeonKit::PickPlayer(me, rule);
        if (!first)
            return false;
        std::vector<Player*> targets{ first };
        if (kVisageCones(heroic) > 1)
        {
            DungeonKit::PickRule other;
            other.nonTank = true;
            other.tankIfAlone = false;
            other.exclude.push_back(first->GetGUID().GetRawValue());
            if (Player* second = DungeonKit::PickPlayer(me, other))
                targets.push_back(second);
        }

        me->SetFacingToObject(first);
        DungeonKit::CastBar(me, heroic ? SPELL_BA_VISAGE_BAR_HEROIC : SPELL_BA_VISAGE_BAR, nullptr,
            EMOTE_BARONESS_VEIL, first);
        std::string detail;
        for (Player* target : targets)
        {
            Position at = me->GetPosition();
            at.SetOrientation(me->GetAngle(target));
            MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::Cone(at, kVisageAngleDeg, kVisageLengthYd),
                Ms(kVisageCastMs(heroic)));
            ref.Damage(kVisagePct(heroic)).TankDamage(kVisagePct(heroic)).School(SPELL_SCHOOL_SHADOW)
                .Spell(SPELL_BA_VISAGE_HIT).Weakened().Rider(SPELL_BA_TERRIFIED).Tag(TAG_VISAGE);
            Track(ref.Handle());
            detail += Acore::StringFormat(" {}@{:.2f}", target->GetName(), at.GetOrientation());
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "visage",
            Acore::StringFormat("heroic={} cones={} pct={:.0f} cast={}ms{}", heroic ? 1 : 0, targets.size(),
                kVisagePct(heroic), kVisageCastMs(heroic), detail));
        return true;
    }

    // BA7: a real cast on the interrupt list; OnSpellCast lands it. False when the cast was refused.
    bool StartLament()
    {
        if (me->CastSpell(me, SPELL_BA_LAMENT, false) != SPELL_CAST_OK)
            return false;
        Talk(YELL_BARONESS_LAMENT);
        Mechanic::NoteNextCastIn(me, SPELL_BA_LAMENT, Ms(kLament.every));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "lament", Acore::StringFormat("cast={}ms", kLamentCastMs));
        return true;
    }

    void LamentLanded()
    {
        uint32 stacked = 0;
        for (Player* player : AlivePlayers())
        {
            DungeonKit::AddStacks(player, SPELL_BA_DEATHS_ECHO, 1, me);
            ++stacked;
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "lament-landed", Acore::StringFormat("echo on {}", stacked));
    }

    // BA8: the stock Banshee Wail on her victim (DD scales it on heroic). False when it could not start.
    bool StartBansheeWail()
    {
        Unit* victim = me->GetVictim();
        if (!victim)
            return false;
        return me->CastSpell(victim, SPELL_BANSHEE_WAIL, false) == SPELL_CAST_OK;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (ST): kill order her; interrupt the Lament (heroic); no dispels
    // ----------------------------------------------------------------------------------------------------------------

    void Describe(bool heroic)
    {
        BossMechanics::Descriptor d;
        d.targets.emplace_back(NPC_BARONESS, 1, BossMechanics::Who::Any);
        if (heroic)
            d.interrupts.emplace_back(NPC_BARONESS, SPELL_BA_LAMENT, 3, Ms(kLament.every));
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest strat baroness` entry points (`heroic` forces the heroic form on a normal map)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Keen,
        Knell,
        Wail,
        Visage,
        Lament,
    };

    // An empty string when fired; otherwise why not.
    std::string TestFire(TestMechanic mechanic, bool heroic)
    {
        if (!me->IsEngaged())
            return "The Baroness must be in combat (the keen picks among the players in the fight).";
        if (mechanic == TestMechanic::Knell)
        {
            if (!_keen.active)
                return "No keen is running; fire `keen` first.";
            ResolveKnell(_keen.heroic);
            return {};
        }
        if (mechanic == TestMechanic::Keen)
        {
            if (_keen.active)
                return "A keen is running.";
            if (!StartKeen(heroic))
                return "Nobody in the fight can be doomed (a GM does not count).";
            return {};
        }
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return "The Baroness is casting; try again in a moment.";
        switch (mechanic)
        {
            case TestMechanic::Wail:
                StartWail(heroic);
                _plan.Started(CastPlan::Wail, _clockMs);
                break;
            case TestMechanic::Visage:
                if (!StartVisage(heroic))
                    return "No player on her threat list to turn to.";
                _plan.Started(CastPlan::Visage, _clockMs);
                break;
            case TestMechanic::Lament:
                if (!StartLament())
                    return "The Lament cast was refused (silenced, or still casting).";
                _plan.Started(CastPlan::Lament, _clockMs);
                break;
            default:
                break;
        }
        return {};
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    // `.dbtest strat baroness echo <n>`: n Death's Echo stacks on `player`.
    uint32 TestEcho(Player* player, uint32 stacks)
    {
        return DungeonKit::AddStacks(player, SPELL_BA_DEATHS_ECHO, static_cast<int32>(stacks), me);
    }

    std::string TestState() const
    {
        std::string keen = "none";
        if (_keen.active)
        {
            Player* doomed = ObjectAccessor::GetPlayer(*me, _keen.doomed);
            keen = Acore::StringFormat("{} ends in {}s", doomed ? doomed->GetName() : "?",
                _keen.endMs > _clockMs ? (_keen.endMs - _clockMs) / 1000 : 0);
        }
        auto due = [this](CastPlan::Cast cast)
        {
            std::optional<uint64> const at = _plan.DueAt(cast);
            return at ? static_cast<int64>(*at / 1000) : int64(-1);
        };
        return Acore::StringFormat("clock={}s keen={} nextKeen={}s heroic={} next wail/visage/lament/filler="
            "{}/{}/{}/{}s", _clockMs / 1000, keen, _nextKeenMs / 1000, _plan.Heroic() ? 1 : 0,
            due(CastPlan::Wail), due(CastPlan::Visage), due(CastPlan::Lament), due(CastPlan::BansheeWail));
    }

private:
    struct Keen
    {
        bool active = false;
        bool heroic = false;
        ObjectGuid doomed;
        uint64 endMs = 0;
        Position lastPos;
        MechanicHandle stack;
        MechanicHandle avoid;
    };

    // Runs `fn(ai, result)` on this boss when a mechanic resolves, if he is still there. Captures the map and the guid
    // only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnBaroness(Fn fn)
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
            if (auto* ai = dynamic_cast<boss_baroness_anastari_rework*>(boss->AI()))
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

    // The pull's state: nothing pending, no keen, no Echo or Keened on anyone (Reset, evade, death, a new pull).
    void Cleanup()
    {
        ++_generation;      // a chained echo of an older pull stops
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        if (_keen.stack)
            Mechanic::Cancel(me, _keen.stack);
        if (_keen.avoid)
            Mechanic::Cancel(me, _keen.avoid);
        _keen = Keen();
        if (Map* map = me->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* player = ref.GetSource())
                {
                    player->RemoveAurasDueToSpell(SPELL_BA_KEENED);
                    player->RemoveAurasDueToSpell(SPELL_BA_DEATHS_ECHO);
                }
        _plan.Reset(false);
        _clockMs = 0;
        _nextKeenMs = 0;
        _keenNominalMs = 0;
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    CastPlan _plan;
    Keen _keen;
    uint64 _clockMs = 0;                        // ms since the pull: every timer of the fight
    uint64 _nextKeenMs = 0;
    uint64 _keenNominalMs = 0;                  // the planned start of the next keen (the cadence is start to start)
    uint32 _generation = 0;
    std::vector<MechanicHandle> _live;
};

namespace
{
    boss_baroness_anastari_rework* FindBaronessAI(ChatHandler* handler)
    {
        Creature* boss = StratTest::FindBoss(handler, NPC_BARONESS);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_baroness_anastari_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "The Baroness is not running boss_baroness_anastari_rework (check the "
                "ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_baroness_anastari_rework::TestMechanic mechanic, Optional<uint32> heroic,
        char const* what)
    {
        boss_baroness_anastari_rework* ai = FindBaronessAI(handler);
        if (!ai)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        std::string const error = ai->TestFire(mechanic, isHeroic);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("The Baroness: {} fired ({}).", what, isHeroic ? "heroic" : "normal");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return StratTest::ShowBossInfo(handler, NPC_BARONESS, BOSS_BARONESS);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_baroness_anastari_rework* ai = FindBaronessAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("The Baroness: {}", ai->TestState());
        return true;
    }

    bool HandleKeen(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_baroness_anastari_rework::TestMechanic::Keen, heroic,
            "the Keening (BA1: the most isolated player, a Death Knell at its end)");
    }

    bool HandleKnell(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_baroness_anastari_rework::TestMechanic::Knell, heroic,
            "the Death Knell now (BA2)");
    }

    bool HandleWail(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_baroness_anastari_rework::TestMechanic::Wail, heroic,
            "Wail of the Banshee (BA4; heroic: the echo donut after it)");
    }

    bool HandleVisage(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_baroness_anastari_rework::TestMechanic::Visage, heroic,
            "Horrifying Visage (BA6; heroic: two cones)");
    }

    bool HandleLament(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_baroness_anastari_rework::TestMechanic::Lament, heroic,
            "Lament for the Living (BA7)");
    }

    // `.dbtest strat baroness echo <n>`: n Death's Echo stacks on the selected player (yourself when none).
    bool HandleEcho(ChatHandler* handler, uint32 stacks)
    {
        boss_baroness_anastari_rework* ai = FindBaronessAI(handler);
        if (!ai)
            return false;
        Player* player = handler->getSelectedPlayerOrSelf();
        if (!player)
            return false;
        uint32 const now = ai->TestEcho(player, stacks);
        handler->PSendSysMessage("The Baroness: {} now has {} stack(s) of Death's Echo.", player->GetName(), now);
        return true;
    }

    // `.dbtest strat baroness <sub> [1]`: the optional 1 forces the heroic form (0 forces normal); default: the map's.
    ChatCommandTable const& BaronessTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",   HandleInfo,   SEC_GAMEMASTER, Console::No },
            { "state",  HandleState,  SEC_GAMEMASTER, Console::No },
            { "keen",   HandleKeen,   SEC_GAMEMASTER, Console::No },
            { "knell",  HandleKnell,  SEC_GAMEMASTER, Console::No },
            { "wail",   HandleWail,   SEC_GAMEMASTER, Console::No },
            { "visage", HandleVisage, SEC_GAMEMASTER, Console::No },
            { "lament", HandleLament, SEC_GAMEMASTER, Console::No },
            { "echo",   HandleEcho,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_baroness_anastari_rework()
{
    RegisterDungeonReworkCreatureAI(boss_baroness_anastari_rework, StratholmeRework::kInstanceScriptName);
    StratTest::RegisterBoss("baroness", BaronessTestCommands());
}
