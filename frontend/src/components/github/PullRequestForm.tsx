import { useState, type FormEvent, type ReactNode } from "react";
import { GitPullRequest } from "lucide-react";
import { Button } from "@/components/common/Button";

export interface PullRequestInput {
  owner: string;
  repo: string;
  pullNumber: number;
}

// GitHub owner: alphanumerics/hyphens; repo: alphanumerics, ".", "_", "-".
const OWNER_RE = /^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$/;
const REPO_RE = /^[A-Za-z0-9._-]{1,100}$/;

interface Errors {
  owner?: string;
  repo?: string;
  pull?: string;
}

function validate(owner: string, repo: string, pull: string): Errors {
  const errors: Errors = {};
  if (!owner) errors.owner = "Repository owner is required.";
  else if (!OWNER_RE.test(owner)) errors.owner = "Use letters, numbers and hyphens only (max 39 characters).";

  if (!repo) errors.repo = "Repository name is required.";
  else if (!REPO_RE.test(repo) || repo === "." || repo === "..") errors.repo = "Use letters, numbers, dots, hyphens and underscores only.";

  if (!pull) errors.pull = "Pull request number is required.";
  else if (!/^\d+$/.test(pull) || Number(pull) < 1 || !Number.isSafeInteger(Number(pull))) errors.pull = "Enter a whole number of 1 or more.";
  return errors;
}

function Field({ id, label, error, children }: { id: string; label: string; error?: string; children: ReactNode }) {
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-slate-700">
        {label}
      </label>
      {children}
      {error && (
        <p id={`${id}-error`} className="mt-1 text-xs text-rose-600">
          {error}
        </p>
      )}
    </div>
  );
}

const inputClass = (invalid: boolean) =>
  `w-full rounded-lg border bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 disabled:bg-slate-50 ${
    invalid ? "border-rose-400 focus:ring-rose-500/20" : "border-slate-300 focus:border-brand-500 focus:ring-brand-500/20"
  }`;

export function PullRequestForm({ onSubmit, loading }: { onSubmit: (input: PullRequestInput) => void; loading: boolean }) {
  const [owner, setOwner] = useState("");
  const [repo, setRepo] = useState("");
  const [pull, setPull] = useState("");
  const [errors, setErrors] = useState<Errors>({});

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const o = owner.trim();
    const r = repo.trim();
    const p = pull.trim();
    const found = validate(o, r, p);
    setErrors(found);
    if (Object.keys(found).length > 0) return;
    onSubmit({ owner: o, repo: r, pullNumber: Number(p) });
  };

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4 p-5">
      <Field id="owner" label="Repository owner" error={errors.owner}>
        <input
          id="owner"
          value={owner}
          onChange={(e) => setOwner(e.target.value)}
          placeholder="e.g. octocat"
          autoComplete="off"
          disabled={loading}
          aria-invalid={!!errors.owner}
          aria-describedby={errors.owner ? "owner-error" : undefined}
          className={inputClass(!!errors.owner)}
        />
      </Field>
      <Field id="repo" label="Repository name" error={errors.repo}>
        <input
          id="repo"
          value={repo}
          onChange={(e) => setRepo(e.target.value)}
          placeholder="e.g. hello-world"
          autoComplete="off"
          disabled={loading}
          aria-invalid={!!errors.repo}
          aria-describedby={errors.repo ? "repo-error" : undefined}
          className={inputClass(!!errors.repo)}
        />
      </Field>
      <Field id="pull" label="Pull request number" error={errors.pull}>
        <input
          id="pull"
          inputMode="numeric"
          value={pull}
          onChange={(e) => setPull(e.target.value)}
          placeholder="e.g. 42"
          autoComplete="off"
          disabled={loading}
          aria-invalid={!!errors.pull}
          aria-describedby={errors.pull ? "pull-error" : undefined}
          className={inputClass(!!errors.pull)}
        />
      </Field>
      <Button type="submit" loading={loading} className="w-full">
        {!loading && <GitPullRequest className="h-4 w-4" />}
        {loading ? "Analyzing pull request…" : "Analyze pull request"}
      </Button>
    </form>
  );
}
