import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { STATUS_COLORS, statusLabel } from "@/lib/status";
import type { WorkflowSummary } from "@/types/api";

export function StatusDistributionChart({ workflows }: { workflows: WorkflowSummary[] }) {
  const counts = new Map<string, number>();
  for (const w of workflows) counts.set(w.status, (counts.get(w.status) ?? 0) + 1);
  const data = [...counts.entries()].map(([status, value]) => ({ status, name: statusLabel(status), value }));

  return (
    <div className="flex flex-col items-center gap-4 p-5 sm:flex-row">
      <div className="h-48 w-48 shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={52} outerRadius={80} paddingAngle={2} stroke="none">
              {data.map((d) => (
                <Cell key={d.status} fill={STATUS_COLORS[d.status] ?? "#94a3b8"} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <ul className="w-full space-y-2 text-sm">
        {data.map((d) => (
          <li key={d.status} className="flex items-center justify-between gap-3">
            <span className="flex items-center gap-2 text-slate-700">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: STATUS_COLORS[d.status] ?? "#94a3b8" }} />
              {d.name}
            </span>
            <span className="font-medium text-slate-900">{d.value}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
