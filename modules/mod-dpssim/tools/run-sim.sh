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
# `docker run`, flip Playerbots.Enabled for the duration of the run) - see
# .agents/plans/dps-sim-module/dps-sim-module.PLAN.md's "Operational recipe" section for the
# original manual version this replaces.
#
# Usage:
#   modules/mod-dpssim/tools/run-sim.sh <profile> [durationSeconds] [level] [race] [iterations] [stepMs] [targets]
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
#   [targets]          Number of stacked target dummies (DpsSim.TargetCount), 1-10. Default: 1. All of them
#                       sit within DpsSim.TargetSpreadYards (3) of each other, so every target is inside
#                       every AoE radius - the best case for AoE. For N > 1 the batch files are named
#                       "<Profile>.T<N>.<ts>..." (iteration reports, aggregated report, kept run log);
#                       T1 names are unchanged.
#
# Environment:
#   DPSSIM_TARGET_RANK  Dummy rank (DpsSim.TargetRank): boss, elite or auto. Default: auto.
#   DPSSIM_KEEP_LOG=1   Keep the container's log next to the reports.
#   DPSSIM_IMAGE        Worldserver image to run instead of the one the live ac-worldserver container was started from
#                       (e.g. acore/ac-wotlk-worldserver:master after a `docker compose build` the live container has
#                       not been recreated for).
#   DPSSIM_EXTRA_CONF   Extra lines appended to the generated dpssim.conf (printf %b, so "\n" separates lines).
#
# Healing runs: a profile with "Mode = Heal" (see SimProfile.h) runs the healing sim. Everything above applies, with
# these differences: [targets] must be 1, [durationSeconds] is at most 300, the reports are named
# "<Profile>.<group>.<tag>.<ts>..." (the tag is explained below) and the baked page is
# modules/mod-dpssim/reports/HealProfileReport.html. Environment, all optional (without them the profile's own
# HealGroup / HealTargets / InfiniteMana apply):
#   HEALSIM_GROUP          party | raid10 | raid20 (DpsSim.HealGroup). The healer is always one of the members.
#   HEALSIM_TARGETS        what each member suffers (DpsSim.HealTargets). A preset applies one mode to every member
#                          of the group (party = 1 tank, 3 dps and the healer; raid10 = 2 tanks, 7 dps and the healer;
#                          raid20 = 2 tanks, 17 dps and the healer):
#                            pin50 / pin20   every member is kept at 50% / 20% health by real damage hits (the pure
#                                            HPS measurement)
#                            drain:<n>       every member takes <n> damage a second; the tanks take 3x <n>, the DPS and
#                                            the healer <n> (the survival measurement)
#                          or a full list such as "tank:drain:450, 3*dps:drain:150, self:drain:100" (SimHeal.h has the
#                          syntax). The key handed to the worldserver always holds the full expanded list.
#   HEALSIM_INFINITE_MANA  1/true or 0/false (DpsSim.InfiniteMana): keep the healer's mana full during the fight.
# File tag: the preset name (pin50, drain150, ...) or, for a full HEALSIM_TARGETS list (or none at all, the profile's
# own), "x" and a short hash of the list; "-inf" is appended for infinite mana.
#
# Tank runs: a profile with "Mode = Tank" (see SimProfile.h, plan .agents/plans/tank-sim/tank-sim.PLAN.md) runs the DPS
# sim with the dummies swinging at the actor. Everything above applies, including [targets] (1 = a boss dummy, 2-10 = an
# elite pack, every dummy swings). The reports are named "<Profile>.tank-<scenario>.<targets>t.<ts>..." (so aggregation
# never mixes scenarios or pack sizes) and the baked page is modules/mod-dpssim/reports/TankProfileReport.html. They are
# DPS reports with a tank section ("kind": "tank"). Environment, all optional (without them the profile's own
# TankScenario / TankHitDamage / TankPackHitDamage / TankSwingMs apply; DPSSIM_EXTRA_CONF may not set these keys, the run
# refuses it). A run that overrides the hit or swing numbers adds a tag "x<hash>" after the target count in its names:
#   TANKSIM_SCENARIO   dps | survive (DpsSim.TankScenario). dps: the tank's health is refilled every step, it never
#                      dies (read DPS and TPS). survive: no outside healing, the run ends at its death (read the time to
#                      death and the net damage taken per second).
#   TANKSIM_HIT        the boss's hit before armor (DpsSim.TankHitDamage): "2250-2750" or one value. 1 target only.
#   TANKSIM_PACK_HIT   each pack dummy's hit before armor (DpsSim.TankPackHitDamage), same syntax. 2+ targets only.
#   TANKSIM_SWING_MS   the dummies' swing time, 500-10000 (DpsSim.TankSwingMs).
#
# Examples:
#   modules/mod-dpssim/tools/run-sim.sh ArcaneMageSim              # 180s @ level 60, avg of 10 @ 100ms (the defaults)
#   modules/mod-dpssim/tools/run-sim.sh FrostMageSim 300
#   modules/mod-dpssim/tools/run-sim.sh modules/mod-dpssim/conf/profiles/ArcaneMageSim.conf 60 80
#   modules/mod-dpssim/tools/run-sim.sh ArcaneMageSim 180 60 1 1   # single run, no averaging
#   modules/mod-dpssim/tools/run-sim.sh ArcaneMageSim 120 60 1 100 100   # 100 runs at a 100ms step
#   modules/mod-dpssim/tools/run-sim.sh DestructionWarlockSim 300 60 2 10 100 5   # 5 stacked dummies
#   TANKSIM_SCENARIO=survive modules/mod-dpssim/tools/run-sim.sh ProtWarriorTankSim 120 60 1 10   # time to death
#   modules/mod-dpssim/tools/run-sim.sh ProtWarriorTankSim 120 60 1 10 100 5     # tank dps vs 5 dummies
#
# Database isolation: the sim never connects to the live acore_characters. Before booting, this script clones the
# live characters schema (structure plus the small static/bookkeeping tables the worldserver reads at startup, see
# CHARS_COPY_DATA_TABLES) into a throwaway schema "acore_characters_sim_<pid>", points the sim container's
# AC_CHARACTER_DATABASE_INFO at it, and drops it on exit (also after a failed or interrupted run). mod-dpssim itself
# refuses to run on any characters DB not named acore_characters_sim*. The login, world and playerbots databases
# are shared as before (the sim only reads the first two; it doesn't write the playerbots one).
#
# Requires: the normal Docker stack already up (ac-database healthy, ac-worldserver running -
# its image, network, volume, and DB credentials are all discovered by inspecting that live
# container, not hardcoded here, so this stays correct if any of those ever change).

