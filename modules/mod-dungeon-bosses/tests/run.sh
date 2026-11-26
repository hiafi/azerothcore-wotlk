#!/usr/bin/env bash
# Builds and runs the standalone mod-dungeon-bosses tests with every available host compiler (g++ and clang++).
# Pure headers only (src/<Dungeon>/*Logic.h, src/DungeonSets/*Logic.h, DeadminesKitMath.h, DeadminesRework.h,
# ShadowfangKeepRework.h, ScholomanceRework.h, SoloLessonLogic.h, StratholmeRework.h, BlackrockSpireRework.h,
# BlackrockDepthsRework.h, ScarletMonasteryRework.h, RagefireChasmRework.h, ZulFarrakRework.h, GnomereganRework.h,
# the shared kit's pure
# src/Kit/DungeonKit{Math,State,Arena,Logic,Ids,Floor,Flow,WallLogic,FrontLogic,RingLogic,ZoneLogic,WingLogic,
# WaterLogic,SoakLogic,ArenaEdgeLogic,LightLogic,MineLogic,ComboLogic}.h, the
# generated src/Generated/ItemSpellCopies.h): no server build needed.
# A boss WP adds nothing here: every tests/<boss>_test.cpp is listed below already (one per boss file).
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(dirname "$here")"
out="$(mktemp -d)"
trap 'rm -rf "$out"' EXIT

compilers=()
if [[ -n "${CXX:-}" ]]; then
  compilers=("$CXX")
else
  for c in g++ clang++; do
    if command -v "$c" > /dev/null; then
      compilers+=("$c")
    fi
  done
fi

tests=(
  dungeon_kit_test
  kit_test
  rhahk_zor_test
  miner_johnson_test
  sneed_test
  gilnid_test
  mr_smite_test
  cookie_test
  greenskin_test
  vancleef_test
  hard_mode_test
  hard_mode_items_test
  scholomance_items_test
  stratholme_hard_mode_items_test
  shadowfang_keep_hard_mode_items_test
  blackrock_spire_hard_mode_items_test
  blackrock_depths_hard_mode_items_test
  scarlet_monastery_hard_mode_items_test
  ragefire_chasm_hard_mode_items_test
  zul_farrak_hard_mode_items_test
  zul_farrak_sulthraze_join_test
  gnomeregan_hard_mode_items_test
  haunted_set_test
  molten_set_test
  zealot_set_test
  shadowfang_keep_test
  sfk_rethilgore_test
  sfk_razorclaw_test
  sfk_silverlaine_test
  sfk_springvale_test
  sfk_odo_test
  sfk_deathsworn_captain_test
  sfk_fenrus_test
  sfk_nandos_test
  sfk_arugal_test
  sfk_face_him_alone_test
  scholomance_test
  scholo_jandice_test
  scholo_rattlegore_test
  scholo_marduk_test
  scholo_ras_test
  scholo_malicia_test
  scholo_krastinov_test
  scholo_polkelt_test
  scholo_ravenian_test
  scholo_alexei_test
  scholo_illucia_test
  scholo_gandling_test
  scholo_keepsake_test
  scholo_exam_test
  stratholme_test
  strat_barthilas_test
  strat_baroness_test
  strat_nerubenkan_test
  strat_maleki_test
  strat_ramstein_test
  strat_baron_test
  strat_ultimatum_test
  strat_unforgiven_test
  strat_forresten_test
  strat_timmy_test
  strat_malor_test
  strat_willey_test
  strat_galford_test
  strat_dathrohan_test
  strat_grand_lie_test
  kit_walls_test
  kit_fronts_test
  kit_water_test
  kit_edge_test
  kit_soak_test
  kit_lights_test
  kit_mines_test
  kit_combo_test
  blackrock_spire_test
  brs_omokk_test
  brs_voshgajin_test
  brs_voone_test
  brs_smolderweb_test
  brs_urok_test
  brs_zigris_test
  brs_halycon_gizrul_test
  brs_wyrmthalak_test
  brs_wyrmthalak_hard_mode_test
  brs_emberseer_test
  brs_solakar_test
  brs_rend_gyth_test
  brs_beast_test
  brs_drakkisath_test
  brs_drakkisath_hard_mode_test
  blackrock_depths_test
  brd_gerstahn_test
  brd_roccor_test
  brd_grebmar_test
  brd_ring_of_law_test
  brd_ring_champions_test
  brd_ring_encore_test
  brd_loregrain_test
  brd_stilgiss_verek_test
  brd_vault_test
  brd_fineous_test
  brd_incendius_test
  brd_incendius_hard_mode_test
  brd_baelgar_test
  brd_angerforge_test
  brd_argelmach_test
  brd_argelmach_hard_mode_test
  brd_guzzler_test
  brd_hurley_test
  brd_phalanx_test
  brd_flamelash_test
  brd_the_seven_test
  brd_magmus_test
  brd_emperor_test
  brd_emperor_hard_mode_test
  scarlet_monastery_test
  sm_vishas_test
  sm_ironspine_test
  sm_council_test
  sm_thalnos_test
  sm_thalnos_hard_mode_test
  sm_loksey_test
  sm_kell_test
  sm_hollis_grey_test
  sm_doan_test
  sm_doan_hard_mode_test
  sm_crell_test
  sm_halden_test
  sm_herod_test
  sm_herod_hard_mode_test
  sm_thorne_test
  sm_last_stand_test
  sm_whitemane_test
  sm_whitemane_hard_mode_test
  ragefire_chasm_test
  rfc_oggleflint_test
  rfc_jergosh_test
  rfc_bazzalan_test
  rfc_taragaman_test
  rfc_taragaman_hard_mode_test
  zul_farrak_test
  zf_theka_test
  zf_antusul_test
  zf_zumrah_test
  zf_block_test
  zf_stair_test
  zf_crew_test
  zf_crewfight_test
  zf_ukorz_test
  zf_gahzrilla_test
  zf_hard_mode_test
  zf_deluge_test
  gnomeregan_test
  gnomer_techbot_test
  gnomer_fallout_test
  gnomer_electro_test
  gnomer_alert_test
  gnomer_pummeler_test
  gnomer_thermaplugg_test
  gnomer_hard_mode_test
  gnomer_hard_mode_machines_test
)

