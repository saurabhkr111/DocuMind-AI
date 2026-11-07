import { cn, formatDateTime, humanize } from "@/lib/utils";
import { StatusBadge } from "@/components/common/StatusBadge";
import type { WorkspaceDocument } from "@/hooks/useWorkspace";

export function DocumentListItem({ doc, selected, onSelect }: { doc: WorkspaceDocument; selected: boolean; onSelect: () => void }) {
  return (
    <li>
      <button
        onClick={onSelect}
        aria-current={selected ? "true" : undefined}
        className={cn(
          "w-full px-4 py-3 text-left transition-colors hover:bg-slate-50",
          selected && "bg-brand-500/5 ring-1 ring-inset ring-brand-500/30",
        )}
      >
        <div className="flex items-start justify-between gap-2">
          <p className="line-clamp-2 text-sm font-medium text-slate-900">{doc.title}</p>
          <StatusBadge status={doc.approval_status} />
        </div>
        <p className="mt-1 text-xs text-slate-500">
          #{doc.id} · {humanize(doc.document_type)} · Workflow #{doc.workflow_id}
        </p>
        <p className="text-xs text-slate-400">{formatDateTime(doc.created_at)}</p>
      </button>
    </li>
  );
}
