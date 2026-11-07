import { Activity } from "lucide-react";
import { Card, CardHeader, PageHeader } from "@/components/common/Card";
import { EmptyState, ErrorState } from "@/components/common/EmptyState";
import { Skeleton, TableSkeleton } from "@/components/common/Skeleton";
import { AgentCard } from "@/components/agents/AgentCard";
import { AgentRunsTable } from "@/components/agents/AgentRunsTable";
import { useWorkspace } from "@/hooks/useWorkspace";
import { AGENTS } from "@/lib/status";

const MAX_ROWS = 50;

export default function AgentsPage() {
  const { agentRuns, status, error, refresh } = useWorkspace();

  return (
    <>
      <PageHeader title="Agent Monitoring" description="Execution history of the three DocuMind agents." />

      {status === "error" ? (
        <Card>
          <ErrorState message={error ?? "Unable to load agent data."} onRetry={() => void refresh()} />
        </Card>
      ) : (
        <>
          <div className="grid gap-4 lg:grid-cols-3">
            {status === "loading"
              ? AGENTS.map((a) => <Skeleton key={a.name} className="h-44" />)
              : AGENTS.map((a) => (
                  <AgentCard key={a.name} label={a.label} description={a.description} runs={agentRuns.filter((r) => r.agent_name === a.name)} />
                ))}
          </div>

          <Card className="mt-6">
            <CardHeader
              title="Recent executions"
              description="Execution time is calculated from each run's recorded start and completion timestamps."
            />
            {status === "loading" ? (
              <TableSkeleton />
            ) : agentRuns.length === 0 ? (
              <EmptyState icon={Activity} title="No agent executions recorded" description="Run a pull request analysis to see agent activity here." />
            ) : (
              <>
                <AgentRunsTable runs={agentRuns.slice(0, MAX_ROWS)} />
                {agentRuns.length > MAX_ROWS && (
                  <p className="border-t border-slate-100 px-5 py-3 text-xs text-slate-500">
                    Showing the latest {MAX_ROWS} of {agentRuns.length} executions.
                  </p>
                )}
              </>
            )}
          </Card>
        </>
      )}
    </>
  );
}
