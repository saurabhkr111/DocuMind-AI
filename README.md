# DocuMind AI — Documentation and Team Intelligence

**An AI-powered multi-agent platform that transforms development updates into structured documentation, code-review insights, and actionable team summaries.**

## Overview

Software teams often struggle with outdated documentation, repetitive code reviews, and scattered development updates.

**DocuMind AI** addresses these challenges through three specialized AI agents working together in an orchestrated workflow.

## Key Features

- **Documentation Agent:** Generates structured technical documentation from repository metadata, commits, and changed files.
- **Code Review Agent:** Identifies potential code issues and provides recommendations.
- **Team Intelligence Agent:** Summarizes completed tasks, technical decisions, blockers, and action items.
- **Multi-Agent Orchestration:** Coordinates specialized agents and combines their results.
- **Human Approval:** Supports review and approval of generated documents.
- **Workflow Persistence:** Stores execution logs and generated documents using SQLite.

## Architecture

```text
       Team Request
            |
            v
      FastAPI Backend
            |
            v
    Agent Orchestrator
       /          \
      v            v
Documentation   Code Review
    Agent          Agent
       \          /
        v        v
     Team Intelligence
           Agent
             |
             v
     Generated Documents
             |
             v
       Human Approval
```

## Technology Stack

| Category | Technologies |
|---|---|
| Language | Python |
| Backend | FastAPI |
| Database | SQLite |
| API | REST, Authenticated Webhooks |
| Architecture | Multi-Agent Orchestration |
| Integration | Switch |

## Getting Started

**1. Clone the repository**

```bash
git clone https://github.com/saurabhkr111/DocuMind-AI.git
cd DocuMind-AI
```

**2. Create and activate a virtual environment**

```bash
py -3.11 -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

Create a `.env` file and configure the API authentication variables required by the backend. Never commit API keys or secrets.

**5. Start the backend**

```bash
python -m uvicorn backend.app.main:app --reload --port 8001
```

API documentation:

`http://127.0.0.1:8001/docs`

## Switch Integration

DocuMind AI was developed for the **Flip the Switch Hackathon**.

We used **Switch Console** to create and configure three corresponding specialized agents. The backend also provides an authenticated webhook:

`POST /api/v1/switch/webhook`

The local backend webhook and multi-agent orchestration were tested successfully. However, a complete end-to-end workflow triggered directly through Switch was not verified because of an execution-environment usage limitation during development.

## Future Improvements

- Complete end-to-end Switch integration.
- Connect team communication platforms.
- Integrate GitHub repositories and pull requests.
- Improve code analysis using repository diffs.
- Add advanced workflow monitoring and reporting.

## Built For & Credits

Built for **AgentSync — Flip the Switch Hackathon**.

Special thanks to **Switch and WeMakeDevs** for providing the platform and opportunity to explore AI-powered agent workflows.

## Author

**Saurabh Kumar Chaudhary**

GitHub: `@saurabhkr111`

---

*DocuMind AI — Turning development activity into actionable engineering knowledge.*




