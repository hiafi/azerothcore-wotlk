/*
 * mod-dungeon-bosses, Zul'Farrak D7Ha: the crew at the pool, the main half of the hard mode "The Crew at the Pool"
 * (heroic only, armed by Bly's Test with all five crew at the pool; the instance arms the flag at the gong, sets the
 * loot bit and the kill slot 8). Build spec: docs/dungeons/zul-farrak-rework.md "Hard mode: the crew at the pool"
 * (GZ15-GZ21, rulings 41-43); handoff sections 3.5 row D7Ha, 3.7, 3.8, 3.9 rows 9 and 13, 7 #16, #17, #39, #43, #58
 * and 10. Pure rules and every number: GahzrillaCrewHardModeLogic.h. A package of D7's pool encounter (PoolFight.h,
 * PoolPackage::Crew, made at Velratha's pull on the hard mode's key or flag, before D7Hb's Deluge) and a PoolAlly
 * handler on CR's crew (BlyCrew.h): it never edits D7's, D7Hb's or CR's files and moves, damages, heals and kills the
 * crew only through BlyCrew.h (rule 28). The crew's damage and healing at the pool are script (rule 29).
 *
 *   The crew's rules    GZ21: the five fight from the pull: Bly and Raven in melee of the boss in play (Velratha, then
 *                       Gahz'rilla once ashore), Oro, Murta and Weegli 20 yd out, fanned toward the group; their hits
 *                       are small script hits (about 15% of the group's, never the killing blow). They take every
 *                       Discharge as players do, as a percent of their own health (40% plus 10% a Charged stack;
 *                       in water a 2 s stun), gain Charged a second in unfrozen water, carry Conductive, and step out
 *                       of water to the nearest dry ground or ice 2 s late. Murta casts Greater Heal on the member
 *                       lowest on health. Human healers heal them (CR's CAN_ASSIST, section 7 #17 A): a player's heal
 *                       fills the share of them it would of a player (their hits are percents too). A member who
 *                       dies stays dead for the attempt (the instance; a pool wipe brings all five back, 7 #16 A):
 *                       Gahz'rilla heals 5% and emotes line 2, and its answer falls back on the group
 *   GZ15 Wellspring     20 s, then every 40 s, phases 1 and 2: a spring (301031, 40,000 health on heroic) bursts at a
 *                       random shore point at least 15 yd from every player, with a 6 yd puddle that cannot freeze and
 *                       grows 2 yd every 5 s. Weegli dead: the spring tops the bots' kill order
 *   GZ16 Blasting Charge Weegli runs to the newest spring (water on his path costs him Charged), plants for 5 s (a stun
 *                       starts it over), yells line 4 and steps away: a 3 s fuse, then 60% Fire to the players within
 *                       10 yd (registry Circle, tag 40); the spring and its puddle are gone
 *   GZ17 Storm's Chosen 15 s, then every 30 s: a random player, the tank included, is marked for 4 s (Bly yells
 *                       line 5); then a bolt for 150% Nature. The marked player within 5 yd of Bly (dry, not
 *                       stunned): Bly takes it (2 Charged). Bly dead: the bolt splits among the players within 5 yd of
 *                       the mark, 1 Charged each. Bots: a Stack on Bly for the marked one (tag 39), on the mark for
 *                       everyone when Bly fell
 *   GZ18 Overcharge     25 s, then every 25 s: a random player, the tank included, Overcharged for 8 s, then 5 Charged
 *                       for good, unless Oro (dry, not stunned) drains it with a 3 s Siphon Charge from within 10 yd
 *                       (1 Charged on Oro). Bots: a Stack on Oro for the carrier (tag 36)
 *   GZ19 Conductive     every Discharge leaves Conductive on everyone (ConductiveOnEveryone: D7 on the players, here on
 *                       the crew, with their arcs); Murta (dry, not stunned) casts Mass Dispel for 2 s after each
 *                       Discharge: Conductive off everyone within 15 yd of her. Bots gather within 13 yd of her from
 *                       the bar to the dispel (a Stack, tag 35) while D7's Conductive Spread keeps them 6 yd apart
 *   GZ20 Twin Call      whenever Gahz'rilla casts Call the Waters, his second head (301032) casts its own 2 s copy;
 *                       Raven (in melee, dry, not stunned) kicks it 0.8 s in. Landed, it lands as his own (D7's
 *                       puddles under three players and the heroic growth). Raven dead: the head joins the bots'
 *                       interrupt list (two kicks at once)
 *   The Deluge          (D7Hb) no more Wellsprings: the ones standing are swallowed, Weegli's job ends. The rest goes
 *                       on; the crew's dry ground is the ice
 *
 * Cleanup (RB-1): OnEnd (his death, a wipe, an evade, or the gong without the flag) cancels the handles, takes the
 * springs, their puddles and the head away, clears the crew's and the players' auras of this package and walks the
 * living crew back to their pool spots. Every firing logs one INFO line "zf-build poolcrew <mechanic> ..."; `.dbtest zf
 * poolcrew <mechanic>` fires one.
 */

#include "BlyCrew.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Containers.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "DungeonKitWater.h"
#include "GahzrillaCrewHardModeLogic.h"
#include "GahzrillaLogic.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "PoolFight.h"
#include "SharedDefines.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "StringFormat.h"
#include "ZulFarrakKit.h"
#include "ZulFarrakRework.h"
#include "ZulFarrakTestCommand.h"
#include <algorithm>
#include <array>
#include <cctype>
#include <cmath>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ZulFarrakRework;
using namespace ZfPoolCrew;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using ZfPool::FreezeKind;
using ZfPool::PoolFight;
using ZfPool::PoolPhase;

class CrewHardMode;

namespace
{
    char const* const kLogKey = "poolcrew";
    float constexpr kFloorBandYd = 6.f;
    float constexpr kShoreZ = 9.5f;

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(static_cast<int64>(ms));
    }

    void LogHm(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kLogKey, mechanic, detail);
    }

    char const* NameOf(uint32 member)
    {
        return member < kCrewCount ? kCrewNames[member] : "?";
    }

    // The floor under (x, y) near `zHint`; the hint where the map has none close to it.
    float FloorZ(WorldObject const* ref, Vec2 p, float zHint)
    {
        if (!ref)
            return zHint;
        float const floor = ref->GetMapHeight(p.x, p.y, zHint + 5.f);
        return (floor > INVALID_HEIGHT + 1.f && std::fabs(floor - zHint) <= kFloorBandYd) ? floor : zHint;
    }

    // The live packages by map, for the crew handler, the add AIs and `.dbtest` (maps update on several threads).
    std::mutex& LiveLock()
    {
        static std::mutex lock;
        return lock;
    }

    std::unordered_map<Map const*, CrewHardMode*>& Live()
    {
        static std::unordered_map<Map const*, CrewHardMode*> live;
        return live;
    }

    uint32 const kCrewAuras[] = { ZfPool::SPELL_GZ_CHARGED, ZfPool::SPELL_GZ_CONDUCTIVE, ZfPool::SPELL_GZ_STATIC_SHOCK,
        SPELL_HM_PLANT_CHARGE, SPELL_HM_SIPHON_CHARGE, SPELL_HM_MASS_DISPEL, SPELL_HM_GREATER_HEAL };
    uint32 const kPlayerAuras[] = { SPELL_HM_STORMS_CHOSEN, SPELL_HM_OVERCHARGE, SPELL_HM_SIPHON_CHARGE };
}

// ---------------------------------------------------------------------------------------------------------------------
// The package (PoolFight.h PoolHardMode), one per pull of the hard mode
// ---------------------------------------------------------------------------------------------------------------------

class CrewHardMode final : public ZfPool::PoolHardMode
{
public:
    explicit CrewHardMode(PoolFight& fight) : _fight(&fight)
    {
        if (Creature* keeper = fight.Keeper())
            _map = keeper->GetMap();
        std::lock_guard<std::mutex> guard(LiveLock());
        Live()[_map] = this;
    }

    ~CrewHardMode() override
    {
        Unlist();
    }

    static CrewHardMode* Find(Map const* map)
    {
        if (!map)
            return nullptr;
        std::lock_guard<std::mutex> guard(LiveLock());
        auto it = Live().find(map);
        return it == Live().end() ? nullptr : it->second;
    }

    // ---- PoolHardMode ---------------------------------------------------------------------------------------------

    void OnEngage(PoolFight& fight) override
    {
        _clock.Start();
        _alive = 0;
        for (uint32 m = 0; m < kCrewCount; ++m)
            if (Creature* c = Crew(m); c && c->IsAlive())
                _alive |= CrewBit(m);
        InstanceScript* instance = fight.Instance();
        LogHm("armed", Acore::StringFormat("crew={} at-pool={} key={} flag={}", _alive,
            instance ? instance->GetData(DATA_CREW_AT_POOL) : 0, instance ? instance->GetData(DATA_HARD_MODE_KEY) : 0,
            instance ? instance->GetData(DATA_HARD_MODE) : 0));
    }

    void OnGongStruck(PoolFight& /*fight*/, bool armed) override
    {
        LogHm(armed ? "gong-armed" : "dropped", armed ? std::string() : "the flag did not arm at the gong");
    }

    void OnGahzrillaArrive(PoolFight& fight) override
    {
        Creature* gahzrilla = fight.Gahzrilla();
        if (!gahzrilla)
            return;
        // GZ20: the second head rides with him from now on (D7's cleanup despawns it).
        if (Creature* head = fight.Summon(NPC_ZF_SECOND_HEAD, gahzrilla->GetPosition()))
        {
            _head = head->GetGUID();
            head->SetFloatValue(UNIT_FIELD_COMBATREACH, gahzrilla->GetCombatReach());
            head->SetFloatValue(UNIT_FIELD_BOUNDINGRADIUS, gahzrilla->GetFloatValue(UNIT_FIELD_BOUNDINGRADIUS));
            head->SetFaction(gahzrilla->GetFaction());
            Mechanic::TrackUnit(gahzrilla, head);
        }
        for (Spring const& s : _springs)
            if (Creature* spring = _map->GetCreature(s.guid))
                Mechanic::TrackUnit(gahzrilla, spring);
        LogHm("head", _head.IsEmpty() ? "refused" : "summoned");
    }

