/*
 * mod-dungeon-bosses, Gnomeregan D6Ha: the Whole Workshop, part a (Mekgineer Thermaplugg's heroic hard mode; SP
 * 1738-1864, rulings 43-53; handoff section 3.5 row D6Ha, 3.7). The pure rules and numbers are
 * ThermapluggHardModeLogic.h (GnomerWorkshop); the hooks are D6's ThermapluggFight.h; the machines are D1's Duplicator
 * and D2's DoseField (GnomereganMachines.h).
 *
 *   go_gnomer_clearance_console   GO 301382 (the S0 rev spawns it on heroic only): the Prismatic Punch Card in the
 *                                 bags, heroic, out of combat, Thermaplugg neither fighting nor dead, a confirmation
 *                                 (the gossip option's box); the card is read and kept. Sets DATA_HARD_MODE (the
 *                                 instance checks again and saves it; it holds through wipes). A bot gets no menu
 *                                 (rule 34). Lit (GO state active) while the flag is set.
 *   SchematicsA                   the package (HardModePackage::SchematicsA), made at his armed pull by D6:
 *     MT15  the yell (7800 line 9) on the first schematic (90%) and the console's line "Loading schematic: TECHBOT"
 *           / "VISCOUS FALLOUT" (a raid boss emote from him over the room, D6Hb's form; D6Hb says its own three);
 *     MT16  90%: walking bombs duplicate (D1's Duplicator: alive 10 s, a 2 s Nature bar, every 10 s, no cap); the copy
 *           becomes D6's bomb through AdoptBomb at the source's health; bots kill a casting bomb first and kick it;
 *     MT17  75%: venting, 1 dose to every player in the room per open face every 8 s, green vapor (a vent stalker
 *           301138) at each open face;
 *     MT18  the hard mode dose (D2's DoseField on SPELL_HM_IRRADIATED: +3% done, healing done and taken a stack,
 *           never drains); a plate touch halves it (DoseField::Halve, D2's one rule); the bots' plate rule:
 *           D6's own plate Soak (one exclusive group) takes the dose ordering, and every bot at 8 or more is sent
 *           to its nearest lit plate first (PlanPlates, D6's SetPlatePlan; F-1d, STAGE-R-1-C Minor-1 and DQ1);
 *     MT19  Leaking at 10: a Wandering Puddle (301135) every 10 s at the carrier's feet: forms in 1.5 s, drifts at
 *           2 yd/s turning at the walls (its own AI), 4 yd, 2 min; inside: 8% and 1 dose a second (judged by script,
 *           once a second however many overlap); the bots see a lasting zone that follows the puddle;
 *     MT20  Meltdown at 20: a lasting 6 yd Spread on the carrier (5% a second to the others) and the carrier's own 5%;
 *     MT25  the Reactor Leak: the alarm at 2 min, 1 min, 30 s and 10 s left, then from 180 s 10% of the reference row
 *           a second to every player on his threat list (s7 #35 A), multiplied by the dose; a green screen.
 *   npc_gnomer_wandering_puddle   301135: the drift.
 *   npc_gnomer_workshop_stalker   301137 the room alarm, 301138 the vent stalker and the Leak's disc: inert.
 *
 * Cleanup (RB-1): OnEnd (first in D6's cleanup: a wipe, an evade or his death) clears both machines, the plate plan,
 * the puddles and their zones, the Meltdown spreads, every handle, the stalkers and every aura of the package; D6's
 * summons.DespawnAll then catches anything left. Nothing is saved: a reload or a restart resets him (Reset) and the
 * next armed pull builds a new package; the console relights from the instance's saved flag.
 *
 * Mirrored code (AGENTS.md credit rule): none. The DoseField callbacks and the Meltdown spread follow D2's
 * boss_viscous_fallout_rework.cpp (this build), the console D16's go_brd_activation_console (this repository).
 */

#include "Chat.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "DungeonKitSoaks.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "GnomereganKit.h"
#include "GnomereganMachines.h"
#include "GnomereganRework.h"
#include "GnomereganTestCommand.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MechanicDescriptor.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "ScriptedGossip.h"
#include "SharedDefines.h"
#include "StringFormat.h"
#include "ThermapluggFight.h"
#include "ThermapluggHardModeLogic.h"
#include "ThermapluggLogic.h"
#include "WorldSession.h"
#include <array>
#include <map>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

using namespace Acore::ChatCommands;
using namespace GnomereganRework;
using namespace GnomerWorkshop;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using GnomerThermaplugg::ThermapluggFight;

