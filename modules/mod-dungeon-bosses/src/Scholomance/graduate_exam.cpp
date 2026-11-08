/*
 * mod-dungeon-bosses, Scholomance S13:
 * Darkmaster Gandling's hard mode, "the Graduate Exam" (heroic only).
 * STUB written by WP-KS (the Scholomance kit); WP-S13 owns this file from now on.
 *
 * What WP-KS built for it (the instance, instance_scholomance_rework.cpp; ScholomanceRework.h, ScholomanceKit.h):
 * - Passing Grades (ruling 22, handoff section 7 #18): each instructor's GradeWatch (in the six instructor stubs)
 *   records every registry failure with a player during the heroic fight and, at the death, awards the grade to every
 *   other player in the instance: SetGuidData(DataPassingGrade(instructor), player). The instance keeps them per
 *   player (PassingGrades, kGradeSlots), saved; GetData(DataGradeHolders(i)) counts holders; GetData(DATA_HONORS_OPEN)
 *   is 1 when every instructor has kHonorsMinHolders (3) holders. GetInstanceApi(instance)->Grades() reads the table.
 * - DATA_GANDLING_HARD_MODE: SetData(25, 1) signs the honors program (honors open, heroic, Gandling revealed, not
 *   fighting, not dead); saved; the loot bit rides Gandling while it is lit. DATA_GANDLING_HARD_MODE_KILLED on his
 *   death with the flag.
 * - The paper's spot: kHonorsPaper (z 115.8 floor over the study; route unchecked, handoff section 7 #17) or
 *   kHonorsPaperAlt; entry GO_SC_HONORS_PAPER 301153. Examiners NPC_SC_EXAMINER_* 300548-300554.
 * - `.dbtest scholo instance grade|grades|hardmode gandling` drive the same data by hand.
 *
 * TODO(WP-S13):
 * - SC 2909-3006, 3046-3063; handoff section 3.5 row S13.
 * - The Passing Grade auras (one per instructor, the display of the instance data): apply them on the award and when
 *   a player enters the instance (spells in kSpellsGandlingHardMode; icons in source/npcs/scholomance/_visuals.py).
 * - go_sc_honors_paper (here): usable when GetData(DATA_HONORS_OPEN); SetData(DATA_GANDLING_HARD_MODE, 1); yell 4.
 * - The gauntlet (six rooms in a random order, the examiners in examiner mode of each instructor's AI, the portals),
 *   then the final phase on S11's Gandling (200k); a wipe resets all of it, the grades stay.
 * - Bots never click the paper (handoff section 3.12).
 */

#include "Chat.h"
#include "GraduateExamLogic.h"
#include "InstanceScript.h"
#include "Player.h"
#include "ScholomanceRework.h"
#include "ScholomanceTestCommand.h"

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        if (!ScholoTest::RequireScholomance(handler))
            return false;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
            return false;
        handler->PSendSysMessage("The Graduate Exam: honors program {}, signed {}, killed {}",
            instance->GetData(DATA_HONORS_OPEN) ? "open" : "closed", instance->GetData(DATA_GANDLING_HARD_MODE),
            instance->GetData(DATA_GANDLING_HARD_MODE_KILLED));
        for (std::size_t i = 0; i < kInstructorCount; ++i)
            handler->PSendSysMessage("{}: {} holder(s)", kInstructorNames[i],
                instance->GetData(DataGradeHolders(Instructor(i))));
        return true;
    }

    ChatCommandTable const& ExamTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_scholo_graduate_exam()
{
    ScholoTest::RegisterBoss("exam", ExamTestCommands());
}
