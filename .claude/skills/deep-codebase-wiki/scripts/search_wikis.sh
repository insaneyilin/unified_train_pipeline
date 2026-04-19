#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

# Global index (always available)
WIKIS_DIR="${WIKIS_DIR:-${HOME}/.claude/wikis}"
INDEX_FILE="${INDEX_FILE:-${WIKIS_DIR}/index.json}"

# Project-local index (available when inside a git repo)
PROJECT_WIKIS_DIR=""
PROJECT_INDEX_FILE=""
_project_root="$(detect_project_root)"
if [[ -n "$_project_root" ]]; then
    PROJECT_WIKIS_DIR="$_project_root/.claude/wikis"
    PROJECT_INDEX_FILE="$PROJECT_WIKIS_DIR/index.json"
fi

usage() {
    echo "Usage:"
    echo "  $0 --list"
    echo "  $0 --repo <owner/repo|wiki-name>"
    echo "  $0 --local <path>"
    echo "  $0 --query <search>"
    echo "  $0 --add <name> <repo> <path> <sha> [--source-type github|local] [--source-path PATH]"
    echo "  $0 --remove <name>"
    echo ""
    echo "Notes:"
    echo "  --query searches repository/name metadata in index.json."
    echo "  --local finds a wiki by original source path (for local projects)."
    echo "  Searches check project-local index first, then global."
}

ensure_index() {
    local dir="$1"
    local file="$2"
    mkdir -p "$dir"
    if [[ ! -f "$file" ]]; then
        echo '{"wikis":[]}' > "$file"
    fi
}

init_global_index() {
    ensure_index "$WIKIS_DIR" "$INDEX_FILE"
}

init_project_index() {
    if [[ -n "$PROJECT_WIKIS_DIR" ]]; then
        ensure_index "$PROJECT_WIKIS_DIR" "$PROJECT_INDEX_FILE"
    fi
}

# --- Search functions (project-local first, then global) ---

list_wikis() {
    init_global_index
    if [[ -n "$PROJECT_INDEX_FILE" && -f "$PROJECT_INDEX_FILE" ]]; then
        jq -r '.wikis[] | "\(.name) - \(.repository // .source_path // "local") [\(.source_type // "github")] (analyzed: \(.analyzed_at)) [project]"' "$PROJECT_INDEX_FILE"
    fi
    jq -r '.wikis[] | "\(.name) - \(.repository // .source_path // "local") [\(.source_type // "github")] (analyzed: \(.analyzed_at))"' "$INDEX_FILE"
}

search_by_repo() {
    local repo="$1"
    # Check project-local first
    if [[ -n "$PROJECT_INDEX_FILE" && -f "$PROJECT_INDEX_FILE" ]]; then
        local result
        result=$(jq -r --arg repo "$repo" '.wikis[] | select(.repository == $repo or .name == $repo) | .path' "$PROJECT_INDEX_FILE")
        if [[ -n "$result" ]]; then
            echo "$result"
            return
        fi
    fi
    init_global_index
    jq -r --arg repo "$repo" '.wikis[] | select(.repository == $repo or .name == $repo) | .path' "$INDEX_FILE"
}

search_by_local() {
    local source_path="$1"
    local norm_path
    norm_path="$(cd "$source_path" 2>/dev/null && pwd)" || norm_path="$source_path"
    # Check project-local first
    if [[ -n "$PROJECT_INDEX_FILE" && -f "$PROJECT_INDEX_FILE" ]]; then
        local result
        result=$(jq -r --arg sp "$norm_path" '.wikis[] | select(.source_path == $sp) | .path' "$PROJECT_INDEX_FILE")
        if [[ -n "$result" ]]; then
            echo "$result"
            return
        fi
    fi
    init_global_index
    jq -r --arg sp "$norm_path" '.wikis[] | select(.source_path == $sp) | .path' "$INDEX_FILE"
}

search_by_query() {
    local query="$1"
    if [[ -n "$PROJECT_INDEX_FILE" && -f "$PROJECT_INDEX_FILE" ]]; then
        jq -r --arg q "$query" '.wikis[] | select((.repository // "" | contains($q)) or (.name | contains($q)) or (.source_path // "" | contains($q))) | "\(.name) - \(.repository // .source_path // "local") - \(.path) [project]"' "$PROJECT_INDEX_FILE"
    fi
    init_global_index
    jq -r --arg q "$query" '.wikis[] | select((.repository // "" | contains($q)) or (.name | contains($q)) or (.source_path // "" | contains($q))) | "\(.name) - \(.repository // .source_path // "local") - \(.path)"' "$INDEX_FILE"
}

# --- Write functions ---

