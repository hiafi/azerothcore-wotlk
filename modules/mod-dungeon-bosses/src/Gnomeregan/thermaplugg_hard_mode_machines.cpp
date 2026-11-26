/*
 * mod-dungeon-bosses, Gnomeregan D6Hb: the Whole Workshop, part b, the package SchematicsB of Mekgineer Thermaplugg's
 * heroic hard mode (ThermapluggFight.h). Build spec: docs/dungeons/gnomeregan-rework.md "Hard mode: the Whole
 * Workshop" (SP 1738-1864; MT15, MT21-MT24), rulings 43-53, 68, 69; handoff sections 3.5 row D6Hb, 3.7, 3.8 (the
 * room), 3.9 row 10, 7 #33 A, #35 A, 10. Pure rules and every number: ThermapluggHardModeMachinesLogic.h. It plugs
 * into D6's hooks only (never boss_thermaplugg_rework.cpp) and loads the earlier bosses' machines onto him; it never
 * re-implements one (GnomereganMachines.h):
 *
 *   The package        GnomerThermaplugg::RegisterThermapluggHardMode(HardModePackage::SchematicsB): D6 makes one at
 *                      his pull of the hard mode (heroic, the console's flag), after D6Ha's SchematicsA
 *   MT15 the loads     HealthThresholds 60 / 45 / 30: each loads its schematic once and it stays to the end; the
 *                      console's line "Loading schematic: <NAME>" (a boss emote over the room; D6Ha yells line 9 on
 *                      the first load at 90%)
 *   60% Electrocutioner MT21 / MT22 by D3's VoltageMeter (MakeElectroVoltageMeter) on him: +1,000 volts every 5 s and
 *                      for every player a mine or a bomb hits (OnPlayersHit), 3% to all his damage a stack (his aura
 *                      for melee and Knock Away, DamageFactor for D6's percent hits, this package's own hits), never
 *                      resets; Electric Justice at every 6,000: a 4 s Physical bar, emote line 10, the room outside
 *                      8 yd of him, 75% times the factor (the dose multiplies it too: ruling 49)
 *   45% Alert System   MT23 by D4's LightsMachine (MakeAlertLightsMachine) riding on him: two opposite 30 degree cones
 *                      to the wall at 12 degrees a second, lit after a 3 s dim opening; Spotted (D4's 3 s latch):
 *                      50% times the factor, no Weakened, and a closed face opens (ThermapluggFight::OpenFace)
 *   30% Pummeler       MT24 by D5's ComboMachine (MakeComboMachine, the 3-argument factory), a new machine on a new
 *                      frame each combination: every 18 s a random Gnome Face (open or shut) lights up and the
 *                      Pummeler's Fist (301136) winds up behind it; three of the four shapes read from that face
 *                      (its left and right halves split on the face-to-center line, near within 50 yd of it, far past
 *                      it: section 7 #33 A) drawn at once and numbered on the floor (V's numerals on light stalkers
 *                      301113), punches at 4.0 / 6.5 / 9.0 s, 60% times the factor and Weakened, emote line 11
 *   Not D6Hb's         the console, the flag, the verdict, the health and the loot bit (D6Ha, D6, the instance); the
 *                      Techbot and Fallout schematics and the Reactor Leak (D6Ha); every raised heroic value (D6's
 *                      Mode::HardMode)
 *
 * Cleanup (RB-1): OnEnd clears the three machines (the Voltage aura, the Justice zone, the lights and their stalkers,
 * the fist's zones and decoys), despawns the fist and the numerals and takes the face's glow off; D6's cleanup right
 * after despawns his summons and cancels the handles this package tracked. Every firing logs one INFO line
 * "gnomer-build schematics <mechanic> ..." (the machines' own lines carry the same key); `.dbtest gnomer schematics
 * <mechanic>` fires one. No stock code is mirrored (the stock Thermaplugg ran SmartAI; the machines are D3's, D4's and
 * D5's).
 */

#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "CrowdPummelerMachine.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "ElectrocutionerMachine.h"
#include "GnomereganKit.h"
#include "GnomereganMachines.h"
#include "GnomereganRework.h"
#include "GnomereganTestCommand.h"
#include "Map.h"
#include "MechanicDescriptor.h"
#include "MobileAlertSystemMachine.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SharedDefines.h"
#include "StringFormat.h"
#include "ThermapluggFight.h"
#include "ThermapluggHardModeMachinesLogic.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

