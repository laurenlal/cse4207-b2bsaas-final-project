"""Small on-disk time-to-live (TTL) cache used to avoid repeat SerpApi calls during local development.

Why on disk instead of in memory: `uvicorn --reload` restarts the process every time a
file is saved, which would wipe an in-memory cache and cost a fresh API call.

Only the local FastAPI /products endpoint uses this. The Lambda ingestion function must
call SerpApi directly (see ingestion/serpapi_client.py) so every scheduled run records a
fresh observation.
"""

import hashlib
import json
import os
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_TTL_SECONDS = 2 * 60 * 60  # 2 hours
CACHE_DIR = Path(
    os.getenv("CACHE_DIR", Path(__file__).resolve().parents[1] / ".cache")
)

_locks = {}
_locks_guard = threading.Lock()


def _ttl_seconds():
    try:
        return int(os.getenv("CACHE_TTL_SECONDS", DEFAULT_TTL_SECONDS))
    except ValueError:
        return DEFAULT_TTL_SECONDS


def _key_lock(path):
    # One lock per cache key, so two simultaneous requests for the same query
    # (e.g. React StrictMode's double effect) trigger only one upstream call.
    with _locks_guard:
        return _locks.setdefault(path, threading.Lock())


def _path_for(namespace, key):
    normalized = " ".join(key.lower().split())
    digest = hashlib.sha256(f"{namespace}:{normalized}".encode()).hexdigest()[:32]
    return CACHE_DIR / f"{namespace}-{digest}.json"


def _read_fresh(path, ttl):
    try:
        entry = json.loads(path.read_text())
        age = time.time() - entry["fetchedAtEpoch"]
        if 0 <= age < ttl:
            return entry
    except (OSError, ValueError, KeyError):
        pass  # missing, unreadable, or corrupt -> treat as a miss
    return None


def _write(path, entry):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    # Write to a temp file then rename, so a crash never leaves a half-written entry.
    fd, tmp = tempfile.mkstemp(dir=CACHE_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(entry, f)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def get_or_fetch(namespace, key, fetch):
    """Return (value, meta). Calls fetch() only on a miss or when the entry is expired.

    meta = {"cached": bool, "fetchedAt": ISO-8601 UTC string}.
    Exceptions from fetch() propagate and nothing is cached, so failures are retried.
    """
    ttl = _ttl_seconds()
    path = _path_for(namespace, key)

    with _key_lock(path):
        entry = _read_fresh(path, ttl)
        cached = entry is not None

        if entry is None:
            now = time.time()
            entry = {
                "fetchedAtEpoch": now,
                "fetchedAt": datetime.fromtimestamp(now, timezone.utc).isoformat(),
                "value": fetch(),
            }
            _write(path, entry)

    return entry["value"], {"cached": cached, "fetchedAt": entry["fetchedAt"]}