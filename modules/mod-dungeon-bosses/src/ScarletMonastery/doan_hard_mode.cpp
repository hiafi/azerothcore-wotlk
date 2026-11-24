/*
 * mod-dungeon-bosses, Scarlet Monastery D8H: Arcanist Doan's hard mode, the Kel'Thuzad Heresy (heroic only).
 * Build spec: docs/dungeons/scarlet-monastery-2-library.md "Hard mode: The Kel'Thuzad Heresy" (HM1-HM5, the Build
 * spec rows), handoff section 3.7, 3.8 row "D8H pages", 7 #27 A. Pure rules: DoanHardModeLogic.h. It fights on D8's
 * AI (boss_arcanist_doan_rework) through DoanFight.h and never edits it.
 *
 *   The trigger      four evidence pages (goobers 301320-301323, heroic spawns only) read in any order, each once per
 *                    instance: the reader sees the page's text and the emote "You have found evidence of heresy (n of
 *                    4)."; the fourth lights DATA_HARD_MODE_DOAN (the instance's flag, saved; it also sets the loot
 *                    bit), Doan yells line 2 across the Library and takes the hard mode's red aura (it holds a wipe:
 *                    AURA_STAYS_AFTER_COMBAT). He stays where he is; the group pulls him when ready
 *   The pull         400k (back to his heroic health on a wipe); every DoanFight tuning query: the bubble every 35 s,
 *                    Marks every 30 s (3 players, D8's heroic count), the pools for the rest of the fight, Detonation
 *                    200%
 *   HM1 Icy Death    a Curse (8 s, refreshed, 60% slower, Frost a second) riding Arcane Explosion, the Mark's burst
 *                    and own share, the pools, a landed Flamestrike and Shadow Fissure. On the bots' dispel list
 *   HM3 the shard    every bubble raises the Phylactery Shard (300920) on the next free anchor spot as one more
 *                    anchor (DoanFight::AddBubbleAnchor): warded (immune) while another anchor stands, 2.5 x a hard
 *                    mode anchor's health; the anchors themselves 1.25 x their heroic health
 *   HM4 fissures     from the end of his first bubble, every 10 s (held while Overloaded): 6 yd under 2 random
 *                    players, a 3 s marker, 60% Shadow
 *   HM5 the Purged   at the end of his second bubble, once: six Risen Purged (300921) rise along the south wall
 *                    (line 3) and walk to him; each that reaches him is one more anchor next bubble
 *
 * Every unit comes from DoanFight::Summon (D8's cleanup despawns it), every registry handle goes to DoanFight::Track;
 * OnEnd puts his health back and clears Icy Death. Every firing logs one INFO line "sm doan heresy-<mechanic> ..."
 * (module.dungeonbosses); `.dbtest sm heresy ...` fires one on demand.
 */

#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DoanFight.h"
#include "DoanHardModeLogic.h"
#include "DoanLogic.h"
#include "DungeonKit.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScarletMonasteryRework.h"
#include "ScarletMonasteryTestCommand.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "SpellMgr.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "WorldPacket.h"
#include "WorldSession.h"
#include <algorithm>
#include <cmath>
#include <memory>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScarletMonasteryRework;
using namespace SmHeresy;
using BossMechanics::MechanicRef;
using SmDoan::DoanFight;
using SmDoan::DoanHit;

// RiddenHit mirrors DoanFight.h's DoanHit (the pure header cannot include the engine side).
static_assert(static_cast<uint8>(DoanHit::Explosion) == static_cast<uint8>(RiddenHit::Explosion)
    && static_cast<uint8>(DoanHit::MarkBurst) == static_cast<uint8>(RiddenHit::MarkBurst)
    && static_cast<uint8>(DoanHit::MarkSelf) == static_cast<uint8>(RiddenHit::MarkSelf)
    && static_cast<uint8>(DoanHit::Pool) == static_cast<uint8>(RiddenHit::Pool)
    && static_cast<uint8>(DoanHit::Flamestrike) == static_cast<uint8>(RiddenHit::Flamestrike)
    && static_cast<uint8>(DoanHit::Scorched) == static_cast<uint8>(RiddenHit::Scorched)
    && static_cast<uint8>(DoanHit::Detonation) == static_cast<uint8>(RiddenHit::Detonation),
    "RiddenHit must follow DoanHit");

