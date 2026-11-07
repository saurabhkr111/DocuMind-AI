import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, ExternalLink, FileText, RefreshCw } from "lucide-react";
import { Button } from "@/components/common/Button";
import { Card, CardHeader } from "@/components/common/Card";
import { EmptyState, ErrorState } from "@/components/common/EmptyState";
import { Skeleton } from "@/components/common/Skeleton";
import { StatusBadge } from "@/components/common/StatusBadge";
import { AgentProgress, latestLogByAgent } from "@/components/workflows/AgentProgress";
import { AgentResultPanel } from "@/components/workflows/AgentResultPanel";
import { useAsync } from "@/hooks/useAsync";
import { getWorkflowDetails } from "@/services/api";
import { AGENTS } from "@/lib/status";
import { cn, formatDateTime, humanize } from "@/lib/utils";

function Info({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="min-w-0">
      <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-1 break-words text-sm text-slate-900">{children}</dd>
    </div>
  );
}

export default function WorkflowDetailsPage() {
  const { workflowId } = useParams();
  const id = Number(workflowId);
  const valid = Number.isInteger(id) && id > 0;

  const { data: workflow, loading, error, reload } = useAsync(() => (valid ? getWorkflowDetails(id) : Promise.reject(new Error("Invalid workflow ID."))), [id]);
  const [activeAgent, setActiveAgent] = useState<string>(AGENTS[0].name);

  useEffect(() => setActiveAgent(AGENTS[0].name), [id]);

  const latest = useMemo(() => latestLogByAgent(workflow?.agent_logs ?? []), [workflow]);

  const back = (
    <Link to="/workflows" className="mb-4 inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800">
      <ArrowLeft className="h-4 w-4" /> Workflows
    </Link>
  );

  if (loading && !workflow) {
    return (
      <>
        {back}
        <Skeleton className="mb-4 h-10 w-2/3" />
        <Skeleton className="mb-4 h-40" />
        <Skeleton className="h-64" />
      </>
    );
  }

  if (error || !workflow) {
    return (
      <>
        {back}
        <Card>
          <ErrorState message={error ?? "Workflow not found."} onRetry={valid ? reload : undefined} />
        </Card>
      </>
    );
  }

  const sourceUrl = workflow.source_reference?.startsWith("https://github.com/") ? workflow.source_reference : null;
  const activeLog = latest[activeAgent];

  return (
    <>
      {back}
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="break-words text-2xl font-semibold tracking-tight text-slate-900">{workflow.title}</h1>
            <StatusBadge status={workflow.status} />
          </div>
          <p className="mt-1 font-mono text-xs text-slate-500">Workflow #{workflow.id}</p>
        </div>
        <Button variant="secondary" onClick={reload} loading={loading}>
          {!loading && <RefreshCw className="h-4 w-4" />} Refresh
        </Button>
      </div>

      <Card>
        <CardHeader title="Workflow information" />
        <dl className="grid gap-5 p-5 sm:grid-cols-2 lg:grid-cols-4">
          <Info label="Source type">{workflow.source_type ? humanize(workflow.source_type) : "—"}</Info>
          <Info label="GitHub source">
            {sourceUrl ? (
              <a href={sourceUrl} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-brand-600 hover:text-brand-700">
                <span className="break-all">{sourceUrl.replace("https://github.com/", "")}</span>
                <ExternalLink className="h-3.5 w-3.5 shrink-0" />
              </a>
            ) : (
              (workflow.source_reference ?? "—")
            )}
          </Info>
          <Info label="Created">{formatDateTime(workflow.created_at)}</Info>
          <Info label="Last updated">{formatDateTime(workflow.updated_at)}</Info>
        </dl>
        {workflow.description && (
          <div className="border-t border-slate-100 px-5 py-4">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Description</p>
            <p className="mt-1 whitespace-pre-wrap break-words text-sm text-slate-700">{workflow.description}</p>
          </div>
        )}
      </Card>

      <Card className="mt-6">
        <CardHeader title="Agent execution" description="Latest recorded run for each agent" />
        <div className="p-5">
          <AgentProgress logs={workflow.agent_logs} />
        </div>
      </Card>

      <Card className="mt-6">
        <CardHeader title="Agent results" />
        <div role="tablist" aria-label="Agent results" className="flex gap-1 overflow-x-auto border-b border-slate-100 px-3">
          {AGENTS.map((a) => (
            <button
              key={a.name}
              role="tab"
              aria-selected={activeAgent === a.name}
              onClick={() => setActiveAgent(a.name)}
              className={cn(
                "whitespace-nowrap border-b-2 px-3 py-3 text-sm font-medium transition-colors",
                activeAgent === a.name ? "border-brand-600 text-brand-700" : "border-transparent text-slate-500 hover:text-slate-800",
              )}
            >
              {a.label}
            </button>
          ))}
        </div>
        <div role="tabpanel">
          {activeLog ? <AgentResultPanel log={activeLog} /> : <EmptyState title="No result recorded" description="This agent has not produced a result for this workflow." />}
        </div>
      </Card>

      <Card className="mt-6">
        <CardHeader title={`Generated documents (${workflow.documents.length})`} />
        {workflow.documents.length === 0 ? (
          <EmptyState icon={FileText} title="No documents generated" />
        ) : (
          <ul className="divide-y divide-slate-100">
            {workflow.documents.map((d) => (
              <li key={d.id}>
                <Link to={`/documents/${d.id}`} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3.5 hover:bg-slate-50">
                  <div className="min-w-0">
                    <p className="break-words text-sm font-medium text-slate-900">{d.title}</p>
                    <p className="text-xs text-slate-500">
                      #{d.id} · {humanize(d.document_type)} · {formatDateTime(d.created_at)}
                    </p>
                  </div>
                  <StatusBadge status={d.approval_status} />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </>
  );
}
