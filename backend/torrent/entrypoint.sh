#!/bin/bash
set -e

echo "Starting ClickHouse in the background..."
clickhouse-server --daemon

# Wait a few seconds for ClickHouse to be ready
sleep 5

# (Optional) do any setup or ingestion here
# e.g. python /insert_data.py

# Keep the container running forever
# Option 1: Tail a file (like ClickHouse logs)
# tail -f /var/log/clickhouse-server/clickhouse-server.log

# Option 2: Sleep infinity (if your base image supports it)
sleep infinity