namespace
{
    char const* const kBossLogName = "doan";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // Create health is the base the engine rebuilds max health from (the Baron's and Ras's hard mode pattern).
    void SetCreatureHealth(Creature* creature, uint32 health)
    {
        creature->SetCreateHealth(health);
        creature->SetStatFlatModifier(UNIT_MOD_HEALTH, BASE_VALUE, static_cast<float>(health));
        creature->UpdateMaxHealth();
        creature->SetHealth(creature->GetMaxHealth());
    }

    // The floor under a point; falls back to the given height.
    float FloorZ(WorldObject const* ref, float x, float y, float z)
    {
        float const floor = ref->GetMapHeight(x, y, z + 2.f);
        return (floor <= INVALID_HEIGHT + 1.f || std::fabs(floor - z) > 4.f) ? z : floor;
    }

    // The chamber floor (DoanLogic.h kChamberOutline): every spot the bots plan for a fissure stays on it (rule 12).
    BossMechanics::SpotBounds ChamberBounds()
    {
        std::vector<Position> room;
        room.reserve(SmDoan::kChamberOutline.size());
        for (DungeonKit::Vec2 const& p : SmDoan::kChamberOutline)
            room.emplace_back(p.x, p.y, SmDoan::kChamberCenter.z);
        return BossMechanics::SpotBounds().Polygon(room, SmDoan::kChamberZMin, SmDoan::kChamberZMax);
    }

    // The Doan of the reader's instance (ObjectData), alive or not; nullptr when he is not loaded.
    Creature* DoanOf(InstanceScript* instance, Map* map)
    {
        if (!instance || !map)
            return nullptr;
        ObjectGuid const guid = instance->GetGuidData(DATA_ARCANIST_DOAN);
        return guid ? map->GetCreature(guid) : nullptr;
    }

    // The hard mode's red aura on him (a wipe keeps it; a cold load or a respawn needs it again: OnEngage and the
    // fourth page put it on, IdleHeresyAura keeps it on out of combat).
    void ApplyHeresyAura(Creature* doan)
    {
        if (doan && doan->IsAlive() && !doan->HasAura(SPELL_HERESY_AURA))
            doan->CastSpell(doan, SPELL_HERESY_AURA, true);
    }

    // D8's idle hook (DoanFight.h RegisterDoanIdleHook), every tick out of combat: the red aura while the instance's
    // flag is lit on a heroic map (a cold load with the flag saved, a respawn), none otherwise.
    void IdleHeresyAura(Creature* doan)
    {
        if (!doan || !sSpellMgr->GetSpellInfo(SPELL_HERESY_AURA))
            return;
        InstanceScript* instance = doan->GetInstanceScript();
        bool const lit = instance && DungeonKit::IsHeroicMap(doan) && instance->GetData(DATA_HARD_MODE_DOAN) != 0;
        bool const has = doan->HasAura(SPELL_HERESY_AURA);
        if (lit && !has)
            ApplyHeresyAura(doan);
        else if (!lit && has)
            doan->RemoveAurasDueToSpell(SPELL_HERESY_AURA);
    }

    // A page read by `reader` (the page gameobject's click, or the GM test with `source` the reader). Returns why it
    // did not count. The page's own text shows either way (the goober's page_text).
    PageRefusal ReadPage(Player* reader, uint32 page, WorldObject* source)
    {
        InstanceScript* instance = reader ? reader->GetInstanceScript() : nullptr;
        if (!instance || reader->GetMapId() != kMapScarletMonastery)
            return PageRefusal::NotAPage;
        uint32 const before = instance->GetData(DATA_DOAN_PAGES_MASK);
        bool const litBefore = instance->GetData(DATA_HARD_MODE_DOAN) != 0;
        PageRefusal const why = PageRefusalFor(reader->GetMap()->IsHeroic(),
            static_cast<uint32>(instance->GetBossState(BOSS_DOAN)), before, page);
        if (why != PageRefusal::None)
        {
            if (char const* notice = PageRefusalNotice(why))
                ChatHandler(reader->GetSession()).SendNotification(std::string_view(notice));
            return why;
        }

        instance->SetData(DATA_DOAN_PAGE_READ, page);
        uint32 const after = instance->GetData(DATA_DOAN_PAGES_MASK);
        if (after == before)
            return PageRefusal::AlreadyRead;       // the instance refused it (its own DoanPageAllowed)
        uint32 const read = instance->GetData(DATA_DOAN_PAGE_READ);
        WorldPacket data;
        ChatHandler::BuildChatPacket(data, CHAT_MSG_RAID_BOSS_EMOTE, LANG_UNIVERSAL, source ? source : reader, reader,
            PageEmote(read));
        reader->SendDirectMessage(&data);
        bool const lit = instance->GetData(DATA_HARD_MODE_DOAN) != 0;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "heresy-page",
            Acore::StringFormat("page={} ({}) by={} read={} of {} lit={}", page + 1, kPages[page].what,
                reader->GetName(), read, kPageCount, lit ? 1 : 0));
        if (lit && !litBefore)
        {
            Creature* doan = DoanOf(instance, reader->GetMap());
            if (doan && doan->IsAlive() && doan->IsAIEnabled)
                doan->AI()->Talk(SmDoan::SAY_HERESY);
            ApplyHeresyAura(doan);
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "heresy-lit",
                Acore::StringFormat("by={} doan={}", reader->GetName(), doan ? 1 : 0));
        }
        return PageRefusal::None;
    }
}

