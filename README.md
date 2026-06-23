# 🩺 Repo Doctor

An AI-powered multi-agent system built on the Google Agent Development Kit (ADK) that reviews public GitHub repositories for code quality and security vulnerabilities.

[![Python Version](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-1.0.0%2B-orange)](https://github.com/google/interactive-media-ads-python)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 🔍 What It Does

Repo Doctor leverages a **multi-agent architecture** powered by Gemini 2.5 Flash and Google ADK to analyze GitHub repositories. It coordinates specialized agents to analyze repository files, redact sensitive keys before processing, and generate a unified report.

### Multi-Agent Architecture
- **Coordinator Agent (`coordinator_agent`)**: The main orchestrator. It accepts a GitHub repository URL from the user, invokes the specialized sub-agents sequentially, and compiles their findings into a cohesive, structured Markdown report.
- **Code Quality Agent (`code_quality_agent`)**: Analyzes the repository layout, inspects main source files, and reviews code readability, structure, error handling, and bad coding patterns.
- **Security Agent (`security_agent`)**: Scans code and configuration files (such as dependency manifests) to identify security vulnerabilities, vulnerable dependency patterns, insecure practices, and hardcoded credentials.

### Secure, Read-Only Repository Fetching
- Both agents use the **GitHub MCP Server** via standard Model Context Protocol (MCP) tool calls (`list_repo_files` and `get_scrubbed_file_contents`) to interact with the repository.
- **Secret Redaction**: To protect developer privacy and security, a regex-based pre-processing scrubber runs on file contents inside `tools/github_tools.py`. Any detected GitHub tokens, Google API keys, GCP credentials, or generic bearer tokens are redacted **before** the code content is sent to Gemini.

---

## 🏗️ Architecture Flow

```
                      ┌──────────────┐
                      │     User     │
                      └──────┬───────┘
                             │
                             ▼
              ┌─────────────────────────────┐
              │  Streamlit UI / CLI Runner  │
              └──────────────┬──────────────┘
                             │ (GitHub URL)
                             ▼
              ┌─────────────────────────────┐
              │      coordinator_agent      │
              └──────┬───────────────┬──────┘
                     │               │
            ┌────────▼───────┐┌──────▼────────┐
            │  code_quality  ││   security    │
            │    _agent      ││    _agent     │
            └────────┬───────┘└──────┬────────┘
                     │               │
                     └───────┬───────┘
                             │ (MCP: list_repo_files, get_scrubbed_file_contents)
                             ▼
              ┌─────────────────────────────┐
              │      GitHub MCP Server      │
              └──────────────┬──────────────┘
                             │ (Scrubbed Code Content)
                             ▼
              ┌─────────────────────────────┐
              │      Gemini 2.5 Flash       │ (Fallback: 2.5-flash -> 2.0-flash -> 2.0-flash-lite)
              └─────────────────────────────┘
```

---

## 🚀 Key Features

- **Multi-Agent Orchestration**: Modular sub-agents coordinate to evaluate distinct aspects of codebase health using Google ADK.
- **GitHub MCP Server Integration**: Read-only repository interaction powered by Model Context Protocol stdio client.
- **Privacy-First Secret Redaction**: Eliminates keys and credentials from source code before they are processed by the LLM.
- **Robust Model Fallback Chain**: Automatically downgrades across model versions (`gemini-2.5-flash` → `gemini-2.0-flash` → `gemini-2.0-flash-lite`) if quota rate limits (HTTP 429) or connection issues occur.
- **Intelligent Local Caching**: Caches reports locally in `analysis_cache.json` keyed by the repository URL and its latest commit SHA for up to 1 hour, minimizing API consumption.
- **Interactive Streamlit Web UI**: Simple, sleek interface featuring a zero-setup **Sample Report Mode** that demonstrates results instantly without calling external APIs.

---

## 🗂️ Project Structure

```
Repo_doctor/
├── code_quality_agent/     # Code Quality Agent definition
│   ├── __init__.py
│   └── agent.py            # Agent rules, tools configuration, and instructions
├── coordinator_agent/      # Main orchestrator agent definitions
│   ├── __init__.py
│   └── agent.py            # Coordinates analysis, delegating to sub-agents
├── hello_agent/            # Smoke-test agent for initial installation verification
│   ├── __init__.py
│   └── agent.py
├── repo_reader_agent/      # Helper agent for general file-reading tasks
│   ├── __init__.py
│   └── agent.py
├── security_agent/         # Security vulnerability scanning agent
│   ├── __init__.py
│   └── agent.py            # Rules & tools to identify unsafe patterns & hardcoded keys
├── tools/                  # Shared helper libraries and MCP tools
│   ├── __init__.py
│   ├── cache.py            # Local JSON cache implementation (1-hour expiration)
│   ├── github_tools.py     # GitHub MCP tool wrappers & regex secret scrubber
│   └── model_config.py     # Gemini model fallback chain configuration
├── .antigravity-rules      # Project coding rules
├── app.py                  # Streamlit Web UI entry point
├── requirements.txt        # Python dependency manifest
└── run_analysis.py         # CLI entry point for headless repository analysis
```

---

## ⚙️ Environment Variables

Create a `.env` file in the root of the project with the following configuration:

```env
# Google Gemini API Key (Required for analysis)
# Get one from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=AIzaSy...

# GitHub Personal Access Token (Required for the GitHub MCP Server)
# Get one from: https://github.com/settings/tokens (no special scopes needed for public repos)
GITHUB_TOKEN=ghp_...
```

---

## ⚡ Quick Start

### 1. Clone & Set Up
```bash
# Clone the repository
git clone https://github.com/bindusmita49/repo-doctor.git
cd repo-doctor

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows CMD:
.venv\Scripts\activate.bat
# macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Add Credentials
Create your `.env` file in the project root:
```bash
# Windows (PowerShell)
New-Item -Path .env -ItemType File
# macOS/Linux/Git Bash
touch .env
```
Open `.env` in your editor and paste:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GITHUB_TOKEN=your_github_token_here
```

### 3. Launch App
Run the Streamlit app:
```bash
streamlit run app.py
```

---

## 🖥️ How To Run

### A. Web Application (Streamlit)
```bash
streamlit run app.py
```
- Open your browser to the URL displayed in the terminal (typically `http://localhost:8501`).
- Enter any public GitHub repository URL (e.g., `https://github.com/octocat/Hello-World`).
- Check **Use sample report (No API call)** to test the UI instantly without credentials, or uncheck it to run a live analysis against the real Gemini API.

### B. Command-Line Interface (CLI)
For automated checks, headlessly execute the script with:
```bash
python run_analysis.py <github_repo_url>
```
*Example:*
```bash
python run_analysis.py https://github.com/octocat/Hello-World
```

#### CLI Options
* `--no-cache`: Force a fresh analysis by bypassing the local `analysis_cache.json` file.
  ```bash
  python run_analysis.py https://github.com/octocat/Hello-World --no-cache
  ```

---

## 🛠️ Built With

* **[Google Agent Development Kit (ADK)](https://adk.dev/)** - Framework for building and running multi-agent workflows.
* **[Gemini 2.5 Flash](https://deepmind.google/technologies/gemini/)** - High-speed, long-context generative model for repo reasoning.
* **[GitHub MCP Server](https://github.com/modelcontextprotocol/servers)** - Model Context Protocol server exposing repository APIs.
* **[Streamlit](https://streamlit.io/)** - For the rapid development of the interactive web dashboard.
* **[Python 3.11+](https://www.python.org/)** - Base programming language.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
