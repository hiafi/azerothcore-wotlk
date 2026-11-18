/*
 * mod-dungeon-bosses, Blackrock Depths D10: Fineous Darkvire (9056), "the thief who would be master builder", a
 * rare-style mini-boss with no encounter credit (ruling 46), and the Guzzler rope (rulings 66, 67). Build spec:
 * docs/dungeons/blackrock-depths-2-shadowforge-city.md "Fineous Darkvire" (FD1, FD2, the rope), handoff sections 3.4
 * / 3.5 row D10, 3.6, 3.7, 3.8. Replaces his SmartAI (rows 0-5: Devotion Aura, two Holy Lights, Holy Strike, Kick,
 * Seal of Reckoning; rev_blackrock_depths_skeleton.sql drops them); bound by apps/dbc-tools
 * source/npcs/blackrock_depths/fineous.py. The patrol (path 476310) is kept: it is the creature's own movement type.
 * Pure rules: FineousLogic.h.
 *
 *   Stock kit    Devotion Aura on the pull; Holy Strike on the victim at 3 s, then every 6 to 8.5 s; Kick (a 6 s
 *                lockout) on a player casting within 5 yd, checked at 12 s and every 7 s after; Seal of Reckoning
 *                once at 20%. All stock spells, kept as they were.
 *   FD2 Holy    twice, once at 60% and once at 40% health: a 2.5 s interruptible cast (211121, a copy of the stock
 *       Light   heal: 4% of his health, so it scales with the 50,000 / 80,000). Neither repeats, so a kick that lands
 *                is a real gain; a descriptor entry names it for the bots.
 *   FD1 Shoddy   at 8 s (heroic 6 s), then every 15 s (heroic 12 s): a pillar goes into the ramp at a random
 *       Construc-  player's spot (the tank too, ruling 88; never one on the two narrow corners, 3-6 yd wide), and 3 s
 *       tion       later it collapses in a 6 yd circle (a registry circle): 25% (heroic 40%) + Weakened. No knockback
 *                  (the ramp rings an open drop).
 *   Death        Ironfel and the rest of his loot are the loot pass's; the script adds the Guzzler rope (item 70622)
 *                once per instance, free for all (every group member may loot his own: HANDOFF section 10), and a
 *                copy of Franclorn's Spirit says one line by the corpse.
 *   The rope     item 70622's use spell (211261, spell_brd_guzzler_rope) works only within 12 yd of the climb spot
 *                behind Lord Incendius (the Anvil's bulge) and hangs the rope for the rest of the instance (the
 *                instance's saved DATA_GUZZLER_ROPE); the hanging rope (GO 301282, go_brd_hanging_rope) is a static
 *                spawn there that the instance's state shows and hides, so it is back after every reload; a click on
 *                it moves the player to the floor past the Bar Door.
 *
 * Every timer runs on the AI's own clock, never on BossAI's scheduler (a cast bar pauses that one). Every firing logs
 * one INFO line "brd fineous <mechanic> ..." (module.dungeonbosses); `.dbtest brd fineous <mechanic>` fires one on
 * demand.
 */

#include "ArenaGuard.h"
#include "BlackrockDepthsKit.h"
#include "BlackrockDepthsRework.h"
#include "BlackrockDepthsTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "FineousLogic.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "Group.h"
#include "InstanceScript.h"
#include "LootMgr.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "WorldSession.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdFineous;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "fineous";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // The map's rope state (ROPE_NONE when there is no instance).
    uint32 RopeStateOf(WorldObject const* where)
    {
        InstanceScript* instance = where ? where->GetInstanceScript() : nullptr;
        return instance ? instance->GetData(DATA_GUZZLER_ROPE) : uint32(ROPE_NONE);
    }
}