    void OnUpdate(PoolFight& fight, uint32 diff) override
    {
        if (_ended)
            return;
        _clock.Advance(diff);
        if (_pendingDeaths)
            ResolveDeaths(fight);
        CheckDeluge(fight);

        _chargedTick += diff;
        while (_chargedTick >= ZfPool::Tune::kChargedTickMs)
        {
            _chargedTick -= ZfPool::Tune::kChargedTickMs;
            TickCrewCharged(fight);
        }
        _thinkTick += diff;
        if (_thinkTick >= Tune::kCrewThinkMs)
        {
            _thinkTick = 0;
            Think(fight);
        }
        CrewHits(fight);

        for (HmAct act = _clock.Next(); act != HmAct::None; act = _clock.Next())
        {
            // A mark needs a boss to own its hit and its shape: none for a moment (Velratha died before he came
            // ashore), the beat waits for him instead of passing.
            if (!Fire(fight, act, nullptr) && act != HmAct::Wellspring && !Owner(fight))
                _clock.Retry(act);
            else
                _clock.Done(act);
        }

        UpdateSprings(fight);
        UpdateWeegli(fight);
        UpdateChosen(fight);
        UpdateOvercharge(fight);
        UpdateMurta(fight);
        UpdateTwinCall(fight);
        TickConductive(fight);
    }

    // GZ19: D7 puts Conductive on every player at each landing (and this package on the crew).
    bool ConductiveOnEveryone(PoolFight const& /*fight*/) const override { return true; }

    // GZ19: the bots gather on Murta from the bar to her dispel.
    void OnDischargeBar(PoolFight& fight) override
    {
        Creature* murta = Crew(CREW_MURTA);
        Unit* owner = Owner(fight);
        if (!murta || !murta->IsAlive() || !owner)
            return;
        uint64 const hold = ZfPool::Tune::kDischargeCastMs + Tune::kMassDispelCastMs + Tune::kGatherSlackMs;
        MechanicRef ref = Mechanic::Stack(owner, murta, Tune::kGatherStackYd, Ms(hold));
        ref.Within(PoolFloorBounds()).Tag(TAG_HM_GATHER);
        fight.Track(ref.Handle());
    }

    // GZ21 / GZ19: the crew take the landing as players do, on their own health, and carry Conductive; then Murta's
    // Mass Dispel.
    void OnDischargeLand(PoolFight& fight, std::vector<ZfPool::DischargeHit> const& /*players*/) override
    {
        SpellInfo const* hit = sSpellMgr->GetSpellInfo(ZfPool::SPELL_GZ_DISCHARGE);
        std::string detail;
        std::vector<std::pair<ObjectGuid, uint32>> hits;
        for (uint32 m = 0; m < kCrewCount; ++m)
        {
            Creature* c = Crew(m);
            if (!c || !c->IsAlive())
                continue;
            bool const wet = fight.IsWater(c);
            uint32 const charged = fight.Charged(c);
            uint32 const amount = PctOfHealth(c->GetMaxHealth(), CrewDischargePct(charged));
            if (wet)
            {
                _mates[m].stunnedUntil = _clock.Now() + Tune::kCrewStunMs;
                c->AddAura(ZfPool::SPELL_GZ_STATIC_SHOCK, c);   // the look (Bly's 1972 refuses it: the rule holds)
                Interrupted(m, "stun");
            }
            c->AddAura(ZfPool::SPELL_GZ_CONDUCTIVE, c);
            hits.emplace_back(c->GetGUID(), amount);
            detail += Acore::StringFormat("{}{}:{}{}", detail.empty() ? "" : ",", NameOf(m), amount, wet ? "w" : "");
        }
        _arcAt = _clock.Now() + ZfPool::Tune::kConductiveTickMs;
        // The hits last: one may kill (its death is handled on the next tick).
        for (auto const& [guid, amount] : hits)
            if (Creature* c = _map->GetCreature(guid); c && c->IsAlive())
                ZfCrew::DamageCrew(c, nullptr, amount, SPELL_SCHOOL_MASK_NATURE, hit);
        LogHm("crew-discharge", Acore::StringFormat("n={} hits={}", fight.DischargesLanded(),
            detail.empty() ? "-" : detail));
        StartMassDispel(fight, "discharge");
    }

    // GZ23 is D7Hb's (it handles every freeze from the Deluge on).
    bool OnFreeze(PoolFight& /*fight*/, FreezeKind /*kind*/, Unit* /*target*/, Position const& /*at*/,
        DungeonKit::FreezeResult& /*result*/) override
    {
        return false;
    }

    void OnEnd(PoolFight& fight, bool won) override
    {
        if (_ended)
            return;
        _ended = true;
        Creature* keeper = fight.Keeper();
        for (MechanicHandle const& h : _handles)
            if (keeper)
                Mechanic::Cancel(keeper, h);
        _handles.clear();
        // The springs and their puddles go now (at the gong without the flag the encounter runs on, plain heroic).
        for (Spring const& s : _springs)
            RemoveSpring(fight, s);
        _springs.clear();
        RemoveBarrel();
        if (Creature* head = _head.IsEmpty() ? nullptr : _map->GetCreature(_head))
            head->DespawnOrUnsummon();
        _head.Clear();
        InstanceScript* instance = fight.Instance();
        if (instance)
            for (uint32 const spell : kPlayerAuras)
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
        for (uint32 m = 0; m < kCrewCount; ++m)
        {
            ZfCrew::BlyCrewAI* ai = instance ? ZfCrew::CrewAI(instance, m) : nullptr;
            Creature* c = ai ? ai->Me() : nullptr;
            if (!c || !c->IsAlive())
                continue;
            if (c->IsNonMeleeSpellCast(false))
                c->InterruptNonMeleeSpells(false);
            for (uint32 const spell : kCrewAuras)
                c->RemoveAurasDueToSpell(spell);
            if (ai->Mode() == CrewMode::PoolAlly)
                ai->WalkTo(ai->SpotPosition(ZfCrew::CrewSpot::Pool), kPointCrewHome, false);
        }
        _clock.Stop();
        LogHm("end", Acore::StringFormat("won={} crew={} springs={} blasts={} chosen={} bodyguard={} overcharges={} "
            "siphons={} dispels={} twin={} raven-kicks={} devoured={}", won ? 1 : 0, _alive, _counts.springs,
            _counts.blasts, _counts.chosen, _counts.bodyguard, _counts.overcharges, _counts.siphons, _counts.dispels,
            _counts.twin, _counts.ravenKicks, _counts.devoured));
        Unlist();
    }

    void DescribeExtra(PoolFight& /*fight*/, Creature* /*boss*/, BossMechanics::Descriptor& d) override
    {
        // GZ15 fallback: the spring must be killed while Weegli is dead.
        if (!(_alive & CrewBit(CREW_WEEGLI)))
            d.targets.emplace_back(NPC_ZF_WELLSPRING, kWellspringTargetPriority);
        // GZ20 fallback: two player kicks at once while Raven is dead.
        if (!(_alive & CrewBit(CREW_RAVEN)))
            d.interrupts.emplace_back(NPC_ZF_SECOND_HEAD, SPELL_HM_TWIN_CALL, kTwinCallKickPriority,
                Ms(ZfPool::Tune::kCallEveryMs.heroic));
        // F-1 MI-3: the head takes no damage, so no bot targets it or counts it for AoE while Raven stands and takes
        // its cast. The condition reads Raven live (this descriptor is rebuilt only on the next tick after her death)
        // and the ignore ends with her: BM's interrupt pass skips ignored units, and the kick fallback above needs it.
        else
            d.ignores.push_back(BossMechanics::IgnoreEntry(NPC_ZF_SECOND_HEAD,
                BossMechanics::Condition::Custom([](Unit const* head)
                {
                    InstanceScript* instance = head ? head->GetInstanceScript() : nullptr;
                    Creature const* raven = instance ? CrewCreature(instance, CREW_RAVEN) : nullptr;
                    return raven && raven->IsAlive();
                })));
    }

    // ---- From the crew handler and the add AIs ---------------------------------------------------------------------

    // A crew member died (CR's JustDied, inside a damage call: handled on the next tick).
    void NoteDeath(uint32 member)
    {
        if (member < kCrewCount && (_alive & CrewBit(member)))
            _pendingDeaths |= CrewBit(member);
    }

    // A heal on a crew member from a player (or a player's pet or totem): scaled to the member's health (Murta's own
    // heals are percent already and never pass here as a player's).
    uint32 ScalePlayerHeal(Creature* crew, Unit* healer, uint32 heal)
    {
        if (_ended || !crew || !healer || !healer->GetCharmerOrOwnerPlayerOrPlayerItself())
            return heal;
        Unit* owner = Owner(*_fight);
        uint32 const row = owner ? DungeonKit::RefFlat(owner, 100.f) : 0;
        return ScaledCrewHeal(heal, crew->GetMaxHealth(), row);
    }

    void NoteWeegliArrived()
    {
        if (_weegli == WeegliStep::Running)
            _weegliArrived = true;
    }

    // A spring killed by the group (Weegli dead, or faster than him).
    void SpringDied(ObjectGuid guid)
    {
        for (auto it = _springs.begin(); it != _springs.end(); ++it)
        {
            if (it->guid != guid)
                continue;
            RemoveSpring(*_fight, *it);
            LogHm("wellspring-killed", Acore::StringFormat("sheet={} left={}", it->sheet, _springs.size() - 1));
            if (_jobSpring == guid)
                EndWeegliJob("spring-killed");
            _springs.erase(it);
            return;
        }
    }

    // GZ20: the second head's cast landed (or was stopped).
    void HeadCall(Creature* head, bool landed)
    {
        if (_ended)
            return;
        _headCasting = false;
        if (landed)
        {
            ++_counts.twin;
            _fight->LandCallTheWaters(head, "twin-call");
        }
        LogHm(landed ? "twin-call-land" : "twin-call-stopped");
    }

    // ---- `.dbtest` -----------------------------------------------------------------------------------------------

