#!/bin/sh
set -e

# Optionally, wait for the database to be ready:
echo "Waiting for database..."
until pg_isready -h db -p 5432; do
  >&2 echo "Database is unavailable - sleeping"
  sleep 1
done
>&2 echo "Database is up - creating tables..."

# Run the table creation script
python create_tables.py

echo "Starting Flask server..."
exec python -u -m flask run --host=0.0.0.0 --port=5000

