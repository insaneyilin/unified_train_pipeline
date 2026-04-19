#!/bin/bash
# Prepare a local (non-GitHub) codebase for wiki analysis.
# Usage: analyze_local.sh <path> [--name NAME]
#
# Detects project info from a local directory and prints the variables
# needed by the wiki workflow. Works for any directory — git repo or not.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

TARGET_PATH=""
WIKI_NAME=""

usage() {
    echo "Usage: $0 <path> [--name NAME]"
    echo ""
    echo "Prepare a local codebase for wiki analysis."
    echo "  <path>       Directory to analyze (must exist)"
    echo "  --name NAME  Wiki name override (default: derived from directory name)"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --name)
            [[ $# -ge 2 ]] || die "--name requires a value"
            WIKI_NAME="$2"
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
            if [[ -n "$TARGET_PATH" ]]; then
                die "Unexpected positional argument: $1"
            fi
            TARGET_PATH="$1"
            shift
            ;;
    esac
done

if [[ -z "$TARGET_PATH" ]]; then
    usage
    die "Path is required."
fi

TARGET_PATH="$(cd "$TARGET_PATH" && pwd)"

if [[ ! -d "$TARGET_PATH" ]]; then
    die "Directory does not exist: $TARGET_PATH"
fi

# --- Derive wiki name ---
if [[ -z "$WIKI_NAME" ]]; then
    # Try git remote first
    if git -C "$TARGET_PATH" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        REMOTE_URL="$(git -C "$TARGET_PATH" remote get-url origin 2>/dev/null || true)"
        if [[ -n "$REMOTE_URL" ]]; then
            # Extract owner/repo from URL
            WIKI_NAME="$(echo "$REMOTE_URL" | sed -E 's#.*[:/]([^/]+)/([^/.]+)(\.git)?$#\1-\2#')"
        fi
    fi

    # Fall back to directory name
    if [[ -z "$WIKI_NAME" ]]; then
        WIKI_NAME="local-$(basename "$TARGET_PATH")"
    fi
fi

# Sanitize name: lowercase, replace non-alphanumeric with hyphens
WIKI_NAME="$(echo "$WIKI_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//')"

# --- Detect git info (optional) ---
COMMIT_SHA="none"
COMMIT_DATE=""
IS_GIT="false"
GIT_REMOTE=""

if git -C "$TARGET_PATH" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    IS_GIT="true"
    COMMIT_SHA="$(git -C "$TARGET_PATH" rev-parse HEAD 2>/dev/null || echo "none")"
    COMMIT_DATE="$(git -C "$TARGET_PATH" log -1 --format=%cd --date=iso 2>/dev/null || true)"
    GIT_REMOTE="$(git -C "$TARGET_PATH" remote get-url origin 2>/dev/null || true)"
fi

# --- Detect primary language (bash 3 compatible — no associative arrays) ---
PRIMARY_LANG="Unknown"

count_ext() {
    find "$TARGET_PATH" -maxdepth 4 -name "*.$1" \
        -not -path "*/node_modules/*" -not -path "*/.git/*" \
        -not -path "*/vendor/*" -not -path "*/dist/*" \
        -not -path "*/build/*" 2>/dev/null | head -200 | wc -l | tr -d ' '
}

best_count=0

check_lang() {
    local lang="$1"
    shift
    local total=0
    for ext in "$@"; do
        local c
        c=$(count_ext "$ext")
        total=$((total + c))
    done
    if [[ $total -gt $best_count ]]; then
        best_count=$total
        PRIMARY_LANG="$lang"
    fi
}

check_lang "TypeScript" ts tsx
check_lang "JavaScript" js jsx
check_lang "Python" py
check_lang "Go" go
check_lang "Rust" rs
check_lang "Java" java
check_lang "Ruby" rb
check_lang "Swift" swift
check_lang "Kotlin" kt
check_lang "C" c
check_lang "C++" cpp
check_lang "C#" cs
check_lang "PHP" php

# --- Count total files ---
TOTAL_FILES=$(find "$TARGET_PATH" -type f -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/vendor/*" -not -path "*/dist/*" -not -path "*/build/*" 2>/dev/null | head -5000 | wc -l)
TOTAL_FILES=$((TOTAL_FILES + 0))

# --- Output ---
echo "Wiki name: $WIKI_NAME"
echo "Source path: $TARGET_PATH"
echo "Is git repo: $IS_GIT"
echo "Commit SHA: $COMMIT_SHA"
if [[ -n "$COMMIT_DATE" ]]; then
    echo "Commit date: $COMMIT_DATE"
fi
if [[ -n "$GIT_REMOTE" ]]; then
    echo "Git remote: $GIT_REMOTE"
fi
echo "Primary language: $PRIMARY_LANG"
echo "Total files: $TOTAL_FILES"
echo ""
echo "Export for use:"
echo "export WIKI_REPO_DIR=\"$TARGET_PATH\""
echo "export WIKI_COMMIT_SHA=\"$COMMIT_SHA\""
echo "export WIKI_NAME=\"$WIKI_NAME\""
echo "export WIKI_SOURCE_TYPE=\"local\""