    std::string GmFire(HmAct act, Player* who)
    {
        if (_ended)
            return "The package has ended.";
        if (!Fire(*_fight, act, who))
            return "Refused (see the log line: nobody to pick, no spot, or no boss to own it).";
        return {};
    }

    std::string GmCharge()
    {
        if (!(_alive & CrewBit(CREW_WEEGLI)))
            return "Weegli is dead.";
        if (_springs.empty())
            return "No spring stands (`.dbtest zf poolcrew spring` first).";
        EndWeegliJob("gm");
        StartWeegliJob(*_fight);
        return _weegli == WeegliStep::Idle ? "He could not start." : std::string();
    }

    std::string GmDispel()
    {
        return StartMassDispel(*_fight, "gm") ? std::string() : "Murta cannot (dead, wet, stunned or casting).";
    }

    std::string GmTwin()
    {
        Creature* head = Head();
        if (!head)
            return "No second head (Gahz'rilla must be ashore).";
        return StartHeadCast(head) ? std::string() : "The head is casting already, or the cast was refused.";
    }

    std::string GmDevour(uint32 member)
    {
        Creature* c = Crew(member);
        if (!c || !c->IsAlive())
            return "That crew member is not alive at the pool.";
        if (!ZfCrew::KillCrew(c, _fight->Gahzrilla()))
            return "Refused (CR: Weegli's floor holds until he stands at the pool).";
        return {};
    }

    std::string State(PoolFight& fight)
    {
        std::string crew;
        for (uint32 m = 0; m < kCrewCount; ++m)
        {
            Creature* c = Crew(m);
            crew += Acore::StringFormat(" {}={}", NameOf(m), !c || !c->IsAlive() ? std::string("dead")
                : Acore::StringFormat("{:.0f}%/c{}{}{}", c->GetHealthPct(), fight.Charged(c), fight.IsWater(c) ? "/wet"
                    : "", Stunned(m, c) ? "/stun" : ""));
        }
        return Acore::StringFormat("clock={}s phase={} springs={} weegli={} chosen={} overcharge={} dispel={} head={} "
            "next: spring {} ms, chosen {} ms, overcharge {} ms;{}", _clock.Now() / 1000, uint32(fight.Phase()),
            _springs.size(), uint32(_weegli), _chosen.live ? 1 : 0, _over.live ? 1 : 0, _dispelAt ? 1 : 0,
            _head.IsEmpty() ? 0 : 1, _clock.In(HmAct::Wellspring), _clock.In(HmAct::StormsChosen),
            _clock.In(HmAct::Overcharge), crew);
    }

private:
    struct Mate
    {
        uint64 wetSince = 0;
        bool wet = false;
        bool leaving = false;
        uint64 stunnedUntil = 0;
        uint64 nextHitAt = 0;
        std::optional<Vec2> goal;
    };

    struct Spring
    {
        ObjectGuid guid;
        uint32 sheet = 0;
        Position at;
        uint64 nextGrowAt = 0;
        uint64 nextLookAt = 0;
        bool charged = false;       // Weegli planted on it
    };

    struct Mark
    {
        ObjectGuid player;
        uint64 endsAt = 0;
        bool live = false;
        bool siphoning = false;     // Overcharge: Oro's channel runs
        uint64 siphonEndsAt = 0;
    };

    struct Counts
    {
        uint32 springs = 0;
        uint32 blasts = 0;
        uint32 chosen = 0;
        uint32 bodyguard = 0;
        uint32 overcharges = 0;
        uint32 siphons = 0;
        uint32 dispels = 0;
        uint32 twin = 0;
        uint32 ravenKicks = 0;
        uint32 devoured = 0;
    };

    void Unlist()
    {
        std::lock_guard<std::mutex> guard(LiveLock());
        auto it = Live().find(_map);
        if (it != Live().end() && it->second == this)
            Live().erase(it);
    }

    void Track(MechanicHandle h)
    {
        if (!h)
            return;
        _handles.push_back(h);
        _fight->Track(h);
    }

    void Cancel(MechanicHandle& h)
    {
        if (h)
            if (Creature* keeper = _fight->Keeper())
                Mechanic::Cancel(keeper, h);
        h = MechanicHandle();
    }

    // ---- Units -----------------------------------------------------------------------------------------------------

    // A crew member standing at the pool in its PoolAlly mode (dead ones too; nullptr: not there).
    Creature* Crew(uint32 member)
    {
        InstanceScript* instance = _fight->Instance();
        ZfCrew::BlyCrewAI* ai = instance ? ZfCrew::CrewAI(instance, member) : nullptr;
        if (ai && ai->Mode() == CrewMode::PoolAlly)
            return ai->Me();
        Creature* c = instance ? CrewCreature(instance, member) : nullptr;
        return c && !c->IsAlive() ? c : nullptr;
    }

    ZfCrew::BlyCrewAI* CrewAIOf(uint32 member)
    {
        InstanceScript* instance = _fight->Instance();
        ZfCrew::BlyCrewAI* ai = instance ? ZfCrew::CrewAI(instance, member) : nullptr;
        return ai && ai->Mode() == CrewMode::PoolAlly && ai->Me()->IsAlive() ? ai : nullptr;
    }

    bool Stunned(uint32 m, Creature const* c) const
    {
        return _clock.Now() < _mates[m].stunnedUntil || (c && c->HasUnitState(UNIT_STATE_STUNNED));
    }

    // The answers' rule: alive, standing dry (dry ground or ice) and not stunned.
    bool Able(uint32 m, Creature* c) const
    {
        return c && c->IsAlive() && !_fight->IsWater(c) && !Stunned(m, c);
    }

    Creature* Head()
    {
        Creature* head = _head.IsEmpty() ? nullptr : _map->GetCreature(_head);
        return head && head->IsAlive() ? head : nullptr;
    }

    // The boss the crew fight: Gahz'rilla once ashore, else Velratha alive (phase 1 and the rise).
    Creature* CrewTarget(PoolFight& fight)
    {
        if (fight.Phase() >= PoolPhase::Gahzrilla)
            if (Creature* g = fight.Gahzrilla(); g && g->IsAlive() && !g->HasUnitFlag(UNIT_FLAG_NOT_SELECTABLE))
                return g;
        Creature* v = fight.Velratha();
        return v && v->IsAlive() ? v : nullptr;
    }

    // The owner of this package's registry shapes and the caster of its player hits: the boss in play (registry
    // shapes need an encounter; the keeper has none).
    Unit* Owner(PoolFight& fight)
    {
        if (Creature* g = fight.Gahzrilla(); g && g->IsAlive() && g->IsEngaged())
            return g;
        if (Creature* v = fight.Velratha(); v && v->IsAlive() && v->IsEngaged())
            return v;
        return nullptr;
    }

    std::vector<Vec2> PlayerSpots(PoolFight& fight)
    {
        std::vector<Vec2> out;
        for (Player* p : fight.FightPlayers())
            out.push_back(DungeonKit::PlaneOf(p));
        return out;
    }

    // Dry ground or ice at (p, near zHint) on the shore: never the pool, never water.
    bool DryAt(PoolFight& fight, Vec2 p, float zHint)
    {
        float const z = FloorZ(fight.Keeper(), p, zHint);
        Position const pos(p.x, p.y, z);
        if (fight.Water().IsIce(pos))
            return true;
        return OnShore(p) && !fight.Water().IsWater(pos);
    }

    // The ice sheets' middles (in the Deluge the only dry ground).
    std::vector<Vec2> IceMiddles(PoolFight& fight)
    {
        std::vector<Vec2> out;
        for (DungeonKit::WaterSheet const& s : fight.Water().All())
            if (!s.IsWater() && !s.IsStrip())
                out.push_back(s.center);
        return out;
    }

    // The nearest dry spot to `want` (rings around it, then the ice).
    std::optional<Position> NearestDry(PoolFight& fight, Vec2 want, float zHint)
    {
        std::vector<Vec2> const ice = IceMiddles(fight);
        std::vector<Vec2> const candidates = SearchCandidates(want, ice);
        std::optional<Vec2> const best = NearestOf(want, std::span<Vec2 const>(candidates),
            [&](Vec2 c) { return DryAt(fight, c, zHint); });
        if (!best)
            return std::nullopt;
        return Position(best->x, best->y, FloorZ(fight.Keeper(), *best, zHint));
    }

    void WalkCrew(uint32 m, Position const& pos, uint32 pointId)
    {
        ZfCrew::BlyCrewAI* ai = CrewAIOf(m);
        if (!ai)
            return;
        ai->WalkTo(pos, pointId, true);
        _mates[m].goal = Vec2{ pos.GetPositionX(), pos.GetPositionY() };
    }

    // A member busy in place (a cast, a channel, Weegli's job): the think loop leaves it.
    bool Busy(uint32 m) const
    {
        switch (m)
        {
            case CREW_WEEGLI:
                return _weegli != WeegliStep::Idle;
            case CREW_ORO:
                return _over.siphoning;
            case CREW_MURTA:
                return _dispelAt || _healAt;
            default:
                return false;
        }
    }

    // ---- GZ21 the crew's rules -------------------------------------------------------------------------------------

    void TickCrewCharged(PoolFight& fight)
    {
        for (uint32 m = 0; m < kCrewCount; ++m)
            if (Creature* c = Crew(m); c && c->IsAlive() && fight.IsWater(c))
                fight.AddCharged(c, 1);
    }

