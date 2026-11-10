/*
 * mod-dungeon-bosses, Stratholme S9: Magistrate Barthilas (10435), "The Epidemic": the man who watched his city sicken,
 * and caught it. Build spec ST 2355-2407 (docs/dungeons/stratholme-rework.md), handoff section 3.4 rows BT and 3.5 row
 * S9. Replaces stock SmartAI 10435 (Furious Anger 16791 becomes Fever, Crowd Pummel 10887 leaves his kit, his run to
 * the Slaughterhouse is gone; WP-S9's SQL rev drops the rows and the Service Entrance Gate's gossip row); bound by
 * apps/dbc-tools source/npcs/stratholme/magistrate_barthilas.py. Pure rules: BarthilasLogic.h.
 *
 *   BT1  Infection     8 s, then every 15 s: emote line 1, he coughs on a random player, the tank included (heroic:
 *                      two). Infected (206605, Disease) for 10 s: 4% of the reference row every 2 s (the kit's
 *                      spell_dungeon_refflat_periodic) and a green cloud. A dispel ends it with no cough (the reward)
 *   BT2  Contagion     a healthy player within 5 yd of a carrier for 1 s (heroic 0.5 s) catches a fresh one: Fever
 *                      +1. Bots: a rolling telegraph-only RunOut (5 yd) on every carrier (SelfTrigger), and X1's route
 *                      avoidance walks them around carriers on their way into a ward
 *   BT3  The cough     each infection registers an 8 yd RunOut on its carrier that lands as it ends: 30% / 40% Nature
 *                      + Weakened to everyone else inside (206606), Fever +1 per player hit. The carrier then
 *                      Recovers (206608): 10 s immune to catching it. A dispel, a Sick Ward cure or a death cancels it
 *   BT4  Plagued Grain 12 s, then every 20 s: a sack (206609) at a random player's spot, a 2 s 6 yd marker, 30% Nature
 *                      + Weakened (206610); yell line 4 on the 1st, 4th, 7th ... throw
 *   BT5  Grain pile    where it landed: a 5 yd pile for 30 s (heroic 45 s), at most 2 (heroic 3), the oldest
 *                      dries up; standing in it 0.5 s catches Infection (Fever +1). A stalker (300580) carries the
 *                      fog (206611); the kit's PuddleField owns the union and the markers
 *   BT6  Quarantine    25 s, then every 30 s: yell line 2, a Sick Ward (green Stack, carriers) and a Well Ward
 *                      (yellow Stack, the healthy), 6 yd (heroic 5 yd), on a line through him picked from the floor
 *                      (never on a pile), centers 9 yd (8 yd) from him so the edges are 6 yd apart; ward stalkers
 *                      300581 anchor them. 5 s (heroic 4 s) later
 *   BT7  The purge     outside both wards: 40% Nature (206612, the kit's RegistryHit); carriers in the Sick Ward are
 *                      cured; a healthy player in the Sick Ward, or in the Well Ward with a carrier, catches it
 *   BT8  Fever         his stacking buff (206613): +5% (heroic +6%) damage and +3% attack speed a stack, no cap; +1
 *                      every 20 s and for every catch and cough hit above, heroic Bedlam +5. The fight's enrage
 *   BT9  Bedlam (H)    35 s, then every 30 s: yell line 3, a 3 s kickable cast (206614; the interrupt list,
 *                      priority 3). Finished: every player not already sick is Infected at once (their coughs land
 *                      together at 40%) and he gains 5 Fever
 *   BT10 Cough puddle  heroic: every cough leaves a 4 yd puddle for 20 s where it went off; 0.5 s inside catches it
 *   BT11 Stock kit     Mighty Blow 14099 (11 s, every 15 s) and Draining Blow 16793 (4 s, every 12-15 s) on his
 *                      victim, the stock timers; DD scales both on heroic
 *   Look               Transformation 16794 on reset and on death (his living face, as the stock rows did)
 *   Arena              StratholmeRework::LeashOptions on BarthilasArena() (no grips; he holds at the edge). His
 *                      portcullises 175377 / 175372 are the instance's door data on BOSS_BARTHILAS (S0)
 *
 * Every timer runs on the AI's own clock, never on BossAI's scheduler (a cast bar pauses that one). Every firing logs
 * one INFO line "strat barthilas <mechanic> ..." (module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "BarthilasLogic.h"
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
#include "SpellAuraEffects.h"
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
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

using namespace Acore::ChatCommands;
using namespace StratholmeRework;
using namespace StratBarthilas;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;

namespace
{
    char const* const kBossLogName = "barthilas";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    bool CountsAsPlayer(Player const* p)
    {
        return p && p->IsInWorld() && p->IsAlive() && !p->IsGameMaster();
    }

    void LogBt(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, mechanic, detail);
    }
}

struct boss_magistrate_barthilas_rework : public BossAI
{
private:
    struct Ward
    {
        Vec2 p;
        float z = 0.f;
    };

    struct PuddleRec
    {
        uint32 id = 0;
        ObjectGuid stalker;
        bool pile = false;
    };

    struct Sack
    {
        Position spot;
        uint64 launchAtMs = 0;
    };

public:
    explicit boss_magistrate_barthilas_rework(Creature* creature)
        : BossAI(creature, BOSS_BARTHILAS), _arena(BarthilasArena(), LeashOptions(kBossLogName)),
        _field(Ms(kPileTickMs))
    {
    }

    // The AI behind a lambda's captured guid (registry callbacks capture guids only).
    static boss_magistrate_barthilas_rework* From(Map* map, ObjectGuid guid)
    {
        Creature* boss = map ? map->GetCreature(guid) : nullptr;
        if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_magistrate_barthilas_rework*>(boss->AI());
    }

    void Reset() override
    {
        _Reset();
        Cleanup();
        WearLivingFace();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        Cleanup();
        _heroic = DungeonKit::IsHeroicMap(me);
        _engaged = true;
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_BARTHILAS;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        _nextInfectionMs = kInfectionFirstMs;
        _nextGrainMs = kGrainFirstMs;
        _nextQuarantineMs = kQuarantineFirstMs;
        _nextFeverMs = kFeverEveryMs;
        _nextBedlamMs = _heroic ? kBedlamFirstMs : 0;
        _nextMightyBlowMs = kMightyBlowFirstMs;
        _nextDrainingBlowMs = kDrainingBlowFirstMs;
        if (_heroic)
            Mechanic::NoteNextCastIn(me, SPELL_BT_BEDLAM, Ms(kBedlamFirstMs));
        RefreshContagionRunOut();
        Talk(SAY_BARTHILAS_AGGRO);
        LogBt("engage", Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f}) health={}", _heroic ? 1 : 0,
            me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), me->GetMaxHealth()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Talk(YELL_BARTHILAS_DEATH);
        uint32 const fever = DungeonKit::Stacks(me, SPELL_BT_FEVER);
        Cleanup();
        BossAI::JustDied(killer);   // DONE (the portcullises open), the summons despawn, the encounter ends
        WearLivingFace();
        LogBt("death", Acore::StringFormat("fever={} killer={}", fever, killer ? killer->GetName() : "none"));
    }

    // The stalkers never fight: BossAI's zoning would pull them into combat.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    // BT9: Bedlam finished (an interrupted cast never gets here).
    void OnSpellCast(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_BT_BEDLAM && _engaged)
            BedlamLands();
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        // The AI's own clock: nothing below waits for a cast bar.
        _clockMs += diff;
        UpdateContagion(diff);
        _field.Update(me, diff, [this](Player* player, uint32 msInside) { InPile(player, msInside); });
        _runOutMs += diff;
        if (_runOutMs >= kRunOutRefreshMs)
            RefreshContagionRunOut();
        LaunchDueSacks();
        if (_purgeAtMs && _clockMs >= _purgeAtMs)
            Purge();
        if (!me->IsAlive() || !me->IsEngaged())
            return;

        if (_clockMs >= _nextInfectionMs)
        {
            _nextInfectionMs += kInfectionEveryMs;
            CoughOnPatients(kPatients(_heroic));
        }
        if (_clockMs >= _nextGrainMs)
        {
            _nextGrainMs += kGrainEveryMs;
            ThrowGrain(nullptr);
        }
        if (_clockMs >= _nextQuarantineMs)
        {
            _nextQuarantineMs += kQuarantineEveryMs;
            Quarantine();
        }
        if (_clockMs >= _nextFeverMs)
        {
            _nextFeverMs += kFeverEveryMs;
            AddFever(1, "clock");
        }

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (_nextBedlamMs && _clockMs >= _nextBedlamMs)
        {
            _nextBedlamMs += kBedlamEveryMs;
            Bedlam();
            return;
        }
        if (Unit* victim = me->GetVictim(); victim && me->IsWithinMeleeRange(victim))
        {
            if (_clockMs >= _nextMightyBlowMs)
            {
                _nextMightyBlowMs = _clockMs + kMightyBlowEveryMs;
                me->CastSpell(victim, SPELL_MIGHTY_BLOW, false);
            }
            else if (_clockMs >= _nextDrainingBlowMs)
            {
                _nextDrainingBlowMs = _clockMs + urand(kDrainingBlowMinMs, kDrainingBlowMaxMs);
                me->CastSpell(victim, SPELL_DRAINING_BLOW, false);
            }
        }
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BT1 Infection, BT3 the cough
    // ----------------------------------------------------------------------------------------------------------------

    // The players of the fight: alive, not game masters, in combat with him.
    std::vector<Player*> FightPlayers() const
    {
        std::vector<Player*> players;
        for (auto const& ref : me->GetMap()->GetPlayers())
            if (Player* p = ref.GetSource(); CountsAsPlayer(p) && p->IsInCombatWith(me))
                players.push_back(p);
        return players;
    }

    bool Infected(Unit const* unit) const
    {
        return unit && unit->HasAura(SPELL_BT_INFECTION);
    }

    bool Recovered(Unit const* unit) const
    {
        return unit && unit->HasAura(SPELL_BT_RECOVERED);
    }

    bool CanCatchNow(Player const* p) const
    {
        return CountsAsPlayer(p) && CanCatch(Infected(p), Recovered(p));
    }

    // BT1: he coughs on `count` players (the tank included; never a carrier, a recovering one only when nobody else
    // is left). `forced`: the test command's pick.
    void CoughOnPatients(uint32 count, Player* forced = nullptr)
    {
        std::vector<Player*> picked;
        if (forced)
            picked.push_back(forced);
        else
        {
            std::vector<Player*> const players = FightPlayers();
            std::vector<PatientCandidate> candidates;
            for (Player* p : players)
                candidates.push_back({ p->GetGUID().GetRawValue(), Infected(p), Recovered(p) });
            for (uint64 raw : PickPatients(candidates, count, [](std::size_t n) { return urand(0, uint32(n) - 1); }))
                for (Player* p : players)
                    if (p->GetGUID().GetRawValue() == raw)
                        picked.push_back(p);
        }
        for (Player* p : picked)
        {
            if (!Infect(p, "patient"))
                continue;
            Talk(EMOTE_BARTHILAS_COUGH, p);
        }
        if (picked.empty())
            LogBt("infection", "no patient");
    }

    // A fresh Infection on `player` and its cough (BT3): false when they are already sick or the aura did not take.
    bool Infect(Player* player, char const* source)
    {
        if (!CountsAsPlayer(player) || Infected(player))
            return false;
        player->RemoveAurasDueToSpell(SPELL_BT_RECOVERED);
        if (!me->AddAura(SPELL_BT_INFECTION, player))
            return false;
        _carriers[player->GetGUID()] = RegisterCough(player, Ms(kInfectionMs));
        LogBt("infection", Acore::StringFormat("source={} player={} carriers={}", source, player->GetName(),
            _carriers.size()));
        return true;
    }

    // BT3: the 8 yd RunOut on the carrier, landing as the infection ends; Fever +1 per player it hits.
    MechanicHandle RegisterCough(Player* carrier, Milliseconds warn)
    {
        Map* map = me->GetMap();
        ObjectGuid const bossGuid = me->GetGUID();
        MechanicRef ref = Mechanic::RunOut(me, carrier, kCoughYd, warn);
        ref.Damage(kCoughPct(_heroic)).School(SPELL_SCHOOL_NATURE).Spell(SPELL_BT_COUGH).Weakened()
            .Color(BossMechanics::Color::Green).Tag(TAG_BT_COUGH);
        ref.OnHit([map, bossGuid](Unit* hit)
        {
            if (boss_magistrate_barthilas_rework* ai = From(map, bossGuid); ai && hit && hit->IsPlayer())
                ai->AddFever(1, "cough-hit");
        });
        return ref.Handle();
    }

    // The Infection aura left `target` (spell_st_barthilas_infection). Expired: the cough goes off (its RunOut lands
    // now), the carrier Recovers, and on heroic a puddle stays. Removed any other way (a dispel, a Sick Ward cure, a
    // death, a map change): no cough.
    void InfectionEnded(Unit* target, bool expired)
    {
        if (!target)
            return;
        auto it = _carriers.find(target->GetGUID());
        if (it == _carriers.end())
            return;     // not ours (a cleanup)
        MechanicHandle const cough = it->second;
        _carriers.erase(it);
        if (!expired)
        {
            if (cough)
                Mechanic::Cancel(me, cough);
            LogBt("infection-ended", Acore::StringFormat("player={} cough=0", target->GetName()));
            return;
        }
        if (!target->IsAlive())
            return;
        target->CastSpell(target, SPELL_BT_COUGHING, true);
        me->AddAura(SPELL_BT_RECOVERED, target);
        if (_heroic)
            AddPuddle(target->GetPosition(), false);
        LogBt("cough", Acore::StringFormat("player={} heroicPuddle={}", target->GetName(), _heroic ? 1 : 0));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BT2 Contagion
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateContagion(uint32 diff)
    {
        _contagionPollMs += diff;
        if (_contagionPollMs < kContagionPollMs)
            return;
        uint32 const elapsed = _contagionPollMs;
        _contagionPollMs = 0;

        std::vector<Player*> carriers;
        std::vector<Player*> healthy;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* p = ref.GetSource();
            if (!CountsAsPlayer(p))
                continue;
            if (Infected(p))
                carriers.push_back(p);
            else if (!Recovered(p))
                healthy.push_back(p);
        }
        std::vector<uint64> near;
        for (Player* p : healthy)
            for (Player* c : carriers)
                if (p->GetExactDist2d(c) <= kContagionYd
                    && std::fabs(p->GetPositionZ() - c->GetPositionZ()) <= kContagionZYd)
                {
                    near.push_back(p->GetGUID().GetRawValue());
                    break;
                }
        for (uint64 raw : Catches(_contagion.Update(near, elapsed), kContagionHoldMs(_heroic)))
            for (Player* p : healthy)
                if (p->GetGUID().GetRawValue() == raw && Infect(p, "contagion"))
                    AddFever(1, "contagion");
    }

    // The bots' 5 yd RunOut on every carrier, re-registered before it resolves (the Ras pattern). No telegraph: the
    // humans read the green cloud and the cough's 8 yd circle.
    void RefreshContagionRunOut()
    {
        _runOutMs = 0;
        if (_contagionRunOut)
            Mechanic::Cancel(me, _contagionRunOut);
        MechanicRef ref = Mechanic::RunOut(me, nullptr, kContagionYd, Ms(kRunOutWarnMs));
        ref.SelfTrigger(SPELL_BT_INFECTION, 1).NoTelegraph().Tag(TAG_BT_CONTAGION);
        _contagionRunOut = ref.Handle();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BT4 Plagued Grain, BT5 the pile, BT10 the cough puddle
    // ----------------------------------------------------------------------------------------------------------------

    void ThrowGrain(Player* forced)
    {
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = false;
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!target)
        {
            LogBt("grain", "no target");
            return;
        }
        Position const spot = target->GetPosition();
        ++_throws;
        if (GrainYells(_throws))
            Talk(YELL_BARTHILAS_GRAIN);
        Map* map = me->GetMap();
        ObjectGuid const bossGuid = me->GetGUID();
        MechanicRef ref = Mechanic::Circle(me, spot, kGrainYd, Ms(kGrainWarnMs));
        ref.Damage(kGrainPct).School(SPELL_SCHOOL_NATURE).Spell(SPELL_BT_GRAIN_IMPACT).Weakened()
            .Color(BossMechanics::Color::Green).Tag(TAG_BT_GRAIN);
        ref.OnResolve([map, bossGuid, spot](BossMechanics::ResolveResult const& r)
        {
            if (boss_magistrate_barthilas_rework* ai = From(map, bossGuid))
                ai->AddPuddle(spot, true, uint32(r.hits.size()));
        });
        _sacks.push_back({ spot, _clockMs + SackLaunchDelayMs(me->GetExactDist2d(&spot)) });
        LogBt("grain", Acore::StringFormat("throw={} target={} at=({:.1f}, {:.1f})", _throws, target->GetName(),
            spot.GetPositionX(), spot.GetPositionY()));
    }

    // The sack leaves so it lands as the marker resolves (look only: the registry circle owns the hit).
    void LaunchDueSacks()
    {
        for (auto it = _sacks.begin(); it != _sacks.end();)
        {
            if (_clockMs < it->launchAtMs)
            {
                ++it;
                continue;
            }
            me->CastSpell(it->spot.GetPositionX(), it->spot.GetPositionY(), it->spot.GetPositionZ(),
                SPELL_BT_GRAIN_THROW, true);
            it = _sacks.erase(it);
        }
    }

    // A grain pile (BT5: `pile`, capped, the oldest dries up) or a cough puddle (BT10) at `at`, with its fog stalker.
    void AddPuddle(Position const& at, bool pile, uint32 grainHits = 0)
    {
        if (!_engaged)
            return;
        // Forget the ones the field already dried up.
        _puddles.erase(std::remove_if(_puddles.begin(), _puddles.end(),
            [this](PuddleRec const& p) { return !_field.Find(p.id); }), _puddles.end());
        if (pile)
        {
            uint32 live = 0;
            for (PuddleRec const& p : _puddles)
                live += p.pile ? 1 : 0;
            for (uint32 drop = PilesToDrop(live, kPileCap(_heroic)); drop; --drop)
            {
                auto oldest = std::find_if(_puddles.begin(), _puddles.end(), [](PuddleRec const& p) { return p.pile; });
                if (oldest == _puddles.end())
                    break;
                DropPuddle(*oldest);
                _puddles.erase(oldest);
            }
        }
        uint32 const lifeMs = pile ? kPileLifeMs(_heroic) : kPuddleLifeMs;
        DungeonKit::PuddleSpec spec;
        spec.radius = pile ? kPileYd : kPuddleYd;
        spec.armAfter = Ms(250);
        spec.life = Ms(lifeMs);
        spec.color = BossMechanics::Color::Green;
        spec.tag = pile ? TAG_BT_PILE : TAG_BT_PUDDLE;
        DungeonKit::PuddleSet::AddResult const added = _field.Add(me, at, spec);
        if (!added.id)
            return;
        PuddleRec rec;
        rec.id = added.id;
        rec.pile = pile;
        if (TempSummon* fog = me->SummonCreature(NPC_ST_GRAIN_PILE, at, TEMPSUMMON_TIMED_DESPAWN, lifeMs))
        {
            fog->CastSpell(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), SPELL_BT_PLAGUE_FOG, true);
            rec.stalker = fog->GetGUID();
        }
        _puddles.push_back(rec);
        LogBt(pile ? "grain-pile" : "cough-puddle", Acore::StringFormat("at=({:.1f}, {:.1f}) grainHits={} live={}",
            at.GetPositionX(), at.GetPositionY(), grainHits, _puddles.size()));
    }

    void DropPuddle(PuddleRec const& rec)
    {
        _field.Remove(me, rec.id);
        if (Creature* fog = ObjectAccessor::GetCreature(*me, rec.stalker))
            fog->DespawnOrUnsummon();
    }

    // BT5 / BT10: a player in the union of piles and puddles for 0.5 s catches Infection (once per tick, however
    // many overlap).
    void InPile(Player* player, uint32 msInside)
    {
        if (msInside < kPileGraceMs || !CanCatchNow(player))
            return;
        if (Infect(player, "pile"))
            AddFever(1, "pile");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BT6 Quarantine, BT7 the purge
    // ----------------------------------------------------------------------------------------------------------------

    void Quarantine()
    {
        if (_purgeAtMs)
            return;     // the last one has not closed (the test command)
        float const r = kWardYd(_heroic);
        std::vector<DungeonKit::AvoidCircle> piles;
        for (DungeonKit::Puddle const& p : _field.All())
            piles.push_back({ p.center, p.radius });
        Vec2 const boss = DungeonKit::PlaneOf(me);
        float const bossZ = me->GetPositionZ();
        Arena const arena = BarthilasArena();
        auto floorAt = [this, bossZ, &arena](Vec2 p) -> std::optional<float>
        {
            float const z = me->GetMapHeight(p.x, p.y, bossZ + 3.f);
            if (z <= INVALID_HEIGHT + 1.f || std::fabs(z - bossZ) > kWardFloorZBand || !arena.Contains(p, z))
                return std::nullopt;
            return z;
        };
        std::optional<WardLine> const line = PickWardLine(boss, r, piles, frand(0.f, DungeonKit::kPi), floorAt);
        if (!line)
            return;
        bool const sickFirst = urand(0, 1) == 0;
        _sick = { sickFirst ? line->a : line->b, sickFirst ? line->za : line->zb };
        _well = { sickFirst ? line->b : line->a, sickFirst ? line->zb : line->za };
        for (Ward* w : { &_sick, &_well })
            if (w->z == 0.f)
                w->z = bossZ;       // a center with no floor (best effort): his height
        _wardYd = r;
        uint32 const warn = kQuarantineWarnMs(_heroic);
        _purgeAtMs = _clockMs + warn;

        BossMechanics::Eligibility sick;
        sick.auraSpell = SPELL_BT_INFECTION;
        sick.minStacks = 1;
        BossMechanics::Eligibility well;
        well.auraSpell = SPELL_BT_INFECTION;
        well.maxStacks = 0;
        _sickHandle = RegisterWard(_sick, sick, BossMechanics::Color::Green, TAG_BT_WARD_SICK, warn);
        _wellHandle = RegisterWard(_well, well, BossMechanics::Color::Yellow, TAG_BT_WARD_WELL, warn);
        Talk(YELL_BARTHILAS_QUARANTINE);
        LogBt("quarantine", Acore::StringFormat("sick=({:.1f}, {:.1f}) well=({:.1f}, {:.1f}) r={} warn={} full={} "
            "floorMisses={} pileHits={}", _sick.p.x, _sick.p.y, _well.p.x, _well.p.y, r, warn, line->full ? 1 : 0,
            line->floorMisses, line->pileHits));
    }

    // A telegraph-only Stack on a ward stalker (the point when the stalker cannot be summoned): it draws the disc and
    // sends the eligible bots in; the purge is the script's.
    MechanicHandle RegisterWard(Ward const& w, BossMechanics::Eligibility const& who, BossMechanics::Color color,
        uint32 tag, uint32 warnMs)
    {
        Position const at = DungeonKit::ToPosition(w.p, w.z);
        TempSummon* stalker = me->SummonCreature(NPC_ST_WARD, at, TEMPSUMMON_TIMED_DESPAWN, warnMs + 1000);
        if (stalker)
            _wardStalkers.push_back(stalker->GetGUID());
        MechanicRef ref = stalker ? Mechanic::Stack(me, stalker, _wardYd, Ms(warnMs))
            : Mechanic::Stack(me, at, _wardYd, Ms(warnMs));
        ref.Eligible(who).Color(color).Tag(tag);
        return ref.Handle();
    }

    void Purge()
    {
        _purgeAtMs = 0;
        struct Subject
        {
            Player* player;
            PurgeSubject s;
        };
        std::vector<Subject> subjects;
        bool carrierInWell = false;
        for (Player* p : FightPlayers())
        {
            Vec2 const at = DungeonKit::PlaneOf(p);
            PurgeSubject s;
            s.infected = Infected(p);
            s.recovered = Recovered(p);
            s.inSick = InWard(at, p->GetPositionZ(), _sick.p, _sick.z, _wardYd);
            s.inWell = !s.inSick && InWard(at, p->GetPositionZ(), _well.p, _well.z, _wardYd);
            carrierInWell = carrierInWell || (s.infected && s.inWell);
            subjects.push_back({ p, s });
        }
        GuidSet hits;
        uint32 cured = 0;
        uint32 caught = 0;
        std::vector<Player*> catchers;
        for (Subject const& sub : subjects)
            switch (PurgeFor(sub.s, carrierInWell))
            {
                case PurgeFate::Hit:
                    hits.insert(sub.player->GetGUID());
                    break;
                case PurgeFate::Cured:
                    sub.player->RemoveAurasDueToSpell(SPELL_BT_INFECTION);     // no cough (InfectionEnded)
                    ++cured;
                    break;
                case PurgeFate::Caught:
                    catchers.push_back(sub.player);
                    break;
                case PurgeFate::Safe:
                    break;
            }
        for (Player* p : catchers)
            if (Infect(p, "ward"))
            {
                ++caught;
                AddFever(1, "ward");
            }
        if (!hits.empty())
        {
            DungeonKit::RegistryHitSpec spec;
            spec.pct = kPurgePct;
            spec.school = SPELL_SCHOOL_NATURE;
            spec.spellId = SPELL_BT_PURGE;
            spec.weakened = false;
            spec.tag = TAG_BT_PURGE;
            DungeonKit::RegistryHit(me, hits, spec);
        }
        EndWards();
        LogBt("purge", Acore::StringFormat("players={} outside={} cured={} caught={} carrierInWell={}",
            subjects.size(), hits.size(), cured, caught, carrierInWell ? 1 : 0));
    }

    void EndWards()
    {
        for (MechanicHandle* h : { &_sickHandle, &_wellHandle })
            if (*h)
            {
                Mechanic::Cancel(me, *h);
                *h = {};
            }
        for (ObjectGuid const& guid : _wardStalkers)
            if (Creature* stalker = ObjectAccessor::GetCreature(*me, guid))
                stalker->DespawnOrUnsummon();
        _wardStalkers.clear();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BT8 Fever, BT9 Bedlam
    // ----------------------------------------------------------------------------------------------------------------

    void AddFever(uint32 stacks, char const* why)
    {
        if (!stacks || !_engaged)
            return;
        uint32 const now = DungeonKit::AddStacks(me, SPELL_BT_FEVER, int32(stacks), me);
        LogBt("fever", Acore::StringFormat("why={} +{} stacks={}", why, stacks, now));
    }

    void Bedlam()
    {
        Talk(YELL_BARTHILAS_BEDLAM);
        SpellCastResult const result = me->CastSpell(me, SPELL_BT_BEDLAM, false);
        Mechanic::NoteNextCastIn(me, SPELL_BT_BEDLAM, Ms(kBedlamEveryMs));
        LogBt("bedlam-cast", Acore::StringFormat("result={}", uint32(result)));
    }

    void BedlamLands()
    {
        uint32 infected = 0;
        for (Player* p : FightPlayers())
            infected += Infect(p, "bedlam") ? 1 : 0;
        AddFever(kBedlamFever, "bedlam");
        LogBt("bedlam", Acore::StringFormat("infected={}", infected));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (ST): dispel BT1 (Disease, optional: priority 1); interrupt BT9 (heroic, expected: priority 3, every
    // 30 s); kill order him.
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        BossMechanics::Descriptor d;
        d.dispels.emplace_back(SPELL_BT_INFECTION, 1);
        if (_heroic)
            d.interrupts.emplace_back(NPC_BARTHILAS, SPELL_BT_BEDLAM, kBedlamKickPriority, Ms(kBedlamEveryMs));
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest strat barthilas` entry points
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Infect,
        Cough,
        Grain,
        Quarantine,
        Bedlam,
    };

    std::string TestFire(TestMechanic mechanic, Player* target)
    {
        if (!_engaged || !me->IsEngaged())
            return "Barthilas must be in combat (the infections, piles and wards belong to the fight).";
        switch (mechanic)
        {
            case TestMechanic::Infect:
                if (target)
                    CoughOnPatients(1, target);
                else
                    CoughOnPatients(kPatients(_heroic));
                break;
            case TestMechanic::Cough:
            {
                if (!target)
                    return "Select a carrier.";
                Aura* aura = target->GetAura(SPELL_BT_INFECTION, me->GetGUID());
                auto it = _carriers.find(target->GetGUID());
                if (!aura || it == _carriers.end())
                    return "The selected player is not Infected.";
                // The cough in 1.5 s: the aura and its RunOut both shortened.
                aura->SetDuration(1500);
                if (it->second)
                    Mechanic::Cancel(me, it->second);
                it->second = RegisterCough(target, Ms(1500));
                break;
            }
            case TestMechanic::Grain:
                ThrowGrain(target);
                break;
            case TestMechanic::Quarantine:
                if (_purgeAtMs)
                    return "A Quarantine is already up.";
                Quarantine();
                break;
            case TestMechanic::Bedlam:
                if (me->HasUnitState(UNIT_STATE_CASTING))
                    return "Barthilas is casting.";
                Bedlam();
                break;
        }
        return {};
    }

    std::string TestFever(uint32 stacks)
    {
        if (!_engaged)
            return "Barthilas must be in combat.";
        int32 const delta = int32(stacks) - int32(DungeonKit::Stacks(me, SPELL_BT_FEVER, me->GetGUID()));
        DungeonKit::AddStacks(me, SPELL_BT_FEVER, delta, me);
        LogBt("fever", Acore::StringFormat("why=test stacks={}", stacks));
        return {};
    }

    std::string TestState() const
    {
        uint32 piles = 0;
        for (PuddleRec const& p : _puddles)
            piles += p.pile ? 1 : 0;
        return Acore::StringFormat("heroic={} clock={}s carriers={} piles={}/{} puddles={} fever={} throws={} "
            "nextInfection={}s nextGrain={}s nextQuarantine={}s nextBedlam={}s wards={}", _heroic ? 1 : 0,
            _clockMs / 1000, _carriers.size(), piles, kPileCap(_heroic), _puddles.size() - piles,
            DungeonKit::Stacks(me, SPELL_BT_FEVER), _throws, _nextInfectionMs / 1000, _nextGrainMs / 1000,
            _nextQuarantineMs / 1000, _nextBedlamMs / 1000, _purgeAtMs ? "up" : "none");
    }

private:
    // Transformation 16794: his living face (Magistrate Burnside's display), on reset and on death, as the stock rows.
    void WearLivingFace()
    {
        if (!me->HasAura(SPELL_TRANSFORMATION))
            me->CastSpell(me, SPELL_TRANSFORMATION, true);
    }

    // The pull's state: nothing pending, no infections, piles, wards or Fever (Reset, evade, death, a new pull).
    void Cleanup()
    {
        _engaged = false;
        EndWards();
        if (_contagionRunOut)
            Mechanic::Cancel(me, _contagionRunOut);
        _contagionRunOut = {};
        for (auto const& [guid, cough] : _carriers)
            if (cough)
                Mechanic::Cancel(me, cough);
        _carriers.clear();      // before the auras go: InfectionEnded then finds nothing to do
        for (PuddleRec const& rec : _puddles)
            if (Creature* fog = ObjectAccessor::GetCreature(*me, rec.stalker))
                fog->DespawnOrUnsummon();
        _puddles.clear();
        _field.Clear(me);
        for (auto const& ref : me->GetMap()->GetPlayers())
            if (Player* p = ref.GetSource())
            {
                p->RemoveAurasDueToSpell(SPELL_BT_INFECTION, me->GetGUID());
                p->RemoveAurasDueToSpell(SPELL_BT_RECOVERED, me->GetGUID());
            }
        me->RemoveAurasDueToSpell(SPELL_BT_FEVER);
        _contagion.Clear();
        _sacks.clear();
        _clockMs = 0;
        _contagionPollMs = 0;
        _runOutMs = 0;
        _purgeAtMs = 0;
        _throws = 0;
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::PuddleField _field;
    DungeonKit::InsideClock _contagion;
    std::unordered_map<ObjectGuid, MechanicHandle> _carriers;   // carrier -> their cough (BT3)
    std::vector<PuddleRec> _puddles;
    std::vector<Sack> _sacks;
    std::vector<ObjectGuid> _wardStalkers;
    MechanicHandle _contagionRunOut;
    MechanicHandle _sickHandle;
    MechanicHandle _wellHandle;
    Ward _sick;
    Ward _well;
    float _wardYd = 6.f;
    bool _heroic = false;
    bool _engaged = false;
    uint64 _clockMs = 0;                // ms since the pull: every timer of the fight
    uint64 _nextInfectionMs = 0;
    uint64 _nextGrainMs = 0;
    uint64 _nextQuarantineMs = 0;
    uint64 _nextFeverMs = 0;
    uint64 _nextBedlamMs = 0;           // 0: none (normal)
    uint64 _nextMightyBlowMs = 0;
    uint64 _nextDrainingBlowMs = 0;
    uint64 _purgeAtMs = 0;              // 0: no Quarantine up
    uint32 _contagionPollMs = 0;
    uint32 _runOutMs = 0;
    uint32 _throws = 0;
};

// BT1 206605 Infection: the cough on expiry, nothing on any other removal (a dispel, a Sick Ward cure, a death, a map
// change). The periodic damage is the kit's spell_dungeon_refflat_periodic (bound beside this one).
class spell_st_barthilas_infection : public AuraScript
{
    PrepareAuraScript(spell_st_barthilas_infection);

    void AfterRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* caster = GetCaster();
        Creature* boss = caster ? caster->ToCreature() : nullptr;
        if (!boss || !boss->IsAIEnabled)
            return;
        auto* ai = dynamic_cast<boss_magistrate_barthilas_rework*>(boss->AI());
        if (!ai)
            return;
        AuraApplication const* app = GetTargetApplication();
        ai->InfectionEnded(GetTarget(), app && app->GetRemoveMode() == AURA_REMOVE_BY_EXPIRE);
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_st_barthilas_infection::AfterRemove, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE, AURA_EFFECT_HANDLE_REAL);
    }
};

// BT8 206613 Fever: +5% damage a stack on normal (the spell value), +6% on heroic (the aura multiplies by the stacks).
class spell_st_barthilas_fever : public AuraScript
{
    PrepareAuraScript(spell_st_barthilas_fever);

    void CalcAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        amount = static_cast<int32>(kFeverDamagePct(DungeonKit::IsHeroicMap(GetUnitOwner())));
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_st_barthilas_fever::CalcAmount, EFFECT_0,
            SPELL_AURA_MOD_DAMAGE_PERCENT_DONE);
    }
};

namespace
{
    boss_magistrate_barthilas_rework* FindBarthilasAI(ChatHandler* handler)
    {
        Creature* boss = StratTest::FindBoss(handler, NPC_BARTHILAS);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_magistrate_barthilas_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}",
                "Magistrate Barthilas is not running boss_magistrate_barthilas_rework (check the ScriptName).");
        return ai;
    }

    Player* SelectedPlayer(ChatHandler* handler)
    {
        Player* p = handler->getSelectedPlayer();
        return p && p->IsAlive() ? p : nullptr;
    }

    bool Fire(ChatHandler* handler, boss_magistrate_barthilas_rework::TestMechanic mechanic, Player* target,
        char const* what)
    {
        boss_magistrate_barthilas_rework* ai = FindBarthilasAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestFire(mechanic, target);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Magistrate Barthilas: {} fired.", what);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return StratTest::ShowBossInfo(handler, NPC_BARTHILAS, BOSS_BARTHILAS);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_magistrate_barthilas_rework* ai = FindBarthilasAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Magistrate Barthilas: {}", ai->TestState());
        return true;
    }

    // `.dbtest strat barthilas infect`: the selected player (else his usual 1 / 2 random patients) is Infected (BT1).
    bool HandleInfect(ChatHandler* handler)
    {
        return Fire(handler, boss_magistrate_barthilas_rework::TestMechanic::Infect, SelectedPlayer(handler),
            "Infection (BT1, its cough BT3 in 10 s)");
    }

    // `.dbtest strat barthilas cough`: the selected carrier coughs in 1.5 s (BT3; heroic: its puddle BT10).
    bool HandleCough(ChatHandler* handler)
    {
        return Fire(handler, boss_magistrate_barthilas_rework::TestMechanic::Cough, SelectedPlayer(handler),
            "the cough in 1.5 s (BT3)");
    }

    // `.dbtest strat barthilas grain`: Plagued Grain on the selected player (else a random one), then its pile.
    bool HandleGrain(ChatHandler* handler)
    {
        return Fire(handler, boss_magistrate_barthilas_rework::TestMechanic::Grain, SelectedPlayer(handler),
            "Plagued Grain (BT4, then the pile BT5)");
    }

    bool HandleQuarantine(ChatHandler* handler)
    {
        return Fire(handler, boss_magistrate_barthilas_rework::TestMechanic::Quarantine, nullptr,
            "Quarantine (BT6, the purge BT7 at its end)");
    }

    bool HandleBedlam(ChatHandler* handler)
    {
        return Fire(handler, boss_magistrate_barthilas_rework::TestMechanic::Bedlam, nullptr,
            "Bedlam (BT9: a 3 s kickable cast)");
    }

    // `.dbtest strat barthilas fever <n>`: his Fever set to n stacks (BT8).
    bool HandleFever(ChatHandler* handler, uint32 stacks)
    {
        boss_magistrate_barthilas_rework* ai = FindBarthilasAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestFever(stacks);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Magistrate Barthilas: Fever set to {} stacks.", stacks);
        return true;
    }

    ChatCommandTable const& BarthilasTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,       SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,      SEC_GAMEMASTER, Console::No },
            { "infect",     HandleInfect,     SEC_GAMEMASTER, Console::No },
            { "cough",      HandleCough,      SEC_GAMEMASTER, Console::No },
            { "grain",      HandleGrain,      SEC_GAMEMASTER, Console::No },
            { "quarantine", HandleQuarantine, SEC_GAMEMASTER, Console::No },
            { "bedlam",     HandleBedlam,     SEC_GAMEMASTER, Console::No },
            { "fever",      HandleFever,      SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_magistrate_barthilas_rework()
{
    RegisterDungeonReworkCreatureAI(boss_magistrate_barthilas_rework, StratholmeRework::kInstanceScriptName);
    RegisterSpellScript(spell_st_barthilas_infection);
    RegisterSpellScript(spell_st_barthilas_fever);
    StratTest::RegisterBoss("barthilas", BarthilasTestCommands());
}
