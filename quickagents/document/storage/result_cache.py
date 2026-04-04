"""
Result cache - In-memory cache for intermediate analysis results.

Avoids re-parsing unchanged documents by caching results.
"""

from typing import Dict, Optional, Any
from hashlib import sha256
import time


class ResultCache:
    """In-memory cache for document/source analysis results."""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = max_size
        self._ttl = ttl_seconds

    def put(self, key: str, result: Any, file_hash: str = "") -> None:
        self._evict_if_needed()
        self._cache[key] = {
            "result": result,
            "hash": file_hash,
            "ts": time.time(),
        }

    def get(self, key: str, file_hash: str = "") -> Optional[Any]:
        entry = self._cache.get(key)
        if entry is None:
            return None
        if time.time() - entry["ts"] > self._ttl:
            del self._cache[key]
            return None
        if file_hash and entry["hash"] != file_hash:
            del self._cache[key]
            return None
        return entry["result"]

    def invalidate(self, key: str) -> None:
        self._cache.pop(key, None)

    def clear(self) -> None:
        self._cache.clear()

    def has(self, key: str) -> bool:
        return key in self._cache

    def size(self) -> int:
        return len(self._cache)

    def compute_hash(self, file_path: str) -> str:
        h = sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
        except (OSError, IOError):
            return ""
        return h.hexdigest()

    def _evict_if_needed(self) -> None:
        if len(self._cache) >= self._max_size:
            oldest_key = min(self._cache, key=lambda k: self._cache[k]["ts"])
            del self._cache[oldest_key]
