"""
Gnomeregan build WP-S0: the instance's own ids (.agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md s3.2, s3.3,
s7 #5 A). The shared slice 214280-214299 (kSpellsShared of modules/mod-dungeon-bosses
src/Gnomeregan/GnomereganRework.h) is S0's, then the orchestrator's:

  214280         reserved: a script-applied Weakened copy (s3.5 rule 22), if a WP needs one beyond the registry's own
  214281-214299  spare

Nothing is declared here yet. Unlike Zul'Farrak, no encounter needs a credit spell: every Gnomeregan encounter is a
kill credit on its boss (instance_encounters creditType 0), WP-H's rows: 379 re-pointed from Grubbis to Techbot
301105, the new 1107 for the Alert System 301110, heroic 1108-1113. Slot 6 (the Whole Workshop's kill) has no DBC row:
the instance writes it inside Thermaplugg's DONE.

The skeleton's other data (the S0 rev, data/sql/updates/pending_db_world/rev_skeleton_gnomeregan.sql): the SmartAI it
drops, Emi's event, the Alert hall's packs and the pocket's patrols, Fallout's and Pummeler's moves (Pummeler's
creature_template_movement row), Electrocutioner's wander, the new spawns (Techbot, the Alert System, the 3005-A copy,
the console), the Workshop Door made keyless and bound to go_gnomer_workshop_door, the Buttons made unselectable.
The checkpoint rows are mod-dungeon-checkpoint's (u_dungeon_checkpoint_2026_11_26_00.sql, applied by hand).
"""
