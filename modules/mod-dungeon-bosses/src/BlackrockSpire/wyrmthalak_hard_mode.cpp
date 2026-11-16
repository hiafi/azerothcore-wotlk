/*
 * mod-dungeon-bosses, Blackrock Spire B9: Overlord Wyrmthalak's hard mode, the war horn (heroic only).
 * Build spec SP 2436-2521 rows WT9-WT17 (design SP 2322-2389, rulings 48-49); handoff section 3.7, section 3.4 row
 * "WT hard mode", section 3.5 row B9, section 7 #14, #22, #25, #26, #28. It fights on B8's AI
 * (boss_overlord_wyrmthalak_rework) through WyrmthalakFight.h: B8 makes one WarHorn per heroic pull with the horn lit
 * and calls its hooks. Pure rules and numbers: WyrmthalakHardModeLogic.h.
 *
 *   WT9  The Muster        the Bloodaxe War Horn (GO 301255, go_brs_war_horn, at the ramp head): on heroic, out of
 *                          combat, before the kill, it lights DATA_WAR_HORN (the instance's per-pull flag, refused
 *                          otherwise), his emote line 7 and the horn's burst. The pull reads it (B8): 400k x the flex
 *                          ladder, all three champions with the first order (10 s), two tribes an order (25 s).
 *   Champions              100k each x the ladder (Flex::SetHealth as they appear on the ramp).
 *   WT10 Stolen Boulders   every boulder leaves a Stolen Magic shard (Urok's 300706, UrokShards.h) at its center:
 *                          taken on touch (2 yd), no buff; left 10 s it crawls 3 yd/s to the Spirestone Champion: +1
 *                          Stolen Power (+5% damage); at 5 a 3 s cast, then the Overcharge: 40% to every player within
 *                          100 yd, the stacks reset. His death clears the shards.
 *   WT11 Chained Axes      the Smolderthorn Champion throws the Axe Volley himself (B8's AxeThrower); each axe sticks
 *                          (Stuck Axe 301250 + Chain Anchor 300704, Voone's) chained to him: a live 2 yd line, 10%
 *                          and Weakened per crossing, every 2 s from 2 s to 8 s; at 8 s the 1.5 s taut warning of the
 *                          3 yd haul from the axe to him (35%, Weakened), then the axe flies home. G1 drill tag 6.
 *   WT12 Riders stay       up to 4 / 8 riders a fight turn and fight after their charge: attackable 6k x the ladder,
 *                          each after a random player (the kit's Chaser, no threat, a new pick every 8 s), Rabies on
 *                          their melee (1.5% a stack every 3 s, 5, Disease); past the cap they ride back down.
 *   WT13 Tribal Ward       -20% damage taken a stack on him, one stack per living champion (60% with all three).
 *   WT14 Caustic Venom     the Bloodaxe Champion's death: every hit of his (Cleave, Black Dragonfire, Tail Swipe, the
 *                          spear's impact, the spit's circles) adds a Caustic Poison stack (0.5% every 2 s, 10, 20 s,
 *                          Poison); Caustic Roar 8 s later, every 20 s: 2.5 s interruptible cast (line 8), landed 20%
 *                          Nature to everyone and 2 stacks.
 *   WT15 Empowered         the Smolderthorn Champion's death: his burns last 120 s on the whole 25 yd cone, at most 3
 *        Dragonfire        (the cap-3 fallback, section 7 #28); the Spear Chain 10 s later, every 30 s: a random
 *                          non-tank (line 9), 10% on impact, then a live 2 yd chain from him to them for 20 s (10% and
 *                          Weakened once per player, crossing every 2 s; the speared player is not on it).
 *   WT16 Shadowflame Spit  the Spirestone Champion's death: 5 s later, every 15 s, a 4 yd circle under every player
 *                          (2 s, 25%, Weakened); 2 / 3 of them burn 40 s (5% a second, Weakened once per player).
 *   WT17 Reset             B8's cleanup despawns every summon (champions, riders, shards, anchors, patches) and
 *                          cancels every tracked mechanic; OnEnd stops the chasers, removes the axes, the auras and
 *                          Tribal Ward and puts his heroic health back; the instance clears the horn (blow it again).
 *   Loot                   B8's pull passes hardMode to OnBossPull (DungeonKit::Flex::OnPull: LootMode 8 at 10); the
 *                          instance keeps LootMode 2 while the horn is lit and records BOSS_WAR_HORN (26) on the kill.
 *
 * Every timer runs on the fight's clock (WyrmthalakFight::FightMs). Every firing logs one INFO line
 * "brs wyrmthalak warhorn-<mechanic> ..." (module.dungeonbosses); `.dbtest brs warhorn <...>` fires them.
 */

#include "BlackrockSpireRework.h"
#include "BlackrockSpireTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "DungeonKitChase.h"
#include "DungeonKitFields.h"
#include "DungeonKitFlex.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "UrokShards.h"
#include "VooneLogic.h"
#include "WyrmthalakFight.h"
#include "WyrmthalakHardModeLogic.h"
#include "WyrmthalakLogic.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <map>
#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;
using namespace BrsWarHorn;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using BrsWyrmthalak::Ability;
using BrsWyrmthalak::BurnSpec;
using BrsWyrmthalak::Tribe;
using BrsWyrmthalak::WyrmthalakFight;
using BrsWyrmthalak::WyrmthalakHardMode;

namespace
{
    char const* const kLogKey = "warhorn";
    uint32 constexpr kRiderFlags = UNIT_FLAG_NON_ATTACKABLE | UNIT_FLAG_IMMUNE_TO_PC | UNIT_FLAG_IMMUNE_TO_NPC;

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // Applies `stacks` Caustic Poison stacks from him on a player (WT14), refreshed, at most 10.
    void Poison(Creature* boss, Unit* hit, uint32 stacks)
    {
        if (!boss || !hit || !hit->IsAlive() || !hit->IsPlayer())
            return;
        DungeonKit::AddStacks(hit, SPELL_WH_CAUSTIC_POISON, int32(stacks), boss, kPoisonMaxStacks);
    }

    GuidSet GuidsOf(std::vector<Player*> const& players)
    {
        GuidSet out;
        for (Player* p : players)
            if (p)
                out.insert(p->GetGUID());
        return out;
    }

    // ---- WT9 the horn (the object and `.dbtest brs warhorn blow` share it) ------------------------------------------

    HornRefusal RefusalAt(WorldObject const* where)
    {
        InstanceScript* instance = where ? where->GetInstanceScript() : nullptr;
        if (!instance)
            return HornRefusal::NotHeroic;
        return HornRefusalFor(where->GetMap()->IsHeroic(), instance->GetBossState(BOSS_WYRMTHALAK),
            instance->GetData(DATA_WAR_HORN) != 0);
    }

