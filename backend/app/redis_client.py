import redis
import os
import time
import json

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB   = int(os.getenv("REDIS_DB", 0))

RESULT_TTL_SECONDS = 24 * 60 * 60  # 1 day for final results
PROGRESS_TTL_SECONDS = 24 * 60 * 60  # 1 day for progress updates

_redis_instance = None

def get_redis_connection(retries=20, delay=1):
    """
    Return a Redis connection. Lazy-loads the instance and retries if Redis is not ready.
    """
    global _redis_instance
    if _redis_instance is not None:
        return _redis_instance

    for i in range(retries):
        try:
            r = redis.Redis(
                host=REDIS_HOST, 
                port=REDIS_PORT, 
                db=REDIS_DB, 
                decode_responses=True
            )
            r.ping()  # Check connection
            print(f"[Redis] Connected on attempt {i+1}")
            _redis_instance = r
            return r
        except redis.ConnectionError:
            print(f"[Redis] Not ready, retrying in {delay}s...")
            time.sleep(delay)

    raise Exception("[Redis] Could not connect after retries")


# -----------------------------
# Result helpers
# -----------------------------
def set_result(job_id: str, result: dict):
    """
    Store the final job result in Redis with TTL.
    """
    r = get_redis_connection()
    r.set(f"result:{job_id}", json.dumps(result), ex=RESULT_TTL_SECONDS)


def get_result(job_id: str):
    """
    Retrieve the final job result from Redis.
    """
    r = get_redis_connection()
    data = r.get(f"result:{job_id}")
    if data is None:
        return None
    return json.loads(data)


# -----------------------------
# Progress helpers
# -----------------------------
def set_progress(job_id: str, progress: dict):
    """
    Store a job's progress update in Redis with TTL.
    """
    r = get_redis_connection()
    r.set(f"progress:{job_id}", json.dumps(progress), ex=PROGRESS_TTL_SECONDS)


def get_progress(job_id: str):
    """
    Retrieve a job's progress update from Redis.
    """
    r = get_redis_connection()
    data = r.get(f"progress:{job_id}")
    if data is None:
        return None
    return json.loads(data)