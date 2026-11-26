/*
 * mod-dungeon-bosses, Gnomeregan D6: Mekgineer Thermaplugg (7800, boss_thermaplugg_rework), the end of section 2.
 * Build spec: docs/dungeons/gnomeregan-rework.md "Mekgineer Thermaplugg" (MT1-MT14; rulings 37-42, 64), handoff
 * sections 3.5 row D6 (rules 1-38, the kick and dispel table), 3.6, 3.8, 3.9 rows 8 and 9, 7 #30 A, #31 B, #32 A,
 * #35 A, #36-#38, #40 A and 10. Replaces the stock SmartAI of 7800, 7915 and the twelve faces and buttons (WP-S0's
 * rev drops it). Pure rules and every number: ThermapluggLogic.h. The Whole Workshop (heroic hard mode, D6Ha and D6Hb)
 * plugs in through ThermapluggFight.h (this AI implements ThermapluggFight); this file never needs an edit for it.
 *
 *   MT1  a face opens   every 20 s (heroic 15, hard mode 12) from 10 s: a random closed Gnome Face opens (its stock
 *                       object, GO state active), a beam joins him and the face's stalker at the alcove mouth, emote 4
 *   MT2  the chutes     an open face builds every 8 s (first 2 s after it opens; The Big One every 16 s); normal: at
 *                       most 8 bombs alive (a due bomb is skipped)
 *   MT3  Walking Bomb   301120 at the alcove mouth (37 yd out), a random player marked (tank included), walking at
 *                       them at 4.6 yd/s (s7 #31 B; DungeonKit::Chaser: MovePoint, never a victimless MoveChase, rule
 *                       32); within 3 yd it blows: 8 yd, 40% (heroic 60%, hard mode 70%) and Weakened. Killed first it
 *                       falls apart (normal) or blows where it dies (heroic, MT8). The bots: the marked player keeps
 *                       away (a RunOut, bots only), the ranged kill the bombs first
 *   MT4  the plates     one per face, 25 yd out on its bearing (s7 #30 A): a ranked DwellSoak on a stalker while the
 *                       face is open; the first player to touch it (not Locked Out) shuts the face and is Locked Out
 *                       for 30 s. Ranks: SP's face priority on heroic (The Big One first), unranked on normal. One
 *                       exclusive group (tag 71); a package may set its Ordering and serve order (SetPlatePlan: the
 *                       hard mode's dose, D6Ha)
 *   MT5  the mines      every 15 s (hard mode 12) from 8 s, with yell 2: a mine at the feet of 3 random players
 *                       (heroic: every player), KT-G's TwoRingMines: arms in 3 s, a player 0.5 s in the 3 yd ring
 *                       sets it off, the 6 yd ring takes 40% (60%, 70%) and Weakened; 45 s (60, 75) of life. Bombs
 *                       never set one off
 *   MT6  Override       every 45 s (hard mode 35), yell 1 and emote 5: three closed faces open (heroic: every one)
 *   MT7  Knock Away     the stock 10101's copy on his target in reach, 3 s then every 15 s
 *   MT9  Incendiary     face 02 (heroic): the blast leaves an 8 yd fire patch, 20 s, 15% a second
 *   MT10 Frost          face 03: the blast roots for 3 s (Magic: a dispel reward)
 *   MT11 Radioactive    face 04: the blast leaves a stacking Poison (4% a second a stack, 12 s; a dispel reward)
 *   MT12 Sticky Bomb    face 05: no unit; every 8 s a bomb lobbed from the face onto a random player (tank included),
 *                       emote 6; 5 s later 60% (hard mode 70%) to everyone else within 8 yd (a RunOut)
 *   MT13 The Big One    face 06: every 16 s, 301124 walks to the room's center at 3 yd/s (s7 #38 h), emote 7, a Stack
 *                       on it for the bots that resolves when the walk should end; it blows then, wherever it is
 *                       (BigOneBlows): its 100% is split among the players within 8 yd (nobody: everyone takes 100%);
 *                       not attackable, never Weakened
 *   MT14 Detonator      heroic, from 20 s every 25 s (hard mode 20): a 3 s Fire bar, emote 8, kickable (the expected
 *                       kick); landed, every living bomb blows where it is and every armed mine goes off
 *
 * A wipe, an evade or his death: the packages' OnEnd first, then every face shuts, every bomb, stalker, mine body and
 * plate goes, the registry handles are canceled, the players' auras of the fight removed and his health given back
 * (the hard mode's 800,000). Reload mid-fight: the creature reloads and Reset shuts the faces (RB-23). End NPC 2 is the
 * instance's (S0 Q1). Every firing logs one INFO line "gnomer-build thermaplugg <mechanic> ..."; `.dbtest gnomer
 * thermaplugg ...` fires each mechanic on demand.
 *
 * Mirrored code: none (the stock SmartAI's facts only: the face entries and their GO states, the bomb's stock speed,
 * the texts).
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Containers.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitChase.h"
#include "DungeonKitFields.h"
#include "DungeonKitMines.h"
#include "DungeonKitSoaks.h"
#include "GameObject.h"
#include "GnomereganKit.h"
#include "GnomereganRework.h"
#include "GnomereganTestCommand.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ThermapluggFight.h"
#include "ThermapluggLogic.h"
#include <algorithm>
#include <array>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace GnomereganRework;
using namespace GnomerThermaplugg;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;

namespace
{
    char const* const kBoss = "thermaplugg";
    uint32 constexpr kBigOnePoint = 13;     // The Big One's MovePoint id (MT13)

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(static_cast<int64>(ms));
    }

    uint32 RandBelow(uint32 n)
    {
        return n > 1 ? urand(0, n - 1) : 0;
    }

    // A player the fight acts on: in the world, alive, not a game master.
    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    Position ToPos(Point3 const& p)
    {
        return Position(p.x, p.y, p.z, p.o);
    }

    // D6's own plate rule (SP MT4 Bots: non-tanks first, then by ETA); a package may set another (SetPlatePlan).
    BossMechanics::Ordering DefaultPlateOrder()
    {
        BossMechanics::Ordering order;
        order.roleLast = BossMechanics::Role::Tank;
        return order;
    }

    bool SameOrdering(BossMechanics::Ordering const& a, BossMechanics::Ordering const& b)
    {
        return a.auraSpell == b.auraSpell && a.ascending == b.ascending && a.capStacks == b.capStacks
            && a.roleLast == b.roleLast && a.minStacks == b.minStacks;
    }

    // Create health is the base the engine rebuilds max health from (the Deadmines, Stratholme and Zul'Farrak hard
    // modes' way).
    void SetCreatureHealth(Creature* creature, uint32 health)
    {
        if (!creature || !health || !creature->IsAlive())
            return;
        creature->SetCreateHealth(health);
        creature->SetStatFlatModifier(UNIT_MOD_HEALTH, BASE_VALUE, static_cast<float>(health));
        creature->UpdateMaxHealth();
        creature->SetHealth(creature->GetMaxHealth());
    }

    std::array<ThermapluggHardModeFactory, std::size_t(HardModePackage::Count)>& Factories()
    {
        static std::array<ThermapluggHardModeFactory, std::size_t(HardModePackage::Count)> factories;
        return factories;
    }

    // The registry's own resolves (a Sticky Bomb's RunOut) wait here for the next tick (rule 11): the hook and the log
    // never run inside the registry's callback.
    struct QueuedHit
    {
        HitSource source = HitSource::Bomb;
        ObjectGuid anchor;
        GuidSet hit;
    };
}

// Mekgineer Thermaplugg 7800
struct boss_thermaplugg_rework : public BossAI, public ThermapluggFight
{
private:
    struct BombState
    {
        ObjectGuid guid;
        BombType type = BombType::Walking;
        uint32 face = 0;
        DungeonKit::Chaser chase;
        ObjectGuid target;
        MechanicHandle ring;        // MT3 the 8 yd outline (telegraph only, canceled at the blast)
        MechanicHandle keepAway;    // MT3 the marked player's RunOut (bots only, never resolves)
        MechanicHandle stack;       // MT13 The Big One's Stack (bots; the blast is the script's)
        uint64 bornMs = 0;
        uint32 stackMs = 0;         // MT13 The Big One: its Stack resolves and it blows this long after its spawn
        bool moveEnded = false;     // MT13 The Big One: its point move ended (the engine's arrival)
        bool paused = false;        // its chase is held while it casts (the hard mode's Duplication)
        bool done = false;          // blown up, fallen apart or gone: nothing more happens to it
    };

    struct FaceState
    {
        bool open = false;
        uint64 nextBuildMs = 0;
        uint32 soak = 0;            // the plate's DwellSoak id (0: none)
        uint32 built = 0;
    };

    struct StickyState
    {
        ObjectGuid carrier;
        uint64 dueMs = 0;
    };

public:
    explicit boss_thermaplugg_rework(Creature* creature)
        : BossAI(creature, BOSS_THERMAPLUGG), _arena(RoomArena(), LeashOptions(kBoss)), _room(RoomArena()),
            _bounds(ThermapluggFloorBounds()) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();
        Cleanup(false);
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        bool const heroic = DungeonKit::IsHeroicMap(me);
        if (!_baseHealth)
            _baseHealth = me->GetMaxHealth();
        _engaged = true;
        _clockMs = 0;
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_THERMAPLUGG;
        Mechanic::BeginEncounter(me, options);

        // RB-24: the packages are made at the pull, then the instance hears whether they were.
        if (heroic && instance && instance->GetData(DATA_HARD_MODE) != 0)
        {
            _packages = CreateThermapluggHardModes(*this);
            if (_packages.empty())
                Log("hardmode-missing", "the flag is set but no package was made: plain heroic");
        }
        bool const hardMode = !_packages.empty();
        if (instance)
            instance->SetData(DATA_HARD_MODE_VERDICT, hardMode ? kVerdictArmed : kVerdictPlain);
        if (hardMode)
            SetCreatureHealth(me, Health::kWholeWorkshop);
        _mode = ModeFor(heroic, hardMode);
        StartClocks();
        SummonStalkers();
        _arena.Engage(me);
        for (std::unique_ptr<ThermapluggHardMode>& package : _packages)
            package->OnEngage(*this);
        _thresholds.assign(_packages.size(), ThresholdLatch());
        for (std::size_t i = 0; i < _packages.size(); ++i)
            _thresholds[i].Arm(_packages[i]->HealthThresholds());
        Describe();
        Talk(SAY_MT_AGGRO);
        OnBossPull(me, kBoss, hardMode);    // after the health the hard mode set
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        if (_engaged)
            Log("evade", Acore::StringFormat("reason={}", uint32(why)));
        Cleanup(false);
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Log("death", Acore::StringFormat("mode={} bombs={} blasts={} plates={} mines={} detonations={} killer={}",
            kModeNames[ModeIndex(_mode)], _bombsBuilt, _blasts, _plateTouchesDone, _minesLaid, _detonations,
            killer ? killer->GetName() : std::string("none")));
        Cleanup(true);
        BossAI::JustDied(killer);   // slot 5 DONE: the instance's slot 6, loot bit and End NPC 2
    }

    void KilledUnit(Unit* victim) override
    {
        if (!victim || !victim->IsPlayer() || !_engaged)
            return;
        if (_lastKillLineMs && _clockMs < _lastKillLineMs + Tune::kKillLineCooldownMs)
            return;
        _lastKillLineMs = std::max<uint64>(_clockMs, 1);
        Talk(SAY_MT_KILL, victim);
    }

    // The bombs, stalkers and mine bodies join his summon list (despawned on reset, evade and death) but never his
    // fight: they are passive, and a bomb only enters combat when a player hits it.
    void JustSummoned(Creature* summon) override
    {
        if (summon)
            summons.Summon(summon);
    }

    void SummonedCreatureDies(Creature* summon, Unit* killer) override
    {
        if (summon && BombTypeOfEntry(summon->GetEntry()))
            BombKilled(summon);
        BossAI::SummonedCreatureDies(summon, killer);
    }

    // MT13: The Big One's point move ended (the engine's arrival, wherever the path ended). Only noted: it blows when
    // its Stack resolves (UpdateBombs, BigOneBlows), never inside the bomb's motion update.
    void SummonMovementInform(Creature* summon, uint32 type, uint32 point) override
    {
        if (!summon || type != POINT_MOTION_TYPE || point != kBigOnePoint)
            return;
        if (BombState* b = FindBomb(summon->GetGUID()); b && !b->done && b->type == BombType::BigOne)
            b->moveEnded = true;
    }

    void SummonedCreatureDespawn(Creature* summon) override
    {
        if (summon && BombTypeOfEntry(summon->GetEntry()))
            BombGone(summon->GetGUID(), "despawned");
        BossAI::SummonedCreatureDespawn(summon);
    }

    // MT14: the Detonator landed (OnSpellCast: the cast finished).
    void OnSpellCast(SpellInfo const* spell) override
    {
        BossAI::OnSpellCast(spell);
        if (spell && spell->Id == SPELL_MT_DETONATOR && _engaged)
            Detonate("cast");
    }

    // A kick (or a silence) stops the Detonator: nothing blows (the expected kick).
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (spell && spell->Id == SPELL_MT_DETONATOR && _engaged)
        {
            ++_detonatorsStopped;
            Log("detonator-stopped", Acore::StringFormat("stopped={}", _detonatorsStopped));
        }
    }

    void UpdateAI(uint32 diff) override
    {
        GnomereganRework::NoAssist(me);     // rule 29, LESSONS L1: every tick, before UpdateVictim
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_engaged)
            return;
        _clockMs += diff;

        UpdateBombs(diff);
        _mines.Update(me, diff);
        SyncMineBodies();
        _plates.Update(me, diff);
        TakePlateTouches();
        UpdateStickies();
        UpdateBeats();
        FlushHits();
        for (std::unique_ptr<ThermapluggHardMode>& package : _packages)
            package->OnUpdate(*this, diff);
        UpdateThresholds();
        if (!_engaged)
            return;

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // ThermapluggFight (the hard mode's view, ThermapluggFight.h)
    // ----------------------------------------------------------------------------------------------------------------

    Creature* Boss() override { return me; }
    InstanceScript* Instance() override { return instance; }
    bool Heroic() const override { return _mode != Mode::Normal; }
    bool HardMode() const override { return !_packages.empty(); }
    Mode FightMode() const override { return _mode; }
    uint64 ClockMs() const override { return _engaged ? _clockMs : 0; }

    std::vector<Player*> FightPlayers() override
    {
        std::vector<Player*> out;
        if (!me->IsInWorld())
            return out;
        for (MapReference const& ref : me->GetMap()->GetPlayers())
            if (Player* player = ref.GetSource())
                if (CountsAsPlayer(player) && _room.Contains(DungeonKit::PlaneOf(player), player->GetPositionZ()))
                    out.push_back(player);
        return out;
    }

    bool FaceOpen(uint32 face) const override
    {
        return face < kFaceCount && _faces[face].open;
    }

    FaceMask OpenFaces() const override
    {
        FaceMask mask{};
        for (uint32 i = 0; i < kFaceCount; ++i)
            mask[i] = _faces[i].open;
        return mask;
    }

    std::optional<uint32> OpenFace(std::optional<uint32> face, char const* why) override
    {
        if (!_engaged)
            return std::nullopt;
        if (!face || *face >= kFaceCount || _faces[*face].open)
        {
            std::vector<uint32> const picked = PickClosedFaces(OpenFaces(), 1, RandBelow);
            if (picked.empty())
                return std::nullopt;
            face = picked.front();
        }
        if (!OpenOne(*face, why ? why : "package"))
            return std::nullopt;
        return face;
    }

    Position FaceSpot(uint32 face) const override
    {
        return ToPos(kFaceSpots[face % kFaceCount]);
    }

    Position FaceMouth(uint32 face) const override
    {
        return ToPos(kBombStarts[face % kFaceCount]);
    }

    Creature* FaceStalker(uint32 face) override
    {
        return face < kFaceCount ? me->GetMap()->GetCreature(_faceStalkers[face]) : nullptr;
    }

    Creature* PlateAnchor(uint32 face) override
    {
        return face < kFaceCount ? me->GetMap()->GetCreature(_plateAnchors[face]) : nullptr;
    }

    bool PlateLit(uint32 face) const override
    {
        return face < kFaceCount && _faces[face].open && _faces[face].soak != 0;
    }

    bool LockedOut(Unit const* player) const override
    {
        return player && player->HasAura(SPELL_MT_LOCKED_OUT);
    }

    void SetPlatePlan(BossMechanics::Ordering const& order, std::vector<uint32> const& first) override
    {
        if (!_engaged)
            return;
        std::vector<uint32> ids;
        for (uint32 const face : first)
            if (face < kFaceCount && _faces[face].open && _faces[face].soak
                && std::find(ids.begin(), ids.end(), _faces[face].soak) == ids.end())
                ids.push_back(_faces[face].soak);
        std::vector<uint32> const now = _plates.Ids();
        bool const reorder = DungeonKit::SoakPriorityOrder(now, ids) != now;
        bool const rule = !SameOrdering(*_plateOrder, order);
        if (!reorder && !rule)
            return;
        *_plateOrder = order;       // every registration from here on reads it (LightPlate's configure)
        if (now.empty())
            return;
        if (reorder)
            _plates.Reprioritize(me, ids);
        else
            _plates.SetRank(me, now.front(), _plates.RankOf(now.front()));     // the same order: register anew
        std::string faces;
        for (uint32 const face : first)
            faces += Acore::StringFormat("{}{}", faces.empty() ? "" : ",", face + 1);
        Log("plate-plan", Acore::StringFormat("first={} order={}:{}:{} lit={}", faces.empty() ? "-" : faces,
            order.auraSpell, order.ascending ? "asc" : "desc", order.roleLast == BossMechanics::Role::Tank ? "tank-last"
            : "tank-in", now.size()));
    }

    std::vector<ObjectGuid> Bombs() const override
    {
        std::vector<ObjectGuid> out;
        for (std::unique_ptr<BombState> const& b : _bombs)
            if (!b->done)
                out.push_back(b->guid);
        return out;
    }

    bool AdoptBomb(Creature* source, Creature* copy) override
    {
        if (!_engaged || !source || !copy || source->GetEntry() != copy->GetEntry())
            return false;
        BombState const* from = FindBomb(source->GetGUID());
        if (!from || from->done || !WalksAtPlayer(from->type))
            return false;
        uint32 const health = std::max<uint32>(1, source->GetHealth());
        copy->SetMaxHealth(Values().bombHealth);
        copy->SetHealth(std::min(health, copy->GetMaxHealth()));
        copy->SetReactState(REACT_PASSIVE);
        Player* target = ObjectAccessor::GetPlayer(*me, from->target);
        if (!CountsAsPlayer(target))
            target = PickBombTarget();
        if (!target)
            return false;
        return SetupWalker(copy, from->type, from->face, target, true) != nullptr;
    }

    Creature* Summon(uint32 entry, Position const& at, uint32 despawnMs) override
    {
        if (!_engaged)
            return nullptr;
        return despawnMs ? me->SummonCreature(entry, at, TEMPSUMMON_TIMED_DESPAWN, despawnMs)
            : me->SummonCreature(entry, at, TEMPSUMMON_MANUAL_DESPAWN);
    }

    void Track(MechanicHandle handle) override
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 192)     // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 96);
    }

    void RefreshDescriptors() override
    {
        if (_engaged)
            Describe();
    }

    uint32 RefFlatOn(Unit const* target, float pct) override
    {
        return DungeonKit::RefFlatOn(me, target, pct);
    }

    void Say(uint8 group, WorldObject const* target) override
    {
        Talk(group, target);
    }

    void Log(char const* mechanic, std::string const& detail = {}) override
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    bool Engaged() const { return _engaged; }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest gnomer thermaplugg` entry points
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Face,
        Shut,
        Override,
        Bomb,
        Mines,
        Sticky,
        BigOne,
        Detonator,
        Knock,
    };

    // An empty string when fired; otherwise why not. `who` is the GM's selected player (or the GM); `face` 1 to 6.
    std::string TestFire(TestMechanic mechanic, Player* who, std::optional<uint32> face)
    {
        if (!me->IsEngaged() || !_engaged)
            return "Thermaplugg must be in combat (the picks read his room, the mechanics his encounter).";
        std::optional<uint32> index;
        if (face)
        {
            if (*face < 1 || *face > kFaceCount)
                return "Faces are 1 to 6 (ruling 64: 01 at (-561.2, 709.9), then round the room).";
            index = *face - 1;
        }
        switch (mechanic)
        {
            case TestMechanic::Face:
                if (!OpenFace(index, "gm"))
                    return "Every face is open (or that face is).";
                break;
            case TestMechanic::Shut:
            {
                if (!index || !_faces[*index].open)
                    return "Name an open face (1 to 6).";
                ShutFace(*index, nullptr, "gm");
                break;
            }
            case TestMechanic::Override:
                Override("gm");
                break;
            case TestMechanic::Bomb:
            {
                uint32 const f = index.value_or(0);
                BombType const type = FaceBomb(_mode, f);
                if (!WalksAtPlayer(type))
                    return "That face builds no walking bomb in this mode (5 Sticky, 6 The Big One).";
                Player* target = CountsAsPlayer(who) ? who : PickBombTarget();
                if (!target || !SpawnWalker(f, type, target))
                    return "No bomb: nobody alive (and not .gm on) in the room, or the summon failed.";
                break;
            }
            case TestMechanic::Mines:
                LayMines("gm");
                break;
            case TestMechanic::Sticky:
                if (!FireSticky(index.value_or(4), CountsAsPlayer(who) ? who : nullptr))
                    return "No carrier: nobody alive (and not .gm on) in the room.";
                break;
            case TestMechanic::BigOne:
                if (!SpawnBigOne(index.value_or(5)))
                    return "The Big One's summon failed.";
                break;
            case TestMechanic::Detonator:
                if (me->HasUnitState(UNIT_STATE_CASTING))
                    return "He is casting; try again when it ends.";
                if (!StartDetonator())
                    return "The cast was refused (a locked school, or he is silenced).";
                break;
            case TestMechanic::Knock:
                if (!me->GetVictim())
                    return "He holds no target now.";
                me->CastSpell(me->GetVictim(), SPELL_MT_KNOCK_AWAY, true);
                break;
        }
        return {};
    }

    // The heroic form (typed faces, the Detonator, the heroic numbers) on any map until the end of the pull (the
    // reference row stays the map's). False: not fighting, or the hard mode.
    bool TestHeroic(bool heroic)
    {
        if (!_engaged || !_packages.empty())
            return false;
        _mode = ModeFor(heroic, false);
        if (heroic && !_detonatorDueMs)
            _detonatorDueMs = _clockMs + Tune::kDetonatorFirstMs;
        for (uint32 i = 0; i < kFaceCount; ++i)
            if (_faces[i].open && _faces[i].soak)
                _plates.SetRank(me, _faces[i].soak, PlateRank(_mode, i));
        Describe();
        Log("mode", Acore::StringFormat("{} (gm)", kModeNames[ModeIndex(_mode)]));
        return true;
    }

    std::string TestState() const
    {
        std::string faces;
        for (uint32 i = 0; i < kFaceCount; ++i)
            faces += _faces[i].open ? static_cast<char>('1' + i) : '-';
        auto in = [this](uint64 due) -> int64
        {
            return due ? static_cast<int64>(due) - static_cast<int64>(_clockMs) : -1;
        };
        std::string text = Acore::StringFormat("clock={}s mode={} faces={} bombs={} mines={} armed={} plates={} "
            "stickies={} next face={}ms override={}ms mines={}ms detonator={}ms built={} blasts={} touches={} "
            "detonations={} stopped={} factor={:.2f} packages={}", _clockMs / 1000, kModeNames[ModeIndex(_mode)],
            faces, Bombs().size(), _mines.Count(), _mines.ArmedCount(), _plates.Count(), _stickies.size(),
            in(_faceDueMs), in(_overrideDueMs), in(_mineDueMs), in(_detonatorDueMs), _bombsBuilt, _blasts,
            _plateTouchesDone, _detonations, _detonatorsStopped, Factor(), _packages.size());
        for (std::unique_ptr<ThermapluggHardMode> const& package : _packages)
        {
            std::string const line = package->Describe();
            if (!line.empty())
                text += " | " + line;
        }
        return text;
    }

private:
    ModeValues Values() const
    {
        return ValuesFor(_mode);
    }

    // The packages' factors on his percent hits (MT21).
    float Factor() const
    {
        std::vector<float> factors;
        for (std::unique_ptr<ThermapluggHardMode> const& package : _packages)
            factors.push_back(package->DamageFactor(*this));
        return CombinedFactor(factors);
    }

    void StartClocks()
    {
        ModeValues const v = Values();
        _faceDueMs = Tune::kFaceFirstMs;
        _overrideDueMs = v.overrideEveryMs;
        _mineDueMs = Tune::kMineFirstMs;
        _knockDueMs = Tune::kKnockFirstMs;
        _detonatorDueMs = v.detonatorEveryMs ? Tune::kDetonatorFirstMs : 0;
        if (_detonatorDueMs)
            Mechanic::NoteNextCastIn(me, SPELL_MT_DETONATOR, Ms(_detonatorDueMs));
    }

    // The face stalkers at the alcove mouths (the beam's end, the bombs' start) and the plates' anchors.
    void SummonStalkers()
    {
        for (uint32 i = 0; i < kFaceCount; ++i)
        {
            if (Creature* stalker = me->SummonCreature(NPC_FACE_STALKER, ToPos(kBombStarts[i]),
                    TEMPSUMMON_MANUAL_DESPAWN))
                _faceStalkers[i] = stalker->GetGUID();
            if (Creature* anchor = me->SummonCreature(NPC_ZONE_STALKER, ToPos(kPlateSpots[i]),
                    TEMPSUMMON_MANUAL_DESPAWN))
                _plateAnchors[i] = anchor->GetGUID();
        }
    }

    GameObject* FaceObject(uint32 face)
    {
        if (face >= kFaceCount)
            return nullptr;
        if (GameObject* go = me->GetMap()->GetGameObject(_faceGos[face]))
            return go;
        GameObject* go = me->FindNearestGameObject(kFaceEntries[face], 120.f);
        _faceGos[face] = go ? go->GetGUID() : ObjectGuid::Empty;
        return go;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The beats: MT1 faces, MT6 Override, MT5 mines, MT7 Knock Away, MT14 Detonator, MT2 the chutes
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateBeats()
    {
        ModeValues const v = Values();
        if (_clockMs >= _faceDueMs)
        {
            std::vector<uint32> const picked = PickClosedFaces(OpenFaces(), 1, RandBelow);
            if (!picked.empty() && OpenOne(picked.front(), "timer"))
                Talk(EMOTE_MT_FACE);
            _faceDueMs = NextDue(_faceDueMs, v.faceEveryMs, _clockMs);
        }
        if (_clockMs >= _overrideDueMs)
        {
            Override("timer");
            _overrideDueMs = NextDue(_overrideDueMs, v.overrideEveryMs, _clockMs);
        }
        if (_clockMs >= _mineDueMs)
        {
            LayMines("timer");
            _mineDueMs = NextDue(_mineDueMs, v.mineEveryMs, _clockMs);
        }
        if (_clockMs >= _knockDueMs && !me->HasUnitState(UNIT_STATE_CASTING))
        {
            Unit* victim = me->GetVictim();
            if (victim && me->IsWithinMeleeRange(victim))
            {
                me->CastSpell(victim, SPELL_MT_KNOCK_AWAY, true);
                _knockDueMs = _clockMs + Tune::kKnockEveryMs;
            }
            else
                _knockDueMs = _clockMs + Tune::kKnockRetryMs;
        }
        if (_detonatorDueMs && v.detonatorEveryMs && _clockMs >= _detonatorDueMs
            && !me->HasUnitState(UNIT_STATE_CASTING))
        {
            if (StartDetonator())
                _detonatorDueMs = NextDue(_detonatorDueMs, v.detonatorEveryMs, _clockMs);
            else
                _detonatorDueMs = _clockMs + Tune::kDetonatorRetryMs;
            Mechanic::NoteNextCastIn(me, SPELL_MT_DETONATOR, Ms(_detonatorDueMs - _clockMs));
        }
        UpdateChutes();
    }

    // MT1: a face opens (GO state active), its beam and its plate come up.
    bool OpenOne(uint32 face, char const* why)
    {
        if (face >= kFaceCount || _faces[face].open)
            return false;
        FaceState& f = _faces[face];
        f.open = true;
        f.nextBuildMs = _clockMs + Tune::kBombFirstAfterOpenMs;
        if (GameObject* go = FaceObject(face))
            go->SetGoState(GO_STATE_ACTIVE);
        if (Creature* stalker = FaceStalker(face))
            stalker->CastSpell(me, SPELL_MT_FACE_BEAM, true);
        LightPlate(face);
        Log("face-open", Acore::StringFormat("face={} type={} why={} open={}", face + 1,
            kBombTypeNames[std::size_t(FaceBomb(_mode, face))], why, OpenCount(OpenFaces())));
        for (std::unique_ptr<ThermapluggHardMode>& package : _packages)
            package->OnFaceOpened(*this, face, why);
        return true;
    }

    void ShutFace(uint32 face, Player* by, char const* why)
    {
        if (face >= kFaceCount || !_faces[face].open)
            return;
        FaceState& f = _faces[face];
        f.open = false;
        if (f.soak)
            _plates.Cancel(me, f.soak);
        f.soak = 0;
        if (GameObject* go = FaceObject(face))
            go->SetGoState(GO_STATE_READY);
        Log("face-shut", Acore::StringFormat("face={} why={} by={} open={}", face + 1, why,
            by ? by->GetName() : std::string("none"), OpenCount(OpenFaces())));
        for (std::unique_ptr<ThermapluggHardMode>& package : _packages)
            package->OnFaceShut(*this, face, by);
    }

    // MT6: three closed faces open at once (heroic and up: every closed face).
    void Override(char const* why)
    {
        std::vector<uint32> const picked = PickClosedFaces(OpenFaces(), Values().overrideFaces, RandBelow);
        Talk(SAY_MT_OVERRIDE);
        Talk(EMOTE_MT_OVERRIDE);
        for (uint32 const face : picked)
            OpenOne(face, "override");
        Log("override", Acore::StringFormat("why={} opened={} open={}", why, picked.size(),
            OpenCount(OpenFaces())));
    }

    // MT2: every open face's chute.
    void UpdateChutes()
    {
        ModeValues const v = Values();
        for (uint32 i = 0; i < kFaceCount; ++i)
        {
            FaceState& f = _faces[i];
            if (!f.open || _clockMs < f.nextBuildMs)
                continue;
            BombType const type = FaceBomb(_mode, i);
            f.nextBuildMs = NextDue(f.nextBuildMs, ChuteEveryMs(type), _clockMs);
            if (type == BombType::Sticky)
            {
                if (FireSticky(i, nullptr))
                    ++f.built;
                continue;
            }
            if (type == BombType::BigOne)
            {
                if (SpawnBigOne(i))
                    ++f.built;
                continue;
            }
            if (!ChuteMayBuild(v.bombCap, static_cast<uint32>(Bombs().size())))
            {
                Log("chute-capped", Acore::StringFormat("face={} alive={} cap={}", i + 1, Bombs().size(), v.bombCap));
                continue;
            }
            if (Player* target = PickBombTarget())
                if (SpawnWalker(i, type, target))
                    ++f.built;
        }
    }

    // MT3: a random player of the fight, the tank included (rule 36: bombs fixate their marked player).
    Player* PickBombTarget()
    {
        std::vector<Player*> players = FightPlayers();
        if (players.empty())
            return nullptr;
        return players[RandBelow(static_cast<uint32>(players.size()))];
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MT3, MT8-MT11 the walking bombs; MT13 The Big One
    // ----------------------------------------------------------------------------------------------------------------

    Creature* SummonBomb(uint32 face, BombType type)
    {
        DungeonKit::WaveSpec spec;
        spec.entry = BombEntry(type);
        spec.health = type == BombType::BigOne ? 0 : Values().bombHealth;
        spec.passive = true;
        spec.type = TEMPSUMMON_CORPSE_TIMED_DESPAWN;
        spec.despawn = Ms(Tune::kBombDespawnMs);
        Position at = ToPos(kBombStarts[face % kFaceCount]);
        float z = at.GetPositionZ();
        me->UpdateAllowedPositionZ(at.GetPositionX(), at.GetPositionY(), z);
        at.m_positionZ = z;
        at.SetOrientation(at.GetAngle(kRoomCenter.x, kRoomCenter.y));
        std::vector<Creature*> const wave = DungeonKit::SummonWave(me, spec, { at }, summons);
        if (wave.empty())
            return nullptr;
        ++_bombsBuilt;
        return wave.front();
    }

    bool SpawnWalker(uint32 face, BombType type, Unit* target)
    {
        Creature* bomb = SummonBomb(face, type);
        if (!bomb)
            return false;
        if (!SetupWalker(bomb, type, face, target, false))
        {
            bomb->DespawnOrUnsummon();
            return false;
        }
        return true;
    }

    DungeonKit::ChaserSpec ChaseSpec(ObjectGuid guid)
    {
        DungeonKit::ChaserSpec chase;
        chase.speed = Tune::kBombSpeedYdPerSec;
        chase.honorSlows = true;
        chase.reach = Tune::kBombReachYd;
        chase.pauseOnControl = Ms(Tune::kStopOnControlMs);
        chase.life = Ms(0);                 // the fuse is the script's (it survives a Duplication's pause)
        chase.endOnArrive = true;
        chase.tauntImmune = false;          // passive: no threat to taunt
        chase.fixate = false;
        chase.pick.nonTank = false;         // the tank is in every pick
        chase.onArrive = [this, guid](Creature*, Unit*) { _explode.emplace_back(guid, "reached"); };
        chase.onEnd = [this, guid](Creature*, DungeonKit::ChaseEnd why)
        {
            _explode.emplace_back(guid, why == DungeonKit::ChaseEnd::NoTarget ? "no-target" : "fuse");
        };
        chase.onTarget = [this, guid](Creature*, Unit* newTarget) { Retarget(guid, newTarget); };
        return chase;
    }

    BombState* SetupWalker(Creature* bomb, BombType type, uint32 face, Unit* target, bool copy)
    {
        if (!bomb || !target)
            return nullptr;
        auto entry = std::make_unique<BombState>();
        entry->guid = bomb->GetGUID();
        entry->type = type;
        entry->face = face;
        entry->bornMs = _clockMs;
        if (!entry->chase.Start(bomb, target, ChaseSpec(entry->guid), me))
            return nullptr;
        if (Tune::kDrawBombRings)
        {
            MechanicRef ring = Mechanic::Circle(me, bomb, Tune::kBombBlastYd, Ms(Tune::kBombRingWarnMs));
            ring.NoFillTimer().ZTolerance(Tune::kBlastZBandYd).Tag(TAG_MT_BOMB_RING);
            entry->ring = ring.Handle();
        }
        BombState* raw = entry.get();
        _bombs.push_back(std::move(entry));
        Mark(*raw, target);
        Log("bomb", Acore::StringFormat("type={} face={} target={} copy={} alive={}", kBombTypeNames[std::size_t(type)],
            face + 1, target->GetName(), copy ? 1 : 0, Bombs().size()));
        for (std::unique_ptr<ThermapluggHardMode>& package : _packages)
            package->OnBombSpawned(*this, bomb, type, copy);
        return raw;
    }

    // The mark (on the target, the bomb its caster) and the bots' keep-away move with the bomb's target.
    void Mark(BombState& b, Unit* target)
    {
        Creature* bomb = me->GetMap()->GetCreature(b.guid);
        if (Unit* old = b.target.IsEmpty() ? nullptr : ObjectAccessor::GetUnit(*me, b.target))
            old->RemoveAurasDueToSpell(SPELL_MT_BOMB_MARK, b.guid);
        if (b.keepAway)
            Mechanic::Cancel(me, b.keepAway);
        b.keepAway = {};
        b.target = target ? target->GetGUID() : ObjectGuid::Empty;
        if (!target)
            return;
        if (bomb)
            bomb->AddAura(SPELL_MT_BOMB_MARK, target);
        MechanicRef run = Mechanic::RunOut(me, target, Tune::kBombBlastYd, Ms(Tune::kBombRingWarnMs));
        run.NoTelegraph().Tag(TAG_MT_BOMB_RUN).Within(_bounds);
        b.keepAway = run.Handle();
    }

    void Retarget(ObjectGuid guid, Unit* target)
    {
        if (BombState* b = FindBomb(guid); b && !b->done)
        {
            Mark(*b, target);
            Log("bomb-retarget", Acore::StringFormat("target={}", target ? target->GetName() : std::string("none")));
        }
    }

    // MT13: The Big One walks to the room's center; the Stack on it tells the bots to meet it there.
    bool SpawnBigOne(uint32 face)
    {
        Creature* bigOne = SummonBomb(face, BombType::BigOne);
        if (!bigOne)
            return false;
        auto entry = std::make_unique<BombState>();
        entry->guid = bigOne->GetGUID();
        entry->type = BombType::BigOne;
        entry->face = face;
        entry->bornMs = _clockMs;
        Position const center = ToPos(kRoomCenter);
        float const walk = bigOne->GetExactDist2d(center.GetPositionX(), center.GetPositionY());
        uint32 const walkMs = WalkMs(walk, Tune::kBigOneSpeedYdPerSec);
        entry->stackMs = BigOneStackMs(walkMs);
        bigOne->SetReactState(REACT_PASSIVE);
        DungeonKit::SetRunSpeedPct(bigOne, Tune::kBigOneSpeedYdPerSec / 7.f * 100.f);
        bigOne->GetMotionMaster()->MovePoint(kBigOnePoint, center);
        // The Stack resolves when the walk should end, and the bomb blows then (BigOneBlows): the bots, the drill and
        // the blast agree (STAGE-R-1-C Minor-2).
        MechanicRef stack = Mechanic::Stack(me, bigOne, Tune::kBigOneYd, Ms(entry->stackMs));
        stack.Tag(TAG_MT_BIG_ONE).Within(_bounds);
        entry->stack = stack.Handle();
        _bombs.push_back(std::move(entry));
        Talk(EMOTE_MT_BIG_ONE);
        Log("big-one", Acore::StringFormat("face={} walk={:.1f}yd {}ms", face + 1, walk, walkMs));
        for (std::unique_ptr<ThermapluggHardMode>& package : _packages)
            package->OnBombSpawned(*this, bigOne, BombType::BigOne, false);
        return true;
    }

    // Every tick: the chases move (held while a bomb casts), the fuses burn, The Big One arrives, and the blasts the
    // callbacks asked for go off.
    void UpdateBombs(uint32 diff)
    {
        Position const center = ToPos(kRoomCenter);
        for (std::unique_ptr<BombState> const& entry : _bombs)
        {
            BombState& b = *entry;
            if (b.done)
                continue;
            Creature* bomb = me->GetMap()->GetCreature(b.guid);
            if (!bomb || !bomb->IsAlive())
                continue;
            if (b.type == BombType::BigOne)
            {
                if (BigOneBlows(_clockMs - b.bornMs, b.stackMs))
                {
                    bool const atCenter = bomb->GetExactDist2d(center.GetPositionX(), center.GetPositionY())
                        <= Tune::kBigOneArriveYd;
                    _explode.emplace_back(b.guid, atCenter ? "arrived" : b.moveEnded ? "short" : "late");
                }
                continue;
            }
            if (_clockMs >= b.bornMs + Tune::kBombFuseMs)
            {
                _explode.emplace_back(b.guid, "fuse");
                continue;
            }
            bool const casting = bomb->HasUnitState(UNIT_STATE_CASTING);
            if (casting && !b.paused)
            {
                b.chase.Stop(bomb);
                bomb->StopMoving();
                b.paused = true;
                continue;
            }
            if (!casting && b.paused)
            {
                b.paused = false;
                Unit* target = ObjectAccessor::GetUnit(*me, b.target);
                if (!target || !target->IsAlive())
                    target = PickBombTarget();
                if (!target || !b.chase.Start(bomb, target, ChaseSpec(b.guid), me))
                {
                    _explode.emplace_back(b.guid, "no-target");
                    continue;
                }
                if (target->GetGUID() != b.target)
                    Mark(b, target);
                continue;
            }
            if (!b.paused)
                b.chase.Update(bomb, diff);
        }
        std::vector<std::pair<ObjectGuid, char const*>> queue;
        queue.swap(_explode);
        for (auto const& [guid, why] : queue)
            ExplodeBomb(guid, why, std::nullopt);
        std::vector<std::pair<ObjectGuid, Position>> killed;
        killed.swap(_killedBlasts);
        for (auto const& [guid, at] : killed)
            ExplodeBomb(guid, "killed", at);
        _bombs.erase(std::remove_if(_bombs.begin(), _bombs.end(),
            [](std::unique_ptr<BombState> const& b) { return b->done; }), _bombs.end());
    }

    BombState* FindBomb(ObjectGuid guid)
    {
        for (std::unique_ptr<BombState> const& b : _bombs)
            if (b->guid == guid)
                return b.get();
        return nullptr;
    }

    BombState const* FindBomb(ObjectGuid guid) const
    {
        for (std::unique_ptr<BombState> const& b : _bombs)
            if (b->guid == guid)
                return b.get();
        return nullptr;
    }

    void ReleaseMechanics(BombState& b)
    {
        for (MechanicHandle* h : { &b.ring, &b.keepAway, &b.stack })
        {
            if (*h)
                Mechanic::Cancel(me, *h);
            *h = {};
        }
        if (Unit* target = b.target.IsEmpty() ? nullptr : ObjectAccessor::GetUnit(*me, b.target))
            target->RemoveAurasDueToSpell(SPELL_MT_BOMB_MARK, b.guid);
        b.target = ObjectGuid::Empty;
    }

    // A walking bomb killed: normal, it falls apart; heroic and up, it blows where it died (MT8).
    void BombKilled(Creature* bomb)
    {
        BombState* b = FindBomb(bomb->GetGUID());
        if (!b || b->done)
            return;
        if (Values().blowWhenKilled && b->type != BombType::BigOne)
        {
            _killedBlasts.emplace_back(b->guid, bomb->GetPosition());
            return;
        }
        BombGone(b->guid, "killed");
    }

    // A bomb left without a blast (killed on normal, no target, despawned): its mechanics go, the packages hear it.
    void BombGone(ObjectGuid guid, char const* why)
    {
        BombState* b = FindBomb(guid);
        if (!b || b->done)
            return;
        b->done = true;
        ReleaseMechanics(*b);
        if (Creature* bomb = me->GetMap()->GetCreature(guid))
            if (bomb->IsAlive())
                b->chase.Stop(bomb);
        Log("bomb-gone", Acore::StringFormat("type={} why={}", kBombTypeNames[std::size_t(b->type)], why));
        for (std::unique_ptr<ThermapluggHardMode>& package : _packages)
            package->OnBombGone(*this, guid, why);
    }

    void ExplodeBomb(ObjectGuid guid, char const* why, std::optional<Position> at)
    {
        BombState* b = FindBomb(guid);
        if (!b || b->done)
            return;
        if (std::string(why) == "no-target")
        {
            BombGone(guid, why);    // first: the despawn's own report then finds it gone
            if (Creature* bomb = me->GetMap()->GetCreature(guid))
                bomb->DespawnOrUnsummon();
            return;
        }
        b->done = true;
        Creature* bomb = me->GetMap()->GetCreature(guid);
        Position const spot = at ? *at : bomb ? bomb->GetPosition() : me->GetPosition();
        if (bomb && bomb->IsAlive())
        {
            b->chase.Stop(bomb);
            bomb->StopMoving();
        }
        ReleaseMechanics(*b);
        ++_blasts;
        if (b->type == BombType::BigOne)
            BigOneBlast(spot, why);
        else
            WalkerBlast(b->type, spot, why);
        if (bomb)
            bomb->DespawnOrUnsummon(Ms(bomb->IsAlive() ? 200 : Tune::kBombDespawnMs));
        for (std::unique_ptr<ThermapluggHardMode>& package : _packages)
            package->OnBombGone(*this, guid, "blast");
    }

    GuidSet PlayersWithin(Position const& at, float radius)
    {
        GuidSet out;
        for (Player* player : FightPlayers())
            if (GnomerThermaplugg::InBlast(Vec2{ at.GetPositionX(), at.GetPositionY() }, at.GetPositionZ(),
                    DungeonKit::PlaneOf(player), player->GetPositionZ(), radius, Tune::kBlastZBandYd))
                out.insert(player->GetGUID());
        return out;
    }

    // A look at a spot: a short-lived zone stalker plays it (a dead bomb cannot cast).
    void PlayLookAt(Position const& at, uint32 spellId, uint32 forMs = 3000)
    {
        if (Creature* stalker = me->SummonCreature(NPC_ZONE_STALKER, at, TEMPSUMMON_TIMED_DESPAWN, forMs))
            stalker->CastSpell(stalker, spellId, true);
    }

    // MT3, MT8-MT11: the walking bomb's blast on everyone within 8 yd (the tank included), its rider, the fire patch.
    void WalkerBlast(BombType type, Position const& at, char const* why)
    {
        float const pct = Values().blastPct * Factor();
        BlastKind const kind = BlastOf(type);
        GuidSet const hit = PlayersWithin(at, Tune::kBombBlastYd);
        if (!hit.empty())
        {
            DungeonKit::RegistryHitSpec spec;
            spec.pct = pct;
            spec.tankPct = pct;
            spec.school = kind.school;
            spec.spellId = kind.spellId;
            spec.weakened = true;
            spec.rider = kind.rider;
            spec.tag = TAG_MT_BOMB_BLAST;
            Track(DungeonKit::RegistryHit(me, hit, spec));
        }
        PlayLookAt(at, SPELL_MT_BLAST_LOOK);
        if (type == BombType::Incendiary)
            FirePatch(at);
        Log("bomb-blast", Acore::StringFormat("type={} why={} at=({:.1f}, {:.1f}) hits={} pct={:.1f}",
            kBombTypeNames[std::size_t(type)], why, at.GetPositionX(), at.GetPositionY(), hit.size(), pct));
        if (!hit.empty())
            _pendingHits.push_back({ HitSource::Bomb, ObjectGuid::Empty, hit });
    }

    // MT9: an 8 yd patch for 20 s, 15% a second (a stalker carries the look; the registry owns the ticks).
    void FirePatch(Position const& at)
    {
        DungeonKit::LingerSpec linger;
        linger.duration = Ms(Tune::kFirePatchMs);
        linger.tick = Ms(Tune::kFirePatchTickMs);
        linger.pct = Tune::kFirePatchPct * Factor();
        linger.school = SPELL_SCHOOL_FIRE;
        linger.spellId = SPELL_MT_FIRE_PATCH;
        linger.slow = false;
        linger.tag = TAG_MT_FIRE_PATCH;
        MechanicHandle const patch = DungeonKit::Linger(me, BossMechanics::Shapes::Circle(at, Tune::kFirePatchYd),
            linger).Within(_bounds);
        Track(patch);
        if (Creature* stalker = me->SummonCreature(NPC_ZONE_STALKER, at, TEMPSUMMON_TIMED_DESPAWN,
                Tune::kFirePatchMs + 500))
        {
            stalker->CastSpell(stalker, SPELL_MT_FIRE_PATCH_CAST, true);
            stalker->CastSpell(stalker, SPELL_MT_FIRE_PATCH_LOOK, true);
        }
        Log("fire-patch", Acore::StringFormat("at=({:.1f}, {:.1f})", at.GetPositionX(), at.GetPositionY()));
    }

    // MT13: 100% split among the players within 8 yd; nobody there: everyone takes the whole blast. Never Weakened.
    void BigOneBlast(Position const& at, char const* why)
    {
        float const total = Tune::kBigOnePct * Factor();
        GuidSet inside = PlayersWithin(at, Tune::kBigOneYd);
        bool const shared = !inside.empty();
        GuidSet const hit = shared ? inside : [this]()
        {
            GuidSet all;
            for (Player* player : FightPlayers())
                all.insert(player->GetGUID());
            return all;
        }();
        float const each = BigOneSharePct(static_cast<uint32>(inside.size()), total);
        if (!hit.empty())
        {
            DungeonKit::RegistryHitSpec spec;
            spec.pct = each;
            spec.tankPct = each;
            spec.school = SPELL_SCHOOL_FIRE;
            spec.spellId = SPELL_MT_BIG_ONE_BLAST;
            spec.weakened = false;
            spec.tag = TAG_MT_BOMB_BLAST;
            Track(DungeonKit::RegistryHit(me, hit, spec));
        }
        PlayLookAt(at, SPELL_MT_BLAST_LOOK);
        PlayLookAt(at, SPELL_MT_BLAST_FLASH);
        Log("big-one-blast", Acore::StringFormat("why={} at=({:.1f}, {:.1f}) inside={} each={:.1f}%", why,
            at.GetPositionX(), at.GetPositionY(), inside.size(), each));
        if (!hit.empty())
            _pendingHits.push_back({ HitSource::BigOne, ObjectGuid::Empty, hit });
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MT12 the Sticky Bomb
    // ----------------------------------------------------------------------------------------------------------------

    bool FireSticky(uint32 face, Player* forced)
    {
        Player* carrier = forced ? forced : PickBombTarget();
        if (!carrier)
            return false;
        float const pct = Values().stickyPct * Factor();
        if (Creature* stalker = FaceStalker(face))
            stalker->CastSpell(carrier, SPELL_MT_MINE_LOB, true);
        me->AddAura(SPELL_MT_STICKY_BOMB, carrier);
        Talk(EMOTE_MT_STICKY, carrier);
        ObjectGuid const carrierGuid = carrier->GetGUID();
        std::weak_ptr<std::vector<QueuedHit>> queue = _registryHits;
        MechanicRef run = Mechanic::RunOut(me, carrier, Tune::kStickyYd, Ms(Tune::kStickyFuseMs));
        run.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_FIRE).Spell(SPELL_MT_STICKY_BLAST).Tag(TAG_MT_STICKY)
            .Within(_bounds).OnResolve([queue, carrierGuid](BossMechanics::ResolveResult const& r)
            {
                if (std::shared_ptr<std::vector<QueuedHit>> q = queue.lock())
                    q->push_back({ HitSource::Sticky, carrierGuid, GuidSet(r.hits.begin(), r.hits.end()) });
            });
        Track(run.Handle());
        _stickies.push_back({ carrierGuid, _clockMs + Tune::kStickyFuseMs });
        Log("sticky", Acore::StringFormat("face={} carrier={} pct={:.1f}", face + 1, carrier->GetName(), pct));
        return true;
    }

    // The fuse's end: the bomb leaves the carrier with its flash (the RunOut dealt the hits).
    void UpdateStickies()
    {
        for (auto it = _stickies.begin(); it != _stickies.end();)
        {
            if (_clockMs < it->dueMs)
            {
                ++it;
                continue;
            }
            if (Player* carrier = ObjectAccessor::GetPlayer(*me, it->carrier))
            {
                carrier->RemoveAurasDueToSpell(SPELL_MT_STICKY_BOMB, me->GetGUID());
                PlayLookAt(carrier->GetPosition(), SPELL_MT_BLAST_FLASH);
            }
            it = _stickies.erase(it);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MT5 the mines
    // ----------------------------------------------------------------------------------------------------------------

    void ConfigureMines()
    {
        ModeValues const v = Values();
        DungeonKit::TwoRingMineSpec spec;
        spec.triggerYd = Tune::kMineTriggerYd;
        spec.blastYd = Tune::kMineBlastYd;
        spec.zBand = Tune::kBlastZBandYd;
        spec.arm = Ms(Tune::kMineArmMs);
        spec.grace = Ms(Tune::kMineGraceMs);
        spec.life = Ms(v.mineLifeMs);
        spec.pct = v.minePct * Factor();
        spec.tankPct = spec.pct;
        spec.school = SPELL_SCHOOL_FIRE;
        spec.spellId = SPELL_MT_MINE_BLAST;
        spec.weakened = true;
        spec.tag = TAG_MT_MINE;
        BossMechanics::SpotBounds const bounds = _bounds;
        spec.configureTrigger = [bounds](MechanicRef& ref) { ref.Within(bounds); };
        spec.configureBlast = [bounds](MechanicRef& ref) { ref.Tag(TAG_MT_MINE_RING).Within(bounds); };
        spec.onBlast = [this](Creature*, uint32 id, Position const& at, GuidSet const& hit, bool tripped)
        {
            MineBlasted(id, at, hit, tripped);
        };
        spec.dungeon = kLogDungeon;
        spec.boss = kBoss;
        spec.name = "mine";
        _mines.Configure(std::move(spec));
    }

    // Three random players (heroic: every player) get a mine at their feet, with his stock line.
    void LayMines(char const* why)
    {
        std::vector<Player*> players = FightPlayers();
        if (players.empty())
            return;
        uint32 const n = MineTargets(Values().mineCount, static_cast<uint32>(players.size()));
        Acore::Containers::RandomResize(players, n);
        ConfigureMines();       // this wave's percent (the hard mode's factor) and life
        Talk(SAY_MT_MINES);
        uint32 laid = 0;
        for (Player* player : players)
        {
            Position const at = player->GetPosition();
            me->CastSpell(player, SPELL_MT_MINE_LOB, true);
            uint32 const id = _mines.Add(me, at);
            if (!id)
                continue;
            ++laid;
            ++_minesLaid;
            if (Creature* body = me->SummonCreature(NPC_MINE, at, TEMPSUMMON_TIMED_DESPAWN,
                    Values().mineLifeMs + 2000))
                _mineBodies[id] = body->GetGUID();
        }
        Log("mines", Acore::StringFormat("why={} laid={} live={}", why, laid, _mines.Count()));
    }

    void MineBlasted(uint32 id, Position const& at, GuidSet const& hit, bool tripped)
    {
        auto it = _mineBodies.find(id);
        if (it != _mineBodies.end())
        {
            if (Creature* body = me->GetMap()->GetCreature(it->second))
            {
                body->CastSpell(body, SPELL_MT_MINE_LOOK, true);
                body->DespawnOrUnsummon(Ms(1000));
            }
            _mineBodies.erase(it);
        }
        (void)tripped;
        if (!hit.empty())
            _pendingHits.push_back({ HitSource::Mine, ObjectGuid::Empty, hit });
        (void)at;
    }

    // A mine whose life ran out goes without a blast (KT-G Q4): its body goes too.
    void SyncMineBodies()
    {
        if (_mineBodies.empty())
            return;
        std::vector<uint32> const ids = _mines.Ids();
        for (auto it = _mineBodies.begin(); it != _mineBodies.end();)
        {
            if (std::find(ids.begin(), ids.end(), it->first) != ids.end())
            {
                ++it;
                continue;
            }
            if (Creature* body = me->GetMap()->GetCreature(it->second))
                body->DespawnOrUnsummon();
            it = _mineBodies.erase(it);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MT4 the plates
    // ----------------------------------------------------------------------------------------------------------------

    void LightPlate(uint32 face)
    {
        Creature* anchor = PlateAnchor(face);
        if (!anchor)
            return;
        DungeonKit::DwellSoakSpec spec;
        spec.radius = Tune::kPlateTouchYd;
        spec.zBand = Tune::kBlastZBandYd;
        spec.dwell = Ms(0);
        spec.life = Ms(0);
        spec.count = 1;
        spec.excludeAura = SPELL_MT_LOCKED_OUT;
        spec.oneClaimPerBot = true;
        spec.draw = true;
        spec.tag = TAG_MT_PLATE;
        spec.rank = PlateRank(_mode, face);
        BossMechanics::SpotBounds const bounds = _bounds;
        // The rule now at every registration (D6's non-tanks first, or a package's SetPlatePlan): shared, not `this`.
        std::shared_ptr<BossMechanics::Ordering const> const order = _plateOrder;
        spec.configure = [bounds, order](MechanicRef& ref)
        {
            ref.Order(*order).Within(bounds);
        };
        spec.onDone = [this, face](Player* taker, Unit*)
        {
            if (taker)
                _plateTouches.emplace_back(face, taker->GetGUID());
        };
        spec.dungeon = kLogDungeon;
        spec.boss = kBoss;
        spec.name = "plate";
        _faces[face].soak = _plates.Add(me, anchor, std::move(spec));
    }

    // The touches the plates reported this tick (queued: never inside DwellSoaks' own loop).
    void TakePlateTouches()
    {
        std::vector<std::pair<uint32, ObjectGuid>> touches;
        touches.swap(_plateTouches);
        for (auto const& [face, guid] : touches)
        {
            Player* player = ObjectAccessor::GetPlayer(*me, guid);
            _faces[face].soak = 0;      // the held Soak is already gone
            if (!CountsAsPlayer(player) || !PlateTakes(FaceOpen(face), LockedOut(player)))
            {
                if (FaceOpen(face))
                    LightPlate(face);   // a touch that did not count: the plate glows again
                continue;
            }
            ShutFace(face, player, "plate");
            me->AddAura(SPELL_MT_LOCKED_OUT, player);
            ++_plateTouchesDone;
            Log("plate", Acore::StringFormat("face={} by={} touches={}", face + 1, player->GetName(),
                _plateTouchesDone));
            for (std::unique_ptr<ThermapluggHardMode>& package : _packages)
                package->OnPlateTouched(*this, player, face);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MT14 Remote Detonator
    // ----------------------------------------------------------------------------------------------------------------

    bool StartDetonator()
    {
        me->StopMoving();
        SpellCastResult const result = me->CastSpell(me, SPELL_MT_DETONATOR, false);
        if (result != SPELL_CAST_OK)
        {
            Log("detonator-refused", Acore::StringFormat("result={}", uint32(result)));
            return false;
        }
        Talk(EMOTE_MT_DETONATOR);
        Log("detonator", Acore::StringFormat("bombs={} armed={}", Bombs().size(), _mines.ArmedCount()));
        return true;
    }

    // Every living bomb blows where it is, then every armed mine (KT-G Q3: armed only).
    void Detonate(char const* why)
    {
        ++_detonations;
        std::vector<ObjectGuid> const bombs = Bombs();
        for (ObjectGuid const& guid : bombs)
            ExplodeBomb(guid, "detonator", std::nullopt);
        uint32 const mines = _mines.DetonateAll(me, true);
        SyncMineBodies();
        Log("detonate", Acore::StringFormat("why={} bombs={} mines={}", why, bombs.size(), mines));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Hooks, thresholds, boss data
    // ----------------------------------------------------------------------------------------------------------------

    void FlushHits()
    {
        std::vector<QueuedHit> queued;
        queued.swap(*_registryHits);
        for (QueuedHit& q : queued)
            _pendingHits.push_back(std::move(q));
        std::vector<QueuedHit> pending;
        pending.swap(_pendingHits);
        for (QueuedHit const& q : pending)
        {
            if (q.hit.empty())
                continue;
            Position at = me->GetPosition();
            if (!q.anchor.IsEmpty())
                if (Unit* anchor = ObjectAccessor::GetUnit(*me, q.anchor))
                    at = anchor->GetPosition();
            if (q.source == HitSource::Sticky)
                Log("sticky-blast", Acore::StringFormat("hits={}", q.hit.size()));
            for (std::unique_ptr<ThermapluggHardMode>& package : _packages)
                package->OnPlayersHit(*this, q.source, at, q.hit);
        }
    }

    void UpdateThresholds()
    {
        if (_packages.empty())
            return;
        float const pct = me->GetHealthPct();
        for (std::size_t i = 0; i < _packages.size() && i < _thresholds.size(); ++i)
            for (float const t : _thresholds[i].Crossed(pct))
            {
                Log("threshold", Acore::StringFormat("package={} at={:.0f}% health={:.1f}%", i, t, pct));
                _packages[i]->OnHealthPct(*this, t);
            }
    }

    // SP Bots: the walking bombs before him for the ranged (heroic: only those 8 yd from every player, MT8, and
    // nobody's damage on one near a player); melee cleave a bomb that reached him (normal); the Detonator on the
    // interrupt list; the Frost root and the Radioactive Poison on the dispel list (rewards); the plates, the mines,
    // the Sticky Bomb and The Big One are registry kinds.
    void Describe()
    {
        using BossMechanics::Condition;
        using BossMechanics::Who;
        BossMechanics::Descriptor d;
        bool const heroic = _mode != Mode::Normal;
        for (uint32 const entry : kWalkingBombEntries)
        {
            if (!heroic)
            {
                if (entry != NPC_WALKING_BOMB)
                    continue;
                d.targets.push_back(BossMechanics::TargetEntry(entry, Tune::kBombTargetPriority, Who::Ranged)
                    .AoeOk());
                d.targets.push_back(BossMechanics::TargetEntry(entry, Tune::kBombTargetPriority, Who::Melee,
                    Condition::NearUnit(NPC_THERMAPLUGG, Tune::kBombBlastYd)).AoeOk());
                continue;
            }
            d.targets.push_back(BossMechanics::TargetEntry(entry, Tune::kBombTargetPriority, Who::Ranged,
                Condition::Not(Condition::NearPlayer(Tune::kBombBlastYd))));
            d.holds.push_back(BossMechanics::HoldEntry::Damage(entry, 0, BossMechanics::kSchoolMaskAll,
                Condition::NearPlayer(Tune::kBombBlastYd)));
        }
        for (uint32 const entry : { uint32(NPC_THE_BIG_ONE), uint32(NPC_FACE_STALKER), uint32(NPC_MINE),
                uint32(NPC_ZONE_STALKER) })
            d.ignores.emplace_back(entry);
        if (uint32 const every = Values().detonatorEveryMs)
            d.interrupts.emplace_back(NPC_THERMAPLUGG, SPELL_MT_DETONATOR, Tune::kDetonatorKickPriority, Ms(every));
        if (heroic)
        {
            d.dispels.emplace_back(SPELL_MT_FROST_ROOT, Tune::kFrostRootDispelPriority);
            d.dispels.emplace_back(SPELL_MT_RADIO_POISON, Tune::kRadioPoisonDispelPriority);
        }
        for (std::unique_ptr<ThermapluggHardMode>& package : _packages)
            package->DescribeExtra(*this, d);
        Mechanic::Describe(me, std::move(d));
    }

    // The fight's state: the packages undo theirs first (OnEnd), then nothing of D6's is left: no face open, no
    // bomb, stalker, mine, plate, handle or aura of the fight, his health given back (Reset, evade, death; RB-1).
    void Cleanup(bool won)
    {
        bool const wasEngaged = _engaged;
        _engaged = false;
        std::vector<std::unique_ptr<ThermapluggHardMode>> packages;
        packages.swap(_packages);
        if (wasEngaged)
            for (std::unique_ptr<ThermapluggHardMode>& package : packages)
                package->OnEnd(*this, won);
        packages.clear();
        _thresholds.clear();

        for (std::unique_ptr<BombState> const& b : _bombs)
        {
            if (Creature* bomb = me->GetMap()->GetCreature(b->guid); bomb && bomb->IsAlive())
                b->chase.Stop(bomb);
            ReleaseMechanics(*b);
        }
        _bombs.clear();
        _explode.clear();
        _killedBlasts.clear();
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        _plates.Clear(me);
        _plateTouches.clear();
        *_plateOrder = DefaultPlateOrder();
        _mines.Clear(me);
        _mineBodies.clear();
        _stickies.clear();
        _registryHits->clear();
        _pendingHits.clear();
        for (uint32 i = 0; i < kFaceCount; ++i)
        {
            _faces[i] = FaceState{};
            if (GameObject* go = me->IsInWorld() ? FaceObject(i) : nullptr)
                go->SetGoState(GO_STATE_READY);
        }
        summons.DespawnAll();
        _faceStalkers.fill(ObjectGuid::Empty);
        _plateAnchors.fill(ObjectGuid::Empty);
        if (instance)
            for (uint32 const spell : { uint32(SPELL_MT_BOMB_MARK), uint32(SPELL_MT_LOCKED_OUT),
                    uint32(SPELL_MT_STICKY_BOMB), uint32(SPELL_MT_FROST_ROOT), uint32(SPELL_MT_RADIO_POISON) })
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
        if (me->IsAlive() && !won && _baseHealth && me->GetMaxHealth() != _baseHealth)
            SetCreatureHealth(me, _baseHealth);
        _arena.Reset();
        _mode = Mode::Normal;
        _clockMs = 0;
        _faceDueMs = _overrideDueMs = _mineDueMs = _knockDueMs = _detonatorDueMs = 0;
        _lastKillLineMs = 0;
        _bombsBuilt = _blasts = _plateTouchesDone = _minesLaid = _detonations = _detonatorsStopped = 0;
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::Arena const _room;
    BossMechanics::SpotBounds const _bounds;
    std::vector<std::unique_ptr<ThermapluggHardMode>> _packages;
    std::vector<ThresholdLatch> _thresholds;
    std::vector<std::unique_ptr<BombState>> _bombs;
    std::vector<std::pair<ObjectGuid, char const*>> _explode;       // blasts the chases asked for (next tick)
    std::vector<std::pair<ObjectGuid, Position>> _killedBlasts;     // MT8: killed bombs, where they died
    std::array<FaceState, kFaceCount> _faces{};
    std::array<ObjectGuid, kFaceCount> _faceGos{};
    std::array<ObjectGuid, kFaceCount> _faceStalkers{};
    std::array<ObjectGuid, kFaceCount> _plateAnchors{};
    DungeonKit::DwellSoaks _plates;
    // The plates' Ordering (SetPlatePlan); LightPlate's configure holds a copy of the pointer.
    std::shared_ptr<BossMechanics::Ordering> _plateOrder =
        std::make_shared<BossMechanics::Ordering>(DefaultPlateOrder());
    std::vector<std::pair<uint32, ObjectGuid>> _plateTouches;
    DungeonKit::TwoRingMines _mines;
    std::unordered_map<uint32, ObjectGuid> _mineBodies;
    std::vector<StickyState> _stickies;
    std::shared_ptr<std::vector<QueuedHit>> _registryHits = std::make_shared<std::vector<QueuedHit>>();
    std::vector<QueuedHit> _pendingHits;
    std::vector<MechanicHandle> _live;
    Mode _mode = Mode::Normal;
    uint64 _clockMs = 0;            // ms since the pull: every timer of the fight
    uint64 _faceDueMs = 0;
    uint64 _overrideDueMs = 0;
    uint64 _mineDueMs = 0;
    uint64 _knockDueMs = 0;
    uint64 _detonatorDueMs = 0;     // 0: no Detonator in this mode
    uint64 _lastKillLineMs = 0;
    uint32 _baseHealth = 0;         // his template health (the hard mode's 800,000 is undone to it)
    uint32 _bombsBuilt = 0;
    uint32 _blasts = 0;
    uint32 _plateTouchesDone = 0;
    uint32 _minesLaid = 0;
    uint32 _detonations = 0;
    uint32 _detonatorsStopped = 0;
    bool _engaged = false;
};

// ---------------------------------------------------------------------------------------------------------------------
// The adds: the bombs (301120-301124) are passive bodies the boss drives (his Chaser, his MovePoint); the stalkers
// (301125 face, 301126 mine body, 301127 zone and plate) only stand there.
// ---------------------------------------------------------------------------------------------------------------------

struct npc_gnomer_walking_bomb : public ScriptedAI
{
    explicit npc_gnomer_walking_bomb(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    // Never walks home: the boss moves it, blows it up or despawns it.
    void EnterEvadeMode(EvadeReason /*why*/) override { }
    void UpdateAI(uint32 /*diff*/) override { }
};

