import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { getWorkflowDetails, getWorkflows } from "@/services/api";
import { errorMessage } from "@/services/errors";
import type { AgentLog, DocumentItem, WorkflowDetail, WorkflowSummary } from "@/types/api";

/**
 * The backend has no "list documents" or "list agent runs" endpoint, and the
 * workflow list omits source_type / created_at. Everything else is therefore
 * derived from GET /workflows/ + GET /workflows/{id}/details (fetched with
 * limited concurrency). All values are real backend data.
 */

const DETAIL_CONCURRENCY = 4;

export interface WorkspaceDocument extends DocumentItem {
  workflow_title: string;
}
export interface WorkspaceAgentRun extends AgentLog {
  workflow_id: number;
  workflow_title: string;
}

interface WorkspaceValue {
  summaries: WorkflowSummary[];
  details: Record<number, WorkflowDetail>;
  documents: WorkspaceDocument[];
  agentRuns: WorkspaceAgentRun[];
  /** "loading" only before the first successful load; later refreshes keep data visible. */
  status: "loading" | "ready" | "error";
  refreshing: boolean;
  error: string | null;
  failedDetailIds: number[];
  lastUpdated: Date | null;
  refresh: () => Promise<void>;
  refreshWorkflow: (id: number) => Promise<void>;
}

const WorkspaceContext = createContext<WorkspaceValue | null>(null);

async function mapLimit<T, R>(items: T[], limit: number, fn: (item: T) => Promise<R>): Promise<R[]> {
  const results: R[] = new Array(items.length);
  let cursor = 0;
  async function worker() {
    while (cursor < items.length) {
      const index = cursor++;
      results[index] = await fn(items[index]);
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, worker));
  return results;
}

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [summaries, setSummaries] = useState<WorkflowSummary[]>([]);
  const [details, setDetails] = useState<Record<number, WorkflowDetail>>({});
  const [status, setStatus] = useState<WorkspaceValue["status"]>("loading");
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [failedDetailIds, setFailedDetailIds] = useState<number[]>([]);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const requestId = useRef(0);

  const refresh = useCallback(async () => {
    const current = ++requestId.current;
    setRefreshing(true);
    try {
      const list = await getWorkflows();
      const failed: number[] = [];
      const fetched = await mapLimit(list, DETAIL_CONCURRENCY, async (w) => {
        try {
          return await getWorkflowDetails(w.id);
        } catch {
          failed.push(w.id);
          return null;
        }
      });
      if (current !== requestId.current) return; // a newer refresh superseded this one

      const map: Record<number, WorkflowDetail> = {};
      for (const d of fetched) if (d) map[d.id] = d;
      setSummaries(list);
      setDetails(map);
      setFailedDetailIds(failed);
      setError(null);
      setStatus("ready");
      setLastUpdated(new Date());
    } catch (e) {
      if (current !== requestId.current) return;
      setError(errorMessage(e));
      setStatus((s) => (s === "ready" ? "ready" : "error"));
    } finally {
      if (current === requestId.current) setRefreshing(false);
    }
  }, []);

  const refreshWorkflow = useCallback(async (id: number) => {
    try {
      const fresh = await getWorkflowDetails(id);
      setDetails((prev) => ({ ...prev, [id]: fresh }));
      setSummaries((prev) =>
        prev.some((w) => w.id === id)
          ? prev.map((w) => (w.id === id ? { ...w, status: fresh.status, title: fresh.title, description: fresh.description } : w))
          : [{ id: fresh.id, title: fresh.title, description: fresh.description, status: fresh.status }, ...prev],
      );
      setLastUpdated(new Date());
    } catch {
      // Fall back to a full refresh if a single refresh fails.
      await refresh();
    }
  }, [refresh]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const documents = useMemo<WorkspaceDocument[]>(
    () =>
      Object.values(details)
        .flatMap((w) => w.documents.map((d) => ({ ...d, workflow_title: w.title })))
        .sort((a, b) => b.id - a.id),
    [details],
  );

  const agentRuns = useMemo<WorkspaceAgentRun[]>(
    () =>
      Object.values(details)
        .flatMap((w) => w.agent_logs.map((l) => ({ ...l, workflow_id: w.id, workflow_title: w.title })))
        .sort((a, b) => b.id - a.id),
    [details],
  );

  const value = useMemo<WorkspaceValue>(
    () => ({ summaries, details, documents, agentRuns, status, refreshing, error, failedDetailIds, lastUpdated, refresh, refreshWorkflow }),
    [summaries, details, documents, agentRuns, status, refreshing, error, failedDetailIds, lastUpdated, refresh, refreshWorkflow],
  );

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspace(): WorkspaceValue {
  const ctx = useContext(WorkspaceContext);
  if (!ctx) throw new Error("useWorkspace must be used within WorkspaceProvider");
  return ctx;
}
