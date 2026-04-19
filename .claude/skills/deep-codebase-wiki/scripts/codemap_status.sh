#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

AS_JSON="false"

usage() {
    echo "Usage: $0 [--json]"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            AS_JSON="true"
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            usage
            exit 1
            ;;
    esac
done

platform="$(detect_platform)"
preference="$("$SCRIPT_DIR/codemap_preference.sh" get)"
installed="false"
version=""

if command -v codemap >/dev/null 2>&1; then
    installed="true"
    version="$(codemap --version 2>/dev/null || echo "unknown")"
fi

if [[ "$AS_JSON" == "true" ]]; then
    printf '{\n'
    printf '  "installed": %s,\n' "$installed"
    printf '  "version": "%s",\n' "${version//\"/\\\"}"
    printf '  "preference": "%s",\n' "$preference"
    printf '  "platform": "%s"\n' "$platform"
    printf '}\n'
    exit 0
fi

echo "codemap_installed=$installed"
echo "codemap_version=$version"
echo "codemap_preference=$preference"
echo "platform=$platform"

if [[ "$installed" == "false" ]]; then
    case "$platform" in
        darwin|linux)
            echo "install_hint=brew tap JordanCoin/tap && brew install codemap"
            ;;
        windows)
            echo "install_hint=scoop bucket add codemap https://github.com/JordanCoin/scoop-codemap && scoop install codemap"
            ;;
        *)
            echo "install_hint=See https://github.com/JordanCoin/codemap for installation options"
            ;;
    esac
fi