namespace
{
    char const* const kKey = "workshop";
    uint8 constexpr kSchoolNature = SPELL_SCHOOL_NATURE;
    uint32 constexpr kPuddlePoint = 1;
    std::size_t constexpr kLiveTrimAt = 256;      // the oldest handles resolved long ago: drop kLiveTrimDrop
    std::size_t constexpr kLiveTrimDrop = 128;

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(static_cast<int64>(ms));
    }

    Position ToPos(Point3 const& p)
    {
        return Position(p.x, p.y, p.z, p.o);
    }

    bool Alive(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    // Rule 34: bots never use the console. A playerbot session is built without a socket (mod-playerbots creates
    // every bot's WorldSession with a null socket), so a session with no open socket is a bot.
    bool IsBotPlayer(Player const* player)
    {
        WorldSession* session = player ? player->GetSession() : nullptr;
        return !session || session->IsSocketClosed();
    }

    void Log(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kKey, mechanic, detail);
    }

    // The console's verdict for `player` now (GnomereganRework.h ConsoleCheck; the instance checks again on the Set).
    ConsoleVerdict ConsoleVerdictFor(Player* player)
    {
        InstanceScript* instance = GnomereganInstance(player);
        if (!instance)
            return CONSOLE_NOT_HEROIC;
        return ConsoleCheck(DungeonKit::IsHeroicMap(player), IsBotPlayer(player), player->IsInCombat(),
            player->HasItemCount(ITEM_PRISMATIC_PUNCH_CARD, 1, false), SlotState(instance, BOSS_THERMAPLUGG),
            instance->GetData(DATA_HARD_MODE));
    }

    // Thermaplugg's slot is DONE (the refusal's text: he is dead, not fighting).
    bool ThermapluggDone(Player* player)
    {
        InstanceScript* instance = player ? GnomereganInstance(player) : nullptr;
        return instance && SlotState(instance, BOSS_THERMAPLUGG) == DungeonKit::State::Done;
    }

    // The console's accept (the gossip option, `.dbtest gnomer workshop console`): the checks, the flag, the screen.
    ConsoleVerdict ArmFromConsole(Player* player, char const* how)
    {
        if (!player)
            return CONSOLE_NOT_HEROIC;
        ConsoleVerdict const verdict = ConsoleVerdictFor(player);
        if (verdict != CONSOLE_ACCEPTED)
        {
            if (verdict != CONSOLE_BOT)
                ChatHandler(player->GetSession()).SendNotification(
                    std::string_view(ConsoleRefusalText(verdict, ThermapluggDone(player))));
            Log("console-refused", Acore::StringFormat("player={} verdict={} how={}", player->GetName(),
                uint32(verdict), how));
            return verdict;
        }
        InstanceScript* instance = GnomereganInstance(player);
        instance->SetData(DATA_HARD_MODE, 1);
        if (!instance->GetData(DATA_HARD_MODE))
        {
            Log("console-refused", Acore::StringFormat("player={} the instance refused the flag how={}",
                player->GetName(), how));
            return CONSOLE_BOSS_ENGAGED;
        }
        instance->DoSendNotifyToInstance("%s", kConsoleAccepted);
        Log("console", Acore::StringFormat("accepted player={} how={} (the card is kept)", player->GetName(), how));
        return CONSOLE_ACCEPTED;
    }

    class SchematicsA;

    // `.dbtest gnomer workshop` finds the running package by Thermaplugg's guid (map threads register, the command
    // reads: one lock).
    std::mutex& RunningLock()
    {
        static std::mutex lock;
        return lock;
    }

    std::unordered_map<uint64, SchematicsA*>& Running()
    {
        static std::unordered_map<uint64, SchematicsA*> running;
        return running;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The package: the Techbot and Viscous Fallout schematics, MT15's lines, the Reactor Leak
    // ----------------------------------------------------------------------------------------------------------------
    class SchematicsA final : public GnomerThermaplugg::ThermapluggHardMode
    {
    public:
        explicit SchematicsA(ThermapluggFight& fight)
            : _fight(fight), _bounds(ThermapluggFloorBounds())
        {
            if (Creature* boss = fight.Boss())
                _boss = boss->GetGUID();
            std::lock_guard<std::mutex> guard(RunningLock());
            Running()[_boss.GetRawValue()] = this;
        }

        ~SchematicsA() override
        {
            Unregister();
        }

        // ---- the hooks ----------------------------------------------------------------------------------------------

        void OnEngage(ThermapluggFight& fight) override
        {
            Creature* boss = fight.Boss();
            if (Creature* alarm = fight.Summon(NPC_ROOM_ALARM, ToPos(kConsoleSpot)))
                _alarm = alarm->GetGUID();
            fight.Log("hardmode=1", Acore::StringFormat("health={} package=a schematics=techbot,fallout leak={}s",
                boss ? boss->GetMaxHealth() : 0, Tune::kLeakStartMs / 1000));
        }

        void OnUpdate(ThermapluggFight& fight, uint32 diff) override
        {
            Creature* boss = fight.Boss();
            if (!boss || !boss->IsAlive())
                return;
            uint64 const now = fight.ClockMs();
            if (_dup)
                _dup->Update(diff);
            if (_dose)
            {
                _dose->Update(diff);
                SyncFaces();
                PlanPlates(diff, false);
                UpdateVenting(now);
                UpdatePuddles(diff, now);
                UpdateCarriers(diff);
            }
            UpdateLeak(now);
            if (_live.size() > kLiveTrimAt)
                _live.erase(_live.begin(), _live.begin() + kLiveTrimDrop);
        }

        std::vector<float> HealthThresholds() const override
        {
            return { kSchematicPct.begin(), kSchematicPct.end() };
        }

        void OnHealthPct(ThermapluggFight& /*fight*/, float pct) override
        {
            std::optional<Schematic> const s = SchematicAt(pct);
            if (!s)
                return;
            Load(*s, "health");
        }

        void OnFaceOpened(ThermapluggFight& /*fight*/, uint32 /*face*/, char const* /*why*/) override
        {
            if (_dose)
                SyncFaces();
        }

        void OnFaceShut(ThermapluggFight& /*fight*/, uint32 /*face*/, Player* /*by*/) override
        {
            if (_dose)
                SyncFaces();
        }

        // MT18: the touch halves the dose (D2's rule; the machine logs it).
        void OnPlateTouched(ThermapluggFight& /*fight*/, Player* player, uint32 face) override
        {
            if (!_dose || !player)
                return;
            ++_halves;
            uint32 const after = _dose->Halve(player, face < kFaceCount ? kPlateWhy[face] : "plate");
            (void)after;
        }

        // MT16: every walking bomb D6 builds after the Techbot schematic loaded (a copy is the machine's already).
        void OnBombSpawned(ThermapluggFight& /*fight*/, Creature* bomb, GnomerThermaplugg::BombType /*type*/,
            bool copy) override
        {
            if (_dup && bomb && !copy)
                _dup->Track(bomb);  // the spec's entries filter The Big One out
        }

        void OnBombGone(ThermapluggFight& /*fight*/, ObjectGuid bomb, char const* /*why*/) override
        {
            if (_dup)
                _dup->Forget(bomb);
        }

        void OnEnd(ThermapluggFight& fight, bool won) override
        {
            Creature* boss = fight.Boss();
            if (_dup)
                _dup->Clear();
            _dup.reset();
            if (_dose)
                _dose->Clear();
            _dose.reset();
            _plan.clear();
            for (Puddle const& p : _puddles)
            {
                Cancel(boss, p.ring);
                Despawn(boss, p.guid);
            }
            _puddles.clear();
            for (auto const& [raw, handle] : _meltdown)
                Cancel(boss, handle);
            _meltdown.clear();
            for (MechanicHandle const& handle : _live)
                Cancel(boss, handle);
            _live.clear();
            for (ObjectGuid& vent : _vents)
            {
                Despawn(boss, vent);
                vent.Clear();
            }
            Despawn(boss, _alarm);
            Despawn(boss, _leakDisc);
            _alarm.Clear();
            _leakDisc.Clear();
            if (InstanceScript* instance = fight.Instance())
                for (uint32 const spell : { uint32(SPELL_HM_IRRADIATED), uint32(SPELL_HM_DOSE_GLOW),
                        uint32(SPELL_HM_MELTDOWN_AURA), uint32(SPELL_HM_LEAK_AURA) })
                    instance->DoRemoveAurasDueToSpellOnPlayers(spell);
            _glowing.clear();
            _geiger.clear();
            Log("end", Acore::StringFormat("won={} loaded={} copies={} vents={} halves={} puddles={} leak_ticks={}", won
                ? 1 : 0, LoadedNames(), _copies, _ventPulses, _halves, _puddlesDropped, _leakTicks));
            _loaded.fill(false);
            _leakOn = false;
            Unregister();
        }

        // SP Bots: a bomb casting Duplication is the ranged's first kill (unless a player stands in its blast: D6's
        // hold), its bar is on the kick list (a reward: a stun stops it too); the package's units are never targets.
        void DescribeExtra(ThermapluggFight& /*fight*/, BossMechanics::Descriptor& d) override
        {
            using BossMechanics::Condition;
            using BossMechanics::TargetEntry;
            using BossMechanics::Who;
            for (uint32 const entry : GnomerThermaplugg::kWalkingBombEntries)
            {
                d.interrupts.emplace_back(entry, SPELL_HM_DUPLICATION, Tune::kDupKickPriority);
                // Captures nothing (a Custom condition may run on a bot's copy): the id is a constant.
                d.targets.push_back(TargetEntry(entry, Tune::kCastingBombPriority, Who::Ranged, Condition::AllOf({
                    Condition::Custom([](Unit const* unit)
                    {
                        return unit->FindCurrentSpellBySpellId(SPELL_HM_DUPLICATION) != nullptr;
                    }),
                    Condition::Not(Condition::NearPlayer(GnomerThermaplugg::Tune::kBombBlastYd)) })));
            }
            for (uint32 const entry : { uint32(NPC_WANDERING_PUDDLE), uint32(NPC_ROOM_ALARM),
                    uint32(NPC_VENT_STALKER) })
                d.ignores.emplace_back(entry);
        }

        std::string Describe() const override
        {
            std::string plan;
            for (uint32 const face : _plan)
                plan += Acore::StringFormat("{}{}", plan.empty() ? "" : ",", face + 1);
            return Acore::StringFormat("workshop-a loaded={} dup=[{}] dose=[{}] vents={} plates=[{}]{} puddles={} "
                "meltdown={} leak={} alarms={:#x} copies={} halves={}", LoadedNames(),
                _dup ? _dup->Describe() : std::string("-"), _dose ? _dose->Describe() : std::string("-"),
                VentCount(), plan, _tankLast ? "" : " tank-sheds", _puddles.size(), _meltdown.size(), _leakOn ? 1 : 0,
                uint32(_alarmFired), _copies, _halves);
        }

        // ---- `.dbtest gnomer workshop` ------------------------------------------------------------------------------

        bool TestLoad(Schematic s)
        {
            return Load(s, "gm");
        }

        bool TestVent()
        {
            if (!_dose)
                return false;
            Vent(_fight.ClockMs());
            return true;
        }

        bool TestDose(Player* player, uint32 dose)
        {
            if (!_dose || !Alive(player))
                return false;
            _dose->Set(player, dose, "gm");
            return true;
        }

        bool TestPuddle(Position const& at)
        {
            return DropPuddle(at, "gm");
        }

        void TestLeak()
        {
            _alarmFired = 0x0F;
            StartLeak(_fight.ClockMs(), "gm");
        }

        void TestAlarm(uint8 group)
        {
            AlarmSay(group);
        }

    private:
        struct Puddle
        {
            ObjectGuid guid;
            uint64 bornMs = 0;
            MechanicHandle ring;
        };

        static constexpr std::array<char const*, kFaceCount> kPlateWhy{ {
            "plate-1", "plate-2", "plate-3", "plate-4", "plate-5", "plate-6" } };

        void Unregister()
        {
            std::lock_guard<std::mutex> guard(RunningLock());
            auto it = Running().find(_boss.GetRawValue());
            if (it != Running().end() && it->second == this)
                Running().erase(it);
        }

        void Cancel(Creature* boss, MechanicHandle handle)
        {
            if (boss && handle)
                Mechanic::Cancel(boss, handle);
        }

        void Despawn(Creature* boss, ObjectGuid guid)
        {
            if (!boss || guid.IsEmpty() || !boss->IsInWorld())
                return;
            if (Creature* unit = boss->GetMap()->GetCreature(guid))
                unit->DespawnOrUnsummon();
        }

        Creature* Find(ObjectGuid guid) const
        {
            Creature* boss = _fight.Boss();
            return boss && !guid.IsEmpty() && boss->IsInWorld() ? boss->GetMap()->GetCreature(guid) : nullptr;
        }

        std::string LoadedNames() const
        {
            std::string out;
            for (std::size_t i = 0; i < kSchematicCount; ++i)
                if (_loaded[i])
                    out += (out.empty() ? "" : ",") + std::string(kSchematicKeys[i]);
            return out.empty() ? "-" : out;
        }

        uint32 VentCount() const
        {
            uint32 n = 0;
            for (ObjectGuid const& vent : _vents)
                n += vent.IsEmpty() ? 0 : 1;
            return n;
        }

        void AlarmSay(uint8 group)
        {
            if (Creature* alarm = Find(_alarm); alarm && alarm->IsAIEnabled)
                alarm->AI()->Talk(group);
        }

        // ---- MT15 ---------------------------------------------------------------------------------------------------

        // The yell on the first schematic (part a's 90%), the console's line on each of part a's two (D6Hb's form).
        void Announce(Creature* boss, Schematic s)
        {
            if (!_yelled)
            {
                _yelled = true;
                _fight.Say(SAY_HM_SCHEMATIC);
            }
            boss->Talk(LoadLine(s), CHAT_MSG_RAID_BOSS_EMOTE, LANG_UNIVERSAL, Tune::kConsoleLineYd, nullptr);
        }

        bool Load(Schematic s, char const* why)
        {
            std::size_t const i = std::size_t(s);
            if (i >= kSchematicCount || _loaded[i])
                return false;
            Creature* boss = _fight.Boss();
            if (!boss)
                return false;
            GnomereganMachines::MachineOwner const owner{ boss, kKey, true };
            if (s == Schematic::Techbot)
            {
                GnomereganMachines::DuplicatorSpec spec;
                spec.barSpellId = SPELL_HM_DUPLICATION;
                spec.castMs = Tune::kDupCastMs;
                spec.firstAfterMs = Tune::kDupFirstMs;
                spec.repeatMs = Tune::kDupRepeatMs;
                spec.capAlive = Tune::kDupCapAlive;
                spec.entries.assign(GnomerThermaplugg::kWalkingBombEntries.begin(),
                    GnomerThermaplugg::kWalkingBombEntries.end());
                // The machine is this package's member and is cleared in OnEnd, so its callback may hold `this`.
                spec.onCopy = [this](Creature* source, Creature* copy) { OnCopy(source, copy); };
                _dup = GnomereganMachines::MakeDuplicator(owner, std::move(spec));
                // The bombs already walking start their life clock now.
                for (ObjectGuid const& guid : _fight.Bombs())
                    if (Creature* bomb = Find(guid); bomb && bomb->IsAlive())
                        _dup->Track(bomb);
            }
            else
            {
                GnomereganMachines::DoseSpec spec;
                spec.auraSpellId = SPELL_HM_IRRADIATED;
                spec.drainEveryMs = 0;              // it never drains (SP 1786)
                spec.capAt = 0;
                spec.leakAt = Tune::kLeakAt;
                spec.leakEveryMs = Tune::kLeakEveryMs;
                spec.onLeak = [this](Player* /*player*/, Position const& at) { DropPuddle(at, "leaking"); };
                spec.meltdownAt = Tune::kMeltdownAt;
                spec.onMeltdown = [this](Player* player, bool on) { Meltdown(player, on); };
                _dose = GnomereganMachines::MakeDoseField(owner, std::move(spec));
                _ventDueMs = _fight.ClockMs() + Tune::kVentEveryMs;
                SyncFaces();
                PlanPlates(0, true);
            }
            _loaded[i] = true;
            Announce(boss, s);
            Log("load", Acore::StringFormat("name={} why={} bombs={} open={}", kSchematicKeys[i], why,
                _fight.Bombs().size(), GnomerThermaplugg::OpenCount(_fight.OpenFaces())));
            return true;
        }

        // ---- MT16 ---------------------------------------------------------------------------------------------------

        // The copy becomes D6's bomb (the source's type, mark and health); one D6 refuses goes at once.
        void OnCopy(Creature* source, Creature* copy)
        {
            if (!copy)
                return;
            if (source && _fight.AdoptBomb(source, copy))
            {
                ++_copies;
                return;
            }
            if (_dup)
                _dup->Forget(copy->GetGUID());
            copy->DespawnOrUnsummon();
            Log("copy-refused", Acore::StringFormat("source={} copy={}", source ? source->GetGUID().ToString() : "-",
                copy->GetGUID().ToString()));
        }

        // ---- MT17, MT18: the vents and the plates' dose rule --------------------------------------------------------

        void SyncFaces()
        {
            Creature* boss = _fight.Boss();
            if (!boss)
                return;
            bool const fallout = _dose != nullptr;
            for (uint32 face = 0; face < kFaceCount; ++face)
            {
                Creature* vent = Find(_vents[face]);
                bool const ventWanted = VentWanted(fallout, _fight.FaceOpen(face));
                if (ventWanted && !vent)
                {
                    if (Creature* made = _fight.Summon(NPC_VENT_STALKER, _fight.FaceMouth(face)))
                    {
                        made->AddAura(SPELL_HM_VENT, made);
                        _vents[face] = made->GetGUID();
                    }
                }
                else if (!ventWanted && vent)
                {
                    vent->DespawnOrUnsummon();
                    _vents[face].Clear();
                }
                else if (!vent)
                    _vents[face].Clear();
            }
        }

        // MT18 (F-1d, STAGE-R-1-C Minor-1 and DQ1): D6's plates are the one exclusive group; while the Fallout
        // schematic runs they take the dose ordering (the highest dose first, no floor: a bot under 8 still presses
        // plates, SP MT4; the tank last unless it is the only one at 8 or more) and the serve order that sends every
        // bot at 8 or more to its nearest lit plate (PlatePlan). Again every kPlatePlanMs; D6 does nothing when
        // neither changed.
        void PlanPlates(uint32 diff, bool now)
        {
            Creature* boss = _fight.Boss();
            _planMs += diff;
            if (!boss || (!now && _planMs < Tune::kPlatePlanMs))
                return;
            _planMs = 0;
            BossMechanics::RoleProvider const& roles = BossMechanics::GetRoleProvider();
            std::vector<PlatePlayer> players;
            for (Player* player : _fight.FightPlayers())
            {
                PlatePlayer p;
                p.guid = player->GetGUID().GetRawValue();
                p.dose = player->GetAuraCount(SPELL_HM_IRRADIATED);     // BM's Ordering reads the same count
                p.bot = IsBotPlayer(player);
                p.tank = roles.Get(boss, player) == BossMechanics::Role::Tank;
                p.eligible = !_fight.LockedOut(player);
                p.at = DungeonKit::PlaneOf(player);
                players.push_back(p);
            }
            std::vector<LitPlate> plates;
            for (uint32 face = 0; face < kFaceCount; ++face)
                if (_fight.PlateLit(face))
                    if (Creature* anchor = _fight.PlateAnchor(face))
                        plates.push_back({ face, DungeonKit::PlaneOf(anchor),
                            GnomerThermaplugg::PlateRank(_fight.FightMode(), face) });
            bool const tankLast = TankPlatesLast(players);
            BossMechanics::Ordering order;
            order.auraSpell = SPELL_HM_IRRADIATED;
            order.ascending = false;        // the highest dose first
            order.roleLast = tankLast ? BossMechanics::Role::Tank : BossMechanics::Role::None;
            _plan = PlatePlan(std::move(plates), players, tankLast);
            _tankLast = tankLast;
            _fight.SetPlatePlan(order, _plan, PlatePlanBots(players, tankLast));
        }

        void UpdateVenting(uint64 now)
        {
            if (now < _ventDueMs)
                return;
            _ventDueMs = GnomerThermaplugg::NextDue(_ventDueMs, Tune::kVentEveryMs, now);
            Vent(now);
        }

        // MT17: one pulse, 1 dose a player per open face.
        void Vent(uint64 now)
        {
            uint32 const open = GnomerThermaplugg::OpenCount(_fight.OpenFaces());
            uint32 const doses = VentDoses(open);
            if (!doses)
                return;
            std::vector<Player*> const players = _fight.FightPlayers();
            for (Player* player : players)
                _dose->Add(player, int32(doses), "vent");
            ++_ventPulses;
            Log("vent", Acore::StringFormat("open={} doses={} players={} at={}", open, doses, players.size(), now));
        }

        // ---- MT19 the Wandering Puddles -----------------------------------------------------------------------------

        bool DropPuddle(Position const& at, char const* why)
        {
            Creature* boss = _fight.Boss();
            if (!boss)
                return false;
            Creature* puddle = _fight.Summon(NPC_WANDERING_PUDDLE, at, Tune::kPuddleFormMs + Tune::kPuddleLifeMs);
            if (!puddle)
                return false;
            Puddle p;
            p.guid = puddle->GetGUID();
            p.bornMs = _fight.ClockMs();
            // The bots' lasting zone rides the puddle (an anchor unit); it draws and steers, the script judges.
            MechanicRef ring = Mechanic::Circle(boss, puddle, Tune::kPuddleYd, Ms(Tune::kPuddleFormMs));
            if (ring.IsValid())
            {
                ring.Persistent(Ms(Tune::kPuddleLifeMs), Ms(0)).ZTolerance(Tune::kPuddleZBandYd).Within(_bounds)
                    .Tag(TAG_HM_PUDDLE);
                p.ring = ring.Handle();
            }
            _puddles.push_back(p);
            ++_puddlesDropped;
            Log("puddle", Acore::StringFormat("at=({:.1f}, {:.1f}, {:.1f}) alive={} dropped={} why={}",
                at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), _puddles.size(), _puddlesDropped, why));
            return true;
        }

        void UpdatePuddles(uint32 diff, uint64 now)
        {
            Creature* boss = _fight.Boss();
            std::vector<PuddleSpot> spots;
            for (auto it = _puddles.begin(); it != _puddles.end();)
            {
                Creature* puddle = Find(it->guid);
                if (!puddle || !puddle->IsAlive())
                {
                    Cancel(boss, it->ring);
                    it = _puddles.erase(it);
                    continue;
                }
                spots.push_back({ DungeonKit::PlaneOf(puddle), puddle->GetPositionZ(), it->bornMs });
                ++it;
            }
            _puddleTickMs += diff;
            if (_puddleTickMs < Tune::kPuddleTickMs)
                return;
            _puddleTickMs = 0;
            if (spots.empty())
                return;
            GuidSet inside;
            std::vector<ObjectGuid> dosed;
            for (Player* player : _fight.FightPlayers())
                if (InAnyPuddle(spots, DungeonKit::PlaneOf(player), player->GetPositionZ(), now))
                {
                    inside.insert(player->GetGUID());
                    dosed.push_back(player->GetGUID());
                }
            if (inside.empty())
                return;
            DungeonKit::RegistryHitSpec spec;
            spec.pct = Tune::kPuddlePct;
            spec.tankPct = Tune::kPuddlePct;        // rule 17: the tank in a puddle takes the tank row
            spec.school = kSchoolNature;
            spec.spellId = SPELL_HM_PUDDLE;
            spec.weakened = false;                  // a lingering patch (MT19: no penalty)
            spec.tag = TAG_HM_PUDDLE_TICK;
            _live.push_back(DungeonKit::RegistryHit(boss, inside, spec));
            for (ObjectGuid const& guid : dosed)
                if (Player* player = ObjectAccessor::GetPlayer(*boss, guid))
                    _dose->Add(player, int32(Tune::kPuddleDose), "puddle");
        }

        // ---- MT18 the glow and the geiger click, MT20 Meltdown ------------------------------------------------------

        void UpdateCarriers(uint32 diff)
        {
            Creature* boss = _fight.Boss();
            _carrierPollMs += diff;
            if (_carrierPollMs < Tune::kCarrierPollMs)
                return;
            uint32 const elapsed = _carrierPollMs;
            _carrierPollMs = 0;
            _carrierSecondMs += elapsed;

            std::map<uint64, uint32> doses;
            for (auto const& [guid, dose] : _dose->Carriers())
                doses[guid.GetRawValue()] = dose;
            for (auto it = _geiger.begin(); it != _geiger.end();)
                it = doses.count(it->first) ? std::next(it) : _geiger.erase(it);
            for (auto const& [raw, dose] : doses)
            {
                uint32& clock = _geiger[raw];
                clock += elapsed;
                uint32 const every = GnomerFallout::GeigerEveryMs(dose);
                if (!every || clock < every)
                    continue;
                clock = 0;
                if (Player* player = ObjectAccessor::GetPlayer(*boss, ObjectGuid(raw)); Alive(player))
                    player->PlayDirectSound(kSoundGeiger, player);
            }

            if (_carrierSecondMs < Tune::kCarrierSecondMs)
                return;
            _carrierSecondMs = 0;

            // The bright glow at 10 and up (the Leaking read).
            for (auto it = _glowing.begin(); it != _glowing.end();)
            {
                auto const d = doses.find(it->GetRawValue());
                if (d != doses.end() && d->second >= Tune::kGlowAt)
                {
                    ++it;
                    continue;
                }
                if (Player* player = ObjectAccessor::GetPlayer(*boss, *it))
                    player->RemoveAurasDueToSpell(SPELL_HM_DOSE_GLOW, boss->GetGUID());
                it = _glowing.erase(it);
            }
            for (auto const& [raw, dose] : doses)
                if (dose >= Tune::kGlowAt)
                    if (Player* player = ObjectAccessor::GetPlayer(*boss, ObjectGuid(raw)); Alive(player)
                        && !player->HasAura(SPELL_HM_DOSE_GLOW, boss->GetGUID()))
                    {
                        boss->AddAura(SPELL_HM_DOSE_GLOW, player);
                        _glowing.insert(player->GetGUID());
                    }

            // MT20: the carriers' own tick (the Spread hits the others), the spreads kept in step with the ledger (a
            // carrier who left the map gets no callback).
            if (_meltdown.empty())
                return;
            GuidSet carriers;
            for (auto it = _meltdown.begin(); it != _meltdown.end();)
            {
                Player* player = ObjectAccessor::GetPlayer(*boss, ObjectGuid(it->first));
                auto const d = doses.find(it->first);
                if (!Alive(player) || d == doses.end() || d->second < Tune::kMeltdownAt)
                {
                    EndMeltdown(boss, it->first, it->second);
                    it = _meltdown.erase(it);
                    continue;
                }
                carriers.insert(player->GetGUID());
                ++it;
            }
            if (carriers.empty())
                return;
            DungeonKit::RegistryHitSpec spec;
            spec.pct = Tune::kMeltdownPct;
            spec.tankPct = Tune::kMeltdownPct;
            spec.school = kSchoolNature;
            spec.spellId = SPELL_HM_MELTDOWN;
            spec.weakened = false;
            spec.tag = TAG_HM_MELTDOWN;
            _live.push_back(DungeonKit::RegistryHit(boss, carriers, spec));
        }

        void Meltdown(Player* player, bool on)
        {
            Creature* boss = _fight.Boss();
            if (!boss || !player)
                return;
            uint64 const raw = player->GetGUID().GetRawValue();
            auto it = _meltdown.find(raw);
            if (!on)
            {
                if (it != _meltdown.end())
                {
                    EndMeltdown(boss, raw, it->second);
                    _meltdown.erase(it);
                }
                return;
            }
            if (it != _meltdown.end() || !Alive(player))
                return;
            // A lasting 6 yd Spread on the carrier: the others inside take 5% a tick (carriers stack on each other).
            MechanicRef ref = Mechanic::Spread(boss, Tune::kMeltdownYd, Ms(Tune::kMeltdownWarnMs));
            if (!ref.IsValid())
                return;
            ref.Targets(GuidSet{ player->GetGUID() }).Persistent(Ms(Tune::kWholeFightMs), Ms(Tune::kMeltdownTickMs))
                .Damage(Tune::kMeltdownPct).TankDamage(Tune::kMeltdownPct).School(kSchoolNature)
                .Spell(SPELL_HM_MELTDOWN).Within(_bounds).Tag(TAG_HM_MELTDOWN);
            _meltdown[raw] = ref.Handle();
            boss->AddAura(SPELL_HM_MELTDOWN_AURA, player);
            Log("meltdown", Acore::StringFormat("player={} dose={} carriers={}", player->GetName(),
                _dose ? _dose->Dose(player->GetGUID()) : 0, _meltdown.size()));
        }

        void EndMeltdown(Creature* boss, uint64 raw, MechanicHandle handle)
        {
            Cancel(boss, handle);
            if (Player* player = boss ? ObjectAccessor::GetPlayer(*boss, ObjectGuid(raw)) : nullptr)
                player->RemoveAurasDueToSpell(SPELL_HM_MELTDOWN_AURA, boss->GetGUID());
        }

        // ---- MT25 the Reactor Leak ----------------------------------------------------------------------------------

        void UpdateLeak(uint64 now)
        {
            for (uint8 const line : AlarmsDue(now, _alarmFired))
            {
                _alarmFired |= uint8(1u << line);
                AlarmSay(line);
                PlayAlarm();
                Log("alarm", Acore::StringFormat("line={} at={}", line, now));
            }
            if (!_leakOn)
            {
                if (LeakOn(now))
                    StartLeak(now, "clock");
                return;
            }
            if (now < _leakDueMs)
                return;
            _leakDueMs = GnomerThermaplugg::NextDue(_leakDueMs, Tune::kLeakTickMs, now);
            LeakTick();
        }

        void StartLeak(uint64 now, char const* why)
        {
            if (_leakOn)
                return;
            _leakOn = true;
            _leakDueMs = now + Tune::kLeakTickMs;
            AlarmSay(ALARM_FAILURE);
            PlayAlarm();
            if (Creature* disc = _fight.Summon(NPC_VENT_STALKER, ToPos(kRoomCenter)))
            {
                disc->SetDisplayId(kDisplayNatureDisc, kLeakDiscScale);     // one call: a display change resets it
                _leakDisc = disc->GetGUID();
            }
            Log("reactor-leak", Acore::StringFormat("at={} why={}", now, why));
        }

        // MT25: 10% of the reference row to every player in combat with him (his threat list, s7 #35 A), wherever
        // they stand; the damage taken of the dose multiplies it. The flooded room's screen rides each of them.
        void LeakTick()
        {
            Creature* boss = _fight.Boss();
            GuidSet targets;
            for (ThreatReference const* ref : boss->GetThreatMgr().GetUnsortedThreatList())
            {
                Player* player = ref->GetVictim() ? ref->GetVictim()->ToPlayer() : nullptr;
                if (!Alive(player) || !player->IsInMap(boss))
                    continue;
                targets.insert(player->GetGUID());
                if (!player->HasAura(SPELL_HM_LEAK_AURA, boss->GetGUID()))
                    boss->AddAura(SPELL_HM_LEAK_AURA, player);
            }
            if (targets.empty())
                return;
            DungeonKit::RegistryHitSpec spec;
            spec.pct = Tune::kLeakPct;
            spec.tankPct = Tune::kLeakPct;
            spec.school = kSchoolNature;
            spec.spellId = SPELL_HM_REACTOR_LEAK;
            spec.weakened = false;
            spec.tag = TAG_HM_REACTOR_LEAK;
            _live.push_back(DungeonKit::RegistryHit(boss, targets, spec));
            ++_leakTicks;
        }

        void PlayAlarm()
        {
            for (Player* player : _fight.FightPlayers())
                player->PlayDirectSound(kSoundAlarm, player);
        }

        ThermapluggFight& _fight;
        ObjectGuid _boss;
        BossMechanics::SpotBounds const _bounds;
        std::unique_ptr<GnomereganMachines::Duplicator> _dup;
        std::unique_ptr<GnomereganMachines::DoseField> _dose;
        std::vector<uint32> _plan;          // MT18: the lit plates' serve order PlanPlates last gave D6
        bool _tankLast = true;
        uint32 _planMs = 0;
        std::array<ObjectGuid, kFaceCount> _vents{};
        ObjectGuid _alarm;
        ObjectGuid _leakDisc;
        std::vector<Puddle> _puddles;
        std::map<uint64, MechanicHandle> _meltdown;     // the carrier's raw guid -> its lasting Spread
        GuidSet _glowing;
        std::map<uint64, uint32> _geiger;
        std::vector<MechanicHandle> _live;
        std::array<bool, kSchematicCount> _loaded{};
        bool _yelled = false;
        bool _leakOn = false;
        uint8 _alarmFired = 0;
        uint64 _ventDueMs = 0;
        uint64 _leakDueMs = 0;
        uint32 _puddleTickMs = 0;
        uint32 _carrierPollMs = 0;
        uint32 _carrierSecondMs = 0;
        uint32 _copies = 0;
        uint32 _ventPulses = 0;
        uint32 _halves = 0;
        uint32 _puddlesDropped = 0;
        uint32 _leakTicks = 0;
    };

    // The running package of the GM's map (an error and nullptr when none runs).
    SchematicsA* RunningPackage(ChatHandler* handler)
    {
        if (!GnomerTest::RequireGnomeregan(handler))
            return nullptr;
        Player* gm = handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
        ThermapluggFight* fight = gm ? GnomerThermaplugg::FindThermapluggFight(gm->GetMap()) : nullptr;
        Creature* boss = fight ? fight->Boss() : nullptr;
        if (boss)
        {
            std::lock_guard<std::mutex> guard(RunningLock());
            auto it = Running().find(boss->GetGUID().GetRawValue());
            if (it != Running().end())
                return it->second;
        }
        handler->SendErrorMessage("{}", "No Whole Workshop pull is running (set the flag on heroic with the console or "
            "`.dbtest gnomer hardmode arm`, then pull Thermaplugg).");
        return nullptr;
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// The Clearance Console 301382 (questgiver type: gossip menu 5300022, npc_text 900029; the S0 rev spawns it heroic
// only). Always selectable (a refused player reads why); lit while the flag is set.
// ---------------------------------------------------------------------------------------------------------------------
struct go_gnomer_clearance_console : public GameObjectAI
{
    explicit go_gnomer_clearance_console(GameObject* go) : GameObjectAI(go) { }

    void UpdateAI(uint32 diff) override
    {
        if (_pollMs > diff)
        {
            _pollMs -= diff;
            return;
        }
        _pollMs = kConsolePollMs;
        InstanceScript* instance = me->GetInstanceScript();
        GOState const want = instance && instance->GetData(DATA_HARD_MODE) ? GO_STATE_ACTIVE : GO_STATE_READY;
        if (me->GetGoState() != want)
            me->SetGoState(want);
    }

    bool GossipHello(Player* player, bool reportUse) override
    {
        if (reportUse || !player)
            return true;
        ConsoleVerdict const verdict = ConsoleVerdictFor(player);
        if (verdict == CONSOLE_BOT)
            return true;        // rule 34: no menu, no line
        ClearGossipMenuFor(player);
        if (verdict == CONSOLE_ACCEPTED)
            AddGossipItemFor(player, kConsoleGossipMenu, kConsoleGossipOption, GOSSIP_SENDER_MAIN, kConsoleActionArm);
        else
            ChatHandler(player->GetSession()).SendNotification(
                std::string_view(ConsoleRefusalText(verdict, ThermapluggDone(player))));
        SendGossipMenuFor(player, kConsoleNpcText, me->GetGUID());
        return true;
    }

    // The option's box was confirmed (the client asks before it sends the choice).
    bool GossipSelect(Player* player, uint32 /*menuId*/, uint32 gossipListId) override
    {
        if (!player)
            return true;
        uint32 const action = player->PlayerTalkClass->GetGossipOptionAction(gossipListId);
        ClearGossipMenuFor(player);     // the engine's own gossip select then finds nothing to do
        CloseGossipMenuFor(player);
        if (action == kConsoleActionArm && ArmFromConsole(player, "console") == CONSOLE_ACCEPTED)
        {
            me->SetGoState(GO_STATE_ACTIVE);
            _pollMs = kConsolePollMs;
        }
        return true;
    }

private:
    uint32 _pollMs = 0;
};

// ---------------------------------------------------------------------------------------------------------------------
// The Wandering Puddle 301135 (MT19): forms in 1.5 s, then drifts across the room at 2 yd/s, straight on while the
// floor goes on and turning back at the walls; the package owns its zone and its tick, D6's summon list its despawn.
// ---------------------------------------------------------------------------------------------------------------------
struct npc_gnomer_wandering_puddle : public ScriptedAI
{
    explicit npc_gnomer_wandering_puddle(Creature* creature) : ScriptedAI(creature), _room(RoomArena()) { }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
        me->SetDisplayId(kDisplayNatureDisc, Tune::kPuddleDiscScale * Tune::kPuddleFormScale);
        _formMs = Tune::kPuddleFormMs;
        _legMs = 0;
        _legDone = false;
        _heading = frand(0.f, 2.f * kPi);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void EnterEvadeMode(EvadeReason /*why*/) override { }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type == POINT_MOTION_TYPE && id == kPuddlePoint)
            _legDone = true;    // the next leg from UpdateAI (no new motion inside the motion's own callback)
    }

    void UpdateAI(uint32 diff) override
    {
        if (_formMs)
        {
            if (_formMs > diff)
            {
                _formMs -= diff;
                return;
            }
            _formMs = 0;
            me->SetDisplayId(kDisplayNatureDisc, Tune::kPuddleDiscScale);
            NextLeg();
            return;
        }
        _legMs += diff;
        if (_legDone || _legMs >= Tune::kPuddleLegTimeoutMs)
            NextLeg();
    }

