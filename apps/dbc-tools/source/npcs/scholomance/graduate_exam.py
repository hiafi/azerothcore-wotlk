"""
Scholomance build WP-S13: Darkmaster Gandling's hard mode "the Graduate Exam", heroic only
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S13; build spec
docs/dungeons/scholomance-rework.md SC 2909-3006, 3046-3063). WP-S13 owns this file.

Nothing is declared yet. WP-KS built the instance half (modules/mod-dungeon-bosses src/Scholomance/
instance_scholomance_rework.cpp; graduate_exam.cpp lists it): the Passing Grades per player (the instructors'
GradeWatch awards them), the honors program rule (3 of 5 per instructor), the hard mode and kill flags and the loot
bit. The paper's spot is ScholomanceRework.h's kHonorsPaper.

TODO(WP-S13): the spells (206365-206384: the six Passing Grade auras, the gauntlet), the seven Graduate Examiners
300548-300554 (80k each; the Ravenian 60k, Corvane 20k; immunity 1972), the honors program paper 301153 and its
spawn (heroic spawnMask 2).
"""
