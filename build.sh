#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
npm ci
npm run build:css

python manage.py collectstatic --noinput
python manage.py check --deploy
