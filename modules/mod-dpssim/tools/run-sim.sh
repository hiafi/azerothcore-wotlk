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
#   modules/mod-dpssim/tools/run-sim.sh <profile> [durationSeconds] [level] [race]
#
#   <profile>          Either a bare profile name (FrostMageSim, ArcaneMageSim, ...) resolved
#                       against modules/mod-dpssim/conf/profiles/<name>.conf, or a path to a
#                       profile file directly (relative to the repo root or absolute).
#   [durationSeconds]  Sim duration in simulated seconds (DpsSim.DurationSeconds). Default: 180.
#   [level]            Actor/target level (DpsSim.PlayerbotLevel). Default: 60.
#   [race]             Actor race, RACE_* value from SharedDefines.h (DpsSim.PlayerbotRace).
#                       Default: 1 (Human).
#
# Examples:
#   modules/mod-dpssim/tools/run-sim.sh ArcaneMageSim              # 180s at level 60 (the defaults)
#   modules/mod-dpssim/tools/run-sim.sh FrostMageSim 300
#   modules/mod-dpssim/tools/run-sim.sh modules/mod-dpssim/conf/profiles/ArcaneMageSim.conf 60 80
#
# Requires: the normal Docker stack already up (ac-database healthy, ac-worldserver running -
# its image, network, volume, and DB credentials are all discovered by inspecting that live
# container, not hardcoded here, so this stays correct if any of those ever change).

set -euo pipefail

PROFILE_ARG="${1:?usage: run-sim.sh <profile> [durationSeconds] [level] [race]}"
DURATION_SECONDS="${2:-180}"
LEVEL="${3:-60}"
RACE="${4:-1}"

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
DpsSim.ReportPath = ${REPORT_CONTAINER_PATH}
EOF

echo "Running '${PROFILE_NAME}' for ${DURATION_SECONDS}s (sim time) at level ${LEVEL}, race ${RACE}..." >&2

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

REPORT_HOST_PATH="$SCRATCH/logs/${PROFILE_NAME}.report.json"
if [[ $STATUS -ne 0 || ! -f "$REPORT_HOST_PATH" ]]; then
    echo "error: sim run failed or produced no report - last 40 lines of container output:" >&2
    tail -40 "$RUN_LOG" >&2
    exit 1
fi

# Report was written inside the now-deleted scratch dir's tmp mount - copy it out before the
# EXIT trap removes $SCRATCH.
REPORTS_DIR="$REPO_ROOT/modules/mod-dpssim/reports"
FINAL_PATH="$REPORTS_DIR/${PROFILE_NAME}.$(date +%Y%m%d-%H%M%S).report.json"
mkdir -p "$REPORTS_DIR"
cp "$REPORT_HOST_PATH" "$FINAL_PATH"

# Bake this run straight into SimProfileReport.html - single spec, no comparison slot, no
# "load report" click needed, just open the file.
HTML_PATH="$REPORTS_DIR/SimProfileReport.html"
python3 "$REPO_ROOT/modules/mod-dpssim/tools/build_report_html.py" "$HTML_PATH" \
    "$PROFILE_NAME" "$FINAL_PATH" >&2

echo "$FINAL_PATH"
echo "$HTML_PATH"
