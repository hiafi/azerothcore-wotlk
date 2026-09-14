#!/usr/bin/env bash
#
# run-sim.sh - runs a mod-dpssim DpsSim.RunPlayerbot job against this deployment's real live
# Docker stack (same DB, same client data, same worldserver image the real server uses), without
# touching the live ac-worldserver container at all. On success this also bakes
# modules/mod-dpssim/reports/SimProfileReport.html (see build_report_html.py) and prints both the
# report JSON path and that HTML path - open the HTML directly, or browse every past run (this one
# included) via apps/sim-reports (apps/wow-tools-webui's /reports/ page).
#
# This is the exact procedure that used to be run by hand each time (scratch etc/ dir, throwaway
# `docker run`, flip AiPlayerbot.Enabled for the duration of the run) - see
# .agents/plans/dps-sim-module/dps-sim-module.PLAN.md's "Operational recipe" section for the
# original manual version this replaces.
#
# Usage:
#   modules/mod-dpssim/tools/run-sim.sh <profile> [durationSeconds] [level] [race] [iterations] [stepMs]
#
#   <profile>          Either a bare profile name (FrostMageSim, ArcaneMageSim, ...) resolved
#                       against modules/mod-dpssim/conf/profiles/<name>.conf, or a path to a
#                       profile file directly (relative to the repo root or absolute).
#   [durationSeconds]  Sim duration in simulated seconds (DpsSim.DurationSeconds). Default: 180.
#   [level]            Actor/target level (DpsSim.PlayerbotLevel). Default: 60.
#   [race]             Actor race, RACE_* value from SharedDefines.h (DpsSim.PlayerbotRace).
#                       Default: 1 (Human).
#   [iterations]       Run this many independent samples of the same profile/duration/level/race
#                       and average the results (see aggregate_reports.py) - see
#                       docs/bugs-and-fixes.md's SimDaemon::RunPlayerbot() non-determinism entry
#                       for why: even an identical run produces a different DPS number every time,
#                       so one run alone is a noisy sample. Default: 10 - this is "the config" the
#                       stat-weight tooling means when it says "iterations from the config" (there
#                       is no separate config file for it, this default *is* the config). All N
#                       samples run inside ONE container (DpsSim.Iterations - see
#                       SimDaemon::RunPlayerbotBatch()'s doc comment) rather than one throwaway
#                       `docker run` per sample like this script used to do - container boot/
#                       teardown turned out to dominate the old approach's wall-clock cost far more
#                       than the actual sim work (confirmed 2026-09-13: ~27-34s per sample almost
#                       entirely fixed overhead, regardless of DpsSim.StepMs). Keeps every
#                       iteration's raw report JSON on disk (named "...iterN.report.json")
#                       alongside the averaged one, for anyone who wants to look at a single sample
#                       directly; pass 1 explicitly to skip averaging and go back to a plain single
#                       run.
#   [stepMs]           Fixed-timestep size in simulated ms (DpsSim.StepMs) - see that key's own
#                       doc comment in dpssim.conf.dist for the full precision/cost tradeoff data.
#                       Default: 100 (changed from 10 on 2026-09-13 after a step-size sweep -
#                       10/50/100/200/300/500/1000ms, 100 iterations each, in-process batching -
#                       found 100ms the best trade: 4.6x faster than 10ms with no accuracy cost
#                       distinguishable from run-to-run noise across two independent 100-run
#                       batches, while every coarser step tested (200ms onward) showed severe,
#                       worsening bias - 1000ms undercounts casts by ~24% and DPS by ~26%. 50ms
#                       was worse on *both* axes than 100ms - slower and less accurate - so it's
#                       not a fallback either.
#
# Examples:
#   modules/mod-dpssim/tools/run-sim.sh ArcaneMageSim              # 180s @ level 60, avg of 10 @ 100ms (the defaults)
#   modules/mod-dpssim/tools/run-sim.sh FrostMageSim 300
#   modules/mod-dpssim/tools/run-sim.sh modules/mod-dpssim/conf/profiles/ArcaneMageSim.conf 60 80
#   modules/mod-dpssim/tools/run-sim.sh ArcaneMageSim 180 60 1 1   # single run, no averaging
#   modules/mod-dpssim/tools/run-sim.sh ArcaneMageSim 120 60 1 100 100   # 100 runs at a 100ms step
#
# Requires: the normal Docker stack already up (ac-database healthy, ac-worldserver running -
# its image, network, volume, and DB credentials are all discovered by inspecting that live
# container, not hardcoded here, so this stays correct if any of those ever change).

set -euo pipefail

