/*
 * mod-dungeon-bosses, Scholomance S13: the Graduate Exam's driver, as the instance sees it (engine side; the pure half
 * is GraduateExamLogic.h, the code graduate_exam.cpp).
 *
 * The instance (instance_scholomance_rework.cpp) owns one driver per map, ticks it from InstanceScript::Update and
 * hands it each player who enters and each Passing Grade it awards. The driver:
 *   - shows the Passing Grades as auras (one per instructor) on every player of the map, from the instance's table;
 *   - runs the gauntlet once the honors program paper (GO 301153, go_sc_honors_paper) is signed: the six rooms in a
 *     random order with an examiner in each, Gandling's lanes and swaps reaching in, then the final phase in the study
 *     on Gandling (200k); a wipe puts everything back and the paper can be signed again (the grades stay).
 *
 *     GraduateExam* exam = GetGraduateExam(instance);   // nullptr: not the Scholomance rework instance
 *     exam->TrySign(player);                             // the paper's click
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_GRADUATE_EXAM_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_GRADUATE_EXAM_H

#include "Define.h"
#include "GraduateExamLogic.h"
#include <memory>
#include <optional>
#include <string>

class InstanceScript;
class Player;

namespace ScholoGraduateExam
{
    class GraduateExam
    {
    public:
        virtual ~GraduateExam() = default;

        // InstanceScript::Update: the grade displays and the gauntlet's steps.
        virtual void Update(uint32 diff) = 0;
        // A player entered the map, or earned a grade: their grade auras now.
        virtual void SyncGrades(Player* player) = 0;

        // The paper: why it would refuse now (None: it can be signed).
        virtual PaperRefusal Check() const = 0;
        // The paper's click: signs the honors program (DATA_GANDLING_HARD_MODE) and starts the gauntlet. `firstRoom`
        // (a test command) leads the order. False when refused (Check(), or the instance refused the signature).
        virtual bool TrySign(Player* by, std::optional<Classroom> firstRoom = std::nullopt) = 0;

        virtual bool Running() const = 0;
        // Test commands: kill the room's examiner, jump to the final phase, stop (a wipe), the state line.
        virtual std::string SkipRoom() = 0;
        virtual std::string SkipToFinal() = 0;
        virtual void Stop(char const* why) = 0;
        virtual std::string StateLine() const = 0;
    };

    // The instance creates its driver with this (graduate_exam.cpp).
    std::unique_ptr<GraduateExam> CreateGraduateExam(InstanceScript* instance);

    // The map's driver, or nullptr when `instance` is not the Scholomance rework instance.
    GraduateExam* GetGraduateExam(InstanceScript* instance);

    // The paper's refusal, told to the player who clicked.
    char const* PaperRefusalText(PaperRefusal why);
}

#endif
