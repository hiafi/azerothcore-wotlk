/*
 * mod-dungeon-bosses, Scarlet Monastery D4H: Bloodmage Thalnos's hard mode, the Desecration (heroic only). Build spec:
 * docs/dungeons/scarlet-monastery-1-graveyard.md "Hard mode" and "Build spec" (TH7, TH8, RH1-RH6, "The Desecration"),
 * handoff sections 3.6, 3.7 row D4H, 3.8 (the lawn), 7 #18 A. It fights on D4's AI (boss_bloodmage_thalnos_rework)
 * through ThalnosFight.h: D4 makes one Desecration per heroic pull with DATA_HARD_MODE_THALNOS lit and calls its hooks;
 * the idle hook keeps his red aura while the flag is lit. Pure rules and numbers: ThalnosHardModeLogic.h.
 *
 *   Trigger      four gravestones on the lawn disc (GOs 301310-301313, go_sm_desecration_stone; heroic only by their
 *                spawn mask) read their epitaph by gossip and offer "Disturb the Grave" (a 2 s cast of the player's on
 *                the stone) out of combat, while the council is dead and Thalnos neither fights nor is dead. The
 *                instance keeps the touch order and judges the fourth (Galvar, Fairbell, Voss, Goodchilde). A touched
 *                stone stirs (a faint glow, no right or wrong signal). Right: the flag is lit (saved, the loot bit),
 *                all four bleed red, Thalnos yells line 4 and wears the red aura. Wrong: the stones go dark and three
 *                Haunting Phantasms (6427) rise on the lawn and attack. The blood rite (GO 301314, go_sm_blood_rite)
 *                in the z 0 court reads the order in other words.
 *   The pull     360k (back on a wipe), the red aura, Blood Pact's ward (no risen yet), the loot bit (rule 1; the
 *                instance keeps it too).
 *   TH7          at 75%: line 1, a 3 s Arcane bar (no kick), then every fight player within 60 yd of him (the crypt,
 *                its stair, the court) and Thalnos land on the lawn disc (1798.5, 1348.5); SetGround(Lawn) the same
 *                tick; the crypt's pools stay behind. Once everyone has arrived (2 s at most), Galvar and Fairbell
 *                rise.
 *   The risen    each rises at its own stone (Raise Dead's look), joins the fight (every fight player at 0 threat, the
 *                tank first: rule 19). Voss 20 s later, Goodchilde 20 s after that, then every 20 s the first dead one.
 *                Each channels a red tether into Thalnos (Blood Siphon's look).
 *   TH8          Blood Pact: one stack per living risen on Thalnos, 20% less damage taken each (80% with four).
 *   RH1          Galvar, 5 s then every 25 s: line 0, a banner at his feet for 30 s; Thalnos and the risen within 10 yd
 *                deal 25% more damage (the Rallied buff); a 10 yd zone only the tank is eligible for (the drag).
 *   RH2          Galvar, 8 s then every 15 s: the farthest player on the lawn, a 5 yd marker for 2 s, he charges onto
 *                it: 30% Physical and Weakened to everyone inside.
 *   RH3          Fairbell, 6 s then every 12 s: Repent, a 2 s Holy cast (kick: a reward), 2 s incapacitate.
 *   RH4 / RH5    Voss: Greater Heal 4 s then every 12 s, a 3 s Holy cast on the most wounded ally, 10% of its health
 *                (kick: expected); Power Word: Shield 10 s then every 20 s, a 5k absorb on an ally without it (purge).
 *   RH6          Goodchilde, 6 s then every 20 s: line 0, a 2 s wind-up in place, 4 s spinning: 30% Physical and
 *                Weakened each second within 8 yd (the tank included).
 *   Stacks       the risen's ability hits on players feed Blood Ritual (Repent, the charge, the spin: once per player
 *                per cast); their melee does not (designer question).
 *   The end      a wipe: the risen, the banners and the tethers go with D4's cleanup, he returns to the crypt (D4),
 *                the flag stays; his death: the instance records BOSS_DESECRATION and stands portal P1h.
 *
 * Every firing logs one INFO line "sm thalnos desecration-<mechanic> ..." (the fight's) or "sm desecration <...>"
 * (the stones); `.dbtest sm desecration <...>` fires them.
 */

#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "DungeonKitFlex.h"
#include "DungeonKitWard.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "ScarletMonasteryRework.h"
#include "ScarletMonasteryTestCommand.h"
#include "ScriptMgr.h"
#include "ScriptedCreature.h"
#include "ScriptedGossip.h"
#include "Spell.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ThalnosFight.h"
#include "ThalnosHardModeLogic.h"
#include "ThalnosLogic.h"
#include "ThreatManager.h"
#include "WorldSession.h"
#include <array>
#include <atomic>
#include <cmath>
#include <memory>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScarletMonasteryRework;
using namespace SmDesecration;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using SmThalnos::Ground;
using SmThalnos::ThalnosFight;
using SmThalnos::ThalnosHardMode;

namespace
{
    char const* const kStoneLogName = "desecration";

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(ms);
    }

    void LogStone(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kStoneLogName, mechanic, detail);
    }

    bool SpellExists(uint32 spellId)
    {
        return sSpellMgr->GetSpellInfo(spellId) != nullptr;
    }

    bool StalkerExists()
    {
        return sObjectMgr->GetCreatureTemplate(NPC_SM_STALKER) != nullptr;
    }

    // The floor under (x, y) near `z`; `z` when the probe finds nothing close (the lawn's NAVMESH heights).
    float FloorZ(WorldObject const* ref, float x, float y, float z)
    {
        float const found = ref->GetMap()->GetHeight(ref->GetPhaseMask(), x, y, z + 3.f, true, 8.f);
        return (found > INVALID_HEIGHT && std::fabs(found - z) <= 4.f) ? found : z;
    }

    Position LawnPosition(WorldObject const* ref, float x, float y, float z, float o)
    {
        return Position(x, y, FloorZ(ref, x, y, z), o);
    }

    Position LawnCenter()
    {
        return Position(SmThalnos::kLawnCenter.x, SmThalnos::kLawnCenter.y, kCouncilLawn.z, 0.f);
    }

    // The bots' hard bounds on the lawn (D4's: 30 yd round the disc).
    BossMechanics::SpotBounds LawnBounds()
    {
        return BossMechanics::SpotBounds().Circle(LawnCenter(), SmThalnos::kLawnBoundsYd, SmThalnos::kLawnZMin,
            SmThalnos::kLawnZMax);
    }

    bool OnLawn(WorldObject const* o)
    {
        return o && SmThalnos::OnLawnFloor(DungeonKit::PlaneOf(o), o->GetPositionZ());
    }

    // A regular cast in progress (the tether is a channel that allows actions: it never counts).
    bool BusyCasting(Unit const* unit)
    {
        Spell const* spell = unit->GetCurrentSpell(CURRENT_GENERIC_SPELL);
        return spell && spell->getState() != SPELL_STATE_FINISHED;
    }

    bool CanAct(Creature const* unit)
    {
        return unit && unit->IsAlive() && unit->IsInWorld() && !BusyCasting(unit)
            && !unit->HasUnitState(UNIT_STATE_LOST_CONTROL);
    }

    void Notify(Player* player, char const* text)
    {
        if (player && player->GetSession() && text && *text)
            ChatHandler(player->GetSession()).SendNotification(text);
    }

    Creature* ThalnosOf(WorldObject* where)
    {
        InstanceScript* instance = where ? where->GetInstanceScript() : nullptr;
        if (!instance)
            return nullptr;
        return where->GetMap()->GetCreature(instance->GetGuidData(kGuidBossBase + BOSS_THALNOS));
    }

    ThalnosFight* FightOf(Creature* thalnos)
    {
        if (!thalnos || !thalnos->IsAIEnabled)
            return nullptr;
        return dynamic_cast<ThalnosFight*>(thalnos->AI());
    }

    // The idle hook (D4: alive, not engaged, not evading): the red aura while the flag is lit on heroic.
    void IdleLook(Creature* boss)
    {
        if (!SpellExists(SPELL_DS_HARD_MODE_AURA))
            return;
        InstanceScript* instance = boss->GetInstanceScript();
        bool const lit = instance && DungeonKit::IsHeroicMap(boss) && instance->GetData(DATA_HARD_MODE_THALNOS) != 0;
        bool const has = boss->HasAura(SPELL_DS_HARD_MODE_AURA);
        if (lit && !has)
            boss->CastSpell(boss, SPELL_DS_HARD_MODE_AURA, true);
        else if (!lit && has)
            boss->RemoveAurasDueToSpell(SPELL_DS_HARD_MODE_AURA);
    }
}

// -------------------------------------------------------------------------------------------------------------------
// The hard mode of one pull (D4 makes it at a heroic pull with the Desecration answered and ends it with the pull)
// -------------------------------------------------------------------------------------------------------------------