PROFILE_ARG="${1:?usage: run-sim.sh <profile> [durationSeconds] [level] [race] [iterations] [stepMs]}"
DURATION_SECONDS="${2:-180}"
LEVEL="${3:-60}"
RACE="${4:-1}"
ITERATIONS="${5:-10}"
STEP_MS="${6:-100}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$REPO_ROOT"

# --- resolve the profile file -------------------------------------------------------------
if [[ -f "$PROFILE_ARG" ]]; then
    PROFILE_HOST_PATH="$(cd "$(dirname "$PROFILE_ARG")" && pwd)/$(basename "$PROFILE_ARG")"
elif [[ -f "modules/mod-dpssim/conf/profiles/${PROFILE_ARG}.conf" ]]; then
    PROFILE_HOST_PATH="$REPO_ROOT/modules/mod-dpssim/conf/profiles/${PROFILE_ARG}.conf"
else
    echo "error: no such profile file '$PROFILE_ARG' and no" \
        "modules/mod-dpssim/conf/profiles/${PROFILE_ARG}.conf either" >&2
    exit 1
fi
PROFILE_NAME="$(basename "$PROFILE_HOST_PATH" .conf)"
# modules/ is bind-mounted into the container at /azerothcore/modules (see docker-compose
# override's ac-worldserver.volumes) - translate the host path to that container path.
PROFILE_CONTAINER_PATH="/azerothcore/modules/${PROFILE_HOST_PATH#"$REPO_ROOT"/modules/}"

# --- discover the live stack's real network / image / volume / DB creds ------------------
if ! docker inspect ac-worldserver >/dev/null 2>&1; then
    echo "error: no 'ac-worldserver' container found - is the normal stack up" \
        "('docker compose up -d')?" >&2
    exit 1
fi

NETWORK="$(docker inspect ac-worldserver --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}')"
IMAGE="$(docker inspect ac-worldserver --format '{{.Config.Image}}')"
CLIENT_DATA_VOLUME="$(docker inspect ac-worldserver --format '{{range .Mounts}}{{if eq .Type "volume"}}{{.Name}}{{end}}{{end}}')"

if [[ -z "$NETWORK" || -z "$IMAGE" || -z "$CLIENT_DATA_VOLUME" ]]; then
    echo "error: couldn't work out ac-worldserver's network/image/client-data volume from" \
        "'docker inspect' - inspect it by hand and fix this script's discovery logic." >&2
    exit 1
fi

# Pull out just the AC_*_DATABASE_INFO env vars the live container was actually launched with,
# rather than re-guessing credentials - stays correct if DOCKER_DB_ROOT_PASSWORD is ever changed.
mapfile -t DB_ENV < <(docker inspect ac-worldserver --format '{{range .Config.Env}}{{println .}}{{end}}' \
    | grep -E '^AC_(LOGIN|WORLD|CHARACTER|PLAYERBOTS)_DATABASE_INFO=')
if [[ "${#DB_ENV[@]}" -lt 4 ]]; then
    echo "error: expected 4 AC_*_DATABASE_INFO env vars on ac-worldserver, found ${#DB_ENV[@]}." \
        "DB env discovery may need updating." >&2
    exit 1
fi
DB_ENV_ARGS=()
for kv in "${DB_ENV[@]}"; do DB_ENV_ARGS+=(-e "$kv"); done

# --- build a scratch etc/ + logs/ dir for this one run ------------------------------------
SCRATCH="$(mktemp -d -t dpssim-run.XXXXXX)"
trap 'rm -rf "$SCRATCH"' EXIT
mkdir -p "$SCRATCH/logs"
cp -r env/dist/etc/. "$SCRATCH/etc/"

# Boot this throwaway worldserver in sim-daemon mode - never a connectable realm (no socket
# listeners at all in this mode), so it's safe to run alongside the real ac-worldserver.
printf '\nDpsSim.Enabled = 1\n' >> "$SCRATCH/etc/worldserver.conf"

# SimBot::Create() needs a real, working PlayerbotAI - flip this on for the sim run regardless
# of the live deployment's own playerbots.conf (confirmed 2026-09-12: the live server currently
# runs with AiPlayerbot.Enabled = 0, which makes SimBot::Create() fail outright). Only affects
# this throwaway scratch copy, never the real env/dist/etc/modules/playerbots.conf.
if grep -q '^AiPlayerbot\.Enabled' "$SCRATCH/etc/modules/playerbots.conf"; then
    sed -i 's/^AiPlayerbot\.Enabled.*/AiPlayerbot.Enabled = 1/' "$SCRATCH/etc/modules/playerbots.conf"
else
    printf '\nAiPlayerbot.Enabled = 1\n' >> "$SCRATCH/etc/modules/playerbots.conf"
fi

