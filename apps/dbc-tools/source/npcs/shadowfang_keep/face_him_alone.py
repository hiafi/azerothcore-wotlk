"""
Shadowfang Keep build WP-S10: Archmage Arugal's hard mode "Face Him Alone", heroic only
(.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md s3.6 row S10; build spec
docs/dungeons/shadowfang-keep-rework.md SK 1491-1511). WP-S10 owns this file.

Nothing is declared here, on purpose. The hard mode is a choice, not a mechanic:
  - the gossip option is C++ (modules/mod-dungeon-bosses src/ShadowfangKeep/face_him_alone.cpp, through S9's
    SfkLairPrisoner hooks): no gossip_menu_option rows;
  - the prisoner's hard mode line (creature_text group 7 on 300513 / 300514) is S9's (archmage_arugal.py's SQL rev);
  - the flag and the loot bit are the instance's (WP-K); the hard mode list is WP-L's (source/items/
    shadowfang_keep_loot.py, group 2 of 310051 at LootMode 2);
  - the fight without wards is S9's (Arugal's PlaceWard skips every ward while DATA_HARD_MODE is lit).

The spell slice 206085-206089 (the last five of Arugal's) stays reserved for this WP and unused; FaceHimAloneLogic.h
names the slice and no spell. lib/test_shadowfang_keep_face_him_alone.py checks the data half of the path.
"""
