#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

WIKI_PATH="${1:-}"

if [[ -z "$WIKI_PATH" ]]; then
    echo "Usage: $0 <wiki-path>" >&2
    exit 1
fi

if [[ ! -d "$WIKI_PATH" ]]; then
    echo "Error: Wiki path does not exist: $WIKI_PATH" >&2
    exit 1
fi

ERRORS=0
WARNINGS=0

check_file() {
    local file="$1"
    local level="${2:-error}"
    
    if [[ ! -f "$WIKI_PATH/$file" ]]; then
        if [[ "$level" == "error" ]]; then
            echo "ERROR: Missing required file: $file"
            ERRORS=$((ERRORS + 1))
        else
            echo "WARNING: Missing recommended file: $file"
            WARNINGS=$((WARNINGS + 1))
        fi
        return 1
    fi
    return 0
}

check_dir() {
    local dir="$1"
    local level="${2:-warning}"
    
    if [[ ! -d "$WIKI_PATH/$dir" ]]; then
        if [[ "$level" == "error" ]]; then
            echo "ERROR: Missing required directory: $dir"
            ERRORS=$((ERRORS + 1))
        else
            echo "WARNING: Missing recommended directory: $dir"
            WARNINGS=$((WARNINGS + 1))
        fi
        return 1
    fi
    return 0
}

check_yaml_field() {
    local field="$1"
    
    if ! grep -q "^${field}:" "$WIKI_PATH/metadata.yaml" 2>/dev/null; then
        echo "ERROR: Missing metadata field: $field"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
    return 0
}

echo "Validating wiki: $WIKI_PATH"
echo ""

check_file "metadata.yaml" "error" || true
check_file "overview.md" "error" || true

check_dir "systems" "warning" || true
check_dir "components" "warning" || true
check_dir "traces" "warning" || true

if [[ -f "$WIKI_PATH/metadata.yaml" ]]; then
    check_yaml_field "analyzed_at" || true
    check_yaml_field "scope" || true

    # source_type determines which fields are required
    local source_type
    source_type=$(awk -F': *' '$1 == "source_type" {print substr($0, index($0,$2)); exit}' "$WIKI_PATH/metadata.yaml" 2>/dev/null)
    source_type="${source_type#\'}"
    source_type="${source_type%\'}"
    source_type="${source_type#\"}"
    source_type="${source_type%\"}"

    if [[ "$source_type" == "local" ]]; then
        # Local wikis need source_path instead of repository
        if ! grep -q "^source_path:" "$WIKI_PATH/metadata.yaml" 2>/dev/null; then
            echo "WARNING: Missing metadata field: source_path (local wiki)"
            WARNINGS=$((WARNINGS + 1))
        fi
    else
        check_yaml_field "repository" || true
        check_yaml_field "commit_sha" || true
    fi
fi

if [[ -f "$WIKI_PATH/overview.md" ]]; then
    word_count=$(wc -w < "$WIKI_PATH/overview.md")
    if [[ $word_count -lt 50 ]]; then
        echo "WARNING: overview.md seems very short ($word_count words)"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

echo ""
if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
    echo "Wiki validation passed."
    exit 0
elif [[ $ERRORS -eq 0 ]]; then
    echo "Wiki validation passed with $WARNINGS warning(s)."
    exit 0
else
    echo "Wiki validation failed with $ERRORS error(s) and $WARNINGS warning(s)."
    exit 1
fi