    // Blows the horn for `player` at `where` (the object, or the GM). Returns the refusal (None: lit).
    HornRefusal BlowHorn(WorldObject* where, Player* player)
    {
        HornRefusal refusal = RefusalAt(where);
        InstanceScript* instance = where ? where->GetInstanceScript() : nullptr;
        if (refusal == HornRefusal::None && instance)
        {
            instance->SetData(DATA_WAR_HORN, 1);
            if (!instance->GetData(DATA_WAR_HORN))
                refusal = HornRefusal::Fighting;    // the instance refused it (WarHornChangeAllowed)
        }
        if (refusal != HornRefusal::None)
        {
            if (player && player->GetSession())
                ChatHandler(player->GetSession()).SendNotification(HornRefusalText(refusal));
            DungeonKit::LogMechanic(kLogDungeon, "wyrmthalak", "warhorn-refused", Acore::StringFormat("by={} why={}",
                player ? player->GetName() : std::string("none"), uint32(refusal)));
            return refusal;
        }
        if (Creature* boss = instance->GetCreature(BOSS_WYRMTHALAK))
            if (boss->IsAlive() && boss->IsAIEnabled)
                boss->AI()->Talk(BrsWyrmthalak::EMOTE_WT_HORN);
        // The burst (V-1's SV 90602: the stock horn's sound and animation kit plus the war horn impact) from a stalker
        // on the horn: the Chain Anchor (an invisible unit without the trigger bit, so its looks show).
        if (Creature* stalker = where->SummonCreature(NPC_BRS_CHAIN_ANCHOR, where->GetPositionX(),
            where->GetPositionY(), where->GetPositionZ(), where->GetOrientation(), TEMPSUMMON_TIMED_DESPAWN,
            kHornLookMs))
        {
            stalker->SetReactState(REACT_PASSIVE);
            stalker->CastSpell(stalker, SPELL_WH_HORN_BLOWN, true);
        }
        DungeonKit::LogMechanic(kLogDungeon, "wyrmthalak", "warhorn-blown", Acore::StringFormat("by={}",
            player ? player->GetName() : std::string("none")));
        return HornRefusal::None;
    }
}

// The hard mode of one pull (B8 makes it at a heroic pull with the horn lit and ends it with the pull).
class WarHorn final : public WyrmthalakHardMode
{
public:
    WarHorn() : _serial(++NextSerial()) { }

    // The pull's hard mode, as a registry callback or a command finds it again: his AI's ActiveHardMode on the same
    // pull (`serial`), or nullptr.
    static WarHorn* Find(Map* map, ObjectGuid bossGuid, uint32 serial, WyrmthalakFight** fightOut = nullptr)
    {
        if (!map)
            return nullptr;
        Creature* boss = map->GetCreature(bossGuid);
        if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
            return nullptr;
        auto* fight = dynamic_cast<WyrmthalakFight*>(boss->AI());
        auto* horn = fight ? dynamic_cast<WarHorn*>(fight->ActiveHardMode()) : nullptr;
        if (!horn || (serial && horn->_serial != serial))
            return nullptr;
        if (fightOut)
            *fightOut = fight;
        return horn;
    }

    // ---- the pull ---------------------------------------------------------------------------------------------------

    void OnEngage(WyrmthalakFight& fight) override
    {
        Creature* boss = fight.Boss();
        _map = boss->GetMap();
        _bossGuid = boss->GetGUID();
        _players = fight.Players();
        _baseHealth = BaseBeforeHardMode(boss->GetMaxHealth(), _players);
        DungeonKit::Flex::SetHealth(boss, kBossHealthAt5, true);
        boss->RemoveAurasDueToSpell(SPELL_WH_TRIBAL_WARD);
        Describe(boss);
        fight.Log("warhorn-engage", Acore::StringFormat("players={} health={} base-before={} rider-cap={}", _players,
            boss->GetMaxHealth(), _baseHealth, kRiderCap.At(_players)));
    }

    void OnUpdate(WyrmthalakFight& fight, uint32 diff) override
    {
        Creature* boss = fight.Boss();
        uint64 const now = fight.FightMs();
        RunPending(fight, now);
        for (UnlockBook::Push const& push : _book.TakePushes(now))
            fight.ScheduleCast(push.id, push.inMs, push.priority);
        SyncTribalWard(fight);
        _shards.Update(boss, diff);
        UpdateRiders(fight, diff);
        UpdateSpearChain(fight, now);
    }

    uint8 TribesPerOrder(WyrmthalakFight const& /*fight*/) const override
    {
        return kTribesPerOrder;
    }

    bool AllChampionsAtFirstOrder(WyrmthalakFight const& /*fight*/) const override
    {
        return true;
    }

    void OnChampionSummoned(WyrmthalakFight& fight, Tribe tribe, Creature* champion) override
    {
        if (!champion)
            return;
        DungeonKit::Flex::SetHealth(champion, kChampionHealthAt5, true);
        fight.Log("warhorn-champion", Acore::StringFormat("tribe={} health={}", BrsWyrmthalak::TribeName(tribe),
            champion->GetMaxHealth()));
    }

    void OnChampionDied(WyrmthalakFight& fight, Tribe tribe, Creature* /*champion*/) override
    {
        if (tribe == Tribe::Spirestone)
            _shards.Clear(fight.Boss());
        if (tribe == Tribe::Smolderthorn)
            EndAxeChains(fight, "champion-died");
        Open(fight, UnlockOf(tribe), "champion-died");
    }

    // ---- WT10 Stolen Boulders ---------------------------------------------------------------------------------------

    void OnBoulderLanded(WyrmthalakFight& fight, Position const& at) override
    {
        AddShard(fight, at);
    }

    // ---- WT11 Chained Axes ------------------------------------------------------------------------------------------

    Creature* AxeThrower(WyrmthalakFight& fight) override
    {
        return fight.Champion(Tribe::Smolderthorn);
    }

    void OnAxesLanded(WyrmthalakFight& fight, std::vector<Position> const& spots) override
    {
        Creature* champion = fight.Champion(Tribe::Smolderthorn);
        if (!champion)
            return;
        for (Position const& spot : spots)
            AddAxeChain(fight, spot, champion);
    }

    // ---- WT12 riders that stay --------------------------------------------------------------------------------------

