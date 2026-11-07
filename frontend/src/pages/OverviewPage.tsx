import { Link } from "react-router-dom";
import { AlertTriangle, CheckCircle2, Clock, ListChecks, XCircle } from "lucide-react";
import { Card, CardHeader, PageHeader } from "@/components/common/Card";
import { EmptyState, ErrorState } from "@/components/common/EmptyState";
import { Skeleton, TableSkeleton } from "@/components/common/Skeleton";
import { StatCard } from "@/components/dashboard/StatCard";
import { StatusDistributionChart } from "@/components/dashboard/StatusDistributionChart";
import { AgentOverviewChart } from "@/components/dashboard/AgentOverviewChart";
import { WorkflowTable } from "@/components/workflows/WorkflowTable";
import { useWorkspace } from "@/hooks/useWorkspace";

export default function OverviewPage() {
  const { summaries, details, agentRuns, status, error, failedDetailIds, refresh } = useWorkspace();
  const loading = status === "loading";

  if (status === "error") {
    return (
      <>
        <PageHeader title="Overview" />
        <Card>
          <ErrorState message={error ?? "Unable to load workflows."} onRetry={() => void refresh()} />
        </Card>
      </>
    );
  }

  const count = (s: string) => summaries.filter((w) => w.status === s).length;
  const partial = count("PARTIAL");

  return (
    <>
      <PageHeader title="Overview" description="Live summary of DocuMind AI workflows and agent activity." />

      {failedDetailIds.length > 0 && (
        <div className="mb-4 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800" role="alert">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          Details could not be loaded for {failedDetailIds.length} workflow(s), so agent and document figures may be incomplete.
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total workflows" value={summaries.length} icon={ListChecks} accent="bg-brand-500/10 text-brand-600" loading={loading} />
        <StatCard label="Approved workflows" value={count("APPROVED")} icon={CheckCircle2} accent="bg-emerald-50 text-emerald-600" loading={loading} />
        <StatCard label="Pending approvals" value={count("AWAITING_APPROVAL")} icon={Clock} accent="bg-amber-50 text-amber-600" loading={loading} hint="Workflows awaiting document review" />
        <StatCard
          label="Failed workflows"
          value={count("FAILED")}
          icon={XCircle}
          accent="bg-rose-50 text-rose-600"
          loading={loading}
          hint={partial > 0 ? `+ ${partial} partially failed` : undefined}
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Workflow status distribution" />
          {loading ? <Skeleton className="m-5 h-48" /> : summaries.length === 0 ? <EmptyState title="No workflows yet" /> : <StatusDistributionChart workflows={summaries} />}
        </Card>
        <Card>
          <CardHeader title="Agent execution overview" description="Recorded runs per agent" />
          {loading ? <Skeleton className="m-5 h-52" /> : agentRuns.length === 0 ? <EmptyState title="No agent runs recorded" /> : <AgentOverviewChart runs={agentRuns} />}
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader
          title="Recent workflows"
          action={
            <Link to="/workflows" className="text-sm font-medium text-brand-600 hover:text-brand-700">
              View all
            </Link>
          }
        />
        {loading ? (
          <TableSkeleton rows={4} />
        ) : summaries.length === 0 ? (
          <EmptyState
            title="No workflows yet"
            description="Analyze a GitHub pull request to create your first workflow."
            action={
              <Link to="/github" className="text-sm font-medium text-brand-600 hover:text-brand-700">
                Analyze a pull request
              </Link>
            }
          />
        ) : (
          <WorkflowTable workflows={summaries.slice(0, 5)} details={details} compact />
        )}
      </Card>
    </>
  );
}
