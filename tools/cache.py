"""
tools/cache.py
──────────────
Local JSON cache for Repo Doctor analysis results.

How it works
────────────
1. Before calling Gemini, we fetch the target repo's latest commit SHA from
   the GitHub REST API (free, no Gemini quota consumed).
2. The cache KEY is sha256(repo_url + commit_sha) — so the cache is
   automatically invalidated the moment new code is pushed to the repo.
3. Each cache entry also stores a timestamp; entries older than CACHE_TTL_SECONDS
   (default 1 hour) are treated as expired and re-fetched fresh.
4. All entries are persisted to a local JSON file (CACHE_FILE).

Usage
─────
    from tools.cache import get_cached_result, set_cached_result, build_cache_key
    
    key = await build_cache_key(repo_url)   # None if GitHub API is unreachable
    hit = get_cached_result(key)            # None on miss/expiry
    if hit:
        return hit
    result = await run_agents(...)
    set_cached_result(key, repo_url, result)
"""

import hashlib
import json
import os
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

# ── Config ────────────────────────────────────────────────────────────────────
# Cache lives in the project root alongside .env
CACHE_FILE = Path(__file__).parent.parent / "analysis_cache.json"
CACHE_TTL_SECONDS = 3600  # 1 hour


# ── Internal helpers ──────────────────────────────────────────────────────────

def _load_cache() -> dict:
    """Read the cache file from disk. Returns an empty dict if missing/corrupt."""
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # Corrupt cache file — start fresh
        return {}


def _save_cache(cache: dict) -> None:
    """Persist the cache dict to disk as JSON."""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def _fetch_commit_sha(owner: str, repo: str, token: Optional[str] = None) -> Optional[str]:
    """
    Fetch the SHA of the latest commit on the default branch via the GitHub REST API.
    
    This is a lightweight call that costs no Gemini quota. Returns None if the
    request fails (e.g., network error, private repo without token, rate limit).
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/HEAD"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "RepoDoctor/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("sha")
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError):
        return None


def _parse_owner_repo(repo_url: str) -> Optional[tuple[str, str]]:
    """
    Extract (owner, repo) from a GitHub URL.
    Handles: https://github.com/owner/repo  and  github.com/owner/repo
    """
    # Strip trailing slash and .git
    url = repo_url.rstrip("/").removesuffix(".git")
    # Match path segments after github.com
    parts = url.split("github.com/", 1)
    if len(parts) != 2:
        return None
    segments = parts[1].strip("/").split("/")
    if len(segments) < 2:
        return None
    return segments[0], segments[1]


# ── Public API ────────────────────────────────────────────────────────────────

def build_cache_key(repo_url: str) -> Optional[str]:
    """
    Build a stable cache key for a given GitHub repo URL.

    The key is sha256(repo_url + ":" + latest_commit_sha).
    This means the cache is automatically invalidated whenever new code is
    pushed to the repo, without us having to fetch any file contents.

    Returns None if the commit SHA cannot be fetched (network error, etc.).
    In that case, caching is simply skipped for this run.
    """
    parsed = _parse_owner_repo(repo_url)
    if not parsed:
        return None

    owner, repo = parsed
    token = os.getenv("GITHUB_TOKEN")
    commit_sha = _fetch_commit_sha(owner, repo, token)
    if not commit_sha:
        return None

    raw = f"{repo_url}:{commit_sha}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_cached_result(key: Optional[str]) -> Optional[str]:
    """
    Look up a cache entry by key.

    Returns the cached analysis string if:
      - the key is not None
      - an entry exists for that key
      - the entry is less than CACHE_TTL_SECONDS old

    Returns None otherwise (cache miss, expired, or key is None).
    """
    if not key:
        return None

    cache = _load_cache()
    entry = cache.get(key)
    if not entry:
        return None

    age = time.time() - entry.get("timestamp", 0)
    if age >= CACHE_TTL_SECONDS:
        return None  # Entry exists but is stale

    return entry.get("result")


def set_cached_result(key: Optional[str], repo_url: str, result: str) -> None:
    """
    Store an analysis result in the cache.

    Does nothing if key is None (meaning we couldn't build one this run).
    Overwrites any existing entry for the same key.
    """
    if not key:
        return

    cache = _load_cache()
    cache[key] = {
        "repo_url": repo_url,           # human-readable label for debugging
        "timestamp": time.time(),        # Unix epoch seconds
        "result": result,
    }
    _save_cache(cache)


def get_cache_info(key: Optional[str]) -> Optional[dict]:
    """
    Return metadata about a cache entry (without the full result body).
    Used for printing cache status to the user.
    """
    if not key:
        return None

    cache = _load_cache()
    entry = cache.get(key)
    if not entry:
        return None

    age = time.time() - entry.get("timestamp", 0)
    return {
        "repo_url": entry.get("repo_url", "unknown"),
        "age_seconds": int(age),
        "is_fresh": age < CACHE_TTL_SECONDS,
        "expires_in_seconds": max(0, int(CACHE_TTL_SECONDS - age)),
    }
