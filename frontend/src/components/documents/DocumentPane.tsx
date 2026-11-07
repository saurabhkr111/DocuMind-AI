import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, FileText } from "lucide-react";
import { Card } from "@/components/common/Card";
import { Markdown } from "@/components/common/Markdown";
import { StatusBadge } from "@/components/common/StatusBadge";
import { useAsync } from "@/hooks/useAsync";
import { getDocument } from "@/services/api";
import { formatDateTime, humanize } from "@/lib/utils";
import type { DocumentItem } from "@/types/api";

function Meta({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="min-w-0">
      <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-0.5 break-words text-sm text-slate-900">{children}</dd>
    </div>
  );
}

/**
 * Shows a document using the list data immediately, then re-fetches the
 * authoritative copy from GET /api/v1/documents/{id}.
 */
export function DocumentPane({ doc, footer }: { doc: DocumentItem; footer?: ReactNode }) {
  const { data, error } = useAsync(() => getDocument(doc.id), [doc.id, doc.approval_status]);
  const current = data ?? doc;
  const isMarkdown = /markdown|^md$/i.test(current.document_type);

  return (
    <Card className="flex min-h-0 flex-col">
      <div className="border-b border-slate-100 px-5 py-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex min-w-0 items-start gap-3">
            <div className="rounded-lg bg-slate-100 p-2 text-slate-600">
              <FileText className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <h2 className="break-words text-base font-semibold text-slate-900">{current.title}</h2>
              <p className="text-xs text-slate-500">
                Document #{current.id} ·{" "}
                <Link to={`/workflows/${current.workflow_id}`} className="text-brand-600 hover:text-brand-700">
                  Workflow #{current.workflow_id}
                </Link>
              </p>
            </div>
          </div>
          <StatusBadge status={current.approval_status} />
        </div>

        <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Meta label="Type">{humanize(current.document_type)}</Meta>
          <Meta label="Created">{formatDateTime(current.created_at)}</Meta>
          <Meta label="Reviewed by">{current.reviewed_by ?? "—"}</Meta>
          <Meta label="Reviewed at">{formatDateTime(current.reviewed_at)}</Meta>
        </dl>

        {current.approval_reason && (
          <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">
            <span className="font-medium">Rejection reason: </span>
            <span className="break-words">{current.approval_reason}</span>
          </div>
        )}
        {error && (
          <p className="mt-3 flex items-center gap-1.5 text-xs text-amber-700">
            <AlertTriangle className="h-3.5 w-3.5" /> Could not refresh this document; showing the last loaded copy.
          </p>
        )}
      </div>

      <div className="max-h-[65vh] overflow-y-auto px-5 py-4">
        {isMarkdown ? <Markdown content={current.content} /> : <pre className="whitespace-pre-wrap break-words text-sm text-slate-800">{current.content}</pre>}
      </div>

      {footer && <div className="border-t border-slate-100 px-5 py-4">{footer}</div>}
    </Card>
  );
}
