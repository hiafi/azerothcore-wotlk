/*
 * mod-dungeon-bosses, Zul'Farrak D7: the pool's hooks (engine side) for the hard mode packages D7Ha (the crew at the
 * pool, GZ15-GZ21) and D7Hb (the Deluge, GZ22-GZ24). Owned by WP-D7; D7Ha and D7Hb never edit D7's .cpp
 * (boss_gahzrilla_rework.cpp) and share only this file. Pure rules and numbers: GahzrillaLogic.h.
 *
 * One encounter, three units. Velratha (slot 0) fights phase 1; at her 30% she strikes the gong and the instance
 * summons Gahz'rilla (slot 1), who walks ashore and fights phase 2; she dies during his rise. Neither boss lives
 * through the whole encounter, so the encounter's state is held by a third unit: **the sacred pool's stalker** (entry
 * 301030, npc_zf_puddle, the same invisible stalker template as the water discs), summoned at the pool's middle at
 * Velratha's pull and despawned at the encounter's end. Its AI holds the PoolFight below: the water field (it owns
 * every water zone and disc, so a boss's death never drops the water), the clock, Charged, Conductive and the hard
 * mode objects. The bosses drive their own casts and call into it.
 *
 *   PoolFight          what D7 offers the hard mode, valid from Velratha's pull to the encounter's end (passed to
 *                      every hook). Find it from anywhere with ZfPool::FindPoolFight(map) (the add AIs, `.dbtest`).
 *   PoolHardMode       one hard mode package's per-pull object. A package registers a factory once, from its AddSC_:
 *                          ZfPool::RegisterPoolHardMode(ZfPool::PoolPackage::Crew,
 *                              [](ZfPool::PoolFight& fight) { return std::make_unique<X>(fight); });
 *                      At Velratha's pull, on heroic with the hard mode flag or its key (DATA_HARD_MODE ||
 *                      DATA_HARD_MODE_KEY: S0 Q3, her 200,000 is set then), D7 asks every registered factory for one
 *                      (Crew first, then Deluge) and calls their hooks in that order; with neither, none is made
 *                      (the pull is plain heroic, logged). At the gong, if the flag did not arm (a crew member died
 *                      during her phase: the key is gone), every object gets OnGongStruck(false) and then
 *                      OnEnd(false) and is dropped: Gahz'rilla is plain heroic. Armed, Gahz'rilla's 500,000 is set as
 *                      he comes ashore.
 *
 * Hook order on a pull of the hard mode:
 *   Velratha's pull      D7's encounter, the pool strip, then OnEngage (each package), then the descriptors (D7's, then
 *                        DescribeExtra), then her pull line (so it logs the health D7 set).
 *   every pool tick      D7's clocks (thaw, Charged, Conductive), then OnUpdate.
 *   the gong             OnGongStruck(armed) right after the instance's summon; OnVelrathaDied when she dies.
 *   his arrival          his 500,000, his clock, then OnGahzrillaArrive, then the descriptors.
 *   a Discharge          OnDischargeBar at the bar's start (D7 has registered the water's zones); at its landing D7
 *                        hits the players (DischargeHit list), applies Static Shock and, on heroic, Conductive (to
 *                        everyone when a package's ConductiveOnEveryone says so), then OnDischargeLand, then Rising
 *                        Water. The crew's own hits are the package's (rule 29: NPC damage at the pool is script).
 *   Call the Waters      OnCallTheWaters(landed) after his own cast (landed: after D7's puddles). A second head's cast
 *                        that lands calls fight.LandCallTheWaters(caster) (the same puddles and growth).
 *   a freeze             OnFreeze first (each package in order; true: handled, D7 does nothing more: the Deluge adds a
 *                        floe itself); else D7's rules (Meltwater on heroic, the pool's shore spill).
 *   his damage           OnGahzrillaDamaged before D7 (D7Hb's 40%).
 *   the end              OnEnd(won) first in D7's cleanup (his death, a wipe, an evade), with the fight still usable;
 *                        then D7 clears the water, its handles, its summons, the players' auras, and the stalker.
 *
 * Everything a package changes (auras on players or the crew, the bosses' health, a pin) it undoes in OnEnd. Units it
 * summons come from Summon and handles go to Track: D7's cleanup takes both away (RB-1).
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_POOL_FIGHT_H
#define MOD_DUNGEON_BOSSES_ZF_POOL_FIGHT_H

#include "BossMechanics.h"
#include "Define.h"
#include "DungeonKitWater.h"
#include "ObjectGuid.h"
#include "Position.h"
#include "ZulFarrakKit.h"
#include "ZulFarrakRework.h"
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <vector>

class Creature;
class InstanceScript;
class Map;
class Player;
class Unit;
class WorldObject;

namespace ZfPool
{
    class PoolHardMode;

    enum class PoolPhase : uint8
    {
        Velratha = 1,       // phase 1: her pull to the gong (and her last 30% during his rise)
        Rise = 2,           // the gong struck, Gahz'rilla not ashore yet
        Gahzrilla = 3,      // phase 2: he fights
        Deluge = 4,         // the hard mode's phase 3 (D7Hb sets it with SetPhase)
    };

    enum class FreezeKind : uint8
    {
        Icicle,             // GZ6: the sheet the target stands in (KT: the nearest one)
        FreezeSolid,        // GZ7: every sheet whose edge is within 8 yd of the target
    };

    // One player of a Discharge's landing (GZ3): what D7 dealt.
    struct DischargeHit
    {
        ObjectGuid player;
        bool inWater = false;       // stunned (Static Shock) and, on heroic, Conductive
        uint32 charged = 0;         // the stacks the damage was raised by (heroic)
        float pct = 0.f;            // of the reference row (0: nothing, normal on dry ground)
    };

    // D7's encounter, as the hard mode sees it (valid from Velratha's pull to the encounter's end).
    class PoolFight
    {
    public:
        virtual ~PoolFight() = default;

        // The units. Velratha may be dead (her corpse) or gone; Gahz'rilla is nullptr before the gong.
        virtual Creature* Keeper() = 0;             // the pool's stalker: owner of the water's zones and discs
        virtual Creature* Velratha() = 0;
        virtual Creature* Gahzrilla() = 0;
        virtual InstanceScript* Instance() = 0;
        virtual bool Heroic() const = 0;
        // The hard mode objects live (heroic, the flag or the key at her pull, and the flag at the gong).
        virtual bool HardMode() const = 0;
        virtual PoolPhase Phase() const = 0;
        virtual void SetPhase(PoolPhase phase) = 0;     // D7Hb: Deluge (also Mechanic::SetPhase on Gahz'rilla)
        virtual uint64 ClockMs() const = 0;             // since Velratha's pull
        virtual uint64 GahzrillaClockMs() const = 0;    // since he came ashore (0 before)

        // The players of the fight: alive, in the world, not game masters, on the pool's arena (shore or water).
        virtual std::vector<Player*> FightPlayers() = 0;

        // ---- The water (KT's WaterField; every zone and disc is the stalker's) ----
        virtual DungeonKit::WaterField& Water() = 0;
        // A new puddle by D7's rules (8 yd unless `radius`, freezes, grows, thaws 45 / 30 s), its z on the floor;
        // `kind` is the SheetRules kind (GahzrillaLogic.h SheetKind; the packages use 10 and up). 0: refused.
        virtual uint32 AddPuddle(Position const& at, float radius, uint32 kind, char const* why) = 0;
        // Any sheet with the packages' own rules (a Wellspring, the Deluge sheet, a floe), its z as given.
        virtual uint32 AddSheet(Position const& at, float radius, DungeonKit::SheetRules const& rules,
            DungeonKit::SheetState state, char const* why) = 0;
        virtual bool IsWater(WorldObject const* o) const = 0;  // unfrozen water: a puddle or the pool (ice wins)
        virtual uint32 PoolSheet() const = 0;                   // the pool strip's sheet id

        // ---- The storm (GZ3) ----
        virtual uint32 DischargesLanded() const = 0;
        virtual uint64 NextDischargeInMs() const = 0;           // to the next landing (0: no clock yet)
        // GZ23: Icicle every `everyMs` from now on (0: the normal pace).
        virtual void SetIcicleEvery(uint32 everyMs) = 0;

        // ---- Charged and Conductive (GZ12, GZ14) ----
        virtual uint32 Charged(Unit const* unit) const = 0;
        // Stacks on any unit (a crew member too); returns the new count. No cap.
        virtual uint32 AddCharged(Unit* unit, int32 delta) = 0;
        // Conductive on `unit` (10 s, Magic) with D7's arcs every 2 s (players hit; a package arcs to its own NPCs).
        virtual bool ApplyConductive(Unit* unit) = 0;

        // ---- Gahz'rilla ----
        // GZ22: he walks to `spot` and fights from there (melee in reach, else Acid Spit); nullopt: he chases again.
        virtual void PinGahzrilla(std::optional<Position> spot) = 0;
        // A heal of `pct` percent of his maximum health (GZ21: a crew member eaten).
        virtual void HealGahzrilla(float pct) = 0;
        // GZ20: a second head's Call the Waters landed: D7's puddles under random players (and the heroic growth).
        virtual void LandCallTheWaters(Unit* caster, char const* why) = 0;

        // ---- Plumbing ----
        // A unit for the fight (manual despawn unless `despawnMs`), despawned by D7's cleanup. nullptr: refused.
        virtual Creature* Summon(uint32 entry, Position const& at, uint32 despawnMs = 0) = 0;
        // A registry handle cancelled with the fight.
        virtual void Track(BossMechanics::MechanicHandle handle) = 0;
        // Describe both bosses again (DescribeExtra included): a phase change, a crew member lost.
        virtual void RefreshDescriptors() = 0;
        // `percent` of the reference row (the tank row on the tank) with the fight's boss as the owner (rule 2).
        virtual uint32 RefFlatOn(Unit const* target, float pct) = 0;
        // One INFO line "zf-build pool <mechanic> <detail>".
        virtual void Log(char const* mechanic, std::string const& detail = {}) = 0;
    };

    // One hard mode package's object for one pull. Every hook has a do-nothing default.
    class PoolHardMode
    {
    public:
        virtual ~PoolHardMode() = default;

        virtual void OnEngage(PoolFight& /*fight*/) { }
        virtual void OnUpdate(PoolFight& /*fight*/, uint32 /*diff*/) { }
        // `armed`: DATA_HARD_MODE is set. Not armed: OnEnd(false) follows and the object is dropped.
        virtual void OnGongStruck(PoolFight& /*fight*/, bool /*armed*/) { }
        virtual void OnVelrathaDied(PoolFight& /*fight*/) { }
        virtual void OnGahzrillaArrive(PoolFight& /*fight*/) { }
        virtual void OnGahzrillaDamaged(PoolFight& /*fight*/, Unit* /*attacker*/, uint32& /*damage*/) { }
        virtual void OnDischargeBar(PoolFight& /*fight*/) { }
        virtual void OnDischargeLand(PoolFight& /*fight*/, std::vector<DischargeHit> const& /*players*/) { }
        // GZ19: every Discharge leaves Conductive on every player, not only those in water.
        virtual bool ConductiveOnEveryone(PoolFight const& /*fight*/) const { return false; }
        // His own Call the Waters: landed, or stopped (a kick).
        virtual void OnCallTheWaters(PoolFight& /*fight*/, bool /*landed*/) { }
        // A freeze landed at `at` on `target` (may be gone). True: handled (D7 adds no Meltwater, no shore spill).
        virtual bool OnFreeze(PoolFight& /*fight*/, FreezeKind /*kind*/, Unit* /*target*/, Position const& /*at*/,
            DungeonKit::FreezeResult& /*result*/)
        {
            return false;
        }
        // The encounter ends: his death (won), a wipe or an evade. Undo everything here.
        virtual void OnEnd(PoolFight& /*fight*/, bool /*won*/) { }

        // Extra entries for the bots' boss data of `boss` (Velratha or Gahz'rilla); D7's are already in `d`.
        virtual void DescribeExtra(PoolFight& /*fight*/, Creature* /*boss*/, BossMechanics::Descriptor& /*d*/) { }
    };

    enum class PoolPackage : uint8
    {
        Crew = 0,           // D7Ha
        Deluge = 1,         // D7Hb
        Count = 2,
    };

    using PoolHardModeFactory = std::function<std::unique_ptr<PoolHardMode>(PoolFight& fight)>;

    // D7Ha / D7Hb, from their AddSC_ function (once each; a second call replaces the first; any AddSC_ order).
    void RegisterPoolHardMode(PoolPackage package, PoolHardModeFactory factory);
    // D7, at Velratha's pull of the hard mode: one object per registered package, in PoolPackage order.
    std::vector<std::unique_ptr<PoolHardMode>> CreatePoolHardModes(PoolFight& fight);
    // The fight on `map` (nullptr between pulls or off map 209).
    PoolFight* FindPoolFight(Map* map);
}

#endif
