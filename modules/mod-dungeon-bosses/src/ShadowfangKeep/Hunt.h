/*
 * mod-dungeon-bosses, Shadowfang Keep: the Hunt (engine half), shared by Odo the Blindwatcher (WP-S5, OD1 / OD2) and
 * Baron Silverlaine's Echo of Odo (WP-S3, BS5). Pure numbers and rules: HuntLogic.h.
 *
 * The chase is modeled on mod-boss-mechanics' `sfk-hunt` drill (MechanicCommand.cpp RegisterHunt) so the drill's sweep
 * measures what the boss does:
 *   - Start: the chaser stops, faces the target and casts its howl (a cast bar on itself, `warn` long); the hunted
 *     player gets the Hunted debuff; the chaser's MOVE_RUN rate is set to ratePct (so the bots' drift read,
 *     MechanicBotView AnchorDriftSpeed, sees the chase speed from the start); a registry circle of `radius` anchored
 *     on the chaser, persistent for `chase` with a pass every `tick`, eligible for the hunted player only.
 *   - Every pass that does not hold the player re-aims a MovePoint at the player (the chaser's run speed, so a slow on
 *     the chaser counts). The first pass that holds the player is the catch: the circle's resolve copy (`catchHit`,
 *     the hit in the ledger and its impact) and its rider (`maul`, the stun and bleed) land on the player, and the
 *     hunt ends there.
 *   - The hunt also ends when the chase runs out (escaped), the player dies or leaves the map (target lost), or the
 *     script stops it (a bell, death, reset). Every end removes Hunted, cancels the circle, restores the template run
 *     speed and combat movement and, unless told not to, sends the chaser back to its victim.
 *
 * Use (one Hunt member per chaser AI):
 *
 *     SfkHunt::Hunt _hunt;
 *     // start: owner = the registry encounter (Odo himself; Silverlaine for his echo), chaser = me
 *     SfkHunt::HuntSpells spells{ SPELL_..._HOWL, SPELL_..._HUNTED, SPELL_..._MAUL_HIT, SPELL_..._MAUL };
 *     _hunt.Start(owner, me, target, SfkHunt::kEchoHunt, spells, TAG_ECHO_HUNT);
 *     // UpdateAI, every tick, before UpdateVictim (out of combat too):
 *     switch (_hunt.Update(me, diff)) { case SfkHunt::HuntEnd::Caught: ...; default: break; }
 *     // while _hunt.Active(): no melee, no other casts
 *     // JustDied / Reset / EnterEvadeMode: _hunt.Stop(me, false);
 *
 * The Maul aura's script `spell_sfk_hunt_maul` is generic (its bleed's calculated value is the total percent of
 * reference health; see HuntLogic.h); Odo's AddSC registers it once (SfkHunt::AddSC_sfk_hunt), so a second dungeon file
 * only binds its own Maul copy to the same script name in its DT file.
 */

#ifndef MOD_DUNGEON_BOSSES_SFK_HUNT_H
#define MOD_DUNGEON_BOSSES_SFK_HUNT_H

#include "Define.h"
#include "HuntLogic.h"
#include "ObjectGuid.h"
#include <memory>

class Creature;
class Map;
class Player;
class Unit;

namespace SfkHunt
{
    // The spells of one chaser's hunt (0: none).
    struct HuntSpells
    {
        uint32 howl = 0;        // the cast bar (warn long, cast by the chaser on itself; not triggered)
        uint32 hunted = 0;      // the debuff on the hunted player (removed when the hunt ends)
        uint32 catchHit = 0;    // the circle's resolve copy (a mod-boss-mechanics resolve copy; 0: the registry's own)
        uint32 maul = 0;        // the circle's rider: the stun and bleed (spell_sfk_hunt_maul)
    };

    class Hunt
    {
    public:
        // Starts a hunt (ends a running one first, without resuming the chase). `owner` is the registry encounter the
        // circle belongs to (the boss); `chaser` moves. False (nothing started) without a chaser, target or owner, or
        // when the registry refuses the circle.
        bool Start(Unit* owner, Creature* chaser, Player* target, HuntTuning const& tuning, HuntSpells const& spells,
            uint32 tag = 0);

        // Every UpdateAI tick, in or out of combat. Returns how the hunt ended, once, on the tick it ended (None while
        // it runs or when there is none). The cleanup is done by then.
        HuntEnd Update(Creature* chaser, uint32 diff);

        // Ends the hunt now (a bell, death, reset): no catch. `resumeChase`: send the chaser back to its victim.
        void Stop(Creature* chaser, bool resumeChase = true);

        bool Active() const { return _state != nullptr; }
        // Past the howl: the chaser is moving.
        bool Chasing() const;
        ObjectGuid Target() const;
        uint32 ElapsedMs() const { return _elapsedMs; }
        HuntTuning const& Tuning() const { return _tuning; }

        // The shared state of the circle's resolve callback (Hunt.cpp); public so the callback can name it.
        struct State;

    private:
        void Finish(Creature* chaser, bool resumeChase);

        std::shared_ptr<State> _state;
        HuntTuning _tuning;
        HuntSpells _spells;
        uint32 _elapsedMs = 0;
    };

    // Registers spell_sfk_hunt_maul (call once, from Odo's AddSC).
    void AddSC_sfk_hunt();
}

#endif
