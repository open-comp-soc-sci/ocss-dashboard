#!/usr/bin/env python3

import sys
import os
import json
import signal
import time
from datetime import datetime, timezone
from clickhouse_driver import Client
from yaspin import yaspin

# Ignore SIGHUP so the process is less likely to die if SSH disconnects.
signal.signal(signal.SIGHUP, signal.SIG_IGN)

# Hardcode an approximate total lines
HARDCODED_LINE_COUNT = 300_000_000

# Adjust these defaults as needed
CH_HOST = "127.0.0.1"
CH_PORT = 9000
CH_DATABASE = "default"
CH_USER = "default"
CH_PASSWORD = "heyheyhey"

# Our batch size for inserting rows
BATCH_SIZE = 300_000  # Insert rows in batches of 300k

def convert_unix_to_datetime64(unix_timestamp):
    """Converts Unix timestamp to a timezone-aware datetime object, truncated to millisecond precision."""
    if isinstance(unix_timestamp, (int, float)):
        if unix_timestamp > 9999999999:  # If timestamp is in milliseconds
            unix_timestamp = unix_timestamp / 1000
        dt = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
        # Truncate microseconds to millisecond precision (3 decimals)
        truncated_microseconds = (dt.microsecond // 1000) * 1000
        return dt.replace(microsecond=truncated_microseconds)
    return datetime(1970, 1, 1, tzinfo=timezone.utc)

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} /path/to/file.jsonl")
        sys.exit(1)

    file_path = sys.argv[1]
    if not os.path.isfile(file_path):
        print(f"Error: file not found: {file_path}")
        sys.exit(1)

    # Get the base name of the file (without extension), e.g., RC_2024-01
    file_basename = os.path.splitext(os.path.basename(file_path))[0]

    # We skip counting lines. Hardcode ~300M
    line_count = HARDCODED_LINE_COUNT
    print(f"Skipping line counting. Assuming ~{line_count:,} lines in {file_path}.")

    print(f"Connecting to ClickHouse at {CH_HOST}:{CH_PORT}...")
    client = Client(
        host=CH_HOST,
        port=CH_PORT,
        user=CH_USER,
        password=CH_PASSWORD,
        database=CH_DATABASE
    )

    # Create table if not exists, adding the file_name column.
    print("Creating table reddit_comments if it does not exist...")
    client.execute('''
        CREATE TABLE IF NOT EXISTS reddit_comments (
            id String CODEC(ZSTD(9)),
            author LowCardinality(String) CODEC(ZSTD(3)),
            subreddit LowCardinality(String) CODEC(ZSTD(3)),
            link_id LowCardinality(String) CODEC(ZSTD(3)),
            parent_id LowCardinality(String) CODEC(ZSTD(3)),
            body String CODEC(ZSTD(7)),
            created_utc DateTime64(3) CODEC(Delta, ZSTD(3)),
            score Int32 CODEC(ZSTD(1)),
            file_name LowCardinality(String) CODEC(ZSTD(3))
        )
        ENGINE = MergeTree()
        PARTITION BY toYYYYMM(toDateTime64(created_utc, 3))
        ORDER BY (subreddit, created_utc)
    ''')

    rows_buffer = []
    inserted_count = 0

    print(f"Reading {file_path}...")

    # Initialize last_print_time for log output (if not a TTY)
    last_print_time = time.time()

    # Use spinner only if stdout is a TTY
    use_spinner = sys.stdout.isatty()

    if use_spinner:
        spinner_ctx = yaspin(text=f"Processing lines: 0/{line_count:,}", color="cyan")
        spinner = spinner_ctx.__enter__()
    else:
        spinner = None

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            # Update progress output:
            if use_spinner:
                if line_num % 100_000 == 0:
                    spinner.text = f"Processing lines: {line_num:,}/{line_count:,}"
            else:
                # Only print a status update every 60 seconds if not a TTY
                if time.time() - last_print_time >= 60:
                    print(f"Processing lines: {line_num:,}/{line_count:,}")
                    last_print_time = time.time()

            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                if use_spinner:
                    spinner.write(f"Invalid JSON at line {line_num}: {e}")
                else:
                    print(f"Invalid JSON at line {line_num}: {e}")
                continue

            # Convert created_utc to proper DateTime64(3) format
            created_val = convert_unix_to_datetime64(record.get('created_utc', 0))

            # Safely convert None to '' for string columns
            def safe_str(val):
                return '' if val is None else str(val)

            id_val = safe_str(record.get('id'))
            author_val = safe_str(record.get('author'))
            subreddit_val = safe_str(record.get('subreddit'))
            link_id_val = safe_str(record.get('link_id'))
            parent_id_val = safe_str(record.get('parent_id'))
            body_val = safe_str(record.get('body'))

            score_val = record.get('score', 0)
            if isinstance(score_val, float):
                score_val = int(score_val)

            # Append row with file_basename added to the end
            rows_buffer.append([
                id_val,
                author_val,
                subreddit_val,
                link_id_val,
                parent_id_val,
                body_val,
                created_val,
                score_val,
                file_basename
            ])

            if len(rows_buffer) >= BATCH_SIZE:
                client.execute('''
                    INSERT INTO reddit_comments
                    (id, author, subreddit, link_id, parent_id, body, created_utc, score, file_name)
                    VALUES
                ''', rows_buffer)
                inserted_count += len(rows_buffer)
                rows_buffer.clear()

        # Insert any remaining rows
        if rows_buffer:
            client.execute('''
                INSERT INTO reddit_comments
                (id, author, subreddit, link_id, parent_id, body, created_utc, score, file_name)
                VALUES
            ''', rows_buffer)
            inserted_count += len(rows_buffer)
            rows_buffer.clear()

    if use_spinner:
        spinner.ok(f"\nDone! Inserted {inserted_count:,} rows from {file_path}.")
        spinner_ctx.__exit__(None, None, None)
    else:
        print(f"\nDone! Inserted {inserted_count:,} rows from {file_path}.")

if __name__ == "__main__":
    main()
