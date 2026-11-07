import { useState } from "react";
import { Link } from "react-router-dom";
import { Check, ShieldCheck, X } from "lucide-react";
import { Button } from "@/components/common/Button";
import { Card, CardHeader, PageHeader } from "@/components/common/Card";
import { EmptyState, ErrorState } from "@/components/common/EmptyState";
import { ConfirmDialog } from "@/components/common/Modal";
import { TableSkeleton } from "@/components/common/Skeleton";
import { DocumentListItem } from "@/components/documents/DocumentListItem";
import { DocumentPane } from "@/components/documents/DocumentPane";
import { useToast } from "@/hooks/useToast";
import { useWorkspace } from "@/hooks/useWorkspace";
import { approveDocument, rejectDocument } from "@/services/api";
import { toApiError } from "@/services/errors";

const MIN_REASON = 5; // DocumentRejectionRequest.reason min_length
const MAX_REASON = 2000; // DocumentRejectionRequest.reason max_length

export default function ApprovalsPage() {
  const { documents, status, error, refresh, refreshWorkflow } = useWorkspace();
  const toast = useToast();

  const pending = documents.filter((d) => d.approval_status === "PENDING");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const selected = pending.find((d) => d.id === selectedId) ?? pending[0];

  const [dialog, setDialog] = useState<"approve" | "reject" | null>(null);
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const trimmed = reason.trim();
  const reasonValid = trimmed.length >= MIN_REASON && trimmed.length <= MAX_REASON;

  const closeDialog = () => {
    if (submitting) return;
    setDialog(null);
    setReason("");
  };

  async function confirm() {
    if (!selected || !dialog) return;
    const doc = selected;
    setSubmitting(true);
    try {
      if (dialog === "approve") {
        await approveDocument(doc.id);
        toast.success("Document approved", `“${doc.title}” was approved.`);
      } else {
        await rejectDocument(doc.id, trimmed);
        toast.success("Document rejected", `“${doc.title}” was rejected.`);
      }
      setDialog(null);
      setReason("");
      // Workflow status is recalculated by the backend; pull the fresh state.
      await refreshWorkflow(doc.workflow_id);
    } catch (e) {
      const err = toApiError(e);
      toast.error(dialog === "approve" ? "Could not approve document" : "Could not reject document", err.message);
      if (err.status === 409 || err.status === 404) {
        // Already reviewed elsewhere (or removed): sync and close.
        setDialog(null);
        setReason("");
        await refreshWorkflow(doc.workflow_id);
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <PageHeader title="Approvals" description="Review generated documents before they are accepted." />

      {status === "loading" ? (
        <Card>
          <TableSkeleton />
        </Card>
      ) : status === "error" ? (
        <Card>
          <ErrorState message={error ?? "Unable to load documents."} onRetry={() => void refresh()} />
        </Card>
      ) : pending.length === 0 ? (
        <Card>
          <EmptyState
            icon={ShieldCheck}
            title="Nothing awaiting approval"
            description="All generated documents have been reviewed."
            action={
              <Link to="/documents" className="text-sm font-medium text-brand-600 hover:text-brand-700">
                Browse all documents
              </Link>
            }
          />
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[22rem_minmax(0,1fr)]">
          <Card className="flex max-h-[75vh] flex-col overflow-hidden">
            <CardHeader title={`Awaiting approval (${pending.length})`} />
            <ul className="divide-y divide-slate-100 overflow-y-auto">
              {pending.map((d) => (
                <DocumentListItem key={d.id} doc={d} selected={selected?.id === d.id} onSelect={() => setSelectedId(d.id)} />
              ))}
            </ul>
          </Card>

          <div className="min-w-0">
            {selected && (
              <DocumentPane
                doc={selected}
                footer={
                  <div className="flex flex-wrap justify-end gap-2">
                    <Button variant="danger" onClick={() => setDialog("reject")}>
                      <X className="h-4 w-4" /> Reject
                    </Button>
                    <Button onClick={() => setDialog("approve")}>
                      <Check className="h-4 w-4" /> Approve
                    </Button>
                  </div>
                }
              />
            )}
          </div>
        </div>
      )}

      <ConfirmDialog
        open={dialog === "approve"}
        title="Approve this document?"
        description={selected ? `“${selected.title}” will be marked as approved under your API key identity. This cannot be undone.` : undefined}
        confirmLabel="Approve"
        loading={submitting}
        onConfirm={() => void confirm()}
        onCancel={closeDialog}
      />

      <ConfirmDialog
        open={dialog === "reject"}
        title="Reject this document?"
        description={selected ? `“${selected.title}” will be marked as rejected. This cannot be undone.` : undefined}
        confirmLabel="Reject"
        confirmVariant="danger"
        confirmDisabled={!reasonValid}
        loading={submitting}
        onConfirm={() => void confirm()}
        onCancel={closeDialog}
      >
        <label htmlFor="reject-reason" className="mb-1.5 block text-sm font-medium text-slate-700">
          Reason for rejection
        </label>
        <textarea
          id="reject-reason"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          rows={4}
          maxLength={MAX_REASON}
          disabled={submitting}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-rose-500 focus:outline-none focus:ring-2 focus:ring-rose-500/20"
          placeholder="Explain what needs to change (at least 5 characters)"
        />
        <p className={`mt-1 text-xs ${trimmed.length > 0 && !reasonValid ? "text-rose-600" : "text-slate-500"}`}>
          {trimmed.length < MIN_REASON ? `At least ${MIN_REASON} characters required.` : `${trimmed.length}/${MAX_REASON}`}
        </p>
      </ConfirmDialog>
    </>
  );
}
