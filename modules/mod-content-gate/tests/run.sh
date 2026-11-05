#!/usr/bin/env bash
# Builds and runs the standalone mod-content-gate tests with every available host compiler (g++ and clang++).
# Pure header only (src/ContentGateRules.h): no server build needed.
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

status=0
for cxx in "${compilers[@]}"; do
  for test in rules_test; do
    echo "== $cxx $test"
    "$cxx" -std=c++20 -Wall -Wextra -Werror -O1 -I "$root/src" -I "$here" "$here/$test.cpp" -o "$out/$test-$cxx"
    if ! "$out/$test-$cxx"; then
      status=1
    fi
  done
done
exit $status
