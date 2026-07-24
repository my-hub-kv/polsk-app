#!/usr/bin/env bash
set -euo pipefail

if ! python -c 'import sys; raise SystemExit(sys.version_info[:2] != (3, 12))'; then
  echo "Python 3.12 is required." >&2
  exit 1
fi

python -m pip install -r requirements.txt
export DJANGO_DEBUG=True
export DJANGO_SECRET_KEY=codex-local-only
export USE_SQLITE=True
python manage.py migrate --noinput
