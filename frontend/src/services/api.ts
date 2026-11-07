import { http } from "./http";
import { toApiError } from "./errors";
import type {
  DocumentItem,
  HealthResponse,
  InfoResponse,
  ProxyStatus,
  PullRequestAnalysisResponse,
  WorkflowDetail,
  WorkflowSummary,
} from "@/types/api";

async function call<T>(promise: Promise<{ data: T }>): Promise<T> {
  try {
    return (await promise).data;
  } catch (error) {
    throw toApiError(error);
  }
}

// ---- Workflows ----
// Trailing slash matches the FastAPI route ("/api/v1/workflows/").
export const getWorkflows = () => call(http.get<WorkflowSummary[]>("/api/v1/workflows/"));

export const getWorkflowDetails = (id: number) =>
  call(http.get<WorkflowDetail>(`/api/v1/workflows/${id}/details`));

// ---- Documents ----
export const getDocument = (id: number) => call(http.get<DocumentItem>(`/api/v1/documents/${id}`));

/** reviewed_by is intentionally omitted: the backend ignores it and uses the authenticated principal. */
export const approveDocument = (id: number) =>
  call(http.post<DocumentItem>(`/api/v1/documents/${id}/approve`, {}));

export const rejectDocument = (id: number, reason: string) =>
  call(http.post<DocumentItem>(`/api/v1/documents/${id}/reject`, { reason }));

// ---- GitHub ----
export const analyzePullRequest = (owner: string, repo: string, pullNumber: number) =>
  call(
    http.post<PullRequestAnalysisResponse>(
      `/api/v1/github/repositories/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}/pulls/${pullNumber}/analyze`,
      undefined,
      { timeout: 330_000 }, // three agents + GitHub fetches can be slow
    ),
  );

// ---- System ----
export const getHealth = () => call(http.get<HealthResponse>("/health"));
export const getInfo = () => call(http.get<InfoResponse>("/api/v1/info"));
export const getProxyStatus = () => call(http.get<ProxyStatus>("/__documind/proxy-status"));
