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
      className="flex flex-col items-center justify-center ui-card w-full px-6 py-9 text-center sm:py-12"
    >
      <div className="p-3 bg-brand-50 rounded-xl text-brand-700 mb-4">
        {icon || <FileQuestion aria-hidden="true" className="w-7 h-7" />}
      </div>
      <h3 className="text-lg font-semibold text-stone-900">{title}</h3>
      <p className="mt-2 max-w-md text-sm leading-6 text-stone-600">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
};
