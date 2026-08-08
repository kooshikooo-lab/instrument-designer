#!/usr/bin/env bash
# onboard_new_machine.sh — bring a fresh Linux machine onto the team.
#
# Usage (on the NEW machine, after it has internet):
#   bash scripts/onboard_new_machine.sh <machine-name>
# Example:
#   bash scripts/onboard_new_machine.sh scrappy
#
# What it does (each step is idempotent — safe to re-run):
#   1. Installs git/curl/python3 (+ `python` alias package)
#   2. Installs + starts Tailscale (prints a login link — sign in with the team GitHub account)
#   3. Installs GitHub CLI `gh` (needed by scripts/team_chat.py) and authenticates
#   4. Clones instrument-designer into ~/src and sets git identity + hooks (Law 15/16)
#   5. Runs system_audit.py + team_chat.py sync to prove the machine is compliant
#
# Tested on MX Linux (Debian base). Other apt distros should work.

set -euo pipefail

MACHINE="${1:-}"
if [ -z "$MACHINE" ]; then
    echo "usage: bash scripts/onboard_new_machine.sh <machine-name>" >&2
    exit 1
fi
echo "== Onboarding machine: $MACHINE =="

# --- 1. Base packages -------------------------------------------------------
echo "[1/5] base packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq git curl python3 python3-pip python3-venv python-is-python3

# --- 2. Tailscale -----------------------------------------------------------
echo "[2/5] tailscale..."
if ! command -v tailscale >/dev/null 2>&1; then
    curl -fsSL https://tailscale.com/install.sh | sh
fi
if ! tailscale status >/dev/null 2>&1; then
    echo ">>> Tailscale login: a link will appear below — open it in a browser and"
    echo ">>> sign in with the TEAM GitHub account (kooshikooo-lab)."
    sudo tailscale up
else
    echo "tailscale already up: $(tailscale ip -4 2>/dev/null || echo '?')"
fi

# --- 3. GitHub CLI ----------------------------------------------------------
echo "[3/5] github cli..."
if ! command -v gh >/dev/null 2>&1; then
    sudo mkdir -p -m 755 /etc/apt/keyrings
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/etc/apt/keyrings/githubcli-archive-keyring.gpg 2>/dev/null
    sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt-get update -qq
    sudo apt-get install -y -qq gh
fi
if ! gh auth status >/dev/null 2>&1; then
    echo ">>> GitHub login: follow the prompts (browser flow is easiest)."
    gh auth login
else
    echo "gh already authed: $(gh api user -q .login 2>/dev/null || echo '?')"
fi

# --- 4. Clone + identity + hooks ---------------------------------------------
echo "[4/5] repo + hooks..."
mkdir -p "$HOME/src"
cd "$HOME/src"
if [ ! -d instrument-designer ]; then
    git clone https://github.com/kooshikooo-lab/instrument-designer.git
fi
cd instrument-designer
git config user.name "Admin"
git config user.email "kooshikooo@gmail.com"
git config core.hooksPath scripts/git-hooks   # same as install_hooks.ps1, Linux edition
echo "machine name for team channel: export TEAM_MACHINE=$MACHINE"
grep -q "TEAM_MACHINE=$MACHINE" "$HOME/.bashrc" || echo "export TEAM_MACHINE=$MACHINE" >> "$HOME/.bashrc"

# --- 5. Compliance proof -----------------------------------------------------
echo "[5/5] compliance check..."
python3 scripts/system_audit.py && echo "AUDIT: PASS"
TEAM_MACHINE="$MACHINE" python3 scripts/team_chat.py sync || true

echo
echo "== Onboarding complete for '$MACHINE' =="
echo "Next: TEAM_MACHINE=$MACHINE python3 scripts/team_chat.py post \"scrappy online\""