class Desecration final : public ThalnosHardMode
{
public:
    enum class Stage : uint8
    {
        Crypt,          // before 75%
        Casting,        // the 3 s bar
        Arriving,       // landed; the risen wait for everyone
        Yard,           // the risen rise
    };

    // ---- the pull ---------------------------------------------------------------------------------------------------

    void OnEngage(ThalnosFight& fight) override
    {
        Creature* boss = fight.Thalnos();
        _baseHealth = boss->GetMaxHealth();
        DungeonKit::Flex::SetHealth(boss, kThalnosHardModeHealth, true);
        DungeonKit::SetHardModeLoot(boss, true);            // rule 1: at the pull (the instance keeps it too)
        if (SpellExists(SPELL_DS_HARD_MODE_AURA) && !boss->HasAura(SPELL_DS_HARD_MODE_AURA))
            boss->CastSpell(boss, SPELL_DS_HARD_MODE_AURA, true);
        StartWard(boss);
        fight.Log("desecration-engage", Acore::StringFormat("health={} base={} threshold={:.0f} players={}",
            boss->GetMaxHealth(), _baseHealth, SmThalnos::kNoRestPct, fight.FightPlayers().size()));
    }

    void OnThreshold(ThalnosFight& fight) override
    {
        StartNoRest(fight, "threshold");
    }

    void OnUpdate(ThalnosFight& fight, uint32 diff) override
    {
        Creature* boss = fight.Thalnos();
        uint64 const now = fight.FightMs();
        _ward.Update(boss, diff);
        switch (_stage)
        {
            case Stage::Casting:
                if (now >= _teleportAtMs)
                    Teleport(fight);
                break;
            case Stage::Arriving:
                if (Arrived(boss) || now >= _arriveByMs)
                    Landed(fight);
                break;
            case Stage::Yard:
                if (std::optional<Hero> h = _rise.Due(now, AliveNow(boss)))
                    Raise(fight, *h);
                break;
            default:
                break;
        }
        if (_stage == Stage::Yard)
            for (Hero h : kHeroes)
                UpdateRisen(fight, h, now);
        UpdateRally(fight, diff);
        UpdateTethers(boss, diff);
    }

    // TH8: 20% less per living risen (the ward counts; the aura is the look).
    void OnDamageTaken(ThalnosFight& /*fight*/, Unit* /*attacker*/, uint32& damage) override
    {
        _ward.Mitigate(damage);
    }

    void OnSummonDied(ThalnosFight& fight, Creature* summon, Unit* killer) override
    {
        std::optional<Hero> const h = summon ? HeroOfEntry(summon->GetEntry()) : std::nullopt;
        if (!h)
            return;
        ++_risenKilled;
        // A dead Galvar lands no charge, a dead Goodchilde spins no more.
        RisenState& r = _risen[IndexOf(*h)];
        for (MechanicHandle* handle : { &r.chargeZone, &r.spinZone })
            if (*handle)
            {
                Mechanic::Cancel(fight.Thalnos(), *handle);
                *handle = MechanicHandle();
            }
        AliveMask const alive = AliveNow(fight.Thalnos());
        fight.Log("desecration-risen-died", Acore::StringFormat("hero={} killer={} alive={} pact={:.0f}%", NameOf(*h),
            killer ? killer->GetName() : std::string("none"), CountAlive(alive), _ward.ReductionPct()));
    }

    void ConfigureDescriptor(ThalnosFight& /*fight*/, BossMechanics::Descriptor& d) override
    {
        // The kill order: Voss, Fairbell, Galvar, Goodchilde, then Thalnos (0). Blood Pact enforces it.
        for (Hero h : kHeroes)
            d.targets.push_back(BossMechanics::TargetEntry(EntryOf(h), KillPriority(h), BossMechanics::Who::Dps));
        // Repent a reward, Greater Heal expected (a heal on Thalnos is a lasting setback); never the tether.
        d.interrupts.push_back(BossMechanics::InterruptEntry(NPC_SM_FAIRBELL, SPELL_DS_REPENT, 1,
            Ms(kRepentBeat.everyMs)));
        d.interrupts.push_back(BossMechanics::InterruptEntry(NPC_SM_VOSS, SPELL_DS_GREATER_HEAL, 3,
            Ms(kHealBeat.everyMs)));
        d.interrupts.push_back(BossMechanics::InterruptEntry(0, SPELL_DS_PACT_TETHER, 0));
        // Voss's shield: a purge reward.
        d.purges.push_back(BossMechanics::PurgeEntry(0, SPELL_DS_POWER_WORD_SHIELD, 1));
        // The banner is scenery (not selectable).
        d.ignores.push_back(BossMechanics::IgnoreEntry(NPC_SM_RALLYING_BANNER));
    }

    // Death (died), evade or reset; D4 then despawns his summons (the risen, the banners) and cancels the tracked
    // shapes, and puts him back in the crypt on a lawn evade.
    void OnEnd(ThalnosFight& fight, bool died) override
    {
        Creature* boss = fight.Thalnos();
        _ward.Stop(boss);
        boss->RemoveAurasDueToSpell(SPELL_DS_BLOOD_PACT);
        boss->RemoveAurasDueToSpell(SPELL_DS_RALLIED);
        for (Hero h : kHeroes)
            if (Creature* risen = Risen(boss, h))
                risen->DespawnOrUnsummon();
        if (InstanceScript* instance = boss->GetInstanceScript())
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_DS_REPENT);
        if (!died && _baseHealth)
            DungeonKit::Flex::SetHealth(boss, _baseHealth, true);
        _rise.Stop();
        fight.Log("desecration-end", Acore::StringFormat("died={} stage={} rises={} risen-killed={} banners={} "
            "charges={} repents={} heals={} heals-kicked={} shields={} spins={}", died ? 1 : 0, StageName(_stage),
            _rises, _risenKilled, _banners, _charges, _repents, _heals, _healsKicked, _shields, _spins));
        _stage = Stage::Crypt;
    }

    // ---- what the risen's AI forwards -----------------------------------------------------------------------------

    // A risen's spell hit a unit: Repent on a player feeds Blood Ritual; the heal logs.
    void RisenSpellHit(ThalnosFight& fight, Creature* risen, Unit* target, SpellInfo const* spell)
    {
        if (!spell || !target)
            return;
        if (spell->Id == SPELL_DS_REPENT && target->IsPlayer())
            fight.AddRitualStacks(1, "repent");
        else if (spell->Id == SPELL_DS_GREATER_HEAL)
            fight.Log("desecration-heal-lands", Acore::StringFormat("by={} on={} health={:.1f}", risen->GetName(),
                target->GetName(), target->GetHealthPct()));
    }

    void RisenSpellFailed(ThalnosFight& fight, Creature* risen, SpellInfo const* spell)
    {
        if (!spell)
            return;
        if (spell->Id == SPELL_DS_GREATER_HEAL)
        {
            ++_healsKicked;
            fight.Log("desecration-heal-kicked", Acore::StringFormat("by={}", risen->GetName()));
        }
        else if (spell->Id == SPELL_DS_REPENT)
            fight.Log("desecration-repent-kicked", Acore::StringFormat("by={}", risen->GetName()));
    }

    // ---- `.dbtest sm desecration` -------------------------------------------------------------------------------

    bool TestTeleport(ThalnosFight& fight)
    {
        return StartNoRest(fight, "gm");
    }

    // Raises `h` now on the lawn (the yard stage only).
    bool TestRise(ThalnosFight& fight, Hero h)
    {
        if (_stage != Stage::Yard)
            return false;
        if (Creature* risen = Risen(fight.Thalnos(), h))
            if (risen->IsAlive())
                return false;
        return Raise(fight, h) != nullptr;
    }

    enum class TestAbility : uint8
    {
        Banner,
        Charge,
        Repent,
        Heal,
        Shield,
        Whirlwind,
    };

    // An empty string when fired; otherwise why not.
    std::string TestFire(ThalnosFight& fight, TestAbility a, Player* on)
    {
        Creature* boss = fight.Thalnos();
        uint64 const now = fight.FightMs();
        auto need = [this, boss](Hero h) -> Creature*
        {
            Creature* risen = Risen(boss, h);
            return risen && CanAct(risen) ? risen : nullptr;
        };
        switch (a)
        {
            case TestAbility::Banner:
                if (Creature* galvar = need(Hero::Galvar))
                    return PlantBanner(fight, galvar) ? std::string() : "The banner did not plant (see the log).";
                return "Galvar is not standing (or is busy).";
            case TestAbility::Charge:
                if (Creature* galvar = need(Hero::Galvar))
                    return StartCharge(fight, galvar, now, on) ? std::string() : "Nobody on the lawn to charge.";
                return "Galvar is not standing (or is busy).";
            case TestAbility::Repent:
                if (Creature* fairbell = need(Hero::Fairbell))
                    return CastRepent(fight, fairbell, on) ? std::string() : "Repent did not start (see the log).";
                return "Fairbell is not standing (or is busy).";
            case TestAbility::Heal:
                if (Creature* voss = need(Hero::Voss))
                    return CastHeal(fight, voss) ? std::string() : "Greater Heal did not start (see the log).";
                return "Voss is not standing (or is busy).";
            case TestAbility::Shield:
                if (Creature* voss = need(Hero::Voss))
                    return CastShield(fight, voss) ? std::string() : "Every ally is shielded already.";
                return "Voss is not standing (or is busy).";
            case TestAbility::Whirlwind:
                if (Creature* goodchilde = need(Hero::Goodchilde))
                    return StartWhirlwind(fight, goodchilde, now) ? std::string() : "The spin did not start.";
                return "Goodchilde is not standing (or is busy).";
        }
        return "Unknown ability.";
    }

    std::string TestState(ThalnosFight& fight)
    {
        Creature* boss = fight.Thalnos();
        uint64 const now = fight.FightMs();
        std::string risen;
        for (Hero h : kHeroes)
        {
            Creature* r = Risen(boss, h);
            risen += Acore::StringFormat(" {}={}", NameOf(h), r && r->IsAlive()
                ? Acore::StringFormat("{}/{}", r->GetHealth(), r->GetMaxHealth()) : std::string("down"));
        }
        return Acore::StringFormat("clock={}s stage={} ground={} health={}/{} pact={:.0f}% next-rise={} banners={}{} "
            "rises={} killed={}", now / 1000, StageName(_stage),
            fight.CurrentGround() == Ground::Lawn ? "lawn" : "crypt", boss->GetHealth(), boss->GetMaxHealth(),
            _ward.ReductionPct(), _rise.On() && _rise.DueMs() > now ? Acore::StringFormat("{}s",
                (_rise.DueMs() - now) / 1000) : std::string("-"), _bannerList.size(), risen, _rises, _risenKilled);
    }