REPORT_CONTAINER_PATH="/azerothcore/env/dist/logs/${PROFILE_NAME}.report.json"
cat > "$SCRATCH/etc/modules/dpssim.conf" <<EOF
DpsSim.Enabled = 1
DpsSim.RunPlayerbot = 1
DpsSim.Profile = ${PROFILE_CONTAINER_PATH}
DpsSim.DurationSeconds = ${DURATION_SECONDS}
DpsSim.PlayerbotLevel = ${LEVEL}
DpsSim.PlayerbotRace = ${RACE}
DpsSim.StepMs = ${STEP_MS}
DpsSim.Iterations = ${ITERATIONS}
DpsSim.ReportPath = ${REPORT_CONTAINER_PATH}
EOF

REPORTS_DIR="$REPO_ROOT/modules/mod-dpssim/reports"
mkdir -p "$REPORTS_DIR"
BATCH_TS="$(date +%Y%m%d-%H%M%S)"

echo "Running '${PROFILE_NAME}' (${ITERATIONS} iteration(s), in one container) for ${DURATION_SECONDS}s" \
    "(sim time) each at level ${LEVEL}, race ${RACE}, ${STEP_MS}ms step..." >&2

RUN_LOG="$SCRATCH/run.log"
set +e
docker run --rm --network "$NETWORK" \
    -v "$SCRATCH/etc:/azerothcore/env/dist/etc:ro" \
    -v "$CLIENT_DATA_VOLUME:/azerothcore/env/dist/data:ro" \
    -v "$SCRATCH/logs:/azerothcore/env/dist/logs" \
    -v "$REPO_ROOT/modules:/azerothcore/modules:ro" \
    -e AC_DATA_DIR="/azerothcore/env/dist/data" \
    -e AC_LOGS_DIR="/azerothcore/env/dist/logs" \
    "${DB_ENV_ARGS[@]}" \
    "$IMAGE" \
    > "$RUN_LOG" 2>&1
STATUS=$?
set -e

if [[ $STATUS -ne 0 ]]; then
    echo "error: sim run failed - last 40 lines of container output:" >&2
    tail -40 "$RUN_LOG" >&2
    exit 1
fi

# Collect every iteration's report out of the scratch dir before the EXIT trap removes it, renaming
# into $REPORTS_DIR under the same external naming convention (aggregate_reports.py, apps/
# sim-reports) already expects - nothing downstream of this needs to know the container ran N
# samples internally instead of N separate containers. DpsSim.Iterations = 1 has SimDaemon write
# the bare "<profile>.report.json" (see IterationReportPath()'s doc comment, DpsSim.cpp) - anything
# higher writes "<profile>.report.iterN.json" per sample instead, addressed by exact name (not a
# glob+sort) so "iter10" can never sort before "iter2".
ITERATION_PATHS=()
if [[ "$ITERATIONS" -gt 1 ]]; then
    for ((i = 1; i <= ITERATIONS; i++)); do
        SRC="$SCRATCH/logs/${PROFILE_NAME}.report.iter${i}.json"
        if [[ ! -f "$SRC" ]]; then
            echo "error: expected iteration ${i}/${ITERATIONS}'s report at '$SRC' but it's missing -" \
                "last 40 lines of container output:" >&2
            tail -40 "$RUN_LOG" >&2
            exit 1
        fi
        DEST="$REPORTS_DIR/${PROFILE_NAME}.${BATCH_TS}.iter${i}.report.json"
        cp "$SRC" "$DEST"
        ITERATION_PATHS+=("$DEST")
    done
else
    SRC="$SCRATCH/logs/${PROFILE_NAME}.report.json"
    if [[ ! -f "$SRC" ]]; then
        echo "error: sim run produced no report - last 40 lines of container output:" >&2
        tail -40 "$RUN_LOG" >&2
        exit 1
    fi
    DEST="$REPORTS_DIR/${PROFILE_NAME}.${BATCH_TS}.report.json"
    cp "$SRC" "$DEST"
    ITERATION_PATHS+=("$DEST")
fi

if [[ "$ITERATIONS" -gt 1 ]]; then
    FINAL_PATH="$REPORTS_DIR/${PROFILE_NAME}.${BATCH_TS}.report.json"
    python3 "$REPO_ROOT/modules/mod-dpssim/tools/aggregate_reports.py" "$FINAL_PATH" "${ITERATION_PATHS[@]}" >&2
else
    FINAL_PATH="${ITERATION_PATHS[0]}"
fi

# Bake this run straight into SimProfileReport.html - single spec, no comparison slot, no
# "load report" click needed, just open the file.
HTML_PATH="$REPORTS_DIR/SimProfileReport.html"
python3 "$REPO_ROOT/modules/mod-dpssim/tools/build_report_html.py" "$HTML_PATH" \
    "$PROFILE_NAME" "$FINAL_PATH" >&2

echo "$FINAL_PATH"
echo "$HTML_PATH"