    bool OnRiderCharged(WyrmthalakFight& fight, Creature* rider) override
    {
        if (!rider || !rider->IsAlive())
            return false;
        PruneRiders(fight);
        if (!KeepRider(uint32(_riders.size()), _players))
        {
            fight.Log("warhorn-rider", Acore::StringFormat("kept={} cap={} rides home", _riders.size(),
                kRiderCap.At(_players)));
            return false;
        }
        Creature* boss = fight.Boss();
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        Player* target = DungeonKit::PickPlayer(boss, rule);
        if (!target)
            return false;

        rider->RemoveUnitFlag(UnitFlags(kRiderFlags));
        if (TempSummon* summon = rider->ToTempSummon())
        {
            // B8 summoned it for its 15 s charge: it now stays until killed, its corpse a little longer.
            summon->SetTempSummonType(TEMPSUMMON_CORPSE_TIMED_DESPAWN);
            summon->SetTimer(kRiderCorpseMs);
        }
        DungeonKit::Flex::SetHealth(rider, kRiderHealthAt5, true);
        rider->AddAura(SPELL_WH_RABID_BITE, rider);

        DungeonKit::ChaserSpec spec;
        spec.speed = kRiderChaseSpeed;
        spec.reach = kRiderReach;
        spec.retargetEvery = Ms(kRiderRetargetMs);
        spec.endOnArrive = false;
        spec.fixate = true;
        spec.tauntImmune = true;
        spec.pick.nonTank = false;
        DungeonKit::Chaser& chase = _riders[rider->GetGUID()];
        if (!chase.Start(rider, target, std::move(spec), boss))
        {
            _riders.erase(rider->GetGUID());
            rider->SetUnitFlag(UnitFlags(kRiderFlags));
            return false;
        }
        // Every other fight player at 0 threat (the fixate still picks): a rider whose fixate target dies, feigns
        // death or vanishes always has someone left on its list, so it never evades (an evade strips Rabid Bite and
        // the flex health; R-1-B M4). The Chaser retargets on its own update.
        for (Player* player : fight.FightPlayers())
            if (player != target && player->IsAlive())
                rider->GetThreatMgr().AddThreat(player, 0.f, nullptr, true, true);
        fight.Log("warhorn-rider", Acore::StringFormat("kept={} cap={} on={} health={}", _riders.size(),
            kRiderCap.At(_players), target->GetName(), rider->GetMaxHealth()));
        return true;
    }

    // ---- WT15 the burns ---------------------------------------------------------------------------------------------

    BurnSpec Burn(WyrmthalakFight const& /*fight*/, BurnSpec base) const override
    {
        BurnNumbers in;
        in.length = base.length;
        in.lifeMs = base.lifeMs;
        in.graceMs = base.graceMs;
        in.maxAlive = base.maxAlive;
        BurnNumbers const out = HardModeBurn(in, _book.IsOpen(Unlock::EmpoweredDragonfire));
        base.length = out.length;
        base.lifeMs = out.lifeMs;
        base.graceMs = out.graceMs;
        base.maxAlive = out.maxAlive;
        return base;
    }

    // ---- WT14 Caustic Venom -----------------------------------------------------------------------------------------

    void OnAbilityHit(WyrmthalakFight& fight, Ability /*ability*/, Unit* hit) override
    {
        if (_book.IsOpen(Unlock::CausticVenom))
            Poison(fight.Boss(), hit, 1);
    }

    // ---- the unlocks' casts (B8's queue) ----------------------------------------------------------------------------

    std::optional<uint32> OnCast(WyrmthalakFight& fight, uint32 id) override
    {
        std::optional<Unlock> const unlock = UnlockOfCast(id);
        if (!unlock || !_book.IsOpen(*unlock))
            return std::nullopt;
        uint64 const now = fight.FightMs();
        bool started = false;
        switch (*unlock)
        {
            case Unlock::CausticVenom:          started = StartRoar(fight); break;
            case Unlock::EmpoweredDragonfire:   started = StartSpear(fight); break;
            case Unlock::ShadowflameSpit:       started = StartSpit(fight); break;
        }
        if (!started)
        {
            _book.Refused(*unlock, now);
            return std::nullopt;
        }
        _book.Started(*unlock, now);
        return RuleOf(*unlock).holdMs;
    }

    // ---- WT17 the end -----------------------------------------------------------------------------------------------

    void OnEnd(WyrmthalakFight& fight, bool died) override
    {
        Creature* boss = fight.Boss();
        for (auto& [guid, chase] : _riders)
            if (Creature* rider = ObjectAccessor::GetCreature(*boss, guid))
                chase.Stop(rider);
        _riders.clear();
        _shards.Clear(boss);
        EndAxeChains(fight, died ? "death" : "reset");
        EndSpearChain(fight, died ? "death" : "reset");
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(boss, handle);
        _live.clear();
        _pending.clear();
        boss->RemoveAurasDueToSpell(SPELL_WH_TRIBAL_WARD);
        if (InstanceScript* instance = boss->GetInstanceScript())
        {
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_WH_CAUSTIC_POISON);
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_WH_RABIES);
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_WH_SPEAR_CHAIN);
        }
        // His heroic health back (DD restores the base a script set: put the heroic one back before the evade).
        if (!died && _baseHealth)
            DungeonKit::Flex::SetHealth(boss, _baseHealth, true);
        fight.Log("warhorn-end", Acore::StringFormat("died={} unlocks={}{}{} base={}", died ? 1 : 0,
            _book.IsOpen(Unlock::CausticVenom) ? "V" : "-", _book.IsOpen(Unlock::EmpoweredDragonfire) ? "D" : "-",
            _book.IsOpen(Unlock::ShadowflameSpit) ? "S" : "-", died ? 0 : _baseHealth));
    }

    // ---- `.dbtest brs warhorn` entry points -------------------------------------------------------------------------

    void TestUnlock(WyrmthalakFight& fight, Tribe tribe)
    {
        Open(fight, UnlockOf(tribe), "test");
    }

    bool TestRoar(WyrmthalakFight& fight) { return StartRoar(fight); }
    bool TestSpear(WyrmthalakFight& fight) { return StartSpear(fight); }
    bool TestSpit(WyrmthalakFight& fight) { return StartSpit(fight); }
    bool TestShard(WyrmthalakFight& fight, Position const& at) { return AddShard(fight, at); }

    bool TestOvercharge(WyrmthalakFight& fight)
    {
        Creature* champion = fight.Champion(Tribe::Spirestone);
        if (!champion)
            return false;
        StartOvercharge(fight, champion);
        return true;
    }

    std::string TestState(WyrmthalakFight& fight)
    {
        uint64 const now = fight.FightMs();
        std::string out = Acore::StringFormat("serial={} players={} t={}ms ward={} shards={} axe-chains={} "
            "riders={}/{} spear={} patches={} burns={}", _serial, _players, now,
            DungeonKit::Stacks(fight.Boss(), SPELL_WH_TRIBAL_WARD), _shards.Count(), _axes.size(), _riders.size(),
            kRiderCap.At(_players), _spear.target.IsEmpty() ? "-" : "on", _patches, fight.Burns().size());
        for (Unlock u : kUnlocks)
        {
            std::optional<uint64> const due = _book.DueAt(u);
            out += Acore::StringFormat("\n  {}: {}", UnlockName(u), due ? Acore::StringFormat("open, next cast at {}ms",
                *due) : std::string("locked"));
        }
        if (Creature* spirestone = fight.Champion(Tribe::Spirestone))
            out += Acore::StringFormat("\n  spirestone stolen power {}", DungeonKit::Stacks(spirestone,
                BrsUrok::SPELL_UR_STOLEN_POWER));
        return out;
    }

    // WT14: the roar landed (spell_brs_wyrmthalak_caustic_roar, AfterCast; an interrupted roar never gets here).
    void RoarLanded(WyrmthalakFight& fight)
    {
        Creature* boss = fight.Boss();
        GuidSet const targets = GuidsOf(fight.FightPlayers());
        DungeonKit::RegistryHitSpec spec;
        spec.pct = kRoarPct;
        spec.school = SPELL_SCHOOL_NATURE;
        spec.spellId = SPELL_WH_CAUSTIC_ROAR_HIT;
        spec.weakened = false;
        spec.tag = TAG_WH_ROAR;
        spec.onHit = OnHorn([](WarHorn& /*horn*/, WyrmthalakFight& f, Unit* hit)
        {
            Poison(f.Boss(), hit, kRoarPoisonStacks);
        });
        Keep(fight, DungeonKit::RegistryHit(boss, targets, spec));
        fight.Log("warhorn-roar-landed", Acore::StringFormat("players={}", targets.size()));
    }

