#!/usr/bin/env bash
set -euo pipefail

python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py collectstatic --noinput
git diff --check