set -euo pipefail

PROFILE_ARG="${1:?usage: run-sim.sh <profile> [durationSeconds] [level] [race] [iterations] [stepMs] [targets]}"
DURATION_SECONDS="${2:-180}"
LEVEL="${3:-60}"
RACE="${4:-1}"
ITERATIONS="${5:-10}"
STEP_MS="${6:-100}"
TARGETS="${7:-1}"
TARGET_RANK="${DPSSIM_TARGET_RANK:-auto}"

if ! [[ "$TARGETS" =~ ^([1-9]|10)$ ]]; then
    echo "error: [targets] must be an integer 1-10, got '$TARGETS'" >&2
    exit 1
fi
if ! [[ "$TARGET_RANK" =~ ^(auto|boss|elite)$ ]]; then
    echo "error: DPSSIM_TARGET_RANK must be auto, boss or elite, got '$TARGET_RANK'" >&2
    exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$REPO_ROOT"

die() { echo "error: $*" >&2; exit 1; }

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

# --- healing sim: detect a heal profile and resolve the scenario (group, target list, tag) ---------------------------
# profile_key <Key>: the last "Key = value" line of the profile, without the comment or blanks around the value
profile_key() {
    { grep -iE "^[[:space:]]*$1[[:space:]]*=" "$PROFILE_HOST_PATH" || true; } | tail -1 \
        | sed -E 's/^[^=]*=[[:space:]]*//; s/[[:space:]]*#.*$//; s/[[:space:]]+$//'
}
short_hash() { printf '%s' "$1" | tr -d ' \t' | tr 'A-Z' 'a-z' | sha1sum | cut -c1-6; }

