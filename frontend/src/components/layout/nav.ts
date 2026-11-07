import { Activity, FileText, GitPullRequest, LayoutDashboard, ListChecks, ShieldCheck, Settings, type LucideIcon } from "lucide-react";

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  end?: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/workflows", label: "Workflows", icon: ListChecks },
  { to: "/documents", label: "Documents", icon: FileText },
  { to: "/approvals", label: "Approvals", icon: ShieldCheck },
  { to: "/github", label: "GitHub", icon: GitPullRequest },
  { to: "/agents", label: "Agent Monitoring", icon: Activity },
  { to: "/settings", label: "Settings", icon: Settings },
];
