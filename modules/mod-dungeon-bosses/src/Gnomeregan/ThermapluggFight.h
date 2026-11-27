/*
 * mod-dungeon-bosses, Gnomeregan D6: Mekgineer Thermaplugg's hooks (engine side) for the Whole Workshop's packages
 * D6Ha (thermaplugg_hard_mode.cpp: the console, the Techbot and Fallout schematics, the Reactor Leak) and D6Hb
 * (thermaplugg_hard_mode_machines.cpp: the Electrocutioner, Alert System and Pummeler schematics). The Zul'Farrak
 * PoolFight.h shape (FACTS-FRAMEWORK A.5 #2). Written by WP-D6; after D6 reports it is the orchestrator's (S0 report
 * section 4). D6Ha and D6Hb never edit boss_thermaplugg_rework.cpp and share only this file. Pure rules and numbers:
 * ThermapluggLogic.h (the same namespace).
 *
 *   ThermapluggFight      what D6 offers the packages, valid from his pull to the encounter's end (passed to every
 *                         hook; Thermaplugg's AI implements it). Find it from anywhere (an add's AI, `.dbtest`) with
 *                         GnomerThermaplugg::FindThermapluggFight(map): nullptr between pulls.
 *   ThermapluggHardMode   one package's per-pull object. A package registers a factory once, from its AddSC_:
 *                             GnomerThermaplugg::RegisterThermapluggHardMode(
 *                                 GnomerThermaplugg::HardModePackage::SchematicsA,
 *                                 [](GnomerThermaplugg::ThermapluggFight& fight)
 *                                 { return std::make_unique<X>(fight); });
 *
 * Arming (RB-24, handoff 3.7). At his pull on heroic with the console's flag (DATA_HARD_MODE), D6 asks every
 * registered factory for one object (SchematicsA, then SchematicsB). With at least one made the pull is the Whole
 * Workshop: D6 sends DATA_HARD_MODE_VERDICT kVerdictArmed (the instance lights the loot bit and writes slot 6 at the
 * kill), sets his health to GnomereganRework::Health::kWholeWorkshop (800,000) and runs the mode Mode::HardMode
 * (ThermapluggLogic.h ValuesFor: SP 1799's raised values, which are D6's: faces every 12 s, Override every 35 s, bombs
 * 7,000, blasts and mines 70%, mines every 12 s for 75 s, the Detonator every 20 s, the plate lockout 30 s). With none
 * made (no package registered, or a normal or unflagged pull) the verdict is kVerdictPlain. A factory that returns
 * nullptr opts out of that pull.
 *
 * Hook order:
 *   the pull          BossAI's engage (slot 5 IN_PROGRESS), D6's encounter, the packages made, the verdict, the
 *                     health, then OnEngage (each package, in package order), then the descriptors (D6's, then each
 *                     package's DescribeExtra), then his aggro line and the pull line
 *                     ("gnomer-build thermaplugg pull health=800000 heroic=1 hardmode=1").
 *   every tick        D6's clocks (the faces, the chutes, the bombs, the mines, the plates, the Sticky Bombs, The Big
 *                     One, the Detonator, Knock Away), then OnUpdate (each package), then the health thresholds.
 *   his health        OnHealthPct(pct) once per threshold the package named in HealthThresholds (read once, after
 *                     OnEngage), highest first, as his health falls to or under it (MT15: 90 / 75 / 60 / 45 / 30).
 *   a face opens      OnFaceOpened(face, why) after the face, its beam and its plate are up (why: "timer",
 *                     "override", or the reason the package gave to OpenFace).
 *   a face shuts      OnFaceShut(face, by) after its plate is gone (`by`: the player whose plate touch shut it;
 *                     nullptr when D6 shuts it at the end).
 *   a plate touch     OnPlateTouched(player, face) right after the touch shut the face and Locked Out landed (MT18:
 *                     the dose halves here).
 *   the plates' rule  SetPlatePlan(order, first, planned) (a package, any time in the pull): the Ordering of D6's
 *                     plate Soak, the lit plates the bots serve first and the bots planned (MT18's dose bots, D6Ha).
 *   a bomb            OnBombSpawned(bomb, type, copy) once D6 has set it up (marked, walking, tracked); `copy` is true
 *                     for a unit D6 adopted through AdoptBomb (a Duplicator copy: the machine already tracks it).
 *                     The Sticky Bomb is an aura, never a unit: no call. OnBombGone(guid, why) when a bomb leaves
 *                     ("blast", "killed", "no-target", "despawned", "end"): a Duplicator's Forget goes there.
 *   players hit       OnPlayersHit(source, at, hit) after every blast that reached players (a walking bomb's,
 *                     a mine's, the Sticky Bomb's, The Big One's): MT21's "+1,000 volts per player hit". Never from a
 *                     registry callback (D6 queues the registry's own resolves to its next tick).
 *   his percents      DamageFactor() of every package, multiplied into every percent hit D6 registers from then on
 *                     (bombs, mines, the Sticky Bomb, The Big One, the fire patch): MT21's +3% per 1,000 volts. His
 *                     melee and Knock Away are not D6's percents: a package raises those with an aura on him.
 *   the end           OnEnd(won) first in D6's cleanup (his death: won; a wipe or an evade: not), with the fight
 *                     still usable; then D6 clears its own handles, summons and auras. Everything a package changed
 *                     it undoes in OnEnd: its machines' Clear() goes there (GnomereganMachines.h).
 *
 * Units a package summons come from Summon (his summons: despawned by D6's cleanup) and registry handles go to Track
 * (canceled with the fight). Registry owners: D6 (the boss) for everything; a shape that must outlive a unit sits on a
 * stalker (rule 31). Bot shapes take `.Within(GnomereganRework::ThermapluggFloorBounds())` (rule 14).
 */

