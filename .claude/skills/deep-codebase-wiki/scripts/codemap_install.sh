#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

METHOD="auto"
CONFIRMED="false"
DRY_RUN="false"

usage() {
    echo "Usage: $0 [--method auto|brew|scoop|go] [--yes] [--dry-run]"
    echo ""
    echo "This script installs codemap only after explicit confirmation."
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --method)
            [[ $# -ge 2 ]] || die "--method requires a value"
            METHOD="$2"
            shift 2
            ;;
        --yes)
            CONFIRMED="true"
            shift
            ;;
        --dry-run)
            DRY_RUN="true"
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

if command -v codemap >/dev/null 2>&1; then
    log_info "codemap is already installed."
    codemap --version 2>/dev/null || true
    exit 0
fi

platform="$(detect_platform)"
selected="$METHOD"

if [[ "$selected" == "auto" ]]; then
    case "$platform" in
        darwin|linux)
            if command -v brew >/dev/null 2>&1; then
                selected="brew"
            elif command -v go >/dev/null 2>&1; then
                selected="go"
            else
                die "No supported installer found. Install Homebrew or Go, or install codemap manually."
            fi
            ;;
        windows)
            if command -v scoop >/dev/null 2>&1; then
                selected="scoop"
            else
                die "Scoop is required on Windows for auto install. Install codemap manually."
            fi
            ;;
        *)
            die "Unsupported platform for auto install. Install codemap manually."
            ;;
    esac
fi

case "$selected" in
    brew)
        INSTALL_CMD="brew tap JordanCoin/tap && brew install codemap"
        ;;
    scoop)
        INSTALL_CMD="scoop bucket add codemap https://github.com/JordanCoin/scoop-codemap && scoop install codemap"
        ;;
    go)
        INSTALL_CMD="go install github.com/JordanCoin/codemap@latest"
        ;;
    *)
        die "Unsupported method '$selected'. Use auto|brew|scoop|go."
        ;;
esac

echo "Selected install method: $selected"
echo "Install command: $INSTALL_CMD"

if [[ "$DRY_RUN" == "true" ]]; then
    exit 0
fi

if [[ "$CONFIRMED" != "true" ]]; then
    die "Installation requires explicit confirmation. Re-run with --yes after user approval."
fi

log_info "Installing codemap..."
eval "$INSTALL_CMD"

if command -v codemap >/dev/null 2>&1; then
    log_info "codemap installation completed."
    codemap --version 2>/dev/null || true
    exit 0
fi

die "Installation command finished but codemap is still unavailable in PATH."
