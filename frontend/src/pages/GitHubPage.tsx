import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AlertTriangle, CheckCircle2, GitPullRequest } from "lucide-react";
import { Card, CardHeader, PageHeader } from "@/components/common/Card";
import { StatusBadge } from "@/components/common/StatusBadge";
import { PullRequestForm, type PullRequestInput } from "@/components/github/PullRequestForm";
import { useToast } from "@/hooks/useToast";
import { useWorkspace } from "@/hooks/useWorkspace";
import { analyzePullRequest } from "@/services/api";
import { toApiError } from "@/services/errors";
import { agentLabel } from "@/lib/status";
import { formatDuration } from "@/lib/utils";
import type { PullRequestAnalysisResponse } from "@/types/api";

const REDIRECT_DELAY_MS = 2000;

export default function GitHubPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const { refreshWorkflow } = useWorkspace();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PullRequestAnalysisResponse | null>(null);

  useEffect(() => {
    if (!result) return;
    const timer = window.setTimeout(() => navigate(`/workflows/${result.workflow_id}`), REDIRECT_DELAY_MS);
    return () => window.clearTimeout(timer);
  }, [result, navigate]);

  async function handleSubmit({ owner, repo, pullNumber }: PullRequestInput) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await analyzePullRequest(owner, repo, pullNumber);
      setResult(response);
      toast.success("Analysis complete", `Workflow #${response.workflow_id} was created.`);
      void refreshWorkflow(response.workflow_id);
    } catch (e) {
      const message = toApiError(e).message;
      setError(message);
      toast.error("Pull request analysis failed", message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeader title="GitHub Integration" description="Analyze a pull request with the Documentation, Code Review and Team Intelligence agents." />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Analyze a pull request" />
          <PullRequestForm onSubmit={(input) => void handleSubmit(input)} loading={loading} />
        </Card>

        <div className="space-y-6">
          {loading && (
            <Card className="p-5" >
              <div role="status" className="flex items-start gap-3">
                <GitPullRequest className="mt-0.5 h-5 w-5 animate-pulse text-brand-600" />
                <div>
                  <p className="text-sm font-medium text-slate-900">Analysis in progress</p>
                  <p className="mt-1 text-sm text-slate-500">
                    Fetching the pull request from GitHub and running all three agents. This can take a minute or more—please keep this page open.
                  </p>
                </div>
              </div>
            </Card>
          )}

          {error && (
            <div className="flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800" role="alert">
              <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
              <div>
                <p className="font-medium">Analysis failed</p>
                <p className="mt-1 break-words">{error}</p>
              </div>
            </div>
          )}

          {result && (
            <Card>
              <div className="flex items-start gap-3 border-b border-slate-100 p-5">
                <CheckCircle2 className="mt-0.5 h-5 w-5 text-emerald-600" />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-900">{result.message}</p>
                  <p className="mt-1 text-sm text-slate-600">
                    {result.repository} · Workflow ID <span className="font-mono font-semibold">#{result.workflow_id}</span>
                  </p>
                  <div className="mt-2 flex items-center gap-2 text-sm text-slate-600">
                    Status <StatusBadge status={result.workflow_status} />
                  </div>
                </div>
              </div>
              <ul className="divide-y divide-slate-100">
                {Object.values(result.agent_results).map((a) => (
                  <li key={a.agent_name} className="flex items-center justify-between gap-3 px-5 py-3 text-sm">
                    <span className="text-slate-800">{agentLabel(a.agent_name)}</span>
                    <span className="flex items-center gap-3">
                      <span className="text-xs text-slate-500">{formatDuration(a.execution_time_ms)}</span>
                      <StatusBadge status={a.status} />
                    </span>
                  </li>
                ))}
              </ul>
              <p className="border-t border-slate-100 px-5 py-3 text-xs text-slate-500">
                Opening the workflow… or{" "}
                <Link to={`/workflows/${result.workflow_id}`} className="font-medium text-brand-600 hover:text-brand-700">
                  go there now
                </Link>
                .
              </p>
            </Card>
          )}

          {!loading && !error && !result && (
            <Card className="p-5">
              <p className="text-sm font-medium text-slate-900">How it works</p>
              <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-slate-600">
                <li>DocuMind fetches the pull request and its changed files from GitHub.</li>
                <li>The three agents run and their results are saved.</li>
                <li>A workflow is created and any generated documentation waits for your approval.</li>
              </ol>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}