#ifndef MOD_DUNGEON_BOSSES_GNOMEREGAN_THERMAPLUGG_FIGHT_H
#define MOD_DUNGEON_BOSSES_GNOMEREGAN_THERMAPLUGG_FIGHT_H

#include "BossMechanics.h"
#include "Define.h"
#include "GnomereganKit.h"
#include "GnomereganMachines.h"
#include "GnomereganRework.h"
#include "ObjectGuid.h"
#include "Position.h"
#include "ThermapluggLogic.h"
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

namespace GnomerThermaplugg
{
    class ThermapluggHardMode;

    // What reached players (OnPlayersHit).
    enum class HitSource : uint8
    {
        Bomb,       // a walking bomb's blast (MT3, MT8 to MT11; a Remote Detonator blast too)
        Mine,       // MT5
        Sticky,     // MT12
        BigOne,     // MT13
    };
    inline constexpr std::array<char const*, 4> kHitSourceNames{ { "bomb", "mine", "sticky", "big-one" } };

    // D6's encounter, as the hard mode sees it (valid from his pull to the encounter's end).
    class ThermapluggFight
    {
    public:
        virtual ~ThermapluggFight() = default;

        virtual Creature* Boss() = 0;
        virtual InstanceScript* Instance() = 0;
        virtual bool Heroic() const = 0;
        virtual bool HardMode() const = 0;              // the packages were built at this pull (the armed verdict)
        virtual Mode FightMode() const = 0;             // Normal, Heroic or HardMode (ThermapluggLogic.h ValuesFor)
        virtual uint64 ClockMs() const = 0;             // since his pull
        // The players of the fight: on his threat list, alive, in the world, not game masters, in his room's arena.
        virtual std::vector<Player*> FightPlayers() = 0;

        // ---- The faces (index 0 to 5 = face 01 to 06, ruling 64) ----
        virtual bool FaceOpen(uint32 face) const = 0;
        virtual FaceMask OpenFaces() const = 0;
        // MT23 (a Spotted player opens a closed face): `face` when it is closed, else a random closed one (nullopt:
        // a random one). Returns the face opened (nullopt: every face is open). OnFaceOpened(face, why) follows.
        virtual std::optional<uint32> OpenFace(std::optional<uint32> face, char const* why) = 0;
        // The face's stock object spot (DB) and its alcove mouth (the bomb start, kBombStarts): the fist's frame and
        // the vents read these.
        virtual Position FaceSpot(uint32 face) const = 0;
        virtual Position FaceMouth(uint32 face) const = 0;
        // The face stalker at the alcove mouth (passive, unselectable; the beam's end), nullptr when gone.
        virtual Creature* FaceStalker(uint32 face) = 0;

        // ---- The plates (MT4) ----
        // The plate's anchor unit (passive, unselectable, at kPlateSpots[face]): where the plate is.
        virtual Creature* PlateAnchor(uint32 face) = 0;
        virtual bool PlateLit(uint32 face) const = 0;   // the face is open: a touch shuts it
        virtual bool LockedOut(Unit const* player) const = 0;
        // The bots' plate rule (D6's one plate Soak per lit plate: tag 71, one claim a bot, the one exclusive group;
        // F-1d, STAGE-R-1-C Minor-1). `order` is every plate Soak's Ordering from now on (D6's own until a package
        // sets one: non-tanks first, by ETA); `first` lists lit faces the bots serve first, in that order (the other
        // lit plates follow in their current order); `planned` the bots the plan places (GnomerWorkshop::PlatePlanBots,
        // sorted guids). A call that changes none of the Ordering, the serve order and `planned` does nothing; one
        // that does registers every lit plate anew at once (the bots' claims start over, so an older sticky claim
        // cannot keep a plate the plan gives a bot that just reached 8: RF-1 Minor-5). Plates lit later register with
        // `order` and take their face priority until the next call. D6Ha calls it while the Fallout schematic runs
        // (GnomerWorkshop::PlatePlan); D6 resets it at the end of the encounter.
        virtual void SetPlatePlan(BossMechanics::Ordering const& order, std::vector<uint32> const& first,
            std::vector<uint64> const& planned) = 0;

