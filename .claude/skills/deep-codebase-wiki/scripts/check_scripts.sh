#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Running shell syntax checks..."
bash -n "$SCRIPT_DIR/lib/common.sh"
bash -n "$SCRIPT_DIR/search_wikis.sh"
bash -n "$SCRIPT_DIR/clone_repo.sh"
bash -n "$SCRIPT_DIR/validate_wiki.sh"
bash -n "$SCRIPT_DIR/update_check.sh"
bash -n "$SCRIPT_DIR/serve_wiki_web.sh"
bash -n "$SCRIPT_DIR/build_wiki_site.sh"
bash -n "$SCRIPT_DIR/codemap_snapshot.sh"
bash -n "$SCRIPT_DIR/codemap_preference.sh"
bash -n "$SCRIPT_DIR/codemap_status.sh"
bash -n "$SCRIPT_DIR/codemap_install.sh"
bash -n "$SCRIPT_DIR/analyze_local.sh"

echo "All script syntax checks passed."
