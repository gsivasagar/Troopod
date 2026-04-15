"""
Cache Module
Simple in-memory cache with TTL for storing generated personalizations.
"""
import hashlib
import time
from typing import Optional

                                      
_cache: dict[str, dict] = {}
CACHE_TTL = 3600


def make_cache_key(image_bytes: bytes, url: str) -> str:
    """Generate a cache key from image hash + URL."""
    img_hash = hashlib.md5(image_bytes).hexdigest()
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return f"{img_hash}_{url_hash}"


def get_cached(key: str) -> Optional[dict]:
    """Get cached result if not expired."""
    if key in _cache:
        entry = _cache[key]
        if time.time() - entry["timestamp"] < CACHE_TTL:
            return entry["data"]
        else:
            del _cache[key]
    return None


def set_cache(key: str, data: dict):
    """Store result in cache."""
    _cache[key] = {
        "data": data,
        "timestamp": time.time()
    }
