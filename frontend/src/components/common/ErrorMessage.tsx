import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorMessageProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  title = 'Something went wrong',
  message,
  onRetry,
}) => {
  return (
    <div
      role="alert"
      className="p-4 rounded-xl border border-rose-200 bg-rose-50 text-rose-900 flex items-start gap-3"
    >
      <AlertCircle aria-hidden="true" className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
      <div className="flex-1">
        <h3 className="text-sm font-semibold">{title}</h3>
        <p className="mt-1 text-sm leading-6 text-rose-800">{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            type="button" className="ui-button ui-button-secondary mt-3"
          >
            <RefreshCw aria-hidden="true" className="w-3.5 h-3.5" />
            <span>Try Again</span>
          </button>
        )}
      </div>
    </div>
  );
};
