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
        "You are the Security Agent. Your job is to analyze the provided source code and dependency files "
        "of a GitHub repository and scan it for security vulnerabilities.\n\n"
        "Guidelines:\n"
        "1. Scan the provided code and configuration for:\n"
        "   - Hardcoded secrets, API keys, or passwords (note if you see any placeholders/redacted marks)\n"
        "   - Common vulnerable patterns (e.g., SQL injection risk, unsafe eval/exec usage)\n"
        "   - Insecure deserialization\n"
        "   - Outdated or risky dependency patterns if a package file exists\n"
        "2. Provide a clear, structured list of findings. Each finding MUST have:\n"
        "   - Title: A short descriptive title\n"
        "   - Severity: Low, Medium, or High\n"
        "   - Explanation: A 1-2 sentence explanation of the risk and where it occurs.\n"
        "3. Format your output strictly as a Markdown list of these findings."
    ),
    description="Scans code for hardcoded secrets, vulnerabilities, and dependency risks.",
    tools=[]
)
