"""
code_quality_agent/agent.py
─────────────────────────
ADK Agent that analyzes code for structure, readability, and bad practices.

Agent details
─────────────
  Name   : code_quality_agent
  Model  : gemini-2.5-flash
  Tools  : list_repo_files, get_scrubbed_file_contents
  Purpose: Fetches main code files from a repo and outputs code quality findings.
"""

from google.adk.agents import Agent
from tools.github_tools import list_repo_files, get_scrubbed_file_contents
from tools.model_config import get_available_model

root_agent = Agent(
    name="code_quality_agent",
    model=get_available_model(),
    instruction=(
        "You are the Code Quality Agent. Your job is to analyze the provided source code of a GitHub repository "
        "and assess its overall code quality.\n\n"
        "Guidelines:\n"
        "1. Analyze the provided file contents for:\n"
        "   - Code structure and organization\n"
        "   - Readability\n"
        "   - Obvious bad practices (e.g., deeply nested loops, massive functions)\n"
        "   - Missing error handling\n"
        "   - Lack of comments or documentation\n"
        "2. Provide a clear, structured list of findings. Each finding MUST have:\n"
        "   - Title: A short descriptive title\n"
        "   - Severity: Low, Medium, or High\n"
        "   - Explanation: A 1-2 sentence explanation of the issue and where it occurs.\n"
        "3. Format your output strictly as a Markdown list of these findings."
    ),
    description="Analyzes code for organization, readability, error handling, and bad practices.",
    tools=[]
)