    // Once a second: water reached them (2 s late out), else to their fight spot.
    void Think(PoolFight& fight)
    {
        Creature* boss = CrewTarget(fight);
        std::vector<Vec2> const players = PlayerSpots(fight);
        for (uint32 m = 0; m < kCrewCount; ++m)
        {
            Creature* c = Crew(m);
            if (!c || !c->IsAlive())
                continue;
            Mate& mate = _mates[m];
            bool const wet = fight.IsWater(c);
            if (wet && !mate.wet)
                mate.wetSince = _clock.Now();
            mate.wet = wet;
            if (!wet)
                mate.leaving = false;
            if (Busy(m) || Stunned(m, c))
                continue;
            Vec2 const here = DungeonKit::PlaneOf(c);
            if (wet)
            {
                if (mate.leaving || !WaterExitDue(_clock.Now(), mate.wetSince))
                    continue;
                if (std::optional<Position> dry = NearestDry(fight, here, c->GetPositionZ()))
                {
                    mate.leaving = true;
                    WalkCrew(m, *dry, kPointCrewFight);
                    LogHm("crew-out-of-water", Acore::StringFormat("{} after={}ms charged={} to=({:.1f}, {:.1f})",
                        NameOf(m), _clock.Now() - mate.wetSince, fight.Charged(c), dry->GetPositionX(),
                        dry->GetPositionY()));
                }
                continue;
            }
            if (!boss)
                continue;
            Vec2 const bossAt = DungeonKit::PlaneOf(boss);
            float const toGroup = BearingToMiddle(bossAt, std::span<Vec2 const>(players),
                DungeonKit::BearingTo(bossAt, kPoolMiddle) + DungeonKit::kPi);
            Vec2 const want = CrewFightSpot(m, bossAt, toGroup, boss->GetCombatReach());
            if (mate.goal && DungeonKit::Distance(*mate.goal, want) <= Tune::kCrewMoveSlackYd)
                continue;
            if (DungeonKit::Distance(here, want) <= Tune::kCrewMoveSlackYd)
                continue;
            std::optional<Position> spot = DryAt(fight, want, c->GetPositionZ())
                ? std::optional<Position>(Position(want.x, want.y, FloorZ(fight.Keeper(), want, c->GetPositionZ())))
                : NearestDry(fight, want, c->GetPositionZ());
            if (spot && DungeonKit::Distance(here, { spot->GetPositionX(), spot->GetPositionY() })
                > Tune::kCrewMoveSlackYd)
                WalkCrew(m, *spot, kPointCrewFight);
        }
    }

    // Their small hits on the boss in play (script, rule 29; never the killing blow).
    void CrewHits(PoolFight& fight)
    {
        Creature* boss = CrewTarget(fight);
        if (!boss)
            return;
        for (uint32 m = 0; m < kCrewCount; ++m)
        {
            Creature* c = Crew(m);
            Mate& mate = _mates[m];
            if (!c || !c->IsAlive() || _clock.Now() < mate.nextHitAt || Busy(m) || Stunned(m, c) || c->isMoving())
                continue;
            bool const reach = IsMeleeCrew(m) ? c->IsWithinMeleeRange(boss)
                : c->GetExactDist2d(boss) <= Tune::kCrewHitRangeYd + boss->GetCombatReach();
            if (!reach)
                continue;
            mate.nextHitAt = _clock.Now() + Tune::kCrewHitEveryMs;
            uint32 const amount = CrewHitCapped(CrewHitAmount(m), boss->GetHealth());
            if (!amount)
                continue;
            c->SetFacingToObject(boss);
            c->HandleEmoteCommand(IsMeleeCrew(m) ? EMOTE_ONESHOT_ATTACK1H
                : (m == CREW_WEEGLI ? EMOTE_ONESHOT_ATTACK_THROWN : EMOTE_ONESHOT_SPELL_CAST_OMNI));
            SpellSchoolMask const school = IsMeleeCrew(m) ? SPELL_SCHOOL_MASK_NORMAL
                : (m == CREW_ORO ? SPELL_SCHOOL_MASK_SHADOW : (m == CREW_WEEGLI ? SPELL_SCHOOL_MASK_FIRE
                    : SPELL_SCHOOL_MASK_HOLY));
            // skipCombat: no threat on the boss (the crew are faction 35; he must never turn on them).
            Unit::DealDamage(c, boss, amount, nullptr, DIRECT_DAMAGE, school, nullptr, false, false, nullptr, true);
        }
    }

    // GZ21: a fallen member stays dead for the attempt; the god eats it (5%, line 2); its answer falls to the group.
    void ResolveDeaths(PoolFight& fight)
    {
        uint32 const deaths = _pendingDeaths;
        _pendingDeaths = 0;
        for (uint32 m = 0; m < kCrewCount; ++m)
        {
            if (!(deaths & CrewBit(m)) || !(_alive & CrewBit(m)))
                continue;
            _alive &= ~CrewBit(m);
            ++_counts.devoured;
            Interrupted(m, "death");
            Creature* gahzrilla = fight.Gahzrilla();
            Creature* c = CrewCreature(fight.Instance(), m);
            bool const eaten = gahzrilla && gahzrilla->IsAlive();
            if (eaten)
            {
                fight.HealGahzrilla(Tune::kDevourHealPct);
                if (gahzrilla->IsAIEnabled)
                    gahzrilla->AI()->Talk(EMOTE_GAHZRILLA_DEVOURS, c);
            }
            LogHm("devoured", Acore::StringFormat("{} phase={} eaten={} crew={}", NameOf(m), uint32(fight.Phase()),
                eaten ? 1 : 0, _alive));
        }
        fight.RefreshDescriptors();
    }

    // A member's cast or job is broken (a stun, a death).
    void Interrupted(uint32 m, char const* why)
    {
        switch (m)
        {
            case CREW_WEEGLI:
                // A stun is the plant's own business (UpdateWeegli starts it over); a death ends the run or the plant
                // (a lit fuse still blows).
                if (std::string_view(why) == "death" && (_weegli == WeegliStep::Running
                    || _weegli == WeegliStep::Planting))
                    EndWeegliJob(why);
                break;
            case CREW_ORO:
                if (_over.siphoning)
                {
                    _over.siphoning = false;
                    LogHm("siphon-broken", why);
                    if (Creature* oro = Crew(CREW_ORO); oro && oro->IsAlive())
                        oro->InterruptNonMeleeSpells(false);
                }
                break;
            case CREW_MURTA:
                if (_dispelAt || _healAt)
                {
                    LogHm(_dispelAt ? "mass-dispel-broken" : "greater-heal-broken", why);
                    _dispelAt = 0;
                    _healAt = 0;
                    if (Creature* murta = Crew(CREW_MURTA); murta && murta->IsAlive())
                        murta->InterruptNonMeleeSpells(false);
                }
                break;
            default:
                break;
        }
    }

    // GZ19: everyone within 6 yd of a carrier (or in a wet carrier's sheet) takes an arc every 2 s. D7 arcs from the
    // players to the players; this does the crew's part: crew carriers on players and crew, player carriers on crew.
    void TickConductive(PoolFight& fight)
    {
        if (!_arcAt || _clock.Now() < _arcAt)
            return;
        _arcAt += ZfPool::Tune::kConductiveTickMs;
        Unit* owner = Owner(fight);
        std::vector<Unit*> carriers;
        std::vector<Player*> const players = fight.FightPlayers();
        for (Player* p : players)
            if (p->HasAura(ZfPool::SPELL_GZ_CONDUCTIVE))
                carriers.push_back(p);
        bool crewCarrier = false;
        for (uint32 m = 0; m < kCrewCount; ++m)
            if (Creature* c = Crew(m); c && c->IsAlive() && c->HasAura(ZfPool::SPELL_GZ_CONDUCTIVE))
            {
                carriers.push_back(c);
                crewCarrier = true;
            }
        if (carriers.empty())
        {
            _arcAt = 0;
            return;
        }
        auto reaches = [&](Unit* target, bool crewOnly)
        {
            for (Unit* carrier : carriers)
            {
                if (carrier == target || (crewOnly && carrier->IsPlayer()))
                    continue;
                if (carrier->GetExactDist(target) <= ZfPool::Tune::kConductiveArcYd)
                    return true;
                if (fight.IsWater(carrier))
                    if (std::optional<uint32> sheet = fight.Water().WaterSheetAt(carrier->GetPosition()))
                        if (fight.Water().InWaterSheet(*sheet, target))
                            return true;
            }
            return false;
        };
        SpellInfo const* arc = sSpellMgr->GetSpellInfo(ZfPool::SPELL_GZ_CONDUCTIVE_ARC);
        uint32 crewHits = 0;
        uint32 playerHits = 0;
        std::vector<std::pair<ObjectGuid, uint32>> hits;
        for (uint32 m = 0; m < kCrewCount; ++m)
            if (Creature* c = Crew(m); c && c->IsAlive() && reaches(c, false))
            {
                hits.emplace_back(c->GetGUID(), PctOfHealth(c->GetMaxHealth(), Tune::kCrewConductivePct));
                ++crewHits;
            }
        // Players: only a crew carrier's arcs (D7 does the players' own).
        if (crewCarrier && owner)
            for (Player* p : players)
                if (reaches(p, true))
                {
                    CastSpellExtraArgs args(TRIGGERED_FULL_MASK);
                    args.AddSpellBP0(static_cast<int32>(fight.RefFlatOn(p, Tune::kCrewConductivePct)));
                    owner->CastSpell(p, ZfPool::SPELL_GZ_CONDUCTIVE_ARC, args);
                    ++playerHits;
                }
        for (auto const& [guid, amount] : hits)
            if (Creature* c = _map->GetCreature(guid); c && c->IsAlive())
                ZfCrew::DamageCrew(c, nullptr, amount, SPELL_SCHOOL_MASK_NATURE, arc);
        if (crewHits || playerHits)
            LogHm("crew-conductive", Acore::StringFormat("carriers={} crew-hit={} players-hit={}", carriers.size(),
                crewHits, playerHits));
    }

    // ---- The beats -------------------------------------------------------------------------------------------------

    bool Fire(PoolFight& fight, HmAct act, Player* forced)
    {
        switch (act)
        {
            case HmAct::Wellspring:
                return SpawnSpring(fight);
            case HmAct::StormsChosen:
                return StartChosen(fight, forced);
            case HmAct::Overcharge:
                return StartOvercharge(fight, forced);
            case HmAct::None:
                break;
        }
        return false;
    }

    Player* PickPlayer(PoolFight& fight, Player* forced)
    {
        if (forced)
            return forced;
        std::vector<Player*> players = fight.FightPlayers();
        return players.empty() ? nullptr : Acore::Containers::SelectRandomContainerElement(players);
    }

    // ---- GZ15 Wellspring, GZ16 Blasting Charge --------------------------------------------------------------------