private:
    void NextLeg()
    {
        _legDone = false;
        _legMs = 0;
        float const jitter = frand(-Tune::kPuddleBounceJitterDeg, Tune::kPuddleBounceJitterDeg);
        PuddleLeg const leg = NextPuddleLeg(_room, DungeonKit::PlaneOf(me), me->GetPositionZ(), _heading, jitter);
        _heading = leg.heading;
        if (!leg.moved)
            return;     // nothing fits: it stands until the next timeout
        float z = me->GetPositionZ();
        me->UpdateAllowedPositionZ(leg.to.x, leg.to.y, z);
        me->GetMotionMaster()->MovePoint(kPuddlePoint, leg.to.x, leg.to.y, z, FORCED_MOVEMENT_NONE,
            Tune::kPuddleSpeedYdPerSec);
    }

    Arena const _room;
    uint32 _formMs = 0;
    uint32 _legMs = 0;
    float _heading = 0.f;
    bool _legDone = false;
};

// The room alarm 301137 (the Leak's lines 0-4) and the vent stalker 301138 (the vapor, the Leak's disc): inert.
struct npc_gnomer_workshop_stalker : public NullCreatureAI
{
    explicit npc_gnomer_workshop_stalker(Creature* creature) : NullCreatureAI(creature) { }
};