private:
    struct Pending
    {
        uint64 atMs = 0;
        std::function<void(WarHorn&, WyrmthalakFight&)> fn;
    };

    struct AxeChain
    {
        uint32 id = 0;
        Position spot;
        ObjectGuid anchor;
        ObjectGuid object;
        MechanicHandle chain;
    };

    struct SpearChain
    {
        ObjectGuid target;
        ObjectGuid anchor;
        MechanicHandle chain;
        uint64 untilMs = 0;
    };

    static uint32& NextSerial()
    {
        static uint32 serial = 0;
        return serial;
    }

    // A registry callback that finds this pull's hard mode again (never a captured `this`: the registry may outlive
    // it).
    template <class Fn>
    std::function<void(Unit*)> OnHorn(Fn fn) const
    {
        Map* map = _map;
        ObjectGuid const boss = _bossGuid;
        uint32 const serial = _serial;
        return [map, boss, serial, fn](Unit* hit)
        {
            WyrmthalakFight* fight = nullptr;
            if (WarHorn* horn = Find(map, boss, serial, &fight))
                if (hit)
                    fn(*horn, *fight, hit);
        };
    }

    void Later(WyrmthalakFight& fight, uint32 inMs, std::function<void(WarHorn&, WyrmthalakFight&)> fn)
    {
        _pending.push_back({ fight.FightMs() + inMs, std::move(fn) });
    }

    void RunPending(WyrmthalakFight& fight, uint64 now)
    {
        if (_pending.empty())
            return;
        std::vector<Pending> due;
        std::vector<Pending> later;
        for (Pending& p : _pending)
            (p.atMs <= now ? due : later).push_back(std::move(p));
        _pending = std::move(later);
        for (Pending& p : due)
            p.fn(*this, fight);
    }

    void Keep(WyrmthalakFight& fight, MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        fight.Track(handle);
    }

    // Kill order (SP boss data, hard mode): the Bloodaxe Champion and the riders, the Smolderthorn Champion, the
    // Spirestone Champion, then him. Interrupt: Caustic Roar (expected). Dispels: Caustic Poison and Rabies (rewards).
    // B8's taunt swap and assist-tank entries at 10 stay.
    void Describe(Creature* boss)
    {
        Mechanic::EditDescriptor(boss, [](BossMechanics::Descriptor& d)
        {
            for (BossMechanics::TargetEntry& e : d.targets)
            {
                if (e.who != BossMechanics::Who::Dps)
                    continue;
                if (e.entry == NPC_BRS_BLOODAXE_CHAMPION)
                    e.priority = 4;
                else if (e.entry == NPC_BRS_SMOLDERTHORN_CHAMPION)
                    e.priority = 3;
                else if (e.entry == NPC_BRS_SPIRESTONE_CHAMPION)
                    e.priority = 2;
            }
            d.targets.push_back(BossMechanics::TargetEntry(NPC_BRS_BLOODAXE_WORG_RIDER, 4).AoeOk());
            d.interrupts.emplace_back(NPC_WYRMTHALAK, SPELL_WH_CAUSTIC_ROAR, kRoarKickPriority,
                Ms(RuleOf(Unlock::CausticVenom).everyMs));
            d.dispels.emplace_back(SPELL_WH_CAUSTIC_POISON, 1);
            d.dispels.emplace_back(SPELL_WH_RABIES, 1);
        });
    }

    void Open(WyrmthalakFight& fight, Unlock unlock, char const* why)
    {
        if (!_book.Open(unlock, fight.FightMs()))
            return;
        std::optional<uint64> const due = _book.DueAt(unlock);
        fight.Log("warhorn-unlock", Acore::StringFormat("unlock={} why={} first-cast-at={}ms", UnlockName(unlock),
            why, due ? *due : 0));
    }

    // WT13: one stack per living champion.
    void SyncTribalWard(WyrmthalakFight& fight)
    {
        uint32 alive = 0;
        for (Tribe t : BrsWyrmthalak::kTribes)
            if (fight.Champion(t))
                ++alive;
        Creature* boss = fight.Boss();
        uint32 const want = TribalWardStacks(alive);
        uint32 const have = DungeonKit::Stacks(boss, SPELL_WH_TRIBAL_WARD, boss->GetGUID());
        if (want == have)
            return;
        DungeonKit::AddStacks(boss, SPELL_WH_TRIBAL_WARD, int32(want) - int32(have), boss, kTribalWardMaxStacks);
        fight.Log("warhorn-tribal-ward", Acore::StringFormat("champions={} taken={}%", alive,
            TribalWardTakenPct(alive)));
    }

    // ---- WT10 -------------------------------------------------------------------------------------------------------

    bool AddShard(WyrmthalakFight& fight, Position const& at)
    {
        Creature* champion = fight.Champion(Tribe::Spirestone);
        if (!champion)
            return false;
        DungeonKit::CrawlPickupSpec spec = BrsStolenMagic::ShardSpec(Ms(kShardWaitMs), TAG_WH_SHARD);
        Map* map = _map;
        ObjectGuid const boss = _bossGuid;
        uint32 const serial = _serial;
        spec.onPick = [map, boss, serial](Player* taker, Position const&)
        {
            WyrmthalakFight* f = nullptr;
            if (Find(map, boss, serial, &f))
                f->Log("warhorn-shard-taken", Acore::StringFormat("by={}", taker ? taker->GetName() : "none"));
        };
        spec.onReach = [map, boss, serial](ObjectGuid goal, Position const&)
        {
            WyrmthalakFight* f = nullptr;
            if (WarHorn* horn = Find(map, boss, serial, &f))
                horn->ShardReached(*f, goal);
        };
        uint32 const id = _shards.Add(fight.Boss(), at, std::move(spec), { champion->GetGUID(), std::nullopt });
        fight.Log("warhorn-shard", Acore::StringFormat("at=({:.1f},{:.1f}) id={} live={}", at.GetPositionX(),
            at.GetPositionY(), id, _shards.Count()));
        return id != 0;
    }

    void ShardReached(WyrmthalakFight& fight, ObjectGuid goal)
    {
        Creature* champion = fight.Champion(Tribe::Spirestone);
        if (!champion || champion->GetGUID() != goal)
            return;
        uint32 const stacks = BrsStolenMagic::AddStolenPower(champion, kStolenPowerCap);
        fight.Log("warhorn-stolen-power", Acore::StringFormat("stacks={}", stacks));
        if (OverchargesAt(stacks) && !_overcharging)
            StartOvercharge(fight, champion);
    }

    // The champion's 3 s cast (Urok's bar), then 40% to every player within 100 yd and his stacks gone. The hit is his
    // fight's (owner Wyrmthalak: the ledger, the healers' view); the champion casts the looks.
    void StartOvercharge(WyrmthalakFight& fight, Creature* champion)
    {
        _overcharging = true;
        DungeonKit::CastBar(champion, BrsUrok::SPELL_UR_OVERCHARGE_CAST);
        ObjectGuid const guid = champion->GetGUID();
        fight.Log("warhorn-overcharge", Acore::StringFormat("cast={}ms", BrsUrok::kOverchargeCastMs));
        Later(fight, BrsUrok::kOverchargeCastMs, [guid](WarHorn& horn, WyrmthalakFight& f)
        {
            horn._overcharging = false;
            Creature* c = ObjectAccessor::GetCreature(*f.Boss(), guid);
            if (!c || !c->IsAlive())
                return;
            c->CastSpell(c, BrsUrok::SPELL_UR_OVERCHARGE_LOOK, true);
            c->RemoveAurasDueToSpell(BrsUrok::SPELL_UR_STOLEN_POWER);
            DungeonKit::RegistryHitSpec spec;
            spec.pct = kOverchargePct;
            spec.school = SPELL_SCHOOL_ARCANE;
            spec.spellId = BrsUrok::SPELL_UR_OVERCHARGE;
            spec.weakened = false;
            spec.tag = TAG_WH_OVERCHARGE;
            GuidSet const targets = BrsStolenMagic::PlayersNear(c, kOverchargeRangeYd);
            horn.Keep(f, DungeonKit::RegistryHit(f.Boss(), targets, spec));
            f.Log("warhorn-overcharge-lands", Acore::StringFormat("players={}", targets.size()));
        });
    }

    // ---- WT11 -------------------------------------------------------------------------------------------------------

    void AddAxeChain(WyrmthalakFight& fight, Position const& spot, Creature* champion)
    {
        Creature* boss = fight.Boss();
        AxeChain axe;
        axe.id = ++_nextAxe;
        axe.spot = spot;
        float const o = spot.GetOrientation();
        if (GameObject* go = boss->SummonGameObject(GO_BRS_STUCK_AXE, spot.GetPositionX(), spot.GetPositionY(),
            spot.GetPositionZ(), o, 0.f, 0.f, std::sin(o * 0.5f), std::cos(o * 0.5f), kAxeObjectLifeSec))
            axe.object = go->GetGUID();
        if (Creature* anchor = boss->SummonCreature(NPC_BRS_CHAIN_ANCHOR, spot.GetPositionX(), spot.GetPositionY(),
            spot.GetPositionZ() + kAxeAnchorLiftYd, o, TEMPSUMMON_TIMED_DESPAWN, kAxeObjectLifeSec * 1000))
        {
            anchor->SetReactState(REACT_PASSIVE);
            axe.anchor = anchor->GetGUID();
            // Skadi's Harpoon Chain beam from the axe to him (Voone's chain spell; the anchor channels it).
            anchor->CastSpell(champion, BrsVoone::SPELL_VO_CHAINED_AXE, true);
            // The chain: both ends live (the anchor stands still, the champion moves), 2 yd, a crossing every 2 s from
            // 2 s to 8 s (the G1 drill's row 5).
            MechanicRef ref = Mechanic::Line(boss, BossMechanics::Anchor(anchor), BossMechanics::Anchor(champion),
                kAxeChainWidth, Ms(kAxeChainWarnMs));
            ref.Persistent(Ms(kAxeChainLifeMs - kAxeChainWarnMs), Ms(kAxeChainTickMs)).Damage(kAxeChainPct)
                .TankDamage(kAxeChainPct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_WH_AXE_CHAIN_HIT).Weakened()
                .Within(fight.LedgeBounds()).Tag(TAG_WH_AXE_CHAIN);
            axe.chain = ref.Handle();
            Keep(fight, axe.chain);
        }
        uint32 const id = axe.id;
        _axes.push_back(axe);
        Later(fight, kAxeChainLifeMs, [id](WarHorn& horn, WyrmthalakFight& f) { horn.Haul(f, id); });
        fight.Log("warhorn-axe-chain", Acore::StringFormat("id={} at=({:.1f},{:.1f}) chain={} live={}", id,
            spot.GetPositionX(), spot.GetPositionY(), axe.chain ? 1 : 0, _axes.size()));
    }

    // The chain goes taut: the 3 yd haul from the axe to where he stands now (frozen, the G1 drill's tag 6), 1.5 s.
    void Haul(WyrmthalakFight& fight, uint32 id)
    {
        auto it = std::find_if(_axes.begin(), _axes.end(), [id](AxeChain const& a) { return a.id == id; });
        if (it == _axes.end())
            return;
        Creature* boss = fight.Boss();
        Creature* champion = fight.Champion(Tribe::Smolderthorn);
        if (it->chain)
            Mechanic::Cancel(boss, it->chain);
        it->chain = MechanicHandle();
        if (!champion)
        {
            RemoveAxe(fight, *it, false);
            _axes.erase(it);
            return;
        }
        Position const to = champion->GetPosition();
        MechanicRef ref = Mechanic::Line(boss, BossMechanics::Anchor(it->spot), BossMechanics::Anchor(to), kHaulWidth,
            Ms(kHaulWarnMs));
        ref.Damage(kHaulPct).TankDamage(kHaulPct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_WH_HAUL).Weakened()
            .Within(fight.LedgeBounds()).Tag(TAG_WH_HAUL);
        if (kHaulExcludeChampionEnd > 0.f)
            ref.ExcludeSourceEnd(kHaulExcludeChampionEnd);
        Keep(fight, ref.Handle());
        fight.Log("warhorn-haul", Acore::StringFormat("id={} from=({:.1f},{:.1f}) to=({:.1f},{:.1f}) warn={}ms", id,
            it->spot.GetPositionX(), it->spot.GetPositionY(), to.GetPositionX(), to.GetPositionY(), kHaulWarnMs));
        Later(fight, kHaulWarnMs, [id](WarHorn& horn, WyrmthalakFight& f)
        {
            auto axe = std::find_if(horn._axes.begin(), horn._axes.end(),
                [id](AxeChain const& a) { return a.id == id; });
            if (axe == horn._axes.end())
                return;
            horn.RemoveAxe(f, *axe, true);
            horn._axes.erase(axe);
        });
    }

    // The axe, its anchor and its chain go; `flyHome`: the anchor throws the axe's flight to the champion first.
    void RemoveAxe(WyrmthalakFight& fight, AxeChain& axe, bool flyHome)
    {
        Creature* boss = fight.Boss();
        if (axe.chain)
            Mechanic::Cancel(boss, axe.chain);
        axe.chain = MechanicHandle();
        if (Creature* anchor = ObjectAccessor::GetCreature(*boss, axe.anchor))
        {
            anchor->InterruptNonMeleeSpells(true);
            if (flyHome)
                if (Creature* champion = fight.Champion(Tribe::Smolderthorn))
                    anchor->CastSpell(champion, BrsWyrmthalak::SPELL_WT_THROW_AXE, true);
            anchor->DespawnOrUnsummon(Milliseconds(flyHome ? 1000 : 0));
        }
        if (GameObject* go = ObjectAccessor::GetGameObject(*boss, axe.object))
        {
            if (go->GetOwnerGUID() == boss->GetGUID())
                boss->RemoveGameObject(go, true);
            else
                go->DespawnOrUnsummon();
        }
        axe.anchor.Clear();
        axe.object.Clear();
    }

    void EndAxeChains(WyrmthalakFight& fight, char const* why)
    {
        if (_axes.empty())
            return;
        std::size_t const n = _axes.size();
        for (AxeChain& axe : _axes)
            RemoveAxe(fight, axe, false);
        _axes.clear();
        fight.Log("warhorn-axe-chains-end", Acore::StringFormat("why={} axes={}", why, n));
    }

    // ---- WT12 -------------------------------------------------------------------------------------------------------

    void PruneRiders(WyrmthalakFight& fight)
    {
        Creature* boss = fight.Boss();
        for (auto it = _riders.begin(); it != _riders.end();)
        {
            Creature* rider = ObjectAccessor::GetCreature(*boss, it->first);
            if (!rider || !rider->IsAlive() || !rider->IsInWorld())
                it = _riders.erase(it);
            else
                ++it;
        }
    }

    void UpdateRiders(WyrmthalakFight& fight, uint32 diff)
    {
        if (_riders.empty())
            return;
        PruneRiders(fight);
        Creature* boss = fight.Boss();
        for (auto& [guid, chase] : _riders)
            if (Creature* rider = ObjectAccessor::GetCreature(*boss, guid))
                chase.Update(rider, diff);
    }

    // ---- WT14 -------------------------------------------------------------------------------------------------------

    bool StartRoar(WyrmthalakFight& fight)
    {
        Creature* boss = fight.Boss();
        if (fight.FightPlayers().empty())
            return false;
        if (boss->CastSpell(boss, SPELL_WH_CAUSTIC_ROAR, false) != SPELL_CAST_OK)
            return false;
        boss->AI()->Talk(BrsWyrmthalak::EMOTE_WT_CAUSTIC_ROAR);
        fight.Log("warhorn-roar", Acore::StringFormat("cast={}ms", kRoarCastMs));
        return true;
    }

    // ---- WT15 -------------------------------------------------------------------------------------------------------

    bool StartSpear(WyrmthalakFight& fight)
    {
        Creature* boss = fight.Boss();
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.tankIfAlone = true;
        Player* target = DungeonKit::PickPlayer(boss, rule);
        if (!target)
            return false;
        EndSpearChain(fight, "new-spear");
        boss->AI()->Talk(BrsWyrmthalak::EMOTE_WT_SPEAR, target);
        boss->CastSpell(target, SPELL_WH_SPEAR_THROW, true);
        float const distance = boss->GetDistance(target);
        uint32 const flightMs = uint32(distance / kSpearMissileSpeed * 1000.f);
        ObjectGuid const guid = target->GetGUID();
        Later(fight, flightMs, [guid](WarHorn& horn, WyrmthalakFight& f) { horn.SpearLands(f, guid); });
        fight.Log("warhorn-spear", Acore::StringFormat("on={} flight={}ms", target->GetName(), flightMs));
        return true;
    }

    void SpearLands(WyrmthalakFight& fight, ObjectGuid targetGuid)
    {
        Creature* boss = fight.Boss();
        Player* target = ObjectAccessor::GetPlayer(*boss, targetGuid);
        if (!target || !target->IsAlive())
            return;
        DungeonKit::RegistryHitSpec spec;
        spec.pct = kSpearImpactPct;
        spec.school = SPELL_SCHOOL_NORMAL;
        spec.spellId = SPELL_WH_SPEAR_IMPACT;
        spec.weakened = false;
        spec.tag = TAG_WH_SPEAR;
        spec.onHit = OnHorn([](WarHorn& horn, WyrmthalakFight& f, Unit* hit)
        {
            if (horn._book.IsOpen(Unlock::CausticVenom))
                Poison(f.Boss(), hit, 1);
        });
        GuidSet targets;
        targets.insert(targetGuid);
        Keep(fight, DungeonKit::RegistryHit(boss, targets, spec));

        // The chain: an anchor on him channels the beam at the speared player (its aura keeps them off their own
        // chain); a live 2 yd line from him to them for 20 s.
        _spear.target = targetGuid;
        _spear.untilMs = fight.FightMs() + kSpearChainMs;
        if (Creature* anchor = boss->SummonCreature(NPC_BRS_CHAIN_ANCHOR, boss->GetPositionX(), boss->GetPositionY(),
            boss->GetPositionZ() + kAxeAnchorLiftYd, boss->GetOrientation(), TEMPSUMMON_TIMED_DESPAWN,
            kSpearChainMs + 1000))
        {
            anchor->SetReactState(REACT_PASSIVE);
            anchor->GetMotionMaster()->MoveFollow(boss, 0.f, 0.f);
            anchor->CastSpell(target, SPELL_WH_SPEAR_CHAIN, true);
            _spear.anchor = anchor->GetGUID();
        }
        if (!target->HasAura(SPELL_WH_SPEAR_CHAIN))
            boss->AddAura(SPELL_WH_SPEAR_CHAIN, target);    // no beam, but the speared player stays off the line
        BossMechanics::Eligibility notSpeared;
        notSpeared.auraSpell = SPELL_WH_SPEAR_CHAIN;
        notSpeared.maxStacks = 0;
        MechanicRef ref = Mechanic::Line(boss, BossMechanics::Anchor(boss), BossMechanics::Anchor(target),
            kSpearChainWidth, Ms(kSpearChainWarnMs));
        ref.Persistent(Ms(kSpearChainMs - kSpearChainWarnMs), Ms(kSpearChainTickMs)).Damage(kSpearChainPct)
            .TankDamage(kSpearChainPct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_WH_SPEAR_CHAIN_HIT)
            .WeakenedOncePerPlayer().Eligible(notSpeared).Within(fight.LedgeBounds()).Tag(TAG_WH_SPEAR_CHAIN);
        _spear.chain = ref.Handle();
        Keep(fight, _spear.chain);
        fight.Log("warhorn-spear-lands", Acore::StringFormat("on={} chain={} anchor={}", target->GetName(),
            _spear.chain ? 1 : 0, _spear.anchor.IsEmpty() ? 0 : 1));
    }

    // The chain ends after 20 s, or with the speared player.
    void UpdateSpearChain(WyrmthalakFight& fight, uint64 now)
    {
        if (_spear.target.IsEmpty())
            return;
        Player* target = ObjectAccessor::GetPlayer(*fight.Boss(), _spear.target);
        if (now >= _spear.untilMs)
            EndSpearChain(fight, "expired");
        else if (!target || !target->IsAlive())
            EndSpearChain(fight, "target-gone");
    }

    void EndSpearChain(WyrmthalakFight& fight, char const* why)
    {
        if (_spear.target.IsEmpty())
            return;
        Creature* boss = fight.Boss();
        if (_spear.chain)
            Mechanic::Cancel(boss, _spear.chain);
        if (Creature* anchor = ObjectAccessor::GetCreature(*boss, _spear.anchor))
        {
            anchor->InterruptNonMeleeSpells(true);
            anchor->DespawnOrUnsummon();
        }
        if (Player* target = ObjectAccessor::GetPlayer(*boss, _spear.target))
            target->RemoveAurasDueToSpell(SPELL_WH_SPEAR_CHAIN);
        fight.Log("warhorn-spear-chain-end", Acore::StringFormat("why={}", why));
        _spear = SpearChain();
    }

    // ---- WT16 -------------------------------------------------------------------------------------------------------

    bool StartSpit(WyrmthalakFight& fight)
    {
        std::vector<Player*> const players = fight.FightPlayers();
        if (players.empty())
            return false;
        Creature* boss = fight.Boss();
        std::vector<Position> spots;
        for (Player* player : players)
        {
            Position const at = player->GetPosition();
            MechanicRef ref = Mechanic::Circle(boss, at, kSpitRadius, Ms(kSpitWarnMs));
            ref.Damage(kSpitPct).TankDamage(kSpitPct).School(SPELL_SCHOOL_SHADOW).Spell(SPELL_WH_SPIT).Weakened()
                .Within(fight.LedgeBounds()).Tag(TAG_WH_SPIT);
            ref.OnHit(OnHorn([](WarHorn& horn, WyrmthalakFight& f, Unit* hit)
            {
                if (horn._book.IsOpen(Unlock::CausticVenom))
                    Poison(f.Boss(), hit, 1);
            }));
            Keep(fight, ref.Handle());
            spots.push_back(at);
            float const distance = boss->GetDistance(at);
            Later(fight, BrsWyrmthalak::MissileDelayMs(distance, kSpitMissileSpeed, kSpitWarnMs),
                [at](WarHorn& /*horn*/, WyrmthalakFight& f)
                {
                    f.Boss()->CastSpell(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(),
                        SPELL_WH_SPIT_MISSILE, true);
                });
        }
        uint32 const keep = kSpitPatches.At(_players);
        std::vector<uint32> const picks = PickIndices(uint32(spots.size()), keep,
            [](uint32 m) { return m ? urand(0, m - 1) : 0u; });
        std::vector<bool> patch(spots.size(), false);
        for (uint32 i : picks)
            patch[i] = true;
        for (std::size_t i = 0; i < spots.size(); ++i)
        {
            Position const at = spots[i];
            bool const stays = patch[i];
            Later(fight, kSpitWarnMs, [at, stays](WarHorn& horn, WyrmthalakFight& f)
            {
                f.Boss()->CastSpell(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), SPELL_WH_SPIT_LANDING,
                    true);
                if (stays)
                    horn.AddPatch(f, at);
            });
        }
        fight.Log("warhorn-spit", Acore::StringFormat("circles={} patches={}", spots.size(), picks.size()));
        return true;
    }

    // A burning patch where a spit landed: 40 s, 5% a second (its first tick a second after the landing), Weakened
    // once per player (section 7 #25); the black flame look under it (B8's).
    void AddPatch(WyrmthalakFight& fight, Position const& at)
    {
        Creature* boss = fight.Boss();
        MechanicRef ref = Mechanic::Circle(boss, at, kSpitRadius, Ms(kPatchTickMs));
        ref.Persistent(Ms(kPatchLifeMs - kPatchTickMs), Ms(kPatchTickMs)).Damage(kPatchPct).TankDamage(kPatchPct)
            .School(SPELL_SCHOOL_SHADOW).Spell(SPELL_WH_SPIT_PATCH).WeakenedOncePerPlayer().NoFillTimer()
            .Within(fight.LedgeBounds()).Tag(TAG_WH_SPIT_PATCH);
        Keep(fight, ref.Handle());
        ObjectGuid const look = fight.SpawnFlamePatch(at, kPatchLifeMs);
        ++_patches;
        Later(fight, kPatchLifeMs, [](WarHorn& horn, WyrmthalakFight&) { if (horn._patches) --horn._patches; });
        fight.Log("warhorn-spit-patch", Acore::StringFormat("at=({:.1f},{:.1f}) look={} live={}", at.GetPositionX(),
            at.GetPositionY(), look.IsEmpty() ? 0 : 1, _patches));
    }

    uint32 const _serial;
    Map* _map = nullptr;
    ObjectGuid _bossGuid;
    uint8 _players = 0;
    uint32 _baseHealth = 0;
    UnlockBook _book;
    DungeonKit::CrawlPickups _shards;
    bool _overcharging = false;
    std::vector<AxeChain> _axes;
    uint32 _nextAxe = 0;
    std::map<ObjectGuid, DungeonKit::Chaser> _riders;
    SpearChain _spear;
    uint32 _patches = 0;
    std::vector<MechanicHandle> _live;
    std::vector<Pending> _pending;
};

