import { Link, useNavigate } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { StatusBadge } from "@/components/common/StatusBadge";
import { formatDateTime, humanize } from "@/lib/utils";
import type { WorkflowDetail, WorkflowSummary } from "@/types/api";

export function WorkflowTable({
  workflows,
  details,
  compact,
}: {
  workflows: WorkflowSummary[];
  details: Record<number, WorkflowDetail>;
  compact?: boolean;
}) {
  const navigate = useNavigate();

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-left text-sm">
        <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-5 py-3 font-medium">ID</th>
            <th className="px-5 py-3 font-medium">Title</th>
            {!compact && <th className="px-5 py-3 font-medium">Source</th>}
            <th className="px-5 py-3 font-medium">Created</th>
            <th className="px-5 py-3 font-medium">Status</th>
            <th className="w-8 px-3 py-3" />
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {workflows.map((w) => {
            const d = details[w.id];
            return (
              <tr
                key={w.id}
                onClick={() => navigate(`/workflows/${w.id}`)}
                className="cursor-pointer transition-colors hover:bg-slate-50"
              >
                <td className="whitespace-nowrap px-5 py-3 font-mono text-xs text-slate-500">#{w.id}</td>
                <td className="max-w-xs px-5 py-3">
                  <Link
                    to={`/workflows/${w.id}`}
                    onClick={(e) => e.stopPropagation()}
                    className="line-clamp-2 font-medium text-slate-900 hover:text-brand-600"
                  >
                    {w.title}
                  </Link>
                </td>
                {!compact && (
                  <td className="whitespace-nowrap px-5 py-3 text-slate-600">{d?.source_type ? humanize(d.source_type) : "—"}</td>
                )}
                <td className="whitespace-nowrap px-5 py-3 text-slate-600">{d ? formatDateTime(d.created_at) : "—"}</td>
                <td className="px-5 py-3">
                  <StatusBadge status={w.status} />
                </td>
                <td className="px-3 py-3 text-slate-400">
                  <ChevronRight className="h-4 w-4" />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