// -------------------------------------------------------------------------------------------------------------------
// The hard mode for one pull (DoanFight.h DoanHardMode)
// -------------------------------------------------------------------------------------------------------------------

class HeresyFight : public SmDoan::DoanHardMode
{
public:
    void OnEngage(DoanFight& fight) override
    {
        Creature* doan = fight.Doan();
        _baseCreateHealth = doan->GetCreateHealth();
        SetCreatureHealth(doan, kDoanHealth);
        ApplyHeresyAura(doan);
        fight.Log("heresy-engage", Acore::StringFormat("health={} base-create={} bubble={}ms marks={}ms pools=forever "
            "detonation={:.0f}%", doan->GetMaxHealth(), _baseCreateHealth, kBubbleEveryMs, kMarkEveryMs,
            kDetonationPct));
    }

    void OnUpdate(DoanFight& fight, uint32 /*diff*/) override
    {
        UpdateShard(fight);
        UpdateRisen(fight);
        if (_fissureClock.Due(fight.ClockMs()) && !FissureHeld(fight.Overloaded()))
        {
            _fissureClock.Fired(fight.ClockMs(), kFissureEveryMs);
            OpenFissures(fight);
        }
    }

    // HM3: the shard as one more anchor of this bubble, on the next free anchor spot, warded while another stands.
    void OnBubbleStart(DoanFight& fight, uint32 index) override
    {
        RaiseShard(fight, index);
    }

    // The hard mode's anchors: 1.25 x the heroic anchor (6.25k on H's 5k template, HANDOFF s10 option D).
    void OnAnchorRaised(DoanFight& /*fight*/, Creature* anchor) override
    {
        if (!anchor)
            return;
        uint32 const health = HardModeAnchorHealth(anchor->GetMaxHealth());
        SetCreatureHealth(anchor, health);
        _anchorHealth = health;
    }

    void OnBubbleEnd(DoanFight& fight, uint32 index, bool broken) override
    {
        Creature* doan = fight.Doan();
        bool shardAlive = false;
        if (Creature* shard = _shard ? ObjectAccessor::GetCreature(*doan, _shard) : nullptr)
        {
            shardAlive = shard->IsAlive();
            shard->DespawnOrUnsummon();
        }
        _shard.Clear();
        fight.Log("heresy-bubble-end", Acore::StringFormat("index={} broken={} shard-alive={}", index, broken ? 1 : 0,
            shardAlive ? 1 : 0));
        if (FissuresStart(index) && !_fissureClock.On())
        {
            _fissureClock.Start(fight.ClockMs(), kFissureEveryMs);
            fight.Log("heresy-fissures-start", Acore::StringFormat("first-in={}ms every={}ms", kFissureEveryMs,
                kFissureEveryMs));
        }
        if (RisenRise(index) && !_risenRaised)
            RaiseRisen(fight);
    }

