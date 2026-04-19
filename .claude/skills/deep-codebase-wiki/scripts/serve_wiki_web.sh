#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

WIKI_REF=""
PORT="${WIKI_WEB_PORT:-8000}"
HOST="${WIKI_WEB_HOST:-127.0.0.1}"
OPEN_BROWSER="false"
WEB_WORKDIR="${WIKI_WEB_TMP_DIR:-/tmp/wiki-web}"

usage() {
    echo "Usage: $0 <org-repo|wiki-path> [--port N] [--host ADDR] [--open]"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --port)
            [[ $# -ge 2 ]] || die "--port requires a value"
            PORT="$2"
            shift 2
            ;;
        --host)
            [[ $# -ge 2 ]] || die "--host requires a value"
            HOST="$2"
            shift 2
            ;;
        --open)
            OPEN_BROWSER="true"
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        --*)
            die "Unknown option: $1"
            ;;
        *)
            if [[ -n "$WIKI_REF" ]]; then
                die "Unexpected positional argument: $1"
            fi
            WIKI_REF="$1"
            shift
            ;;
    esac
done

[[ -n "$WIKI_REF" ]] || { usage; die "Wiki reference is required."; }
[[ "$PORT" =~ ^[1-9][0-9]*$ ]] || die "Invalid port '$PORT'."

require_cmd "mkdocs" "Install MkDocs first: pip install mkdocs"

if ! WIKI_PATH="$(resolve_wiki_path "$WIKI_REF")"; then
    die "Wiki not found: $WIKI_REF"
fi

SITE_SLUG="$(basename "$WIKI_PATH")"
PROJECT_DIR="$WEB_WORKDIR/$SITE_SLUG"
SITE_URL="http://$HOST:$PORT"

generate_mkdocs_project "$WIKI_PATH" "$PROJECT_DIR" "Wiki: $SITE_SLUG"

echo "Serving wiki from: $WIKI_PATH"
echo "URL: $SITE_URL"
echo "Press Ctrl+C to stop."

if [[ "$OPEN_BROWSER" == "true" ]]; then
    open_url "$SITE_URL"
fi

exec mkdocs serve --dev-addr "$HOST:$PORT" --config-file "$PROJECT_DIR/mkdocs.yml"
