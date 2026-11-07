<div align="center">



\# 🧠 DocuMind AI



\### Documentation and Team Intelligence, Powered by Multi-Agent AI



\*\*Turn development updates into technical documentation, code-review insights, and actionable team intelligence.\*\*



\[!\[Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python\&logoColor=white)](https://www.python.org/)

\[!\[FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi\&logoColor=white)](https://fastapi.tiangolo.com/)

\[!\[SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite\&logoColor=white)](https://www.sqlite.org/)

\[!\[Status](https://img.shields.io/badge/Status-Active%20Development-orange)]()



\[\*\*GitHub Repository\*\*](https://github.com/saurabhkr111/DocuMind-AI) · \[\*\*Report an Issue\*\*](https://github.com/saurabhkr111/DocuMind-AI/issues)



</div>



\---



\## 📌 Table of Contents



\- \[Overview](#-overview)

\- \[Problem Statement](#-problem-statement)

\- \[Key Features](#-key-features)

\- \[System Architecture](#-system-architecture)

\- \[Agent Workflow](#-agent-workflow)

\- \[Technology Stack](#-technology-stack)

\- \[Project Structure](#-project-structure)

\- \[Getting Started](#-getting-started)

\- \[Environment Configuration](#-environment-configuration)

\- \[API Documentation](#-api-documentation)

\- \[Screenshots](#-screenshots)

\- \[Security](#-security)

\- \[Current Limitations](#-current-limitations)

\- \[Future Enhancements](#-future-enhancements)

\- \[Contributing](#-contributing)

\- \[Author and Credits](#-author-and-credits)

\- \[License](#-license)



\---



\## 🚀 Overview



\*\*DocuMind AI\*\* is an AI-powered documentation and team intelligence platform designed to help software development teams transform development updates and repository metadata into structured, actionable knowledge.



The platform uses three specialized agents:



\- \*\*Documentation Agent:\*\* Generates structured technical documentation from supplied development context, changed-file metadata, commit messages, and available patches.

\- \*\*Code Review Agent:\*\* Examines supplied change metadata and patches for configured patterns and potential issues.

\- \*\*Team Intelligence Agent:\*\* Summarizes team progress, decisions, blockers, and pending action items.



A FastAPI backend orchestrates the agents, persists workflow results, and supports an authenticated webhook endpoint intended for integration with Switch.



The system also includes a human-approval workflow for generated documents.



\### Project Goals



\- Reduce repetitive documentation work.

\- Make development updates easier to understand.

\- Organize team decisions and action items.

\- Provide a structured multi-agent workflow.

\- Preserve generated outputs and execution logs.

\- Keep humans involved in approving generated documentation.



\---



\## ❗ Problem Statement



Software development teams frequently face several operational challenges:



1\. \*\*Documentation gaps:\*\* Technical documentation may become outdated as code changes.

2\. \*\*Fragmented team knowledge:\*\* Decisions and progress updates can be scattered across conversations and repositories.

3\. \*\*Repetitive reviews:\*\* Developers repeatedly inspect change metadata and look for common issues.

4\. \*\*Unclear ownership:\*\* Blockers and action items can be overlooked.

5\. \*\*Limited traceability:\*\* Teams need a consistent record of workflow execution and generated documents.



DocuMind AI addresses these challenges through a structured, multi-agent workflow that transforms supplied development context into documentation, review observations, and team summaries.



\---



\## ✨ Key Features



\### 📝 1. Automated Technical Documentation



The Documentation Agent generates Markdown documentation containing:



\- Repository and change summaries.

\- Commit history.

\- Changed-file information.

\- Preliminary impact observations.

\- Documentation gaps and analysis limitations.



The quality of the output depends on the input provided. When actual patches are unavailable, the agent cannot perform line-by-line change analysis.



\### 🔍 2. Code Review Assistance



The Code Review Agent evaluates supplied change information and applies configured checks to identify potential issues.



It provides:



\- Review summaries.

\- Potential findings.

\- Risk classifications.

\- Recommendations for further review.



\*\*Note:\*\* A result containing zero detected issues does not establish that code is defect-free. Manual review and appropriate testing remain necessary.



\### 🧠 3. Team Intelligence



The Team Intelligence Agent consolidates development updates into a structured team summary.



It can organize:



\- Completed work.

\- Technical decisions.

\- Blockers.

\- Pending action items.

\- Results returned by the other agents.



\### ⚙️ 4. Multi-Agent Orchestration



The backend coordinates three specialized agents.



The Documentation and Code Review agents run concurrently, after which Team Intelligence processes the results.



\### 🔐 5. Authenticated API



The backend supports API-key authentication using a Bearer token.



Protected endpoints require an appropriately configured API key.



\### 💾 6. Workflow Persistence



The application persists workflow information, agent execution logs, and generated documents using its database layer.



Database migrations are maintained through Alembic.



\### 👤 7. Human Approval Workflow



Generated documents can be reviewed and approved or rejected through the document-management API.



This keeps human review in the workflow rather than automatically treating every generated output as approved.



\### 🔗 8. Switch Webhook Endpoint



The backend exposes an authenticated webhook intended to receive tasks from Switch:



`POST /api/v1/switch/webhook`



The endpoint reuses the existing agent orchestration and persistence implementation.



The backend webhook has been tested locally. A successful local webhook test does not, by itself, establish that Switch Console has successfully triggered the endpoint.



\---



\## 🏗️ System Architecture



```mermaid

flowchart TD

&#x20;   U\[Developer or Team Update] --> API\[FastAPI Backend]



&#x20;   API --> AUTH\[API-Key Authentication]

&#x20;   AUTH --> ORCH\[Agent Orchestrator]



&#x20;   ORCH --> DOC\[Documentation Agent]

&#x20;   ORCH --> REVIEW\[Code Review Agent]



&#x20;   DOC --> TEAM\[Team Intelligence Agent]

&#x20;   REVIEW --> TEAM



&#x20;   DOC --> DB\[(Database)]

&#x20;   REVIEW --> DB

&#x20;   TEAM --> DB



&#x20;   DB --> LOGS\[Workflow and Agent Logs]

&#x20;   DB --> DOCUMENTS\[Generated Documents]



&#x20;   DOCUMENTS --> APPROVAL\[Human Approval]

&#x20;   APPROVAL --> OUTPUT\[Approved Documentation]

```



\### Architecture Components



| Component | Responsibility |

|---|---|

| FastAPI | HTTP API and request handling |

| Authentication layer | API-key validation |

| Agent orchestrator | Coordinates agent execution |

| Documentation Agent | Produces technical Markdown |

| Code Review Agent | Identifies potential issues |

| Team Intelligence Agent | Summarizes team progress and decisions |

| SQLAlchemy | Database access and persistence |

| SQLite | Local development database |

| Alembic | Database schema migrations |

| Document API | Document retrieval and approval operations |

| Switch webhook | Entry point for intended external workflow integration |

| Frontend | User interface for the application |



\---



\## 🔄 Agent Workflow



A typical execution follows these steps:



1\. \*\*Receive a task:\*\* The backend accepts a task and its associated context.

2\. \*\*Validate the request:\*\* Authentication and request-schema validation are performed.

3\. \*\*Execute documentation and review:\*\* The orchestrator runs the Documentation and Code Review agents concurrently.

4\. \*\*Analyze team intelligence:\*\* Team Intelligence combines the available results with the supplied team context.

5\. \*\*Persist results:\*\* The backend stores the workflow, agent logs, and generated document records.

6\. \*\*Return the response:\*\* The API returns structured results for the executed agents.

7\. \*\*Request human approval:\*\* Generated documents can remain pending until reviewed.



```text

Task Submission

&#x20;     |

&#x20;     v

Authentication and Validation

&#x20;     |

&#x20;     v

Agent Orchestrator

&#x20;     |

&#x20;     +----------------------+

&#x20;     |                      |

&#x20;     v                      v

Documentation Agent     Code Review Agent

&#x20;     |                      |

&#x20;     +-----------+----------+

&#x20;                 |

&#x20;                 v

&#x20;      Team Intelligence Agent

&#x20;                 |

&#x20;                 v

&#x20;      Persist Workflow Results

&#x20;                 |

&#x20;                 v

&#x20;        Generated Documents

&#x20;                 |

&#x20;                 v

&#x20;         Human Approval

```



\---



\## 🛠️ Technology Stack



| Technology | Purpose |

|---|---|

| Python | Backend development |

| FastAPI | REST API and webhook handling |

| Pydantic | Request and response validation |

| SQLAlchemy | Database models and persistence |

| SQLite | Local database |

| Alembic | Database migrations |

| Uvicorn | ASGI application server |

| Pytest | Automated testing |

| Git and GitHub | Version control and collaboration |

| Switch | Intended workflow integration |

| JavaScript and frontend tooling | Frontend application |



The exact frontend framework and installed package versions should be confirmed from the frontend configuration and dependency files.



\---



\## 📁 Project Structure



```text

DocuMind-AI/

│

├── backend/

│   ├── app/

│   │   ├── agents/

│   │   │   ├── base\_agent.py

│   │   │   └── documentation\_agent.py

│   │   ├── auth/

│   │   ├── database/

│   │   ├── models/

│   │   ├── orchestrator/

│   │   ├── routes/

│   │   │   ├── agents.py

│   │   │   ├── documents.py

│   │   │   ├── github.py

│   │   │   ├── switch.py

│   │   │   └── workflow.py

│   │   ├── schemas/

│   │   ├── services/

│   │   ├── tests/

│   │   └── main.py

│   └── tests/

│

├── frontend/

│

├── migrations/

│

├── scripts/

│

├── alembic.ini

├── requirements.txt

├── api\_schema.json

├── openapi.json

├── .gitignore

└── README.md

```



\*The tree highlights the main application areas. Individual files and directories may change as development progresses.\*



\---



\## 🚀 Getting Started



Follow these instructions to run the backend locally on Windows.



\### Prerequisites



Install:



\- Python 3.11 or a compatible supported version.

\- Git.

\- A terminal such as PowerShell.

\- A GitHub account if you want to clone the repository.



\### 1. Clone the Repository



```powershell

git clone https://github.com/saurabhkr111/DocuMind-AI.git

cd DocuMind-AI

```



\### 2. Create a Virtual Environment



```powershell

py -3.11 -m venv .venv

```



Activate it:



```powershell

.\\.venv\\Scripts\\Activate.ps1

```



If PowerShell blocks activation, you can use the virtual environment's Python executable directly in the following commands.



\### 3. Install Dependencies



```powershell

python -m pip install --upgrade pip

python -m pip install -r requirements.txt

```



\### 4. Configure Environment Variables



Create a local `.env` file in the project root.



Use the variable names expected by the application. See \[Environment Configuration](#-environment-configuration).



Never commit the actual `.env` file.



\### 5. Initialize the Database



The project includes Alembic configuration and migration files.



Review the database URL in the application's configuration, then apply migrations:



```powershell

alembic upgrade head

```



Use this command only after confirming that the configured database URL points to the intended local database.



\### 6. Start the Backend



From the project root:



```powershell

python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001

```



The local backend should be available at:



\- Base URL: `http://127.0.0.1:8001`

\- Interactive API documentation: `http://127.0.0.1:8001/docs`

\- OpenAPI schema: `http://127.0.0.1:8001/openapi.json`



The interactive documentation is available when the application's OpenAPI documentation is enabled.



\### 7. Verify the Backend



Open another PowerShell window:



```powershell

Invoke-RestMethod -Uri "http://127.0.0.1:8001/health"

```



If the health endpoint is configured as expected, it should return a successful response.



You can also open `http://127.0.0.1:8001/docs` in your browser to inspect the available endpoints.



\### 8. Run the Tests



Activate the virtual environment if necessary, then run:





```



Use the actual scripts defined in `frontend/package.json`.



\---



\## 🔐 Environment Configuration



These are example values and should be adjusted to match the application's configuration.



\### Important Security Practices



\- Never commit API keys, passwords, or production credentials.

\- Keep `.env` excluded through `.gitignore`.

\- Use strong, unique API keys.

\- Do not expose secret values in logs, screenshots, or API responses.

\- Use HTTPS and appropriate access controls for remotely accessible deployments.

\- Configure environment-specific settings separately for development and production.



\---



\## 📡 API Documentation



The FastAPI application exposes endpoints for agent execution, workflow management, GitHub-related operations, document management, and Switch integration.



\### Main Endpoints



| Method | Endpoint | Purpose |

|---|---|---|

| GET | `/health` | Health check, if enabled in the application |

| GET | `/api/v1/info` | Application information |

| POST | `/api/v1/agents/analyze` | Execute the multi-agent analysis workflow |

| POST | `/api/v1/switch/webhook` | Receive an authenticated Switch webhook request |

| GET | `/api/v1/workflows/` | Retrieve workflow records |

| GET | `/api/v1/workflows/{workflow\_id}/details` | Retrieve workflow details |

| GET | `/api/v1/docs` | Not applicable; FastAPI's standard documentation URL is `/docs` |



\*\*Important:\*\* Confirm the exact methods and paths in the current OpenAPI schema before relying on this table. Endpoint availability and response schemas may change during development.



\### Example: Execute the Switch Webhook



The following PowerShell example assumes that the backend is running locally and the API key has been configured.



```powershell

$apiKey = Read-Host "Enter your local DocuMind API key"



$headers = @{

&#x20;   Authorization = "Bearer $apiKey"

}



$body = @{

&#x20;   task = "Generate technical documentation for the latest backend changes."

&#x20;   source\_type = "team\_update"

&#x20;   source\_reference = "readme-example"

&#x20;   context = @{

&#x20;       repository = "DocuMind-AI"

&#x20;       team = "DocuMind AI"

&#x20;       completed\_items = @(

&#x20;           "Backend API implemented"

&#x20;           "Multi-agent orchestration implemented"

&#x20;       )

&#x20;       decisions = @(

&#x20;           "Use authenticated API communication"

&#x20;       )

&#x20;       blockers = @()

&#x20;       action\_items = @()

&#x20;       changed\_files = @(

&#x20;           "backend/app/main.py"

&#x20;           "backend/app/routes/switch.py"

&#x20;       )

&#x20;       commits = @(

&#x20;           @{

&#x20;               message = "Add authenticated Switch webhook"

&#x20;           }

&#x20;       )

&#x20;   }

} | ConvertTo-Json -Depth 8



$response = Invoke-RestMethod `

&#x20;   -Uri "http://127.0.0.1:8001/api/v1/switch/webhook" `

&#x20;   -Method POST `

&#x20;   -Headers $headers `

&#x20;   -Body $body `

&#x20;   -ContentType "application/json"



$response | ConvertTo-Json -Depth 10

```



A successful response should contain results for the agents that executed successfully. Inspect each agent's returned status rather than assuming that every request completes successfully.



\### Explore the API



With the backend running, open:



`http://127.0.0.1:8001/docs`



The interactive API documentation provides a convenient way to inspect request schemas and try available endpoints.



\---

```markdown

!\[DocuMind AI dashboard](screenshots/dashboard.png)



!\[Multi-agent execution results](screenshots/agent-results.png)



!\[Generated technical documentation](screenshots/generated-document.png)

```



\*\*Do not add placeholder images that look like real application screenshots.\*\* Capture the actual interface and use the corresponding filenames.



\---



\## 🔒 Security



Security is important because DocuMind AI accepts authenticated requests and persists application data.



Current security-related features include:



\- Bearer API-key authentication.

\- Request validation through Pydantic.

\- A dedicated authentication layer.

\- Local environment-variable configuration.

\- Human approval for generated documents.



Before production deployment, review:



\- Secret rotation and storage.

\- Rate limiting and abuse prevention.

\- Authorization for document approval.

\- Input-size limits and validation.

\- Database backups and recovery.

\- Audit logging.

\- HTTPS and deployment network exposure.



The presence of authentication does not automatically establish that the application is production-ready.



\---



\## ⚠️ Current Limitations



DocuMind AI is under active development.



Known limitations include:



\- Documentation quality depends on the supplied repository context and patch information.

\- Missing GitHub patches prevent line-level change analysis.

\- Pattern-based code review does not replace a complete security audit or comprehensive testing.

\- External Switch-to-backend execution still requires end-to-end verification in the actual Switch environment.

\- Frontend setup and deployment instructions should be validated against the current frontend configuration.

\- Production deployment, monitoring, and security hardening require additional work.



These limitations should be revisited as the project evolves.



\---



\## 🔮 Future Enhancements



\### Agent Intelligence

\- Add more specialized agents for testing, security, and release notes.

\- Improve repository-aware code analysis.

\- Incorporate actual diffs and pull-request context.

\- Add configurable review rules.



\### Integrations

\- Complete end-to-end Switch Console integration.

\- Improve GitHub repository and pull-request workflows.

\- Add team-chat integrations.

\- Support notifications for completed workflows.



\### Workflow Management

\- Add richer document approval and rejection experiences.

\- Provide workflow history and filtering.

\- Track agent execution time and failure reasons.

\- Improve retry handling and error reporting.



\### Frontend and User Experience

\- Build a polished workflow dashboard.

\- Display agent execution progress.

\- Add document previews and approval controls.

\- Improve usability and accessibility.



\### Reliability and Deployment

\- Expand unit, integration, and end-to-end tests.

\- Add continuous integration with GitHub Actions.

\- Add structured logging and monitoring.

\- Evaluate PostgreSQL for production deployments.

\- Document deployment and recovery procedures.



\---



\## 🤝 Contributing



Contributions, bug reports, and suggestions are welcome.



1\. Fork the repository.

2\. Create a feature branch.

3\. Make your changes.

4\. Run the relevant tests.

5\. Commit your work with a descriptive message.

6\. Open a pull request describing the changes.



Example:



```bash

git checkout -b feature/your-feature

git add .

git commit -m "feat: describe your change"

git push origin feature/your-feature

```



Then open a pull request against the repository's `master` branch.



\---



\## 👨‍💻 Author and Credits



\*\*Project:\*\* DocuMind AI — Documentation and Team Intelligence



\*\*Repository:\*\* \[saurabhkr111/DocuMind-AI](https://github.com/saurabhkr111/DocuMind-AI)



\*\*Author:\*\* \[Saurabh Kumar Chaudhary](https://github.com/saurabhkr111)



DocuMind AI is being developed as an exploration of multi-agent orchestration, automated documentation, code-review assistance, and team workflow intelligence.



Third-party libraries and frameworks are acknowledged through their respective project documentation and licenses.



Additional contributors and learning resources should be credited here when their contributions have been verified.



\---



\## 📄 License



No license has been specified in this README.



Before distributing the project as open source, choose an appropriate license and add its text in a `LICENSE` file. Until then, do not assume that others have permission to reuse or redistribute the source code.



\---



<div align="center">



\*\*Built to make development knowledge easier to create, understand, and maintain.\*\*



⭐ If you find this project useful, consider starring the repository.



\[View DocuMind AI on GitHub](https://github.com/saurabhkr111/DocuMind-AI)



</div>