// Fineous Darkvire 9056
struct npc_fineous_darkvire_rework : public BossAI
{
    explicit npc_fineous_darkvire_rework(Creature* creature)
        : BossAI(creature, BOSS_FINEOUS), _arena(RampArena(), LeashOptions(kBossLogName)) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

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

        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        OnBossPull(me, kBossLogName);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_FINEOUS;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);

        bool const heroic = IsHeroicMap(me);
        DoCastSelf(SPELL_FD_DEVOTION_AURA);
        _strikeClock.Start(_clockMs, kHolyStrikeFirstMs);
        _kickClock.Start(_clockMs, kKickFirstMs);
        _shoddyClock.Start(_clockMs, kShoddyFirstMs(heroic));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f}) rope={}", heroic ? 1 : 0, me->GetPositionX(),
                me->GetPositionY(), me->GetPositionZ(), RopeStateName(RopeStateOf(me))));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    // Loot and the loot mode are fixed by the kill (Unit::Kill fills the corpse's loot before this runs): the rope is
    // added to the filled loot, once per instance (RopeDropAllowed), and the lootable flag is kept when it is the only
    // thing on the corpse.
    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        bool const roped = DropRope();
        FranclornSpeaks();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("pillars={} rope={} roped={} killer={}", _pillarsFallen, RopeStateName(RopeStateOf(me)),
                roped ? 1 : 0, killer ? killer->GetName() : "none"));
        Cleanup();
    }

    // The spirit's copy is a prop: it never zones into the fight.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        BossAI::OnSpellCast(spell);
        if (spell->Id == SPELL_FD_HOLY_LIGHT)
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "holy-light-cast",
                Acore::StringFormat("health={:.0f}%", me->GetHealthPct()));
    }

    // FD2: an interrupted Holy Light is lost (no repeat), the reward of a kick.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (spell->Id == SPELL_FD_HOLY_LIGHT)
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "holy-light-interrupted",
                Acore::StringFormat("health={:.0f}%", me->GetHealthPct()));
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        if (!UpdateVictim())
            return;

        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        UpdateBeats();

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The beats
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateBeats()
    {
        bool const heroic = IsHeroicMap(me);
        if (_shoddyClock.Due(_clockMs))
        {
            if (ShoddyConstruction())
                _shoddyClock.Fired(_clockMs, kShoddyEveryMs(heroic));
            else
                _shoddyClock.Start(_clockMs, kShoddyRetryMs);
        }

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;     // the casts below wait for a free bar (Holy Light first: it is the one that matters)

        int const light = NextHolyLight(me->GetHealthPct(), _holyLightsDone);
        if (light >= 0 && me->CastSpell(me, SPELL_FD_HOLY_LIGHT, false) == SPELL_CAST_OK)
        {
            // The threshold counts once the cast starts (stock: no repeat); an interrupt loses it.
            _holyLightsDone |= 1u << light;
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "holy-light",
                Acore::StringFormat("at={}% health={:.0f}% heal={:.0f}%", uint32(kHolyLightAtPct[light]),
                    me->GetHealthPct(), kHolyLightHealPct));
            return;
        }
        if (SealDue(me->GetHealthPct(), _sealDone))
        {
            _sealDone = true;
            DoCastSelf(SPELL_FD_SEAL_OF_RECKONING);
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "seal-of-reckoning",
                Acore::StringFormat("health={:.0f}%", me->GetHealthPct()));
        }
        if (_strikeClock.Due(_clockMs))
        {
            _strikeClock.Start(_clockMs, urand(kHolyStrikeMinMs, kHolyStrikeMaxMs));
            HolyStrike();
        }
        if (_kickClock.Due(_clockMs))
        {
            _kickClock.Start(_clockMs, kKickEveryMs);
            Kick(nullptr);
        }
    }

    // The stock Holy Strike on his victim (SmartAI row 3).
    void HolyStrike()
    {
        Unit* victim = me->GetVictim();
        if (!victim || !me->IsWithinMeleeRange(victim))
            return;
        DoCastVictim(SPELL_FD_HOLY_STRIKE);
    }

    // The stock Kick (SmartAI row 4, the area-casting event): a player casting within 5 yd, taken from the threat
    // list in order. `forced` is a `.dbtest` target.
    bool Kick(Player* forced)
    {
        Player* target = forced;
        if (!target)
            for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
            {
                Player* player = ref->GetVictim() ? ref->GetVictim()->ToPlayer() : nullptr;
                if (player && player->IsAlive() &&
                    KickTarget(player->IsNonMeleeSpellCast(false, false, true), me->GetDistance(player)))
                {
                    target = player;
                    break;
                }
            }
        if (!target)
            return false;
        bool const cast = me->CastSpell(target, SPELL_FD_KICK, false) == SPELL_CAST_OK;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "kick",
            Acore::StringFormat("target={} cast={}", target->GetName(), cast ? 1 : 0));
        return cast;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // FD1 Shoddy Construction
    // ----------------------------------------------------------------------------------------------------------------

    // A random player, the tank included (ruling 88), except one standing on a narrow corner (no pillar circle there).
    Player* PickShoddyTarget() const
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        std::vector<Player*> players = DungeonKit::PickPlayers(me, rule, kPickAll);
        std::erase_if(players, [](Player* p) { return OnCorner(DungeonKit::PlaneOf(p)); });
        if (players.empty())
            return nullptr;
        return players[urand(0, uint32(players.size()) - 1)];
    }

    // The floor under a player: a player in the air gets the floor within kShoddyGroundSearchYd below him, else his
    // own height.
    float GroundZ(Player const* player) const
    {
        float const x = player->GetPositionX();
        float const y = player->GetPositionY();
        float const z = player->GetPositionZ();
        float const floor = me->GetMap()->GetHeight(player->GetPhaseMask(), x, y, z + 2.f, true,
            kShoddyGroundSearchYd + 2.f);
        return (floor > INVALID_HEIGHT && std::fabs(floor - z) <= kShoddyGroundSearchYd) ? floor : z;
    }

    // One pillar at `forced`'s spot (a `.dbtest` pillar), else at a picked player's. False: nobody to fall on.
    bool ShoddyConstruction(Player* forced = nullptr)
    {
        bool const heroic = IsHeroicMap(me);
        Player* target = forced ? forced : PickShoddyTarget();
        if (!target)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "shoddy-construction", "no target (corners or nobody)");
            return false;
        }
        float const x = target->GetPositionX();
        float const y = target->GetPositionY();
        float const z = GroundZ(target);
        Position const spot(x, y, z, 0.f);

        // The pillar goes in (the object and the earth spike) and falls with the circle.
        Pillar pillar;
        pillar.spot = spot;
        if (GameObject* go = me->SummonGameObject(GO_BRD_SHODDY_PILLAR, x, y, z, frand(0.f, DungeonKit::kTwoPi), 0.f,
                0.f, 0.f, 0.f, kShoddyObjectBackstopMs / 1000 + 1))
            pillar.go = go->GetGUID();
        me->CastSpell(x, y, z, SPELL_FD_PILLAR_RISE, true);

        MechanicRef ref = Mechanic::Circle(me, spot, kShoddyRadiusYd, Ms(kShoddyWarnMs));
        ref.Damage(kShoddyPct(heroic)).TankDamage(kShoddyPct(heroic)).Spell(SPELL_FD_SHODDY_COLLAPSE).Weakened()
            .Tag(TAG_SHODDY_CONSTRUCTION);      // the tank on its own row (ruling 88, R-1-A n7)
        ObjectGuid const goGuid = pillar.go;
        ref.OnResolve(OnFineous([spot, goGuid](npc_fineous_darkvire_rework& ai, BossMechanics::ResolveResult const& r)
        {
            ai.Collapsed(spot, goGuid, r.hits.size());
        }));
        pillar.id = ref.Handle().id;
        if (!pillar.id)
        {
            DeleteObject(pillar.go);
            return false;
        }
        _pillars.push_back(pillar);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "shoddy-construction",
            Acore::StringFormat("on={} at=({:.1f}, {:.1f}, {:.1f}) r={:.0f} warn={}s pct={:.0f} heroic={}",
                target->GetName(), x, y, z, kShoddyRadiusYd, kShoddyWarnMs / 1000, kShoddyPct(heroic),
                heroic ? 1 : 0));
        return true;
    }

    // The collapse: the registry dealt the damage; the pillar is gone and the dust rises.
    void Collapsed(Position const& spot, ObjectGuid go, std::size_t hits)
    {
        DeleteObject(go);
        me->CastSpell(spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(), SPELL_FD_COLLAPSE_DUST, true);
        std::erase_if(_pillars, [go](Pillar const& p) { return p.go == go; });
        ++_pillarsFallen;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "shoddy-collapse",
            Acore::StringFormat("at=({:.1f}, {:.1f}) hits={}", spot.GetPositionX(), spot.GetPositionY(), hits));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The death: the rope, Franclorn's line
    // ----------------------------------------------------------------------------------------------------------------

    // The Guzzler rope (ruling 67): one per instance, a 100% white item in his loot, free for all (HANDOFF section 10:
    // anyone in the group may loot it, not only the round-robin looter, often a bot). Added after the loot was filled;
    // DATA_GUZZLER_ROPE is saved by the instance. Only for a corpse the group tapped (a loot owner).
    bool DropRope()
    {
        InstanceScript* instance = me->GetInstanceScript();
        if (!instance || !RopeDropAllowed(instance->GetData(DATA_GUZZLER_ROPE)))
            return false;
        Player* owner = me->GetLootRecipient();
        if (!owner)
            return false;
        ItemTemplate const* proto = sObjectMgr->GetItemTemplate(kItemGuzzlerRope);
        if (!proto)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "rope-drop", "item 70622 missing");
            return false;
        }
        Loot& loot = me->loot;
        if (!loot.lootOwnerGUID)
            loot.lootOwnerGUID = owner->GetGUID();
        size_t const before = loot.items.size();
        uint8 const countedBefore = loot.unlootedCount;
        loot.AddItem(LootStoreItem(kItemGuzzlerRope, 0, 100.f, false, LOOT_MODE_DEFAULT, 0, 1, 1));
        if (loot.items.size() == before)
            return false;
        MakeFreeForAll(loot, uint8(loot.items.size() - 1), countedBefore, owner);
        // The corpse is lootable even when the rope is all it holds (the flag was set before this ran).
        if (me->GetLootMode() && !me->HasDynamicFlag(UNIT_DYNFLAG_LOOTABLE))
            me->SetDynamicFlag(UNIT_DYNFLAG_LOOTABLE);
        instance->SetData(DATA_GUZZLER_ROPE, ROPE_DROPPED);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "rope-drop",
            Acore::StringFormat("owner={} items={} rope={}", owner->GetName(), loot.items.size(),
                RopeStateName(instance->GetData(DATA_GUZZLER_ROPE))));
        return true;
    }

    // The rope as a free-for-all item, the way Loot::FillLoot treats an ITEM_FLAG_MULTI_DROP one: every member gets
    // his own copy to loot (Loot::FillFFALoot's per-player list), and the corpse stays lootable until each has taken
    // it. AddItem counted it once as a one-player item; that count is taken back (the per-player lists count it).
    void MakeFreeForAll(Loot& loot, uint8 index, uint8 countedBefore, Player* owner)
    {
        loot.items[index].freeforall = true;
        loot.items[index].is_underthreshold = false;
        if (loot.unlootedCount > countedBefore)
            --loot.unlootedCount;
        std::vector<Player*> members;
        if (Group* group = owner->GetGroup())
        {
            for (GroupReference* ref = group->GetFirstMember(); ref; ref = ref->next())
                if (Player* member = ref->GetSource())
                    if (member->IsInMap(me))
                        members.push_back(member);
        }
        else
            members.push_back(owner);
        for (Player* member : members)
        {
            auto const listed = loot.GetPlayerFFAItems().find(member->GetGUID());
            if (listed != loot.GetPlayerFFAItems().end() && listed->second)
            {
                listed->second->push_back(QuestItem(index));
                ++loot.unlootedCount;
            }
            else
                loot.FillNotNormalLootFor(member);      // FillFFALoot lists (and counts) the rope for him
        }
    }

    // S2 749: Franclorn's Spirit (9542) is only ever summoned at Loregrain's shrine, so a short-lived copy of it stands
    // by the corpse and speaks its group 1.
    void FranclornSpeaks()
    {
        float const o = me->GetOrientation();
        float const x = me->GetPositionX() + std::cos(o) * kFranclornOffsetYd;
        float const y = me->GetPositionY() + std::sin(o) * kFranclornOffsetYd;
        TempSummon* spirit = me->SummonCreature(NPC_FRANCLORNS_SPIRIT, x, y, me->GetPositionZ(), o + DungeonKit::kPi,
            TEMPSUMMON_TIMED_DESPAWN, kFranclornLifeMs);
        if (!spirit)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "franclorn", "summon failed");
            return;
        }
        if (spirit->IsAIEnabled && spirit->AI())
            spirit->AI()->Talk(TEXT_FRANCLORN_IRONFEL);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "franclorn", "spoke");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Bots and the `.dbtest` entry points
    // ----------------------------------------------------------------------------------------------------------------

    // Holy Light is the cast worth a kick (the reward of FD2); the pillar circles are the registry's.
    void Describe()
    {
        BossMechanics::Descriptor d;
        d.interrupts.emplace_back(NPC_FINEOUS, SPELL_FD_HOLY_LIGHT, 1);
        Mechanic::Describe(me, std::move(d));
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    // An empty string when fired; otherwise why not.
    std::string TestPillar(Player* gm)
    {
        if (!me->IsEngaged())
            return "Fineous must be in combat (the collapses run only in the fight).";
        if (!gm)
            return "No player to put a pillar under.";
        if (!ShoddyConstruction(gm))
            return "The pillar was refused.";
        return {};
    }

    std::string TestHolyLight()
    {
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return "He is already casting.";
        if (me->CastSpell(me, SPELL_FD_HOLY_LIGHT, false) != SPELL_CAST_OK)
            return "Holy Light did not cast.";
        return {};
    }

    std::string TestKick(Player* gm)
    {
        if (!me->IsEngaged())
            return "Fineous must be in combat.";
        if (!gm || !Kick(gm))
            return "The kick did not land.";
        return {};
    }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s pillars={} fallen={} holy-lights=0x{:x} seal={} strike={} kick={} "
            "shoddy={} rope={}", _clockMs / 1000, _pillars.size(), _pillarsFallen, _holyLightsDone, _sealDone ? 1 : 0,
            _strikeClock.On() ? "on" : "off", _kickClock.On() ? "on" : "off", _shoddyClock.On() ? "on" : "off",
            RopeStateName(RopeStateOf(me)));
    }

