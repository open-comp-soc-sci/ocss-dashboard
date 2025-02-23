# Dockerfile

FROM clickhouse/clickhouse-server:latest

# Copy our custom entrypoint script into the image
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Use our script as the container entrypoint
ENTRYPOINT ["/entrypoint.sh"]
