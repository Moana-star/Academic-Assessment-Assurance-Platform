#!/bin/bash
set -eu

# Apply Django schema and data migrations to the configured database before serving.
# The demo-cleanup migration removes only recognisable seeded records and moves
# legacy biometric attendance into human review; production DATABASE_URL is
# intentionally unavailable to preview deployments.
python manage.py migrate --noinput

# If DATABASE_URL is configured, preserve records from the previous Vercel
# SQLite build cache before the application starts using managed PostgreSQL.
python manage.py import_legacy_sqlite

# Collect static assets for the Vercel deployment.
python manage.py collectstatic --noinput
