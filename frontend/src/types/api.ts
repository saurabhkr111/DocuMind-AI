// Types mirror backend/app/schemas/*.py exactly. Do not add fields the backend
// does not return.

export type WorkflowStatus =
  | "PENDING"
  | "RUNNING"
  | "COMPLETED"
  | "AWAITING_APPROVAL"
  | "APPROVED"
  | "REJECTED"
  | "PARTIAL"
  | "FAILED";

export type ApprovalStatus = "PENDING" | "APPROVED" | "REJECTED";
export type AgentStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";
export type AgentName = "documentation" | "code_review" | "team_intelligence";
export type FindingSeverity = "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

/** GET /api/v1/workflows/  (WorkflowResponse) */
export interface WorkflowSummary {
  id: number;
  title: string;
  description: string | null;
  status: string; // backend declares a free string; known values are WorkflowStatus
}

/** DocumentResponse */
export interface DocumentItem {
  id: number;
  workflow_id: number;
  title: string;
  document_type: string;
  content: string;
  created_at: string;
  approval_status: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  approval_reason: string | null;
}

/** AgentLogResponse */
export interface AgentLog {
  id: number;
  agent_name: string;
  status: string;
  input_summary: string | null;
  /** JSON-encoded agent result (see persist_agent_results). */
  output_summary: string | null;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
}

/** GET /api/v1/workflows/{id}/details  (WorkflowDetailResponse) */
export interface WorkflowDetail extends WorkflowSummary {
  source_type: string | null;
  source_reference: string | null;
  created_at: string;
  updated_at: string;
  agent_logs: AgentLog[];
  documents: DocumentItem[];
}

/** AgentOutput as returned inside the PR-analysis response. */
export interface AgentOutput {
  agent_name: AgentName;
  status: AgentStatus;
  result: Record<string, unknown> | null;
  error: string | null;
  execution_time_ms: number | null;
}

/** POST .../pulls/{n}/analyze response (inline dict in routes/github.py) */
export interface PullRequestAnalysisResponse {
  message: string;
  repository: string;
  pull_request: Record<string, unknown>;
  workflow_id: number;
  workflow_status: string;
  agent_results: Record<string, AgentOutput>;
}

/** GET /health */
export interface HealthResponse {
  status: string;
  service: string;
  timestamp: string;
}

/** GET /api/v1/info */
export interface InfoResponse {
  project_name: string;
  version: string;
  agents: string[];
  orchestrator: string;
  switch_integration: string;
  backend: string;
}

/** Served by the dashboard proxy itself (server/proxy-core.mjs); contains no secrets. */
export interface ProxyStatus {
  backend_url: string;
  api_key_configured: boolean;
}

// ---- Shapes of parsed agent results (schemas/agent.py) ----
export interface AgentFinding {
  title: string;
  description: string;
  severity: FindingSeverity;
  category?: string | null;
  file_path?: string | null;
  line_number?: number | null;
  recommendation?: string | null;
}
export interface TeamActionItem {
  title: string;
  description?: string | null;
  owner?: string | null;
  priority?: "LOW" | "MEDIUM" | "HIGH";
}