        // ---- The bombs ----
        // The living bombs (walking bombs and The Big One), in spawn order.
        virtual std::vector<ObjectGuid> Bombs() const = 0;
        // MT16: a Duplicator copy (summoned by the machine with Thermaplugg as the owner, at the source's spot, with
        // the source's health) becomes a bomb of the source's type: max health of the mode, the source's current
        // health kept, marked on the source's target (else a new pick), walking, tracked by D6 (its blast, its death,
        // the cleanup). False: `source` is not one of D6's walking bombs, or `copy` is not its entry.
        virtual bool AdoptBomb(Creature* source, Creature* copy) = 0;

        // ---- Plumbing ----
        // A unit for the fight (manual despawn unless `despawnMs`), despawned by D6's cleanup. nullptr: refused.
        virtual Creature* Summon(uint32 entry, Position const& at, uint32 despawnMs = 0) = 0;
        // A registry handle canceled with the fight.
        virtual void Track(BossMechanics::MechanicHandle handle) = 0;
        // Describe the boss again (DescribeExtra included).
        virtual void RefreshDescriptors() = 0;
        // `pct` of the reference row (the tank row on the tank) with Thermaplugg as the owner (rule 2).
        virtual uint32 RefFlatOn(Unit const* target, float pct) = 0;
        // His creature_text group (the packages' own: 9 to 11, kFirstPackageTextGroup); `target` for $n.
        virtual void Say(uint8 group, WorldObject const* target = nullptr) = 0;
        // One INFO line "gnomer-build thermaplugg <mechanic> <detail>".
        virtual void Log(char const* mechanic, std::string const& detail = {}) = 0;
    };

    // One package's object for one pull. Every hook has a do-nothing default.
    class ThermapluggHardMode
    {
    public:
        virtual ~ThermapluggHardMode() = default;

        virtual void OnEngage(ThermapluggFight& /*fight*/) { }
        virtual void OnUpdate(ThermapluggFight& /*fight*/, uint32 /*diff*/) { }
        // His health crossed `pct` downward (each threshold named here, once per pull, highest first).
        virtual std::vector<float> HealthThresholds() const { return {}; }
        virtual void OnHealthPct(ThermapluggFight& /*fight*/, float /*pct*/) { }
        virtual void OnFaceOpened(ThermapluggFight& /*fight*/, uint32 /*face*/, char const* /*why*/) { }
        virtual void OnFaceShut(ThermapluggFight& /*fight*/, uint32 /*face*/, Player* /*by*/) { }
        virtual void OnPlateTouched(ThermapluggFight& /*fight*/, Player* /*player*/, uint32 /*face*/) { }
        virtual void OnBombSpawned(ThermapluggFight& /*fight*/, Creature* /*bomb*/, BombType /*type*/, bool /*copy*/)
        {
        }
        virtual void OnBombGone(ThermapluggFight& /*fight*/, ObjectGuid /*bomb*/, char const* /*why*/) { }
        virtual void OnPlayersHit(ThermapluggFight& /*fight*/, HitSource /*source*/, Position const& /*at*/,
            GuidSet const& /*hit*/)
        {
        }
        // A factor on D6's percent hits from now on (1: none).
        virtual float DamageFactor(ThermapluggFight const& /*fight*/) const { return 1.f; }
        // The encounter ends: his death (won), a wipe or an evade. Undo everything here (machines' Clear included).
        virtual void OnEnd(ThermapluggFight& /*fight*/, bool /*won*/) { }
        // Extra entries for the bots' boss data; D6's are already in `d`.
        virtual void DescribeExtra(ThermapluggFight& /*fight*/, BossMechanics::Descriptor& /*d*/) { }
        // One line for `.dbtest gnomer thermaplugg state` (and the packages' own `state`).
        virtual std::string Describe() const { return {}; }
    };

    enum class HardModePackage : uint8
    {
        SchematicsA = 0,    // D6Ha: Techbot, Viscous Fallout, the Reactor Leak
        SchematicsB = 1,    // D6Hb: Electrocutioner, the Alert System, Crowd Pummeler
        Count = 2,
    };

    using ThermapluggHardModeFactory = std::function<std::unique_ptr<ThermapluggHardMode>(ThermapluggFight& fight)>;

    // D6Ha / D6Hb, from their AddSC_ function (once each; a second call replaces the first; any AddSC_ order).
    void RegisterThermapluggHardMode(HardModePackage package, ThermapluggHardModeFactory factory);
    // D6, at the pull of the hard mode: one object per registered package, in HardModePackage order.
    std::vector<std::unique_ptr<ThermapluggHardMode>> CreateThermapluggHardModes(ThermapluggFight& fight);
    // The fight on `map` (nullptr between pulls or off map 90).
    ThermapluggFight* FindThermapluggFight(Map* map);
}

#endif
