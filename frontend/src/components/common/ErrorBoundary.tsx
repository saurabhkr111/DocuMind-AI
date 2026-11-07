import { Component, type ErrorInfo, type ReactNode } from "react";
import { ErrorState } from "./EmptyState";

interface Props {
  children: ReactNode;
  /** Changing this value resets the boundary (e.g. pass the current route). */
  resetKey?: string;
}
interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("UI error:", error, info.componentStack);
  }

  componentDidUpdate(prev: Props) {
    if (this.state.error && prev.resetKey !== this.props.resetKey) this.setState({ error: null });
  }

  render() {
    if (this.state.error) {
      return <ErrorState message={this.state.error.message || "The page failed to render."} onRetry={() => this.setState({ error: null })} />;
    }
    return this.props.children;
  }
}
