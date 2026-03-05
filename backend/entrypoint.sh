#!/bin/sh
set -e

# If a command is provided (docker-compose "command:"), run it as-is.
# This allows non-web services (e.g., progress_consumer) to use the same image.
if [ "$#" -gt 0 ]; then
  exec "$@"
fi

# Default behavior when no command is provided: start the Flask app.
echo "Waiting for database..."
until pg_isready -h db -p 5432 -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-postgres}"; do
  >&2 echo "Database is unavailable - sleeping"
  sleep 1
done
>&2 echo "Database is up - creating tables..."

python -u create_tables.py

echo "Starting Flask server..."
exec gunicorn --workers=4 --bind=0.0.0.0:5000 "app:create_app()"
