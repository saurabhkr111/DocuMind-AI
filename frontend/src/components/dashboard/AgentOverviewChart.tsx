import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AGENTS } from "@/lib/status";
import type { WorkspaceAgentRun } from "@/hooks/useWorkspace";

export function AgentOverviewChart({ runs }: { runs: WorkspaceAgentRun[] }) {
  const data = AGENTS.map((a) => {
    const own = runs.filter((r) => r.agent_name === a.name);
    return {
      name: a.label.replace(" Agent", ""),
      Completed: own.filter((r) => r.status === "COMPLETED").length,
      Failed: own.filter((r) => r.status === "FAILED").length,
      Other: own.filter((r) => r.status !== "COMPLETED" && r.status !== "FAILED").length,
    };
  });

  return (
    <div className="h-64 p-5">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
          <XAxis dataKey="name" tickLine={false} axisLine={false} tick={{ fontSize: 12, fill: "#64748b" }} />
          <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={{ fontSize: 12, fill: "#64748b" }} />
          <Tooltip cursor={{ fill: "#f1f5f9" }} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="Completed" stackId="a" fill="#16a34a" radius={[0, 0, 0, 0]} />
          <Bar dataKey="Failed" stackId="a" fill="#dc2626" />
          <Bar dataKey="Other" stackId="a" fill="#94a3b8" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
