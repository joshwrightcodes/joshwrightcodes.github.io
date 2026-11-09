#!/bin/bash
# Prepares a new Mac, then hands off to its private configuration.
#
#   curl -fsSL https://josh.wright.codes/mac-bootstrap.sh | bash
#   curl -fsSL https://josh.wright.codes/mac-bootstrap.sh | bash -s -- --profile work
#
# The script installs Homebrew and the GitHub CLI, signs in to GitHub, clones
# the private repository and runs its update command. It skips each step that
# is already done, so it is safe to run again.
set -euo pipefail

REPO="joshwrightcodes/mac-config"
DEST="$HOME/ghq/github.com/$REPO"
BREW="/opt/homebrew/bin/brew"
# A reviewed commit of the official installer.
BREW_INSTALLER="https://raw.githubusercontent.com/Homebrew/install/7986efac25016e41eed7e471666140c06f9d97cf/install.sh"

say() {
	printf '==> %s\n' "$*"
}

main() {
	if [ "$(uname -s)-$(uname -m)" != "Darwin-arm64" ]; then
		say "This script supports Apple Silicon Macs only."
		exit 1
	fi

	if [ ! -x "$BREW" ]; then
		say "Installing Homebrew"
		/bin/bash -c "$(curl -fsSL "$BREW_INSTALLER")"
	fi
	eval "$("$BREW" shellenv)"

	if ! command -v gh >/dev/null 2>&1; then
		say "Installing the GitHub CLI"
		HOMEBREW_NO_AUTO_UPDATE=1 "$BREW" install gh
	fi

	if ! gh auth status --hostname github.com >/dev/null 2>&1; then
		say "Signing in to GitHub"
		gh auth login --hostname github.com --web --git-protocol https
	fi
	gh auth setup-git --hostname github.com

	if [ ! -d "$DEST/.git" ]; then
		say "Cloning $REPO"
		mkdir -p "$(dirname "$DEST")"
		gh repo clone "$REPO" "$DEST"
	fi

	say "Starting the private setup"
	exec "$DEST/setup" update "$@"
}

# With curl | bash, stdin is the script, so prompts must read the terminal.
if (: </dev/tty) 2>/dev/null; then
	main "$@" </dev/tty
else
	say "This script needs a terminal for its prompts."
	exit 1
fi
