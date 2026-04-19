#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

PREF_FILE="$(default_codemap_pref_file)"

usage() {
    echo "Usage:"
    echo "  $0 get"
    echo "  $0 set <ask|always|never>"
    echo "  $0 reset"
}

read_pref() {
    if [[ -f "$PREF_FILE" ]]; then
        tr -d '[:space:]' < "$PREF_FILE"
    else
        echo "ask"
    fi
}

validate_pref() {
    local value="$1"
    case "$value" in
        ask|always|never) return 0 ;;
        *) return 1 ;;
    esac
}

cmd="${1:-}"
case "$cmd" in
    get)
        if [[ $# -ne 1 ]]; then
            usage
            exit 1
        fi
        pref="$(read_pref)"
        if ! validate_pref "$pref"; then
            echo "ask"
            exit 0
        fi
        echo "$pref"
        ;;
    set)
        if [[ $# -ne 2 ]]; then
            usage
            exit 1
        fi
        value="$2"
        validate_pref "$value" || die "Invalid preference '$value'. Use ask|always|never."
        mkdir -p "$(dirname "$PREF_FILE")"
        echo "$value" > "$PREF_FILE"
        echo "Saved codemap preference: $value"
        ;;
    reset)
        if [[ $# -ne 1 ]]; then
            usage
            exit 1
        fi
        rm -f "$PREF_FILE"
        echo "Reset codemap preference to default (ask)."
        ;;
    *)
        usage
        exit 1
        ;;
esac
