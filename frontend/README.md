# DocuMind AI – Dashboard

React + TypeScript + Vite + Tailwind. See `../docs/frontend-integration-report.md` for the backend inspection and architecture.

## Setup
```bash
cd frontend
npm install
cp .env.example .env.local      # then set DOCUMIND_PROXY_API_KEY (one of the backend's DOCU_MIND_API_KEYS)
```
`.env.local` is git-ignored. Never prefix the key with `VITE_`.

## Run (development)
Backend (from the repository root, so `backend.app.*` imports resolve; set DOCU_MIND_API_KEYS first):
```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8001
```
Frontend:
```bash
npm run dev          # http://localhost:5173
```

## Production-style
```bash
npm run build
npm start            # serves dist/ and proxies the API with the server-side key
```

## Notes
- Documents, agent runs and source/created fields are aggregated from `/workflows/` + `/workflows/{id}/details` because the backend has no list endpoints for them.
- Agent execution time is derived from `started_at`/`completed_at`.
