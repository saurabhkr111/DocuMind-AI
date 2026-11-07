import type { LucideIcon } from "lucide-react";
import { Card } from "@/components/common/Card";
import { Skeleton } from "@/components/common/Skeleton";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  icon: Icon,
  accent,
  hint,
  loading,
}: {
  label: string;
  value: number;
  icon: LucideIcon;
  accent: string;
  hint?: string;
  loading?: boolean;
}) {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-500">{label}</p>
          {loading ? <Skeleton className="mt-2 h-8 w-16" /> : <p className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">{value}</p>}
          {hint && !loading && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
        </div>
        <div className={cn("rounded-lg p-2.5", accent)}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </Card>
  );
}
