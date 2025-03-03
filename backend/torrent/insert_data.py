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

# Hardcoded approximate total lines (for progress display)
HARDCODED_LINE_COUNT = 300_000_000

# Connection settings
CH_HOST = "127.0.0.1"
CH_PORT = 9003
CH_DATABASE = "default"
CH_USER = "default"
CH_PASSWORD = "heyheyhey"

# Batch size for inserts
BATCH_SIZE = 300_000  # Insert rows in batches of 300k

def convert_unix_to_datetime64(unix_timestamp):
    """Converts a Unix timestamp to a timezone-aware datetime object with millisecond precision."""
    if isinstance(unix_timestamp, (int, float)):
        if unix_timestamp > 9999999999:  # If timestamp is in milliseconds
            unix_timestamp = unix_timestamp / 1000
        dt = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
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
        
    # Use the file base name (without extension) for tagging inserted rows.
    file_basename = os.path.splitext(os.path.basename(file_path))[0]
    
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
    
    # Read the first non-empty line to determine the file type.
    file_type = None
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            # If "parent_id" exists, assume it's a comment.
            if record.get('parent_id') is not None:
                file_type = 'comment'
            # Otherwise, if "title" or "selftext" exists, assume it's a submission.
            elif record.get('title') is not None or record.get('selftext') is not None:
                file_type = 'submission'
            else:
                file_type = 'unknown'
            break

    if file_type is None or file_type == 'unknown':
        print("Could not determine file type. Exiting.")
        sys.exit(1)
    else:
        print(f"Determined file type as: {file_type}")

    # Create the appropriate table based on the file type.
    if file_type == 'comment':
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
    else:  # file_type == 'submission'
        print("Creating table reddit_submissions if it does not exist...")
        client.execute('''
            CREATE TABLE IF NOT EXISTS reddit_submissions (
                id String CODEC(ZSTD(9)),
                author LowCardinality(String) CODEC(ZSTD(3)),
                subreddit LowCardinality(String) CODEC(ZSTD(3)),
                title String CODEC(ZSTD(7)),
                selftext String CODEC(ZSTD(7)),
                created_utc DateTime64(3) CODEC(Delta, ZSTD(3)),
                score Int32 CODEC(ZSTD(1)),
                file_name LowCardinality(String) CODEC(ZSTD(3))
            )
            ENGINE = MergeTree()
            PARTITION BY toYYYYMM(toDateTime64(created_utc, 3))
            ORDER BY (subreddit, created_utc)
        ''')

    # Prepare a single buffer and counter.
    buffer = []
    inserted_count = 0

    print(f"Reading {file_path}...")
    last_print_time = time.time()
    use_spinner = sys.stdout.isatty()
    if use_spinner:
        spinner_ctx = yaspin(text=f"Processing lines: 0/{line_count:,}", color="cyan")
        spinner = spinner_ctx.__enter__()
    else:
        spinner = None

    # Reopen the file to process all lines.
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            if use_spinner and line_num % 100_000 == 0:
                spinner.text = f"Processing lines: {line_num:,}/{line_count:,}"
            elif not use_spinner and time.time() - last_print_time >= 60:
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

            created_val = convert_unix_to_datetime64(record.get('created_utc', 0))
            def safe_str(val):
                return '' if val is None else str(val)

            if file_type == 'comment':
                row = [
                    safe_str(record.get('id')),
                    safe_str(record.get('author')),
                    safe_str(record.get('subreddit')),
                    safe_str(record.get('link_id')),
                    safe_str(record.get('parent_id')),
                    safe_str(record.get('body')),
                    created_val,
                    int(record.get('score', 0)),
                    file_basename
                ]
            else:  # file_type == 'submission'
                row = [
                    safe_str(record.get('id')),
                    safe_str(record.get('author')),
                    safe_str(record.get('subreddit')),
                    safe_str(record.get('title')),
                    safe_str(record.get('selftext')),
                    created_val,
                    int(record.get('score', 0)),
                    file_basename
                ]

            buffer.append(row)
            if len(buffer) >= BATCH_SIZE:
                if file_type == 'comment':
                    client.execute('''
                        INSERT INTO reddit_comments
                        (id, author, subreddit, link_id, parent_id, body, created_utc, score, file_name)
                        VALUES
                    ''', buffer)
                else:
                    client.execute('''
                        INSERT INTO reddit_submissions
                        (id, author, subreddit, title, selftext, created_utc, score, file_name)
                        VALUES
                    ''', buffer)
                inserted_count += len(buffer)
                buffer.clear()

        # Insert any remaining rows.
        if buffer:
            if file_type == 'comment':
                client.execute('''
                    INSERT INTO reddit_comments
                    (id, author, subreddit, link_id, parent_id, body, created_utc, score, file_name)
                    VALUES
                ''', buffer)
            else:
                client.execute('''
                    INSERT INTO reddit_submissions
                    (id, author, subreddit, title, selftext, created_utc, score, file_name)
                    VALUES
                ''', buffer)
            inserted_count += len(buffer)
            buffer.clear()

    if use_spinner:
        spinner.ok(f"\nDone! Inserted {inserted_count:,} rows from {file_path} as {file_type}s.")
        spinner_ctx.__exit__(None, None, None)
    else:
        print(f"\nDone! Inserted {inserted_count:,} rows from {file_path} as {file_type}s.")

if __name__ == "__main__":
    main()
