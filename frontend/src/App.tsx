import { Route, Routes } from "react-router-dom";
import { ToastProvider } from "@/hooks/useToast";
import { WorkspaceProvider } from "@/hooks/useWorkspace";
import { AppLayout } from "@/components/layout/AppLayout";
import { EmptyState } from "@/components/common/EmptyState";
import { Link } from "react-router-dom";
import OverviewPage from "@/pages/OverviewPage";
import WorkflowsPage from "@/pages/WorkflowsPage";
import WorkflowDetailsPage from "@/pages/WorkflowDetailsPage";
import DocumentsPage from "@/pages/DocumentsPage";
import ApprovalsPage from "@/pages/ApprovalsPage";
import GitHubPage from "@/pages/GitHubPage";
import AgentsPage from "@/pages/AgentsPage";
import SettingsPage from "@/pages/SettingsPage";

function NotFound() {
  return (
    <EmptyState
      title="Page not found"
      description="The page you are looking for does not exist."
      action={
        <Link to="/" className="text-sm font-medium text-brand-600 hover:text-brand-700">
          Back to overview
        </Link>
      }
    />
  );
}

export default function App() {
  return (
    <ToastProvider>
      <WorkspaceProvider>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<OverviewPage />} />
            <Route path="workflows" element={<WorkflowsPage />} />
            <Route path="workflows/:workflowId" element={<WorkflowDetailsPage />} />
            <Route path="documents" element={<DocumentsPage />} />
            <Route path="documents/:documentId" element={<DocumentsPage />} />
            <Route path="approvals" element={<ApprovalsPage />} />
            <Route path="github" element={<GitHubPage />} />
            <Route path="agents" element={<AgentsPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </WorkspaceProvider>
    </ToastProvider>
  );
}
