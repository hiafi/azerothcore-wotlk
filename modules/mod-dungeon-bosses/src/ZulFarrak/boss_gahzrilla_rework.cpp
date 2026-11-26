/*
 * mod-dungeon-bosses, Zul'Farrak D7: Hydromancer Velratha (7795) and Gahz'rilla (7273), normal and heroic, one
 * encounter at the sacred pool (slots 0 and 1). Build spec: docs/dungeons/zul-farrak-rework.md "Hydromancer Velratha
 * and Gahz'rilla" (GZ1-GZ14, rulings 36-40); handoff sections 3.5 row D7, 3.6, 3.8 (the pool), 3.9 row 11,
 * 7 #35-#40, 10 (#40 B). Replaces SmartAI 7795, 7273 and the gong's (dropped by S0's rev); bound by apps/dbc-tools
 * source/npcs/zul_farrak/gahzrilla.py. Pure rules and every number: GahzrillaLogic.h. The hard mode hooks: PoolFight.h.
 *
 *   The pool's stalker  npc_zf_puddle (301030): summoned at the pool's middle at Velratha's pull, it holds the
 *                       encounter (PoolEncounter: the water field, Charged, Conductive, the hard mode objects) until
 *                       Gahz'rilla dies or the group wipes; neither boss lives that long. The same template is the
 *                       water field's disc (KT's WaterField summons one per puddle; their AI does nothing).
 *   GZ1 Spill the Pool  5 s, then every 10 s (heroic 8 s): a 4 s (heroic 3 s) Arcane bar, never kickable; a random
 *                       player on the pool's arena, tank included, is marked (an 8 yd circle follows them); at the
 *                       bar's end an 8 yd puddle spills where they stand. Bots carry it to the shore's rim, away
 *   GZ2 / GZ4 / GZ8     the puddles (KT's WaterField): a disc and a telegraph-only avoid zone each; frozen ones are
 *                       ice (no zone), thaw after 45 s (heroic 30 s) at the size they froze; every Discharge grows
 *                       every water puddle 2 yd (heroic 3), no cap. The pool is water for good (section 7 #37 A)
 *   GZ9 Healing Wave    12 s, then every 15 s: a kickable 3 s (heroic 2 s) Nature self-heal for 10% (20%)
 *   GZ10 The gong       at her 30% she yells line 1, runs to the gong (about 61 yd; she cannot die on the way), strikes
 *                       it (the instance arms the hard mode and summons Gahz'rilla) and fights on from there, standing
 *   The rise            Gahz'rilla, untargetable, walks from the stock summon point to (1677, 1167) (section 7 #35 A),
 *                       then fights: Velratha's target first, else the nearest player (rule 19). Hard mode: 500,000
 *   GZ3 Static Discharge  Storm Builds' clock from his arrival (normal every 30 s; heroic 20, 20, then 1.5 s sooner,
 *                       never under the bar): the meter (Static Charge, 10 stacks at the bar), emote line 0, a 3 s
 *                       Nature bar (never kickable; nothing a player does moves it) with every water sheet a zone for
 *                       the bots and the storm disc. Lands: normal 50% and a 2 s stun on anyone in water, nothing dry;
 *                       heroic 40% on everyone plus 10% per Charged stack, in water a 2 s stun and Conductive
 *   GZ5 Call the Waters 10 s, then every 15 s (heroic 12 s): a kickable 2.5 s (2 s) Arcane cast; landed, an 8 yd puddle
 *                       under 2 (heroic 3) random players, tank included, and on heroic every water puddle grows 2 yd
 *   GZ6 Icicle          6 s, then every 10 s: a 2.5 s Frost cast on a random player within 40 yd, tank included, never
 *                       kickable (the group's own freeze); the target's bot steps into the nearest water puddle. Its
 *                       hit freezes the puddle the target stands in (KT: the nearest). Heroic: no Charged on the
 *                       target during the cast; nothing frozen: Meltwater (a swimmer: the puddle at the nearest shore)
 *   GZ7 Freeze Solid    15 s, then every 22 s: 2.5 s, a 2 s Magic stun, freezes every puddle whose edge is within 8 yd
 *   GZ11 Pressure       her Frostbolt (stock 10180, a filler that never runs into a Spill); his melee, the Slam (every
 *                       25 to 35 s, everyone within 20 yd, no knock up) and Acid Spit: each swing at a target out of
 *                       his reach is a 150% Nature spit instead
 *   GZ12 Charged        heroic: a stack a second on every player in unfrozen water, for the fight, no cap
 *   GZ14 Conductive     heroic, Magic, 10 s: every 2 s it arcs for 25% to each player within 6 yd and, while its
 *                       carrier stands in water, shocks everyone in that sheet for 25% (one hit a player a tick); bots
 *                       spread 6 yd from carriers and dispel it
 *   Boss data           kill order Velratha, then Gahz'rilla; kicks: her heal, then Call the Waters; dispels:
 *                       Conductive, Freeze Solid's stun, Frostbolt's slow
 *   Arena               PoolArena() (shore and water) with LeashOptions (no grips); every random pick is a player on it
 *
 * Every timer runs on the AIs' own clocks (GahzrillaLogic.h VelrathaClock / GahzrillaClock). Cleanup (a reset, an
 * evade, his death) ends the encounter: the hard mode's OnEnd, the water, the handles, the players' auras, the
 * stalker. Every firing logs one INFO line "zf-build pool <mechanic> ..."; `.dbtest zf pool <mechanic>` fires one.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Containers.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "DungeonKitWater.h"
#include "GahzrillaLogic.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "PoolFight.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "Spell.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ZulFarrakKit.h"
#include "ZulFarrakRework.h"
#include "ZulFarrakTestCommand.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ZulFarrakRework;
using namespace ZfPool;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kLogKey = "pool";
    uint32 constexpr kMovePointGong = 1;
    uint32 constexpr kMovePointAshore = 2;
    uint32 constexpr kMovePointPin = 3;
    // SetGUID id on Gahz'rilla: the pool's stalker (Velratha's strike hands him the encounter).
    int32 constexpr kSetGuidKeeper = 1;
    float constexpr kFloorBandYd = 4.f;
    float constexpr kPinReachedYd = 1.5f;
    float constexpr kShoreRoomZ = 9.5f;

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(static_cast<int64>(ms));
    }

    void LogGz(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kLogKey, mechanic, detail);
    }

    // A player the fight acts on: in the world, alive, not a game master.
    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    // `p` on the floor (a puddle lies on it); the given height when the map has none near it.
    Position OnFloor(WorldObject const* ref, Position const& p)
    {
        float const z = p.GetPositionZ();
        float const floor = ref->GetMapHeight(p.GetPositionX(), p.GetPositionY(), z + 3.f);
        bool const ok = floor > INVALID_HEIGHT + 1.f && std::fabs(floor - z) <= kFloorBandYd;
        return Position(p.GetPositionX(), p.GetPositionY(), ok ? floor : z, p.GetOrientation());
    }

    // Create health is the base the engine rebuilds max health from (the Deadmines and Stratholme hard modes' way).
    void SetCreatureHealth(Creature* creature, uint32 health)
    {
        if (!creature || !health)
            return;
        creature->SetCreateHealth(health);
        creature->SetStatFlatModifier(UNIT_MOD_HEALTH, BASE_VALUE, static_cast<float>(health));
        creature->UpdateMaxHealth();
        creature->SetHealth(creature->GetMaxHealth());
    }

    uint32 PctOfMaxHealth(Unit const* unit, float pct)
    {
        return static_cast<uint32>(static_cast<float>(unit->GetMaxHealth()) * pct / 100.f);
    }

    // The pool's middle on its surface: the stalker's spot.
    Position PoolMiddle()
    {
        return Position((kPoolAxisFrom.x + kPoolAxisTo.x) / 2.f, (kPoolAxisFrom.y + kPoolAxisTo.y) / 2.f,
            kPoolSurfaceZ, 0.f);
    }

    // Her strike spot: kGongStandOffYd from the gong toward the shore she came from, facing the gong.
    Position GongSpot()
    {
        float const dx = kVelrathaSpawn.x - kGong.x;
        float const dy = kVelrathaSpawn.y - kGong.y;
        float const len = std::max(0.1f, std::sqrt(dx * dx + dy * dy));
        float const x = kGong.x + dx / len * Tune::kGongStandOffYd;
        float const y = kGong.y + dy / len * Tune::kGongStandOffYd;
        return Position(x, y, kGong.z, std::atan2(-dy, -dx));
    }

    // The shore polygon for the Spill carrier's drop spot (Edge: the shore's rim).
    std::vector<Position> const& ShoreRoom()
    {
        static std::vector<Position> const room = []
        {
            std::vector<Position> out;
            out.reserve(kShorePolygon.size());
            for (Vec2 const& v : kShorePolygon)
                out.emplace_back(v.x, v.y, kShoreRoomZ);
            return out;
        }();
        return room;
    }

    // The hard mode factories (PoolFight.h), in PoolPackage order.
    std::array<PoolHardModeFactory, static_cast<std::size_t>(PoolPackage::Count)>& Factories()
    {
        static std::array<PoolHardModeFactory, static_cast<std::size_t>(PoolPackage::Count)> factories;
        return factories;
    }

    // The bosses' halves the encounter calls (defined after the AIs).
    void DescribeBoss(Creature* boss);
    void PinGahzrillaAI(Creature* gahzrilla, std::optional<Position> spot);
    void IcicleEveryAI(Creature* gahzrilla, uint32 everyMs);
}

// ---------------------------------------------------------------------------------------------------------------------
// The encounter (PoolFight.h), held by the pool's stalker from Velratha's pull to the encounter's end
// ---------------------------------------------------------------------------------------------------------------------

class PoolEncounter final : public PoolFight
{
public:
    explicit PoolEncounter(Creature* keeper) : _map(keeper->GetMap()), _keeper(keeper->GetGUID()) { }

    // Velratha's pull (or a Gahz'rilla without one): the water field, the pool, then the hard mode objects.
    void Begin(Creature* velratha, bool heroic, bool hardMode)
    {
        _velratha = velratha ? velratha->GetGUID() : ObjectGuid::Empty;
        _heroic = heroic;
        _phase = PoolPhase::Velratha;
        DungeonKit::WaterFieldSpec spec;
        spec.discEntry = NPC_ZF_PUDDLE;
        spec.looks.water = kDisplayWaterDisc;
        spec.looks.ice = kDisplayIceDisc;
        spec.looks.storm = kDisplayStormDisc;
        spec.looks.ydPerScale = kDiscYdPerScale;
        spec.tag = TAG_GZ_WATER;
        spec.dungeon = kLogDungeon;
        spec.boss = kLogKey;
        spec.name = "water";
        _water.Configure(spec);
        if (Creature* keeper = Keeper())
        {
            Position const from(kPoolAxisFrom.x, kPoolAxisFrom.y, kPoolSurfaceZ);
            Position const to(kPoolAxisTo.x, kPoolAxisTo.y, kPoolSurfaceZ);
            _poolSheet = _water.AddStrip(keeper, from, to, kPoolHalfWidthYd, PoolRules());
        }
        if (hardMode)
        {
            _hardModes = CreatePoolHardModes(*this);
            Log("hardmode", Acore::StringFormat("packages={}", _hardModes.size()));
            for (std::unique_ptr<PoolHardMode>& hm : _hardModes)
                hm->OnEngage(*this);
        }
        Log("begin", Acore::StringFormat("heroic={} hardmode={} pool={}", _heroic ? 1 : 0, hardMode ? 1 : 0,
            _poolSheet));
    }

    bool Ended() const { return _ended; }

    void Update(uint32 diff)
    {
        if (_ended)
            return;
        Creature* keeper = Keeper();
        if (!keeper)
            return;
        _clock += diff;
        _water.Update(keeper, diff);
        if (_heroic)
        {
            _chargedTick += diff;
            while (_chargedTick >= Tune::kChargedTickMs)
            {
                _chargedTick -= Tune::kChargedTickMs;
                TickCharged();
            }
            TickConductive();
        }
        for (std::unique_ptr<PoolHardMode>& hm : _hardModes)
            hm->OnUpdate(*this, diff);
    }

    // Gahz'rilla's death (won), a wipe or an evade. The stalker leaves shortly after (never inside its own tick).
    void End(bool won, char const* why)
    {
        if (_ended)
            return;
        for (std::unique_ptr<PoolHardMode>& hm : _hardModes)
            hm->OnEnd(*this, won);
        _hardModes.clear();
        _ended = true;
        Creature* keeper = Keeper();
        _water.Clear(keeper);
        if (keeper)
            for (MechanicHandle const& h : _handles)
                Mechanic::Cancel(keeper, h);
        _handles.clear();
        for (ObjectGuid const& guid : _summons)
            if (Creature* summon = _map->GetCreature(guid))
                summon->DespawnOrUnsummon();
        _summons.clear();
        if (InstanceScript* instance = Instance())
            for (uint32 const spell : { uint32(SPELL_GZ_CHARGED), uint32(SPELL_GZ_CONDUCTIVE),
                uint32(SPELL_GZ_STATIC_SHOCK), uint32(SPELL_GZ_SPILL_MARK), uint32(SPELL_GZ_FREEZE_SOLID),
                uint32(SPELL_GZ_ICICLE) })
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
        _conductive.clear();
        // A Gahz'rilla still rising or idle must not wait in the pool for the next strike (the instance does it too).
        if (!won)
            if (Creature* gahzrilla = Gahzrilla())
                if (gahzrilla->IsAlive() && !gahzrilla->IsEngaged())
                    gahzrilla->DespawnOrUnsummon(1s);
        Log("end", Acore::StringFormat("won={} why={} clock={}s discharges={} spills={} calls={} freezes={} "
            "meltwater={} conductive={}", won ? 1 : 0, why, _clock / 1000, _landed, _counts.spills, _counts.calls,
            _counts.freezes, _counts.meltwater, _counts.conductive));
        if (keeper)
            keeper->DespawnOrUnsummon(500ms);
    }

    // ---- Called by the bosses ---------------------------------------------------------------------------------------

    // The strike (GZ10): the instance summoned him (or not: dead for the lockout). `armed`: DATA_HARD_MODE is set.
    void GongStruck(Creature* gahzrilla, bool armed)
    {
        if (gahzrilla)
            _gahzrilla = gahzrilla->GetGUID();
        _phase = PoolPhase::Rise;
        for (std::unique_ptr<PoolHardMode>& hm : _hardModes)
            hm->OnGongStruck(*this, armed);
        if (!armed && !_hardModes.empty())
        {
            for (std::unique_ptr<PoolHardMode>& hm : _hardModes)
                hm->OnEnd(*this, false);
            _hardModes.clear();
            Log("hardmode-dropped", "the flag did not arm at the gong");
        }
    }

    void VelrathaDied()
    {
        for (std::unique_ptr<PoolHardMode>& hm : _hardModes)
            hm->OnVelrathaDied(*this);
        // Gahz'rilla never came (slot 1 DONE for the lockout): her death ends it.
        if (!Gahzrilla())
            End(true, "velratha-only");
    }

    void GahzrillaArrived(Creature* gahzrilla)
    {
        _gahzrilla = gahzrilla->GetGUID();
        _phase = PoolPhase::Gahzrilla;
        _arrivedAt = _clock;
        for (std::unique_ptr<PoolHardMode>& hm : _hardModes)
            hm->OnGahzrillaArrive(*this);
    }

    void GahzrillaDamaged(Unit* attacker, uint32& damage)
    {
        for (std::unique_ptr<PoolHardMode>& hm : _hardModes)
            hm->OnGahzrillaDamaged(*this, attacker, damage);
    }

    // GZ1: the marked player's puddle.
    void SpillLanded(Position const& spot)
    {
        ++_counts.spills;
        AddPuddle(spot, Tune::kPuddleRadiusYd, SHEET_SPILL, "spill");
    }

    // GZ3: the bar starts (the water's zones for the bots and the storm discs).
    void DischargeBar()
    {
        if (Creature* keeper = Keeper())
            _water.RegisterDischarge(keeper, Ms(Tune::kDischargeCastMs), [](MechanicRef& zone)
            {
                zone.Tag(TAG_GZ_DISCHARGE);
            });
        for (std::unique_ptr<PoolHardMode>& hm : _hardModes)
            hm->OnDischargeBar(*this);
    }

    // GZ3, GZ4, GZ12, GZ14: the landing. Returns the players hit.
    std::vector<DischargeHit> DischargeLand(Creature* gahzrilla)
    {
        ++_landed;
        bool everyone = false;
        for (std::unique_ptr<PoolHardMode>& hm : _hardModes)
            everyone = everyone || hm->ConductiveOnEveryone(*this);
        std::vector<DischargeHit> hits;
        uint32 carriers = 0;
        for (Player* player : FightPlayers())
        {
            DischargeHit hit;
            hit.player = player->GetGUID();
            hit.inWater = IsWater(player);
            hit.charged = _heroic ? Charged(player) : 0;
            hit.pct = DischargePct(_heroic, hit.inWater, hit.charged);
            if (hit.pct > 0.f)
            {
                CastSpellExtraArgs args(TRIGGERED_FULL_MASK);
                args.AddSpellBP0(static_cast<int32>(DungeonKit::RefFlatOn(gahzrilla, player, hit.pct)));
                gahzrilla->CastSpell(player, SPELL_GZ_DISCHARGE, args);
            }
            if (player->IsAlive() && hit.inWater)
                gahzrilla->CastSpell(player, SPELL_GZ_STATIC_SHOCK, true);
            if (_heroic && player->IsAlive() && (hit.inWater || everyone) && ApplyConductive(player))
                ++carriers;
            hits.push_back(hit);
        }
        if (carriers)
        {
            MechanicRef ring = Mechanic::Spread(gahzrilla, Tune::kConductiveArcYd, Ms(Tune::kConductiveTickMs));
            ring.SelfTrigger(SPELL_GZ_CONDUCTIVE, 1)
                .Persistent(Ms(Tune::kConductiveMs), Ms(Tune::kConductiveTickMs))
                .Tag(TAG_GZ_CONDUCTIVE);
            Track(ring.Handle());
        }
        for (std::unique_ptr<PoolHardMode>& hm : _hardModes)
            hm->OnDischargeLand(*this, hits);
        Creature* keeper = Keeper();
        std::size_t const grown = keeper ? _water.GrowWater(keeper, Tune::kRisingWaterYd(_heroic)).size() : 0;
        uint32 wet = 0;
        for (DischargeHit const& hit : hits)
            wet += hit.inWater ? 1 : 0;
        Log("discharge-land", Acore::StringFormat("n={} players={} in-water={} conductive={} grown={} water={} ice={}",
            _landed, hits.size(), wet, carriers, grown, _water.Sheets().CountIn(DungeonKit::SheetState::Water),
            _water.Sheets().CountIn(DungeonKit::SheetState::Ice)));
        return hits;
    }

    // GZ5: his own cast landed or was stopped.
    void CallTheWaters(Unit* caster, bool landed)
    {
        if (landed)
            LandCall(caster, "call");
        for (std::unique_ptr<PoolHardMode>& hm : _hardModes)
            hm->OnCallTheWaters(*this, landed);
    }

    // GZ6 / GZ7 / GZ8 / GZ13: a freeze landed at `at` on `target`.
    void Freeze(FreezeKind kind, Unit* target, Position const& at)
    {
        Creature* keeper = Keeper();
        if (!keeper || _ended)
            return;
        DungeonKit::FreezeResult r = kind == FreezeKind::Icicle ? _water.FreezeAt(keeper, at)
            : _water.FreezeWithin(keeper, at, Tune::kFreezeSolidReachYd);
        _counts.freezes += static_cast<uint32>(r.frozen.size());
        for (uint32 const id : r.frozen)
            if (Creature* disc = _map->GetCreature(_water.DiscOf(id)))
                disc->CastSpell(disc, SPELL_GZ_FREEZE_LOOK, true);
        for (std::unique_ptr<PoolHardMode>& hm : _hardModes)
            if (hm->OnFreeze(*this, kind, target, at, r))
                return;
        switch (MeltFor(_heroic, r))
        {
            case Melt::AtTarget:
                ++_counts.meltwater;
                AddPuddle(at, Tune::kPuddleRadiusYd, SHEET_MELTWATER, "meltwater");
                break;
            case Melt::AtShore:
            {
                ++_counts.meltwater;
                Vec2 const shore = ShoreSpotFor({ at.GetPositionX(), at.GetPositionY() });
                AddPuddle(Position(shore.x, shore.y, kShoreRoomZ), Tune::kPuddleRadiusYd, SHEET_MELTWATER,
                    "meltwater-shore");
                break;
            }
            case Melt::None:
                break;
        }
    }

    // GZ12: the Icicle target gains no Charged for `forMs` (its cast).
    void SetBait(ObjectGuid target, uint64 forMs)
    {
        _bait = target;
        _baitUntil = _clock + forMs;
    }

    void NoteStorm(uint32 landed, uint64 nextInMs)
    {
        _landed = landed;
        _nextLandIn = nextInMs;
    }

    void DescribeExtra(Creature* boss, BossMechanics::Descriptor& d)
    {
        for (std::unique_ptr<PoolHardMode>& hm : _hardModes)
            hm->DescribeExtra(*this, boss, d);
    }

    std::string State() const
    {
        return Acore::StringFormat("clock={}s phase={} heroic={} hardmode={} sheets={} water={} ice={} discharges={} "
            "next={}ms conductive={} spills={} calls={} freezes={} meltwater={}", _clock / 1000, uint32(_phase),
            _heroic ? 1 : 0, _hardModes.empty() ? 0 : 1, _water.Count(),
            _water.Sheets().CountIn(DungeonKit::SheetState::Water),
            _water.Sheets().CountIn(DungeonKit::SheetState::Ice), _landed, _nextLandIn, _conductive.size(),
            _counts.spills, _counts.calls, _counts.freezes, _counts.meltwater);
    }

    // Every ice sheet back to water now (`.dbtest`).
    uint32 ThawAll()
    {
        std::vector<uint32> ids;
        for (DungeonKit::WaterSheet const& s : _water.All())
            if (!s.IsWater())
                ids.push_back(s.id);
        for (uint32 const id : ids)
            _water.Thaw(Keeper(), id);
        return static_cast<uint32>(ids.size());
    }

    // ---- PoolFight --------------------------------------------------------------------------------------------------

    Creature* Keeper() override { return _map->GetCreature(_keeper); }
    Creature* Velratha() override { return _velratha.IsEmpty() ? nullptr : _map->GetCreature(_velratha); }
    Creature* Gahzrilla() override { return _gahzrilla.IsEmpty() ? nullptr : _map->GetCreature(_gahzrilla); }
    InstanceScript* Instance() override
    {
        InstanceMap* instance = _map->ToInstanceMap();
        return instance ? instance->GetInstanceScript() : nullptr;
    }
    bool Heroic() const override { return _heroic; }
    bool HardMode() const override { return !_hardModes.empty(); }
    PoolPhase Phase() const override { return _phase; }
    void SetPhase(PoolPhase phase) override
    {
        _phase = phase;
        if (Creature* gahzrilla = Gahzrilla())
            Mechanic::SetPhase(gahzrilla, static_cast<uint32>(phase));
        Log("phase", Acore::StringFormat("{}", uint32(phase)));
    }
    uint64 ClockMs() const override { return _clock; }
    uint64 GahzrillaClockMs() const override
    {
        return _phase >= PoolPhase::Gahzrilla && _clock >= _arrivedAt ? _clock - _arrivedAt : 0;
    }

    std::vector<Player*> FightPlayers() override
    {
        std::vector<Player*> out;
        for (MapReference const& ref : _map->GetPlayers())
            if (Player* player = ref.GetSource())
                if (CountsAsPlayer(player) && _arena.Contains(DungeonKit::PlaneOf(player), player->GetPositionZ()))
                    out.push_back(player);
        return out;
    }

    DungeonKit::WaterField& Water() override { return _water; }

    uint32 AddPuddle(Position const& at, float radius, uint32 kind, char const* why) override
    {
        Creature* keeper = Keeper();
        if (!keeper || _ended)
            return 0;
        Position const spot = OnFloor(keeper, at);
        uint32 const id = _water.Add(keeper, spot, radius > 0.f ? radius : Tune::kPuddleRadiusYd,
            PuddleRules(_heroic, kind));
        Log("puddle", Acore::StringFormat("why={} id={} at=({:.1f}, {:.1f}, {:.1f}) water={} ice={}", why, id,
            spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(),
            _water.Sheets().CountIn(DungeonKit::SheetState::Water),
            _water.Sheets().CountIn(DungeonKit::SheetState::Ice)));
        return id;
    }

    uint32 AddSheet(Position const& at, float radius, DungeonKit::SheetRules const& rules,
        DungeonKit::SheetState state, char const* why) override
    {
        Creature* keeper = Keeper();
        if (!keeper || _ended)
            return 0;
        uint32 const id = _water.Add(keeper, at, radius, rules, state);
        Log("sheet", Acore::StringFormat("why={} id={} radius={:.1f} kind={}", why, id, radius, rules.kind));
        return id;
    }

    bool IsWater(WorldObject const* o) const override { return _water.IsWater(o); }
    uint32 PoolSheet() const override { return _poolSheet; }

    uint32 DischargesLanded() const override { return _landed; }
    uint64 NextDischargeInMs() const override { return _nextLandIn; }
    void SetIcicleEvery(uint32 everyMs) override
    {
        if (Creature* gahzrilla = Gahzrilla())
            IcicleEveryAI(gahzrilla, everyMs);
    }

    uint32 Charged(Unit const* unit) const override
    {
        return unit ? DungeonKit::Stacks(unit, SPELL_GZ_CHARGED) : 0;
    }

    uint32 AddCharged(Unit* unit, int32 delta) override
    {
        if (!unit || !unit->IsAlive())
            return 0;
        return DungeonKit::AddStacks(unit, SPELL_GZ_CHARGED, delta, Keeper(), Tune::kChargedMaxStacks);
    }

    bool ApplyConductive(Unit* unit) override
    {
        Unit* caster = ReferenceOwner();
        if (!unit || !unit->IsAlive() || !caster)
            return false;
        caster->CastSpell(unit, SPELL_GZ_CONDUCTIVE, true);
        if (!unit->HasAura(SPELL_GZ_CONDUCTIVE))
            return false;
        _conductive[unit->GetGUID()] = _clock + Tune::kConductiveTickMs;
        ++_counts.conductive;
        return true;
    }

    void PinGahzrilla(std::optional<Position> spot) override
    {
        if (Creature* gahzrilla = Gahzrilla())
            PinGahzrillaAI(gahzrilla, spot);
    }

    void HealGahzrilla(float pct) override
    {
        Creature* gahzrilla = Gahzrilla();
        if (!gahzrilla || !gahzrilla->IsAlive())
            return;
        uint32 const heal = PctOfMaxHealth(gahzrilla, pct);
        gahzrilla->ModifyHealth(static_cast<int32>(heal));
        Log("heal", Acore::StringFormat("pct={:.1f} amount={} health={:.1f}", pct, heal, gahzrilla->GetHealthPct()));
    }

    void LandCallTheWaters(Unit* caster, char const* why) override
    {
        LandCall(caster, why);
    }

    Creature* Summon(uint32 entry, Position const& at, uint32 despawnMs) override
    {
        Creature* keeper = Keeper();
        if (!keeper || _ended)
            return nullptr;
        Creature* summon = keeper->SummonCreature(entry, at,
            despawnMs ? TEMPSUMMON_TIMED_DESPAWN : TEMPSUMMON_MANUAL_DESPAWN, despawnMs);
        if (summon)
            _summons.push_back(summon->GetGUID());
        return summon;
    }

    void Track(MechanicHandle handle) override
    {
        if (handle)
            _handles.push_back(handle);
    }

    void RefreshDescriptors() override
    {
        if (Creature* velratha = Velratha())
            DescribeBoss(velratha);
        if (Creature* gahzrilla = Gahzrilla())
            DescribeBoss(gahzrilla);
    }

    uint32 RefFlatOn(Unit const* target, float pct) override
    {
        return DungeonKit::RefFlatOn(ReferenceOwner(), target, pct);
    }

    void Log(char const* mechanic, std::string const& detail = {}) override
    {
        LogGz(mechanic, detail);
    }

private:
    // The fight's boss for hits and reference rows: Gahz'rilla alive, else Velratha alive, else the stalker.
    Unit* ReferenceOwner()
    {
        if (Creature* gahzrilla = Gahzrilla(); gahzrilla && gahzrilla->IsAlive())
            return gahzrilla;
        if (Creature* velratha = Velratha(); velratha && velratha->IsAlive())
            return velratha;
        return Keeper();
    }

    // GZ5 / GZ20: a puddle under `count` random players (the tank included); heroic, every water puddle grows 2 yd.
    void LandCall(Unit* caster, char const* why)
    {
        ++_counts.calls;
        std::vector<Player*> players = FightPlayers();
        Acore::Containers::RandomShuffle(players);
        uint32 const count = std::min<uint32>(Tune::kCallPuddles(_heroic), static_cast<uint32>(players.size()));
        std::string names;
        for (uint32 i = 0; i < count; ++i)
        {
            AddPuddle(players[i]->GetPosition(), Tune::kPuddleRadiusYd, SHEET_CALL, why);
            names += (names.empty() ? "" : ",") + players[i]->GetName();
        }
        std::size_t grown = 0;
        if (Creature* keeper = Keeper(); _heroic && keeper)
            grown = _water.GrowWater(keeper, Tune::kCallHeroicGrowYd).size();
        Log("call-land", Acore::StringFormat("why={} caster={} puddles={} grown={} under={}", why,
            caster ? caster->GetName() : "none", count, grown, names.empty() ? "-" : names));
    }

    // GZ12: a stack a second on every player in unfrozen water (heroic), the Icicle target spared during its cast.
    void TickCharged()
    {
        for (Player* player : FightPlayers())
        {
            if (!IsWater(player))
                continue;
            if (player->GetGUID() == _bait && _clock < _baitUntil)
                continue;
            AddCharged(player, 1);
        }
    }

    // GZ14: every 2 s per carrier, an arc to each player within 6 yd and, in water, a shock to everyone in its sheet.
    void TickConductive()
    {
        for (auto it = _conductive.begin(); it != _conductive.end();)
        {
            Player* carrier = ObjectAccessor::GetPlayer(_map, it->first);
            if (!carrier || !carrier->IsAlive() || !carrier->HasAura(SPELL_GZ_CONDUCTIVE))
            {
                it = _conductive.erase(it);
                continue;
            }
            if (_clock >= it->second)
            {
                it->second += Tune::kConductiveTickMs;
                Arc(carrier);
            }
            ++it;
        }
    }

    // One hit a player a tick, whether the arc, the sheet's shock or both reach them (section 9 Q4 of the report).
    void Arc(Player* carrier)
    {
        Unit* owner = ReferenceOwner();
        if (!owner)
            return;
        std::optional<uint32> const sheet = IsWater(carrier)
            ? _water.WaterSheetAt(carrier->GetPosition()) : std::nullopt;
        uint32 arcs = 0;
        uint32 shocks = 0;
        for (Player* player : FightPlayers())
        {
            bool const arc = player != carrier && player->GetExactDist(carrier) <= Tune::kConductiveArcYd;
            bool const shock = sheet && _water.InWaterSheet(*sheet, player);
            if (!arc && !shock)
                continue;
            arcs += arc ? 1 : 0;
            shocks += shock ? 1 : 0;
            CastSpellExtraArgs args(TRIGGERED_FULL_MASK);
            args.AddSpellBP0(static_cast<int32>(DungeonKit::RefFlatOn(owner, player, Tune::kConductivePct)));
            owner->CastSpell(player, SPELL_GZ_CONDUCTIVE_ARC, args);
        }
        if (arcs || shocks)
            Log("conductive-arc", Acore::StringFormat("carrier={} arcs={} sheet={} shocks={}", carrier->GetName(), arcs,
                sheet ? *sheet : 0, shocks));
    }

    struct Counts
    {
        uint32 spills = 0;
        uint32 calls = 0;
        uint32 freezes = 0;
        uint32 meltwater = 0;
        uint32 conductive = 0;
    };

    Map* _map;
    ObjectGuid _keeper;
    ObjectGuid _velratha;
    ObjectGuid _gahzrilla;
    Arena const _arena = PoolArena();
    DungeonKit::WaterField _water;
    uint32 _poolSheet = 0;
    bool _heroic = false;
    bool _ended = false;
    PoolPhase _phase = PoolPhase::Velratha;
    uint64 _clock = 0;
    uint64 _arrivedAt = 0;
    uint32 _chargedTick = 0;
    uint32 _landed = 0;
    uint64 _nextLandIn = 0;
    ObjectGuid _bait;
    uint64 _baitUntil = 0;
    std::unordered_map<ObjectGuid, uint64> _conductive;     // carrier -> the fight's clock at its next arc
    std::vector<std::unique_ptr<PoolHardMode>> _hardModes;
    std::vector<MechanicHandle> _handles;
    std::vector<ObjectGuid> _summons;
    Counts _counts;
};

// ---------------------------------------------------------------------------------------------------------------------
// npc_zf_puddle (301030): the pool's stalker (holds the encounter) or a water disc (does nothing)
// ---------------------------------------------------------------------------------------------------------------------

struct npc_zf_puddle : public PassiveAI
{
    explicit npc_zf_puddle(Creature* creature) : PassiveAI(creature)
    {
        me->SetReactState(REACT_PASSIVE);
    }

    // Velratha's pull (or a Gahz'rilla without one): this stalker holds the encounter from now on.
    PoolEncounter* BecomeKeeper()
    {
        if (!_fight)
        {
            _fight = std::make_unique<PoolEncounter>(me);
            me->setActive(true);
        }
        return _fight.get();
    }

    PoolEncounter* Fight() { return _fight && !_fight->Ended() ? _fight.get() : nullptr; }

    void UpdateAI(uint32 diff) override
    {
        if (_fight)
            _fight->Update(diff);
    }

    void EnterEvadeMode(EvadeReason /*why*/) override { }

