#!/bin/sh
set -e

host="$1"
shift

echo "Waiting for database at $host:5432..."
until pg_isready -h "$host" -p 5432 -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-postgres}"; do
  >&2 echo "Database is unavailable - sleeping"
  sleep 1
done

>&2 echo "Database is up - executing command"
exec "$@"
