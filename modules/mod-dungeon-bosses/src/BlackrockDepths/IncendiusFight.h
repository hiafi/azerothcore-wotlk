/*
 * mod-dungeon-bosses, Blackrock Depths D11: Lord Incendius's hard mode hooks (engine side). WP-D11 owns this file (the
 * Blackrock Spire WyrmthalakFight.h pattern).
 *
 * The hard mode, Lord of the Lake (WP-D12, heroic only; S2 IN9-IN14, section 3.7, section 7 #14 A), fights on D11's
 * AI, boss_lord_incendius_rework. D11 keeps the kit both use (Curse, Fiery Burst, Fire Storm, Magma Fist, the floor,
 * the neck seals and the crumble steps, the lethal falls); D12 adds the giant, Crushing Fist, Arm Sweep, Lava Spawn,
 * the crumble timer and Firelord's Breath through two interfaces and one idle hook:
 *
 *   IncendiusHardMode   D12's per-pull object. D12 registers a factory once, from AddSC_brd_incendius_hard_mode:
 *                           BrdIncendius::RegisterIncendiusHardMode([](Creature*) { return std::make_unique<X>(); });
 *                       On every pull that is heroic with DATA_CINDER_USED lit, D11 asks the factory for one and calls
 *                       its hooks; on any other pull none is made (a lit Cinder with no factory runs the normal heroic
 *                       and logs a warning).
 *   IncendiusFight      what D11's AI offers the hard mode during the pull (passed to every hook).
 *   IncendiusIdleHook   D12, out of combat: called every AI tick while he is alive and not engaged (the intro after the
 *                       Cinder, the giant's pose in the lake after a reload or a wipe: rule 7). Registered once with
 *                       RegisterIncendiusIdleHook; D11's patrol (path 477330) is his own movement, so a hook that
 *                       poses him stops it itself.
 *
 * What D11 already does on a hard mode pull: reads DATA_CINDER_USED at the pull (heroic only); OnBossPull(me, key,
 * true); the instance keeps the hard mode loot bit while the Cinder is lit and records BOSS_LORD_OF_THE_LAKE on the
 * kill. The FallWatch (a fall into the lake is death, ruling 48) and the neck seals / crumble steps work the same.
 *
 * Hook order: ConfigureArena before the arena guard engages (D12: the giant stands in the lake, off the causeway: turn
 * the boss leash off). OnEngage after D11's own engage (encounter begun, descriptor set, beats started). OnUpdate every
 * AI tick in combat, before D11's beats. OnDamageTaken before the rebirth guard. The policy hooks (Rebirths, LavaSurge,
 * FireStorm*, MagmaFistOnTank) are read when the beat or the guard needs them. OnEnd from D11's cleanup (death, evade,
 * reset; `died` on the death), before D11 despawns its summons and clears its bands: undo every change made to him here
 * (health, scale, display, root, auras).
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_INCENDIUS_FIGHT_H
#define MOD_DUNGEON_BOSSES_BRD_INCENDIUS_FIGHT_H

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Define.h"
#include "IncendiusLogic.h"
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <vector>

class Creature;
class Player;
class Unit;

namespace BrdIncendius
{
    class IncendiusHardMode;

    // D11's AI, as the hard mode sees it during one pull.
    class IncendiusFight
    {
    public:
        virtual ~IncendiusFight() = default;

        virtual Creature* Boss() = 0;
        virtual bool Heroic() const = 0;
        // The pull's hard mode object (nullptr on a pull without it, or out of combat): D12's `.dbtest brd lake`
        // reaches it through his AI (dynamic_cast<BrdIncendius::IncendiusFight*>(boss->AI())).
        virtual IncendiusHardMode* ActiveHardMode() = 0;
        // ms since the pull, on the AI's own clock (never paused by a cast bar or the shatter).
        virtual uint64 FightMs() const = 0;
        // The players of the fight: alive, not game masters, on his threat list.
        virtual std::vector<Player*> FightPlayers() = 0;

        // ---- the floor (IncendiusLogic.h geometry) ----
        // CausewayFloor(): the real edge polygon every push goes over.
        virtual std::vector<Vec2> const& Floor() const = 0;
        virtual bool NecksSealed() const = 0;
        // Long-edge crumble steps raised so far (0-3; a raised step counts from its 5 s warning).
        virtual uint32 CrumbleSteps() const = 0;
        // IN8 / IN13: the two neck seals now (5 s edge marker, emote line 5, then lethal for the rest of the fight).
        // False when already sealed.
        virtual bool SealNecks(char const* why) = 0;
        // IN8 / IN13: the next 2 yd of both long edges now (5 s edge marker, emote line 5; the crumble says emote line
        // 2). False at kCrumbleMaxSteps.
        virtual bool Crumble(char const* why) = 0;
        // The bots' spot bounds for the current floor (SafeFloor(CrumbleSteps()) at the causeway's height): every
        // mechanic of the fight carries it (Within). D12 composes its role-scoped bounds from it.
        virtual BossMechanics::SpotBounds Bounds() const = 0;

        // ---- the shared kit (each fires one now; `forced`: that player instead of the random pick) ----
        // IN3: the marker and the patch (life FireStormLifeMs). Returns the zone (invalid: nobody / refused).
        virtual BossMechanics::MechanicHandle FireStorm(Player* forced) = 0;
        // IN4: the line and the fist (MagmaFistOnTank decides whether the tank may be picked).
        virtual BossMechanics::MechanicHandle MagmaFist(Player* forced) = 0;
        // Fire Storm and Magma Fist wait until FightMs() >= `untilMs` (S2 "Nothing lands during the Sweep").
        virtual void HoldBeats(uint64 untilMs) = 0;
        // Throws `unit` over the nearest long edge (PushOverEdge on Floor(), the Crumbling Ground look); `bearing`:
        // that way instead (the Arm Sweep's direction). The FallWatch does the rest.
        virtual bool ThrowOff(Unit* unit, std::optional<float> bearing, char const* why) = 0;

        // ---- bookkeeping ----
        // A registry handle cancelled with the fight (D11's cleanup).
        virtual void Track(BossMechanics::MechanicHandle handle) = 0;
        // A unit of D12's that belongs to the fight (a Lava Spawn, a stalker): despawned by D11's cleanup.
        virtual void TrackSummon(Creature* summon) = 0;
        // One INFO line "brd incendius <mechanic> <detail>" in module.dungeonbosses.
        virtual void Log(char const* mechanic, std::string const& detail = {}) = 0;
    };

    // D12's hard mode for one pull. Every hook has a do-nothing default (the normal heroic fight).
    class IncendiusHardMode
    {
    public:
        virtual ~IncendiusHardMode() = default;

        // Before the arena guard engages: D12 turns the boss leash off (the giant stands off the causeway), keeps the
        // no-target leash.
        virtual void ConfigureArena(IncendiusFight& /*fight*/, DungeonKit::Arena& /*arena*/,
            DungeonKit::ArenaGuardOptions& /*options*/) { }
        // The pull (D12: the 340k health, the giant's spot, scale, root and combat reach, the neck seals, the
        // descriptor's role bounds and kill order).
        virtual void OnEngage(IncendiusFight& /*fight*/) { }
        virtual void OnUpdate(IncendiusFight& /*fight*/, uint32 /*diff*/) { }
        virtual void OnDamageTaken(IncendiusFight& /*fight*/, Unit* /*attacker*/, uint32& /*damage*/) { }

        // The kit's policy on a hard mode pull (S2 "Kit in the hard mode"):
        // IN6 / IN7: how many rebirths (D12: 0, one kill).
        virtual uint32 Rebirths(IncendiusFight const& /*fight*/, uint32 base) const { return base; }
        // IN5 (D12: false, the Arm Sweep takes its place).
        virtual bool LavaSurge(IncendiusFight const& /*fight*/) const { return true; }
        // IN3: the patch's life (D12: 20 s) and the cadence (D12: 10 s).
        virtual uint32 FireStormLifeMs(IncendiusFight const& /*fight*/, uint32 base) const { return base; }
        virtual uint32 FireStormEveryMs(IncendiusFight const& /*fight*/, uint32 base) const { return base; }
        // IN4: may the tank be the target (D12: false, ruling 90).
        virtual bool MagmaFistOnTank(IncendiusFight const& /*fight*/) const { return true; }
        // IN4: the line starts where it can still reach (D12: true; the giant stands 28 yd out over the lava, so a
        // line from him ran out of length past far targets): IncendiusLogic.h FistStartOffset.
        virtual bool FistFromNearEnd(IncendiusFight const& /*fight*/) const { return false; }
        // A multiplier on D11's own reference hits, Fire Storm and Magma Fist (D12: Firelord's Will, +10% a stack).
        // Fiery Burst reads the same aura through its spell script (spell_brd_lake_scaled_hit).
        virtual float DamageScale(IncendiusFight& /*fight*/) const { return 1.f; }
        // Does D11 melee (D12: the giant's own reach rules; false hands melee to OnUpdate).
        virtual bool Melee(IncendiusFight const& /*fight*/) const { return true; }

        // Death (died), evade or reset. Undo every change made to him here.
        virtual void OnEnd(IncendiusFight& /*fight*/, bool /*died*/) { }
    };

    using IncendiusHardModeFactory = std::function<std::unique_ptr<IncendiusHardMode>(Creature* boss)>;
    using IncendiusIdleHook = std::function<void(Creature* boss, uint32 diff)>;

    // D12, from its AddSC_ function (once; a second call replaces the first).
    void RegisterIncendiusHardMode(IncendiusHardModeFactory factory);
    void RegisterIncendiusIdleHook(IncendiusIdleHook hook);
    // D11, on a heroic pull with DATA_CINDER_USED lit: nullptr when nothing is registered.
    std::unique_ptr<IncendiusHardMode> CreateIncendiusHardMode(Creature* boss);
}

#endif
