import type { AgentName } from "@/types/api";
import { humanize } from "./utils";

export type Tone = "neutral" | "info" | "success" | "warning" | "danger";

const TONES: Record<string, Tone> = {
  PENDING: "neutral",
  RUNNING: "info",
  COMPLETED: "success",
  AWAITING_APPROVAL: "warning",
  APPROVED: "success",
  REJECTED: "danger",
  PARTIAL: "warning",
  FAILED: "danger",
  INFO: "info",
  LOW: "neutral",
  MEDIUM: "warning",
  HIGH: "danger",
  CRITICAL: "danger",
};

export function toneFor(status: string): Tone {
  return TONES[status.toUpperCase()] ?? "neutral";
}

export function statusLabel(status: string): string {
  return humanize(status);
}

/** Hex colors for charts, keyed by tone-ish status. */
export const STATUS_COLORS: Record<string, string> = {
  APPROVED: "#16a34a",
  COMPLETED: "#0ea5e9",
  AWAITING_APPROVAL: "#f59e0b",
  PENDING: "#94a3b8",
  RUNNING: "#6366f1",
  PARTIAL: "#fb923c",
  REJECTED: "#e11d48",
  FAILED: "#dc2626",
};

export const WORKFLOW_STATUSES = [
  "PENDING",
  "RUNNING",
  "COMPLETED",
  "AWAITING_APPROVAL",
  "APPROVED",
  "REJECTED",
  "PARTIAL",
  "FAILED",
] as const;

export const AGENTS: { name: AgentName; label: string; description: string }[] = [
  { name: "documentation", label: "Documentation Agent", description: "Generates technical documentation" },
  { name: "code_review", label: "Code Review Agent", description: "Finds issues and risks in code changes" },
  { name: "team_intelligence", label: "Team Intelligence Agent", description: "Summarizes decisions and action items" },
];

export function agentLabel(name: string): string {
  return AGENTS.find((a) => a.name === name)?.label ?? humanize(name);
}