    // Death, evade or reset: his health back (not on the death), Icy Death off every player. The units and handles
    // are D8's cleanup (DoanFight::Summon / Track).
    void OnEnd(DoanFight& fight, bool died) override
    {
        Creature* doan = fight.Doan();
        if (!died && doan->IsAlive() && _baseCreateHealth)
            SetCreatureHealth(doan, _baseCreateHealth);
        if (InstanceScript* instance = doan->GetInstanceScript())
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_HERESY_ICY_DEATH);
        fight.Log("heresy-end", Acore::StringFormat("died={} fissures={} risen-arrived={} risen-killed={} shards={}",
            died ? 1 : 0, _fissures, _risenArrived, _risenKilled, _shards));
        _fissureClock.Stop();
        _risen.clear();
        _shard.Clear();
    }

    // The bots: the shard after the anchors (ignored while warded), the Risen Purged ahead of Doan (AoE welcome; the
    // tank stays on him), Icy Death on the dispel list (a reward).
    void DescribeExtra(DoanFight& /*fight*/, BossMechanics::Descriptor& d) override
    {
        using BossMechanics::Condition;
        using BossMechanics::TargetEntry;
        using BossMechanics::Who;
        d.targets.emplace_back(NPC_SM_PHYLACTERY_SHARD, 1, Who::Any, Condition::LacksAura(SPELL_HERESY_SHARD_WARD));
        d.ignores.emplace_back(NPC_SM_PHYLACTERY_SHARD, Condition::HasAura(SPELL_HERESY_SHARD_WARD));
        d.targets.push_back(TargetEntry(NPC_SM_RISEN_PURGED, 1, Who::Dps).AoeOk());
        d.targets.push_back(TargetEntry(NPC_SM_RISEN_PURGED, -1, Who::Tank));
        d.dispels.emplace_back(SPELL_HERESY_ICY_DEATH, 1);
    }

    uint32 RiderFor(DoanFight const& /*fight*/, DoanHit hit) const override
    {
        return IcyDeathRides(static_cast<RiddenHit>(hit)) ? uint32(SPELL_HERESY_ICY_DEATH) : 0;
    }

    std::optional<uint32> BubbleEveryMs(DoanFight const& /*fight*/) const override { return kBubbleEveryMs; }
    std::optional<uint32> MarkEveryMs(DoanFight const& /*fight*/) const override { return kMarkEveryMs; }
    std::optional<uint32> PoolLifeMs(DoanFight const& /*fight*/) const override { return kPoolLifeMs; }
    std::optional<float> DetonationPct(DoanFight const& /*fight*/) const override { return kDetonationPct; }

    // `.dbtest sm heresy` entry points.
    bool TestFissures(DoanFight& fight)
    {
        return OpenFissures(fight) > 0;
    }

    std::string TestRisen(DoanFight& fight)
    {
        if (_risenRaised)
            return "The Risen Purged rose already this pull.";
        RaiseRisen(fight);
        return {};
    }

    std::string State(DoanFight& fight) const
    {
        Creature* doan = fight.Doan();
        uint32 risenAlive = 0;
        for (ObjectGuid const& guid : _risen)
            if (Creature* risen = ObjectAccessor::GetCreature(*doan, guid))
                if (risen->IsAlive())
                    ++risenAlive;
        Creature* shard = _shard ? ObjectAccessor::GetCreature(*doan, _shard) : nullptr;
        return Acore::StringFormat("health={}/{} anchor-health={} shard={} fissures={} (next in {}ms) risen={} "
            "(alive {}, arrived {}, killed {}) shards={}", doan->GetHealth(), doan->GetMaxHealth(), _anchorHealth,
            shard ? (shard->IsAlive() ? (shard->HasAura(SPELL_HERESY_SHARD_WARD) ? "warded" : "exposed") : "broken")
                : "none", _fissures,
            _fissureClock.On() && _fissureClock.DueMs() > fight.ClockMs() ? _fissureClock.DueMs() - fight.ClockMs()
                : 0, _risenRaised ? 1 : 0, risenAlive, _risenArrived, _risenKilled, _shards);
    }

