import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ListChecks } from "lucide-react";
import { Card, PageHeader } from "@/components/common/Card";
import { EmptyState, ErrorState } from "@/components/common/EmptyState";
import { SearchInput } from "@/components/common/SearchInput";
import { TableSkeleton } from "@/components/common/Skeleton";
import { WorkflowTable } from "@/components/workflows/WorkflowTable";
import { useWorkspace } from "@/hooks/useWorkspace";
import { WORKFLOW_STATUSES, statusLabel } from "@/lib/status";

export default function WorkflowsPage() {
  const { summaries, details, status, error, refresh } = useWorkspace();
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  const statusOptions = useMemo(() => {
    const known = new Set<string>(WORKFLOW_STATUSES);
    const extra = [...new Set(summaries.map((w) => w.status))].filter((s) => !known.has(s));
    return [...WORKFLOW_STATUSES, ...extra];
  }, [summaries]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return summaries.filter((w) => {
      if (statusFilter !== "ALL" && w.status !== statusFilter) return false;
      if (!q) return true;
      const d = details[w.id];
      return [String(w.id), w.title, w.description ?? "", d?.source_reference ?? "", d?.source_type ?? ""].some((v) => v.toLowerCase().includes(q));
    });
  }, [summaries, details, query, statusFilter]);

  return (
    <>
      <PageHeader title="Workflows" description="Every analysis run created by DocuMind AI." />
      <Card>
        <div className="flex flex-wrap items-center gap-3 border-b border-slate-100 p-4">
          <SearchInput value={query} onChange={setQuery} placeholder="Search by ID, title or source…" />
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <span className="sr-only sm:not-sr-only">Status</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
            >
              <option value="ALL">All statuses</option>
              {statusOptions.map((s) => (
                <option key={s} value={s}>
                  {statusLabel(s)}
                </option>
              ))}
            </select>
          </label>
          {status === "ready" && (
            <p className="ml-auto text-sm text-slate-500">
              {filtered.length} of {summaries.length}
            </p>
          )}
        </div>

        {status === "loading" ? (
          <TableSkeleton />
        ) : status === "error" ? (
          <ErrorState message={error ?? "Unable to load workflows."} onRetry={() => void refresh()} />
        ) : summaries.length === 0 ? (
          <EmptyState
            icon={ListChecks}
            title="No workflows yet"
            description="Workflows appear here after you analyze a pull request."
            action={
              <Link to="/github" className="text-sm font-medium text-brand-600 hover:text-brand-700">
                Analyze a pull request
              </Link>
            }
          />
        ) : filtered.length === 0 ? (
          <EmptyState title="No matching workflows" description="Try a different search term or status filter." />
        ) : (
          <WorkflowTable workflows={filtered} details={details} />
        )}
      </Card>
    </>
  );
}
