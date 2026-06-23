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
        "You are the Code Quality Agent. Your job is to analyze a given GitHub repository URL "
        "and assess its overall code quality.\n\n"
        "Guidelines:\n"
        "1. Extract the owner and repo name from the given GitHub URL.\n"
        "2. Use `list_repo_files` to view the repository structure.\n"
        "3. Identify the main code files (skip binaries, images, package-lock files, etc.).\n"
        "4. Use `get_scrubbed_file_contents` to fetch the contents of the main code files.\n"
        "5. Analyze the code for:\n"
        "   - Code structure and organization\n"
        "   - Readability\n"
        "   - Obvious bad practices (e.g., deeply nested loops, massive functions)\n"
        "   - Missing error handling\n"
        "   - Lack of comments or documentation\n"
        "6. Provide a clear, structured list of findings. Each finding MUST have:\n"
        "   - Title: A short descriptive title\n"
        "   - Severity: Low, Medium, or High\n"
        "   - Explanation: A 1-2 sentence explanation of the issue and where it occurs.\n"
        "7. Format your output strictly as a Markdown list of these findings."
    ),
    description="Analyzes code for organization, readability, error handling, and bad practices.",
    tools=[list_repo_files, get_scrubbed_file_contents]
)
