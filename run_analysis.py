"""
run_analysis.py
───────────────
CLI entry point for Repo Doctor.

Usage:
    python run_analysis.py <github_repo_url> [--no-cache]

Flags:
    --no-cache    Skip the local cache and force a fresh Gemini API call.
                  Useful when you want up-to-date results regardless of cache state.

This script runs the coordinator_agent programmatically using ADK's Runner API.
It caches results locally (analysis_cache.json, keyed by repo URL + latest commit
SHA) for up to 1 hour to avoid burning free-tier Gemini API quota during development.
It also handles Gemini free-tier rate-limit (429) errors with automatic retries.
"""

import asyncio
import re
import sys
from dotenv import load_dotenv

# Load .env before importing agents (agents check env vars at import time)
load_dotenv()

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from coordinator_agent.agent import root_agent
from tools.model_config import get_available_model, fallback_to_next_model
from tools.cache import build_cache_key, get_cached_result, set_cached_result, get_cache_info

APP_NAME    = "repo_doctor"
USER_ID     = "cli_user"
MAX_RETRIES = 3  # Maximum retries on 429 rate-limit errors


# ── Rate-limit retry helpers ──────────────────────────────────────────────────

def _parse_retry_delay(error_msg: str, default: float = 20.0) -> float:
    """Extract the retry delay (in seconds) from a 429 error message string."""
    match = re.search(r"retryDelay.*?(\d+)s", error_msg)
    if match:
        return float(match.group(1)) + 2.0  # add 2s buffer
    return default


async def run_with_retry(repo_url: str) -> str:
    """Run the coordinator agent, retrying automatically on rate-limit (429) errors."""
    session_service = InMemorySessionService()

    user_message = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=f"Please analyze this GitHub repository: {repo_url}")]
    )

    for attempt in range(1, MAX_RETRIES + 1):
        current_model = get_available_model()
        print(f"\n[Attempt {attempt}/{MAX_RETRIES}] Active model: {current_model}")
        
        # Create a fresh session for each attempt so state doesn't bleed across retries
        session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID)

        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service,
        )

        try:
            async for event in runner.run_async(
                user_id=USER_ID,
                session_id=session.id,
                new_message=user_message,
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        return event.content.parts[0].text
                    
                    # ADK swallows the 429 ResourceExhausted exception and yields an empty response.
                    # We treat this as a rate-limit/internal error and retry.
                    if attempt < MAX_RETRIES:
                        delay = 10.0
                        print(f"\n[Warning] Agent returned empty response (likely 429 quota hit).")
                        new_model = fallback_to_next_model()
                        print(f"Switched model from {current_model} to {new_model} due to likely rate limit.")
                        print(f"Waiting {delay}s before retry...")
                        await asyncio.sleep(delay)
                        break  # Break out of the event loop to retry
                    else:
                        return (
                            f"[ERROR] Agent failed to produce a response after {MAX_RETRIES} attempts.\n"
                            "This is likely due to the Gemini API free-tier quota being exhausted (5 requests/minute)."
                        )

        except BaseException as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err or "503" in err or "UNAVAILABLE" in err:
                delay = 10.0
                if attempt < MAX_RETRIES:
                    new_model = fallback_to_next_model()
                    print(f"\n[Rate limit hit / Congestion] Error: {err}")
                    print(f"Switched model from {current_model} to {new_model}.")
                    print(f"Waiting {delay}s before retry (attempt {attempt}/{MAX_RETRIES})...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    return (
                        f"[ERROR] Rate limit hit after {MAX_RETRIES} attempts.\n"
                        "Please wait a minute and try again, or upgrade your Gemini API plan.\n"
                        f"Details: {err}"
                    )
            raise  # re-raise any non-rate-limit error

    return "(No response received after retries.)"


# ── Main entry point ──────────────────────────────────────────────────────────

async def main():
    print("[Repo Doctor] Analysis Runner")
    print("-" * 34)

    # ── Parse arguments ─────────────────────────────────────────────────────
    args = sys.argv[1:]
    no_cache = "--no-cache" in args
    positional = [a for a in args if not a.startswith("--")]

    if not positional:
        print("Usage: python run_analysis.py <github_repo_url> [--no-cache]")
        print("Example: python run_analysis.py https://github.com/octocat/Hello-World")
        print("         python run_analysis.py https://github.com/octocat/Hello-World --no-cache")
        sys.exit(1)

    repo_url = positional[0]
    print(f"\nAnalyzing: {repo_url}")

    # ── Cache lookup ─────────────────────────────────────────────────────────
    cache_key = None
    if no_cache:
        print("[Cache] Skipped (--no-cache flag set)\n")
    else:
        print("[Cache] Checking for a recent cached result...")
        # build_cache_key fetches the latest commit SHA from GitHub REST API —
        # no Gemini quota is consumed here.
        cache_key = build_cache_key(repo_url)

        if cache_key is None:
            print("[Cache] Could not reach GitHub to build cache key — running fresh.\n")
        else:
            cached = get_cached_result(cache_key)
            if cached:
                info = get_cache_info(cache_key)
                mins = info["age_seconds"] // 60
                secs = info["age_seconds"] % 60
                expires = info["expires_in_seconds"] // 60
                print(f"[Cache] HIT  (cached {mins}m {secs}s ago, expires in ~{expires}m)")
                print(f"         Serving from cache. Use --no-cache to force a fresh run.\n")
                print("\n[DONE] Analysis Complete! (from cache)\n")
                print(cached)
                return
            else:
                print("[Cache] MISS — no valid cached result found. Running fresh analysis.\n")

    # ── Fresh analysis ────────────────────────────────────────────────────────
    print("Please wait -- the coordinator is delegating to the Code Quality and Security agents...\n")
    result = await run_with_retry(repo_url)

    # ── Store in cache (only if the run succeeded and produced real content) ──
    if cache_key and not result.startswith("[ERROR]"):
        set_cached_result(cache_key, repo_url, result)
        print("\n[Cache] Result saved to analysis_cache.json")

    print("\n[DONE] Analysis Complete!\n")
    print(result)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAnalysis cancelled.")