private:
    struct Pillar
    {
        uint32 id = 0;          // the registry circle
        ObjectGuid go;          // the object (may be empty: the summon failed)
        Position spot;
    };

    // Everyone on the threat list (the pick's count: a raid never reaches it).
    static uint32 constexpr kPickAll = 40;

    // Runs `fn(ai, result)` on this boss when a mechanic resolves, if he is still there. Captures the map and the guid
    // only (a lambda the registry keeps must not hold a Unit*). A cancelled result runs it too.
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnFineous(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (!map)
                return;
            Creature* boss = map->GetCreature(guid);
            if (!boss || !boss->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<npc_fineous_darkvire_rework*>(boss->AI()))
                fn(*ai, result);
        };
    }

    void DeleteObject(ObjectGuid guid)
    {
        if (!guid)
            return;
        if (GameObject* go = me->GetMap()->GetGameObject(guid))
            go->Delete();
    }

    // The pull's state: no pillar standing, no circle pending, no aura of the fight, the clocks stopped (Reset, evade,
    // death, a new pull).
    void Cleanup()
    {
        for (Pillar const& pillar : _pillars)
        {
            Mechanic::Cancel(me, MechanicHandle{ pillar.id });
            DeleteObject(pillar.go);
        }
        _pillars.clear();
        me->RemoveAurasDueToSpell(SPELL_FD_DEVOTION_AURA);
        me->RemoveAurasDueToSpell(SPELL_FD_SEAL_OF_RECKONING);
        _holyLightsDone = 0;
        _sealDone = false;
        _pillarsFallen = 0;
        _clockMs = 0;
        _strikeClock.Stop();
        _kickClock.Stop();
        _shoddyClock.Stop();
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    FightClock _strikeClock;
    FightClock _kickClock;
    FightClock _shoddyClock;
    std::vector<Pillar> _pillars;
    uint64 _clockMs = 0;            // ms since the reset: every timer of the fight
    uint32 _holyLightsDone = 0;     // bit i = the 60% / 40% Holy Light started
    uint32 _pillarsFallen = 0;
    bool _sealDone = false;
};