private:
    struct RisenState
    {
        ObjectGuid guid;
        uint64 aDueMs = 0;              // Galvar's banner, Fairbell's Repent, Voss's heal, Goodchilde's spin
        uint64 bDueMs = 0;              // Galvar's charge, Voss's shield
        // Galvar's charge in flight
        bool chargePending = false;
        uint64 chargeMoveAtMs = 0;
        Position chargeSpot;
        MechanicHandle chargeZone;
        // Goodchilde's spin
        uint64 spinAtMs = 0;            // the wind-up ends, the spin starts
        uint64 spinEndMs = 0;           // he walks again
        GuidSet spinHit;
        MechanicHandle spinZone;
    };

    struct Banner
    {
        ObjectGuid guid;
        Position at;
        uint64 endMs = 0;
    };

    static char const* StageName(Stage s)
    {
        switch (s)
        {
            case Stage::Crypt:      return "crypt";
            case Stage::Casting:    return "casting";
            case Stage::Arriving:   return "arriving";
            case Stage::Yard:       return "yard";
        }
        return "?";
    }

    static uint32 CountAlive(AliveMask const& alive)
    {
        uint32 n = 0;
        for (bool a : alive)
            n += a ? 1 : 0;
        return n;
    }

    Creature* Risen(Creature* boss, Hero h) const
    {
        ObjectGuid const guid = _risen[IndexOf(h)].guid;
        return guid && boss && boss->IsInWorld() ? boss->GetMap()->GetCreature(guid) : nullptr;
    }

    AliveMask AliveNow(Creature* boss) const
    {
        AliveMask alive{};
        for (Hero h : kHeroes)
        {
            Creature* risen = Risen(boss, h);
            alive[IndexOf(h)] = risen && risen->IsAlive();
        }
        return alive;
    }

    // Runs `fn(desecration, fight)` when the registry calls back, if the pull's hard mode is still this one: same
    // object AND same pull serial (a new Desecration allocated at a freed one's address never takes a stale callback;
    // R-1-GY N-1). Captures the map and guids only.
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnFight(Creature* boss, Fn fn)
    {
        Map* map = boss->GetMap();
        ObjectGuid const guid = boss->GetGUID();
        uint64 const serial = _serial;
        return [map, guid, serial, fn](BossMechanics::ResolveResult const& result)
        {
            Creature* thalnos = map ? map->GetCreature(guid) : nullptr;
            ThalnosFight* fight = FightOf(thalnos);
            Desecration* self = fight ? dynamic_cast<Desecration*>(fight->ActiveHardMode()) : nullptr;
            if (self && self->_serial == serial)
                fn(*self, *fight, result);
        };
    }

    // ---- TH8 Blood Pact ---------------------------------------------------------------------------------------------

    void StartWard(Creature* boss)
    {
        DungeonKit::WardSpec spec;
        spec.aura = SpellExists(SPELL_DS_BLOOD_PACT) ? uint32(SPELL_DS_BLOOD_PACT) : 0u;
        spec.pctPerAdd = kPactPctPerRisen;
        spec.capPct = kPactCapPct;
        spec.auraCarriesReduction = false;      // the aura is the look and the count; OnDamageTaken mitigates
        spec.addEntries = { NPC_SM_GALVAR, NPC_SM_FAIRBELL, NPC_SM_VOSS, NPC_SM_GOODCHILDE };
        spec.searchYd = 100.f;
        spec.onLink = [](Creature* thalnos, Creature* risen) { Tether(thalnos, risen); };
        spec.onUnlink = [](Creature* thalnos, ObjectGuid risenGuid)
        {
            if (Creature* risen = thalnos->GetMap()->GetCreature(risenGuid))
                if (risen->IsAlive())
                    risen->InterruptSpell(CURRENT_CHANNELED_SPELL, false);
        };
        spec.dungeon = kLogDungeon;
        spec.boss = "thalnos";
        _ward.Stop(boss);
        _ward.Start(boss, std::move(spec));
    }

    // A risen's red tether into him (a channel that allows actions: it moves, swings and casts through it). Never
    // started over a cast (a new channel would break it).
    static void Tether(Creature* thalnos, Creature* risen)
    {
        if (!thalnos || !risen || !risen->IsAlive() || !SpellExists(SPELL_DS_PACT_TETHER) || BusyCasting(risen))
            return;
        if (thalnos->HasAura(SPELL_DS_PACT_TETHER, risen->GetGUID()))
            return;
        risen->CastSpell(thalnos, SPELL_DS_PACT_TETHER, true);
    }

    void UpdateTethers(Creature* boss, uint32 diff)
    {
        if (_tetherMs > diff)
        {
            _tetherMs -= diff;
            return;
        }
        _tetherMs = kTetherCheckMs;
        for (Hero h : kHeroes)
            if (Creature* risen = Risen(boss, h))
                Tether(boss, risen);
    }

    // ---- TH7 No Rest for the Angry Dead -----------------------------------------------------------------------------

    bool StartNoRest(ThalnosFight& fight, char const* why)
    {
        if (_stage != Stage::Crypt)
            return false;
        Creature* boss = fight.Thalnos();
        uint64 const now = fight.FightMs();
        fight.StopCasting("no-rest");
        fight.HoldBeats(now + kNoRestCastMs + kArrivalMaxMs);
        fight.Say(SmThalnos::SAY_NO_REST);
        boss->StopMoving();
        if (SpellExists(SPELL_DS_NO_REST))
        {
            SpellCastResult const result = boss->CastSpell(boss, SPELL_DS_NO_REST, false);
            if (result != SPELL_CAST_OK)
                fight.Log("desecration-no-rest-bar-refused", Acore::StringFormat("result={}", uint32(result)));
        }
        _teleportAtMs = now + kNoRestCastMs;
        _stage = Stage::Casting;
        fight.Log("desecration-no-rest", Acore::StringFormat("why={} health={:.1f} in={}ms", why, boss->GetHealthPct(),
            kNoRestCastMs));
        return true;
    }

    // Every fight player near him (the crypt, its stair, the court) and Thalnos to the lawn; the ground follows the
    // same tick (D4: the leash, the bots' bounds, the spike's room, the Lance, the nova's targets).
    void Teleport(ThalnosFight& fight)
    {
        Creature* boss = fight.Thalnos();
        uint64 const now = fight.FightMs();
        if (boss->HasUnitState(UNIT_STATE_CASTING))
            boss->InterruptNonMeleeSpells(false);

        std::vector<Player*> gathered;
        for (Player* player : fight.FightPlayers())
            if (player->IsWithinDist(boss, kTeleportGatherYd) && !player->IsBeingTeleported())
                gathered.push_back(player);
        _sent.clear();
        uint32 const count = static_cast<uint32>(gathered.size());
        for (uint32 i = 0; i < count; ++i)
        {
            Player* player = gathered[i];
            Point4 const land = PlayerLanding(i, count);
            Position const at = LawnPosition(boss, land.x, land.y, land.z, land.o);
            if (player->GetVehicle())
                player->ExitVehicle();
            player->NearTeleportTo(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), at.GetOrientation(),
                false, false, true);
            _sent.push_back(player->GetGUID());
        }
        Position const center = LawnPosition(boss, kLawnLanding.x, kLawnLanding.y, kCouncilLawn.z,
            ThalnosLandingFacing());
        boss->NearTeleportTo(center.GetPositionX(), center.GetPositionY(), center.GetPositionZ(),
            center.GetOrientation());
        fight.SetGround(Ground::Lawn, "no-rest");
        fight.HoldBeats(now + kArrivalMaxMs);
        _arriveByMs = now + kArrivalMaxMs;
        _stage = Stage::Arriving;
        fight.Log("desecration-teleport", Acore::StringFormat("players={} fight-players={} to=({:.1f}, {:.1f}, {:.1f})",
            count, fight.FightPlayers().size(), center.GetPositionX(), center.GetPositionY(),
            center.GetPositionZ()));
    }

    // Everyone sent is on the lawn and done teleporting (or gone, or dead).
    bool Arrived(Creature* boss) const
    {
        for (ObjectGuid const& guid : _sent)
        {
            Player* player = ObjectAccessor::GetPlayer(*boss, guid);
            if (!player || !player->IsInWorld() || !player->IsAlive() || !player->IsInMap(boss))
                continue;
            if (player->IsBeingTeleported() || !OnLawn(player))
                return false;
        }
        return true;
    }

    void Landed(ThalnosFight& fight)
    {
        uint64 const now = fight.FightMs();
        _stage = Stage::Yard;
        std::string names;
        for (Hero h : _rise.Start(now))
            if (Raise(fight, h))
                names += Acore::StringFormat(" {}", NameOf(h));
        fight.Log("desecration-landed", Acore::StringFormat("after={}ms risen:{}", now + kArrivalMaxMs - _arriveByMs,
            names));
    }

    // ---- the rising -------------------------------------------------------------------------------------------------

    Creature* Raise(ThalnosFight& fight, Hero h)
    {
        Creature* boss = fight.Thalnos();
        uint64 const now = fight.FightMs();
        Point4 const s = RiseSpot(h);
        TempSummon* risen = boss->SummonCreature(EntryOf(h), LawnPosition(boss, s.x, s.y, s.z, s.o),
            TEMPSUMMON_CORPSE_TIMED_DESPAWN, kRisenCorpseMs);
        if (!risen)
        {
            fight.Log("desecration-rise-failed", Acore::StringFormat("hero={} entry={}", NameOf(h), EntryOf(h)));
            return nullptr;
        }
        RisenState& r = _risen[IndexOf(h)];
        r = RisenState();
        r.guid = risen->GetGUID();
        switch (h)
        {
            case Hero::Galvar:
                r.aDueMs = now + kBannerBeat.firstMs;
                r.bDueMs = now + kChargeBeat.firstMs;
                break;
            case Hero::Fairbell:
                r.aDueMs = now + kRepentBeat.firstMs;
                break;
            case Hero::Voss:
                r.aDueMs = now + kHealBeat.firstMs;
                r.bDueMs = now + kShieldBeat.firstMs;
                break;
            case Hero::Goodchilde:
                r.aDueMs = now + kWhirlwindBeat.firstMs;
                break;
        }
        if (SpellExists(SPELL_DS_RISE))
            risen->CastSpell(risen, SPELL_DS_RISE, true);
        // Every fight player at 0 threat (rule 11), the tank first (rule 19), the ward's count and the tether.
        fight.JoinFight(risen);
        Unit* tank = boss->GetVictim();
        Unit* first = tank && tank->IsAlive() ? tank : nullptr;
        if (!first)
            if (Player* nearest = NearestOnLawn(fight, risen))
                first = nearest;
        if (first)
        {
            risen->GetThreatMgr().AddThreat(first, 1.f, nullptr, true, true);
            if (risen->IsAIEnabled)
                risen->AI()->AttackStart(first);
        }
        _ward.Link(boss, risen);
        ++_rises;
        AliveMask const alive = AliveNow(boss);
        fight.Log("desecration-rise", Acore::StringFormat("hero={} at=({:.1f}, {:.1f}) health={} alive={} pact={:.0f}% "
            "first={} rises={}", NameOf(h), risen->GetPositionX(), risen->GetPositionY(), risen->GetMaxHealth(),
            CountAlive(alive), _ward.ReductionPct(), first ? first->GetName() : std::string("none"), _rises));
        return risen;
    }

    static Player* NearestOnLawn(ThalnosFight& fight, Creature* from)
    {
        Player* best = nullptr;
        for (Player* player : fight.PlayersOnGround())
            if (!best || from->GetExactDist2d(player) < from->GetExactDist2d(best))
                best = player;
        return best;
    }

    // ---- the risen's beats ------------------------------------------------------------------------------------------

    void UpdateRisen(ThalnosFight& fight, Hero h, uint64 now)
    {
        Creature* boss = fight.Thalnos();
        Creature* risen = Risen(boss, h);
        if (!risen || !risen->IsAlive())
            return;
        RisenState& r = _risen[IndexOf(h)];

        // A chase off the lawn: back to its stone, at the tank again.
        if (RisenOffLawn(DungeonKit::PlaneOf(risen)))
        {
            Point4 const s = RiseSpot(h);
            Position const at = LawnPosition(boss, s.x, s.y, s.z, s.o);
            risen->NearTeleportTo(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), at.GetOrientation());
            if (Unit* tank = boss->GetVictim())
                if (risen->IsAIEnabled)
                    risen->AI()->AttackStart(tank);
            fight.Log("desecration-risen-leash", Acore::StringFormat("hero={}", NameOf(h)));
        }

        if (h == Hero::Galvar && r.chargePending && now >= r.chargeMoveAtMs)
        {
            r.chargePending = false;
            if (SpellExists(SPELL_DS_CHARGE_LOOK))
                risen->CastSpell(risen, SPELL_DS_CHARGE_LOOK, true);
            risen->GetMotionMaster()->MoveCharge(r.chargeSpot.GetPositionX(), r.chargeSpot.GetPositionY(),
                r.chargeSpot.GetPositionZ(), kChargeSpeed, EVENT_CHARGE, nullptr, true);
        }
        if (h == Hero::Goodchilde && r.spinAtMs)
        {
            if (now >= r.spinAtMs)
            {
                r.spinAtMs = 0;
                if (SpellExists(SPELL_DS_WHIRLWIND))
                    risen->CastSpell(risen, SPELL_DS_WHIRLWIND, true);
            }
        }
        if (h == Hero::Goodchilde && r.spinEndMs && now >= r.spinEndMs)
        {
            r.spinEndMs = 0;
            risen->SetControlled(false, UNIT_STATE_ROOT);
            if (Unit* victim = risen->GetVictim())
                risen->GetMotionMaster()->MoveChase(victim);
        }
        if (r.spinEndMs || !CanAct(risen))
            return;

        switch (h)
        {
            case Hero::Galvar:
                if (now >= r.aDueMs)
                    r.aDueMs = now + (PlantBanner(fight, risen) ? kBannerBeat.everyMs : kHeroRetryMs);
                else if (now >= r.bDueMs && !r.chargePending)
                    r.bDueMs = now + (StartCharge(fight, risen, now, nullptr) ? kChargeBeat.everyMs : kHeroRetryMs);
                break;
            case Hero::Fairbell:
                if (now >= r.aDueMs)
                    r.aDueMs = now + (CastRepent(fight, risen, nullptr) ? kRepentBeat.everyMs : kHeroRetryMs);
                break;
            case Hero::Voss:
                if (now >= r.aDueMs)
                    r.aDueMs = now + (CastHeal(fight, risen) ? kHealBeat.everyMs : kHeroRetryMs);
                else if (now >= r.bDueMs)
                    r.bDueMs = now + (CastShield(fight, risen) ? kShieldBeat.everyMs : kHeroRetryMs);
                break;
            case Hero::Goodchilde:
                if (now >= r.aDueMs)
                    r.aDueMs = now + (StartWhirlwind(fight, risen, now) ? kWhirlwindBeat.everyMs : kHeroRetryMs);
                break;
        }
    }

    // ---- RH1 Rallying Banner ----------------------------------------------------------------------------------------

    bool PlantBanner(ThalnosFight& fight, Creature* galvar)
    {
        Creature* boss = fight.Thalnos();
        Position const at = LawnPosition(galvar, galvar->GetPositionX(), galvar->GetPositionY(),
            galvar->GetPositionZ(), galvar->GetOrientation());
        TempSummon* banner = boss->SummonCreature(NPC_SM_RALLYING_BANNER, at, TEMPSUMMON_TIMED_DESPAWN, kBannerMs);
        if (!banner)
        {
            fight.Log("desecration-banner-failed");
            return false;
        }
        banner->SetReactState(REACT_PASSIVE);
        if (galvar->IsAIEnabled)
            galvar->AI()->Talk(EMOTE_RISEN);
        uint64 const now = fight.FightMs();
        _bannerList.push_back({ banner->GetGUID(), at, now + kBannerMs });

        // The drag: a 10 yd zone of no damage only the tank is eligible for (G1 banner-drag).
        BossMechanics::Eligibility tankOnly;
        tankOnly.roles = BossMechanics::Role::Tank;
        MechanicRef ref = Mechanic::Zone(boss, BossMechanics::Shapes::Circle(BossMechanics::Anchor(at),
            kBannerRadius), Ms(kBannerWarnMs));
        ref.Persistent(Ms(kBannerMs - kBannerWarnMs), Ms(kBannerTickMs)).Damage(0.f).Eligible(tankOnly)
            .Within(LawnBounds()).Tag(RH1);
        fight.Track(ref.Handle());
        ++_banners;
        fight.Log("desecration-banner", Acore::StringFormat("at=({:.1f}, {:.1f}) for={}s standing={}",
            at.GetPositionX(), at.GetPositionY(), kBannerMs / 1000, _bannerList.size()));
        return true;
    }

    // Thalnos and the living risen within 10 yd of a standing banner wear Rallied (refreshed; it drops soon after).
    void UpdateRally(ThalnosFight& fight, uint32 diff)
    {
        if (_rallyMs > diff)
        {
            _rallyMs -= diff;
            return;
        }
        _rallyMs = kRallyRefreshMs;
        Creature* boss = fight.Thalnos();
        uint64 const now = fight.FightMs();
        std::erase_if(_bannerList, [boss, now](Banner const& b)
        {
            Creature* banner = boss->GetMap()->GetCreature(b.guid);
            return now >= b.endMs || !banner || !banner->IsAlive();
        });
        if (_bannerList.empty() || !SpellExists(SPELL_DS_RALLIED))
            return;
        std::vector<Creature*> units{ boss };
        for (Hero h : kHeroes)
            if (Creature* risen = Risen(boss, h))
                if (risen->IsAlive())
                    units.push_back(risen);
        for (Creature* unit : units)
        {
            bool inside = false;
            for (Banner const& b : _bannerList)
                if (unit->GetExactDist2d(b.at.GetPositionX(), b.at.GetPositionY()) <= kBannerRadius)
                    inside = true;
            if (!inside)
                continue;
            if (Aura* aura = unit->GetAura(SPELL_DS_RALLIED))
                aura->RefreshDuration();
            else
                unit->AddAura(SPELL_DS_RALLIED, unit);
        }
    }

    // ---- RH2 Crusader's Charge --------------------------------------------------------------------------------------

    bool StartCharge(ThalnosFight& fight, Creature* galvar, uint64 now, Player* forced)
    {
        Player* target = forced && forced->IsAlive() && OnLawn(forced) ? forced : nullptr;
        if (!target)
            for (Player* player : fight.PlayersOnGround())
                if (!target || galvar->GetExactDist2d(player) > galvar->GetExactDist2d(target))
                    target = player;
        if (!target)
            return false;
        Creature* boss = fight.Thalnos();
        Position const spot = target->GetPosition();
        bool const rallied = galvar->HasAura(SPELL_DS_RALLIED);
        float const pct = Rallied(kChargePct, rallied);
        MechanicRef ref = Mechanic::Zone(boss, BossMechanics::Shapes::Circle(BossMechanics::Anchor(spot),
            kChargeRadius), Ms(kChargeWarnMs));
        ref.Damage(pct).TankDamage(pct).Weakened().Spell(SPELL_DS_CHARGE_HIT).Within(LawnBounds()).Tag(RH2)
            .OnResolve(OnFight(boss, [](Desecration& self, ThalnosFight& f, BossMechanics::ResolveResult const& res)
            {
                self.ChargeLanded(f, res);
            }));
        fight.Track(ref.Handle());
        RisenState& r = _risen[IndexOf(Hero::Galvar)];
        r.chargeZone = ref.Handle();
        float const distance = galvar->GetExactDist2d(spot.GetPositionX(), spot.GetPositionY());
        r.chargePending = true;
        r.chargeSpot = spot;
        r.chargeMoveAtMs = now + ChargeStartMs(distance);
        ++_charges;
        fight.Log("desecration-charge", Acore::StringFormat("target={} distance={:.1f} pct={:.1f} rallied={}",
            target->GetName(), distance, pct, rallied ? 1 : 0));
        return true;
    }

    void ChargeLanded(ThalnosFight& fight, BossMechanics::ResolveResult const& result)
    {
        if (result.fizzled)
            return;
        uint32 hits = 0;
        for (ObjectGuid const& g : result.hits)
            hits += g.IsPlayer() ? 1 : 0;
        if (hits)
            fight.AddRitualStacks(hits, "charge");
        fight.Log("desecration-charge-lands", Acore::StringFormat("hits={}", hits));
    }

    // ---- RH3 Repent -------------------------------------------------------------------------------------------------

    bool CastRepent(ThalnosFight& fight, Creature* fairbell, Player* forced)
    {
        Player* target = forced && forced->IsAlive() && OnLawn(forced) ? forced : nullptr;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = false;           // the tank included
            for (Player* player : fight.FightPlayers())
                if (!OnLawn(player))
                    rule.exclude.push_back(player->GetGUID().GetRawValue());
            target = DungeonKit::PickPlayer(fairbell, rule);
        }
        if (!target || !SpellExists(SPELL_DS_REPENT))
            return false;
        fairbell->StopMoving();
        SpellCastResult const result = fairbell->CastSpell(target, SPELL_DS_REPENT, false);
        if (result != SPELL_CAST_OK)
        {
            fight.Log("desecration-repent-refused", Acore::StringFormat("result={}", uint32(result)));
            return false;
        }
        ++_repents;
        fight.Log("desecration-repent", Acore::StringFormat("target={} tank={}", target->GetName(),
            target == fight.Thalnos()->GetVictim() ? 1 : 0));
        return true;
    }

    // ---- RH4 Greater Heal / RH5 Power Word: Shield ------------------------------------------------------------------

    // Thalnos first, then the living risen within 40 yd of `voss`.
    std::array<Creature*, kMaxAllies> Allies(Creature* boss, Creature* voss, std::array<Ally, kMaxAllies>& out,
        std::size_t& count) const
    {
        std::array<Creature*, kMaxAllies> units{};
        count = 0;
        auto add = [&](Creature* unit)
        {
            if (!unit || !unit->IsAlive() || !unit->IsInWorld() || !voss->IsWithinDistInMap(unit, 40.f))
                return;
            units[count] = unit;
            out[count] = { unit->GetGUID().GetRawValue(), unit->GetHealthPct(),
                unit->HasAura(SPELL_DS_POWER_WORD_SHIELD) };
            ++count;
        };
        add(boss);
        for (Hero h : kHeroes)
            add(Risen(boss, h));
        return units;
    }

    bool CastHeal(ThalnosFight& fight, Creature* voss)
    {
        if (!SpellExists(SPELL_DS_GREATER_HEAL))
            return false;
        Creature* boss = fight.Thalnos();
        std::array<Ally, kMaxAllies> allies{};
        std::size_t count = 0;
        std::array<Creature*, kMaxAllies> const units = Allies(boss, voss, allies, count);
        std::optional<std::size_t> const pick = MostWounded(allies, count);
        if (!pick)
            return false;
        Creature* target = units[*pick];
        uint32 const amount = HealAmount(target->GetMaxHealth());
        voss->StopMoving();
        CastSpellExtraArgs args;
        args.AddSpellBP0(static_cast<int32>(amount));
        SpellCastResult const result = voss->CastSpell(target, SPELL_DS_GREATER_HEAL, args);
        if (result != SPELL_CAST_OK)
        {
            fight.Log("desecration-heal-refused", Acore::StringFormat("result={}", uint32(result)));
            return false;
        }
        ++_heals;
        fight.Log("desecration-heal", Acore::StringFormat("on={} health={:.1f} amount={}", target->GetName(),
            target->GetHealthPct(), amount));
        return true;
    }

    bool CastShield(ThalnosFight& fight, Creature* voss)
    {
        if (!SpellExists(SPELL_DS_POWER_WORD_SHIELD))
            return false;
        Creature* boss = fight.Thalnos();
        std::array<Ally, kMaxAllies> allies{};
        std::size_t count = 0;
        std::array<Creature*, kMaxAllies> const units = Allies(boss, voss, allies, count);
        std::optional<std::size_t> const pick = MostWounded(allies, count, true);
        if (!pick)
            return false;
        Creature* target = units[*pick];
        voss->CastSpell(target, SPELL_DS_POWER_WORD_SHIELD, true);
        ++_shields;
        fight.Log("desecration-shield", Acore::StringFormat("on={} absorb={}", target->GetName(), kShieldAbsorb));
        return true;
    }

    // ---- RH6 Whirlwind ----------------------------------------------------------------------------------------------

    bool StartWhirlwind(ThalnosFight& fight, Creature* goodchilde, uint64 now)
    {
        Creature* boss = fight.Thalnos();
        RisenState& r = _risen[IndexOf(Hero::Goodchilde)];
        if (r.spinEndMs)
            return false;
        // He stands still for the wind-up and the spin: the tank steps out too.
        goodchilde->StopMoving();
        goodchilde->SetControlled(true, UNIT_STATE_ROOT);
        if (goodchilde->IsAIEnabled)
            goodchilde->AI()->Talk(EMOTE_RISEN);
        if (SpellExists(SPELL_DS_WHIRLWIND_WINDUP))
            goodchilde->CastSpell(goodchilde, SPELL_DS_WHIRLWIND_WINDUP, false);
        bool const rallied = goodchilde->HasAura(SPELL_DS_RALLIED);
        float const pct = Rallied(kWhirlwindPct, rallied);
        Position const at = goodchilde->GetPosition();
        MechanicRef ref = Mechanic::Zone(boss, BossMechanics::Shapes::Circle(BossMechanics::Anchor(at),
            kWhirlwindRadius), Ms(kWhirlwindWindupMs));
        ref.Persistent(Ms(kWhirlwindSpinMs), Ms(kWhirlwindTickMs)).Damage(pct).TankDamage(pct).Weakened()
            .Spell(SPELL_DS_WHIRLWIND_HIT).Within(LawnBounds()).Tag(RH6)
            .OnResolve(OnFight(boss, [](Desecration& self, ThalnosFight& f, BossMechanics::ResolveResult const& res)
            {
                self.SpinTick(f, res);
            }));
        fight.Track(ref.Handle());
        r.spinZone = ref.Handle();
        r.spinHit.clear();
        r.spinAtMs = now + kWhirlwindWindupMs;
        r.spinEndMs = now + kWhirlwindHoldMs;
        ++_spins;
        fight.Log("desecration-whirlwind", Acore::StringFormat("at=({:.1f}, {:.1f}) pct={:.1f} rallied={}",
            at.GetPositionX(), at.GetPositionY(), pct, rallied ? 1 : 0));
        return true;
    }

    // One tick of the spin: each player is one stack for the whole spin.
    void SpinTick(ThalnosFight& fight, BossMechanics::ResolveResult const& result)
    {
        if (result.fizzled)
            return;
        RisenState& r = _risen[IndexOf(Hero::Goodchilde)];
        uint32 fresh = 0;
        for (ObjectGuid const& g : result.hits)
            if (g.IsPlayer() && r.spinHit.insert(g).second)
                ++fresh;
        if (fresh)
            fight.AddRitualStacks(fresh, "whirlwind");
    }

    static constexpr uint32 kRisenCorpseMs = 8000;

    DungeonKit::WardOfTheLiving _ward;
    RiseClock _rise;
    std::array<RisenState, kHeroCount> _risen{};
    std::vector<Banner> _bannerList;
    std::vector<ObjectGuid> _sent;
    Stage _stage = Stage::Crypt;
    uint64 _teleportAtMs = 0;
    uint64 _arriveByMs = 0;
    uint32 _baseHealth = 0;
    // This pull's serial (OnFight's stale-callback guard): every Desecration gets the next one.
    static inline std::atomic<uint64> s_nextSerial{ 0 };   // maps update on several threads
    uint64 const _serial = ++s_nextSerial;
    uint32 _rallyMs = 0;
    uint32 _tetherMs = 0;
    uint32 _rises = 0;
    uint32 _risenKilled = 0;
    uint32 _banners = 0;
    uint32 _charges = 0;
    uint32 _repents = 0;
    uint32 _heals = 0;
    uint32 _healsKicked = 0;
    uint32 _shields = 0;
    uint32 _spins = 0;
};