private:
    void RaiseShard(DoanFight& fight, uint32 index)
    {
        Creature* doan = fight.Doan();
        // The first spot no living anchor stands on (n4: never on top of an anchor); all 12 taken: beside the last.
        uint32 taken = 0;
        for (ObjectGuid const& guid : fight.LiveAnchors())
            if (Creature const* anchor = ObjectAccessor::GetCreature(*doan, guid))
                for (uint32 i = 0; i < SmDoan::kAnchorSpotCount; ++i)
                {
                    Position const spot = fight.AnchorSpot(i);
                    if (anchor->GetExactDist2d(spot.GetPositionX(), spot.GetPositionY()) < kShardSpotTakenYd)
                        taken |= 1u << i;
                }
        uint32 const freeSpot = ShardSpotIndex(taken);
        bool const crowded = freeSpot >= SmDoan::kAnchorSpotCount;
        uint32 const spotIndex = crowded ? SmDoan::kAnchorSpotCount - 1 : freeSpot;
        Position at = fight.AnchorSpot(spotIndex);
        if (crowded)
        {
            float const toDoan = std::atan2(doan->GetPositionY() - at.GetPositionY(), doan->GetPositionX()
                - at.GetPositionX());
            at.Relocate(at.GetPositionX() + kShardCrowdedStepYd * std::cos(toDoan),
                at.GetPositionY() + kShardCrowdedStepYd * std::sin(toDoan), at.GetPositionZ());
        }
        at.m_positionZ = FloorZ(doan, at.GetPositionX(), at.GetPositionY(), at.GetPositionZ());
        at.SetOrientation(std::atan2(doan->GetPositionY() - at.GetPositionY(), doan->GetPositionX()
            - at.GetPositionX()));
        Creature* shard = fight.Summon(NPC_SM_PHYLACTERY_SHARD, at);
        if (!shard)
        {
            fight.Log("heresy-shard-refused", Acore::StringFormat("index={} spot={}", index, spotIndex));
            return;
        }
        uint32 const health = ShardHealth(_anchorHealth ? _anchorHealth : HardModeAnchorHealth(
            SmDoan::kAnchorHealthHeroic));
        SetCreatureHealth(shard, health);
        shard->CastSpell(shard, SPELL_HERESY_SHARD_WARD, true);
        if (doan->IsAIEnabled)
            doan->AI()->DoZoneInCombat(shard);
        shard->CastSpell(doan, SmDoan::SPELL_DN_ANCHOR_BEAM, true);
        bool const added = fight.AddBubbleAnchor(shard);
        _shard = shard->GetGUID();
        ++_shards;
        fight.Log("heresy-shard", Acore::StringFormat("index={} spot={}{} at=({:.1f}, {:.1f}) health={} added={}",
            index, spotIndex, crowded ? " (crowded)" : "", at.GetPositionX(), at.GetPositionY(), health,
            added ? 1 : 0));
    }

    // The ward comes off once no other anchor of the bubble stands.
    void UpdateShard(DoanFight& fight)
    {
        if (!_shard)
            return;
        Creature* shard = ObjectAccessor::GetCreature(*fight.Doan(), _shard);
        if (!shard || !shard->IsAlive() || !shard->HasAura(SPELL_HERESY_SHARD_WARD))
            return;
        for (ObjectGuid const& guid : fight.LiveAnchors())
            if (guid != _shard)
                return;
        shard->RemoveAurasDueToSpell(SPELL_HERESY_SHARD_WARD);
        fight.Log("heresy-shard-exposed", Acore::StringFormat("bubble={} health={}", fight.BubblesStarted(),
            shard->GetHealth()));
    }

    // HM4: a 6 yd circle under each of 2 random players (the tank may be one), 3 s, then 60% Shadow and Icy Death.
    uint32 OpenFissures(DoanFight& fight)
    {
        Creature* doan = fight.Doan();
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        rule.tankIfAlone = true;
        std::vector<Player*> const targets = DungeonKit::PickPlayers(doan, rule, kFissureCount);
        std::string who;
        uint32 opened = 0;
        for (Player* target : targets)
        {
            Position const at(target->GetPositionX(), target->GetPositionY(), target->GetPositionZ(), 0.f);
            MechanicRef ref = Mechanic::Circle(doan, at, kFissureRadiusYd, Ms(kFissureWarnMs));
            ref.Damage(kFissurePct).TankDamage(kFissurePct).School(SPELL_SCHOOL_SHADOW).Spell(SPELL_HERESY_FISSURE)
                .Rider(SPELL_HERESY_ICY_DEATH).Within(ChamberBounds()).Tag(TAG_HM_FISSURE);
            if (!ref.IsValid())
            {
                fight.Log("heresy-fissure-refused", target->GetName());
                continue;
            }
            fight.Track(ref.Handle());
            if (Creature* look = fight.Summon(NPC_SM_STALKER, at, kFissureWarnMs + kFissureLookTailMs))
                look->CastSpell(look, SPELL_HERESY_FISSURE_LOOK, true);
            ++opened;
            who += (who.empty() ? "" : ",") + target->GetName();
        }
        _fissures += opened ? 1 : 0;
        fight.Log(opened ? "heresy-fissure" : "heresy-fissure-skipped", Acore::StringFormat(
            "targets=[{}] r={:.0f} warn={}ms pct={:.0f} fissures={}", who, kFissureRadiusYd, kFissureWarnMs,
            kFissurePct, _fissures));
        return opened;
    }

    // HM5: six Risen Purged along the south wall, line 3; each walks to him (npc_sm_risen_purged).
    void RaiseRisen(DoanFight& fight);

    // A Risen Purged that reached him: one more anchor next bubble, and it is gone. A dead one is counted once.
    void UpdateRisen(DoanFight& fight)
    {
        if (_risen.empty())
            return;
        Creature* doan = fight.Doan();
        for (auto it = _risen.begin(); it != _risen.end();)
        {
            Creature* risen = ObjectAccessor::GetCreature(*doan, *it);
            if (!risen || !risen->IsAlive())
            {
                if (risen)
                    ++_risenKilled;
                it = _risen.erase(it);
                continue;
            }
            if (!RisenArrived(risen->GetExactDist2d(doan), doan->GetCombatReach()))
            {
                ++it;
                continue;
            }
            ++_risenArrived;
            fight.AddNextBubbleAnchors(1, "risen-purged");
            fight.Log("heresy-risen-arrived", Acore::StringFormat("arrived={} health={}/{}", _risenArrived,
                risen->GetHealth(), risen->GetMaxHealth()));
            risen->DespawnOrUnsummon();
            it = _risen.erase(it);
        }
    }

    SmDoan::BeatClock _fissureClock;
    std::vector<ObjectGuid> _risen;
    ObjectGuid _shard;
    uint32 _baseCreateHealth = 0;
    uint32 _anchorHealth = 0;
    uint32 _fissures = 0;
    uint32 _risenArrived = 0;
    uint32 _risenKilled = 0;
    uint32 _shards = 0;
    bool _risenRaised = false;
};