struct npc_gnomer_thermaplugg_stalker : public NullCreatureAI
{
    explicit npc_gnomer_thermaplugg_stalker(Creature* creature) : NullCreatureAI(creature) { }
};

// ThermapluggFight.h's registry.
namespace GnomerThermaplugg
{
    void RegisterThermapluggHardMode(HardModePackage package, ThermapluggHardModeFactory factory)
    {
        if (package < HardModePackage::Count)
            Factories()[std::size_t(package)] = std::move(factory);
    }

    std::vector<std::unique_ptr<ThermapluggHardMode>> CreateThermapluggHardModes(ThermapluggFight& fight)
    {
        std::vector<std::unique_ptr<ThermapluggHardMode>> made;
        for (ThermapluggHardModeFactory const& factory : Factories())
            if (factory)
                if (std::unique_ptr<ThermapluggHardMode> object = factory(fight))
                    made.push_back(std::move(object));
        return made;
    }

    ThermapluggFight* FindThermapluggFight(Map* map)
    {
        InstanceMap* instanceMap = map ? map->ToInstanceMap() : nullptr;
        InstanceScript* script = instanceMap ? instanceMap->GetInstanceScript() : nullptr;
        if (!script || map->GetId() != kMapGnomeregan)
            return nullptr;
        Creature* boss = map->GetCreature(script->GetGuidData(kGuidBossBase + BOSS_THERMAPLUGG));
        if (!boss || !boss->IsAIEnabled)
            return nullptr;
        auto* ai = dynamic_cast<boss_thermaplugg_rework*>(boss->AI());
        return ai && ai->Engaged() ? ai : nullptr;
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// `.dbtest gnomer thermaplugg <subcommand>`
// ---------------------------------------------------------------------------------------------------------------------

namespace
{
    boss_thermaplugg_rework* ThermapluggAI(ChatHandler* handler)
    {
        Creature* boss = GnomerTest::FindBoss(handler, NPC_THERMAPLUGG);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_thermaplugg_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{} does not run the reworked script.", boss->GetName());
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_thermaplugg_rework::TestMechanic mechanic, char const* what,
        Optional<uint32> face = {})
    {
        boss_thermaplugg_rework* ai = ThermapluggAI(handler);
        if (!ai)
            return false;
        std::optional<uint32> const f = face ? std::optional<uint32>(*face) : std::nullopt;
        std::string const error = ai->TestFire(mechanic, handler->getSelectedPlayerOrSelf(), f);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Thermaplugg: {}.", what);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return GnomerTest::ShowBossInfo(handler, NPC_THERMAPLUGG, BOSS_THERMAPLUGG);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_thermaplugg_rework* ai = ThermapluggAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Thermaplugg: {}", ai->TestState());
        return true;
    }

    bool HandleFace(ChatHandler* handler, Optional<uint32> face)
    {
        return Fire(handler, boss_thermaplugg_rework::TestMechanic::Face, "a face opens (MT1; 1-6, else random)",
            face);
    }

    bool HandleShut(ChatHandler* handler, Optional<uint32> face)
    {
        return Fire(handler, boss_thermaplugg_rework::TestMechanic::Shut, "the face shuts (no lockout)", face);
    }

    bool HandleOverride(ChatHandler* handler)
    {
        return Fire(handler, boss_thermaplugg_rework::TestMechanic::Override, "Override (MT6)");
    }

    bool HandleBomb(ChatHandler* handler, Optional<uint32> face)
    {
        return Fire(handler, boss_thermaplugg_rework::TestMechanic::Bomb,
            "a walking bomb from the face (MT3; 1-4 on heroic, default 1) at the selected player", face);
    }

    bool HandleMines(ChatHandler* handler)
    {
        return Fire(handler, boss_thermaplugg_rework::TestMechanic::Mines, "a wave of mines (MT5)");
    }

    bool HandleSticky(ChatHandler* handler)
    {
        return Fire(handler, boss_thermaplugg_rework::TestMechanic::Sticky,
            "a Sticky Bomb on the selected player (MT12)");
    }

    bool HandleBigOne(ChatHandler* handler)
    {
        return Fire(handler, boss_thermaplugg_rework::TestMechanic::BigOne, "The Big One from face 6 (MT13)");
    }

    bool HandleDetonator(ChatHandler* handler)
    {
        return Fire(handler, boss_thermaplugg_rework::TestMechanic::Detonator, "Remote Detonator (MT14)");
    }

    bool HandleKnock(ChatHandler* handler)
    {
        return Fire(handler, boss_thermaplugg_rework::TestMechanic::Knock, "Knock Away on his target (MT7)");
    }

    // `.dbtest gnomer thermaplugg heroic [0|1]`: the heroic form on a normal map until the end of the pull.
    bool HandleHeroic(ChatHandler* handler, Optional<uint32> on)
    {
        boss_thermaplugg_rework* ai = ThermapluggAI(handler);
        if (!ai)
            return false;
        if (!ai->TestHeroic(on.value_or(1) != 0))
        {
            handler->SendErrorMessage("Only in combat and not in the hard mode.");
            return false;
        }
        handler->SendSysMessage("Set until the end of the pull (the reference row stays the map's).");
        return true;
    }

    ChatCommandTable const& ThermapluggTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",      HandleInfo,      SEC_GAMEMASTER, Console::No },
            { "state",     HandleState,     SEC_GAMEMASTER, Console::No },
            { "face",      HandleFace,      SEC_GAMEMASTER, Console::No },
            { "shut",      HandleShut,      SEC_GAMEMASTER, Console::No },
            { "override",  HandleOverride,  SEC_GAMEMASTER, Console::No },
            { "bomb",      HandleBomb,      SEC_GAMEMASTER, Console::No },
            { "mines",     HandleMines,     SEC_GAMEMASTER, Console::No },
            { "sticky",    HandleSticky,    SEC_GAMEMASTER, Console::No },
            { "bigone",    HandleBigOne,    SEC_GAMEMASTER, Console::No },
            { "detonator", HandleDetonator, SEC_GAMEMASTER, Console::No },
            { "knock",     HandleKnock,     SEC_GAMEMASTER, Console::No },
            { "heroic",    HandleHeroic,    SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_thermaplugg_rework()
{
    RegisterDungeonReworkCreatureAI(boss_thermaplugg_rework, GnomereganRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_gnomer_walking_bomb, GnomereganRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_gnomer_thermaplugg_stalker, GnomereganRework::kInstanceScriptName);
    GnomerTest::RegisterBoss("thermaplugg", ThermapluggTestCommands());
}
