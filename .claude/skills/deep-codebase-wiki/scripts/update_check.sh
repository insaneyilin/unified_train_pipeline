#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

WIKI_PATH="${1:-}"
BRANCH="${2:-${WIKI_DEFAULT_BRANCH:-main}}"
TEMP_DIR="${WIKI_UPDATE_TMP_DIR:-/tmp/wiki-update-check}"
GIT_BASE_URL="${GIT_BASE_URL:-https://github.com}"

usage() {
    echo "Usage: $0 <wiki-path> [branch]"
}

if [[ -z "$WIKI_PATH" ]]; then
    usage >&2
    exit 1
fi

require_cmd "git"

if [[ ! -f "$WIKI_PATH/metadata.yaml" ]]; then
    echo "Error: No metadata.yaml found in $WIKI_PATH" >&2
    exit 1
fi

get_metadata_value() {
    local key="$1"
    local value
    value=$(awk -F': *' -v key="$key" '$1 == key {print substr($0, index($0,$2)); exit}' "$WIKI_PATH/metadata.yaml")
    value="${value#\'}"
    value="${value%\'}"
    value="${value#\"}"
    value="${value%\"}"
    echo "$value"
}

SOURCE_TYPE="$(get_metadata_value "source_type")"
SOURCE_TYPE="${SOURCE_TYPE:-github}"
REPO="$(get_metadata_value "repository")"
OLD_SHA="$(get_metadata_value "commit_sha")"
ANALYZED_AT="$(get_metadata_value "analyzed_at")"
SOURCE_PATH="$(get_metadata_value "source_path")"