private:
    std::unique_ptr<PoolEncounter> _fight;
};

namespace
{
    PoolEncounter* FightOf(Map* map, ObjectGuid keeper)
    {
        Creature* stalker = (map && !keeper.IsEmpty()) ? map->GetCreature(keeper) : nullptr;
        if (!stalker || !stalker->IsAIEnabled)
            return nullptr;
        auto* ai = dynamic_cast<npc_zf_puddle*>(stalker->AI());
        return ai ? ai->Fight() : nullptr;
    }

    // A new stalker at the pool's middle (no summoner: no boss's summon list holds it) with a fresh encounter.
    std::pair<ObjectGuid, PoolEncounter*> SummonKeeper(Creature* by)
    {
        TempSummon* stalker = by->GetMap()->SummonCreature(NPC_ZF_PUDDLE, PoolMiddle());
        if (!stalker || !stalker->IsAIEnabled)
            return { ObjectGuid::Empty, nullptr };
        auto* ai = dynamic_cast<npc_zf_puddle*>(stalker->AI());
        if (!ai)
        {
            stalker->DespawnOrUnsummon();
            return { ObjectGuid::Empty, nullptr };
        }
        return { stalker->GetGUID(), ai->BecomeKeeper() };
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// Hydromancer Velratha 7795 (slot 0)
// ---------------------------------------------------------------------------------------------------------------------

struct boss_velratha_rework : public BossAI
{
    explicit boss_velratha_rework(Creature* creature)
        : BossAI(creature, BOSS_VELRATHA), _arena(PoolArena(), LeashOptions(kLogKey)) { }

    void Reset() override
    {
        _Reset();
        if (!_baseHealth)
            _baseHealth = me->GetMaxHealth();
        Cleanup();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        Cleanup();
        _heroic = IsHeroicMap(me);
        _hardMode = _heroic && HardModeNow();
        // Section 7 #1 A: 200,000 on the hard mode (S0 Q3: the key at her pull); else the template's own health.
        SetCreatureHealth(me, _hardMode ? Health::kHardModeVelratha : _baseHealth);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_VELRATHA;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);
        _engaged = true;
        _clock.Start(_heroic);
        StartFight();
        Describe();
        OnBossPull(me, kLogKey, _hardMode);
        Talk(YELL_VELRATHA_AGGRO);
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        if (_engaged)
            LogGz("velratha-evade", Acore::StringFormat("reason={}", uint32(why)));
        // A Gahz'rilla in combat keeps the encounter (his own evade ends it); otherwise this is the wipe.
        if (PoolEncounter* fight = Fight())
        {
            Creature* gahzrilla = fight->Gahzrilla();
            if (!(gahzrilla && gahzrilla->IsAlive() && gahzrilla->IsEngaged()))
                fight->End(false, "velratha-evade");
        }
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        LogGz("velratha-death", Acore::StringFormat("clock={}s struck={} killer={}", _clock.Now() / 1000,
            _struck ? 1 : 0, killer ? killer->GetName() : "none"));
        if (PoolEncounter* fight = Fight())
            fight->VelrathaDied();
        Cleanup();
        BossAI::JustDied(killer);
    }

    // Nothing of hers is zoned into combat.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    // GZ10: she cannot die before the strike (her last 30% plays out at the gong, during his rise).
    void DamageTaken(Unit* /*attacker*/, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*mask*/) override
    {
        if (_engaged && !_struck && _lethal.Intercept(me, damage))
            LogGz("velratha-held", "a lethal hit before the gong");
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type == POINT_MOTION_TYPE && id == kMovePointGong && _run)
            Strike("arrived");
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (!spell || !_engaged)
            return;
        if (spell->Id == SPELL_GZ_HEALING_WAVE || spell->Id == SPELL_GZ_HEALING_WAVE_HEROIC)
            LogGz("heal-stopped", Acore::StringFormat("health={:.1f}", me->GetHealthPct()));
        else if (spell->Id == SPELL_FROSTBOLT)
            LogGz("frostbolt-stopped");
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        BossAI::OnSpellCast(spell);
        if (spell && _engaged && (spell->Id == SPELL_GZ_HEALING_WAVE || spell->Id == SPELL_GZ_HEALING_WAVE_HEROIC))
            LogGz("heal", Acore::StringFormat("health={:.1f}", me->GetHealthPct()));
    }

