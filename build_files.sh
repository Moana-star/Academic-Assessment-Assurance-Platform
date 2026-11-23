#!/bin/bash
set -eu

# Apply additive Django schema migrations to the configured production database
# before serving the deployment. This creates the incident/audit tables required
# by the Incident Cues workflow.
python manage.py migrate --noinput

# Collect static assets for the Vercel deployment.
python manage.py collectstatic --noinput