# --- Local wiki update check ---
if [[ "$SOURCE_TYPE" == "local" ]]; then
    if [[ -z "$SOURCE_PATH" || ! -d "$SOURCE_PATH" ]]; then
        die "Local wiki source_path is missing or does not exist: $SOURCE_PATH"
    fi

    NOW=$(date -u +%s)
    if ANALYZED_TS="$(iso8601_to_epoch "$ANALYZED_AT")"; then
        :
    else
        log_warn "Could not parse analyzed_at '$ANALYZED_AT'; using current time."
        ANALYZED_TS="$NOW"
    fi
    AGE_DAYS=$(( (NOW - ANALYZED_TS) / 86400 ))

    echo "Wiki: $(basename "$WIKI_PATH")"
    echo "Source: $SOURCE_PATH (local)"
    echo "Analyzed: $ANALYZED_AT ($AGE_DAYS days ago)"

    # For git-tracked local repos, compare commits
    if git -C "$SOURCE_PATH" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        NEW_SHA=$(git -C "$SOURCE_PATH" rev-parse HEAD 2>/dev/null || echo "none")
        echo "Commit: ${OLD_SHA:0:8} -> ${NEW_SHA:0:8}"

        if [[ "$OLD_SHA" == "$NEW_SHA" && $AGE_DAYS -le 90 ]]; then
            echo ""
            echo "Status: UP TO DATE"
            exit 0
        fi

        if [[ "$OLD_SHA" != "none" && "$NEW_SHA" != "none" && "$OLD_SHA" != "$NEW_SHA" ]]; then
            STATS=$(git -C "$SOURCE_PATH" diff --shortstat "$OLD_SHA" "$NEW_SHA" 2>/dev/null || echo "0 files changed")
            echo ""
            echo "Changes: $STATS"
        fi
    fi

    echo ""
    RECOMMENDATION="up_to_date"
    REASONS=()
    if [[ $AGE_DAYS -gt 90 ]]; then
        REASONS+=("Wiki is $AGE_DAYS days old (>90 days)")
    fi
    if [[ -n "${NEW_SHA:-}" && "$OLD_SHA" != "${NEW_SHA:-}" ]]; then
        REASONS+=("Source has new commits since analysis")
    fi

    if [[ ${#REASONS[@]} -ge 2 ]]; then
        RECOMMENDATION="full_reanalysis"
    elif [[ ${#REASONS[@]} -ge 1 ]]; then
        RECOMMENDATION="partial_update"
    fi

    echo "Recommendation: ${RECOMMENDATION^^}"
    if [[ ${#REASONS[@]} -gt 0 ]]; then
        echo "Reasons:"
        for reason in "${REASONS[@]}"; do
            echo "  - $reason"
        done
    fi
    exit 0
fi

# --- GitHub wiki update check ---
if [[ -z "$REPO" || -z "$OLD_SHA" ]]; then
    die "metadata.yaml must include repository and commit_sha fields."
fi

REPO_NAME="${REPO//\//-}"
REPO_DIR="$TEMP_DIR/$REPO_NAME"

mkdir -p "$TEMP_DIR"

if [[ -d "$REPO_DIR" ]]; then
    cd "$REPO_DIR"
    git fetch origin "$BRANCH" --quiet
    git reset --hard "origin/$BRANCH" --quiet
else
    git clone --depth 50 --branch "$BRANCH" "${GIT_BASE_URL}/${REPO}.git" "$REPO_DIR" --quiet
    cd "$REPO_DIR"
fi

NEW_SHA=$(git rev-parse HEAD)

if [[ "$OLD_SHA" == "$NEW_SHA" ]]; then
    echo "Wiki: $(basename "$WIKI_PATH")"
    echo "Repository: $REPO"
    echo "Status: UP TO DATE"
    echo "Commit: $OLD_SHA"
    exit 0
fi

STATS=$(git diff --shortstat "$OLD_SHA" "$NEW_SHA" 2>/dev/null || echo "0 files changed")
FILES_CHANGED=$(echo "$STATS" | grep -o "[0-9]* file" | cut -d' ' -f1)
FILES_CHANGED=${FILES_CHANGED:-0}

TOTAL_FILES=$(git ls-files | wc -l)
if [[ "$TOTAL_FILES" -eq 0 ]]; then
    CHANGE_PCT="0.0"
else
    CHANGE_PCT=$(awk "BEGIN {printf \"%.1f\", ($FILES_CHANGED / $TOTAL_FILES) * 100}")
fi

NOW=$(date -u +%s)
if ANALYZED_TS="$(iso8601_to_epoch "$ANALYZED_AT")"; then
    :
else
    log_warn "Could not parse analyzed_at '$ANALYZED_AT'; using current time."
    ANALYZED_TS="$NOW"
fi
AGE_DAYS=$(( (NOW - ANALYZED_TS) / 86400 ))

echo "Wiki: $(basename "$WIKI_PATH")"
echo "Repository: $REPO"
echo "Analyzed: $ANALYZED_AT ($AGE_DAYS days ago)"
echo "Commit: ${OLD_SHA:0:8} -> ${NEW_SHA:0:8}"
echo ""
echo "Changes:"
echo "  Files changed: $FILES_CHANGED / $TOTAL_FILES ($CHANGE_PCT%)"
echo "  $STATS"
echo ""

RECOMMENDATION="up_to_date"
REASONS=()

if [[ $AGE_DAYS -gt 90 ]]; then
    REASONS+=("Wiki is $AGE_DAYS days old (>90 days)")
fi

if awk "BEGIN {exit !($CHANGE_PCT > 30)}"; then
    REASONS+=("$CHANGE_PCT% of files changed (>30%)")
fi

if [[ $FILES_CHANGED -gt 100 ]]; then
    REASONS+=("$FILES_CHANGED files changed (>100)")
fi

if [[ ${#REASONS[@]} -ge 2 ]] || awk "BEGIN {exit !($CHANGE_PCT > 50)}"; then
    RECOMMENDATION="full_reanalysis"
elif [[ ${#REASONS[@]} -ge 1 ]] || [[ $FILES_CHANGED -gt 10 ]]; then
    RECOMMENDATION="partial_update"
fi

echo "Recommendation: ${RECOMMENDATION^^}"
if [[ ${#REASONS[@]} -gt 0 ]]; then
    echo "Reasons:"
    for reason in "${REASONS[@]}"; do
        echo "  - $reason"
    done
fi
