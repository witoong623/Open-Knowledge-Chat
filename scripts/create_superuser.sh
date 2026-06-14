#!/usr/bin/env bash
#
# Create a superuser account "admin" for local development.
#
# Usage:
#   ./scripts/create_superuser.sh
set -euo pipefail

# Resolve the project root (parent of this script's directory) and run from there.
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Load environment variables from .env if present.
if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    . ./.env
    set +a
fi

export PYTHONPATH="open_knowledge_chat${PYTHONPATH:+:$PYTHONPATH}"
export DJANGO_SETTINGS_MODULE="config.settings"

DJANGO_SUPERUSER_USERNAME="admin" \
DJANGO_SUPERUSER_PASSWORD="pass1234" \
DJANGO_SUPERUSER_EMAIL="admin@gmail.com" \
uv run manage.py createsuperuser --noinput
