/*
 * mod-dungeon-bosses, Scholomance S4: Ras Frostwhisper's hard mode hooks (engine side). WP-S4 owns this file.
 *
 * The hard mode "the Torn Keepsake" (WP-S12, heroic only) fights on S4's AI, boss_ras_frostwhisper_rework. S4 keeps
 * the whole normal and heroic kit (Chill, warmth, the 2 s tomb and its thaw, Frost Mark, Blizzard, the Volley); S12
 * adds the permanent tomb, the transition, Siphon Warmth and Mortal Decay through two interfaces:
 *
 *   RasHardMode   S12's per-pull object. S12 registers a factory once, from AddSC_scholo_ras_hard_mode:
 *                     ScholoRas::RegisterRasHardMode([](Creature* ras) { return std::make_unique<KeepsakeFight>(); });
 *                 On every pull that is heroic with DATA_RAS_HARD_MODE lit, S4 asks the factory for one and calls its
 *                 hooks below; on a normal pull none is made.
 *   RasFight      what S4's AI offers the hard mode during the pull (passed to every hook): the fight's players,
 *                 the Chill meter, warmth, the thaw, the handle list.
 *
 * Hook order: OnEngage after S4's own engage (encounter begun, descriptor set, the warm Stack registered); OnUpdate
 * every AI tick in combat before S4's beats; OnDamageTaken before BossAI's; OnFreeze when a player reaches 20 Chill
 * (S4 has already emptied the meter); OnEnd from S4's cleanup (death, evade, reset; `died` on the death). The hold
 * queries are read every tick.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_RAS_FIGHT_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_RAS_FIGHT_H

#include "BossMechanics.h"
#include "Define.h"
#include <functional>
#include <memory>
#include <string>
#include <vector>

class Creature;
class Player;
class Unit;

namespace ScholoRas
{
    // S4's AI, as the hard mode sees it during one pull.
    class RasFight
    {
    public:
        virtual ~RasFight() = default;

        virtual Creature* Ras() = 0;
        virtual bool Heroic() const = 0;

        // The players of the fight: alive, not game masters, in combat with Ras or on his arena.
        virtual std::vector<Player*> FightPlayers() = 0;
        // RF2 as of the last Chill beat (1 s): two or more living, not entombed allies within 8 yd.
        virtual bool IsWarm(Player const* player) const = 0;
        // RF3: the player holds S4's Entombed aura (SPELL_RF_ENTOMBED, any duration). An entombed player builds no
        // Chill, gives and gets no warmth, is never marked and is left out of the Blizzard picks.
        virtual bool IsEntombed(Player const* player) const = 0;

        // RF1: the player's Chill stacks.
        virtual uint32 ChillOf(Player const* player) const = 0;
        // RF1: adds (or removes) Chill and updates the looks; at 20 the player freezes (OnFreeze first). Dead and
        // entombed players are left alone. Returns the new count (0 after a freeze).
        virtual uint32 AddChill(Player* player, int32 delta, char const* why) = 0;
        // RF3 / RF4: ends a freeze now. Removes S4's Entombed aura if present and, with `burst`, lands the thaw at
        // the player (6 yd, 30% / 45% Frost, 1 Weakened, heroic +3 Chill; the player is spared). S12 calls it with
        // burst when a permanent tomb is broken.
        virtual void Thaw(Player* player, bool burst) = 0;

        // A registry handle cancelled with the fight (S4's cleanup).
        virtual void Track(BossMechanics::MechanicHandle handle) = 0;
        // One INFO line "scholo ras <mechanic> <detail>" in module.dungeonbosses.
        virtual void Log(char const* mechanic, std::string const& detail = {}) = 0;
    };

    // S12's hard mode for one pull. Every hook has a do-nothing default.
    class RasHardMode
    {
    public:
        virtual ~RasHardMode() = default;

        virtual void OnEngage(RasFight& /*fight*/) { }
        virtual void OnUpdate(RasFight& /*fight*/, uint32 /*diff*/) { }
        // Before BossAI::DamageTaken: clamp `damage` here for the transition (DungeonKit::LethalGuard).
        virtual void OnDamageTaken(RasFight& /*fight*/, Unit* /*attacker*/, uint32& /*damage*/) { }
        // A player reached 20 Chill (the meter is already empty). True: the hard mode holds them (the permanent
        // tomb) and S4 applies no Entombed aura and schedules no thaw; false: S4's 2 s tomb and thaw. To keep S4's
        // rules for a held player (no Chill, no warmth, no mark), hold them with S4's own aura made permanent:
        //     if (Aura* a = fight.Ras()->AddAura(SPELL_RF_ENTOMBED, player))
        //     {
        //         a->SetMaxDuration(-1);
        //         a->SetDuration(-1);
        //     }
        // and end it with fight.Thaw(player, true) when the Ice Tomb unit dies.
        virtual bool OnFreeze(RasFight& /*fight*/, Player* /*player*/) { return false; }
        // Death (died), evade or reset. Undo every change made to Ras here (display, health, flags).
        virtual void OnEnd(RasFight& /*fight*/, bool /*died*/) { }

        // True: S4's fight clock stands still (no Frost Mark, Blizzard or Volley comes due, no Chill beat): the 3 s
        // transition.
        virtual bool HoldsTimeline(RasFight const& /*fight*/) const { return false; }
        // True: a due Frost Mark waits (cast when this turns false): a Siphon Warmth.
        virtual bool HoldsFrostMark(RasFight const& /*fight*/) const { return false; }
        // True: S4's per-second Chill beat is skipped (the Siphon builds Chill itself through AddChill).
        virtual bool HoldsChillBeat(RasFight const& /*fight*/) const { return false; }
    };

    using RasHardModeFactory = std::function<std::unique_ptr<RasHardMode>(Creature* ras)>;

    // S12, from its AddSC_ function (once; a second call replaces the first).
    void RegisterRasHardMode(RasHardModeFactory factory);
    // S4, on a heroic pull with DATA_RAS_HARD_MODE lit: nullptr when nothing is registered.
    std::unique_ptr<RasHardMode> CreateRasHardMode(Creature* ras);
}

#endif