// -------------------------------------------------------------------------------------------------------------------
// The hanging rope (301282, a static spawn at the climb spot behind Lord Incendius): hidden and not clickable until the
// instance's rope is placed (a saved state, so it is there after every reload); a click moves the player to the floor
// past the Bar Door. The pickup is an item, not an object (the Rope Pile display was for a ground pickup).
// -------------------------------------------------------------------------------------------------------------------

struct go_brd_hanging_rope : public GameObjectAI
{
    explicit go_brd_hanging_rope(GameObject* go) : GameObjectAI(go) { }

    void InitializeAI() override
    {
        SyncFlag();
    }

    bool CanBeSeen(Player const* /*seer*/) override
    {
        return Shown();
    }

    bool GossipHello(Player* player, bool reportUse) override
    {
        // Handled either way (true): the click never reaches GameObject::Use's goober branch (no cooldown, no state).
        if (reportUse || !player)
            return true;
        Climb(player);
        return true;
    }

    void UpdateAI(uint32 diff) override
    {
        if (_pollMs > diff)
        {
            _pollMs -= diff;
            return;
        }
        _pollMs = kPollMs;
        if (!_synced || Shown() != _lastShown)
            Refresh();
    }

    // The state changed (the use spell placed it, a `.dbtest` set it): show or hide now.
    void Refresh()
    {
        bool const shown = Shown();
        SyncFlag();
        _synced = true;
        if (me->IsInWorld())
            me->UpdateObjectVisibility(true);
        if (shown != _lastShown)
        {
            _lastShown = shown;
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, shown ? "rope-shown" : "rope-hidden",
                Acore::StringFormat("rope={}", RopeStateName(RopeStateOf(me))));
        }
    }