    void UpdateAI(uint32 diff) override
    {
        ZulFarrak::NoAssist(me);        // rule 27, LESSONS L1: every tick, before UpdateVictim
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off her arena, or nobody on it for 10 s: evading
        if (!_engaged)
            return;

        _clock.Advance(diff);
        if (_run)
        {
            _runMs += diff;
            if (_runMs >= Tune::kGongRunTimeoutMs)
                Strike("timeout");
            return;     // no casts on the run
        }
        if (GongDue(me->GetHealthPct(), _struck))
        {
            StartGongRun();
            return;
        }
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        VAct const act = _clock.Next();
        if (act != VAct::None)
        {
            if (Begin(act))
                _clock.Done(act, act == VAct::Frostbolt
                    ? urand(Tune::kFrostboltEveryMinMs, Tune::kFrostboltEveryMaxMs) : 0);
            else
                _clock.Retry(act);
            if (me->HasUnitState(UNIT_STATE_CASTING))
                return;
        }
        DoMeleeAttackIfReady();
    }

    // ---- shared with the encounter and `.dbtest` --------------------------------------------------------------------

    PoolEncounter* Fight() { return FightOf(me->GetMap(), _keeper); }
    ObjectGuid KeeperGuid() const { return _keeper; }

    void Describe()
    {
        BossMechanics::Descriptor d;
        uint32 const heal = _heroic ? SPELL_GZ_HEALING_WAVE_HEROIC : SPELL_GZ_HEALING_WAVE;
        d.interrupts.emplace_back(NPC_VELRATHA, heal, kHealKickPriority, Ms(Tune::kHealEveryMs));
        d.dispels.emplace_back(SPELL_FROSTBOLT, kFrostboltDispelPriority);
        if (_heroic)
            d.dispels.emplace_back(SPELL_GZ_CONDUCTIVE, kConductiveDispelPriority);
        // Kill order: Velratha, then Gahz'rilla (phase 1 has only her; she is finished at the gong while he rises).
        d.targets.emplace_back(NPC_VELRATHA, 2);
        d.targets.emplace_back(NPC_GAHZRILLA, 1);
        if (PoolEncounter* fight = Fight())
            fight->DescribeExtra(me, d);
        Mechanic::Describe(me, std::move(d));
        Mechanic::NoteNextCastIn(me, heal, Ms(_clock.In(VAct::Heal)));
    }

