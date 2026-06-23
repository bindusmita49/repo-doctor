"""
coordinator_agent/agent.py
─────────────────────────
ADK Agent that orchestrates the code quality and security analysis.

Agent details
─────────────
  Name   : coordinator_agent
  Model  : gemini-2.5-flash
  Tools  : AgentTool(code_quality_agent), AgentTool(security_agent)
  Purpose: Takes a GitHub URL, delegates to sub-agents, and compiles a final report.

Note: Sub-agents must be wrapped in AgentTool before being passed to the parent's
tools list. Passing raw Agent instances raises a pydantic validation error.
"""

from google.adk.agents import Agent
from google.adk.tools import AgentTool
from code_quality_agent.agent import root_agent as code_quality_agent
from security_agent.agent import root_agent as security_agent
from tools.model_config import get_available_model

root_agent = Agent(
    name="coordinator_agent",
    model=get_available_model(),
    instruction=(
        "You are the Coordinator Agent for Repo Doctor. Your job is to take the provided code quality findings "
        "and security findings for a GitHub repository and compile them into a single, cohesive Markdown report.\n\n"
        "Guidelines:\n"
        "1. Combine the provided findings into a single Markdown report with two sections:\n"
        "   ## 🔍 Code Quality Findings\n"
        "   ## 🔐 Security Findings\n"
        "2. End the report with a brief overall summary and severity overview."
    ),
    description="Orchestrates code quality and security analysis by delegating to specialized sub-agents.",
    tools=[]
)
