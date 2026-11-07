#!/usr/bin/env bash
# Builds and runs the standalone mod-dungeon-bosses tests with every available host compiler (g++ and clang++).
# Pure headers only (src/<Dungeon>/*Logic.h, DeadminesKitMath.h, DeadminesRework.h, the generated
# src/Generated/ItemSpellCopies.h): no server build needed.
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
)

status=0
for cxx in "${compilers[@]}"; do
  for test in "${tests[@]}"; do
    echo "== $cxx $test"
    "$cxx" -std=c++20 -Wall -Wextra -Werror -O1 -I "$root/src/Deadmines" -I "$root/src/Generated" -I "$here" \
      "$here/$test.cpp" -o "$out/$test-$cxx"
    if ! "$out/$test-$cxx"; then
      status=1
    fi
  done
done
exit $status
