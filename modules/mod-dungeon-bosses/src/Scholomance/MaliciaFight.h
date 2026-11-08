/*
 * mod-dungeon-bosses, Scholomance S5: Instructor Malicia's hooks for the other WPs (engine side; the pure numbers are
 * MaliciaLogic.h).
 *
 * S13, the Graduate Exam (SC 3046; handoff section 3.5 row S13): her Graduate Examiner fights on her own AI in examiner
 * mode. WP-S5 registers the script `npc_sc_examiner_malicia` (kExaminerScriptName); WP-S13 declares the examiner
 * entry NPC_SC_EXAMINER_MALICIA 300548 with that ScriptName (heroic only, no heroic template) and summons it in the
 * Coven. Examiner mode, by default:
 *   - heroic values everywhere (whatever the map), 80k health (kExaminerHealth, set by the AI on every reset);
 *   - her two own mechanics: Soul Drain with the Soul meter and the Loose Souls (MA1-MA3, MA5) and Soulstorm (MA6);
 *     Call a Student (MA4, the shades) and her stock kit (Shadow Heal, Slow, Corruption) are off (orchestrator
 *     default, F-B 2026-11-08);
 *   - no boss state (no gates, no Gandling reveal), no Passing Grades, no emotes (300548 has no creature_text);
 *   - the Ghost Visual tint (AURA_GHOST_VISUAL 9617), the Coven arena leash;
 *   - its registry encounter is the examiner itself (Mechanic::Failures(examiner, player) reads its ledger).
 * Call ConfigureExaminer before the pull to change any of it (the gauntlet's own death handling goes in `onDeath`).
 *
 * The script is registered only once wave C binds (ScholomanceRework.h kWaveCBound), so wave B's boot names no unbound
 * script. Only the players inside the Coven arena (MaliciaArena(), with its Z band) are in her fight: S13 must bring
 * the whole group into the room before the pull. End the fight (kill or evade the examiner) before a despawn.
 *
 * S11, detention (handoff section 3.7): the Coven's solo lesson is registered from AddSC_boss_instructor_malicia_rework
 * (RegisterSoloLesson(Classroom::Coven, ...)); S11 only calls CreateSoloLesson(Classroom::Coven). The lesson and her
 * fight (or her examiner) must not run at once in the Coven: each clears only the Soul meters it gave.
 *
 * The Soul meter and its weight (206205 / 206206) carry AURA_INTERRUPT_FLAG_CHANGE_MAP: a logout or a map change
 * drops them, so neither survives outside Scholomance.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_MALICIA_FIGHT_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_MALICIA_FIGHT_H

#include "Define.h"
#include "MaliciaLogic.h"
#include <functional>

class Creature;
class Player;

namespace ScholoMalicia
{
    char constexpr kExaminerScriptName[] = "npc_sc_examiner_malicia";

    struct ExaminerOptions
    {
        uint32 health = kExaminerHealth;        // 0: keep the template's
        bool soulDrain = true;                  // MA1-MA3 and MA5 (the meter, the drains, the souls, Bound Soul)
        bool callAStudent = false;              // MA4 (off: the examiner runs her two own mechanics)
        bool soulstorm = true;                  // MA6
        bool shadowHeal = false;                // MA7
        bool slow = false;                      // MA8 (stock 13747)
        bool corruption = false;                // MA9 (stock 18376)
        bool ghostTint = true;                  // AURA_GHOST_VISUAL 9617
        std::function<void(Creature* examiner)> onDeath;    // capture guids only
    };

    // Before the pull. False when `examiner` does not run npc_sc_examiner_malicia (or is fighting already).
    bool ConfigureExaminer(Creature* examiner, ExaminerOptions options);

    // The Soul meter of a player (0: none), and its removal (the meter and its hidden weight), for anything that
    // moves a player out of her fight or her lesson by force.
    uint32 SoulOf(Player const* player);
    void ClearSoul(Player* player);
}

#endif
