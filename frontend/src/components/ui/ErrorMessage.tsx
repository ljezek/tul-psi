import { AlertCircle } from 'lucide-react';
import { Button } from './Button';

export interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
}

export const ErrorMessage = ({ message, onRetry, retryLabel }: ErrorMessageProps) => {
  return (
    <div className="flex flex-col items-center justify-center p-6 bg-red-50 text-red-800 rounded-lg border border-red-200">
      <AlertCircle className="w-8 h-8 text-red-500 mb-3" />
      <p className="text-center mb-4">{message}</p>
      {onRetry && retryLabel && (
        <Button variant="outline" size="sm" onClick={onRetry} className="bg-white border-red-300 text-red-700 hover:bg-red-50">
          {retryLabel}
        </Button>
      )}
    </div>
  );
};