    void CheckDeluge(PoolFight& fight)
    {
        if (_delugeSeen || fight.Phase() != PoolPhase::Deluge)
            return;
        _delugeSeen = true;
        _clock.StopSprings();
        EndWeegliJob("deluge");
        uint32 const swallowed = static_cast<uint32>(_springs.size());
        for (Spring const& s : _springs)
            RemoveSpring(fight, s);
        _springs.clear();
        LogHm("deluge", Acore::StringFormat("springs-swallowed={}", swallowed));
    }

    bool SpawnSpring(PoolFight& fight)
    {
        if (!_clock.SpringsRunning())
            return false;
        Creature* keeper = fight.Keeper();
        if (!keeper)
            return false;
        std::vector<Vec2> const players = PlayerSpots(fight);
        std::vector<Vec2> candidates = SpringCandidates(std::span<Vec2 const>(players));
        Acore::Containers::RandomShuffle(candidates);
        std::optional<Position> at;
        for (Vec2 const& c : candidates)
        {
            float const floor = keeper->GetMapHeight(c.x, c.y, kShoreZ + 5.f);
            if (floor <= INVALID_HEIGHT + 1.f || floor < kShoreZMin || floor > kShoreZMax)
                continue;
            Position const pos(c.x, c.y, floor);
            if (fight.Water().IsWater(pos) || fight.Water().IsIce(pos))
                continue;       // dry ground: a new spring is a new puddle
            at = pos;
            break;
        }
        if (!at)
        {
            LogHm("wellspring-none", Acore::StringFormat("candidates={}", candidates.size()));
            return false;
        }
        Creature* spring = fight.Summon(NPC_ZF_WELLSPRING, *at);
        if (!spring)
        {
            LogHm("wellspring-refused");
            return false;
        }
        DungeonKit::SheetRules rules;
        rules.canFreeze = false;
        rules.grows = false;            // its own growth (below); Rising Water and Call the Waters skip it
        rules.thawMs = 0;
        rules.zBand = Tune::kWellspringZBandYd;
        rules.kind = SHEET_WELLSPRING;
        Spring s;
        s.guid = spring->GetGUID();
        s.at = *at;
        s.sheet = fight.AddSheet(*at, Tune::kWellspringRadiusYd, rules, DungeonKit::SheetState::Water, "wellspring");
        s.nextGrowAt = _clock.Now() + Tune::kWellspringGrowEveryMs;
        s.nextLookAt = _clock.Now() + Tune::kWellspringLookEveryMs;
        spring->CastSpell(spring, SPELL_HM_WELLSPRING, true);
        if (Unit* owner = Owner(fight))
            Mechanic::TrackUnit(owner, spring);
        _springs.push_back(s);
        ++_counts.springs;
        LogHm("wellspring", Acore::StringFormat("sheet={} at=({:.1f}, {:.1f}, {:.1f}) live={} weegli={}", s.sheet,
            at->GetPositionX(), at->GetPositionY(), at->GetPositionZ(), _springs.size(),
            (_alive & CrewBit(CREW_WEEGLI)) ? 1 : 0));
        if (_weegli == WeegliStep::Idle)
            StartWeegliJob(fight);
        return true;
    }

    // The spring's puddle goes, and the spring with it (a killed one leaves its corpse to D7's cleanup).
    void RemoveSpring(PoolFight& fight, Spring const& s)
    {
        if (Creature* keeper = fight.Keeper(); keeper && s.sheet)
            fight.Water().Remove(keeper, s.sheet);
        if (Creature* spring = _map->GetCreature(s.guid); spring && spring->IsAlive())
            spring->DespawnOrUnsummon();
    }

    void UpdateSprings(PoolFight& fight)
    {
        Creature* keeper = fight.Keeper();
        for (auto it = _springs.begin(); it != _springs.end();)
        {
            Creature* spring = _map->GetCreature(it->guid);
            if (!spring || !spring->IsAlive())
            {
                // Killed (SpringDied handles it on its death; this is the safety net) or gone.
                RemoveSpring(fight, *it);
                if (_jobSpring == it->guid)
                    EndWeegliJob("spring-gone");
                it = _springs.erase(it);
                continue;
            }
            if (_clock.Now() >= it->nextGrowAt)
            {
                it->nextGrowAt += Tune::kWellspringGrowEveryMs;
                if (keeper && it->sheet)
                    fight.Water().Grow(keeper, it->sheet, Tune::kWellspringGrowYd);
            }
            if (_clock.Now() >= it->nextLookAt)
            {
                it->nextLookAt += Tune::kWellspringLookEveryMs;
                spring->CastSpell(spring, SPELL_HM_WELLSPRING, true);
            }
            ++it;
        }
    }

    Spring* FindSpring(ObjectGuid guid)
    {
        for (Spring& s : _springs)
            if (s.guid == guid)
                return &s;
        return nullptr;
    }

    // The newest spring nobody planted on.
    Spring* NewestOpenSpring()
    {
        for (auto it = _springs.rbegin(); it != _springs.rend(); ++it)
            if (!it->charged)
                return &*it;
        return nullptr;
    }

    void StartWeegliJob(PoolFight& fight)
    {
        Spring* s = NewestOpenSpring();
        Creature* weegli = Crew(CREW_WEEGLI);
        if (!s || !weegli || !weegli->IsAlive() || _weegli != WeegliStep::Idle)
            return;
        _jobSpring = s->guid;
        _weegli = WeegliStep::Running;
        _weegliArrived = false;
        _plantRestart = false;
        _stepAt = _clock.Now() + Tune::kWeegliRunTimeoutMs;
        // Up to the spring's middle, stopping a little short (he plants from within kPlantReachYd).
        Vec2 const from = DungeonKit::PlaneOf(weegli);
        Vec2 const to{ s->at.GetPositionX(), s->at.GetPositionY() };
        float const d = DungeonKit::Distance(from, to);
        float const stop = std::min(d, Tune::kPlantReachYd - 1.f);
        Vec2 const spot = d > 0.1f ? Vec2{ to.x + (from.x - to.x) / d * stop, to.y + (from.y - to.y) / d * stop } : to;
        if (ZfCrew::BlyCrewAI* ai = CrewAIOf(CREW_WEEGLI))
            ai->WalkTo(Position(spot.x, spot.y, FloorZ(fight.Keeper(), spot, s->at.GetPositionZ())), kPointWeegliSpring,
                true);
        _mates[CREW_WEEGLI].goal.reset();
        LogHm("weegli-run", Acore::StringFormat("walk={:.1f}", d));
    }

    void RemoveBarrel()
    {
        if (GameObject* barrel = _barrel.IsEmpty() ? nullptr : _map->GetGameObject(_barrel))
            barrel->DespawnOrUnsummon();
        _barrel.Clear();
    }

    void EndWeegliJob(char const* why)
    {
        if (_weegli == WeegliStep::Idle)
            return;
        if (_weegli == WeegliStep::Fuse)
        {
            // A planted charge still blows (the fuse is lit); only the spring's death or the Deluge stop it.
            if (std::string_view(why) != "spring-killed" && std::string_view(why) != "spring-gone"
                && std::string_view(why) != "deluge" && std::string_view(why) != "gm")
                return;
            Cancel(_blast);
            RemoveBarrel();
        }
        if (Creature* weegli = Crew(CREW_WEEGLI); weegli && weegli->IsAlive() && weegli->IsNonMeleeSpellCast(false))
            weegli->InterruptNonMeleeSpells(false);
        if (Spring* s = FindSpring(_jobSpring); s && _weegli != WeegliStep::Fuse)
            s->charged = false;
        LogHm("weegli-job-end", Acore::StringFormat("why={} step={}", why, uint32(_weegli)));
        _weegli = WeegliStep::Idle;
        _jobSpring.Clear();
    }

    void UpdateWeegli(PoolFight& fight)
    {
        if (_weegli == WeegliStep::Idle)
        {
            if (!_springs.empty() && (_alive & CrewBit(CREW_WEEGLI)))
                StartWeegliJob(fight);
            return;
        }
        Spring* s = FindSpring(_jobSpring);
        Creature* weegli = Crew(CREW_WEEGLI);
        bool const weegliUp = weegli && weegli->IsAlive();
        if (!s || (!weegliUp && _weegli != WeegliStep::Fuse))
        {
            EndWeegliJob(!s ? "spring-gone" : "weegli-gone");
            return;
        }
        switch (_weegli)
        {
            case WeegliStep::Running:
            {
                bool const there = weegli->GetExactDist2d(s->at.GetPositionX(), s->at.GetPositionY())
                    <= Tune::kPlantReachYd + 0.5f;
                if (!there && !_weegliArrived && _clock.Now() < _stepAt)
                    break;
                if (Stunned(CREW_WEEGLI, weegli))
                    break;
                weegli->StopMoving();
                weegli->SetFacingTo(weegli->GetAbsoluteAngle(s->at.GetPositionX(), s->at.GetPositionY()));
                weegli->CastSpell(weegli, SPELL_HM_PLANT_CHARGE, false);
                s->charged = true;
                _weegli = WeegliStep::Planting;
                _stepAt = _clock.Now() + Tune::kPlantMs;
                LogHm("weegli-plant", Acore::StringFormat("how={} charged={}", there ? "arrived" : "timeout",
                    fight.Charged(weegli)));
                break;
            }
            case WeegliStep::Planting:
                if (Stunned(CREW_WEEGLI, weegli))
                {
                    // A stun starts the plant over once he can act again.
                    _plantRestart = true;
                    _stepAt = _clock.Now() + Tune::kPlantMs;
                    break;
                }
                if (_plantRestart)
                {
                    _plantRestart = false;
                    _stepAt = _clock.Now() + Tune::kPlantMs;
                    weegli->CastSpell(weegli, SPELL_HM_PLANT_CHARGE, false);
                    LogHm("weegli-plant", "restart");
                    break;
                }
                if (_clock.Now() < _stepAt)
                    break;
                LightFuse(fight, *s, weegli);
                break;
            case WeegliStep::Fuse:
                if (_clock.Now() < _stepAt)
                    break;
                Blast(fight, *s);
                break;
            case WeegliStep::Idle:
                break;
        }
    }

