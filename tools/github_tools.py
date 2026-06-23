"""
tools/github_tools.py
─────────────────────
GitHub repository access via direct REST API calls.

Replaces the previous MCP stdio_client approach (which spawned a subprocess
via npx) with simple HTTPS requests to the GitHub Contents API. This is
compatible with sandboxed environments like Streamlit Cloud where subprocess
execution may be restricted.

API reference:
    GET https://api.github.com/repos/{owner}/{repo}/contents/{path}
    - Returns a list of file/dir objects for directories
    - Returns a single file object (with base64-encoded content) for files
"""

import os
import re
import base64

import requests
from google.adk.tools import FunctionTool


# ── Authentication helper ──────────────────────────────────────────────────────

def _get_headers() -> dict:
    """Build request headers, adding Authorization if GITHUB_TOKEN is set."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "RepoDoctor/1.0",
    }
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    return headers


# ── Secret redaction ───────────────────────────────────────────────────────────

def _scrub_secrets(content: str) -> str:
    """Redact common secret patterns before content reaches the LLM."""
    # GitHub Personal Access Tokens
    content = re.sub(r"(ghp_[0-9a-zA-Z]{36})", "[REDACTED_GITHUB_TOKEN]", content)
    content = re.sub(r"(github_pat_[0-9a-zA-Z_]{82})", "[REDACTED_GITHUB_PAT]", content)
    # Google / GCP API Keys
    content = re.sub(r"(AIza[0-9A-Za-z\-_]{35})", "[REDACTED_GOOGLE_API_KEY]", content)
    # Generic Bearer tokens / JWTs
    content = re.sub(r"(Bearer\s+[A-Za-z0-9\-\._~+\/]+=*)", "Bearer [REDACTED_TOKEN]", content)
    return content


# ── API functions ──────────────────────────────────────────────────────────────

async def list_repo_files(owner: str, repo: str, path: str = "") -> str:
    """Lists files in a GitHub repository directory via the GitHub REST API.

    Args:
        owner: The owner of the repository (e.g., 'octocat').
        repo:  The repository name (e.g., 'Hello-World').
        path:  Directory path to list. Use an empty string for the root.

    Returns:
        JSON string — a list of file/directory objects from the GitHub API.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    resp = requests.get(url, headers=_get_headers(), timeout=15)
    resp.raise_for_status()
    return resp.text  # Raw JSON array of file/dir objects


async def get_scrubbed_file_contents(owner: str, repo: str, path: str) -> str:
    """Gets a file's decoded text content from GitHub, with secrets redacted.

    Fetches the file via the GitHub REST API, decodes the base64 payload,
    then scrubs common secret patterns before returning the plain text.

    Args:
        owner: The owner of the repository (e.g., 'octocat').
        repo:  The repository name (e.g., 'Hello-World').
        path:  Path to the specific file (e.g., 'src/main.py').

    Returns:
        The plain-text content of the file with secrets redacted.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    resp = requests.get(url, headers=_get_headers(), timeout=15)
    resp.raise_for_status()
    data = resp.json()

    # Extract and decode file content
    content = ""
    if isinstance(data, dict) and "content" in data:
        raw = data["content"]
        if data.get("encoding") == "base64":
            try:
                # GitHub wraps lines at 60 chars with \n — strip before decoding
                decoded_bytes = base64.b64decode(raw)
                content = decoded_bytes.decode("utf-8", errors="ignore")
            except Exception:
                content = raw
        else:
            content = raw
    else:
        # Fallback: return raw response text
        content = resp.text

    return _scrub_secrets(content)


# ── FunctionTool wrappers (used by run_analysis.py via .func()) ───────────────
list_repo_files = FunctionTool(list_repo_files)
get_scrubbed_file_contents = FunctionTool(get_scrubbed_file_contents)