// WT14 Caustic Roar 210293: the cast landed (an interrupted cast never reaches AfterCast).
class spell_brs_wyrmthalak_caustic_roar : public SpellScript
{
    PrepareSpellScript(spell_brs_wyrmthalak_caustic_roar);

    void Landed()
    {
        Creature* boss = GetCaster() ? GetCaster()->ToCreature() : nullptr;
        if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
            return;
        auto* fight = dynamic_cast<WyrmthalakFight*>(boss->AI());
        if (auto* horn = fight ? dynamic_cast<WarHorn*>(fight->ActiveHardMode()) : nullptr)
            horn->RoarLanded(*fight);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_brs_wyrmthalak_caustic_roar::Landed);
    }
};

// The Bloodaxe War Horn 301255 (a goober at the ramp head; heroic only by its spawn mask): blowing it before the pull
// lights the hard mode. Not selectable while it cannot be blown (in combat, after the kill, already lit).
struct go_brs_war_horn : public GameObjectAI
{
    explicit go_brs_war_horn(GameObject* go) : GameObjectAI(go) { }

    void UpdateAI(uint32 diff) override
    {
        if (_pollMs > diff)
        {
            _pollMs -= diff;
            return;
        }
        _pollMs = kHornPollMs;
        bool const usable = RefusalAt(me) == HornRefusal::None;
        bool const flagged = me->HasGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        if (usable && flagged)
            me->RemoveGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        else if (!usable && !flagged)
            me->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
    }