    void LightFuse(PoolFight& fight, Spring const& s, Creature* weegli)
    {
        _weegli = WeegliStep::Fuse;
        _stepAt = _clock.Now() + Tune::kFuseMs;
        if (weegli->IsAIEnabled)
            weegli->AI()->Talk(ZfCrew::YELL_WEEGLI_CHARGE);
        // VISUALS: the plant is his stock barrel (spell 10772 summons GO 141612, a wild object: found and despawned).
        weegli->CastSpell(weegli, ZfCrew::SPELL_WEEGLIS_BARREL, true);
        if (GameObject* barrel = weegli->FindNearestGameObject(GO_WEEGLIS_BARREL, 5.f))
            _barrel = barrel->GetGUID();
        if (Unit* owner = Owner(fight))
        {
            MechanicRef ref = Mechanic::Circle(owner, s.at, Tune::kBlastRadiusYd, Ms(Tune::kFuseMs));
            ref.Damage(Tune::kBlastPct).TankDamage(Tune::kBlastPct).School(SPELL_SCHOOL_FIRE)
                .Spell(SPELL_HM_BLASTING_CHARGE).Within(PoolFloorBounds()).Tag(TAG_HM_BLAST);
            _blast = ref.Handle();
            Track(_blast);
        }
        // He steps out of his own blast, away from the spring toward his fight spot's side.
        Vec2 const spring{ s.at.GetPositionX(), s.at.GetPositionY() };
        Vec2 const here = DungeonKit::PlaneOf(weegli);
        float const away = DungeonKit::Distance(spring, here) > 0.5f ? DungeonKit::BearingTo(spring, here)
            : DungeonKit::BearingTo(spring, kPoolMiddle) + DungeonKit::kPi;
        Vec2 const out = DungeonKit::Advance(spring, away, Tune::kWeegliStepAwayYd);
        std::optional<Position> spot = DryAt(fight, out, weegli->GetPositionZ())
            ? std::optional<Position>(Position(out.x, out.y, FloorZ(fight.Keeper(), out, weegli->GetPositionZ())))
            : std::nullopt;
        WalkCrew(CREW_WEEGLI, spot ? *spot : Position(out.x, out.y, FloorZ(fight.Keeper(), out,
            weegli->GetPositionZ())), kPointCrewFight);
        LogHm("blasting-charge", Acore::StringFormat("fuse={}ms radius={:.0f} pct={:.0f}", Tune::kFuseMs,
            Tune::kBlastRadiusYd, Tune::kBlastPct));
    }

    // The blast: the registry hits the players (tag 40); the spring and its puddle go here, whatever the registry did.
    void Blast(PoolFight& fight, Spring const& s)
    {
        ObjectGuid const guid = s.guid;
        if (Creature* spring = _map->GetCreature(guid); spring && spring->IsAlive())
            spring->CastSpell(spring, SPELL_HM_BLAST_LOOK, true);
        ++_counts.blasts;
        RemoveBarrel();
        _blast = MechanicHandle();
        _weegli = WeegliStep::Idle;
        _jobSpring.Clear();
        for (auto it = _springs.begin(); it != _springs.end(); ++it)
            if (it->guid == guid)
            {
                RemoveSpring(fight, *it);
                _springs.erase(it);
                break;
            }
        LogHm("blast", Acore::StringFormat("springs-left={}", _springs.size()));
    }

    // ---- GZ17 Storm's Chosen --------------------------------------------------------------------------------------

    bool StartChosen(PoolFight& fight, Player* forced)
    {
        if (_chosen.live)
            ResolveChosen(fight);
        Unit* owner = Owner(fight);
        Player* target = PickPlayer(fight, forced);
        if (!owner)
            return false;       // retried (the beat loop)
        if (!target)
        {
            LogHm("storms-chosen-none", "no player");
            return false;
        }
        owner->CastSpell(target, SPELL_HM_STORMS_CHOSEN, true);
        DungeonKit::ShortenAura(target, SPELL_HM_STORMS_CHOSEN, owner->GetGUID(), Ms(Tune::kChosenMarkMs));
        _chosen = Mark();
        _chosen.player = target->GetGUID();
        _chosen.endsAt = _clock.Now() + Tune::kChosenMarkMs;
        _chosen.live = true;
        ++_counts.chosen;
        Creature* bly = Crew(CREW_BLY);
        bool const blyUp = bly && bly->IsAlive();
        if (blyUp)
        {
            if (bly->IsAIEnabled)
                bly->AI()->Talk(ZfCrew::YELL_BLY_BEHIND_ME, target);
            BossMechanics::Eligibility only;
            only.carriers.insert(target->GetGUID());
            MechanicRef ref = Mechanic::Stack(owner, bly, Tune::kChosenStackYd, Ms(Tune::kChosenMarkMs));
            ref.Eligible(only).Within(PoolFloorBounds()).Tag(TAG_HM_CHOSEN);
            Track(ref.Handle());
        }
        else
        {
            MechanicRef ref = Mechanic::Stack(owner, target, Tune::kChosenSplitYd - 1.f, Ms(Tune::kChosenMarkMs));
            ref.Within(PoolFloorBounds()).Tag(TAG_HM_CHOSEN);
            Track(ref.Handle());
        }
        LogHm("storms-chosen", Acore::StringFormat("target={} tank={} bly={}", target->GetName(),
            target == owner->GetVictim() ? 1 : 0, blyUp ? 1 : 0));
        return true;
    }

    void UpdateChosen(PoolFight& fight)
    {
        if (_chosen.live && _clock.Now() >= _chosen.endsAt)
            ResolveChosen(fight);
    }

    void ResolveChosen(PoolFight& fight)
    {
        _chosen.live = false;
        Player* target = ObjectAccessor::GetPlayer(_map, _chosen.player);
        Unit* owner = Owner(fight);
        if (!target || !target->IsAlive() || !target->IsInWorld() || !owner)
        {
            LogHm("storms-chosen-fizzle", !owner ? "no boss" : "the mark is gone");
            return;
        }
        target->RemoveAurasDueToSpell(SPELL_HM_STORMS_CHOSEN);
        Creature* bly = Crew(CREW_BLY);
        bool const blyAlive = bly && bly->IsAlive();
        float const toBly = blyAlive ? target->GetExactDist(bly) : 999.f;
        switch (ChosenFor(blyAlive, blyAlive && Able(CREW_BLY, bly), toBly))
        {
            case Chosen::Bodyguard:
                bly->CastSpell(bly, SPELL_HM_BODYGUARD, true);
                bly->CastSpell(bly, SPELL_HM_STORM_BOLT_LOOK, true);
                fight.AddCharged(bly, int32(Tune::kBodyguardCharged));
                ++_counts.bodyguard;
                LogHm("storms-chosen-land", Acore::StringFormat("bodyguard target={} bly-charged={}",
                    target->GetName(), fight.Charged(bly)));
                break;
            case Chosen::Alone:
            {
                CastSpellExtraArgs args(TRIGGERED_FULL_MASK);
                uint32 const amount = fight.RefFlatOn(target, Tune::kChosenPct);
                args.AddSpellBP0(static_cast<int32>(amount));
                owner->CastSpell(target, SPELL_HM_STORMS_CHOSEN_BOLT, args);
                LogHm("storms-chosen-land", Acore::StringFormat("alone target={} amount={} to-bly={:.1f} bly-able={}",
                    target->GetName(), amount, toBly, Able(CREW_BLY, bly) ? 1 : 0));
                break;
            }
            case Chosen::Split:
            {
                std::vector<Unit*> inside;
                for (Player* p : fight.FightPlayers())
                    if (p == target || p->GetExactDist(target) <= Tune::kChosenSplitYd)
                        inside.push_back(p);
                std::vector<std::pair<ObjectGuid, uint32>> const shares =
                    DungeonKit::SplitShares(owner, inside, Tune::kChosenPct);
                for (auto const& [guid, amount] : shares)
                    if (Player* p = ObjectAccessor::GetPlayer(_map, guid))
                    {
                        CastSpellExtraArgs args(TRIGGERED_FULL_MASK);
                        args.AddSpellBP0(static_cast<int32>(amount));
                        owner->CastSpell(p, SPELL_HM_STORMS_CHOSEN_BOLT, args);
                        if (p->IsAlive())
                            fight.AddCharged(p, int32(Tune::kChosenSplitCharged));
                    }
                LogHm("storms-chosen-land", Acore::StringFormat("split target={} players={}", target->GetName(),
                    shares.size()));
                break;
            }
        }
    }

    // ---- GZ18 Overcharge ------------------------------------------------------------------------------------------

    bool StartOvercharge(PoolFight& fight, Player* forced)
    {
        if (_over.live)
            EndOvercharge(fight, "replaced");
        Unit* owner = Owner(fight);
        Player* target = PickPlayer(fight, forced);
        if (!owner)
            return false;       // retried (the beat loop)
        if (!target)
        {
            LogHm("overcharge-none", "no player");
            return false;
        }
        owner->CastSpell(target, SPELL_HM_OVERCHARGE, true);
        _over = Mark();
        _over.player = target->GetGUID();
        _over.endsAt = _clock.Now() + Tune::kOverchargeMs;
        _over.live = true;
        ++_counts.overcharges;
        Creature* oro = Crew(CREW_ORO);
        bool const oroUp = oro && oro->IsAlive();
        if (oroUp)
        {
            BossMechanics::Eligibility only;
            only.carriers.insert(target->GetGUID());
            MechanicRef ref = Mechanic::Stack(owner, oro, Tune::kOverchargeStackYd, Ms(Tune::kOverchargeMs));
            ref.Eligible(only).Within(PoolFloorBounds()).Tag(TAG_HM_OVERCHARGE);
            _overStack = ref.Handle();
            Track(_overStack);
        }
        LogHm("overcharge", Acore::StringFormat("target={} tank={} oro={}", target->GetName(),
            target == owner->GetVictim() ? 1 : 0, oroUp ? 1 : 0));
        return true;
    }

