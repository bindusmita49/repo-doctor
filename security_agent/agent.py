"""
security_agent/agent.py
─────────────────────────
ADK Agent that scans code for security vulnerabilities and hardcoded secrets.

Agent details
─────────────
  Name   : security_agent
  Model  : gemini-2.5-flash
  Tools  : list_repo_files, get_scrubbed_file_contents
  Purpose: Fetches code files from a repo and outputs security findings.
"""

from google.adk.agents import Agent
from tools.github_tools import list_repo_files, get_scrubbed_file_contents
from tools.model_config import get_available_model

root_agent = Agent(
    name="security_agent",
    model=get_available_model(),
    instruction=(
        "You are the Security Agent. Your job is to analyze a given GitHub repository URL "
        "and scan it for security vulnerabilities.\n\n"
        "Guidelines:\n"
        "1. Extract the owner and repo name from the given GitHub URL.\n"
        "2. Use `list_repo_files` to view the repository structure.\n"
        "3. Identify the main code files and dependency files (e.g., requirements.txt, package.json).\n"
        "4. Use `get_scrubbed_file_contents` to fetch their contents. Note that obvious secrets "
        "   may have already been redacted by an internal tool step.\n"
        "5. Scan the code and configuration for:\n"
        "   - Hardcoded secrets, API keys, or passwords (even if redacted, note their presence)\n"
        "   - Common vulnerable patterns (e.g., SQL injection risk, unsafe eval/exec usage)\n"
        "   - Insecure deserialization\n"
        "   - Outdated or risky dependency patterns if a package file exists\n"
        "6. Provide a clear, structured list of findings. Each finding MUST have:\n"
        "   - Title: A short descriptive title\n"
        "   - Severity: Low, Medium, or High\n"
        "   - Explanation: A 1-2 sentence explanation of the risk and where it occurs.\n"
        "7. Format your output strictly as a Markdown list of these findings."
    ),
    description="Scans code for hardcoded secrets, vulnerabilities, and dependency risks.",
    tools=[list_repo_files, get_scrubbed_file_contents]
)