// -------------------------------------------------------------------------------------------------------------------
// Risen Purged 300921 (HM5): rises (Raise Dead's look), then walks to Doan and never fights. The hard mode reads
// where it is (arrived, dead); the unit only moves, re-aimed every second at him, so a slow, a root or a stun holds it
// back (the Lava Spawn pattern, incendius_hard_mode.cpp).
// -------------------------------------------------------------------------------------------------------------------

struct npc_sm_risen_purged : public ScriptedAI
{
    explicit npc_sm_risen_purged(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }

    // Nobody left to fight (Doan's cleanup despawns it anyway): gone, never a walk home.
    void EnterEvadeMode(EvadeReason /*why*/) override
    {
        me->DespawnOrUnsummon();
    }

    // The hard mode raises it: the look now, the first step after `riseMs`.
    void Rise()
    {
        me->CastSpell(me, SPELL_HERESY_RAISE_LOOK, true);
        _riseMs = kRisenRiseMs;
        _risen = true;
    }

    void UpdateAI(uint32 diff) override
    {
        if (!_risen || !UpdateVictim())
            return;
        if (_riseMs > diff)
        {
            _riseMs -= diff;
            return;
        }
        _riseMs = 0;
        _aimMs += diff;
        if (_walking && _aimMs < kRisenReaimMs)
            return;
        _aimMs = 0;
        _walking = true;
        Aim();
    }

private:
    void Aim()
    {
        if (!me->IsAlive() || me->HasUnitState(UNIT_STATE_ROOT | UNIT_STATE_STUNNED | UNIT_STATE_CONFUSED |
            UNIT_STATE_FLEEING | UNIT_STATE_DISTRACTED))
            return;
        TempSummon* summon = me->ToTempSummon();
        Unit* doan = summon ? summon->GetSummonerUnit() : nullptr;
        if (!doan || !doan->IsAlive())
            return;
        // A slow on it cuts its walk (its run speed rate against the template's).
        float rate = 1.f;
        if (CreatureTemplate const* t = me->GetCreatureTemplate())
            if (t->speed_run > 0.f)
                rate = std::clamp(me->GetSpeedRate(MOVE_RUN) / t->speed_run, 0.1f, 1.5f);
        me->GetMotionMaster()->MovePoint(1, doan->GetPositionX(), doan->GetPositionY(), doan->GetPositionZ(),
            FORCED_MOVEMENT_WALK, kRisenSpeedYdPerSec * rate);
    }

    uint32 _riseMs = 0;
    uint32 _aimMs = 0;
    bool _risen = false;
    bool _walking = false;
};

void HeresyFight::RaiseRisen(DoanFight& fight)
{
    _risenRaised = true;
    Creature* doan = fight.Doan();
    if (doan->IsAIEnabled)
        doan->AI()->Talk(SmDoan::SAY_RISE_PURGED);
    uint32 raised = 0;
    for (Point3 const& spot : kRisenSpots)
    {
        float const facing = std::atan2(doan->GetPositionY() - spot.y, doan->GetPositionX() - spot.x);
        Position const at(spot.x, spot.y, FloorZ(doan, spot.x, spot.y, spot.z), facing);
        Creature* risen = fight.Summon(NPC_SM_RISEN_PURGED, at);
        if (!risen)
            continue;
        if (doan->IsAIEnabled)
            doan->AI()->DoZoneInCombat(risen);
        if (auto* ai = risen->IsAIEnabled ? dynamic_cast<npc_sm_risen_purged*>(risen->AI()) : nullptr)
            ai->Rise();
        _risen.push_back(risen->GetGUID());
        ++raised;
    }
    fight.Log("heresy-risen", Acore::StringFormat("raised={} of {} health={} speed={:.1f}yd/s", raised, kRisenCount,
        kRisenHealth, kRisenSpeedYdPerSec));
}