    void UpdateOvercharge(PoolFight& fight)
    {
        if (!_over.live)
            return;
        Player* target = ObjectAccessor::GetPlayer(_map, _over.player);
        if (!target || !target->IsAlive() || !target->IsInWorld())
        {
            EndOvercharge(fight, "gone");
            return;
        }
        Creature* oro = Crew(CREW_ORO);
        if (_over.siphoning)
        {
            if (!oro || !oro->IsAlive() || Stunned(CREW_ORO, oro))
            {
                Interrupted(CREW_ORO, "stun");
                return;
            }
            if (_clock.Now() < _over.siphonEndsAt)
                return;
            if (oro->GetExactDist(target) > Tune::kSiphonRangeYd + 1.f)
            {
                _over.siphoning = false;
                oro->InterruptNonMeleeSpells(false);
                LogHm("siphon-broken", "out of reach");
                return;
            }
            // Drained.
            _over.siphoning = false;
            if (oro->IsNonMeleeSpellCast(false))
                oro->InterruptNonMeleeSpells(false);
            fight.AddCharged(oro, int32(Tune::kSiphonOroCharged));
            ++_counts.siphons;
            target->RemoveAurasDueToSpell(SPELL_HM_OVERCHARGE);
            _over.live = false;
            Cancel(_overStack);
            LogHm("siphon-charge", Acore::StringFormat("target={} oro-charged={}", target->GetName(),
                fight.Charged(oro)));
            return;
        }
        if (_clock.Now() >= _over.endsAt)
        {
            EndOvercharge(fight, "expired");
            return;
        }
        uint64 const left = _over.endsAt - _clock.Now();
        if (oro && oro->IsAlive() && !oro->isMoving()
            && SiphonCanStart(Able(CREW_ORO, oro), oro->GetExactDist(target), left))
        {
            oro->StopMoving();
            oro->SetFacingToObject(target);
            oro->CastSpell(target, SPELL_HM_SIPHON_CHARGE, false);
            _over.siphoning = true;
            _over.siphonEndsAt = _clock.Now() + Tune::kSiphonMs;
            LogHm("siphon-start", Acore::StringFormat("target={} left={}ms", target->GetName(), left));
        }
    }

    // The debuff ran out undrained: 5 Charged for good (or the player is gone: nothing).
    void EndOvercharge(PoolFight& fight, char const* why)
    {
        _over.live = false;
        if (_over.siphoning)
            Interrupted(CREW_ORO, why);
        _over.siphoning = false;
        Cancel(_overStack);
        Player* target = ObjectAccessor::GetPlayer(_map, _over.player);
        if (!target)
            return;
        // The debuff's own 8 s may run out on this very tick: the clock decides, not the aura.
        target->RemoveAurasDueToSpell(SPELL_HM_OVERCHARGE);
        if (std::string_view(why) == "expired" && target->IsAlive())
        {
            uint32 const now = fight.AddCharged(target, int32(Tune::kOverchargeStacks));
            LogHm("overcharge-land", Acore::StringFormat("target={} charged={}", target->GetName(), now));
        }
        else
            LogHm("overcharge-end", why);
    }

    // ---- GZ19 Mass Dispel, GZ21 Greater Heal ----------------------------------------------------------------------

    bool StartMassDispel(PoolFight& fight, char const* why)
    {
        Creature* murta = Crew(CREW_MURTA);
        if (!murta || !murta->IsAlive() || _dispelAt)
            return false;
        if (!Able(CREW_MURTA, murta))
        {
            LogHm("mass-dispel-missed", Acore::StringFormat("why={} wet={} stunned={}", why, fight.IsWater(murta) ? 1
                : 0, Stunned(CREW_MURTA, murta) ? 1 : 0));
            return false;
        }
        if (_healAt)
        {
            _healAt = 0;
            LogHm("greater-heal-broken", "mass dispel first");
        }
        murta->StopMoving();
        if (murta->IsNonMeleeSpellCast(false))
            murta->InterruptNonMeleeSpells(false);
        murta->CastSpell(murta, SPELL_HM_MASS_DISPEL, false);
        _dispelAt = _clock.Now() + Tune::kMassDispelCastMs;
        LogHm("mass-dispel-cast", why);
        return true;
    }

    void UpdateMurta(PoolFight& fight)
    {
        Creature* murta = Crew(CREW_MURTA);
        if (!murta || !murta->IsAlive())
            return;
        if (Stunned(CREW_MURTA, murta) && (_dispelAt || _healAt))
        {
            Interrupted(CREW_MURTA, "stun");
            return;
        }
        if (_dispelAt && _clock.Now() >= _dispelAt)
        {
            _dispelAt = 0;
            ResolveMassDispel(fight, murta);
        }
        if (_healAt && _clock.Now() >= _healAt)
        {
            _healAt = 0;
            Creature* target = Crew(_healTarget);
            if (target && target->IsAlive())
            {
                uint32 const added = ZfCrew::HealCrew(target, murta,
                    PctOfHealth(target->GetMaxHealth(), Tune::kGreaterHealPct));
                LogHm("greater-heal", Acore::StringFormat("target={} added={} health={:.0f}", NameOf(_healTarget),
                    added, target->GetHealthPct()));
            }
        }
        if (_dispelAt || _healAt || _clock.Now() < _nextHealAt || murta->isMoving())
            return;
        if (!CastFitsBeforeDischarge(fight.NextDischargeInMs(), Tune::kGreaterHealCastMs) || Stunned(CREW_MURTA, murta))
            return;
        std::vector<HealCandidate> crew;
        for (uint32 m = 0; m < kCrewCount; ++m)
        {
            HealCandidate h;
            h.member = m;
            Creature* c = Crew(m);
            h.alive = c && c->IsAlive();
            h.healthPct = h.alive ? c->GetHealthPct() : 100.f;
            h.inRange = h.alive && murta->GetExactDist(c) <= Tune::kGreaterHealRangeYd;
            crew.push_back(h);
        }
        std::optional<uint32> const pick = HealPick(std::span<HealCandidate const>(crew));
        if (!pick)
            return;
        Creature* target = Crew(*pick);
        murta->SetFacingToObject(target);
        murta->CastSpell(target, SPELL_HM_GREATER_HEAL, false);
        _healTarget = *pick;
        _healAt = _clock.Now() + Tune::kGreaterHealCastMs;
        _nextHealAt = _clock.Now() + Tune::kGreaterHealCastMs + Tune::kGreaterHealEveryMs;
    }

    void ResolveMassDispel(PoolFight& fight, Creature* murta)
    {
        uint32 players = 0;
        uint32 crew = 0;
        for (Player* p : fight.FightPlayers())
            if (InMassDispel(murta->GetExactDist(p)) && p->HasAura(ZfPool::SPELL_GZ_CONDUCTIVE))
            {
                p->RemoveAurasDueToSpell(ZfPool::SPELL_GZ_CONDUCTIVE);
                ++players;
            }
        for (uint32 m = 0; m < kCrewCount; ++m)
            if (Creature* c = Crew(m); c && c->IsAlive() && InMassDispel(murta->GetExactDist(c))
                && c->HasAura(ZfPool::SPELL_GZ_CONDUCTIVE))
            {
                c->RemoveAurasDueToSpell(ZfPool::SPELL_GZ_CONDUCTIVE);
                ++crew;
            }
        ++_counts.dispels;
        LogHm("mass-dispel", Acore::StringFormat("players={} crew={}", players, crew));
    }

    // ---- GZ20 Twin Call -------------------------------------------------------------------------------------------

    bool StartHeadCast(Creature* head)
    {
        if (head->HasUnitState(UNIT_STATE_CASTING))
            return false;
        if (head->CastSpell(head, SPELL_HM_TWIN_CALL, false) != SPELL_CAST_OK)
        {
            LogHm("twin-call-refused");
            return false;
        }
        _headCasting = true;
        _headCastAt = _clock.Now();
        _ravenTried = false;
        LogHm("twin-call", Acore::StringFormat("raven={}", (_alive & CrewBit(CREW_RAVEN)) ? 1 : 0));
        return true;
    }

    void UpdateTwinCall(PoolFight& fight)
    {
        Creature* gahzrilla = fight.Gahzrilla();
        Creature* head = Head();
        if (!gahzrilla || !gahzrilla->IsAlive() || !head || fight.Phase() < PoolPhase::Gahzrilla)
            return;
        if (!head->HasUnitState(UNIT_STATE_CASTING))
        {
            _headCasting = false;
            if (head->GetExactDist2d(gahzrilla) > 2.f)
                head->NearTeleportTo(gahzrilla->GetPositionX(), gahzrilla->GetPositionY(), gahzrilla->GetPositionZ(),
                    gahzrilla->GetOrientation());
        }
        bool const calling = gahzrilla->FindCurrentSpellBySpellId(ZfPool::SPELL_GZ_CALL_THE_WATERS_HEROIC)
            || gahzrilla->FindCurrentSpellBySpellId(ZfPool::SPELL_GZ_CALL_THE_WATERS);
        if (calling && !_callSeen)
        {
            _callSeen = true;
            StartHeadCast(head);
        }
        else if (!calling)
            _callSeen = false;

        // Raven takes the head's cast (the group takes his).
        if (!_headCasting || _ravenTried || _clock.Now() < _headCastAt + Tune::kRavenKickDelayMs)
            return;
        _ravenTried = true;
        Creature* raven = Crew(CREW_RAVEN);
        bool const alive = raven && raven->IsAlive();
        bool const melee = alive && raven->IsWithinMeleeRange(gahzrilla);
        if (!RavenCanKick(alive && Able(CREW_RAVEN, raven), melee, _clock.Now() - _headCastAt))
        {
            LogHm("raven-kick-missed", Acore::StringFormat("alive={} melee={} wet={} stunned={}", alive ? 1 : 0,
                melee ? 1 : 0, alive && fight.IsWater(raven) ? 1 : 0, alive && Stunned(CREW_RAVEN, raven) ? 1 : 0));
            return;
        }
        raven->SetFacingToObject(gahzrilla);
        raven->HandleEmoteCommand(EMOTE_ONESHOT_ATTACK1H);
        head->InterruptNonMeleeSpells(false);
        ++_counts.ravenKicks;
        LogHm("raven-kick");
    }

