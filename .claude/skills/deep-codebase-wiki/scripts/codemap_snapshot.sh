#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

REPO_PATH=""
OUT_DIR=""
REF="${CODEMAP_REF:-main}"
SKIP_DEPS="false"

usage() {
    echo "Usage: $0 <repo-path> [--out-dir PATH] [--ref BRANCH] [--skip-deps]"
    echo ""
    echo "Optional codemap enhancer:"
    echo "  - Generates JSON snapshots to help wiki analysis."
    echo "  - Exits successfully with a warning when codemap is not installed."
}

run_capture() {
    local output_file="$1"
    shift
    if "$@" >"$output_file" 2>"${output_file}.stderr"; then
        rm -f "${output_file}.stderr"
        return 0
    fi

    log_warn "Command failed: $*"
    return 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out-dir)
            [[ $# -ge 2 ]] || die "--out-dir requires a value"
            OUT_DIR="$2"
            shift 2
            ;;
        --ref)
            [[ $# -ge 2 ]] || die "--ref requires a value"
            REF="$2"
            shift 2
            ;;
        --skip-deps)
            SKIP_DEPS="true"
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
            if [[ -n "$REPO_PATH" ]]; then
                die "Unexpected positional argument: $1"
            fi
            REPO_PATH="$1"
            shift
            ;;
    esac
done

[[ -n "$REPO_PATH" ]] || {
    usage
    die "Repository path is required."
}

[[ -d "$REPO_PATH" ]] || die "Repository path does not exist: $REPO_PATH"

if ! command -v codemap >/dev/null 2>&1; then
    log_warn "codemap is not installed. Skipping optional codemap snapshot."
    log_warn "Install hint: brew tap JordanCoin/tap && brew install codemap"
    exit 0
fi

if [[ -z "$OUT_DIR" ]]; then
    OUT_DIR="${WIKI_CODEMAP_OUT_DIR:-$REPO_PATH/.codemap-snapshot}"
fi

mkdir -p "$OUT_DIR"

log_info "Generating codemap snapshots for: $REPO_PATH"
log_info "Output directory: $OUT_DIR"

pushd "$REPO_PATH" >/dev/null
run_capture "$OUT_DIR/overview.json" codemap --json .
run_capture "$OUT_DIR/diff.json" codemap --json --diff --ref "$REF" .

if [[ "$SKIP_DEPS" == "false" ]]; then
    if ! run_capture "$OUT_DIR/deps.json" codemap --json --deps .; then
        log_warn "Dependency snapshot failed. This usually means ast-grep is missing."
    fi
fi

run_capture "$OUT_DIR/context.json" codemap context --compact
popd >/dev/null

cat >"$OUT_DIR/README.md" <<EOF
# Codemap Snapshot

Generated from: \`$REPO_PATH\`

Files:
- \`overview.json\`: structural project context
- \`diff.json\`: changed files summary compared with \`$REF\`
- \`deps.json\`: dependency flow snapshot (optional)
- \`context.json\`: compact codemap context envelope

These artifacts are optional accelerators for wiki analysis.
EOF

log_info "Codemap snapshot completed."
