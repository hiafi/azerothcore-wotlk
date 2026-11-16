/*
 * mod-dungeon-bosses, Blackrock Spire B14: General Drakkisath's hard mode hooks (engine side). WP-B14 owns this file
 * (the WyrmthalakFight.h / Stratholme BaronFight.h pattern).
 *
 * The hard mode "the General's Army" (WP-B15, heroic only; SP DR10-DR19) fights on B14's AI, boss_drakkisath_rework.
 * B14 keeps the whole normal and heroic kit (the brands, Thunderclap, Flamestrike, Blackblade Sweep, Rage, Seared Flesh
 * at 10) and the Elite Guards' AI; B15 adds the Muster, the squads, phase 2 and the Champion's Challenge through two
 * interfaces:
 *
 *   DrakkisathHardMode  B15's per-pull object. B15 registers a factory once, from AddSC_brs_drakkisath_hard_mode:
 *                           BrsDrakkisath::RegisterDrakkisathHardMode([](Creature*) { return std::make_unique<X>(); });
 *                       On every pull that is heroic with DATA_GENERALS_ARMY lit, B14 asks the factory for one and
 *                       calls its hooks; on any other pull none is made (a lit flag with no factory runs a plain
 *                       heroic, without the hard mode loot bits).
 *   DrakkisathFight     what B14's AI offers the hard mode during the pull (passed to every hook): the players, the
 *                       Guards and their hold, his root, his kit's gate and restart, the brands, the cast queue, the
 *                       room bounds, the handle and summon lists.
 *
 * What B14 already does on a hard mode pull: reads DATA_GENERALS_ARMY at the pull (heroic only); OnBossPull(me, key,
 * true) holds the flex count and sets the flex hard mode loot bit (LootMode 8 at 10 players); the instance records
 * BOSS_GENERALS_ARMY on the kill, keeps the hard mode loot bit (LootMode 2) while the flag is lit and clears the flag
 * when the attempt ends (DR19: the herald arms it again). Everything summoned through him (JustSummoned: B15's squads
 * when he is the summoner) and everything handed to TrackSummon despawns with the fight; the Guards are the instance's
 * minions (they respawn at his sides when the boss state goes back to NOT_STARTED).
 *
 * Hook order: OnEngage after B14's own engage (encounter begun, descriptor set, timers started, the aggro yell).
 * OnUpdate every AI tick in combat, before B14's beats. UsesAbility before each of his abilities starts (false:
 * skipped; its timer re-arms at its cadence, so a gate that opens later picks it up within one cadence; RestartKit to
 * start them over). OnBrands after a brand cast with its bearers. OnCast when the cast queue picks one of B15's ids.
 * OnSpellFailed when a cast bar of his is kicked or cancelled (after B14 has ended the hold that bar's OnCast set:
 * lesson 6). OnDamageTaken before BossAI's (the Challenge's damage count). OnDamageDealt after his Seared Flesh
 * (the Trophy). OnSummonDied for any creature he summoned or
 * that was tracked (a squad soldier). OnGuardDied after B14's bookkeeping. OnEnd from B14's cleanup (death, evade,
 * reset; `died` on the death), before B14 despawns its summons: undo every change made to him here (health, auras,
 * root).
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_DRAKKISATH_FIGHT_H
#define MOD_DUNGEON_BOSSES_BRS_DRAKKISATH_FIGHT_H

#include "BossMechanics.h"
#include "Define.h"
#include "DrakkisathLogic.h"
#include "ObjectGuid.h"
#include "Position.h"
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <vector>

class Creature;
class Player;
class Unit;

namespace BrsDrakkisath
{
    class DrakkisathHardMode;

    // His own abilities, as UsesAbility names them.
    enum class Ability : uint8
    {
        Brands = 0,             // DR2 / DR3 (the timer; Brands() below always fires)
        Thunderclap = 1,        // DR5
        Flamestrike = 2,        // DR6
        BlackbladeSweep = 3,    // DR7
        Rage = 4,               // DR8 (stock 16789)
        SearedFlesh = 5,        // DR9 (10 players; while it is off, his target's stacks are not held either)
        Melee = 6,              // his auto attack
    };

    // B14's AI, as the hard mode sees it during one pull.
    class DrakkisathFight
    {
    public:
        virtual ~DrakkisathFight() = default;

        virtual Creature* Boss() = 0;
        virtual bool Heroic() const = 0;
        // The flex count held at the pull (5..10): FlexAB pairs, DungeonKit::Flex::TankSwapOn.
        virtual uint8 Players() const = 0;
        // The pull's hard mode object (nullptr on a pull without it, or out of combat): B15's `.dbtest brs army`
        // reaches it through his AI (dynamic_cast<BrsDrakkisath::DrakkisathFight*>(boss->AI())).
        virtual DrakkisathHardMode* ActiveHardMode() = 0;
        // ms since the pull, on the AI's own clock (never paused by a cast bar).
        virtual uint64 FightMs() const = 0;
        // The players of the fight: alive, not game masters, in combat with him or on his arena.
        virtual std::vector<Player*> FightPlayers() = 0;

        // ---- DR1 the Elite Guards (10814, the instance's minions; their AI is B14's) ----
        virtual std::vector<Creature*> Guards() = 0;                        // the living ones
        // DR12: each living Guard holds `spots[i]` (the alcove mouth; extra Guards take the last spot): it walks there,
        // stays rooted and strikes only a player within `reachYd` of its spot (the nearest), standing idle otherwise.
        virtual void HoldGuards(std::vector<Position> const& spots, float reachYd) = 0;
        // DR16: the Guards leave their spots and fight on their threat (they "step down with him").
        virtual void ReleaseGuards() = 0;

        // ---- him ----
        // DR12: rooted in place (he stays in his alcove; he still turns and swings at a target in reach). Undone by
        // false and by B14's cleanup.
        virtual void SetRooted(bool rooted) = 0;
        // DR16: every one of his abilities starts over from now: its first timer (DrakkisathLogic.h) plus `delayMs`.
        virtual void RestartKit(uint32 delayMs = 0) = 0;
        // DR2 / DR3 now, outside the timer: `searing` Searing and `collapsing` Collapsing bearers among the non-tanks
        // (the emotes, the registry spread and stacks, the ticks). Returns the bearers.
        virtual GuidSet Brands(uint8 searing, uint8 collapsing) = 0;

        // ---- room, queue, bookkeeping ----
        // The bots' spot bounds (the hall and his alcove): every mechanic of the fight carries it (Within).
        virtual BossMechanics::SpotBounds RoomBounds() const = 0;
        // The cast queue: ids from kHardModeCastBase. When `id` comes up B14 calls DrakkisathHardMode::OnCast. Higher
        // priority first; his own wind-ups are priorities 1-3 (DrakkisathLogic.h).
        virtual void ScheduleCast(uint32 id, uint32 inMs, uint8 priority) = 0;
        virtual void CancelCast(uint32 id) = 0;
        // A registry handle cancelled with the fight (B14's cleanup).
        virtual void Track(BossMechanics::MechanicHandle handle) = 0;
        // A unit of B15's that belongs to the fight (a squad soldier summoned by someone else, a ring trigger):
        // despawned by B14's cleanup, and counted as a unit of his encounter (the descriptor's targets, the assist
        // tank).
        virtual void TrackSummon(Creature* summon) = 0;
        // One INFO line "brs drakkisath <mechanic> <detail>" in module.dungeonbosses.
        virtual void Log(char const* mechanic, std::string const& detail = {}) = 0;
    };

    // B15's hard mode for one pull. Every hook has a do-nothing default.
    class DrakkisathHardMode
    {
    public:
        virtual ~DrakkisathHardMode() = default;

        // The pull (B15: the 240k phase 2 health through DungeonKit::Flex::SetHealth, the Muster, the Guards' hold, the
        // descriptor edits).
        virtual void OnEngage(DrakkisathFight& /*fight*/) { }
        virtual void OnUpdate(DrakkisathFight& /*fight*/, uint32 /*diff*/) { }
        virtual void OnDamageTaken(DrakkisathFight& /*fight*/, Unit* /*attacker*/, uint32& /*damage*/) { }
        // His damage on `victim` (after B14's Seared Flesh): every hit he owns, his melee (`melee`) and the spells and
        // registry hits cast as his (the brands, Thunderclap, Flamestrike and its patches, the Sweep, B15's own
        // blows). B15's Trophy raises the non-melee ones (the aura already raises his melee).
        virtual void OnDamageDealt(DrakkisathFight& /*fight*/, Unit* /*victim*/, uint32& /*damage*/, bool /*melee*/) { }

        // DR12 / DR16: whether his ability `a` runs now (phase 1: the brands only, his melee in reach).
        virtual bool UsesAbility(DrakkisathFight const& /*fight*/, Ability /*a*/) const { return true; }
        // A brand cast landed on these bearers.
        virtual void OnBrands(DrakkisathFight& /*fight*/, GuidSet const& /*searing*/, GuidSet const& /*collapsing*/) { }

        // The queue picked `id` (one of B15's): start the cast now. Return how long it holds him (ms: a cast bar, the
        // Challenge's 12 s), during which nothing else on the queue starts, his own abilities wait and he does not
        // melee; nullopt: it could not start. B14 takes the entry off the queue before this call (StartHardModeCast),
        // so a ScheduleCast of the same id from here (the next one, or a retry) stays queued.
        virtual std::optional<uint32> OnCast(DrakkisathFight& /*fight*/, uint32 /*id*/) { return std::nullopt; }
        // A cast bar of his was kicked or cancelled (`spellId`); the hold its OnCast set has already ended.
        virtual void OnSpellFailed(DrakkisathFight& /*fight*/, uint32 /*spellId*/) { }

        // A creature he summoned (or one handed to TrackSummon) died.
        virtual void OnSummonDied(DrakkisathFight& /*fight*/, Creature* /*summon*/) { }
        // An Elite Guard died.
        virtual void OnGuardDied(DrakkisathFight& /*fight*/, Creature* /*guard*/) { }

        // Death (died), evade or reset. Undo every change made to him here (health, auras).
        virtual void OnEnd(DrakkisathFight& /*fight*/, bool /*died*/) { }
    };

    using DrakkisathHardModeFactory = std::function<std::unique_ptr<DrakkisathHardMode>(Creature* boss)>;

    // B15, from its AddSC_ function (once; a second call replaces the first).
    void RegisterDrakkisathHardMode(DrakkisathHardModeFactory factory);
    // B14, on a heroic pull with DATA_GENERALS_ARMY lit: nullptr when nothing is registered.
    std::unique_ptr<DrakkisathHardMode> CreateDrakkisathHardMode(Creature* boss);
}

#endif