private:
    static uint32 constexpr kPollMs = 1000;

    bool Shown() const
    {
        return RopeObjectShown(RopeStateOf(me));
    }

    void SyncFlag()
    {
        bool const shown = Shown();
        bool const flagged = me->HasGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        if (shown && flagged)
            me->RemoveGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        else if (!shown && !flagged)
            me->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
    }

    // The climb: a near teleport to kRopeLanding on the same map (the pets follow on their own: a near teleport keeps
    // a pet within the visibility range).
    void Climb(Player* player)
    {
        if (!RopeClickAllowed(RopeStateOf(me), me->GetDistance(player)))
            return;
        if (player->HasUnitState(UNIT_STATE_CASTING) || !player->IsAlive())
            return;
        player->TeleportTo(player->GetMapId(), kRopeLanding.x, kRopeLanding.y, kRopeLanding.z, kRopeLanding.o);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "rope-climb",
            Acore::StringFormat("player={} to=({:.1f}, {:.1f}, {:.1f})", player->GetName(), kRopeLanding.x,
                kRopeLanding.y, kRopeLanding.z));
    }

    uint32 _pollMs = 0;
    bool _synced = false;
    bool _lastShown = false;
};

// -------------------------------------------------------------------------------------------------------------------
// 211261 the Guzzler Rope's use (item 70622; a DUMMY on the user, consumed by a successful cast): only on the ledge
// behind Lord Incendius, once per instance. The hanging rope stays for the rest of the instance (DATA_GUZZLER_ROPE
// PLACED, saved).
// -------------------------------------------------------------------------------------------------------------------