    enum class TestMechanic : uint8
    {
        Gong,
        Spill,
        Heal,
    };

    std::string TestFire(TestMechanic mechanic, Player* who)
    {
        if (!_engaged || !me->IsEngaged())
            return "Velratha must be in combat (the picks read the pool's players, the mechanics her encounter).";
        Player* forced = CountsAsPlayer(who) ? who : nullptr;
        switch (mechanic)
        {
            case TestMechanic::Gong:
                if (_struck || _run)
                    return "She has struck the gong already (or is on her way).";
                StartGongRun();
                break;
            case TestMechanic::Spill:
                if (me->HasUnitState(UNIT_STATE_CASTING) || _run)
                    return "She is casting (or running to the gong).";
                if (!CastSpill(forced))
                    return "The engine refused it.";
                break;
            case TestMechanic::Heal:
                if (me->HasUnitState(UNIT_STATE_CASTING) || _run)
                    return "She is casting (or running to the gong).";
                if (!CastHeal())
                    return "The engine refused it (a kick locked Nature?).";
                break;
        }
        return {};
    }

    std::string TestState()
    {
        return Acore::StringFormat("clock={}s heroic={} hardmode={} health={:.1f} struck={} run={} next: spill {} ms, "
            "heal {} ms, frostbolt {} ms", _clock.Now() / 1000, _heroic ? 1 : 0, _hardMode ? 1 : 0,
            me->GetHealthPct(), _struck ? 1 : 0, _run ? 1 : 0, _clock.In(VAct::Spill), _clock.In(VAct::Heal),
            _clock.In(VAct::Frostbolt));
    }

private:
    bool HardModeNow() const
    {
        InstanceScript const* script = me->GetInstanceScript();
        return script && (script->GetData(DATA_HARD_MODE) || script->GetData(DATA_HARD_MODE_KEY));
    }

