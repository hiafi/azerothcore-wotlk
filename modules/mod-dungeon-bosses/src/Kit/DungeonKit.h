/*
 * mod-dungeon-bosses, the shared dungeon kit (WP-K0): engine glue every reworked dungeon's boss scripts use. Extracted
 * from the Deadmines Pilot's DeadminesKit (Deadmines keeps its names as aliases: DeadminesKit.h) and extended with the
 * generic helpers Shadowfang Keep asks for (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md
 * section 3.2). Pure parts: DungeonKitMath.h (tuning, geometry, frames), DungeonKitState.h (save strings, rolls),
 * DungeonKitArena.h (arenas, grip tracking), DungeonKitLogic.h (split, picks, stacks, lines, dwell). The arena guard is
 * ArenaGuard.h, the `.<x>test` command shell DungeonTestCommand.h.
 *
 *   AI factory          GetReworkAI / RegisterDungeonReworkCreatureAI(ai, kInstanceScriptName): the AI runs only
 *                       inside an instance bound to that instance script
 *   RefFlat             a percent of the reference row for a script's own spell (SpellScript damage)
 *   IsHeroicMap         the map is the heroic difficulty
 *   ImpactThenLinger    an impact Zone plus, on its resolve, a persistent Zone with its own tick damage and the shared
 *   Linger              "Standing in It" slow rider (SPELL_KIT_STANDING_IN_IT)
 *   CastBar             the boss casts a no-effect spell for the bar (and says an emote); the registry owns the hit
 *   ShortenAura         cut a stock aura's duration and keep its id
 *   ToPosition, PlaneOf, ToRoomFrame    frame points and frames as engine types
 *   JumpTo              a grip / reel / throw jump (players get the anticheat flag)
 *   PickPlayer(s)       one (or n distinct) random or farthest players with the common filters
 *   LineStrike          L4: a line from the source through the target, `overrun` past it, clipped to the arena walls
 *   LethalGuard         keeps a unit at 1 health instead of dying (a fake death / phase change)
 *   SplitShares         a shared hit split among the players inside (percent of the reference row), capped each
 *   AddStacks / Stacks  a stacking meter aura
 *   RollOnce            a once-per-instance chance, saved through the instance's SetData / GetData
 *   SpawnBreakableDoor  an attackable stand-in on a door's line; BreakableDoorAI opens the door when it dies
 *   Pickups             walk-over pickups: a registry Soak for the bots plus a proximity poll
 *   LogMechanic         one INFO line per firing in `module.dungeonbosses`
 *   SetRunSpeedPct      a chaser's run speed as a percent of a player's (SpeedFor)
 *   SetHardModeLoot     the hard mode loot bit on a boss (LOOT_MODE_HARD_MODE_1)
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_H

#include "BossMechanics.h"
#include "CreatureAIImpl.h"
#include "CreatureScript.h"
#include "DungeonKitArena.h"
#include "DungeonKitIds.h"
#include "DungeonKitLogic.h"
#include "DungeonKitMath.h"
#include "DungeonKitState.h"
#include "Duration.h"
#include "GameObjectScript.h"
#include "ObjectGuid.h"
#include "Position.h"
#include "ScriptedCreature.h"
#include <functional>
#include <optional>
#include <string>
#include <utility>
#include <vector>

class Creature;
class GameObject;
class InstanceScript;
class Player;
class Unit;
class WorldObject;

namespace DungeonKit
{
    // Kit-wide spells: SPELL_KIT_CAST_BAR, SPELL_KIT_STANDING_IN_IT (DungeonKitIds.h).

    char constexpr kLogCategory[] = "module.dungeonbosses";

    // ----------------------------------------------------------------------------------------------------------------
    // AI factory: the AI runs only inside an instance bound to `InstanceScriptName` (the stock GetXxxAI pattern)
    //
    //     char constexpr kInstanceScriptName[] = "instance_shadowfang_keep";      // a namespace-scope constant
    //     void AddSC_boss_rethilgore_rework()
    //     {
    //         RegisterDungeonReworkCreatureAI(boss_rethilgore_rework, ShadowfangKeepRework::kInstanceScriptName);
    //     }
    // ----------------------------------------------------------------------------------------------------------------
    template <char const* InstanceScriptName, class AI, class T>
    inline AI* GetReworkAI(T* obj)
    {
        return GetInstanceAI<AI>(obj, InstanceScriptName);
    }

#define RegisterDungeonReworkCreatureAI(ai_name, instance_script_name) \
    new FactoryCreatureScript<ai_name, &DungeonKit::GetReworkAI<instance_script_name, ai_name, Creature>>(#ai_name)
#define RegisterDungeonReworkGameObjectAI(ai_name, instance_script_name) \
    new FactoryGameObjectScript<ai_name, &DungeonKit::GetReworkAI<instance_script_name, ai_name, GameObject>>(#ai_name)

    // ----------------------------------------------------------------------------------------------------------------
    // Reference damage, difficulty
    // ----------------------------------------------------------------------------------------------------------------

    // `pct` percent of the reference health row the registry would pick for `owner` on its current map (its content
    // key: difficulty, the MapLevels pin, else its level): the tank row with `tank`, else the non-tank row. Rounded and
    // clamped like Damage(pct) / TankDamage(pct). A null owner or one not in the world returns 0. Call it at cast or
    // hit time, e.g. in a SpellScript:  SetHitDamage(DungeonKit::RefFlat(GetCaster(), 40.f));
    uint32 RefFlat(Unit const* owner, float pct, bool tank = false);

    // The map is a heroic difficulty (Map::IsHeroic). False without a map.
    bool IsHeroicMap(WorldObject const* me);

    // ----------------------------------------------------------------------------------------------------------------
    // Impact, linger, cast bar, auras
    // ----------------------------------------------------------------------------------------------------------------

    // The lingering half of ImpactThenLinger.
    struct LingerSpec
    {
        Milliseconds duration{ 10000 };
        Milliseconds tick{ 1000 };
        float pct = 5.f;                                        // per tick, % of reference non-tank health
        uint8 school = 0;                                       // SpellSchools: 0 physical .. 6 arcane
        uint32 spellId = 0;                                     // a dungeon copy of the resolve spell (0 = by school)
        bool slow = true;                                       // rider `slowSpell` on every tick hit
        std::optional<BossMechanics::ZoneSpec> shape;           // default: the impact's shape
        std::optional<BossMechanics::Color> color;              // default: the encounter's get-out color
        uint32 tag = 0;
        uint32 slowSpell = SPELL_KIT_STANDING_IN_IT;            // the rider when `slow`
    };

    // The impact half.
    struct ImpactSpec
    {
        BossMechanics::ZoneSpec shape;
        Milliseconds warn{ 2000 };
        float pct = 20.f;                                       // % of reference non-tank health
        float tankPct = -1.f;                                   // >= 0: the tank takes this % of tank health instead
        uint8 school = 0;
        uint32 spellId = 0;
        bool weakened = true;                                   // avoidable single hits apply Weakened
        uint32 tag = 0;
    };

    // Registers the impact Zone and, in its OnResolve, the lingering persistent Zone (one DamageSpec per mechanic, so
    // impact and linger are two registrations). The linger's first tick lands one tick after the impact, and it shows
    // its outline only until then (NoFillTimer). The impact's other options can still be chained on the returned ref
    // (it commits at the end of the calling statement); do not replace its OnResolve. Returns an invalid ref when the
    // registry refuses the impact.
    BossMechanics::MechanicRef ImpactThenLinger(Unit* owner, ImpactSpec const& impact, LingerSpec const& linger);

    // Just the lingering zone, now: the persistent Zone with LingerSpec's numbers on `shape`, its first tick one tick
    // from now.
    BossMechanics::MechanicRef Linger(Unit* owner, BossMechanics::ZoneSpec const& shape, LingerSpec const& linger);

    // The boss casts `spellId` (a no-effect spell with the cast time of the warning: SPELL_KIT_CAST_BAR, or the boss's
    // own named copy) on `target` (nullptr: itself) so players see a cast bar, and says `textGroup` (an emote line)
    // when given. Not triggered, so the cast bar shows; the registry mechanic registered beside it owns the hit.
    void CastBar(Creature* caster, uint32 spellId, Unit* target = nullptr, std::optional<uint8> textGroup = {},
        WorldObject const* textTarget = nullptr);

    // Cuts the aura `spellId` that `caster` put on `target` to `duration` (current and max), keeping the stock spell
    // so DD's heroic scaling still applies. Call it right after the cast lands. False when the aura is not there.
    bool ShortenAura(Unit* target, uint32 spellId, ObjectGuid caster, Milliseconds duration);

    // ----------------------------------------------------------------------------------------------------------------
    // Frames and points
    // ----------------------------------------------------------------------------------------------------------------

    // A measured frame point at height `z`.
    Position ToPosition(Vec2 p, float z, float orientation = 0.f);

    // A world object's position on the map plane.
    Vec2 PlaneOf(WorldObject const* o);

    // A FrameRect at height `z` as a mod-boss-mechanics room frame (Mechanic::RoomFrame lanes).
    BossMechanics::RoomFrame ToRoomFrame(FrameRect const& frame, float z);

    // ----------------------------------------------------------------------------------------------------------------
    // Movement
    // ----------------------------------------------------------------------------------------------------------------

    // Jumps `unit` to `dest` (Spell::EffectPullTowards' arc: speedZ from the 2D distance, at least `minSpeedZ`). With
    // `lookSpell` and `lookCaster`, `lookCaster` first casts it (triggered) on `unit` for the look (Death Grip's chain,
    // a hook). A player gets the anticheat "under ACK" flag. Works on players, bots, pets and creatures.
    void JumpTo(Unit* unit, Position const& dest, float speedXY, float minSpeedZ = 0.f, uint32 lookSpell = 0,
        Unit* lookCaster = nullptr);

    // A chaser's run speed as a percent of a player's 7 yd/s (Hunt at 80 / 95%): SetSpeed(MOVE_RUN, SpeedFor(pct)).
    void SetRunSpeedPct(Creature* creature, float pctOfPlayerRun);

    // ----------------------------------------------------------------------------------------------------------------
    // Target picks
    // ----------------------------------------------------------------------------------------------------------------

    // The candidates are the players on `me`'s threat list (alive, in the world, not game masters); `tank` = `me`'s
    // victim, distance = 2D distance from `me`, LoS from `me`. Rule: DungeonKitLogic.h PickRule.
    Player* PickPlayer(Creature* me, PickRule const& rule);
    std::vector<Player*> PickPlayers(Creature* me, PickRule const& rule, uint32 count);
    // Adds `guids` to `rule.exclude` (raw values).
    void ExcludeGuids(PickRule& rule, GuidSet const& guids);

    // ----------------------------------------------------------------------------------------------------------------
    // Line strike (L4)
    // ----------------------------------------------------------------------------------------------------------------

    struct LineStrikeSpec
    {
        float width = 4.f;
        float overrun = 5.f;                    // yd past the target
        float excludeSourceEnd = 0.f;           // yd at the source end that never hit (the boss's own feet)
        Milliseconds warn{ 2000 };
        float pct = 30.f;                       // % of reference non-tank health
        float tankPct = -1.f;                   // >= 0: the tank takes this % of tank health instead
        uint8 school = 0;
        uint32 spellId = 0;                     // a dungeon copy of the resolve spell (0 = by school)
        bool weakened = true;
        uint32 rider = 0;
        uint32 tag = 0;
        Arena const* clip = nullptr;            // stop at this arena's walls (the region holding the source)
        float inset = 0.5f;                     // yd short of the wall
        std::optional<BossMechanics::Color> color;
        std::function<void(Unit* hit)> onHit;   // capture guids only, never a Unit*
    };

    struct LineStrikeResult
    {
        BossMechanics::MechanicHandle handle;   // invalid: refused
        Position end;                           // where the line stops (the next link of a chained charge)
        float length = 0.f;
        bool clipped = false;                   // a wall stopped it short of target + overrun
    };

    // Registers (and commits) the line from `from` through `target`, `spec.overrun` past it, clipped to `spec.clip`.
    LineStrikeResult LineStrike(Unit* owner, Position const& from, Position const& target, LineStrikeSpec const& spec);
    LineStrikeResult LineStrike(Unit* owner, Unit const* from, Unit const* target, LineStrikeSpec const& spec);

    // ----------------------------------------------------------------------------------------------------------------
    // Lethal damage, split damage, stacks
    // ----------------------------------------------------------------------------------------------------------------

    // Keeps a unit at 1 health instead of dying while armed (a fake death: no kill credit, no loot). Call Intercept
    // from DamageTaken; the first lethal hit after Arm / Reset calls `onZero` once (the phase change). Armed by
    // default, and still armed after firing: every later lethal hit is clamped too until Disarm (call it when the
    // boss may die). Reset (re-arm, not fired) belongs in the boss's Reset, or a wipe after the phase change leaves
    // him at 1 health forever.
    //
    //     void Reset() override { BossAI::Reset(); _lethal.Reset(); }
    //     void DamageTaken(Unit*, uint32& damage, DamageEffectType, SpellSchoolMask) override
    //     {
    //         _lethal.Intercept(me, damage, [this]() { StartPhaseTwo(); });
    //     }
    //     void StartPhaseTwo() { ...; _lethal.Disarm(); }     // the second death is real
    class LethalGuard
    {
    public:
        void Arm() { _latch.Arm(); }
        void Reset() { _latch.Reset(); }
        void Disarm() { _latch.Disarm(); }
        bool Armed() const { return _latch.Armed(); }
        bool Fired() const { return _latch.Fired(); }

        // True when it clamped `damage`.
        bool Intercept(Unit* unit, uint32& damage, std::function<void()> const& onZero = {});

    private:
        LethalLatch _latch;
    };

    // One-shot form of the SFK proposal: clamps a lethal `damage` and calls `onZero` the first time (`fired` keeps the
    // once-only state in the caller).
    bool InterceptLethal(Unit* unit, uint32& damage, bool& fired, std::function<void()> const& onZero = {});

    // The players in `inside` (null entries skipped) each get a share of `totalPct` % of `owner`'s reference non-tank
    // row, at most `capPct` % each (0 = no cap): SplitDamage's even split. Deal the shares with a SpellScript of your
    // own (SetEffectValue in OnEffectLaunchTarget, so the target's defensives count).
    std::vector<std::pair<ObjectGuid, uint32>> SplitShares(Unit const* owner, std::vector<Unit*> const& inside,
        float totalPct, float capPct = 0.f);

    // Adds `delta` stacks (negative removes) of `spellId` from `caster` (nullptr: the target itself) on `target`,
    // clamped to [0, max] (max 0: the spell's own StackAmount; no cap when that is 0 too); 0 removes the aura.
    // Returns the new count. A new aura is applied with Unit::AddAura; every change refreshes its duration.
    uint32 AddStacks(Unit* target, uint32 spellId, int32 delta, Unit* caster = nullptr, uint32 max = 0);
    // The current count (any caster when `caster` is empty).
    uint32 Stacks(Unit const* target, uint32 spellId, ObjectGuid caster = ObjectGuid::Empty);

    // ----------------------------------------------------------------------------------------------------------------
    // Instance helpers
    // ----------------------------------------------------------------------------------------------------------------

    // A once-per-instance roll saved through the instance's own data: GetData(dataId) is Roll::Unrolled until the first
    // call rolls (Present with `presentChancePct` %) and stores it with SetData(dataId, value) (the instance saves it).
    uint32 RollOnce(InstanceScript* instance, uint32 dataId, uint32 presentChancePct);

    // The hard mode loot bit (LOOT_MODE_HARD_MODE_1: a hard mode list in group 2 with LootMode 2) on or off.
    void SetHardModeLoot(Creature* boss, bool lit);

    // ----------------------------------------------------------------------------------------------------------------
    // Breakable doors
    // ----------------------------------------------------------------------------------------------------------------

    // Summons `standInEntry` on `door`'s position (the door line), passive and rooted, with `health` (0: its template
    // health), and hands it the door (BreakableDoorAI::SetGUID). The stand-in's script should be (or derive from)
    // BreakableDoorAI. Returns nullptr when the summon fails.
    //
    // The summoner is the door itself, or `summoner` when given: an instance-owned helper, never a boss. A BossAI
    // summoner zones the stand-in into combat (JustSummoned) and despawns it with his summons on death, evade and
    // reset, which leaves jailed players behind a closed door with nothing to break; such a summoner is refused
    // (logged) and the door summons it instead. An instance DoorData entry on the same door re-closes it on the next
    // boss state change.
    Creature* SpawnBreakableDoor(GameObject* door, uint32 standInEntry, uint32 health = 0,
        WorldObject* summoner = nullptr);

    // The stand-in's AI: never moves or attacks; on death it opens its door (GO_STATE_ACTIVE) and despawns. A dungeon
    // registers it under its own script name (RegisterDungeonReworkCreatureAI(npc_sfk_cell_door, ...)) with a class of
    // its own that derives from this one (an override of DamageTaken or UpdateAI calls this one's).
    //
    // Evade path: in combat with no hit taken for kQuietMs it evades (EVADE_REASON_NO_HOSTILES), so a player who hit
    // it once leaves combat. With `keepDamage` (default) it does not regenerate and keeps its health through the
    // evade: the damage on a door persists.
    struct BreakableDoorAI : public ScriptedAI
    {
        static int32 constexpr kSetDoorGuid = 0x4B444F52;   // SetGUID id: the door this stand-in opens

        explicit BreakableDoorAI(Creature* creature);

        static uint32 constexpr kQuietMs = 10000;

        void Reset() override;
        void SetGUID(ObjectGuid const& guid, int32 id) override;
        void JustDied(Unit* killer) override;
        void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType damageType,
            SpellSchoolMask schoolMask) override;
        void EnterEvadeMode(EvadeReason why) override;
        void UpdateAI(uint32 diff) override;
        void AttackStart(Unit* /*who*/) override { }
        void MoveInLineOfSight(Unit* /*who*/) override { }

        // Called after the door opened (the default logs it).
        virtual void OnDoorOpened(GameObject* door);

        ObjectGuid DoorGuid() const { return _door; }

    protected:
        ObjectGuid _door;
        bool keepDamage = true;         // set in the derived constructor; Reset applies it
        QuietTimer _quiet{ kQuietMs };
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Pickups
    // ----------------------------------------------------------------------------------------------------------------

    struct PickupSpec
    {
        float radius = 2.f;
        Milliseconds life{ 20000 };             // then onExpire (and it is gone)
        Milliseconds dwell{ 0 };                // an eligible player inside this long takes it (0: on touch)
        float zBand = 6.f;                      // yd above or below the spot that still count as on it
        BossMechanics::Eligibility who;         // who may take it (and which bots go for it): Registry::IsEligible
        uint8 count = 1;                        // bodies the bots send (the registry Soak's count)
        std::optional<BossMechanics::Color> color;
        uint32 visualEntry = 0;                 // a creature summoned on the spot for the look (0: none)
        uint32 goEntry = 0;                     // or a gameobject (0: none)
        uint32 tag = 0;
        std::function<void(Player* taker)> onPick;  // capture guids only
        std::function<void()> onExpire;
    };

    // Walk-over pickups owned by one boss AI: Add registers a registry Soak on the spot (the telegraph, and a job for
    // the bots; outline only, cancelled before it could resolve) and Update polls every 250 ms for the first eligible
    // player inside for `dwell`, who takes it (onPick), or the pickup expires after `life` (onExpire). Eligible is the
    // registry's own check on the Soak (roles, carriers, stacks, `.mech test` scope), so a human taker obeys the same
    // rule as the bots. Call Update from
    // the AI's UpdateAI (in or out of combat) and Clear from Reset / JustDied / EnterEvadeMode.
    class Pickups
    {
    public:
        static uint32 constexpr kPollMs = 250;

        // Returns the pickup id (0: refused).
        uint32 Add(Creature* owner, Position const& at, PickupSpec spec);
        void Update(Creature* owner, uint32 diff);
        void Cancel(Creature* owner, uint32 id);
        void Clear(Creature* owner);
        std::size_t Count() const { return _pickups.size(); }

    private:
        struct Entry
        {
            uint32 id = 0;
            Position at;
            PickupSpec spec;
            BossMechanics::MechanicHandle soak;
            ObjectGuid visual;
            ObjectGuid object;
            uint32 ageMs = 0;
            DwellTracker dwell;
        };

        void Remove(Creature* owner, Entry& e);

        std::vector<Entry> _pickups;
        uint32 _nextId = 1;
        uint32 _pollMs = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Logging
    // ----------------------------------------------------------------------------------------------------------------

    // "<dungeon> <boss> <mechanic>[ <detail>]" at INFO in module.dungeonbosses, e.g. LogMechanic("sfk", "odo", "hunt",
    // "target=Bob"). Playtest greps key on it.
    void LogMechanic(char const* dungeon, char const* boss, char const* mechanic, std::string const& detail = {});
}

#endif
