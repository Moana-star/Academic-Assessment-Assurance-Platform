#!/bin/bash
set -eu

# Apply Django schema and data migrations to the configured database before serving.
# The demo-cleanup migration removes only recognisable seeded records and moves
# legacy biometric attendance into human review; production DATABASE_URL is
# intentionally unavailable to preview deployments.
python manage.py migrate --noinput

# Collect static assets for the Vercel deployment.
python manage.py collectstatic --noinput