    // The encounter: a stalker left from an earlier pull ends first (RB-1), then a new one begins.
    void StartFight()
    {
        if (PoolEncounter* old = Fight())
            old->End(false, "new-pull");
        auto [guid, fight] = SummonKeeper(me);
        _keeper = guid;
        if (!fight)
        {
            LogGz("keeper-fail", "the pool's stalker could not be summoned: no water this pull");
            return;
        }
        fight->Begin(me, _heroic, _hardMode);
    }

    bool Begin(VAct act)
    {
        switch (act)
        {
            case VAct::Spill:
                return CastSpill(nullptr);
            case VAct::Heal:
                return CastHeal();
            case VAct::Frostbolt:
                return CastFrostbolt();
            case VAct::None:
                break;
        }
        return true;
    }

    // ---- GZ1 Spill the Pool ----

    bool CastSpill(Player* forced)
    {
        PoolEncounter* fight = Fight();
        if (!fight)
            return true;        // no water this pull (logged at the pull): the beat passes
        Player* target = forced;
        if (!target)
        {
            std::vector<Player*> const players = fight->FightPlayers();
            if (players.empty())
                return true;
            target = Acore::Containers::SelectRandomContainerElement(players);
        }
        uint32 const bar = _heroic ? SPELL_GZ_SPILL_HEROIC : SPELL_GZ_SPILL;
        uint32 const castMs = Tune::kSpillCastMs(_heroic);
        me->StopMoving();
        SpellCastResult const result = me->CastSpell(me, bar, false);
        if (result != SPELL_CAST_OK)
        {
            LogGz("spill-refused", Acore::StringFormat("result={}", uint32(result)));
            return false;
        }
        me->CastSpell(target, SPELL_GZ_SPILL_MARK, true);
        DungeonKit::ShortenAura(target, SPELL_GZ_SPILL_MARK, me->GetGUID(), Ms(castMs));

        DungeonKit::ImpactSpec impact;
        impact.pct = 0.f;
        impact.weakened = false;
        impact.tag = TAG_GZ_SPILL;
        Map* map = me->GetMap();
        ObjectGuid const keeper = _keeper;
        ObjectGuid const targetGuid = target->GetGUID();
        MechanicRef mark = DungeonKit::FollowThenLand(me, target, Tune::kPuddleRadiusYd, Ms(castMs), impact,
            [map, keeper, targetGuid](Creature* /*owner*/, Position const& spot, BossMechanics::ResolveResult const&)
            {
                if (Player* player = ObjectAccessor::GetPlayer(map, targetGuid))
                    player->RemoveAurasDueToSpell(SPELL_GZ_SPILL_MARK);
                if (PoolEncounter* f = FightOf(map, keeper))
                    f->SpillLanded(spot);
            });
        BossMechanics::DropSpotRule rule;
        rule.Room(ShoreRoom()).Edge().Away();
        rule.bounds = PoolFloorBounds();
        mark.DropSpot(rule);
        LogGz("spill", Acore::StringFormat("target={} tank={} cast={}ms", target->GetName(),
            target == me->GetVictim() ? 1 : 0, castMs));
        return true;
    }

    // ---- GZ9 Healing Wave ----

    bool CastHeal()
    {
        uint32 const spell = _heroic ? SPELL_GZ_HEALING_WAVE_HEROIC : SPELL_GZ_HEALING_WAVE;
        CastSpellExtraArgs args(TRIGGERED_NONE);
        args.AddSpellBP0(static_cast<int32>(PctOfMaxHealth(me, Tune::kHealPct(_heroic))));
        me->StopMoving();
        SpellCastResult const result = me->CastSpell(me, spell, args);
        if (result != SPELL_CAST_OK)
        {
            LogGz("heal-refused", Acore::StringFormat("result={}", uint32(result)));
            return false;
        }
        LogGz("heal-cast", Acore::StringFormat("health={:.1f} pct={:.0f}", me->GetHealthPct(),
            Tune::kHealPct(_heroic)));
        Mechanic::NoteNextCastIn(me, spell, Ms(Tune::kHealEveryMs));
        return true;
    }

    // ---- GZ11 Frostbolt (stock 10180) ----

    // Her target if within 30 yd and in sight, else a random player on the arena that is; nobody: the beat passes.
    bool CastFrostbolt()
    {
        Unit* target = me->GetVictim();
        if (!target || me->GetDistance(target) > Tune::kFrostboltRangeYd || !me->IsWithinLOSInMap(target))
        {
            target = nullptr;
            if (PoolEncounter* fight = Fight())
            {
                std::vector<Player*> near;
                for (Player* player : fight->FightPlayers())
                    if (me->GetDistance(player) <= Tune::kFrostboltRangeYd && me->IsWithinLOSInMap(player))
                        near.push_back(player);
                if (!near.empty())
                    target = Acore::Containers::SelectRandomContainerElement(near);
            }
        }
        if (!target)
            return true;
        return me->CastSpell(target, SPELL_FROSTBOLT, false) == SPELL_CAST_OK;
    }

    // ---- GZ10 the gong ----

    void StartGongRun()
    {
        _run = true;
        _runMs = 0;
        if (me->IsNonMeleeSpellCast(false))
            me->InterruptNonMeleeSpells(false);
        Talk(YELL_VELRATHA_GONG);
        me->SetCombatMovement(false);
        Position const spot = GongSpot();
        me->GetMotionMaster()->MovePoint(kMovePointGong, spot);
        LogGz("gong-run", Acore::StringFormat("health={:.1f} from=({:.1f}, {:.1f}) walk={:.1f}", me->GetHealthPct(),
            me->GetPositionX(), me->GetPositionY(), me->GetExactDist2d(spot.GetPositionX(), spot.GetPositionY())));
    }

    // She strikes the gong where she stands (at the gong, or where the run's timeout found her), then fights on there.
    void Strike(char const* how)
    {
        _run = false;
        _struck = true;
        _lethal.Disarm();
        me->StopMoving();
        me->SetCombatMovement(false);
        Map* map = me->GetMap();
        GameObject* gong = (instance && map) ? map->GetGameObject(instance->GetGuidData(kGuidGong)) : nullptr;
        if (gong)
        {
            me->SetFacingToObject(gong);
            gong->SendCustomAnim(0);
        }
        me->CastSpell(me, SPELL_GZ_GONG_STRIKE, true);
        if (instance)
            instance->SetData(DATA_GONG_STRUCK, 1);
        bool const armed = instance && instance->GetData(DATA_HARD_MODE);
        Creature* gahzrilla = (instance && map) ? map->GetCreature(instance->GetGuidData(kGuidGahzrilla)) : nullptr;
        if (gahzrilla && !gahzrilla->IsAlive())
            gahzrilla = nullptr;
        if (PoolEncounter* fight = Fight())
            fight->GongStruck(gahzrilla, armed);
        if (gahzrilla && gahzrilla->IsAIEnabled)
            gahzrilla->AI()->SetGUID(_keeper, kSetGuidKeeper);
        if (_hardMode && !armed)
            _hardMode = false;
        LogGz("gong", Acore::StringFormat("how={} health={:.1f} gahzrilla={} hardmode={} at=({:.1f}, {:.1f})", how,
            me->GetHealthPct(), gahzrilla ? 1 : 0, armed ? 1 : 0, me->GetPositionX(), me->GetPositionY()));
    }

    void Cleanup()
    {
        _engaged = false;
        _clock.Stop();
        _run = false;
        _runMs = 0;
        _struck = false;
        _lethal.Reset();
        if (me->IsNonMeleeSpellCast(false))
            me->InterruptNonMeleeSpells(false);
        me->SetCombatMovement(true);
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::LethalGuard _lethal;
    VelrathaClock _clock;
    ObjectGuid _keeper;
    uint32 _baseHealth = 0;
    uint32 _runMs = 0;
    bool _heroic = false;
    bool _hardMode = false;
    bool _engaged = false;
    bool _run = false;
    bool _struck = false;
};

// ---------------------------------------------------------------------------------------------------------------------
// Gahz'rilla 7273 (slot 1): summoned by the instance at Velratha's strike
// ---------------------------------------------------------------------------------------------------------------------

struct boss_gahzrilla_rework : public BossAI
{
    explicit boss_gahzrilla_rework(Creature* creature)
        : BossAI(creature, BOSS_GAHZRILLA), _arena(PoolArena(), LeashOptions(kLogKey)) { }

    void Reset() override
    {
        _Reset();
        Cleanup();
        if (!_riseStarted)
            BeginRise();
    }