// -------------------------------------------------------------------------------------------------------------------
// Phylactery Shard 300920 (HM3): one more anchor of every bubble. Stands on its spot, never moves or attacks, beams
// into the bubble while it stands (re-cast when the channel drops), never evades on its own (its fight is Doan's).
// The hard mode wards it while another anchor stands and despawns it when the bubble ends.
// -------------------------------------------------------------------------------------------------------------------

struct npc_sm_phylactery_shard : public ScriptedAI
{
    explicit npc_sm_phylactery_shard(Creature* creature) : ScriptedAI(creature) { }

    void InitializeAI() override
    {
        me->SetReactState(REACT_PASSIVE);
        me->SetCombatMovement(false);
        ScriptedAI::InitializeAI();
    }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
        _beamCheckMs = kBeamCheckMs;
    }

    void AttackStart(Unit* /*who*/) override { }
    void EnterEvadeMode(EvadeReason /*why*/) override { }

    void UpdateAI(uint32 diff) override
    {
        if (!me->IsAlive())
            return;
        if (_beamCheckMs > diff)
        {
            _beamCheckMs -= diff;
            return;
        }
        _beamCheckMs = kBeamCheckMs;
        if (me->GetCurrentSpell(CURRENT_CHANNELED_SPELL))
            return;
        TempSummon* summon = me->ToTempSummon();
        Unit* doan = summon ? summon->GetSummonerUnit() : nullptr;
        if (doan && doan->IsAlive() && doan->HasAura(SmDoan::SPELL_DN_ARCANE_BUBBLE))
            me->CastSpell(doan, SmDoan::SPELL_DN_ANCHOR_BEAM, true);
    }

private:
    static constexpr uint32 kBeamCheckMs = 1000;
    uint32 _beamCheckMs = kBeamCheckMs;
};

// -------------------------------------------------------------------------------------------------------------------
// The evidence pages 301320-301323 (goobers showing their page_text; heroic spawns only): a click counts the page
// (ReadPage) and lets the engine show its text.
// -------------------------------------------------------------------------------------------------------------------

struct go_sm_evidence_page : public GameObjectAI
{
    explicit go_sm_evidence_page(GameObject* go) : GameObjectAI(go) { }

    bool GossipHello(Player* player, bool reportUse) override
    {
        if (reportUse || !player)
            return false;
        uint32 const page = PageOf(me->GetEntry());
        if (page < kPageCount)
            ReadPage(player, page, me);
        return false;       // the goober shows its page
    }
};

// -------------------------------------------------------------------------------------------------------------------
// `.dbtest sm heresy`
// -------------------------------------------------------------------------------------------------------------------

namespace
{
    Player* Gm(ChatHandler* handler)
    {
        return handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
    }

    // The running pull's hard mode (an error and nullptr when there is none).
    HeresyFight* FindHeresy(ChatHandler* handler, DoanFight*& fight)
    {
        Creature* boss = SmTest::FindBoss(handler, NPC_DOAN);
        if (!boss)
            return nullptr;
        fight = boss->IsAIEnabled ? dynamic_cast<DoanFight*>(boss->AI()) : nullptr;
        if (!fight)
        {
            handler->SendErrorMessage("{}", "Arcanist Doan is not running boss_arcanist_doan_rework.");
            return nullptr;
        }
        auto* heresy = dynamic_cast<HeresyFight*>(fight->ActiveHardMode());
        if (!heresy)
            handler->SendErrorMessage("{}", "No Heresy pull is running (heroic: read the four pages or `.dbtest sm "
                "doan hardmode`, then pull him).");
        return heresy;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return SmTest::ShowHardModeInfo(handler, "heresy", DATA_HARD_MODE_DOAN, BOSS_HERESY);
    }

