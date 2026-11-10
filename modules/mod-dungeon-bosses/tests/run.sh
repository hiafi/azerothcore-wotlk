#!/usr/bin/env bash
# Builds and runs the standalone mod-dungeon-bosses tests with every available host compiler (g++ and clang++).
# Pure headers only (src/<Dungeon>/*Logic.h, DeadminesKitMath.h, DeadminesRework.h, ShadowfangKeepRework.h,
# ScholomanceRework.h, SoloLessonLogic.h, StratholmeRework.h, the shared kit's pure
# src/Kit/DungeonKit{Math,State,Arena,Logic,Ids,Floor,Flow,WallLogic}.h, the generated src/Generated/ItemSpellCopies.h): no
# server build needed.
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
  haunted_set_test
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
)

status=0
for cxx in "${compilers[@]}"; do
  for test in "${tests[@]}"; do
    echo "== $cxx $test"
    "$cxx" -std=c++20 -Wall -Wextra -Werror -O1 -I "$root/src/Kit" -I "$root/src/Deadmines" \
      -I "$root/src/ShadowfangKeep" -I "$root/src/Scholomance" -I "$root/src/Stratholme" -I "$root/src/Generated" \
      -I "$here" \
      "$here/$test.cpp" -o "$out/$test-$cxx"
    if ! "$out/$test-$cxx"; then
      status=1
    fi
  done
done
exit $status