namespace
{
    // The running pull's hard mode for a unit of it (Thalnos or a risen he summoned), or nullptr.
    Desecration* DesecrationOf(Creature* unit, ThalnosFight*& fight)
    {
        Creature* thalnos = unit && unit->GetEntry() == NPC_THALNOS ? unit : nullptr;
        if (!thalnos && unit)
            if (TempSummon* summon = unit->ToTempSummon())
                if (Unit* summoner = summon->GetSummonerUnit())
                    thalnos = summoner->ToCreature();
        fight = FightOf(thalnos);
        return fight ? dynamic_cast<Desecration*>(fight->ActiveHardMode()) : nullptr;
    }
}

// -------------------------------------------------------------------------------------------------------------------
// The risen heroes 300903-300906 (npc_sm_risen_hero): Thalnos's summons. The hard mode drives their abilities; the AI
// chases, swings and forwards its spell hits and kicks. Orphaned (his fight over), it goes.
// -------------------------------------------------------------------------------------------------------------------

struct npc_sm_risen_hero : public ScriptedAI
{
    explicit npc_sm_risen_hero(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override { }

    void UpdateAI(uint32 diff) override
    {
        if (_checkMs > diff)
            _checkMs -= diff;
        else
        {
            _checkMs = kOrphanCheckMs;
            ThalnosFight* fight = nullptr;
            if (!DesecrationOf(me, fight))
            {
                me->DespawnOrUnsummon();
                return;
            }
        }
        if (!UpdateVictim())
            return;
        DoMeleeAttackIfReady();
    }

    void SpellHitTarget(Unit* target, SpellInfo const* spell) override
    {
        ThalnosFight* fight = nullptr;
        if (Desecration* d = DesecrationOf(me, fight))
            d->RisenSpellHit(*fight, me, target, spell);
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        ThalnosFight* fight = nullptr;
        if (Desecration* d = DesecrationOf(me, fight))
            d->RisenSpellFailed(*fight, me, spell);
    }

    // No walk home: the fight is on the lawn while he lives; it goes when his fight is over (the check above).
    void EnterEvadeMode(EvadeReason /*why*/) override
    {
        ThalnosFight* fight = nullptr;
        if (!DesecrationOf(me, fight))
        {
            me->DespawnOrUnsummon();
            return;
        }
        if (Unit* tank = fight->Thalnos()->GetVictim())
        {
            me->GetThreatMgr().AddThreat(tank, 1.f, nullptr, true, true);
            AttackStart(tank);
        }
    }

private:
    static constexpr uint32 kOrphanCheckMs = 1000;
    uint32 _checkMs = kOrphanCheckMs;
};

// -------------------------------------------------------------------------------------------------------------------
// The gravestones 301310-301313 (go_sm_desecration_stone): the stone's hero is its entry's (never its spot: RB-3)
// -------------------------------------------------------------------------------------------------------------------

namespace
{
    StoneRefusal RefusalAt(WorldObject* where)
    {
        InstanceScript* instance = where ? where->GetInstanceScript() : nullptr;
        if (!instance)
            return StoneRefusal::NotHeroic;
        return RefusalFor(DungeonKit::IsHeroicMap(where), instance->GetBossState(BOSS_THALNOS),
            instance->GetBossState(BOSS_COUNCIL), instance->GetData(DATA_HARD_MODE_THALNOS) != 0);
    }