    bool HandleState(ChatHandler* handler)
    {
        InstanceScript* instance = SmTest::GmInstance(handler);
        if (!instance)
            return false;
        uint32 const mask = instance->GetData(DATA_DOAN_PAGES_MASK);
        handler->PSendSysMessage("heresy: lit={} pages={} of {} (mask {})", instance->GetData(DATA_HARD_MODE_DOAN),
            instance->GetData(DATA_DOAN_PAGE_READ), kPageCount, mask);
        DoanFight* fight = nullptr;
        Creature* boss = SmTest::FindBoss(handler, NPC_DOAN);
        fight = boss && boss->IsAIEnabled ? dynamic_cast<DoanFight*>(boss->AI()) : nullptr;
        auto* heresy = fight ? dynamic_cast<HeresyFight*>(fight->ActiveHardMode()) : nullptr;
        handler->PSendSysMessage("heresy pull: {}", heresy ? heresy->State(*fight) : std::string("none"));
        return true;
    }

    // `.dbtest sm heresy page <1-4>`: the GM reads page n where he stands (the click's checks and effects).
    bool HandlePage(ChatHandler* handler, uint32 n)
    {
        Player* gm = Gm(handler);
        if (!gm || !SmTest::RequireScarletMonastery(handler))
            return false;
        if (n < 1 || n > kPageCount)
        {
            handler->SendErrorMessage("{}", "Pages are 1-4 (1 the kennel ledger, 2 the catalog page, 3 the index "
                "page, 4 Doan's copy).");
            return false;
        }
        PageRefusal const why = ReadPage(gm, n - 1, gm);
        handler->PSendSysMessage("heresy: page {} {}", n, why == PageRefusal::None ? "read"
            : why == PageRefusal::AlreadyRead ? "already read" : why == PageRefusal::NotHeroic ? "refused (not heroic)"
            : why == PageRefusal::DoanFighting ? "refused (Doan fighting)" : why == PageRefusal::DoanDead
            ? "refused (Doan dead)" : "refused");
        return true;
    }

    bool HandleFissure(ChatHandler* handler)
    {
        DoanFight* fight = nullptr;
        HeresyFight* heresy = FindHeresy(handler, fight);
        if (!heresy)
            return false;
        if (!heresy->TestFissures(*fight))
        {
            handler->SendErrorMessage("{}", "No fissure opened (no player to pick; see the log).");
            return false;
        }
        handler->PSendSysMessage("{}", "heresy: Shadow Fissure under 2 players (HM4: 3 s, 6 yd, 60% Shadow).");
        return true;
    }

    bool HandleRisen(ChatHandler* handler)
    {
        DoanFight* fight = nullptr;
        HeresyFight* heresy = FindHeresy(handler, fight);
        if (!heresy)
            return false;
        std::string const error = heresy->TestRisen(*fight);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("{}", "heresy: six Risen Purged rise on the south wall (HM5).");
        return true;
    }

    // `.dbtest sm heresy icy`: Icy Death from Doan on the selected player (or the GM).
    bool HandleIcy(ChatHandler* handler)
    {
        Creature* boss = SmTest::FindBoss(handler, NPC_DOAN);
        Player* who = handler->GetSession() ? handler->getSelectedPlayerOrSelf() : nullptr;
        if (!boss || !who)
            return false;
        boss->CastSpell(who, SPELL_HERESY_ICY_DEATH, true);
        handler->PSendSysMessage("heresy: Icy Death on {} (HM1: a Curse, 8 s).", who->GetName());
        return true;
    }

    ChatCommandTable const& HeresyTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",    HandleInfo,    SEC_GAMEMASTER, Console::No },
            { "state",   HandleState,   SEC_GAMEMASTER, Console::No },
            { "page",    HandlePage,    SEC_GAMEMASTER, Console::No },
            { "fissure", HandleFissure, SEC_GAMEMASTER, Console::No },
            { "risen",   HandleRisen,   SEC_GAMEMASTER, Console::No },
            { "icy",     HandleIcy,     SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_sm_doan_hard_mode()
{
    SmDoan::RegisterDoanHardMode([](Creature* /*doan*/) { return std::make_unique<HeresyFight>(); });
    SmDoan::RegisterDoanIdleHook([](Creature* doan) { IdleHeresyAura(doan); });
    RegisterDungeonReworkCreatureAI(npc_sm_risen_purged, ScarletMonasteryRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sm_phylactery_shard, ScarletMonasteryRework::kInstanceScriptName);
    RegisterDungeonReworkGameObjectAI(go_sm_evidence_page, ScarletMonasteryRework::kInstanceScriptName);
    SmTest::RegisterBoss("heresy", HeresyTestCommands());
}
