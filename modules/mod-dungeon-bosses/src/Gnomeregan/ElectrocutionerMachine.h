/*
 * mod-dungeon-bosses, Gnomeregan D3: the VoltageMeter machine's engine half (GnomereganMachines.h, handoff section 3.2
 * item 7; SP EL1, EL2, MT21, MT22). The pure half (the meter, the cadence, the shape in turn, the outer reach) is
 * ElectrocutionerLogic.h VoltageClock and its helpers.
 *
 * How it runs (ElectrocutionerMachine.cpp), for any owner (Electrocutioner, or Thermaplugg under the hard mode):
 *   - The stacks of `auraSpellId` on the owner are the meter (1,000 volts a stack): +1 every `tickEveryMs`, plus Add()
 *     (a Megavolt hit, a jump, a discharge, a mine or bomb hit). Reasserted every second and on every change (rule 25);
 *     from 3 stacks the owner also wears the brighter crackle (SPELL_VOLTAGE_CHARGED, V's tier 2).
 *   - At every `justiceEvery` stacks (and never while one runs) the owner starts Electric Justice: `barSpellId` on
 *     himself (not triggered: the bar players read; a refusal retries in 1 s, rule 15; a cast already running waits),
 *     the yell and the emote, and a registry zone anchored on him for `castMs`: the donut safe within `safeRadius` out
 *     to the floor's farthest point, or (heroic Electrocutioner, `alternate`) the `circleRadius` circle on every other
 *     one, donut first. `pct` of the reference row (the tank row on the tank) times DamageMultiplier(), Nature,
 *     SPELL_JUSTICE_HIT, no Weakened. The zone's resolve only records its hits; the landing runs on the next Update
 *     (rule 11): `resetAfterJustice` empties the meter, the blast look plays (V's SV 3 on blast stalkers 301132: six
 *     on a ring through the donut, one on him for the circle), then `onJusticeLand(count, hit)`.
 *   - `pauseAfterJusticeMs` (normal): no climb during the bar or for that long after it; Add() is refused meanwhile.
 *   - Clear() cancels the zone, takes both auras off the owner and empties the meter; safe twice, owner or not.
 *   - Logs: "gnomer-build <logKey> voltage <add|justice-start|justice-land|refused|clear> ...".
 *
 * Beyond the contract, for Electrocutioner's own AI: ElectroVoltageMeter (the concrete class) adds the Justice count,
 * the stacks still missing to the next one, and SetBotBounds (his bots' bounds are the 21 yd pick disc, while the
 * donut's reach is the whole platform and the walkway). ElectrocutionerVoltageSpec(heroic) is his spec.
 */

#ifndef MOD_DUNGEON_BOSSES_GNOMER_ELECTROCUTIONER_MACHINE_H
#define MOD_DUNGEON_BOSSES_GNOMER_ELECTROCUTIONER_MACHINE_H

#include "BossMechanics.h"
#include "ElectrocutionerLogic.h"
#include "GnomereganMachines.h"
#include <memory>
#include <optional>
#include <string>
#include <vector>

class Map;

namespace GnomereganMachines
{
    class ElectroVoltageMeter final : public VoltageMeter
    {
    public:
        ElectroVoltageMeter(MachineOwner const& owner, VoltageSpec spec);

        void Update(uint32 diff) override;
        void Clear() override;
        std::string Describe() const override;
        uint32 Add(uint32 stacks, char const* why) override;
        uint32 Stacks() const override { return _clock.Stacks(); }
        float DamageMultiplier() const override;
        bool JusticeRunning() const override { return _clock.Running(); }
        void Pause(uint32 ms) override { _clock.Pause(ms); }

        // Beyond the contract.
        uint32 Justices() const { return _clock.Justices(); }
        uint32 ToNext() const { return _clock.ToNext(); }
        // The bots' hard bounds on the Justice zones (default: the spec's floor).
        void SetBotBounds(BossMechanics::SpotBounds const& bounds) { _botBounds = bounds; }

    private:
        // Matches a resolve of the running Justice zone to its landing (the registry's callback writes only here).
        struct Landing
        {
            uint32 mechanicId = 0;
            bool resolved = false;
            std::vector<ObjectGuid> hits;
        };

        Creature* Owner() const;
        void ApplyStacks(Creature* owner);
        void TryStartJustice(Creature* owner);
        // `hits` by value: the caller's vector lives in the Landing this resets.
        void Land(Creature* owner, std::vector<ObjectGuid> hits, bool resolved);
        void BlastLook(Creature* owner, GnomerElectro::JusticeShape shape);
        void Log(char const* what, std::string const& detail) const;

        ObjectGuid _owner;
        Map* _map = nullptr;
        char const* _logKey = "";
        bool _heroic = false;
        VoltageSpec _spec;
        GnomerElectro::VoltageClock _clock;
        std::optional<BossMechanics::SpotBounds> _botBounds;
        BossMechanics::MechanicHandle _zone;
        std::shared_ptr<Landing> _landing;
        GnomerElectro::JusticeShape _shape = GnomerElectro::JusticeShape::Donut;
        uint32 _started = 0;
        uint32 _now = 0;
        uint32 _landDeadline = 0;
        uint32 _retryLeft = 0;
        uint32 _reassertLeft = 0;
    };

    // Electrocutioner's own meter on a difficulty (SP EL1, EL2): normal resets after each Justice and pauses 10 s,
    // the donut only; heroic never resets, +3% a stack, the donut and the circle in turn. Floor: the platform and the
    // walkway (GnomerElectro::JusticeFloor: the donut reaches about 48 yd, the walkway's far end).
    VoltageSpec ElectrocutionerVoltageSpec(bool heroic);

    // The concrete machine for Electrocutioner's AI (MakeVoltageMeter returns the same class behind the contract).
    std::unique_ptr<ElectroVoltageMeter> MakeElectroVoltageMeter(MachineOwner const& owner, VoltageSpec spec);
}

#endif