    // A look stalker of `owner` (the shared stalker 300922, the orchestrator's template): `look` on it, or none.
    ObjectGuid ShowLook(WorldObject* owner, ObjectGuid current, uint32 look)
    {
        Creature* stalker = current ? owner->GetMap()->GetCreature(current) : nullptr;
        if (!look)
        {
            if (stalker)
                stalker->DespawnOrUnsummon();
            return ObjectGuid::Empty;
        }
        if (!SpellExists(look) || !StalkerExists())
            return current;
        if (!stalker || !stalker->IsAlive())
        {
            stalker = owner->SummonCreature(NPC_SM_STALKER, owner->GetPosition(), TEMPSUMMON_MANUAL_DESPAWN);
            if (!stalker)
                return ObjectGuid::Empty;
        }
        for (uint32 spell : { uint32(SPELL_DS_STONE_STIR), uint32(SPELL_DS_STONE_BLOOD) })
            if (spell != look)
                stalker->RemoveAurasDueToSpell(spell);
        if (!stalker->HasAura(look))
            stalker->CastSpell(stalker, look, true);
        return stalker->GetGUID();
    }
}

struct go_sm_desecration_stone : public GameObjectAI
{
    explicit go_sm_desecration_stone(GameObject* go) : GameObjectAI(go) { }

