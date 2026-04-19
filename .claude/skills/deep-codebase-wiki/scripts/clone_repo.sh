#!/bin/bash
# Clone a GitHub repository for wiki analysis
# Usage: clone_repo.sh <owner/repo> [--depth N] [--branch NAME]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

REPO_PATH=""
DEPTH="${WIKI_DEFAULT_DEPTH:-1}"
BRANCH="${WIKI_DEFAULT_BRANCH:-main}"
WORKDIR="${WIKI_TMP_DIR:-/tmp/wiki-analysis}"
GIT_BASE_URL="${GIT_BASE_URL:-https://github.com}"

usage() {
    echo "Usage: $0 <owner/repo> [--depth N] [--branch NAME]"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --depth)
            [[ $# -ge 2 ]] || die "--depth requires a value"
            DEPTH="$2"
            shift 2
            ;;
        --branch)
            [[ $# -ge 2 ]] || die "--branch requires a value"
            BRANCH="$2"
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
            if [[ -n "$REPO_PATH" ]]; then
                die "Unexpected positional argument: $1"
            fi
            REPO_PATH="$1"
            shift
            ;;
    esac
done

if [[ -z "$REPO_PATH" ]]; then
    usage
    die "Repository path required (format: owner/repo)"
fi

require_cmd "git"

if [[ ! "$REPO_PATH" =~ ^[^/]+/[^/]+$ ]]; then
    die "Invalid repository path '$REPO_PATH'. Expected format: owner/repo"
fi

if [[ ! "$DEPTH" =~ ^[1-9][0-9]*$ ]]; then
    die "Invalid --depth value '$DEPTH'. It must be a positive integer."
fi

# Extract owner and repo
OWNER=$(echo "$REPO_PATH" | cut -d'/' -f1)
REPO=$(echo "$REPO_PATH" | cut -d'/' -f2)
DEST_DIR="$WORKDIR/${OWNER}-${REPO}"

# Create work directory
mkdir -p "$WORKDIR"

# Remove existing clone if present
if [[ -d "$DEST_DIR" ]]; then
    echo "Removing existing clone at $DEST_DIR"
    rm -rf "$DEST_DIR"
fi

# Clone repository
echo "Cloning ${GIT_BASE_URL}/${REPO_PATH}.git"
echo "Destination: $DEST_DIR"
echo "Depth: $DEPTH, Branch: $BRANCH"

if [[ "$DEPTH" -eq 1 ]]; then
    git clone --depth "$DEPTH" --branch "$BRANCH" --single-branch \
        "${GIT_BASE_URL}/${REPO_PATH}.git" "$DEST_DIR"
else
    git clone --depth "$DEPTH" --branch "$BRANCH" \
        "${GIT_BASE_URL}/${REPO_PATH}.git" "$DEST_DIR"
fi

# Get commit SHA
cd "$DEST_DIR"
COMMIT_SHA=$(git rev-parse HEAD)
COMMIT_DATE=$(git log -1 --format=%cd --date=iso)

echo ""
echo "Clone successful"
echo "Location: $DEST_DIR"
echo "Commit: $COMMIT_SHA"
echo "Date: $COMMIT_DATE"
echo ""
echo "Export for use:"
echo "export WIKI_REPO_DIR=\"$DEST_DIR\""
echo "export WIKI_COMMIT_SHA=\"$COMMIT_SHA\""
