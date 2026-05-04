import { Component, ReactNode, ErrorInfo } from 'react';
import { AlertCircle } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('[ErrorBoundary]', error, info.componentStack);
  }

  render(): ReactNode {
    const { error } = this.state;
    if (!error) return this.props.children;

    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-sm border border-slate-200 p-8 text-center">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h1 className="text-xl font-bold text-slate-800 mb-2">Something went wrong</h1>
          <p className="text-slate-500 text-sm mb-6">
            An unexpected error occurred. Reload the page to try again.
          </p>
          <pre className="font-mono text-xs text-red-600 bg-red-50 rounded-lg p-3 mb-6 text-left whitespace-pre-wrap break-all">
            {error.message}
          </pre>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-tul-blue text-white rounded-lg text-sm font-semibold hover:bg-tul-blue/90 transition-colors"
          >
            Reload page
          </button>
        </div>
      </div>
    );
  }
}