    void SetGUID(ObjectGuid const& guid, int32 id) override
    {
        if (id == kSetGuidKeeper)
            _keeper = guid;
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        Cleanup();
        _heroic = IsHeroicMap(me);
        InstanceScript const* script = me->GetInstanceScript();
        _hardMode = _heroic && script && script->GetData(DATA_HARD_MODE);
        if (_hardMode)
            SetCreatureHealth(me, Health::kHardModeGahzrilla);       // section 3.7: 500,000 as he comes ashore
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_GAHZRILLA;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);
        _engaged = true;
        _clock.Start(_heroic);
        PoolEncounter* fight = Fight();
        if (!fight)
        {
            // Ashore without Velratha's encounter (a GM's summon, a reload): his own stalker, no hard mode objects.
            auto [guid, fresh] = SummonKeeper(me);
            _keeper = guid;
            fight = fresh;
            if (fight)
                fight->Begin(nullptr, _heroic, false);
        }
        if (fight)
            fight->GahzrillaArrived(me);
        Describe();
        OnBossPull(me, kLogKey, _hardMode);
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        if (_engaged)
            LogGz("gahzrilla-evade", Acore::StringFormat("reason={} clock={}s", uint32(why), _clock.Now() / 1000));
        if (PoolEncounter* fight = Fight())
        {
            if (Creature* velratha = fight->Velratha(); velratha && velratha->IsAlive() && velratha->IsEngaged()
                && velratha->IsAIEnabled)
                velratha->AI()->EnterEvadeMode(why);
            fight->End(false, "gahzrilla-evade");
        }
        Cleanup();
        BossAI::EnterEvadeMode(why);
        // Section 7 #43 h A: the instance brings Velratha back; the next strike summons a new Gahz'rilla.
        me->DespawnOrUnsummon(1s);
    }

    void JustDied(Unit* killer) override
    {
        LogGz("gahzrilla-death", Acore::StringFormat("clock={}s discharges={} hardmode={} killer={}",
            _clock.Now() / 1000, _clock.Landed(), _hardMode ? 1 : 0, killer ? killer->GetName() : "none"));
        if (PoolEncounter* fight = Fight())
            fight->End(true, "gahzrilla-death");
        Cleanup();
        BossAI::JustDied(killer);
    }

    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type != POINT_MOTION_TYPE)
            return;
        if (id == kMovePointAshore && _rising)
            Arrive("ashore");
        else if (id == kMovePointPin && _pin)
            _pinReached = true;
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*mask*/) override
    {
        if (!_engaged)
            return;
        if (PoolEncounter* fight = Fight())
            fight->GahzrillaDamaged(attacker, damage);
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        BossAI::OnSpellCast(spell);
        if (!spell || !_engaged)
            return;
        PoolEncounter* fight = Fight();
        switch (spell->Id)
        {
            case SPELL_GZ_CALL_THE_WATERS:
            case SPELL_GZ_CALL_THE_WATERS_HEROIC:
                if (fight)
                    fight->CallTheWaters(me, true);
                break;
            case SPELL_GZ_ICICLE:
            case SPELL_GZ_FREEZE_SOLID:
            {
                FreezeKind const kind = spell->Id == SPELL_GZ_ICICLE ? FreezeKind::Icicle : FreezeKind::FreezeSolid;
                Unit* target = ObjectAccessor::GetUnit(*me, _frostTarget);
                if (fight && target)
                    fight->Freeze(kind, target, target->GetPosition());
                if (target)
                    LogGz(kind == FreezeKind::Icicle ? "icicle-land" : "freeze-solid-land",
                        Acore::StringFormat("target={} at=({:.1f}, {:.1f})", target->GetName(),
                            target->GetPositionX(), target->GetPositionY()));
                _frostTarget.Clear();
                break;
            }
            default:
                break;
        }
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (!spell || !_engaged)
            return;
        switch (spell->Id)
        {
            case SPELL_GZ_CALL_THE_WATERS:
            case SPELL_GZ_CALL_THE_WATERS_HEROIC:
                LogGz("call-stopped");
                if (PoolEncounter* fight = Fight())
                    fight->CallTheWaters(me, false);
                break;
            case SPELL_GZ_ICICLE:
            case SPELL_GZ_FREEZE_SOLID:
                LogGz(spell->Id == SPELL_GZ_ICICLE ? "icicle-stopped" : "freeze-solid-stopped");
                _frostTarget.Clear();
                break;
            case SPELL_GZ_DISCHARGE_BAR:
                // Never kickable; the landing is the clock's (Storm Builds), so it lands anyway.
                LogGz("discharge-bar-stopped", "lands on time anyway");
                break;
            default:
                break;
        }
    }

    void UpdateAI(uint32 diff) override
    {
        ZulFarrak::NoAssist(me);        // rule 27, LESSONS L1: every tick, before UpdateVictim
        if (_rising)
        {
            _riseMs += diff;
            if (_riseMs >= Tune::kRiseTimeoutMs)
            {
                me->NearTeleportTo(kGahzrillaAshore.x, kGahzrillaAshore.y, kGahzrillaAshore.z, me->GetOrientation());
                Arrive("timeout");
            }
            return;
        }
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_engaged)
            return;

        _clock.Advance(diff);
        if (_clock.BarRunning() && _clock.Now() >= _clock.LandsAt())
            Land();
        UpdateMeter();
        if (PoolEncounter* fight = Fight())
            fight->NoteStorm(_clock.Landed(), _clock.LandsAt() > _clock.Now() ? _clock.LandsAt() - _clock.Now() : 0);
        UpdatePin();
        if (!me->IsAlive() || me->HasUnitState(UNIT_STATE_CASTING))
            return;

        GAct const act = _clock.Next();
        if (act != GAct::None)
        {
            if (Begin(act))
            {
                if (act != GAct::Discharge)
                    _clock.Done(act, act == GAct::Slam ? urand(Tune::kSlamEveryMinMs, Tune::kSlamEveryMaxMs) : 0);
            }
            else
                _clock.Retry(act);
            if (me->HasUnitState(UNIT_STATE_CASTING))
                return;
        }
        SwingOrSpit();
    }

    // ---- shared with the encounter and `.dbtest` --------------------------------------------------------------------

    PoolEncounter* Fight() { return FightOf(me->GetMap(), _keeper); }
    ObjectGuid KeeperGuid() const { return _keeper; }

    void Describe()
    {
        BossMechanics::Descriptor d;
        uint32 const call = _heroic ? SPELL_GZ_CALL_THE_WATERS_HEROIC : SPELL_GZ_CALL_THE_WATERS;
        d.interrupts.emplace_back(NPC_GAHZRILLA, call, kCallKickPriority, Ms(Tune::kCallEveryMs(_heroic)));
        if (_heroic)
            d.dispels.emplace_back(SPELL_GZ_CONDUCTIVE, kConductiveDispelPriority);
        d.dispels.emplace_back(SPELL_GZ_FREEZE_SOLID, kFreezeSolidDispelPriority, true);
        d.dispels.emplace_back(SPELL_FROSTBOLT, kFrostboltDispelPriority);
        d.targets.emplace_back(NPC_VELRATHA, 2);
        d.targets.emplace_back(NPC_GAHZRILLA, 1);
        if (PoolEncounter* fight = Fight())
            fight->DescribeExtra(me, d);
        Mechanic::Describe(me, std::move(d));
        Mechanic::NoteNextCastIn(me, call, Ms(_clock.In(GAct::CallTheWaters)));
    }

    void Pin(std::optional<Position> spot)
    {
        _pin = spot;
        _pinReached = false;
        if (!spot)
        {
            me->SetCombatMovement(true);
            if (Unit* victim = me->GetVictim())
                me->GetMotionMaster()->MoveChase(victim);
        }
        LogGz("pin", spot ? Acore::StringFormat("at=({:.1f}, {:.1f}, {:.1f})", spot->GetPositionX(),
            spot->GetPositionY(), spot->GetPositionZ()) : std::string("released"));
    }

    void SetIcicleEvery(uint32 everyMs)
    {
        _clock.SetIcicleEvery(everyMs);
        LogGz("icicle-pace", Acore::StringFormat("every={}ms", _clock.IcicleEvery()));
    }

    enum class TestMechanic : uint8
    {
        Discharge,
        Call,
        Icicle,
        FreezeSolid,
        Slam,
    };

    std::string TestFire(TestMechanic mechanic, Player* who)
    {
        if (!_engaged || !me->IsEngaged())
            return "Gahz'rilla must be in combat (ashore and fighting).";
        if (me->HasUnitState(UNIT_STATE_CASTING) || _clock.BarRunning())
            return "He is casting already.";
        Player* forced = CountsAsPlayer(who) ? who : nullptr;
        bool ok = true;
        switch (mechanic)
        {
            case TestMechanic::Discharge:
                StartBar();
                break;
            case TestMechanic::Call:
                ok = CastCall();
                break;
            case TestMechanic::Icicle:
                ok = CastFrost(FreezeKind::Icicle, forced);
                break;
            case TestMechanic::FreezeSolid:
                ok = CastFrost(FreezeKind::FreezeSolid, forced);
                break;
            case TestMechanic::Slam:
                ok = CastSlam();
                break;
        }
        return ok ? std::string() : std::string("The engine refused it (a lockout?).");
    }

    std::string TestState()
    {
        return Acore::StringFormat("clock={}s heroic={} hardmode={} health={:.1f} cycle={} landed={} bar-in={}ms "
            "stacks={} pin={} next: call {} ms, icicle {} ms (every {}), freeze {} ms, slam {} ms",
            _clock.Now() / 1000, _heroic ? 1 : 0, _hardMode ? 1 : 0, me->GetHealthPct(), _clock.Cycle(),
            _clock.Landed(), _clock.In(GAct::Discharge), _clock.Stacks(), _pin ? 1 : 0,
            _clock.In(GAct::CallTheWaters), _clock.In(GAct::Icicle), _clock.IcicleEvery(),
            _clock.In(GAct::FreezeSolid), _clock.In(GAct::Slam));
    }