IS_HEAL=0
if [[ "$(profile_key Mode | tr 'A-Z' 'a-z')" == "heal" ]]; then IS_HEAL=1; fi
HEAL_CONF=""
BATCH_SCENARIO=""
if [[ "$IS_HEAL" -eq 1 ]]; then
    if [[ "$TARGETS" -ne 1 ]]; then
        die "[targets] is for DPS profiles; '$PROFILE_NAME' is a heal profile (its group is HEALSIM_GROUP /" \
            "HEALSIM_TARGETS), got $TARGETS"
    fi
    if ! [[ "$DURATION_SECONDS" =~ ^[0-9]+$ ]]; then
        die "[durationSeconds] must be a whole number, got '$DURATION_SECONDS'"
    fi
    if (( DURATION_SECONDS > 300 )); then
        die "a heal run is at most 300 s (a dead ally would release its spirit after 6 minutes), got $DURATION_SECONDS"
    fi

    PROFILE_GROUP="$(profile_key HealGroup | tr 'A-Z' 'a-z')"
    HEAL_GROUP="$(printf '%s' "${HEALSIM_GROUP:-$PROFILE_GROUP}" | tr 'A-Z' 'a-z')"
    if ! [[ "$HEAL_GROUP" =~ ^(party|raid10|raid20)$ ]]; then
        die "HEALSIM_GROUP must be party, raid10 or raid20," \
            "got '${HEAL_GROUP:-<unset, and the profile has no HealGroup>}'"
    fi

    HEAL_INF=0
    if [[ -n "${HEALSIM_INFINITE_MANA:-}" ]]; then
        case "$(printf '%s' "$HEALSIM_INFINITE_MANA" | tr 'A-Z' 'a-z')" in
            1|true) HEAL_INF=1 ;;
            0|false) HEAL_INF=0 ;;
            *) die "HEALSIM_INFINITE_MANA must be 1/true or 0/false, got '$HEALSIM_INFINITE_MANA'" ;;
        esac
        HEAL_CONF+="DpsSim.InfiniteMana = ${HEAL_INF}"$'\n'
    elif [[ "$(profile_key InfiniteMana | tr 'A-Z' 'a-z')" =~ ^(1|true)$ ]]; then
        HEAL_INF=1
    fi

    HEAL_TAG=""
    HEAL_TARGETS_STR=""
    if [[ -n "${HEALSIM_TARGETS:-}" ]]; then
        T="${HEALSIM_TARGETS}"
        if [[ "$T" =~ (tank|dps|self): ]]; then
            # A full list: the worldserver validates the syntax and the size against the group
            HEAL_TARGETS_STR="$T"
            HEAL_TAG="x$(short_hash "$T")"
        else
            # A preset: one mode for every member. party = 1 tank, 3 dps + the healer; raid10 = 2 tanks, 7 dps + the
            # healer; raid20 = 2 tanks, 17 dps + the healer (the plan's compositions)
            case "$HEAL_GROUP" in
                party) N_TANK=1; N_DPS=3 ;;
                raid10) N_TANK=2; N_DPS=7 ;;
                raid20) N_TANK=2; N_DPS=17 ;;
            esac
            if [[ "$T" =~ ^pin(50|20)$ ]]; then
                TANK_MODE="pin:${T#pin}"
                DPS_MODE="$TANK_MODE"
                HEAL_TAG="$T"
            elif [[ "$T" =~ ^drain:([0-9]+([.][0-9]+)?)$ ]] &&
                    awk -v n="${BASH_REMATCH[1]}" 'BEGIN { exit !(n > 0) }'; then
                N="${BASH_REMATCH[1]}"
                DPS_MODE="drain:${N}"
                TANK_MODE="drain:$(awk -v n="$N" 'BEGIN { printf "%g", n * 3 }')"
                HEAL_TAG="drain${N//./_}"
            else
                die "HEALSIM_TARGETS '$T' is neither a preset (pin50, pin20, drain:<damage per second above 0>)" \
                    "nor a full target list like 'tank:pin:50, 3*dps:pin:50, self:pin:50'"
            fi
            HEAL_TARGETS_STR="${N_TANK}*tank:${TANK_MODE}, ${N_DPS}*dps:${DPS_MODE}, self:${DPS_MODE}"
        fi
        HEAL_CONF+="DpsSim.HealGroup = ${HEAL_GROUP}"$'\n'
        HEAL_CONF+="DpsSim.HealTargets = ${HEAL_TARGETS_STR}"$'\n'
    else
        # Only the group overridden: the profile's own target list must be for the same group
        if [[ -n "${HEALSIM_GROUP:-}" && "$HEAL_GROUP" != "$PROFILE_GROUP" ]]; then
            die "HEALSIM_GROUP=$HEAL_GROUP needs a matching HEALSIM_TARGETS: the profile's own HealTargets is" \
                "for '${PROFILE_GROUP:-no group}'"
        fi
        HEAL_TAG="x$(short_hash "$(profile_key HealTargets)")"
    fi
    if [[ "$HEAL_INF" -eq 1 ]]; then HEAL_TAG+="-inf"; fi
    BATCH_SCENARIO="${HEAL_GROUP}.${HEAL_TAG}"
