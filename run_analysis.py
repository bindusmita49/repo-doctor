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
import json
import base64
import os
from dotenv import load_dotenv

# Load .env before importing agents (agents check env vars at import time)
load_dotenv()

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from coordinator_agent.agent import root_agent
from code_quality_agent.agent import root_agent as code_quality_agent
from security_agent.agent import root_agent as security_agent
from tools.github_tools import list_repo_files, get_scrubbed_file_contents
from tools.model_config import get_available_model, fallback_to_next_model
from tools.cache import build_cache_key, get_cached_result, set_cached_result, get_cache_info, _parse_owner_repo

APP_NAME    = "repo_doctor"
USER_ID     = "cli_user"
MAX_RETRIES = 3  # Maximum retries on 429 rate-limit errors


# ── Programmatic GitHub content fetching (0 Gemini calls) ──────────────────────

async def fetch_repo_code_contents(repo_url: str) -> str:
    parsed = _parse_owner_repo(repo_url)
    if not parsed:
        raise ValueError(f"Invalid GitHub URL: {repo_url}")
    owner, repo = parsed
    
    print(f"Fetching file list for {owner}/{repo}...")
    files_str = await list_repo_files.func(owner, repo, "")
    try:
        files = json.loads(files_str)
    except Exception as e:
        print("Failed to parse file list JSON:", e)
        return f"Error listing repository files: {files_str}"
        
    allowed_extensions = {'.py', '.js', '.ts', '.go', '.java', '.cpp', '.c', '.rs', '.rb', '.php', '.cs', '.html', '.css'}
    allowed_names = {'requirements.txt', 'package.json', 'Cargo.toml', 'go.mod', 'pom.xml', 'build.gradle', 'README.md', 'README'}
    
    file_paths = []
    subdirs = []
    
    for f in files:
        if not isinstance(f, dict):
            continue
        ftype = f.get("type")
        path = f.get("path", "")
        name = f.get("name", "")
        
        if ftype == "file":
            ext = os.path.splitext(name)[1].lower()
            if ext in allowed_extensions or name in allowed_names:
                file_paths.append(path)
        elif ftype == "dir" and name in {"src", "app", "lib", "tools", "agents"}:
            subdirs.append(path)
            
    # If we have less than 4 code files, let's scan one level down in main directories
    if len(file_paths) < 4 and subdirs:
        for subdir in subdirs[:2]:
            print(f"Scanning subdirectory: {subdir}...")
            try:
                sub_files_str = await list_repo_files.func(owner, repo, subdir)
                sub_files = json.loads(sub_files_str)
                for f in sub_files:
                    if isinstance(f, dict) and f.get("type") == "file":
                        path = f.get("path", "")
                        name = f.get("name", "")
                        ext = os.path.splitext(name)[1].lower()
                        if ext in allowed_extensions or name in allowed_names:
                            file_paths.append(path)
            except Exception as e:
                print(f"Failed to scan {subdir}: {e}")
                
    selected_paths = file_paths[:8]
    print(f"Selected {len(selected_paths)} files for analysis: {selected_paths}")
    
    combined_content = []
    for path in selected_paths:
        print(f"Fetching content of: {path}...")
        try:
            content = await get_scrubbed_file_contents.func(owner, repo, path)
            # Try to parse the content JSON to extract the clean file text
            try:
                data = json.loads(content)
                if isinstance(data, dict) and "content" in data:
                    raw_content = data["content"]
                    if data.get("encoding") == "base64":
                        try:
                            if "\n" not in raw_content:
                                decoded_bytes = base64.b64decode(raw_content)
                                raw_content = decoded_bytes.decode("utf-8", errors="ignore")
                        except Exception:
                            pass
                    content = raw_content
            except Exception:
                pass
                
            combined_content.append(f"=== FILE: {path} ===\n{content}\n")
        except Exception as e:
            print(f"Failed to fetch content of {path}: {e}")
            combined_content.append(f"=== FILE: {path} ===\n[Error fetching content: {e}]\n")
            
    return "\n".join(combined_content)


# ── Run agent single-turn helper (Exactly 1 Gemini call) ──────────────────────

async def run_agent_single_turn(agent, user_prompt, session_service) -> str:
    session = await session_service.create_session(app_name=agent.name, user_id=USER_ID)
    runner = Runner(
        agent=agent,
        app_name=agent.name,
        session_service=session_service,
    )
    user_message = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=user_prompt)]
    )
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session.id,
        new_message=user_message,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                res = event.content.parts[0].text
                if not res or res.strip() == "":
                    raise RuntimeError("API returned empty response (likely rate limit/quota hit).")
                return res
            raise RuntimeError("API returned empty response.")
    raise RuntimeError(f"Agent {agent.name} failed to produce a response.")


# ── Rate-limit retry & execution flow (Exactly 3 Gemini calls total) ──────────

async def run_with_retry(repo_url: str) -> str:
    """Run the three agents sequentially, retrying automatically on rate-limit (429) errors."""
    session_service = InMemorySessionService()

    # Fetch repository contents programmatically (0 Gemini calls)
    try:
        repo_contents = await fetch_repo_code_contents(repo_url)
    except Exception as e:
        return f"[ERROR] Failed to fetch repository contents: {e}"

    prompt_cq = (
        f"Here is the source code for the GitHub repository {repo_url}:\n\n"
        f"{repo_contents}\n\n"
        f"Please analyze its code quality and output your findings."
    )
    prompt_sec = (
        f"Here is the source code for the GitHub repository {repo_url}:\n\n"
        f"{repo_contents}\n\n"
        f"Please scan it for security vulnerabilities and output your findings."
    )

    for attempt in range(1, MAX_RETRIES + 1):
        current_model = get_available_model()
        print(f"\n[Attempt {attempt}/{MAX_RETRIES}] Active model: {current_model}")
        
        try:
            # 1. Code Quality Agent run (1 call)
            print("Invoking Code Quality Agent...")
            report_cq = await run_agent_single_turn(code_quality_agent, prompt_cq, session_service)
            
            # 2. Security Agent run (1 call)
            print("Invoking Security Agent...")
            report_sec = await run_agent_single_turn(security_agent, prompt_sec, session_service)
            
            # 3. Coordinator Agent run to merge (1 merge call)
            print("Invoking Coordinator Agent to merge results...")
            prompt_coord = (
                f"Please compile the final report for repository {repo_url} using these findings:\n\n"
                f"--- CODE QUALITY FINDINGS ---\n{report_cq}\n\n"
                f"--- SECURITY FINDINGS ---\n{report_sec}"
            )
            report_final = await run_agent_single_turn(root_agent, prompt_coord, session_service)
            
            return report_final

        except BaseException as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err or "503" in err or "UNAVAILABLE" in err or "rate limit" in err or "quota" in err or "empty response" in err:
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
