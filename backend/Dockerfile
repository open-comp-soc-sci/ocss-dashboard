FROM python:3.9-slim-buster
WORKDIR /app

# Install dependencies and PostgreSQL client
COPY requirements.txt .
RUN apt-get update && apt-get install -y postgresql-client && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /var/lib/apt/lists/*

# Copy your application code, including entrypoint.sh and create_tables.py
COPY . .

# Expose the desired port
EXPOSE 5000

# Set the entrypoint to run the script
ENTRYPOINT ["./entrypoint.sh"]