fi

# --- tank sim: detect a tank profile and resolve the scenario (file names, conf overrides) ---------------------------
IS_TANK=0
TANK_CONF=""
TANK_SCENARIO=""
TANK_TAG=""
if [[ "$(profile_key Mode | tr 'A-Z' 'a-z')" == "tank" ]]; then IS_TANK=1; fi
if [[ "$IS_TANK" -eq 0 ]]; then
    for v in TANKSIM_SCENARIO TANKSIM_HIT TANKSIM_PACK_HIT TANKSIM_SWING_MS; do
        if [[ -n "${!v:-}" ]]; then
            die "$v is set but '$PROFILE_NAME' is not a tank profile (Mode = Tank)"
        fi
    done
else
    # The file name carries the scenario and a tag for the overridden numbers, so the tank settings must come from the
    # profile or the TANKSIM_* variables, never from raw config lines that the name cannot see
    TANK_RAW_RE='^[[:space:]]*DpsSim\.Tank(Scenario|HitDamage|PackHitDamage|SwingMs)[[:space:]]*='
    if printf '%b' "${DPSSIM_EXTRA_CONF:-}" | grep -qiE "$TANK_RAW_RE"; then
        die "DPSSIM_EXTRA_CONF sets a DpsSim.Tank* value (Scenario, HitDamage, PackHitDamage or SwingMs): use" \
            "TANKSIM_SCENARIO, TANKSIM_HIT, TANKSIM_PACK_HIT or TANKSIM_SWING_MS instead, so the report file names" \
            "carry the setting"
    fi
    PROFILE_SCENARIO="$(profile_key TankScenario | tr 'A-Z' 'a-z')"
    TANK_SCENARIO="$(printf '%s' "${TANKSIM_SCENARIO:-${PROFILE_SCENARIO:-dps}}" | tr 'A-Z' 'a-z')"
    if ! [[ "$TANK_SCENARIO" =~ ^(dps|survive)$ ]]; then
        if [[ -n "${TANKSIM_SCENARIO:-}" ]]; then
            die "TANKSIM_SCENARIO must be dps or survive, got '$TANK_SCENARIO'"
        fi
        die "TankScenario in the profile '$PROFILE_NAME' must be dps or survive, got '$TANK_SCENARIO'"
    fi
    if [[ -n "${TANKSIM_SCENARIO:-}" ]]; then TANK_CONF+="DpsSim.TankScenario = ${TANK_SCENARIO}"$'\n'; fi

    # "2250-2750" or one value, both above 0 and in order
    check_hit_range() {
        local name="$1" value="$2"
        if ! [[ "$value" =~ ^([0-9]+)(-([0-9]+))?$ ]]; then
            die "$name must be a range like 2250-2750 or one value, got '$value'"
        fi
        local lo="${BASH_REMATCH[1]}" hi="${BASH_REMATCH[3]:-${BASH_REMATCH[1]}}"
        if (( 10#$lo < 1 || 10#$hi < 10#$lo )); then
            die "$name must be above 0 with the minimum first, got '$value'"
        fi
    }
    if [[ -n "${TANKSIM_HIT:-}" ]]; then
        check_hit_range TANKSIM_HIT "$TANKSIM_HIT"
        TANK_CONF+="DpsSim.TankHitDamage = ${TANKSIM_HIT}"$'\n'
    fi
    if [[ -n "${TANKSIM_PACK_HIT:-}" ]]; then
        check_hit_range TANKSIM_PACK_HIT "$TANKSIM_PACK_HIT"
        TANK_CONF+="DpsSim.TankPackHitDamage = ${TANKSIM_PACK_HIT}"$'\n'
    fi
    if [[ -n "${TANKSIM_SWING_MS:-}" ]]; then
        if ! [[ "$TANKSIM_SWING_MS" =~ ^[0-9]+$ ]] ||
                (( 10#$TANKSIM_SWING_MS < 500 || 10#$TANKSIM_SWING_MS > 10000 )); then
            die "TANKSIM_SWING_MS must be a whole number of 500-10000 ms, got '$TANKSIM_SWING_MS'"
        fi
        TANK_CONF+="DpsSim.TankSwingMs = $((10#$TANKSIM_SWING_MS))"$'\n'
    fi
    # A run that overrides the profile's hit / swing numbers gets a short tag in its file name, like the heal sim's
    # scenario tag ("<Profile>.tank-survive.1t.x1a2b3c.<ts>"); the scenario and the target count are in the name already
    if [[ -n "${TANKSIM_HIT:-}${TANKSIM_PACK_HIT:-}${TANKSIM_SWING_MS:-}" ]]; then
        TANK_TAG="x$(short_hash "hit=${TANKSIM_HIT:-};pack=${TANKSIM_PACK_HIT:-};swing=${TANKSIM_SWING_MS:-}")"
    fi
fi

# --- discover the live stack's real network / image / volume / DB creds ------------------
if ! docker inspect ac-worldserver >/dev/null 2>&1; then
    echo "error: no 'ac-worldserver' container found - is the normal stack up" \
        "('docker compose up -d')?" >&2
    exit 1
fi

NETWORK="$(docker inspect ac-worldserver --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}')"
IMAGE="${DPSSIM_IMAGE:-$(docker inspect ac-worldserver --format '{{.Config.Image}}')}"
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

# The characters DB is the one connection that is NOT passed through: the sim gets a throwaway clone (below).
SIM_CHARS_DB="acore_characters_sim_$$"
DB_ENV_ARGS=()
LIVE_CHARS_INFO=""
for kv in "${DB_ENV[@]}"; do
    if [[ "$kv" == AC_CHARACTER_DATABASE_INFO=* ]]; then
        LIVE_CHARS_INFO="${kv#AC_CHARACTER_DATABASE_INFO=}"
    else
        DB_ENV_ARGS+=(-e "$kv")
    fi
done
# "host;port;user;password;database"
IFS=';' read -r DB_HOST DB_PORT DB_USER DB_PASS LIVE_CHARS_DB <<< "$LIVE_CHARS_INFO"
if [[ -z "$DB_HOST" || -z "$DB_USER" || -z "$LIVE_CHARS_DB" ]]; then
    echo "error: couldn't parse AC_CHARACTER_DATABASE_INFO from ac-worldserver." >&2
    exit 1
fi
if [[ "$SIM_CHARS_DB" == "$LIVE_CHARS_DB" || "$SIM_CHARS_DB" != acore_characters_sim_* ]]; then
    echo "error: refusing to run: scratch characters DB '$SIM_CHARS_DB' must not be the live one." >&2
    exit 1
fi
DB_ENV_ARGS+=(-e "AC_CHARACTER_DATABASE_INFO=${DB_HOST};${DB_PORT};${DB_USER};${DB_PASS};${SIM_CHARS_DB}")

# The mysql client lives in the database container: find the one on the stack's network that answers to $DB_HOST.
DB_CONTAINER=""
for c in $(docker network inspect "$NETWORK" --format '{{range .Containers}}{{.Name}} {{end}}'); do
    if docker inspect "$c" --format "{{range \$k, \$v := .NetworkSettings.Networks}}{{range \$v.Aliases}}{{println .}}{{end}}{{end}}" \
            | grep -qx "$DB_HOST"; then
        DB_CONTAINER="$c"
        break
    fi
done
if [[ -z "$DB_CONTAINER" ]]; then
    echo "error: no container on network '$NETWORK' with the alias '$DB_HOST' - can't create the scratch DB." >&2
    exit 1
fi
# MYSQL_PWD keeps the password out of the process list; mysql on stdin so the multi-statement scripts need no quoting.
db_sql() { docker exec -i -e MYSQL_PWD="$DB_PASS" "$DB_CONTAINER" mysql -u"$DB_USER" -N -B "$@"; }

# --- build a scratch etc/ + logs/ dir for this one run ------------------------------------
SCRATCH="$(mktemp -d -t dpssim-run.XXXXXX)"
cleanup() {
    rm -rf "$SCRATCH"
    # Always drop the throwaway characters schema, whether the run succeeded, failed or was interrupted.
    if [[ "$SIM_CHARS_DB" == acore_characters_sim_* ]]; then
        db_sql -e "DROP DATABASE IF EXISTS \`${SIM_CHARS_DB}\`" || echo "warning: couldn't drop '$SIM_CHARS_DB'" >&2
    fi
}
trap cleanup EXIT
trap 'exit 130' INT TERM
mkdir -p "$SCRATCH/logs"
cp -r env/dist/etc/. "$SCRATCH/etc/"

# Boot this throwaway worldserver in sim-daemon mode - never a connectable realm (no socket
# listeners at all in this mode), so it's safe to run alongside the real ac-worldserver.
printf '\nDpsSim.Enabled = 1\n' >> "$SCRATCH/etc/worldserver.conf"

# SimBot::Create() needs a real, working PlayerbotAI - flip this on for the sim run regardless
# of the live deployment's own playerbots.conf (confirmed 2026-09-12: the live server currently
# runs with Playerbots.Enabled = 0, which makes SimBot::Create() fail outright). Only affects
# this throwaway scratch copy, never the real env/dist/etc/modules/playerbots.conf.
set_playerbots_key() {
    local key="$1" value="$2" conf="$SCRATCH/etc/modules/playerbots.conf"
    if grep -q "^Playerbots\.${key}\b" "$conf"; then
        sed -i "s/^Playerbots\.${key}\b.*/Playerbots.${key} = ${value}/" "$conf"
    else
        printf '\nPlayerbots.%s = %s\n' "$key" "$value" >> "$conf"
    fi
}
set_playerbots_key Enabled 1

# The pre-pull buff phase (SimProfile.h's PrePullBuffMs) runs the bot out of combat, alone, on an overworld map,
# where the live BotActiveAlone (10%) parks it in minimal mode most of the time: only relevance >= 100 triggers,
# so no aura, self-buff or pet summon. Every bot always active for the sim, regardless of the live settings.
set_playerbots_key BotActiveAlone 100
set_playerbots_key botActiveAloneSmartScale 0
# Defensive pets only: an aggressive pet would pick the dummy during the buff phase and pull the bot into combat.
set_playerbots_key DefaultPetStance 1

# mod-ollama-chat off for the sim: its bot chatter would make paid LLM API calls. (Its tables must still exist in
# acore_characters: the module loads its personality templates at startup even when disabled, and aborts without
# them.) Only the scratch copy changes.
if [[ -f "$SCRATCH/etc/modules/mod_ollama_chat.conf" ]]; then
    if grep -q '^OllamaChat\.Enable\b' "$SCRATCH/etc/modules/mod_ollama_chat.conf"; then
        sed -i 's/^OllamaChat\.Enable\b.*/OllamaChat.Enable = 0/' "$SCRATCH/etc/modules/mod_ollama_chat.conf"
    else
        printf '\nOllamaChat.Enable = 0\n' >> "$SCRATCH/etc/modules/mod_ollama_chat.conf"
    fi
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
DpsSim.TargetCount = ${TARGETS}
DpsSim.TargetRank = ${TARGET_RANK}
DpsSim.TargetSpreadYards = 3
DpsSim.Iterations = ${ITERATIONS}
DpsSim.ReportPath = ${REPORT_CONTAINER_PATH}
EOF
if [[ -n "$HEAL_CONF" ]]; then printf '%s' "$HEAL_CONF" >> "$SCRATCH/etc/modules/dpssim.conf"; fi
if [[ -n "$TANK_CONF" ]]; then printf '%s' "$TANK_CONF" >> "$SCRATCH/etc/modules/dpssim.conf"; fi
if [[ -n "${DPSSIM_EXTRA_CONF:-}" ]]; then printf '%b\n' "$DPSSIM_EXTRA_CONF" >> "$SCRATCH/etc/modules/dpssim.conf"; fi

REPORTS_DIR="$REPO_ROOT/modules/mod-dpssim/reports"
mkdir -p "$REPORTS_DIR"
BATCH_TS="$(date +%Y%m%d-%H%M%S)"
# Multi-target batches carry the count in their file names ("<Profile>.T5.<ts>..."); T1 keeps the old names.
BATCH_NAME="${PROFILE_NAME}"
if [[ "$TARGETS" -gt 1 ]]; then BATCH_NAME="${PROFILE_NAME}.T${TARGETS}"; fi
# Heal batches carry the group and the scenario tag ("<Profile>.party.pin50.<ts>...")
if [[ "$IS_HEAL" -eq 1 ]]; then BATCH_NAME="${PROFILE_NAME}.${BATCH_SCENARIO}"; fi
# Tank batches carry the scenario and the dummy count ("<Profile>.tank-survive.5t.<ts>..."), plus "x<hash>" when
# TANKSIM_HIT / TANKSIM_PACK_HIT / TANKSIM_SWING_MS override the profile ("<Profile>.tank-survive.5t.x1a2b3c.<ts>...")
if [[ "$IS_TANK" -eq 1 ]]; then BATCH_NAME="${PROFILE_NAME}.tank-${TANK_SCENARIO}.${TARGETS}t${TANK_TAG:+.$TANK_TAG}"; fi

if [[ "$IS_HEAL" -eq 1 ]]; then
    echo "Running heal profile '${PROFILE_NAME}' (${ITERATIONS} iteration(s), in one container)" \
        "for ${DURATION_SECONDS}s (sim time) each at level ${LEVEL}, race ${RACE}, ${STEP_MS}ms step," \
        "group ${HEAL_GROUP}, scenario ${HEAL_TAG}," \
        "infinite mana $([[ "$HEAL_INF" -eq 1 ]] && echo on || echo off)..." >&2
elif [[ "$IS_TANK" -eq 1 ]]; then
    echo "Running tank profile '${PROFILE_NAME}' (${ITERATIONS} iteration(s), in one container)" \
        "for ${DURATION_SECONDS}s (sim time) each at level ${LEVEL}, race ${RACE}, ${STEP_MS}ms step," \
        "scenario ${TANK_SCENARIO}, ${TARGETS} dummy(ies), rank ${TARGET_RANK}..." >&2
else
    echo "Running '${PROFILE_NAME}' (${ITERATIONS} iteration(s), in one container) for ${DURATION_SECONDS}s" \
        "(sim time) each at level ${LEVEL}, race ${RACE}, ${STEP_MS}ms step," \
        "${TARGETS} target(s), rank ${TARGET_RANK}..." >&2
fi

# --- throwaway characters DB ----------------------------------------------------------------------------------------
# Structure of every live base table (CREATE TABLE ... LIKE keeps columns, keys and defaults), then the rows of only
# the static / bookkeeping tables the worldserver and its modules read at startup:
#   updates, updates_include   the DB updater's applied-migration records (an empty `updates` would make the sim try
#                              to re-apply every characters migration)
#   worldstates, active_arena_season, mail_server_template*   core startup loads
#   mod_ollama_chat_personality_templates   mod-ollama-chat aborts at startup without them, even when disabled
#   playerbots_*_names         name pools playerbots loads at startup
# Everything player-owned (characters, items, pets, mail, ...) stays empty. If a new module's startup load of
# another table aborts a sim boot, add that table here.
CHARS_COPY_DATA_TABLES=(updates updates_include worldstates active_arena_season mail_server_template
    mail_server_template_conditions mail_server_template_items mod_ollama_chat_personality_templates
    playerbots_names playerbots_guild_names playerbots_arena_team_names)

echo "Creating throwaway characters DB ${SIM_CHARS_DB}..." >&2
LIVE_TABLES="$(db_sql -e "SELECT table_name FROM information_schema.tables WHERE table_schema = '${LIVE_CHARS_DB}'
    AND table_type = 'BASE TABLE' ORDER BY table_name")"
SIM_DB_SCRIPT="$SCRATCH/create-sim-db.sql"
{
    echo "DROP DATABASE IF EXISTS \`${SIM_CHARS_DB}\`;"
    echo "CREATE DATABASE \`${SIM_CHARS_DB}\` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    while read -r t; do
        echo "CREATE TABLE \`${SIM_CHARS_DB}\`.\`${t}\` LIKE \`${LIVE_CHARS_DB}\`.\`${t}\`;"
    done <<< "$LIVE_TABLES"
    for t in "${CHARS_COPY_DATA_TABLES[@]}"; do
        # A module that isn't installed has no table to copy; skip it rather than fail the run.
        if grep -qx "$t" <<< "$LIVE_TABLES"; then
            echo "INSERT INTO \`${SIM_CHARS_DB}\`.\`${t}\` SELECT * FROM \`${LIVE_CHARS_DB}\`.\`${t}\`;"
        fi
    done
} > "$SIM_DB_SCRIPT"
db_sql < "$SIM_DB_SCRIPT"

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
# DPSSIM_KEEP_LOG=1 keeps the container's log next to the reports (the scratch dir is deleted on exit) - for
# debugging a run, e.g. the Engine's opening actions.
if [[ "${DPSSIM_KEEP_LOG:-0}" == 1 ]]; then
    cp "$RUN_LOG" "$REPORTS_DIR/${BATCH_NAME}.${BATCH_TS}.run.log"
    echo "kept run log: $REPORTS_DIR/${BATCH_NAME}.${BATCH_TS}.run.log" >&2
fi

if [[ $STATUS -ne 0 ]]; then
    echo "error: sim run failed - last 40 lines of container output:" >&2
    tail -40 "$RUN_LOG" >&2
    exit 1
fi
# A heal run's per-iteration summary lines (the JSON reports carry the same numbers)
if [[ "$IS_HEAL" -eq 1 ]]; then
    { grep -E "heal mode - group|heal iteration [0-9]+/[0-9]+ - |healer DIED" "$RUN_LOG" || true; } \
        | sed -E 's/^.*mod-dpssim: *//' >&2
fi

# A tank run's per-iteration summary lines (the JSON reports carry the same numbers)
if [[ "$IS_TANK" -eq 1 ]]; then
    { grep -E "tank mode - scenario|tank iteration [0-9]+/[0-9]+ \(|tank batch complete|actor DIED" "$RUN_LOG" \
        || true; } | sed -E 's/^.*mod-dpssim: *//' >&2
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
        DEST="$REPORTS_DIR/${BATCH_NAME}.${BATCH_TS}.iter${i}.report.json"
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
    DEST="$REPORTS_DIR/${BATCH_NAME}.${BATCH_TS}.report.json"
    cp "$SRC" "$DEST"
    ITERATION_PATHS+=("$DEST")
fi

if [[ "$ITERATIONS" -gt 1 ]]; then
    FINAL_PATH="$REPORTS_DIR/${BATCH_NAME}.${BATCH_TS}.report.json"
    python3 "$REPO_ROOT/modules/mod-dpssim/tools/aggregate_reports.py" "$FINAL_PATH" "${ITERATION_PATHS[@]}" >&2
else
    FINAL_PATH="${ITERATION_PATHS[0]}"
fi

# Bake this run straight into SimProfileReport.html - single spec, no comparison slot, no
# "load report" click needed, just open the file.
HTML_PATH="$REPORTS_DIR/SimProfileReport.html"
# Heal pages are baked to their own file, so a heal run never overwrites the last DPS page
if [[ "$IS_HEAL" -eq 1 ]]; then HTML_PATH="$REPORTS_DIR/HealProfileReport.html"; fi
# ... and so are tank pages
if [[ "$IS_TANK" -eq 1 ]]; then HTML_PATH="$REPORTS_DIR/TankProfileReport.html"; fi
python3 "$REPO_ROOT/modules/mod-dpssim/tools/build_report_html.py" "$HTML_PATH" \
    "$PROFILE_NAME" "$FINAL_PATH" >&2

echo "$FINAL_PATH"
echo "$HTML_PATH"
