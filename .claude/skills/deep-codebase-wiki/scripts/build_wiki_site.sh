#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

WIKI_REF=""
OUT_DIR=""
WEB_WORKDIR="${WIKI_WEB_TMP_DIR:-/tmp/wiki-web}"

usage() {
    echo "Usage: $0 <org-repo|wiki-path> [--out-dir PATH]"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out-dir)
            [[ $# -ge 2 ]] || die "--out-dir requires a value"
            OUT_DIR="$2"
            shift 2
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
require_cmd "mkdocs" "Install MkDocs first: pip install mkdocs"

if ! WIKI_PATH="$(resolve_wiki_path "$WIKI_REF")"; then
    die "Wiki not found: $WIKI_REF"
fi

SITE_SLUG="$(basename "$WIKI_PATH")"
PROJECT_DIR="$WEB_WORKDIR/$SITE_SLUG"
if [[ -z "$OUT_DIR" ]]; then
    OUT_DIR="${PWD}/site-$SITE_SLUG"
fi

generate_mkdocs_project "$WIKI_PATH" "$PROJECT_DIR" "Wiki: $SITE_SLUG"

echo "Building static site from: $WIKI_PATH"
echo "Output directory: $OUT_DIR"
mkdocs build --config-file "$PROJECT_DIR/mkdocs.yml" --site-dir "$OUT_DIR"
echo "Build completed."