    bool GossipHello(Player* player, bool reportUse) override
    {
        if (reportUse || !player)
            return true;
        if (BlowHorn(me, player) == HornRefusal::None)
        {
            me->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
            _pollMs = kHornPollMs;
        }
        return true;
    }

private:
    uint32 _pollMs = 0;
};

namespace
{
    // The running pull's hard mode (an error and nullptr when there is none).
    WarHorn* FindHorn(ChatHandler* handler, WyrmthalakFight*& fight)
    {
        Creature* boss = BrsTest::FindBoss(handler, NPC_WYRMTHALAK);
        if (!boss)
            return nullptr;
        fight = boss->IsAIEnabled ? dynamic_cast<WyrmthalakFight*>(boss->AI()) : nullptr;
        if (!fight)
        {
            handler->SendErrorMessage("{}", "Wyrmthalak is not running boss_overlord_wyrmthalak_rework.");
            return nullptr;
        }
        auto* horn = dynamic_cast<WarHorn*>(fight->ActiveHardMode());
        if (!horn)
            handler->SendErrorMessage("{}", "No hard mode pull is running (blow the horn on heroic, then pull him).");
        return horn;
    }

    Player* Gm(ChatHandler* handler)
    {
        return handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        if (!BrsTest::RequireBlackrockSpire(handler))
            return false;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
        {
            handler->SendErrorMessage("No instance script on this map.");
            return false;
        }
        handler->PSendSysMessage("warhorn: flag {}, kill {}, boss {}, heroic {}", instance->GetData(DATA_WAR_HORN),
            DungeonTest::StateName(instance->GetBossState(BOSS_WAR_HORN)),
            DungeonTest::StateName(instance->GetBossState(BOSS_WYRMTHALAK)),
            handler->GetPlayer()->GetMap()->IsHeroic() ? 1 : 0);
        return true;
    }

