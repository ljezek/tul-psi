import { Component, ReactNode, ErrorInfo } from 'react';
import { AlertCircle } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

export interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryInnerProps {
  children: ReactNode;
  t: (key: string) => string;
}

interface State {
  error: Error | null;
}

class ErrorBoundaryInner extends Component<ErrorBoundaryInnerProps, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('[ErrorBoundary]', error, info.componentStack);
  }

  render(): ReactNode {
    const { error, t } = { ...this.state, t: this.props.t };
    if (!error) return this.props.children;

    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-sm border border-slate-200 p-8 text-center">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h1 className="text-xl font-bold text-slate-800 mb-2">{t('error.unexpected_title')}</h1>
          <p className="text-slate-500 text-sm mb-6">{t('error.unexpected_desc')}</p>
          {import.meta.env.DEV && (
            <pre className="font-mono text-xs text-red-600 bg-red-50 rounded-lg p-3 mb-6 text-left whitespace-pre-wrap break-all">
              {error.message}
            </pre>
          )}
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-tul-blue text-white rounded-lg text-sm font-semibold hover:bg-tul-blue/90 transition-colors"
          >
            {t('error.reload')}
          </button>
        </div>
      </div>
    );
  }
}

export function ErrorBoundary({ children }: ErrorBoundaryProps) {
  const { t } = useLanguage();
  return <ErrorBoundaryInner t={t}>{children}</ErrorBoundaryInner>;
}