// ---------------------------------------------------------------------------------------------------------------------
// `.dbtest gnomer workshop <subcommand>`
// ---------------------------------------------------------------------------------------------------------------------

namespace
{
    Player* Gm(ChatHandler* handler)
    {
        return handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return GnomerTest::ShowBossInfo(handler, NPC_THERMAPLUGG, BOSS_WHOLE_WORKSHOP);
    }

    // The flag, the verdict, the kill, and the running package's line.
    bool HandleState(ChatHandler* handler)
    {
        InstanceScript* instance = GnomerTest::GmInstance(handler);
        if (!instance)
            return false;
        handler->PSendSysMessage("Whole Workshop: flag={} verdict={} killed={} key={}",
            instance->GetData(DATA_HARD_MODE), instance->GetData(DATA_HARD_MODE_VERDICT),
            instance->GetData(DATA_HARD_MODE_KILLED), instance->GetData(DATA_HARD_MODE_KEY));
        Player* gm = Gm(handler);
        ThermapluggFight* fight = gm ? GnomerThermaplugg::FindThermapluggFight(gm->GetMap()) : nullptr;
        Creature* boss = fight ? fight->Boss() : nullptr;
        std::string line = "no pull";
        if (boss)
        {
            std::lock_guard<std::mutex> guard(RunningLock());
            auto it = Running().find(boss->GetGUID().GetRawValue());
            line = it != Running().end() ? it->second->Describe() : std::string("plain pull (no package)");
        }
        handler->PSendSysMessage("Whole Workshop: {}", line);
        return true;
    }

