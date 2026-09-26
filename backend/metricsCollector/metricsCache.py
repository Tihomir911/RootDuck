import json
import os

import redis

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))

CACHE_KEY = "metrics:recent"

MAX_SNAPSHOTS = 300

_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def push_snapshot(snapshot: dict) -> None:

    serialized = json.dumps(snapshot)

    _client.lpush(CACHE_KEY, serialized)

    _client.ltrim(CACHE_KEY, 0, MAX_SNAPSHOTS - 1)


def get_latest_snapshot() -> dict | None:
    
    raw = _client.lindex(CACHE_KEY, 0)  # элемент по индексу 0 — самый свежий
    if raw is None:
        return None
    return json.loads(raw)


def get_recent_snapshots(limit: int = MAX_SNAPSHOTS) -> list[dict]:
    
    raw_list = _client.lrange(CACHE_KEY, 0, limit - 1)
    return [json.loads(item) for item in raw_list]