    void UpdateAI(uint32 diff) override
    {
        if (_pollMs > diff)
        {
            _pollMs -= diff;
            return;
        }
        _pollMs = kStonePollMs;
        Sync();
    }

    bool GossipHello(Player* player, bool reportUse) override
    {
        if (reportUse || !player)
            return true;
        std::optional<Hero> const hero = HeroOfStone(me->GetEntry());
        if (!hero)
            return true;
        StoneRefusal const refusal = RefusalAt(me);
        ClearGossipMenuFor(player);
        if (refusal == StoneRefusal::None)
            AddGossipItemFor(player, GOSSIP_ICON_CHAT, kDisturbOption, GOSSIP_SENDER_MAIN, GOSSIP_ACTION_INFO_DEF + 1);
        SendGossipMenuFor(player, EpitaphTextId(*hero), me->GetGUID());
        if (refusal == StoneRefusal::CouncilAlive || refusal == StoneRefusal::ThalnosFighting
            || refusal == StoneRefusal::ThalnosDead)
            Notify(player, RefusalText(refusal));
        return true;
    }

    bool GossipSelect(Player* player, uint32 /*menuId*/, uint32 /*gossipListId*/) override
    {
        if (!player)
            return true;
        CloseGossipMenuFor(player);
        Disturb(player);
        return true;
    }