    // `.dbtest brs warhorn blow`: the horn as a player blows it (the same refusals), from where the GM stands.
    bool HandleBlow(ChatHandler* handler)
    {
        if (!BrsTest::RequireBlackrockSpire(handler))
            return false;
        Player* gm = Gm(handler);
        HornRefusal const r = BlowHorn(gm, gm);
        if (r != HornRefusal::None)
        {
            handler->SendErrorMessage("{}", HornRefusalText(r));
            return false;
        }
        handler->PSendSysMessage("{}", "The war horn sounds: the next pull is the hard mode (WT9).");
        return true;
    }

    // `.dbtest brs warhorn clear`: puts the flag out (refused while he fights).
    bool HandleClear(ChatHandler* handler)
    {
        if (!BrsTest::RequireBlackrockSpire(handler))
            return false;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
            return false;
        instance->SetData(DATA_WAR_HORN, 0);
        handler->PSendSysMessage("warhorn: flag {}", instance->GetData(DATA_WAR_HORN));
        return true;
    }

    bool HandleState(ChatHandler* handler)
    {
        WyrmthalakFight* fight = nullptr;
        WarHorn* horn = FindHorn(handler, fight);
        if (!horn)
            return false;
        handler->PSendSysMessage("warhorn: {}", horn->TestState(*fight));
        return true;
    }