    // The console's path for the GM (every check applies: heroic, out of combat, the card in the bags).
    bool HandleConsole(ChatHandler* handler)
    {
        if (!GnomerTest::RequireGnomeregan(handler))
            return false;
        Player* gm = Gm(handler);
        ConsoleVerdict const verdict = ArmFromConsole(gm, "dbtest");
        if (verdict != CONSOLE_ACCEPTED)
        {
            handler->SendErrorMessage("Refused: {}", ConsoleRefusalText(verdict, ThermapluggDone(gm)));
            return false;
        }
        handler->SendSysMessage("The flag is set: Thermaplugg's next heroic pull is the Whole Workshop.");
        return true;
    }

    bool HandleLoad(ChatHandler* handler, std::string which)
    {
        SchematicsA* package = RunningPackage(handler);
        if (!package)
            return false;
        std::optional<Schematic> s;
        if (which == "techbot")
            s = Schematic::Techbot;
        else if (which == "fallout")
            s = Schematic::ViscousFallout;
        if (!s)
        {
            handler->SendErrorMessage("{}", "Usage: .dbtest gnomer workshop load <techbot|fallout>");
            return false;
        }
        if (!package->TestLoad(*s))
        {
            handler->SendErrorMessage("{}", "Already loaded.");
            return false;
        }
        handler->PSendSysMessage("Loaded the {} schematic (its console line said).", which);
        return true;
    }