    // The 2 s use landed.
    void SpellHit(Unit* caster, SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_DS_DISTURB_THE_GRAVE && caster && caster->IsPlayer())
            Touch(caster->ToPlayer());
    }

    // The player's 2 s cast on the stone (moving stops it); straight to the touch when the spell is missing.
    void Disturb(Player* player)
    {
        StoneRefusal const refusal = RefusalAt(me);
        if (refusal != StoneRefusal::None)
        {
            Notify(player, RefusalText(refusal));
            return;
        }
        if (!SpellExists(SPELL_DS_DISTURB_THE_GRAVE))
        {
            Touch(player);
            return;
        }
        // A mounted reader would get "can't do that while mounted" on a gossip option: off the mount first (N-4).
        if (player->IsMounted())
            player->RemoveAurasByType(SPELL_AURA_MOUNTED);
        SpellCastResult const result = player->CastSpell(me, SPELL_DS_DISTURB_THE_GRAVE, false);
        if (result != SPELL_CAST_OK)
            LogStone("stone-cast-refused", Acore::StringFormat("stone={} by={} result={}", me->GetEntry(),
                player->GetName(), uint32(result)));
    }

    // The touch itself (the instance keeps the order and judges the fourth). `player` may be a GM's test.
    void Touch(Player* player)
    {
        std::optional<Hero> const hero = HeroOfStone(me->GetEntry());
        InstanceScript* instance = me->GetInstanceScript();
        if (!hero || !instance || !player)
            return;
        StoneRefusal const refusal = RefusalAt(me);
        if (refusal != StoneRefusal::None)
        {
            Notify(player, RefusalText(refusal));
            return;
        }
        instance->SetData(DATA_DESECRATION_TOUCH, static_cast<uint32>(IndexOf(*hero)));
        auto const verdict = static_cast<DesecrationVerdict>(instance->GetData(DATA_DESECRATION_RESULT));
        switch (verdict)
        {
            case DesecrationVerdict::None:
                _touched = true;
                LogStone("stone-touch", Acore::StringFormat("stone={} by={} touches={}", NameOf(*hero),
                    player->GetName(), instance->GetData(DATA_DESECRATION_TOUCH)));
                break;
            case DesecrationVerdict::Right:
                _touched = false;
                WakeThemAll(player);
                break;
            case DesecrationVerdict::Wrong:
                _touched = false;
                Phantasms(player);
                break;
            case DesecrationVerdict::Repeat:
                Notify(player, kRepeatText);
                break;
            case DesecrationVerdict::Refused:
                Notify(player, RefusalText(RefusalAt(me)));
                break;
        }
        Sync();
    }

private:
    void Sync()
    {
        InstanceScript* instance = me->GetInstanceScript();
        if (!instance)
            return;
        bool const lit = instance->GetData(DATA_HARD_MODE_THALNOS) != 0 && DungeonKit::IsHeroicMap(me);
        uint32 const touches = instance->GetData(DATA_DESECRATION_TOUCH);
        if (!touches)
            _touched = false;
        StoneLook const look = LookFor(lit, _touched, touches);
        uint32 const spell = look == StoneLook::Blood ? uint32(SPELL_DS_STONE_BLOOD)
            : look == StoneLook::Stir ? uint32(SPELL_DS_STONE_STIR) : 0u;
        _look = ShowLook(me, _look, spell);
    }

    // Right: the flag is lit (the instance: saved, the loot bit); Thalnos yells line 4 and wears the red aura.
    void WakeThemAll(Player* player)
    {
        Creature* thalnos = ThalnosOf(me);
        if (thalnos && thalnos->IsAlive() && thalnos->IsAIEnabled)
        {
            thalnos->AI()->Talk(SmThalnos::SAY_WAKE_THEM_ALL);
            IdleLook(thalnos);
        }
        LogStone("lit", Acore::StringFormat("by={} thalnos={}", player->GetName(), thalnos ? 1 : 0));
    }

    // Wrong: the stones go dark; three Haunting Phantasms rise on the lawn and attack the toucher.
    void Phantasms(Player* player)
    {
        uint32 risen = 0;
        for (uint32 i = 0; i < kPhantasmCount; ++i)
        {
            Vec2 const p = PhantasmSpot(i);
            Position const at = LawnPosition(me, p.x, p.y, kStoneSpots[0].z, DungeonKit::BearingTo(p,
                DungeonKit::PlaneOf(player)));
            TempSummon* phantasm = me->SummonCreature(NPC_HAUNTING_PHANTASM, at,
                TEMPSUMMON_TIMED_DESPAWN_OUT_OF_COMBAT, kPhantasmCorpseMs);
            if (!phantasm)
                continue;
            ++risen;
            if (phantasm->IsAIEnabled && player->IsAlive())
                phantasm->AI()->AttackStart(player);
        }
        LogStone("wrong", Acore::StringFormat("by={} phantasms={}", player->GetName(), risen));
    }

    ObjectGuid _look;
    uint32 _pollMs = 0;
    bool _touched = false;
};

// The blood rite 301314 (go_sm_blood_rite): a readable wall scroll in the z 0 court (its text names the order in other
// words than the epitaphs) with a red blood look on heroic.
struct go_sm_blood_rite : public GameObjectAI
{
    explicit go_sm_blood_rite(GameObject* go) : GameObjectAI(go) { }

    void UpdateAI(uint32 diff) override
    {
        if (_pollMs > diff)
        {
            _pollMs -= diff;
            return;
        }
        _pollMs = kRitePollMs;
        _look = ShowLook(me, _look, DungeonKit::IsHeroicMap(me) ? uint32(SPELL_DS_STONE_BLOOD) : 0u);
    }

    bool GossipHello(Player* player, bool reportUse) override
    {
        if (reportUse || !player)
            return true;
        ClearGossipMenuFor(player);
        SendGossipMenuFor(player, kRiteTextId, me->GetGUID());
        LogStone("rite-read", Acore::StringFormat("by={}", player->GetName()));
        return true;
    }

private:
    ObjectGuid _look;
    uint32 _pollMs = 0;
};

// RH1: a Rallied dealer's melee and spells deal 25% more to players (the hard mode's own hits are boosted at their
// registration instead: HookBoosts). A creature with the aura is only ever Thalnos or a risen.
class sm_desecration_rally_hook : public UnitScript
{
public:
    sm_desecration_rally_hook() : UnitScript("sm_desecration_rally_hook", true,
        { UNITHOOK_MODIFY_MELEE_DAMAGE, UNITHOOK_MODIFY_SPELL_DAMAGE_TAKEN }) { }

    void ModifyMeleeDamage(Unit* target, Unit* attacker, uint32& damage) override
    {
        if (damage && Boosts(target, attacker))
            damage = RalliedDamage(damage);
    }

    void ModifySpellDamageTaken(Unit* target, Unit* attacker, int32& damage, SpellInfo const* spellInfo) override
    {
        if (damage > 0 && spellInfo && HookBoosts(spellInfo->Id) && Boosts(target, attacker))
            damage = static_cast<int32>(RalliedDamage(static_cast<uint32>(damage)));
    }

private:
    static bool Boosts(Unit const* target, Unit const* attacker)
    {
        return target && attacker && target->IsPlayer() && attacker->IsCreature()
            && attacker->HasAura(SPELL_DS_RALLIED);
    }
};

// -------------------------------------------------------------------------------------------------------------------
// `.dbtest sm desecration`
// -------------------------------------------------------------------------------------------------------------------

