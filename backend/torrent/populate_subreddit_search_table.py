#!/usr/bin/env python3
from clickhouse_driver import Client
import os

# ── your ClickHouse connection settings ──
CH_HOST     = os.getenv("CH_HOST", "127.0.0.1")
CH_PORT     = os.getenv("CH_PORT", 9003)
CH_DATABASE = os.getenv("CH_DATABASE", "default")
CH_USER     = os.getenv("CH_USER", "default")
CH_PASSWORD = os.getenv("CH_PASSWORD", "heyheyhey")

# ── connect ──
client = Client(
    host=CH_HOST,
    port=CH_PORT,
    user=CH_USER,
    password=CH_PASSWORD,
    database=CH_DATABASE
)


# ── 1) create the target table if it doesn’t exist ──
client.execute("""
CREATE TABLE IF NOT EXISTS subreddits (
  subreddit String
) ENGINE = MergeTree()
PARTITION BY tuple()
ORDER BY subreddit
""")
print("Created table `subreddits` if it did not exist.")

# ── 2) wipe out any old data ──
client.execute("TRUNCATE TABLE subreddits")
print("Truncated table `subreddits`.")

# ── 3) insert all distinct subreddit names in one shot ──
client.execute("""
INSERT INTO subreddits (subreddit)
SELECT DISTINCT subreddit
FROM (
  SELECT subreddit FROM reddit_submissions
  UNION ALL
  SELECT subreddit FROM reddit_comments
)
""")
print("Inserted distinct subreddit names from reddit_submissions and reddit_comments.")

# ── done ──
print("Done: populated `subreddits` table.")