private:
    // ---- The rise (GZ10, section 7 #35 A) ----

    void BeginRise()
    {
        _riseStarted = true;
        _rising = true;
        _riseMs = 0;
        me->SetReactState(REACT_PASSIVE);
        me->SetImmuneToAll(true);
        me->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->GetMotionMaster()->MovePoint(kMovePointAshore,
            Position(kGahzrillaAshore.x, kGahzrillaAshore.y, kGahzrillaAshore.z, kGahzrillaAshore.o));
        LogGz("rise", Acore::StringFormat("from=({:.1f}, {:.1f}, {:.1f})", me->GetPositionX(), me->GetPositionY(),
            me->GetPositionZ()));
    }

    // Ashore: attackable, and he fights Velratha's target first, else the nearest player on the arena (rule 19).
    void Arrive(char const* how)
    {
        _rising = false;
        me->SetImmuneToAll(false);
        me->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->SetReactState(REACT_AGGRESSIVE);
        Unit* target = nullptr;
        if (PoolEncounter* fight = Fight())
        {
            if (Creature* velratha = fight->Velratha(); velratha && velratha->IsAlive())
                if (Unit* victim = velratha->GetVictim(); victim && victim->IsAlive() && _arena.Contains(victim))
                    target = victim;
            if (!target)
            {
                float best = 0.f;
                for (Player* player : fight->FightPlayers())
                {
                    float const d = me->GetExactDist(player);
                    if (!target || d < best)
                    {
                        target = player;
                        best = d;
                    }
                }
            }
        }
        LogGz("ashore", Acore::StringFormat("how={} target={} at=({:.1f}, {:.1f}, {:.1f})", how,
            target ? target->GetName() : "none", me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
        if (target)
            AttackStart(target);
    }

    // ---- GZ3 Static Discharge ----

    void UpdateMeter()
    {
        uint32 const want = _clock.BarRunning() ? Tune::kStaticChargeMax : _clock.Stacks();
        uint32 const have = DungeonKit::Stacks(me, SPELL_GZ_STATIC_CHARGE);
        if (want != have)
            DungeonKit::AddStacks(me, SPELL_GZ_STATIC_CHARGE, int32(want) - int32(have), me, Tune::kStaticChargeMax);
    }

    void StartBar()
    {
        me->StopMoving();
        DungeonKit::CastBar(me, SPELL_GZ_DISCHARGE_BAR, nullptr, EMOTE_GAHZRILLA_CHARGE);
        _clock.BarStarted();
        if (PoolEncounter* fight = Fight())
            fight->DischargeBar();
        LogGz("discharge", Acore::StringFormat("n={} clock={}ms lands={}ms late={}ms", _clock.Cycle(), _clock.Now(),
            _clock.LandsAt(), _clock.Now() > _clock.BarAt() ? _clock.Now() - _clock.BarAt() : 0));
    }

    void Land()
    {
        _clock.MarkLanded();
        if (PoolEncounter* fight = Fight())
            fight->DischargeLand(me);
    }

    bool Begin(GAct act)
    {
        switch (act)
        {
            case GAct::Discharge:
                StartBar();
                return true;
            case GAct::CallTheWaters:
                return CastCall();
            case GAct::Icicle:
                return CastFrost(FreezeKind::Icicle, nullptr);
            case GAct::FreezeSolid:
                return CastFrost(FreezeKind::FreezeSolid, nullptr);
            case GAct::Slam:
                return CastSlam();
            case GAct::None:
                break;
        }
        return true;
    }

    // ---- GZ5 Call the Waters ----

    bool CastCall()
    {
        uint32 const spell = _heroic ? SPELL_GZ_CALL_THE_WATERS_HEROIC : SPELL_GZ_CALL_THE_WATERS;
        me->StopMoving();
        SpellCastResult const result = me->CastSpell(me, spell, false);
        if (result != SPELL_CAST_OK)
        {
            LogGz("call-refused", Acore::StringFormat("result={}", uint32(result)));
            return false;
        }
        LogGz("call", Acore::StringFormat("cast={}ms", Tune::kCallCastMs(_heroic)));
        Mechanic::NoteNextCastIn(me, spell, Ms(Tune::kCallEveryMs(_heroic)));
        return true;
    }

    // ---- GZ6 Icicle, GZ7 Freeze Solid ----

    // A random player on the arena within range and sight, the tank included.
    Player* FrostTarget(float rangeYd)
    {
        PoolEncounter* fight = Fight();
        if (!fight)
            return nullptr;
        std::vector<Player*> pool;
        for (Player* player : fight->FightPlayers())
            if (me->GetDistance(player) <= rangeYd && me->IsWithinLOSInMap(player))
                pool.push_back(player);
        return pool.empty() ? nullptr : Acore::Containers::SelectRandomContainerElement(pool);
    }

    // The target's bot steps into the water it baits (GZ6: a water puddle; GZ7: within reach of puddles).
    void RegisterBait(FreezeKind kind, Player* target, uint32 castMs)
    {
        PoolEncounter* fight = Fight();
        if (!fight)
            return;
        DungeonKit::ImpactSpec impact;
        impact.pct = 0.f;
        impact.weakened = false;
        impact.tag = TAG_GZ_ICICLE_DROP;
        MechanicRef bait = DungeonKit::FollowThenLand(me, target, 1.f, Ms(castMs), impact);
        BossMechanics::DropSpotRule rule;
        uint32 offered = 0;
        DungeonKit::WaterField& water = fight->Water();
        for (DungeonKit::WaterSheet const& s : water.All())
        {
            if (!s.IsWater() || s.IsStrip() || !s.rules.canFreeze)
                continue;
            Position const center(s.center.x, s.center.y, s.z);
            if (kind == FreezeKind::Icicle)
                rule.Prefer(center, std::max(1.f, s.radius - 1.f), water.AvoidZoneOf(s.id).id);
            else
                rule.Prefer(center, s.radius + Tune::kFreezeSolidReachYd - 1.f);
            ++offered;
        }
        if (offered)
        {
            rule.MaxDwell(Ms(Tune::kBaitMaxDwellMs));
            rule.bounds = PoolFloorBounds();
            bait.DropSpot(rule);
        }
        fight->Track(bait.Handle());
    }

    bool CastFrost(FreezeKind kind, Player* forced)
    {
        bool const icicle = kind == FreezeKind::Icicle;
        Player* target = forced ? forced : FrostTarget(icicle ? Tune::kIcicleRangeYd : Tune::kFreezeSolidRangeYd);
        if (!target)
            return true;        // nobody in range: the beat passes
        uint32 const spell = icicle ? SPELL_GZ_ICICLE : SPELL_GZ_FREEZE_SOLID;
        uint32 const castMs = icicle ? Tune::kIcicleCastMs : Tune::kFreezeSolidCastMs;
        int32 const amount = !_heroic
            ? int32(icicle ? urand(Tune::kIcicleMinDamage, Tune::kIcicleMaxDamage) : Tune::kFreezeSolidDamage)
            : int32(DungeonKit::RefFlatOn(me, target, icicle ? Tune::kIcicleHeroicPct : Tune::kFreezeSolidHeroicPct));
        CastSpellExtraArgs args(TRIGGERED_NONE);
        args.AddSpellBP0(amount);
        me->StopMoving();
        SpellCastResult const result = me->CastSpell(target, spell, args);
        if (result != SPELL_CAST_OK)
        {
            LogGz(icicle ? "icicle-refused" : "freeze-solid-refused", Acore::StringFormat("result={}", uint32(result)));
            return false;
        }
        _frostTarget = target->GetGUID();
        RegisterBait(kind, target, castMs);
        if (icicle)
            if (PoolEncounter* fight = Fight())
                fight->SetBait(target->GetGUID(), castMs);
        LogGz(icicle ? "icicle" : "freeze-solid", Acore::StringFormat("target={} tank={} amount={}",
            target->GetName(), target == me->GetVictim() ? 1 : 0, amount));
        return true;
    }

    // ---- GZ11 Slam and Acid Spit ----

    bool CastSlam()
    {
        if (me->CastSpell(me, SPELL_GZ_SLAM, false) != SPELL_CAST_OK)
            return false;
        LogGz("slam");
        return true;
    }

    // His swing: melee in reach; a target out of reach (kited, or past the pool's edge in the Deluge) takes an Acid
    // Spit of 150% of the swing as Nature instead.
    void SwingOrSpit()
    {
        Unit* victim = me->GetVictim();
        if (!victim)
            return;
        if (me->IsWithinMeleeRange(victim))
        {
            DoMeleeAttackIfReady();
            return;
        }
        if (!me->isAttackReady() || me->GetDistance(victim) > Tune::kAcidSpitRangeYd || !me->IsWithinLOSInMap(victim))
            return;
        uint32 const amount = static_cast<uint32>(static_cast<float>(me->CalculateDamage(BASE_ATTACK, false, true))
            * Tune::kAcidSpitMeleePct / 100.f);
        CastSpellExtraArgs args(TRIGGERED_FULL_MASK);
        args.AddSpellBP0(static_cast<int32>(amount));
        me->CastSpell(victim, SPELL_GZ_ACID_SPIT, args);
        me->resetAttackTimer();
        ++_spits;
        if (_spits == 1 || _spits % 10 == 0)
            LogGz("acid-spit", Acore::StringFormat("target={} amount={} count={}", victim->GetName(), amount, _spits));
    }

    // GZ22 (D7Hb): he stands at the pin and fights from there.
    void UpdatePin()
    {
        if (!_pin)
            return;
        me->SetCombatMovement(false);
        if (_pinReached || me->GetExactDist2d(_pin->GetPositionX(), _pin->GetPositionY()) <= kPinReachedYd)
        {
            _pinReached = true;
            return;
        }
        if (!me->isMoving())
            me->GetMotionMaster()->MovePoint(kMovePointPin, *_pin);
    }

    void Cleanup()
    {
        _engaged = false;
        _clock.Stop();
        _frostTarget.Clear();
        _pin.reset();
        _pinReached = false;
        _spits = 0;
        me->RemoveAurasDueToSpell(SPELL_GZ_STATIC_CHARGE);
        if (me->IsNonMeleeSpellCast(false))
            me->InterruptNonMeleeSpells(false);
        me->SetCombatMovement(true);
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    GahzrillaClock _clock;
    ObjectGuid _keeper;
    ObjectGuid _frostTarget;
    std::optional<Position> _pin;
    uint32 _riseMs = 0;
    uint32 _spits = 0;
    bool _riseStarted = false;
    bool _rising = false;
    bool _pinReached = false;
    bool _heroic = false;
    bool _hardMode = false;
    bool _engaged = false;
};

namespace
{
    void DescribeBoss(Creature* boss)
    {
        if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
            return;
        if (auto* velratha = dynamic_cast<boss_velratha_rework*>(boss->AI()))
            velratha->Describe();
        else if (auto* gahzrilla = dynamic_cast<boss_gahzrilla_rework*>(boss->AI()))
            gahzrilla->Describe();
    }

    void PinGahzrillaAI(Creature* gahzrilla, std::optional<Position> spot)
    {
        if (gahzrilla && gahzrilla->IsAIEnabled)
            if (auto* ai = dynamic_cast<boss_gahzrilla_rework*>(gahzrilla->AI()))
                ai->Pin(spot);
    }

    void IcicleEveryAI(Creature* gahzrilla, uint32 everyMs)
    {
        if (gahzrilla && gahzrilla->IsAIEnabled)
            if (auto* ai = dynamic_cast<boss_gahzrilla_rework*>(gahzrilla->AI()))
                ai->SetIcicleEvery(everyMs);
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// PoolFight.h's registry
// ---------------------------------------------------------------------------------------------------------------------

namespace ZfPool
{
    void RegisterPoolHardMode(PoolPackage package, PoolHardModeFactory factory)
    {
        std::size_t const i = static_cast<std::size_t>(package);
        if (i < Factories().size())
            Factories()[i] = std::move(factory);
    }

    std::vector<std::unique_ptr<PoolHardMode>> CreatePoolHardModes(PoolFight& fight)
    {
        std::vector<std::unique_ptr<PoolHardMode>> out;
        for (PoolHardModeFactory const& factory : Factories())
            if (factory)
                if (std::unique_ptr<PoolHardMode> hm = factory(fight))
                    out.push_back(std::move(hm));
        return out;
    }

    PoolFight* FindPoolFight(Map* map)
    {
        InstanceMap* instanceMap = map ? map->ToInstanceMap() : nullptr;
        InstanceScript* script = instanceMap ? instanceMap->GetInstanceScript() : nullptr;
        if (!script || map->GetId() != kMapZulFarrak)
            return nullptr;
        for (uint32 const data : { kGuidBossBase + BOSS_VELRATHA, kGuidGahzrilla })
        {
            Creature* boss = map->GetCreature(script->GetGuidData(data));
            if (!boss || !boss->IsAIEnabled)
                continue;
            ObjectGuid keeper;
            if (auto* velratha = dynamic_cast<boss_velratha_rework*>(boss->AI()))
                keeper = velratha->KeeperGuid();
            else if (auto* gahzrilla = dynamic_cast<boss_gahzrilla_rework*>(boss->AI()))
                keeper = gahzrilla->KeeperGuid();
            if (PoolEncounter* fight = FightOf(map, keeper))
                return fight;
        }
        return nullptr;
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// `.dbtest zf pool <subcommand>`
// ---------------------------------------------------------------------------------------------------------------------

namespace
{
    template <typename AI>
    AI* FindAI(ChatHandler* handler, uint32 entry, char const* name)
    {
        Creature* boss = ZfTest::FindBoss(handler, entry);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<AI*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{} is not running its rework script (check the ScriptName).", name);
        return ai;
    }

    Player* Selected(ChatHandler* handler)
    {
        return handler->GetSession() ? handler->getSelectedPlayerOrSelf() : nullptr;
    }

    bool Fired(ChatHandler* handler, std::string const& error, char const* what)
    {
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("The pool: {} fired.", what);
        return true;
    }

    bool FireVelratha(ChatHandler* handler, boss_velratha_rework::TestMechanic mechanic, char const* what)
    {
        auto* ai = FindAI<boss_velratha_rework>(handler, NPC_VELRATHA, "Velratha");
        return ai && Fired(handler, ai->TestFire(mechanic, Selected(handler)), what);
    }

    bool FireGahzrilla(ChatHandler* handler, boss_gahzrilla_rework::TestMechanic mechanic, char const* what)
    {
        auto* ai = FindAI<boss_gahzrilla_rework>(handler, NPC_GAHZRILLA, "Gahz'rilla");
        return ai && Fired(handler, ai->TestFire(mechanic, Selected(handler)), what);
    }

    PoolEncounter* GmFight(ChatHandler* handler)
    {
        Player* gm = handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
        if (!gm || !ZfTest::RequireZulFarrak(handler))
            return nullptr;
        auto* fight = static_cast<PoolEncounter*>(FindPoolFight(gm->GetMap()));
        if (!fight)
            handler->SendErrorMessage("{}", "No pool encounter is running (pull Velratha first).");
        return fight;
    }

    bool HandleInfoVelratha(ChatHandler* handler)
    {
        return ZfTest::ShowBossInfo(handler, NPC_VELRATHA, BOSS_VELRATHA);
    }

    bool HandleInfoGahzrilla(ChatHandler* handler)
    {
        return ZfTest::ShowBossInfo(handler, NPC_GAHZRILLA, BOSS_GAHZRILLA);
    }

    bool HandleState(ChatHandler* handler)
    {
        PoolEncounter* fight = GmFight(handler);
        if (!fight)
            return false;
        handler->PSendSysMessage("The pool: {}", fight->State());
        if (Creature* velratha = fight->Velratha(); velratha && velratha->IsAIEnabled)
            if (auto* ai = dynamic_cast<boss_velratha_rework*>(velratha->AI()))
                handler->PSendSysMessage("Velratha: {}", ai->TestState());
        if (Creature* gahzrilla = fight->Gahzrilla(); gahzrilla && gahzrilla->IsAIEnabled)
            if (auto* ai = dynamic_cast<boss_gahzrilla_rework*>(gahzrilla->AI()))
                handler->PSendSysMessage("Gahz'rilla: {}", ai->TestState());
        return true;
    }

    bool HandleGong(ChatHandler* handler)
    {
        return FireVelratha(handler, boss_velratha_rework::TestMechanic::Gong,
            "Velratha's run to the gong (GZ10; the strike summons Gahz'rilla)");
    }

    bool HandleSpill(ChatHandler* handler)
    {
        return FireVelratha(handler, boss_velratha_rework::TestMechanic::Spill,
            "Spill the Pool (GZ1: the selected player, else random)");
    }

    bool HandleHeal(ChatHandler* handler)
    {
        return FireVelratha(handler, boss_velratha_rework::TestMechanic::Heal, "Healing Wave (GZ9, kickable)");
    }

    bool HandleDischarge(ChatHandler* handler)
    {
        return FireGahzrilla(handler, boss_gahzrilla_rework::TestMechanic::Discharge,
            "Static Discharge (GZ3: lands at the clock's next landing)");
    }

    bool HandleCall(ChatHandler* handler)
    {
        return FireGahzrilla(handler, boss_gahzrilla_rework::TestMechanic::Call, "Call the Waters (GZ5, kickable)");
    }

    bool HandleIcicle(ChatHandler* handler)
    {
        return FireGahzrilla(handler, boss_gahzrilla_rework::TestMechanic::Icicle,
            "Icicle (GZ6: the selected player, else random)");
    }

    bool HandleFreeze(ChatHandler* handler)
    {
        return FireGahzrilla(handler, boss_gahzrilla_rework::TestMechanic::FreezeSolid,
            "Freeze Solid (GZ7: the selected player, else random)");
    }

    bool HandleSlam(ChatHandler* handler)
    {
        return FireGahzrilla(handler, boss_gahzrilla_rework::TestMechanic::Slam, "the Slam (GZ11)");
    }

    bool HandlePuddle(ChatHandler* handler, Optional<uint32> radius)
    {
        PoolEncounter* fight = GmFight(handler);
        if (!fight)
            return false;
        Player* gm = handler->GetSession()->GetPlayer();
        uint32 const id = fight->AddPuddle(gm->GetPosition(), radius ? float(*radius) : Tune::kPuddleRadiusYd,
            SHEET_GM, "gm");
        if (!id)
        {
            handler->SendErrorMessage("{}", "The water field refused it.");
            return false;
        }
        handler->PSendSysMessage("The pool: puddle {} at your feet.", id);
        return true;
    }

    bool HandleCharged(ChatHandler* handler, Optional<uint32> stacks)
    {
        PoolEncounter* fight = GmFight(handler);
        Player* who = Selected(handler);
        if (!fight || !who)
            return false;
        uint32 const want = stacks.value_or(10);
        uint32 const now = fight->AddCharged(who, int32(want) - int32(fight->Charged(who)));
        handler->PSendSysMessage("The pool: {} carries {} Charged.", who->GetName(), now);
        return true;
    }

    bool HandleConductive(ChatHandler* handler)
    {
        PoolEncounter* fight = GmFight(handler);
        Player* who = Selected(handler);
        if (!fight || !who)
            return false;
        if (!fight->ApplyConductive(who))
        {
            handler->SendErrorMessage("{}", "Conductive did not land.");
            return false;
        }
        handler->PSendSysMessage("The pool: Conductive on {}.", who->GetName());
        return true;
    }

    bool HandleThaw(ChatHandler* handler)
    {
        PoolEncounter* fight = GmFight(handler);
        if (!fight)
            return false;
        handler->PSendSysMessage("The pool: {} ice sheets thawed.", fight->ThawAll());
        return true;
    }

    // `.dbtest zf pool <sub>`: the numbers are the map's difficulty.
    ChatCommandTable const& PoolTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "velratha",   HandleInfoVelratha,  SEC_GAMEMASTER, Console::No },
            { "gahzrilla",  HandleInfoGahzrilla, SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,         SEC_GAMEMASTER, Console::No },
            { "gong",       HandleGong,          SEC_GAMEMASTER, Console::No },
            { "spill",      HandleSpill,         SEC_GAMEMASTER, Console::No },
            { "heal",       HandleHeal,          SEC_GAMEMASTER, Console::No },
            { "discharge",  HandleDischarge,     SEC_GAMEMASTER, Console::No },
            { "call",       HandleCall,          SEC_GAMEMASTER, Console::No },
            { "icicle",     HandleIcicle,        SEC_GAMEMASTER, Console::No },
            { "freeze",     HandleFreeze,        SEC_GAMEMASTER, Console::No },
            { "slam",       HandleSlam,          SEC_GAMEMASTER, Console::No },
            { "puddle",     HandlePuddle,        SEC_GAMEMASTER, Console::No },
            { "charged",    HandleCharged,       SEC_GAMEMASTER, Console::No },
            { "conductive", HandleConductive,    SEC_GAMEMASTER, Console::No },
            { "thaw",       HandleThaw,          SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_gahzrilla_rework()
{
    RegisterDungeonReworkCreatureAI(boss_velratha_rework, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(boss_gahzrilla_rework, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_zf_puddle, ZulFarrakRework::kInstanceScriptName);
    ZfTest::RegisterBoss("pool", PoolTestCommands());
}