namespace
{
    Player* Gm(ChatHandler* handler)
    {
        return handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
    }

    // The running pull's hard mode (an error and nullptr when there is none).
    Desecration* FindDesecration(ChatHandler* handler, ThalnosFight*& fight)
    {
        Creature* boss = SmTest::FindBoss(handler, NPC_THALNOS);
        if (!boss)
            return nullptr;
        Desecration* d = DesecrationOf(boss, fight);
        if (!fight)
        {
            handler->SendErrorMessage("{}", "Bloodmage Thalnos is not running boss_bloodmage_thalnos_rework.");
            return nullptr;
        }
        if (!d)
            handler->SendErrorMessage("{}", "No hard mode pull is running (answer the stones or `.dbtest sm thalnos "
                "hardmode` on heroic, then pull him).");
        return d;
    }

    // The stone of `hero` near the GM (the lawn), or nullptr with an error.
    go_sm_desecration_stone* FindStone(ChatHandler* handler, Hero hero)
    {
        Player* gm = Gm(handler);
        if (!gm || !SmTest::RequireScarletMonastery(handler))
            return nullptr;
        uint32 const entry = GO_SM_GRAVESTONE_GALVAR + static_cast<uint32>(IndexOf(hero));
        GameObject* go = gm->FindNearestGameObject(entry, 250.f);
        auto* ai = go ? dynamic_cast<go_sm_desecration_stone*>(go->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "No gravestone near you (heroic only: stand on the Graveyard lawn).");
        return ai;
    }

    bool TouchStones(ChatHandler* handler, std::array<Hero, kHeroCount> const& order)
    {
        Player* gm = Gm(handler);
        for (Hero h : order)
        {
            go_sm_desecration_stone* stone = FindStone(handler, h);
            if (!stone)
                return false;
            stone->Touch(gm);
        }
        InstanceScript* instance = SmTest::GmInstance(handler);
        handler->PSendSysMessage("desecration: lit={} last={}", instance ? instance->GetData(DATA_HARD_MODE_THALNOS)
            : 0, instance ? instance->GetData(DATA_DESECRATION_RESULT) : 0);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return SmTest::ShowHardModeInfo(handler, "desecration", DATA_HARD_MODE_THALNOS, BOSS_DESECRATION);
    }

    // `.dbtest sm desecration touch <1-4>`: that stone (1 Galvar .. 4 Goodchilde) as a player touches it (no cast).
    bool HandleTouch(ChatHandler* handler, uint32 which)
    {
        if (which < 1 || which > kHeroCount)
        {
            handler->SendErrorMessage("{}", "Stone 1 (Galvar), 2 (Fairbell), 3 (Voss) or 4 (Goodchilde).");
            return false;
        }
        go_sm_desecration_stone* stone = FindStone(handler, kHeroes[which - 1]);
        if (!stone)
            return false;
        stone->Touch(Gm(handler));
        InstanceScript* instance = SmTest::GmInstance(handler);
        handler->PSendSysMessage("desecration: touches={} last={} lit={}",
            instance ? instance->GetData(DATA_DESECRATION_TOUCH) : 0,
            instance ? instance->GetData(DATA_DESECRATION_RESULT) : 0,
            instance ? instance->GetData(DATA_HARD_MODE_THALNOS) : 0);
        return true;
    }

    // `.dbtest sm desecration answer`: the four stones in the right order (the real rules).
    bool HandleAnswer(ChatHandler* handler)
    {
        return TouchStones(handler, kHeroes);
    }

    // `.dbtest sm desecration wrong`: the four stones in the reverse order (three Phantasms rise).
    bool HandleWrong(ChatHandler* handler)
    {
        return TouchStones(handler, { Hero::Goodchilde, Hero::Voss, Hero::Fairbell, Hero::Galvar });
    }

    bool HandleState(ChatHandler* handler)
    {
        ThalnosFight* fight = nullptr;
        Desecration* d = FindDesecration(handler, fight);
        if (!d)
            return false;
        handler->PSendSysMessage("desecration: {}", d->TestState(*fight));
        return true;
    }

    // `.dbtest sm desecration teleport`: TH7 now (once a pull, before 75%).
    bool HandleTeleport(ChatHandler* handler)
    {
        ThalnosFight* fight = nullptr;
        Desecration* d = FindDesecration(handler, fight);
        if (!d)
            return false;
        bool const ok = d->TestTeleport(*fight);
        handler->PSendSysMessage("desecration: {}", ok ? "No Rest for the Angry Dead (3 s)" : "already past the crypt");
        return ok;
    }

    // `.dbtest sm desecration rise <1-4>`: that hero rises now (in the yard, when it is not standing).
    bool HandleRise(ChatHandler* handler, uint32 which)
    {
        if (which < 1 || which > kHeroCount)
        {
            handler->SendErrorMessage("{}", "Hero 1 (Galvar), 2 (Fairbell), 3 (Voss) or 4 (Goodchilde).");
            return false;
        }
        ThalnosFight* fight = nullptr;
        Desecration* d = FindDesecration(handler, fight);
        if (!d)
            return false;
        bool const ok = d->TestRise(*fight, kHeroes[which - 1]);
        handler->PSendSysMessage("desecration: {} {}", NameOf(kHeroes[which - 1]), ok ? "rises"
            : "does not rise (not in the yard yet, or standing)");
        return ok;
    }

    bool Fire(ChatHandler* handler, Desecration::TestAbility a, char const* what)
    {
        ThalnosFight* fight = nullptr;
        Desecration* d = FindDesecration(handler, fight);
        if (!d)
            return false;
        Player* on = handler->getSelectedPlayer();
        std::string const error = d->TestFire(*fight, a, on);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("desecration: {}", what);
        return true;
    }

    bool HandleBanner(ChatHandler* handler)
    {
        return Fire(handler, Desecration::TestAbility::Banner, "Rallying Banner (RH1, at Galvar's feet)");
    }

    bool HandleCharge(ChatHandler* handler)
    {
        return Fire(handler, Desecration::TestAbility::Charge, "Crusader's Charge (RH2, the selected player, else "
            "the farthest)");
    }

    bool HandleRepent(ChatHandler* handler)
    {
        return Fire(handler, Desecration::TestAbility::Repent, "Repent (RH3, the selected player, else random)");
    }

    bool HandleHeal(ChatHandler* handler)
    {
        return Fire(handler, Desecration::TestAbility::Heal, "Greater Heal (RH4, the most wounded ally)");
    }

    bool HandleShield(ChatHandler* handler)
    {
        return Fire(handler, Desecration::TestAbility::Shield, "Power Word: Shield (RH5)");
    }

    bool HandleWhirlwind(ChatHandler* handler)
    {
        return Fire(handler, Desecration::TestAbility::Whirlwind, "Whirlwind (RH6, 2 s wind-up, 4 s spin)");
    }

    ChatCommandTable const& DesecrationTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",      HandleInfo,      SEC_GAMEMASTER, Console::No },
            { "touch",     HandleTouch,     SEC_GAMEMASTER, Console::No },
            { "answer",    HandleAnswer,    SEC_GAMEMASTER, Console::No },
            { "wrong",     HandleWrong,     SEC_GAMEMASTER, Console::No },
            { "state",     HandleState,     SEC_GAMEMASTER, Console::No },
            { "teleport",  HandleTeleport,  SEC_GAMEMASTER, Console::No },
            { "rise",      HandleRise,      SEC_GAMEMASTER, Console::No },
            { "banner",    HandleBanner,    SEC_GAMEMASTER, Console::No },
            { "charge",    HandleCharge,    SEC_GAMEMASTER, Console::No },
            { "repent",    HandleRepent,    SEC_GAMEMASTER, Console::No },
            { "heal",      HandleHeal,      SEC_GAMEMASTER, Console::No },
            { "shield",    HandleShield,    SEC_GAMEMASTER, Console::No },
            { "whirlwind", HandleWhirlwind, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_sm_thalnos_hard_mode()
{
    // D4 asks for a Desecration only on a heroic pull with the Desecration answered.
    SmThalnos::RegisterThalnosHardMode([](Creature*) { return std::make_unique<Desecration>(); });
    SmThalnos::RegisterThalnosIdleHook([](Creature* boss) { IdleLook(boss); });
    RegisterDungeonReworkCreatureAI(npc_sm_risen_hero, ScarletMonasteryRework::kInstanceScriptName);
    RegisterDungeonReworkGameObjectAI(go_sm_desecration_stone, ScarletMonasteryRework::kInstanceScriptName);
    RegisterDungeonReworkGameObjectAI(go_sm_blood_rite, ScarletMonasteryRework::kInstanceScriptName);
    new sm_desecration_rally_hook();
    SmTest::RegisterBoss("desecration", DesecrationTestCommands());
}