    PoolFight* _fight;
    Map* _map = nullptr;
    HardModeClock _clock;
    bool _ended = false;
    bool _delugeSeen = false;
    uint32 _alive = 0;
    uint32 _pendingDeaths = 0;
    uint32 _chargedTick = 0;
    uint32 _thinkTick = 0;
    std::array<Mate, kCrewCount> _mates{};
    std::vector<Spring> _springs;
    std::vector<MechanicHandle> _handles;
    // GZ16
    WeegliStep _weegli = WeegliStep::Idle;
    ObjectGuid _jobSpring;
    uint64 _stepAt = 0;
    bool _weegliArrived = false;
    bool _plantRestart = false;
    MechanicHandle _blast;
    ObjectGuid _barrel;
    // GZ17, GZ18
    Mark _chosen;
    Mark _over;
    MechanicHandle _overStack;
    // GZ19, GZ21
    uint64 _dispelAt = 0;
    uint64 _healAt = 0;
    uint64 _nextHealAt = 0;
    uint32 _healTarget = 0;
    uint64 _arcAt = 0;
    // GZ20
    ObjectGuid _head;
    bool _callSeen = false;
    bool _headCasting = false;
    bool _ravenTried = false;
    uint64 _headCastAt = 0;
    Counts _counts;
};

// ---------------------------------------------------------------------------------------------------------------------
// The crew's PoolAlly handler (CR's BlyCrew.h): while the package runs it owns their tick; it reports deaths and
// Weegli's arrival at a spring
// ---------------------------------------------------------------------------------------------------------------------

class PoolCrewHandler final : public ZfCrew::CrewModeHandler
{
public:
    bool OnUpdate(ZfCrew::BlyCrewAI& ai, uint32 /*diff*/) override
    {
        return CrewHardMode::Find(ai.Me()->GetMap()) != nullptr;
    }

    void OnDied(ZfCrew::BlyCrewAI& ai, Unit* /*killer*/) override
    {
        if (CrewHardMode* hm = CrewHardMode::Find(ai.Me()->GetMap()))
            hm->NoteDeath(ai.Member());
    }

    // GZ21, section 7 #17 A: a player's heal fills the share of the member it would of a player.
    void OnHealReceived(ZfCrew::BlyCrewAI& ai, Unit* healer, uint32& heal) override
    {
        if (CrewHardMode* hm = CrewHardMode::Find(ai.Me()->GetMap()))
            heal = hm->ScalePlayerHeal(ai.Me(), healer, heal);
    }

    void OnMovementInform(ZfCrew::BlyCrewAI& ai, uint32 type, uint32 id) override
    {
        if (type != POINT_MOTION_TYPE || id != kPointWeegliSpring || !ai.IsWeegli())
            return;
        if (CrewHardMode* hm = CrewHardMode::Find(ai.Me()->GetMap()))
            hm->NoteWeegliArrived();
    }
};

// ---------------------------------------------------------------------------------------------------------------------
// npc_zf_wellspring (301031): a spring that feeds its own puddle (GZ15); attackable, does nothing else
// ---------------------------------------------------------------------------------------------------------------------

struct npc_zf_wellspring : public NullCreatureAI
{
    explicit npc_zf_wellspring(Creature* creature) : NullCreatureAI(creature)
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void JustDied(Unit* /*killer*/) override
    {
        if (CrewHardMode* hm = CrewHardMode::Find(me->GetMap()))
            hm->SpringDied(me->GetGUID());
    }
};

// ---------------------------------------------------------------------------------------------------------------------
// npc_zf_second_head (301032): Gahz'rilla's second head for Twin Call (GZ20): it rides with him (the package moves it),
// casts its own Call the Waters, takes no damage and is never a kill target; it can be kicked
// ---------------------------------------------------------------------------------------------------------------------

struct npc_zf_second_head : public NullCreatureAI
{
    explicit npc_zf_second_head(Creature* creature) : NullCreatureAI(creature)
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void DamageTaken(Unit* /*attacker*/, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*mask*/) override
    {
        damage = 0;
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_HM_TWIN_CALL)
            if (CrewHardMode* hm = CrewHardMode::Find(me->GetMap()))
                hm->HeadCall(me, true);
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_HM_TWIN_CALL)
            if (CrewHardMode* hm = CrewHardMode::Find(me->GetMap()))
                hm->HeadCall(me, false);
    }
};

// ---------------------------------------------------------------------------------------------------------------------
// `.dbtest zf poolcrew <subcommand>`
// ---------------------------------------------------------------------------------------------------------------------
//   info                  the hard mode's slot (8) and Gahz'rilla
//   state                 the package's clock, the five answers in play, each crew member's health / Charged / water
//   spring                GZ15: a Wellspring now (Weegli goes for it)
//   charge                GZ16: Weegli's Blasting Charge on the newest spring now
//   chosen                GZ17: Storm's Chosen on the selected player (else yourself)
//   overcharge            GZ18: Overcharge on the selected player (else yourself)
//   dispel                GZ19: Murta's Mass Dispel now
//   twin                  GZ20: the second head's Call the Waters now (Raven kicks it if she can)
//   devour <member>       GZ21: kill a crew member (bly, raven, oro, weegli, murta): Gahz'rilla eats it

namespace
{
    CrewHardMode* FindPackage(ChatHandler* handler)
    {
        Player* gm = handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
        if (!gm || !ZfTest::RequireZulFarrak(handler))
            return nullptr;
        if (!ZfPool::FindPoolFight(gm->GetMap()))
        {
            handler->SendErrorMessage("{}", "No pool encounter is running (pull Velratha first).");
            return nullptr;
        }
        CrewHardMode* hm = CrewHardMode::Find(gm->GetMap());
        if (!hm)
            handler->SendErrorMessage("{}", "No crew package on this pull: the hard mode was not armed (heroic, the "
                "crew at the pool, `.dbtest zf test hardmode 1` before Velratha's pull).");
        return hm;
    }

    Player* Selected(ChatHandler* handler)
    {
        return handler->GetSession() ? handler->getSelectedPlayerOrSelf() : nullptr;
    }

    bool Done(ChatHandler* handler, std::string const& error, char const* what)
    {
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("The crew at the pool: {}.", what);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return ZfTest::ShowBossInfo(handler, NPC_GAHZRILLA, BOSS_CREW_AT_THE_POOL);
    }

    bool HandleState(ChatHandler* handler)
    {
        CrewHardMode* hm = FindPackage(handler);
        Player* gm = handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
        PoolFight* fight = gm ? ZfPool::FindPoolFight(gm->GetMap()) : nullptr;
        if (!hm || !fight)
            return false;
        handler->PSendSysMessage("The crew at the pool: {}", hm->State(*fight));
        return true;
    }

    bool HandleSpring(ChatHandler* handler)
    {
        CrewHardMode* hm = FindPackage(handler);
        return hm && Done(handler, hm->GmFire(HmAct::Wellspring, nullptr), "a Wellspring");
    }

    bool HandleCharge(ChatHandler* handler)
    {
        CrewHardMode* hm = FindPackage(handler);
        return hm && Done(handler, hm->GmCharge(), "Weegli runs to the newest spring");
    }

    bool HandleChosen(ChatHandler* handler)
    {
        CrewHardMode* hm = FindPackage(handler);
        return hm && Done(handler, hm->GmFire(HmAct::StormsChosen, Selected(handler)), "Storm's Chosen");
    }

    bool HandleOvercharge(ChatHandler* handler)
    {
        CrewHardMode* hm = FindPackage(handler);
        return hm && Done(handler, hm->GmFire(HmAct::Overcharge, Selected(handler)), "Overcharge");
    }

    bool HandleDispel(ChatHandler* handler)
    {
        CrewHardMode* hm = FindPackage(handler);
        return hm && Done(handler, hm->GmDispel(), "Murta's Mass Dispel");
    }

    bool HandleTwin(ChatHandler* handler)
    {
        CrewHardMode* hm = FindPackage(handler);
        return hm && Done(handler, hm->GmTwin(), "the second head's Call the Waters");
    }

    bool HandleDevour(ChatHandler* handler, std::string member)
    {
        CrewHardMode* hm = FindPackage(handler);
        if (!hm)
            return false;
        std::transform(member.begin(), member.end(), member.begin(), [](unsigned char ch) { return std::tolower(ch); });
        for (uint32 m = 0; m < kCrewCount; ++m)
        {
            std::string name = kCrewNames[m];
            std::transform(name.begin(), name.end(), name.begin(), [](unsigned char ch) { return std::tolower(ch); });
            if (name == member)
                return Done(handler, hm->GmDevour(m), "a crew member falls");
        }
        handler->SendErrorMessage("{}", "Name one of: bly, raven, oro, weegli, murta.");
        return false;
    }

    ChatCommandTable const& PoolcrewTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,       SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,      SEC_GAMEMASTER, Console::No },
            { "spring",     HandleSpring,     SEC_GAMEMASTER, Console::No },
            { "charge",     HandleCharge,     SEC_GAMEMASTER, Console::No },
            { "chosen",     HandleChosen,     SEC_GAMEMASTER, Console::No },
            { "overcharge", HandleOvercharge, SEC_GAMEMASTER, Console::No },
            { "dispel",     HandleDispel,     SEC_GAMEMASTER, Console::No },
            { "twin",       HandleTwin,       SEC_GAMEMASTER, Console::No },
            { "devour",     HandleDevour,     SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_gahzrilla_crew_hard_mode()
{
    ZfPool::RegisterPoolHardMode(ZfPool::PoolPackage::Crew, [](PoolFight& fight)
    {
        return std::make_unique<CrewHardMode>(fight);
    });
    ZfCrew::RegisterCrewModeHandler(CrewMode::PoolAlly, [](ZfCrew::BlyCrewAI& /*ai*/)
    {
        return std::make_unique<PoolCrewHandler>();
    });
    RegisterDungeonReworkCreatureAI(npc_zf_wellspring, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_zf_second_head, ZulFarrakRework::kInstanceScriptName);
    ZfTest::RegisterBoss("poolcrew", PoolcrewTestCommands());
}
