#!/usr/bin/env bash
# =============================================================================
# Atlas dev environment setup — Linux / BSD
#
#  Usage:  source scripts/setup_dev.sh   (from the project root)
# =============================================================================

if [ -z "${BASH_VERSION:-}" ] && [ -z "${ZSH_VERSION:-}" ]; then
    echo "ERROR: Run this script in bash or zsh: source scripts/setup_dev.sh"
    return 1 2>/dev/null || exit 1
fi

_is_sourced=0
if [[ -n "${BASH_VERSION:-}" ]]; then
    [[ "${BASH_SOURCE[0]}" != "${0}" ]] && _is_sourced=1
elif [[ -n "${ZSH_VERSION:-}" ]]; then
    [[ "${ZSH_EVAL_CONTEXT:-}" == *:file:* || \
       "${ZSH_EVAL_CONTEXT:-}" == *:file  ]] && _is_sourced=1
fi
if [[ "$_is_sourced" == "0" ]]; then
    echo "ERROR: This script must be sourced, not executed directly."
    echo "       Run: source scripts/setup_dev.sh"
    exit 1
fi

if [[ -n "${BASH_VERSION:-}" ]]; then
    _SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
elif [[ -n "${ZSH_VERSION:-}" ]]; then
    # shellcheck disable=SC2296
    _SCRIPT_DIR="$(cd "$(dirname "${(%):-%x}")" && pwd)"
else
    echo "ERROR: Cannot determine script directory." >&2
    return 1
fi
PROJECT_ROOT="$(cd "$_SCRIPT_DIR/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"

setup_venv() {
    if [ -f "$VENV_PATH/bin/activate" ]; then
        echo "Existing virtual environment found."
        return 0
    fi
    echo "Creating virtual environment..."
    python3 -m venv --system-site-packages "$VENV_PATH" || {
        echo "ERROR: Failed to create venv. Install python3-venv and retry."
        return 1 2>/dev/null || exit 1
    }
}

activate_venv() {
    echo "Activating virtual environment..."
    # shellcheck disable=SC1091
    source "$VENV_PATH/bin/activate"
}

setup_venv || { return 1 2>/dev/null || exit 1; }
activate_venv
python -m pip install --upgrade pip --quiet
python -m pip install -e "$PROJECT_ROOT[dev]" --quiet || true

echo "Dev environment ready: $VENV_PATH"