add_wiki() {
    local name="$1"
    local repo="$2"
    local path="$3"
    local commit_sha="$4"
    local source_type="${ADD_SOURCE_TYPE:-github}"
    local source_path="${ADD_SOURCE_PATH:-}"
    local analyzed_at
    analyzed_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

    # Route to project-local or global index
    local target_dir="$WIKIS_DIR"
    local target_index="$INDEX_FILE"
    if [[ "$source_type" == "local" && -n "$PROJECT_WIKIS_DIR" ]]; then
        target_dir="$PROJECT_WIKIS_DIR"
        target_index="$PROJECT_INDEX_FILE"
    fi

    ensure_index "$target_dir" "$target_index"

    # Remove existing entry with same name to avoid duplicates
    jq --arg name "$name" '.wikis |= map(select(.name != $name))' "$target_index" > "${target_index}.tmp"
    mv "${target_index}.tmp" "$target_index"

    local entry
    entry=$(jq -n \
        --arg name "$name" \
        --arg repo "$repo" \
        --arg path "$path" \
        --arg sha "$commit_sha" \
        --arg date "$analyzed_at" \
        --arg stype "$source_type" \
        --arg spath "$source_path" \
        '{name: $name, repository: $repo, path: $path, commit_sha: $sha, analyzed_at: $date, source_type: $stype, source_path: $spath}')

    jq --argjson entry "$entry" '.wikis += [$entry]' "$target_index" > "${target_index}.tmp"
    mv "${target_index}.tmp" "$target_index"

    echo "Added wiki: $name ($repo) [source: $source_type, index: $target_dir]"
}

remove_wiki() {
    local name="$1"
    local wiki_path=""
    local found_in=""

    # Search project-local index first
    if [[ -n "$PROJECT_INDEX_FILE" && -f "$PROJECT_INDEX_FILE" ]]; then
        wiki_path=$(jq -r --arg name "$name" '.wikis[] | select(.name == $name) | .path' "$PROJECT_INDEX_FILE")
        if [[ -n "$wiki_path" ]]; then
            found_in="project"
        fi
    fi

    # Fall back to global
    if [[ -z "$wiki_path" ]]; then
        init_global_index
        wiki_path=$(jq -r --arg name "$name" '.wikis[] | select(.name == $name) | .path' "$INDEX_FILE")
        if [[ -n "$wiki_path" ]]; then
            found_in="global"
        fi
    fi

    if [[ -z "$wiki_path" ]]; then
        echo "No wiki found with name: $name" >&2
        exit 1
    fi

    echo "Removing wiki: $name"
    echo "  Index: $found_in"
    if [[ -d "$wiki_path" ]]; then
        echo "  Directory: $wiki_path"
    else
        echo "  Directory: $wiki_path (not found on disk)"
    fi

    # Remove from the correct index
    if [[ "$found_in" == "project" ]]; then
        jq --arg name "$name" '.wikis |= map(select(.name != $name))' "$PROJECT_INDEX_FILE" > "${PROJECT_INDEX_FILE}.tmp"
        mv "${PROJECT_INDEX_FILE}.tmp" "$PROJECT_INDEX_FILE"
    else
        jq --arg name "$name" '.wikis |= map(select(.name != $name))' "$INDEX_FILE" > "${INDEX_FILE}.tmp"
        mv "${INDEX_FILE}.tmp" "$INDEX_FILE"
    fi

    # Remove from disk
    if [[ -d "$wiki_path" ]]; then
        rm -rf "$wiki_path"
        echo "Deleted directory: $wiki_path"
    fi

    echo "Wiki removed: $name"
}

# --- Main ---

main() {
    require_cmd "jq" "Install jq first (macOS: brew install jq)."

    if [[ $# -eq 0 ]]; then
        usage
        exit 1
    fi

    local cmd="$1"
    shift

    case "$cmd" in
    --list)
        list_wikis
        ;;
    --repo)
        if [[ $# -ne 1 || -z "${1:-}" ]]; then
            usage
            exit 1
        fi
        search_by_repo "$1"
        ;;
    --local)
        if [[ $# -ne 1 || -z "${1:-}" ]]; then
            usage
            exit 1
        fi
        search_by_local "$1"
        ;;
    --query)
        if [[ $# -ne 1 || -z "${1:-}" ]]; then
            usage
            exit 1
        fi
        search_by_query "$1"
        ;;
    --add)
        if [[ $# -lt 4 ]]; then
            usage
            exit 1
        fi
        local add_name="$1" add_repo="$2" add_path="$3" add_sha="$4"
        shift 4
        export ADD_SOURCE_TYPE="github"
        export ADD_SOURCE_PATH=""
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --source-type)
                    [[ $# -ge 2 ]] || die "--source-type requires a value"
                    export ADD_SOURCE_TYPE="$2"
                    shift 2
                    ;;
                --source-path)
                    [[ $# -ge 2 ]] || die "--source-path requires a value"
                    export ADD_SOURCE_PATH="$2"
                    shift 2
                    ;;
                *)
                    die "Unknown add option: $1"
                    ;;
            esac
        done
        add_wiki "$add_name" "$add_repo" "$add_path" "$add_sha"
        ;;
    --remove)
        if [[ $# -ne 1 || -z "${1:-}" ]]; then
            usage
            exit 1
        fi
        remove_wiki "$1"
        ;;
    *)
        usage
        exit 1
        ;;
    esac
}

main "$@"