    // `.dbtest brs warhorn unlock <tribe>`: that champion's unlock now, as if it had died (it stays alive).
    bool HandleUnlock(ChatHandler* handler, std::string tribeName)
    {
        std::optional<Tribe> const tribe = BrsWyrmthalak::TribeByName(tribeName.c_str());
        if (!tribe)
        {
            handler->SendErrorMessage("{}", "Tribe: spirestone, smolderthorn or bloodaxe.");
            return false;
        }
        WyrmthalakFight* fight = nullptr;
        WarHorn* horn = FindHorn(handler, fight);
        if (!horn)
            return false;
        horn->TestUnlock(*fight, *tribe);
        handler->PSendSysMessage("warhorn: {} unlocked.", UnlockName(UnlockOf(*tribe)));
        return true;
    }

    template <bool (WarHorn::*Fire)(WyrmthalakFight&)>
    bool HandleFire(ChatHandler* handler, char const* what)
    {
        WyrmthalakFight* fight = nullptr;
        WarHorn* horn = FindHorn(handler, fight);
        if (!horn)
            return false;
        bool const ok = (horn->*Fire)(*fight);
        handler->PSendSysMessage("warhorn: {} {}.", what, ok ? "now" : "refused (no target or no champion)");
        return ok;
    }

    bool HandleRoar(ChatHandler* handler) { return HandleFire<&WarHorn::TestRoar>(handler, "Caustic Roar (WT14)"); }
    bool HandleSpear(ChatHandler* handler) { return HandleFire<&WarHorn::TestSpear>(handler, "Spear Chain (WT15)"); }
    bool HandleSpit(ChatHandler* handler) { return HandleFire<&WarHorn::TestSpit>(handler, "Shadowflame Spit (WT16)"); }
    bool HandleOvercharge(ChatHandler* handler)
    {
        return HandleFire<&WarHorn::TestOvercharge>(handler, "the Spirestone Champion's Overcharge (WT10)");
    }

    // `.dbtest brs warhorn shard`: a Stolen Magic shard at the GM's feet, crawling to the Spirestone Champion (WT10).
    bool HandleShard(ChatHandler* handler)
    {
        WyrmthalakFight* fight = nullptr;
        WarHorn* horn = FindHorn(handler, fight);
        Player* gm = Gm(handler);
        if (!horn || !gm)
            return false;
        bool const ok = horn->TestShard(*fight, gm->GetPosition());
        handler->PSendSysMessage("warhorn: a shard {}.", ok ? "at your feet" : "refused (no Spirestone Champion)");
        return ok;
    }

    ChatCommandTable const& WarHornTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,       SEC_GAMEMASTER, Console::No },
            { "blow",       HandleBlow,       SEC_GAMEMASTER, Console::No },
            { "clear",      HandleClear,      SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,      SEC_GAMEMASTER, Console::No },
            { "unlock",     HandleUnlock,     SEC_GAMEMASTER, Console::No },
            { "roar",       HandleRoar,       SEC_GAMEMASTER, Console::No },
            { "spear",      HandleSpear,      SEC_GAMEMASTER, Console::No },
            { "spit",       HandleSpit,       SEC_GAMEMASTER, Console::No },
            { "shard",      HandleShard,      SEC_GAMEMASTER, Console::No },
            { "overcharge", HandleOvercharge, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_brs_wyrmthalak_hard_mode()
{
    BrsWyrmthalak::RegisterWyrmthalakHardMode([](Creature*) { return std::make_unique<WarHorn>(); });
    RegisterDungeonReworkGameObjectAI(go_brs_war_horn, BlackrockSpireRework::kInstanceScriptName);
    RegisterSpellScript(spell_brs_wyrmthalak_caustic_roar);
    BrsTest::RegisterBoss(kLogKey, WarHornTestCommands());
}
