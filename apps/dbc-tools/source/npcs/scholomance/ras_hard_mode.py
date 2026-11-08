"""
Scholomance build WP-S12: Ras Frostwhisper's hard mode "the Torn Keepsake", heroic only
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S12, s10; build spec
docs/dungeons/scholomance-rework.md SC 1087-1121, 1207-1209). WP-S12 owns this file.

Nothing is declared yet. WP-KS built the instance half (modules/mod-dungeon-bosses src/Scholomance/
instance_scholomance_rework.cpp; ras_hard_mode.cpp lists it): the page mask, the bound book, the hard mode and kill
flags and the loot bit. The user's measured spots (handoff s10) are ScholomanceRework.h's kKeepsakePages,
kKeepsakeBook and kHardModeTable.

TODO(WP-S12): the spells (206190-206204), the Ice Tomb 300535 (12k), the gameobject templates 301150 (torn page),
301151 / 301152 (the book, empty and bound) and 301154 (the alchemy table that starts the hard mode) with their
scripts, and the spawns (heroic spawnMask 2) in the SQL rev.
"""
