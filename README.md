# 🛡️ CodeSentinel AI — Autonomous AI Code Review Platform

**CodeSentinel AI** is an enterprise-grade, autonomous AI code review and security intelligence platform designed for development teams and individual engineers. It provides automated Pull Request reviews, inline security vulnerability scans, performance bottleneck detection, code smell flagging, and one-click patch generation.

---

## ✨ Features

- **🐙 GitHub Pull Request Reviewer**:
  - Paste any public GitHub PR link (or private PR with a GitHub Token).
  - Fetches PR unified diffs, metadata, commit changes, and line patches via the GitHub REST API.
  - Generates comprehensive PR review summaries ready to publish back to GitHub.

- **💻 Direct Code & Unified Diff Analyzer**:
  - Review arbitrary code snippets or patch diffs across Python, JavaScript/TypeScript, Java, Go, SQL, and more.
  - 1-click interactive demo scenarios for instant evaluation:
    - 🚨 *Auth Flaws & SQL Injection* (Python Flask)
    - ⚡ *Race Condition & Memory Leak* (Node.js Express)
    - 🔄 *Re-render Loop & XSS* (React)
    - 🛡️ *Clean LRU Cache* (Go)

- **🧠 Multi-Model AI Engine**:
  - **Local Heuristic & AST Engine**: Works 100% offline with zero API keys required, scanning for OWASP Top 10 vulnerabilities, credential leaks, and race conditions.
  - **Google Gemini API**: Native integration for Gemini 1.5 Flash, Gemini 2.0 Flash, and Gemini 1.5 Pro.
  - **OpenAI API**: Integration with GPT-4o and GPT-4o-mini.

- **📊 Comprehensive Code Health Score & Grade**:
  - Dynamic 0–100 Code Health Score with radial score meter.
  - Letter grade rating (`A+` to `F`) with clear verdict: `APPROVE`, `COMMENT`, or `REQUEST CHANGES`.
  - Severity breakdown (Critical, High, Medium, Low).

- **🔍 Interactive Line-by-Line Code Viewer**:
  - View full code and diffs with line numbering.
  - Vulnerable lines highlighted with expandable cards displaying issue title, impact, and one-click **"Copy Fix"** suggestion.

- **📋 Ready-to-Publish PR Review Markdown**:
  - Formats an executive summary and table of findings for GitHub pull request comments.
  - One-click copy or direct publish via GitHub API.

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.10+
- Modern web browser (Chrome, Edge, Firefox, Safari)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start CodeSentinel
```bash
python run.py
```
*The command will start the server and automatically open your default browser at `http://127.0.0.1:8000`.*

---

## ⚙️ Configuration & API Keys

Open the **Settings** modal in the top navigation bar to configure:
1. **AI Provider**: Choose between Built-in Smart Heuristic (offline), Google Gemini, or OpenAI.
2. **API Keys**: Pass your Gemini (`AIza...`) or OpenAI (`sk-...`) key directly or via environment variables (`GEMINI_API_KEY` or `OPENAI_API_KEY`).
3. **GitHub Token**: Optional Personal Access Token for reviewing private repositories or posting review comments directly to PRs.
4. **Strictness Level**: Relaxed, Standard, or Paranoid / Enterprise.

---

## 📁 Project Structure

```
Application/
├── backend/
│   ├── analyzer.py       # AI orchestration & scoring engine
│   ├── github_client.py  # GitHub REST API client & diff parser
│   ├── main.py           # FastAPI REST API & static file serving
│   ├── rules.py          # OWASP & heuristic AST security patterns
│   └── samples.py        # Pre-loaded interactive demo scenarios
├── frontend/
│   ├── app.js            # Frontend state, diff renderer, API calls
│   ├── index.html        # Modern dark-mode dashboard UI
│   └── style.css         # Styling, diff highlights, glowing badges
├── run.py                # Single-command launcher script
├── requirements.txt      # Python dependencies
└── README.md             # Documentation & guide
```

