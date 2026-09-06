#!/usr/bin/env bash

set -euo pipefail

CURRENT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$CURRENT_PATH/../bash_shared/includes.sh"

UPDATES_PATH="$AC_PATH_ROOT/data/sql/updates"

# get_next_index "data/sql/updates/db_world/2024_10_14_22.sql"
#   => 23
# get_next_index ""
#   => 00
function get_next_index() {
    if [[ -n "$1" ]]; then
        # PREV_COUNT should be a non-zero padded number
        PREV_COUNT="$(
            # grabs the filename of the first argument, removes ".sql" suffix.
            basename "$1" .sql |
                # get the last number
                cut -f4 -d_ |
                # retrieve the last number, without zero padding
                grep -oE "[1-9][0-9]*$"
        )"

        printf '%02d' "$((PREV_COUNT + 1))"
    else
        echo "00"
    fi
}

# lists all SQL files in the appropriate data/sql/updates/db_$1, and then moves them to a standard format, ordered by date and how many imports have happened that day. The name should be in this format:
#
# /path/to/data/sql/updates/db_NAME/YYYY_MM_DD_INDEX.sql
#
# Where INDEX is a number with a minimum with a minimum width (0-padded) of 2
#
# for example, "data/sql/updates/db_world/2024_10_01_03.sql" translates to "the third update in the world database from October 01, 2024"

TODAY="$(date +%Y_%m_%d)"
function import() {
    PENDING_PATH="$AC_PATH_ROOT/data/sql/updates/pending_db_$1"
    UPDATES_DIR="$UPDATES_PATH/db_$1"

    # Get the most recent SQL file applied to this database. Used for the header comment
    LATEST_UPDATE="$(find "$UPDATES_DIR" -iname "*.sql" | sort -h | tail -n 1)"
    # Get latest SQL file applied to this database, today. This could be empty.
    LATEST_UPDATE_TODAY="$(find "$UPDATES_DIR" -iname "$TODAY*.sql" | sort -h | tail -n 1)"

    # Recursive, not "$PENDING_PATH"/*.sql: a topic subdirectory (e.g.
    # pending_db_world/itemization_templates_v2/, keeping one system's whole pending history
    # browsable in one place) holds real pending files too, and both the real DBUpdater and this
    # repo's own tooling (apps/item-tools/lib/*_overlay.py) already treat migrations as ordered by
    # bare filename, not directory path -- sorted on `-printf '%f\t%p\n' | sort -k1,1` (filename
    # only) for exactly that reason, so a file's position in this merge matches its
    # rev_<timestamp> order globally, regardless of which subdirectory (if any) it started in.
    while IFS= read -r entry; do
        if [[ -f "$entry" ]]; then
            INDEX="$(get_next_index "$LATEST_UPDATE_TODAY")"
            OUTPUT_FILE="${UPDATES_DIR}/${TODAY}_${INDEX}.sql"

            # ensure a note is added as a header comment
            echo "-- DB update $(basename "$LATEST_UPDATE" .sql) -> $(basename "$OUTPUT_FILE" .sql)" >"$OUTPUT_FILE"
            # fill in the SQL contents under that
            cat "$entry" >>"$OUTPUT_FILE"
            # remove the unneeded file
            rm -f "$entry"
            # set the newest file to the file we just moved
            LATEST_UPDATE_TODAY="$OUTPUT_FILE"
            LATEST_UPDATE="$OUTPUT_FILE"
        fi
    done < <(find "$PENDING_PATH" -type f -iname "*.sql" -printf '%f\t%p\n' | sort -k1,1 | cut -f2-)

}

import "world"
import "characters"
import "auth"

echo "Done."