using namespace Acore::ChatCommands;
using namespace GnomereganRework;
using namespace GnomerSchematics;
using GnomerThermaplugg::HitSource;
using GnomerThermaplugg::ThermapluggFight;

class SchematicsHardMode;

namespace
{
    char const* const kLogKey = "schematics";
    float constexpr kFloorBandYd = 8.f;

    void LogSchematics(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kLogKey, mechanic, detail);
    }

    uint32 RandBelow(uint32 n)
    {
        return n ? urand(0, n - 1) : 0;
    }

    // The floor under (x, y) near `zHint`; the hint where the map has none close to it.
    float FloorZ(WorldObject const* ref, Vec2 p, float zHint)
    {
        if (!ref)
            return zHint;
        float const floor = ref->GetMapHeight(p.x, p.y, zHint + 5.f);
        return (floor > INVALID_HEIGHT + 1.f && std::fabs(floor - zHint) <= kFloorBandYd) ? floor : zHint;
    }

    GnomereganMachines::PunchShape ToPunch(Shape s)
    {
        return static_cast<GnomereganMachines::PunchShape>(static_cast<uint8>(s));
    }

    // The live packages by map, for `.dbtest gnomer schematics` (maps update on several threads).
    std::mutex& LiveLock()
    {
        static std::mutex lock;
        return lock;
    }

    std::unordered_map<Map const*, SchematicsHardMode*>& Live()
    {
        static std::unordered_map<Map const*, SchematicsHardMode*> live;
        return live;
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// The package (ThermapluggFight.h ThermapluggHardMode), one per pull of the hard mode
// ---------------------------------------------------------------------------------------------------------------------

class SchematicsHardMode final : public GnomerThermaplugg::ThermapluggHardMode
{
public:
    explicit SchematicsHardMode(ThermapluggFight& fight) : _fight(&fight)
    {
        if (Creature* boss = fight.Boss())
            _map = boss->GetMap();
        std::lock_guard<std::mutex> guard(LiveLock());
        Live()[_map] = this;
    }

    ~SchematicsHardMode() override
    {
        Unlist();
    }

    static SchematicsHardMode* Find(Map const* map)
    {
        std::lock_guard<std::mutex> guard(LiveLock());
        auto it = Live().find(map);
        return it == Live().end() ? nullptr : it->second;
    }

    // ---- ThermapluggHardMode --------------------------------------------------------------------------------------

    void OnEngage(ThermapluggFight& fight) override
    {
        LogSchematics("armed", Acore::StringFormat("heroic={} loads={}/{}/{}", fight.Heroic() ? 1 : 0,
            Tune::kLoadPct[0], Tune::kLoadPct[1], Tune::kLoadPct[2]));
    }

    std::vector<float> HealthThresholds() const override
    {
        return Thresholds();
    }

    void OnHealthPct(ThermapluggFight& fight, float pct) override
    {
        if (std::optional<Schematic> const s = SchematicAt(pct))
            Load(fight, *s, "health");
    }

    void OnUpdate(ThermapluggFight& fight, uint32 diff) override
    {
        if (_ended)
            return;
        if (_voltage)
        {
            _voltage->Update(diff);
            _voltsPeak = std::max(_voltsPeak, _voltage->Stacks());
        }
        if (_lights)
            _lights->Update(diff);
        if (_combo)
            _combo->Update(diff);
        if (Loaded(Schematic::Pummeler) && fight.ClockMs() >= _fistAt && !(_combo && _combo->Running()))
        {
            uint64 const due = _fistAt;
            if (StartCombination(fight, std::nullopt, "timer"))
                _fistAt = GnomerThermaplugg::NextDue(due, Tune::kFistEveryMs, fight.ClockMs());
            else
                _fistAt = fight.ClockMs() + 1000;   // refused (he is gone, the machine refused): look again in 1 s
        }
    }

    // MT21: +1,000 volts for every player a mine or a bomb hit (D6 queues these out of the registry's callbacks).
    void OnPlayersHit(ThermapluggFight& /*fight*/, HitSource source, Position const& /*at*/,
        GuidSet const& hit) override
    {
        if (!_voltage || _ended || !SourceCharges(static_cast<uint8>(source)))
            return;
        std::size_t players = 0;
        for (ObjectGuid const& guid : hit)
            players += guid.IsPlayer() ? 1 : 0;
        if (uint32 const volts = VoltsForHit(players))
            _voltage->Add(volts, GnomerThermaplugg::kHitSourceNames[static_cast<std::size_t>(source)]);
    }

    // MT21: 3% to all his damage per 1,000 volts (D6 multiplies it into every percent hit it registers from now on).
    float DamageFactor(ThermapluggFight const& /*fight*/) const override
    {
        return Factor();
    }

    void OnEnd(ThermapluggFight& fight, bool won) override
    {
        _ended = true;
        Creature* boss = fight.Boss();
        if (_combo)
            _combo->Clear();
        if (_lights)
            _lights->Clear();
        if (_voltage)
            _voltage->Clear();
        EndCombinationUnits(boss);
        LogSchematics("end", Acore::StringFormat("won={} loaded={} combinations={} spotted={} faces-opened={} "
            "peak-voltage={}", won ? 1 : 0, LoadedNames(), _combinations, _spotted, _facesOpened, _voltsPeak));
        Unlist();
    }

    // The bots: the fist and the stalkers this package summons are no one's target (D3's blast stalkers are map
    // summons). The Justice donut, the lights and the fist's shapes are registry kinds the bots read already.
    void DescribeExtra(ThermapluggFight& /*fight*/, BossMechanics::Descriptor& d) override
    {
        d.ignores.emplace_back(NPC_PUMMELERS_FIST);
        d.ignores.emplace_back(NPC_LIGHT_STALKER);
        d.ignores.emplace_back(NPC_BLAST_STALKER);
    }

    std::string Describe() const override
    {
        std::string out = Acore::StringFormat("schematics-b loaded={} factor={:.2f} spotted={} faces-opened={} "
            "combinations={} next-fist={}ms", LoadedNames(), Factor(), _spotted, _facesOpened, _combinations,
            Loaded(Schematic::Pummeler) && _fight ? int64(_fistAt) - int64(_fight->ClockMs()) : -1);
        if (_voltage)
            out += " | " + _voltage->Describe();
        if (_lights)
            out += " | " + _lights->Describe();
        if (_combo)
            out += " | " + _combo->Describe();
        return out;
    }

    // ---- the schematics (OnHealthPct, `.dbtest gnomer schematics load`) --------------------------------------------

    bool Loaded(Schematic s) const
    {
        return _loaded[SchematicIndex(s)];
    }

    // MT15: load `s` now (once; it stays to the end). False: loaded already, or he is gone.
    bool Load(ThermapluggFight& fight, Schematic s, char const* why)
    {
        Creature* boss = fight.Boss();
        if (_ended || Loaded(s) || !boss || !boss->IsAlive() || !boss->IsInWorld())
            return false;
        _loaded[SchematicIndex(s)] = true;
        switch (s)
        {
            case Schematic::Electrocutioner:
                LoadVoltage(boss);
                break;
            case Schematic::AlertSystem:
                LoadLights(boss);
                break;
            case Schematic::Pummeler:
                _fistAt = fight.ClockMs() + Tune::kFistFirstMs;
                break;
        }
        // The console's line over the room (SP MT15; a boss emote: the console is a game object and cannot speak).
        boss->Talk(LoadLine(s), CHAT_MSG_RAID_BOSS_EMOTE, LANG_UNIVERSAL, Tune::kConsoleLineYd, nullptr);
        LogSchematics("load", Acore::StringFormat("schematic={} why={} health={:.1f}% clock={}ms factor={:.2f}",
            kSchematicKeys[SchematicIndex(s)], why, boss->GetHealthPct(), fight.ClockMs(), Factor()));
        return true;
    }

    // ---- `.dbtest gnomer schematics` -------------------------------------------------------------------------------

    GnomereganMachines::ElectroVoltageMeter* Voltage() { return _voltage.get(); }
    GnomereganMachines::AlertLightsMachine* Lights() { return _lights.get(); }

    // MT24 now (a GM; `face` 0 to 5, else a random one). Empty on success, else why not.
    std::string Fist(ThermapluggFight& fight, std::optional<uint32> face)
    {
        if (_combo && _combo->Running())
            return "A combination is running already.";
        return StartCombination(fight, face, "gm") ? std::string() : std::string("The fist refused (see the log).");
    }

private:
    float Factor() const
    {
        return _voltage ? _voltage->DamageMultiplier() : 1.f;
    }

    std::string LoadedNames() const
    {
        std::string out;
        for (std::size_t i = 0; i < kSchematicCount; ++i)
            if (_loaded[i])
                out += (out.empty() ? "" : ",") + std::string(kSchematicKeys[i]);
        return out.empty() ? "none" : out;
    }

    GnomereganMachines::MachineOwner Owner(Creature* boss) const
    {
        GnomereganMachines::MachineOwner owner;
        owner.owner = boss;
        owner.logKey = kLogKey;
        owner.heroic = true;
        return owner;
    }

    void Unlist()
    {
        std::lock_guard<std::mutex> guard(LiveLock());
        auto it = Live().find(_map);
        if (it != Live().end() && it->second == this)
            Live().erase(it);
    }

    // ---- MT21, MT22: the Electrocutioner schematic ------------------------------------------------------------------

    void LoadVoltage(Creature* boss)
    {
        GnomereganMachines::VoltageSpec spec;
        GnomerElectro::VoltageRules const rules = VoltageRules();
        spec.auraSpellId = SPELL_HMB_VOLTAGE;
        spec.tickEveryMs = rules.tickMs;
        spec.justiceEvery = rules.every;
        spec.resetAfterJustice = rules.resetAfterJustice;
        spec.pauseAfterJusticeMs = rules.pauseAfterMs;
        spec.justiceMinGapMs = rules.minGapMs;
        spec.damagePctPerStack = Tune::kVoltagePctPerStack;
        spec.justice.barSpellId = SPELL_HMB_JUSTICE_BAR;
        spec.justice.castMs = Tune::kJusticeCastMs;
        spec.justice.safeRadius = Tune::kJusticeSafeYd;
        spec.justice.alternate = false;     // the hard mode: the donut only
        spec.justice.pct = Tune::kJusticePct;
        spec.justice.floor = RoomArena();
        spec.justice.donutEmoteGroup = EMOTE_HMB_JUSTICE;
        spec.justice.tag = TAG_HMB_JUSTICE;     // G1 row 10's Zone/85 (not Electrocutioner's 40)
        _voltage = GnomereganMachines::MakeElectroVoltageMeter(Owner(boss), std::move(spec));
    }

    // ---- MT23: the Alert System schematic ---------------------------------------------------------------------------

    void LoadLights(Creature* boss)
    {
        GnomereganMachines::LightsSpec spec;
        spec.mode = GnomereganMachines::LightsSpec::Mode::Turning;
        spec.cones = Tune::kLightsCones;
        spec.coneDeg = Tune::kLightsConeDeg;
        spec.rangeYd = Tune::kLightsRangeYd;
        spec.turnDegPerSec = Tune::kLightsDegPerSec;
        spec.speedUpPctPerSpotted = Tune::kLightsSpeedUpPct;
        spec.reverseMinMs = Tune::kLightsReverseMinMs;
        spec.reverseMaxMs = Tune::kLightsReverseMaxMs;
        spec.reverseStopMs = Tune::kLightsReverseStopMs;
        spec.latchMs = Tune::kLightsLatchMs;
        spec.floor = RoomArena();

        GnomereganMachines::LightsExtras extras;
        extras.tag = TAG_HMB_LIGHTS;
        extras.litAfterMs = Tune::kLightsDarkMs;
        extras.direction = Tune::kLightsDirection;
        extras.startBearing = LightsStartBearing(boss->GetOrientation());
        extras.zBand = Tune::kLightsZBandYd;
        extras.bounds = ThermapluggFloorBounds();
        // Called from the machine's Update, inside OnUpdate (never a registry callback): `this` outlives it.
        extras.onSpottedBy = [this](Player* who, GnomereganMachines::SpotSource source, uint8 /*light*/)
        {
            OnSpotted(who, source);
        };

        GnomereganMachines::LightsAnchor anchor;
        anchor.unit = boss->GetGUID();      // the lights ride on him as he walks (KT-G F23, F53)
        _lights = GnomereganMachines::MakeAlertLightsMachine(Owner(boss), anchor, std::move(spec), std::move(extras));
        _lights->Start();
    }

    // MT23: Spotted (the machine's latch passed): 50% times the factor, the beam, and a closed face opens.
    void OnSpotted(Player* who, GnomereganMachines::SpotSource source)
    {
        Creature* boss = _fight ? _fight->Boss() : nullptr;
        if (_ended || !who || !boss || !boss->IsAlive())
            return;
        ++_spotted;
        boss->CastSpell(who, SPELL_HMB_SPOTTED_BEAM, true);
        DungeonKit::RegistryHitSpec hit;
        hit.pct = Scaled(Tune::kSpottedPct, Factor());
        hit.tankPct = hit.pct;      // rule 17: the tank's own row
        hit.school = uint8(SPELL_SCHOOL_ARCANE);
        hit.spellId = SPELL_HMB_SPOTTED;
        hit.weakened = Tune::kSpottedWeakened;
        hit.tag = TAG_HMB_LIGHTS;
        _fight->Track(DungeonKit::RegistryHit(boss, GuidSet{ who->GetGUID() }, hit));
        std::optional<uint32> opened;
        if (Tune::kSpottedOpensFace)
            opened = _fight->OpenFace(std::nullopt, "spotted");
        if (opened)
            ++_facesOpened;
        LogSchematics("spotted", Acore::StringFormat("player={} by={} pct={:.1f} face={} count={}", who->GetName(),
            GnomereganMachines::SpotSourceName(source), hit.pct, opened ? int32(*opened) + 1 : 0, _spotted));
    }

    // ---- MT24: the Pummeler schematic -------------------------------------------------------------------------------

    GnomereganMachines::ComboSpec FistSpec(uint32 face)
    {
        GnomereganMachines::ComboSpec spec;
        DungeonKit::ComboFrame const frame = FistFrame(face);
        spec.frame.origin = Position(frame.origin.x, frame.origin.y, frame.z, frame.facing);
        spec.frame.halfReachYd = Tune::kFistHalfReachYd;
        spec.frame.nearRadiusYd = Tune::kFistNearYd;
        spec.frame.farOuterYd = Tune::kFistFarOuterYd;
        spec.frame.floor = RoomArena();     // the bots' bounds (D5: the hits are not clipped)
        spec.callFlashMs = 0;
        spec.windUpMs = Tune::kFistWindUpMs;
        spec.markerMs = Tune::kFistLiveMs;
        spec.gapMs = Tune::kFistApartMs;
        spec.drawAllAtOnce = true;
        spec.pct.fill(Scaled(Tune::kFistPct, Factor()));
        spec.weakened = Tune::kFistWeakened;
        spec.callEmoteGroup = EMOTE_HMB_FIST;
        // Called by the machine inside Call and Update (inside OnUpdate or a `.dbtest`): `this` outlives it.
        spec.onNumber = [this](uint32 index, Position const& /*kitLabel*/) { PlaceNumeral(index); };
        return spec;
    }

    GnomereganMachines::ComboExtras FistExtras()
    {
        GnomereganMachines::ComboExtras extras;
        extras.spellIds.fill(SPELL_HMB_FIST_HIT);
        extras.tags.fill(TAG_HMB_FIST);
        extras.names = kFistShapeNames;
        extras.school = uint8(SPELL_SCHOOL_NORMAL);
        extras.callColor = BossMechanics::Color::Yellow;
        ObjectGuid const fist = _fist;
        extras.onStrike = [fist](Creature* owner, uint32 /*index*/, GnomereganMachines::Punch const& /*punch*/)
        {
            if (Creature* body = owner ? owner->GetMap()->GetCreature(fist) : nullptr)
                body->HandleEmoteCommand(kFistEmote);
        };
        extras.onEnd = [this](Creature* owner, uint32 punches, uint32 landed)
        {
            LogSchematics("fist-end", Acore::StringFormat("face={} punches={} landed={}", _fistFace + 1, punches,
                landed));
            EndCombinationUnits(owner);
        };
        return extras;
    }

    // MT24: one combination from `faceWanted` (else a random face, open or shut: ruling 68).
    bool StartCombination(ThermapluggFight& fight, std::optional<uint32> faceWanted, char const* why)
    {
        Creature* boss = fight.Boss();
        if (_ended || !boss || !boss->IsAlive() || !boss->IsInWorld() || (_combo && _combo->Running()))
            return false;
        EndCombinationUnits(boss);
        uint32 const face = faceWanted ? *faceWanted % kFaceCount : RollFace(RandBelow);
        std::vector<Shape> const shapes = RollFistChain(RandBelow);
        _fistFace = face;
        _fistShapes = shapes;
        uint32 const lastStrike = FistStrikeMs(shapes.size() - 1);

        // The fist behind the face, winding up (the punch pose's precast for the 4 s), and the face's glow.
        Point3 const body = FistSpot(face);
        if (Creature* fist = fight.Summon(NPC_PUMMELERS_FIST, Position(body.x, body.y, body.z, body.o),
            lastStrike + Tune::kFistLingerMs))
        {
            _fist = fist->GetGUID();
            fist->CastSpell(fist, SPELL_HMB_FIST_WIND_UP, false);
        }
        if (Creature* stalker = fight.FaceStalker(face))
        {
            stalker->CastSpell(stalker, SPELL_HMB_FACE_LIGHT, true);
            _litStalker = stalker->GetGUID();
        }

        // A new machine on the face's frame, its percents at this moment's Voltage factor.
        if (_combo)
            _combo->Clear();
        _combo = GnomereganMachines::MakeComboMachine(Owner(boss), FistSpec(face), FistExtras());
        std::vector<GnomereganMachines::Punch> chain;
        std::string names;
        for (Shape const s : shapes)
        {
            GnomereganMachines::Punch p;
            p.shape = ToPunch(s);
            chain.push_back(p);
            names += (names.empty() ? "" : ",") + std::string(kFistShapeNames[static_cast<std::size_t>(s)]);
        }
        uint32 const length = _combo->Call(chain);
        if (!length)
        {
            LogSchematics("fist-refused", Acore::StringFormat("face={} why={}", face + 1, why));
            EndCombinationUnits(boss);
            return false;
        }
        ++_combinations;
        LogSchematics("fist", Acore::StringFormat("n={} face={} open={} shapes={} pct={:.1f} last-strike={}ms why={}",
            _combinations, face + 1, fight.FaceOpen(face) ? 1 : 0, names, Scaled(Tune::kFistPct, Factor()), length,
            why));
        return true;
    }

    // The numeral of punch `index` (1-based) on its shape's floor until its strike (V's quads on a light stalker).
    void PlaceNumeral(uint32 index)
    {
        Creature* boss = _fight ? _fight->Boss() : nullptr;
        if (!boss || index == 0 || index > _fistShapes.size() || index > kNumeralDisplays.size())
            return;
        Vec2 const p = FistLabel(_fistFace, _fistShapes[index - 1]);
        float const z = FloorZ(boss, p, kRoomCenter.z);
        DungeonKit::ComboFrame const frame = FistFrame(_fistFace);
        if (Creature* numeral = _fight->Summon(NPC_LIGHT_STALKER, Position(p.x, p.y, z, frame.facing),
            FistStrikeMs(index - 1)))
        {
            numeral->SetDisplayId(kNumeralDisplays[index - 1], Tune::kNumeralScale);
            _numerals.push_back(numeral->GetGUID());
        }
    }

    // The fist, the numerals and the face's glow go (a combination's end, a new one, the fight's end).
    void EndCombinationUnits(Creature* boss)
    {
        Map* map = boss ? boss->GetMap() : _map;
        if (map)
        {
            if (Creature* fist = map->GetCreature(_fist))
                fist->DespawnOrUnsummon();
            for (ObjectGuid const& guid : _numerals)
                if (Creature* numeral = map->GetCreature(guid))
                    numeral->DespawnOrUnsummon();
            if (Creature* stalker = map->GetCreature(_litStalker))
                stalker->RemoveAurasDueToSpell(SPELL_HMB_FACE_LIGHT);
        }
        _fist.Clear();
        _numerals.clear();
        _litStalker.Clear();
    }

    ThermapluggFight* _fight = nullptr;
    Map* _map = nullptr;
    std::array<bool, kSchematicCount> _loaded{};
    std::unique_ptr<GnomereganMachines::ElectroVoltageMeter> _voltage;
    std::unique_ptr<GnomereganMachines::AlertLightsMachine> _lights;
    std::unique_ptr<GnomereganMachines::ComboMachine> _combo;
    uint64 _fistAt = 0;
    uint32 _fistFace = 0;
    std::vector<Shape> _fistShapes;
    ObjectGuid _fist;
    ObjectGuid _litStalker;
    std::vector<ObjectGuid> _numerals;
    uint32 _combinations = 0;
    uint32 _spotted = 0;
    uint32 _facesOpened = 0;
    uint32 _voltsPeak = 0;
    bool _ended = false;
};

// ---------------------------------------------------------------------------------------------------------------------
// npc_gnomer_pummelers_fist (301136): the Pummeler's body behind a Gnome Face (V gap 12: no hands-only model), not
// attackable, held still with gravity off (the face's alcove has no floor to stand on). The package drives its pose.
// ---------------------------------------------------------------------------------------------------------------------

struct npc_gnomer_pummelers_fist : public ScriptedAI
{
    explicit npc_gnomer_pummelers_fist(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        Hold();
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void EnterEvadeMode(EvadeReason /*why*/) override { }

    void UpdateAI(uint32 diff) override
    {
        if (_holdInMs > diff)
        {
            _holdInMs -= diff;
            return;
        }
        _holdInMs = kHoldEveryMs;
        Hold();
    }

private:
    static uint32 constexpr kHoldEveryMs = 1000;

    void Hold()
    {
        me->SetReactState(REACT_PASSIVE);
        me->SetDisableGravity(true);
        if (!me->HasUnitState(UNIT_STATE_ROOT))
            me->SetControlled(true, UNIT_STATE_ROOT);
    }

    uint32 _holdInMs = kHoldEveryMs;
};

// ---------------------------------------------------------------------------------------------------------------------
// `.dbtest gnomer schematics <subcommand>`
// ---------------------------------------------------------------------------------------------------------------------

namespace
{
    struct GmSchematics
    {
        ThermapluggFight* fight = nullptr;
        SchematicsHardMode* package = nullptr;
    };

    GmSchematics FindSchematics(ChatHandler* handler)
    {
        Player* gm = handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
        if (!gm || !GnomerTest::RequireGnomeregan(handler))
            return {};
        GmSchematics out;
        out.fight = GnomerThermaplugg::FindThermapluggFight(gm->GetMap());
        if (!out.fight)
        {
            handler->SendErrorMessage("{}", "Thermaplugg is not in his fight (pull him first).");
            return {};
        }
        out.package = SchematicsHardMode::Find(gm->GetMap());
        if (!out.package)
        {
            handler->SendErrorMessage("{}", "No Whole Workshop on this pull: the hard mode was not armed (heroic, "
                "`.dbtest gnomer hardmode arm` before his pull).");
            return {};
        }
        return out;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return GnomerTest::ShowBossInfo(handler, NPC_THERMAPLUGG, BOSS_WHOLE_WORKSHOP);
    }

    bool HandleState(ChatHandler* handler)
    {
        GmSchematics const s = FindSchematics(handler);
        if (!s.package)
            return false;
        handler->PSendSysMessage("Schematics B: {}", s.package->Describe());
        return true;
    }

    // MT15: load one schematic now (`electro`, `alert`, `pummeler`), or `all`, whatever his health.
    bool HandleLoad(ChatHandler* handler, std::string which)
    {
        GmSchematics const s = FindSchematics(handler);
        if (!s.package)
            return false;
        std::vector<Schematic> wanted;
        if (which == "all")
            wanted = { Schematic::Electrocutioner, Schematic::AlertSystem, Schematic::Pummeler };
        else if (std::optional<Schematic> const one = SchematicOfKey(which))
            wanted.push_back(*one);
        else
        {
            handler->SendErrorMessage("{}", "Load what? electro, alert, pummeler or all.");
            return false;
        }
        for (Schematic const w : wanted)
            handler->PSendSysMessage("Schematic {}: {}", kSchematicKeys[SchematicIndex(w)],
                s.package->Load(*s.fight, w, "gm") ? "loaded" : "loaded already (or he is gone)");
        return true;
    }

    // MT21: +n volts (default 1).
    bool HandleVoltage(ChatHandler* handler, Optional<uint32> volts)
    {
        GmSchematics const s = FindSchematics(handler);
        if (!s.package)
            return false;
        GnomereganMachines::ElectroVoltageMeter* meter = s.package->Voltage();
        if (!meter)
        {
            handler->SendErrorMessage("{}", "The Electrocutioner schematic is not loaded (`load electro`).");
            return false;
        }
        handler->PSendSysMessage("Voltage: {} stacks.", meter->Add(volts.value_or(1), "gm"));
        return true;
    }

    // MT22: the meter to the next Electric Justice now.
    bool HandleJustice(ChatHandler* handler)
    {
        GmSchematics const s = FindSchematics(handler);
        if (!s.package)
            return false;
        GnomereganMachines::ElectroVoltageMeter* meter = s.package->Voltage();
        if (!meter)
        {
            handler->SendErrorMessage("{}", "The Electrocutioner schematic is not loaded (`load electro`).");
            return false;
        }
        if (meter->JusticeRunning())
        {
            handler->SendErrorMessage("{}", "Electric Justice is running already.");
            return false;
        }
        uint32 const missing = meter->ToNext();
        if (missing)
            meter->Add(missing, "gm");
        handler->PSendSysMessage("Voltage: {} stacks; Electric Justice on the next tick.", meter->Stacks());
        return true;
    }

    // MT23: the selected player (else yourself) Spotted now, through the lights' latch.
    bool HandleSpot(ChatHandler* handler)
    {
        GmSchematics const s = FindSchematics(handler);
        Player* who = handler->GetSession() ? handler->getSelectedPlayerOrSelf() : nullptr;
        if (!s.package || !who)
            return false;
        GnomereganMachines::AlertLightsMachine* lights = s.package->Lights();
        if (!lights)
        {
            handler->SendErrorMessage("{}", "The Alert System schematic is not loaded (`load alert`).");
            return false;
        }
        if (!lights->Spot(who, GnomereganMachines::SpotSource::Script))
        {
            handler->SendErrorMessage("{}", "Not spotted (the 3 s latch, a game master, or dead).");
            return false;
        }
        handler->PSendSysMessage("Spotted: {}.", who->GetName());
        return true;
    }

    // MT24: a fist combination now, from face 1-6 (else a random one).
    bool HandleFist(ChatHandler* handler, Optional<uint32> face)
    {
        GmSchematics const s = FindSchematics(handler);
        if (!s.package)
            return false;
        if (face && (*face < 1 || *face > kFaceCount))
        {
            handler->SendErrorMessage("{}", "Face 1 to 6.");
            return false;
        }
        std::string const error = s.package->Fist(*s.fight, face ? std::optional<uint32>(*face - 1) : std::nullopt);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("{}", "The fist winds up (4 s to the first punch).");
        return true;
    }

    ChatCommandTable const& SchematicsTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",    HandleInfo,    SEC_GAMEMASTER, Console::No },
            { "state",   HandleState,   SEC_GAMEMASTER, Console::No },
            { "load",    HandleLoad,    SEC_GAMEMASTER, Console::No },
            { "voltage", HandleVoltage, SEC_GAMEMASTER, Console::No },
            { "justice", HandleJustice, SEC_GAMEMASTER, Console::No },
            { "spot",    HandleSpot,    SEC_GAMEMASTER, Console::No },
            { "fist",    HandleFist,    SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_thermaplugg_hard_mode_machines()
{
    GnomerThermaplugg::RegisterThermapluggHardMode(GnomerThermaplugg::HardModePackage::SchematicsB,
        [](ThermapluggFight& fight)
        {
            return std::make_unique<SchematicsHardMode>(fight);
        });
    RegisterDungeonReworkCreatureAI(npc_gnomer_pummelers_fist, GnomereganRework::kInstanceScriptName);
    GnomerTest::RegisterBoss("schematics", SchematicsTestCommands());
}