namespace
{
    // The rope's refusal for `user` right now.
    RopeRefusal RopeRefusalFor(Player* user)
    {
        InstanceScript* instance = user ? user->GetInstanceScript() : nullptr;
        float const dx = user ? user->GetPositionX() - kRopeClimbSpot.x : 0.f;
        float const dy = user ? user->GetPositionY() - kRopeClimbSpot.y : 0.f;
        float const dz = user ? user->GetPositionZ() - kRopeClimbSpot.z : 0.f;
        return RopeUseRefusal(user ? user->GetMapId() : 0, instance != nullptr,
            instance ? instance->GetData(DATA_GUZZLER_ROPE) : uint32(ROPE_NONE), std::sqrt(dx * dx + dy * dy), dz);
    }
}

class spell_brd_guzzler_rope : public SpellScript
{
    PrepareSpellScript(spell_brd_guzzler_rope);

    SpellCastResult CheckCast()
    {
        Player* user = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!user)
            return SPELL_FAILED_BAD_TARGETS;
        RopeRefusal const why = RopeRefusalFor(user);
        if (why == RopeRefusal::None)
            return SPELL_CAST_OK;
        ChatHandler(user->GetSession()).SendNotification(std::string_view(RopeRefusalText(why)));
        return SPELL_FAILED_DONT_REPORT;
    }

    void Hang(SpellEffIndex /*effIndex*/)
    {
        Player* user = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!user || RopeRefusalFor(user) != RopeRefusal::None)
            return;
        InstanceScript* instance = user->GetInstanceScript();
        instance->SetData(DATA_GUZZLER_ROPE, ROPE_PLACED);
        if (instance->GetData(DATA_GUZZLER_ROPE) != ROPE_PLACED)
            return;
        if (GameObject* rope = user->FindNearestGameObject(GO_BRD_HANGING_ROPE, 60.f))
            if (auto* ai = dynamic_cast<go_brd_hanging_rope*>(rope->AI()))
                ai->Refresh();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "rope-hung",
            Acore::StringFormat("by={} at=({:.1f}, {:.1f}, {:.1f}) rope={}", user->GetName(), user->GetPositionX(),
                user->GetPositionY(), user->GetPositionZ(), RopeStateName(instance->GetData(DATA_GUZZLER_ROPE))));
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_brd_guzzler_rope::CheckCast);
        OnEffectHit += SpellEffectFn(spell_brd_guzzler_rope::Hang, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// -------------------------------------------------------------------------------------------------------------------
// `.dbtest brd fineous`
// -------------------------------------------------------------------------------------------------------------------

namespace
{
    npc_fineous_darkvire_rework* FindFineousAI(ChatHandler* handler)
    {
        Creature* boss = BrdTest::FindBoss(handler, NPC_FINEOUS);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<npc_fineous_darkvire_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Fineous is not running npc_fineous_darkvire_rework (check the "
                "ScriptName).");
        return ai;
    }

    Player* GmPlayer(ChatHandler* handler)
    {
        return handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowBossInfo(handler, NPC_FINEOUS, BOSS_FINEOUS);
    }

    bool HandleState(ChatHandler* handler)
    {
        npc_fineous_darkvire_rework* ai = FindFineousAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Fineous: {}", ai->TestState());
        return true;
    }

    // `.dbtest brd fineous pillar`: a pillar under you (FD1; `.gm off` to take the hit).
    bool HandlePillar(ChatHandler* handler)
    {
        npc_fineous_darkvire_rework* ai = FindFineousAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestPillar(GmPlayer(handler));
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Fineous: Shoddy Construction fired under you ({}).",
            ai->HeroicMap() ? "heroic numbers" : "normal numbers");
        return true;
    }

    // `.dbtest brd fineous holylight`: his Holy Light now (FD2: kick it).
    bool HandleHolyLight(ChatHandler* handler)
    {
        npc_fineous_darkvire_rework* ai = FindFineousAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestHolyLight();
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("{}", "Fineous: Holy Light started (a 2.5 s cast, 4% of his health).");
        return true;
    }

    // `.dbtest brd fineous kick`: his stock Kick on you.
    bool HandleKick(ChatHandler* handler)
    {
        npc_fineous_darkvire_rework* ai = FindFineousAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestKick(GmPlayer(handler));
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("{}", "Fineous: Kick landed on you.");
        return true;
    }

    // `.dbtest brd fineous rope`: the rope's state, and what the use spell would say to you here.
    bool HandleRope(ChatHandler* handler)
    {
        if (!BrdTest::RequireBlackrockDepths(handler))
            return false;
        Player* gm = GmPlayer(handler);
        if (!gm)
            return false;
        RopeRefusal const why = RopeRefusalFor(gm);
        handler->PSendSysMessage("Guzzler rope: {}; the use spell here: {}; the climb spot is {:.1f} yd away; "
            "`.dbtest brd instance rope <1|2>` sets the state.", RopeStateName(RopeStateOf(gm)),
            why == RopeRefusal::None ? "allowed" : RopeRefusalText(why),
            std::sqrt(std::pow(gm->GetPositionX() - kRopeClimbSpot.x, 2) +
                std::pow(gm->GetPositionY() - kRopeClimbSpot.y, 2)));
        return true;
    }

    // `.dbtest brd fineous climb`: the click's teleport, without a rope (the landing past the Bar Door).
    bool HandleClimb(ChatHandler* handler)
    {
        if (!BrdTest::RequireBlackrockDepths(handler))
            return false;
        Player* gm = GmPlayer(handler);
        if (!gm)
            return false;
        gm->TeleportTo(gm->GetMapId(), kRopeLanding.x, kRopeLanding.y, kRopeLanding.z, kRopeLanding.o);
        handler->PSendSysMessage("Climbed to ({:.1f}, {:.1f}, {:.1f}).", kRopeLanding.x, kRopeLanding.y,
            kRopeLanding.z);
        return true;
    }

    ChatCommandTable const& NpcFineousDarkvireTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",      HandleInfo,      SEC_GAMEMASTER, Console::No },
            { "state",     HandleState,     SEC_GAMEMASTER, Console::No },
            { "pillar",    HandlePillar,    SEC_GAMEMASTER, Console::No },
            { "holylight", HandleHolyLight, SEC_GAMEMASTER, Console::No },
            { "kick",      HandleKick,      SEC_GAMEMASTER, Console::No },
            { "rope",      HandleRope,      SEC_GAMEMASTER, Console::No },
            { "climb",     HandleClimb,     SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_npc_fineous_darkvire_rework()
{
    RegisterDungeonReworkCreatureAI(npc_fineous_darkvire_rework, BlackrockDepthsRework::kInstanceScriptName);
    RegisterDungeonReworkGameObjectAI(go_brd_hanging_rope, BlackrockDepthsRework::kInstanceScriptName);
    RegisterSpellScript(spell_brd_guzzler_rope);
    BrdTest::RegisterBoss("fineous", NpcFineousDarkvireTestCommands());
}
