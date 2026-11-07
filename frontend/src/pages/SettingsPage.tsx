import type { ReactNode } from "react";
import { CheckCircle2, RefreshCw, XCircle } from "lucide-react";
import { Button } from "@/components/common/Button";
import { Card, CardHeader, PageHeader } from "@/components/common/Card";
import { Skeleton } from "@/components/common/Skeleton";
import { useAsync } from "@/hooks/useAsync";
import { useWorkspace } from "@/hooks/useWorkspace";
import { getHealth, getInfo, getProxyStatus } from "@/services/api";
import { formatDateTime } from "@/lib/utils";

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 px-5 py-3.5 text-sm">
      <dt className="text-slate-500">{label}</dt>
      <dd className="min-w-0 break-words text-right font-medium text-slate-900">{children}</dd>
    </div>
  );
}

function Ok({ ok, yes, no }: { ok: boolean; yes: string; no: string }) {
  return ok ? (
    <span className="inline-flex items-center gap-1.5 text-emerald-700">
      <CheckCircle2 className="h-4 w-4" /> {yes}
    </span>
  ) : (
    <span className="inline-flex items-center gap-1.5 text-rose-700">
      <XCircle className="h-4 w-4" /> {no}
    </span>
  );
}

export default function SettingsPage() {
  const proxy = useAsync(getProxyStatus, []);
  const health = useAsync(getHealth, []);
  const info = useAsync(getInfo, []);
  const workspace = useWorkspace();

  const checking = proxy.loading || health.loading || info.loading;
  const recheck = () => {
    proxy.reload();
    health.reload();
    info.reload();
    void workspace.refresh();
  };

  return (
    <>
      <PageHeader
        title="Settings"
        description="Backend connection and application information."
        action={
          <Button variant="secondary" onClick={recheck} loading={checking}>
            {!checking && <RefreshCw className="h-4 w-4" />} Re-check
          </Button>
        }
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Backend connection" />
          <dl className="divide-y divide-slate-100">
            <Row label="Backend URL">{proxy.loading ? <Skeleton className="h-4 w-40" /> : proxy.data ? <span className="font-mono text-xs">{proxy.data.backend_url}</span> : "Unavailable"}</Row>
            <Row label="Health check">
              {health.loading ? (
                <Skeleton className="h-4 w-24" />
              ) : health.data ? (
                <Ok ok={health.data.status === "healthy"} yes="Healthy" no={health.data.status} />
              ) : (
                <Ok ok={false} yes="" no="Unreachable" />
              )}
            </Row>
            <Row label="Proxy API key">{proxy.loading ? <Skeleton className="h-4 w-24" /> : <Ok ok={!!proxy.data?.api_key_configured} yes="Configured (hidden)" no="Not configured" />}</Row>
            <Row label="Authentication">
              {workspace.status === "loading" ? (
                <Skeleton className="h-4 w-24" />
              ) : workspace.status === "ready" ? (
                <Ok ok yes="API key accepted" no="" />
              ) : (
                <span className="text-rose-700">{workspace.error ?? "Failed"}</span>
              )}
            </Row>
            {health.data && <Row label="Last health response">{formatDateTime(health.data.timestamp)}</Row>}
          </dl>
          {health.error && <p className="border-t border-slate-100 px-5 py-3 text-xs text-rose-700">{health.error}</p>}
        </Card>

        <Card>
          <CardHeader title="Application information" />
          <dl className="divide-y divide-slate-100">
            <Row label="Dashboard">DocuMind AI Dashboard 1.0.0</Row>
            <Row label="Backend service">{info.loading ? <Skeleton className="h-4 w-32" /> : info.data ? `${info.data.project_name} ${info.data.version}` : "Unavailable"}</Row>
            <Row label="Backend framework">{info.data?.backend ?? "—"}</Row>
            <Row label="Orchestrator">{info.data?.orchestrator ?? "—"}</Row>
            <Row label="Agents">{info.data ? info.data.agents.join(", ") : "—"}</Row>
            <Row label="Workflows loaded">{workspace.status === "ready" ? workspace.summaries.length : "—"}</Row>
          </dl>
          {info.error && <p className="border-t border-slate-100 px-5 py-3 text-xs text-rose-700">{info.error}</p>}
        </Card>
      </div>
    </>
  );
}
