import type { ReactNode } from "react";
import { AlertTriangle } from "lucide-react";
import { StatusBadge } from "@/components/common/StatusBadge";
import { agentLabel } from "@/lib/status";
import { asStringArray, durationMs, formatDateTime, formatDuration, isRecord, safeJsonParse } from "@/lib/utils";
import type { AgentFinding, AgentLog, TeamActionItem } from "@/types/api";

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div>
      <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</h4>
      {children}
    </div>
  );
}

function BulletList({ items }: { items: string[] }) {
  if (items.length === 0) return <p className="text-sm text-slate-400">None</p>;
  return (
    <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
      {items.map((item, i) => (
        <li key={i} className="break-words">
          {item}
        </li>
      ))}
    </ul>
  );
}

function toFindings(value: unknown): AgentFinding[] {
  if (!Array.isArray(value)) return [];
  return value.filter(isRecord).map((f) => ({
    title: String(f.title ?? "Untitled finding"),
    description: String(f.description ?? ""),
    severity: String(f.severity ?? "INFO") as AgentFinding["severity"],
    category: typeof f.category === "string" ? f.category : null,
    file_path: typeof f.file_path === "string" ? f.file_path : null,
    line_number: typeof f.line_number === "number" ? f.line_number : null,
    recommendation: typeof f.recommendation === "string" ? f.recommendation : null,
  }));
}

function toActions(value: unknown): TeamActionItem[] {
  if (!Array.isArray(value)) return [];
  return value.filter(isRecord).map((a) => ({
    title: String(a.title ?? "Untitled action"),
    description: typeof a.description === "string" ? a.description : null,
    owner: typeof a.owner === "string" ? a.owner : null,
    priority: (["LOW", "MEDIUM", "HIGH"].includes(String(a.priority)) ? a.priority : "MEDIUM") as TeamActionItem["priority"],
  }));
}

function ResultBody({ name, result }: { name: string; result: Record<string, unknown> }) {
  const summary = typeof result.summary === "string" ? result.summary : null;

  if (name === "documentation") {
    return (
      <div className="space-y-4">
        {summary && <p className="text-sm text-slate-700">{summary}</p>}
        <Section title="Files covered">
          <BulletList items={asStringArray(result.files_covered)} />
        </Section>
        <Section title="Documentation gaps">
          <BulletList items={asStringArray(result.documentation_gaps)} />
        </Section>
      </div>
    );
  }

  if (name === "code_review") {
    const findings = toFindings(result.findings);
    return (
      <div className="space-y-4">
        {summary && <p className="text-sm text-slate-700">{summary}</p>}
        {typeof result.overall_risk === "string" && (
          <div className="flex items-center gap-2 text-sm text-slate-600">
            Overall risk: <StatusBadge status={result.overall_risk} />
          </div>
        )}
        <Section title={`Findings (${findings.length})`}>
          {findings.length === 0 ? (
            <p className="text-sm text-slate-400">No findings reported</p>
          ) : (
            <ul className="space-y-2">
              {findings.map((f, i) => (
                <li key={i} className="rounded-lg border border-slate-200 p-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge status={f.severity} />
                    <span className="text-sm font-medium text-slate-900">{f.title}</span>
                  </div>
                  {(f.file_path || f.category) && (
                    <p className="mt-1 break-all font-mono text-xs text-slate-500">
                      {f.file_path}
                      {f.line_number ? `:${f.line_number}` : ""}
                      {f.category ? ` · ${f.category}` : ""}
                    </p>
                  )}
                  {f.description && <p className="mt-1.5 text-sm text-slate-700">{f.description}</p>}
                  {f.recommendation && <p className="mt-1.5 text-sm text-slate-600">Recommendation: {f.recommendation}</p>}
                </li>
              ))}
            </ul>
          )}
        </Section>
        <Section title="Recommendations">
          <BulletList items={asStringArray(result.recommendations)} />
        </Section>
      </div>
    );
  }

  if (name === "team_intelligence") {
    const actions = toActions(result.action_items);
    return (
      <div className="space-y-4">
        {summary && <p className="text-sm text-slate-700">{summary}</p>}
        <Section title="Completed items">
          <BulletList items={asStringArray(result.completed_items)} />
        </Section>
        <Section title="Decisions">
          <BulletList items={asStringArray(result.decisions)} />
        </Section>
        <Section title="Action items">
          {actions.length === 0 ? (
            <p className="text-sm text-slate-400">None</p>
          ) : (
            <ul className="space-y-2">
              {actions.map((a, i) => (
                <li key={i} className="flex items-start gap-3 rounded-lg border border-slate-200 p-3">
                  <StatusBadge status={a.priority ?? "MEDIUM"} />
                  <div className="min-w-0 text-sm">
                    <p className="font-medium text-slate-900">{a.title}</p>
                    {a.description && <p className="text-slate-600">{a.description}</p>}
                    {a.owner && <p className="text-xs text-slate-500">Owner: {a.owner}</p>}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Section>
        <Section title="Blockers">
          <BulletList items={asStringArray(result.blockers)} />
        </Section>
      </div>
    );
  }

  // Unknown agent: show the raw structured result rather than hiding it.
  return <pre className="overflow-x-auto rounded-lg bg-slate-50 p-3 text-xs text-slate-700">{JSON.stringify(result, null, 2)}</pre>;
}

export function AgentResultPanel({ log }: { log: AgentLog }) {
  const parsed = safeJsonParse<unknown>(log.output_summary);
  const result = isRecord(parsed) ? parsed : null;

  return (
    <div className="space-y-4 p-5">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
        <StatusBadge status={log.status} />
        <span>Started {formatDateTime(log.started_at)}</span>
        <span>Duration {formatDuration(durationMs(log.started_at, log.completed_at))}</span>
      </div>
      {log.error_message && (
        <div className="flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800" role="alert">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span className="break-words">{log.error_message}</span>
        </div>
      )}
      {result ? (
        <ResultBody name={log.agent_name} result={result} />
      ) : (
        !log.error_message && <p className="text-sm text-slate-400">{agentLabel(log.agent_name)} did not store a result.</p>
      )}
    </div>
  );
}
