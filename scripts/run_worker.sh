#!/usr/bin/env bash
#
# Start the Celery worker that processes document ingestion tasks.
#
# Broker: uses the CELERY_BROKER_URL env var if set (e.g. a managed Redis in
# production), otherwise falls back to the local Redis defined in settings.py.
#
# Usage:
#   ./scripts/run_worker.sh                       # local Redis
#   CELERY_BROKER_URL=redis://host:6379/0 ./scripts/run_worker.sh   # custom broker
#   ./scripts/run_worker.sh --concurrency=4       # extra args are forwarded to celery
set -euo pipefail

# Resolve the project root (parent of this script's directory) and run from there.
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Load environment variables from .env if present (e.g. OPENAI_API_KEY, CELERY_BROKER_URL).
if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    . ./.env
    set +a
fi

export PYTHONPATH="open_knowledge_chat${PYTHONPATH:+:$PYTHONPATH}"
export DJANGO_SETTINGS_MODULE="config.settings"

exec uv run celery -A config worker --loglevel=info "$@"
