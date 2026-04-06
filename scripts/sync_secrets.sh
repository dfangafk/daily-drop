#!/usr/bin/env bash
# Sync local secrets and variables to GitHub Actions.
# Requires: gh CLI authenticated (gh auth login)
# Run from the repo root.

set -euo pipefail

# Keys from .env that should be GitHub Variables (not Secrets)
VARIABLES=(
    "PIPELINE__LOG_LEVEL"
    "NOTIFY__TIMEZONE"
    "NOTIFY__SMTP_HOST"
    "NOTIFY__SMTP_PORT"
    "NOTIFY__SMTP_SECURITY"
)

REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "Syncing to $REPO..."

is_variable() {
    local key="$1"
    for v in "${VARIABLES[@]}"; do
        [[ "$key" == "$v" ]] && return 0
    done
    return 1
}

# --- .env ---
if [[ -f .env ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ -z "$line" || "$line" == \#* ]] && continue
        key="${line%%=*}"
        value="${line#*=}"
        if is_variable "$key"; then
            gh variable set "$key" --body "$value"
            echo "  variable: $key"
        else
            gh secret set "$key" --body "$value"
            echo "  secret:   $key"
        fi
    done < .env
else
    echo "Warning: .env not found, skipping"
fi

# --- sources.yaml (variable) ---
if [[ -f sources.yaml ]]; then
    gh variable set SOURCES_YAML --body "$(cat sources.yaml)"
    echo "  variable: SOURCES_YAML"
else
    echo "Warning: sources.yaml not found, skipping"
fi

echo "Done."