status=0
for cxx in "${compilers[@]}"; do
  for test in "${tests[@]}"; do
    echo "== $cxx $test"
    "$cxx" -std=c++20 -Wall -Wextra -Werror -O1 -I "$root/src/Kit" -I "$root/src/Deadmines" \
      -I "$root/src/ShadowfangKeep" -I "$root/src/Scholomance" -I "$root/src/Stratholme" -I "$root/src/Generated" \
      -I "$root/src/BlackrockSpire" -I "$root/src/BlackrockDepths" -I "$root/src/ScarletMonastery" \
      -I "$root/src/RagefireChasm" -I "$root/src/ZulFarrak" -I "$root/src/Gnomeregan" -I "$here" \
      "$here/$test.cpp" -o "$out/$test-$cxx"
    if ! "$out/$test-$cxx"; then
      status=1
    fi
  done
done

# WP-KT-B1: the kit's flex rules against mod-dungeon-difficulties' FlexMath.h, when DD's source is on hand.
dd_src="${DD_SRC:-$(dirname "$root")/mod-dungeon-difficulties/src}"
if [[ -f "$dd_src/FlexMath.h" ]]; then
  for cxx in "${compilers[@]}"; do
    echo "== $cxx kit_flex_parity_test"
    "$cxx" -std=c++20 -Wall -Wextra -Werror -O1 -I "$root/src/Kit" -I "$dd_src" -I "$here" \
      "$here/kit_flex_parity_test.cpp" -o "$out/kit_flex_parity_test-$cxx"
    if ! "$out/kit_flex_parity_test-$cxx"; then
      status=1
    fi
  done
else
  echo "== skip kit_flex_parity_test (no mod-dungeon-difficulties source: set DD_SRC)"
fi
# WP-KT-B2: the kit's front rules against mod-boss-mechanics' MechanicFront.h, when BM's source is on hand.
bm_src="${BM_SRC:-$(dirname "$root")/mod-boss-mechanics/src}"
if [[ -f "$bm_src/MechanicFront.h" ]]; then
  for cxx in "${compilers[@]}"; do
    echo "== $cxx kit_fronts_parity_test"
    "$cxx" -std=c++20 -Wall -Wextra -Werror -O1 -I "$root/src/Kit" -I "$bm_src" -I "$here" \
      "$here/kit_fronts_parity_test.cpp" -o "$out/kit_fronts_parity_test-$cxx"
    if ! "$out/kit_fronts_parity_test-$cxx"; then
      status=1
    fi
  done
else
  echo "== skip kit_fronts_parity_test (no mod-boss-mechanics source: set BM_SRC)"
fi
# F-1d (Gnomeregan): Thermaplugg's plate plan against BM's claim model (one claim per bot, nearest free plate).
if [[ -f "$bm_src/MechanicAssign.h" ]]; then
  for cxx in "${compilers[@]}"; do
    echo "== $cxx gnomer_plate_plan_bm_test"
    "$cxx" -std=c++20 -Wall -Wextra -Werror -O1 -I "$root/src/Kit" -I "$root/src/Gnomeregan" -I "$bm_src" \
      -I "$here" "$here/gnomer_plate_plan_bm_test.cpp" -o "$out/gnomer_plate_plan_bm_test-$cxx"
    if ! "$out/gnomer_plate_plan_bm_test-$cxx"; then status=1; fi
  done
else
  echo "== skip gnomer_plate_plan_bm_test (no mod-boss-mechanics source: set BM_SRC)"
fi
# WP-B10: Emberseer's pulses against BM's solver and brain model (the bots' ring and nova hits).
if [[ -f "$bm_src/MechanicFront.h" && -f "$bm_src/../tests/brain_model.h" ]]; then
  for cxx in "${compilers[@]}"; do
    echo "== $cxx brs_emberseer_bots_test"
    "$cxx" -std=c++20 -Wall -Wextra -Werror -O1 -I "$root/src/Kit" -I "$root/src/BlackrockSpire" -I "$here" \
      -I "$bm_src" -I "$bm_src/../tests" "$here/brs_emberseer_bots_test.cpp" -o "$out/brs_emberseer_bots_test-$cxx"
    if ! "$out/brs_emberseer_bots_test-$cxx"; then
      status=1
    fi
  done
else
  echo "== skip brs_emberseer_bots_test (no mod-boss-mechanics source: set BM_SRC)"
fi
exit $status
