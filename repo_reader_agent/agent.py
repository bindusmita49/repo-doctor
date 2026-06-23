"""
repo_reader_agent/agent.py
─────────────────────────
ADK Agent that connects to the GitHub MCP Server to read file structures
and fetch contents from public repositories.

Agent details
─────────────
  Name   : repo_reader_agent
  Model  : gemini-2.5-flash
  Tools  : McpToolset (GitHub MCP Server) - limited strictly to read-only operations
  Purpose: Given a GitHub repository URL, list files and retrieve file content.
"""

import os
import sys
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

# ── Load environment variables ────────────────────────────────────────────────
load_dotenv()

github_token = os.getenv("GITHUB_TOKEN")
if not github_token:
    raise EnvironmentError(
        "\n\n❌  GITHUB_TOKEN is not set in your .env file.\n"
        "    Please ensure your .env has: GITHUB_TOKEN=github_pat_...\n"
    )

# ── GitHub MCP Server Configuration ──────────────────────────────────────────
# On Windows, 'npx.cmd' is required when spawning a process under subprocess.
server_params = StdioServerParameters(
    command="npx.cmd",
    args=["-y", "@modelcontextprotocol/server-github"],
    env={
        **os.environ,
        "GITHUB_PERSONAL_ACCESS_TOKEN": github_token,
    }
)

connection_params = StdioConnectionParams(
    server_params=server_params,
    timeout=15.0
)

# Initialize the Toolset with strict read-only filter to prevent any writes/mutations.
github_toolset = McpToolset(
    connection_params=connection_params,
    tool_filter=["get_file_contents"]
)

# ── Agent Definition ──────────────────────────────────────────────────────────
root_agent = Agent(
    name="repo_reader_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are the Repo Reader Agent. Your primary job is to inspect a given GitHub repository "
        "URL, list its files, and retrieve the contents of a few files (like the README.md and "
        "another code file).\n\n"
        "To do this, you have access to the `get_file_contents` tool from the GitHub MCP server.\n\n"
        "Guidelines:\n"
        "1. Identify the repository owner and name from the repository URL. For example, from "
        "   'https://github.com/octocat/Hello-World', owner is 'octocat' and repo is 'Hello-World'.\n"
        "2. To list files in the root of the repository, call `get_file_contents` with the owner, "
        "   repo, and path set to '' (empty string) or '.' (dot).\n"
        "3. Once you receive the list of files, select the README.md (or similar) and another source "
        "   code file, and fetch their contents by calling `get_file_contents` again with the specific file path.\n"
        "4. Summarize your findings, list the files in the repository root, and display the contents of the files you retrieved.\n"
        "5. Under no circumstances should you try to create, update, or delete files."
    ),
    description="Reads file listings and file contents from a public GitHub repository using MCP.",
    tools=[github_toolset]
)
