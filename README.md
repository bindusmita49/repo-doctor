# 🩺 Repo Doctor

> An AI agent system that reviews public GitHub repositories for **code quality**
> and **security issues**, built with [Google ADK](https://adk.dev/) and Gemini.

---

## ✨ What It Does

Repo Doctor is a multi-agent application.  You point it at any public GitHub
repository URL and it returns a structured review covering:

| Agent *(coming soon)* | What it checks |
|---|---|
| 🧹 **Code Quality Agent** | Naming conventions, code smells, complexity, dead code |
| 🔒 **Security Agent** | Hardcoded secrets, known vulnerable dependency patterns, unsafe practices |
| 📋 **Orchestrator** | Combines both reports into a single actionable summary |

The **hello_agent** in this scaffold is a smoke-test agent that confirms your
API key and installation are working before you build anything more complex.

---

## 🗂️ Project Structure

```
repo-doctor/
├── agents/
│   ├── __init__.py
│   └── hello_agent.py          ← smoke-test agent (start here!)
├── tools/
│   └── __init__.py             ← tool functions will live here
├── app.py                      ← main entry point / agent orchestrator
├── requirements.txt
├── .env.example                ← copy this to .env and add your keys
├── .gitignore
├── .antigravity-rules          ← project coding conventions for the AI assistant
└── README.md
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python **3.11+**  
- A [Gemini API key](https://aistudio.google.com/app/apikey) (free tier works)
- *(Optional)* A [GitHub Personal Access Token](https://github.com/settings/tokens)
  with `read:repo` scope — prevents API rate-limiting

### 2. Clone & Set Up

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/repo-doctor.git
cd repo-doctor

# Create and activate a virtual environment
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Your Environment

```bash
# Copy the example file
cp .env.example .env   # Windows: copy .env.example .env

# Open .env and fill in your keys:
#   GEMINI_API_KEY=AIza...
#   GITHUB_TOKEN=ghp_...   (optional but recommended)
```

### 4. Run the Smoke Test

#### Option A — ADK Developer Web UI *(recommended)*

```bash
adk web
```

Open **http://localhost:8000** in your browser, choose **hello_agent** from the
sidebar, and send any message.  You should get a friendly reply from Gemini.

#### Option B — Headless terminal run

```bash
adk run agents/hello_agent
```

ADK will prompt you for input.  Type anything and press Enter.
A successful response means your key is valid and everything is wired up.

---

## 🧑‍💻 Development Notes

- **Never commit `.env`** — it is listed in `.gitignore`.  Only `.env.example`
  belongs in version control.
- **Never execute fetched repo content** — all code pulled from GitHub is
  treated as plain text for analysis only.
- See [`.antigravity-rules`](.antigravity-rules) for the full coding conventions
  used in this project.

---

## 🛣️ Roadmap

- [x] Project scaffold & hello_agent smoke test
- [ ] `tools/github_tools.py` — fetch repo file trees & file contents
- [ ] `agents/code_quality_agent.py` — code quality reviewer
- [ ] `agents/security_agent.py` — security issue detector
- [ ] `agents/orchestrator.py` — combines both agents into a unified report
- [ ] Streamlit UI (`app_ui.py`) — a polished web interface

---

## 📄 License

MIT — do whatever you like, just don't blame me if your repos get roasted. 😄