    bool HandleVent(ChatHandler* handler)
    {
        SchematicsA* package = RunningPackage(handler);
        if (!package)
            return false;
        if (!package->TestVent())
        {
            handler->SendErrorMessage("{}", "The Fallout schematic is not loaded (`load fallout`).");
            return false;
        }
        handler->SendSysMessage("A venting pulse: 1 dose per open face to every player in the room.");
        return true;
    }

    bool HandleDose(ChatHandler* handler, uint32 dose)
    {
        SchematicsA* package = RunningPackage(handler);
        if (!package)
            return false;
        Player* target = handler->getSelectedPlayerOrSelf();
        if (!package->TestDose(target, dose))
        {
            handler->SendErrorMessage("{}", "The Fallout schematic is not loaded, or the player is dead.");
            return false;
        }
        handler->PSendSysMessage("{}'s dose is {} (Leaking at 10, Meltdown at 20).", target->GetName(), dose);
        return true;
    }

    bool HandlePuddle(ChatHandler* handler)
    {
        SchematicsA* package = RunningPackage(handler);
        if (!package)
            return false;
        Player* gm = Gm(handler);
        if (!gm || !package->TestPuddle(gm->GetPosition()))
        {
            handler->SendErrorMessage("{}", "The puddle was refused.");
            return false;
        }
        handler->SendSysMessage("A Wandering Puddle at your feet (forms in 1.5 s, drifts for 2 min).");
        return true;
    }

