import React, { ReactNode } from 'react';
import { FileQuestion } from 'lucide-react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
}) => {
  return (
    <div
      data-testid="empty-state"
      className="flex flex-col items-center justify-center ui-card w-full px-6 py-12 text-center sm:py-16"
    >
      <div className="p-3.5 bg-slate-100 rounded-full text-slate-500 mb-3.5">
        {icon || <FileQuestion aria-hidden="true" className="w-7 h-7" />}
      </div>
      <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
      <p className="mt-2 max-w-md text-sm leading-6 text-slate-600">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
};
