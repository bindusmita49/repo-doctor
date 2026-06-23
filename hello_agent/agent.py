"""
hello_agent/agent.py
─────────────────────────────────────────────────────────────────────────────
Smoke-test agent for the Repo Doctor project.

Purpose
-------
This is a minimal ADK agent whose only job is to verify that:
  1. google-adk is installed correctly
  2. Your GEMINI_API_KEY is valid and reachable
  3. The agent can produce a response from Gemini end-to-end

Agent details
─────────────
  Name   : hello_agent
  Model  : gemini-2.5-flash  (project default)
  Tools  : none — intentionally simple for a smoke test
  Input  : any message you type
  Output : a friendly confirmation that setup is working

HOW TO RUN (from the project root: Repo_doctor/)
─────────────────────────────────────────────────
Option A — interactive web UI (recommended):
    adk web
    Then open http://localhost:8000, pick "hello_agent", send any message.

Option B — headless terminal session:
    adk run hello_agent
    Type any message at the prompt and press Enter.
    A Gemini reply = success ✅
─────────────────────────────────────────────────────────────────────────────
"""

import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from tools.model_config import get_available_model

# ── Load .env from the project root ───────────────────────────────────────────
# load_dotenv() walks up from CWD to find the nearest .env file, so this works
# whether you run `adk run` from the project root or a subdirectory.
load_dotenv()

# ── Guard: fail early with a clear message if the API key is missing ──────────
# Without this check ADK would raise a cryptic gRPC / authentication error.
if not os.getenv("GEMINI_API_KEY"):
    raise EnvironmentError(
        "\n\n❌  GEMINI_API_KEY is not set.\n"
        "    Steps to fix:\n"
        "      1. Copy .env.example → .env  (in the project root)\n"
        "      2. Open .env and paste your key:  GEMINI_API_KEY=AIza...\n"
        "    Get a free key at: https://aistudio.google.com/app/apikey\n"
    )

# ── Agent definition ───────────────────────────────────────────────────────────
# `Agent` is the core ADK primitive that wraps a Gemini model with a persona.
# ADK's CLI discovers agents by looking for a module-level `root_agent` variable.
root_agent = Agent(
    # Unique identifier used by the ADK runtime and shown in the web UI.
    name="hello_agent",

    # Gemini 2.5 Flash: fast, cost-effective, great for development.
    # Change to "gemini-2.5-pro" if you want richer reasoning.
    model=get_available_model(),

    # System instruction — defines the agent's persona and task.
    instruction=(
        "You are the Repo Doctor assistant — an AI that will eventually review "
        "GitHub repositories for code quality and security issues. "
        "Right now you are just a smoke-test: greet the user warmly, confirm "
        "that the Gemini API key is working, and let them know the Repo Doctor "
        "project scaffold is set up correctly. Keep your reply short and friendly."
    ),

    # Description shown in the ADK web UI agent selector dropdown.
    description=(
        "Smoke-test agent — confirms that google-adk and the Gemini API key "
        "are configured correctly. Run this first before building anything else."
    ),
)