    bool HandleLeak(ChatHandler* handler)
    {
        SchematicsA* package = RunningPackage(handler);
        if (!package)
            return false;
        package->TestLeak();
        handler->SendSysMessage("The Reactor Leak: 10% a second to his threat list until the fight ends.");
        return true;
    }

    bool HandleAlarm(ChatHandler* handler, uint32 line)
    {
        SchematicsA* package = RunningPackage(handler);
        if (!package)
            return false;
        if (line > kAlarmLastGroup)
        {
            handler->SendErrorMessage("Lines 0-{}.", uint32(kAlarmLastGroup));
            return false;
        }
        package->TestAlarm(uint8(line));
        return true;
    }

    ChatCommandTable const& WorkshopTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",    HandleInfo,    SEC_GAMEMASTER, Console::No },
            { "state",   HandleState,   SEC_GAMEMASTER, Console::No },
            { "console", HandleConsole, SEC_GAMEMASTER, Console::No },
            { "load",    HandleLoad,    SEC_GAMEMASTER, Console::No },
            { "vent",    HandleVent,    SEC_GAMEMASTER, Console::No },
            { "dose",    HandleDose,    SEC_GAMEMASTER, Console::No },
            { "puddle",  HandlePuddle,  SEC_GAMEMASTER, Console::No },
            { "leak",    HandleLeak,    SEC_GAMEMASTER, Console::No },
            { "alarm",   HandleAlarm,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_thermaplugg_hard_mode()
{
    GnomerThermaplugg::RegisterThermapluggHardMode(GnomerThermaplugg::HardModePackage::SchematicsA,
        [](ThermapluggFight& fight) { return std::make_unique<SchematicsA>(fight); });
    RegisterDungeonReworkGameObjectAI(go_gnomer_clearance_console, kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_gnomer_wandering_puddle, kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_gnomer_workshop_stalker, kInstanceScriptName);
    GnomerTest::RegisterBoss("workshop", WorkshopTestCommands());
}
