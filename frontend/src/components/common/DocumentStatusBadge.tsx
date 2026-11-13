import { CheckCircle2, RefreshCw, CircleAlert, Clock3 } from 'lucide-react';
import type { DocumentStatus } from '../../types';

const STATES = {
  READY: { label: 'Ready', icon: CheckCircle2, style: 'border-green-200 bg-green-50 text-green-800' },
  FAILED: { label: 'Failed', icon: CircleAlert, style: 'border-red-200 bg-red-50 text-red-800' },
  PENDING: { label: 'Uploaded', icon: Clock3, style: 'border-stone-200 bg-stone-50 text-stone-600' },
} as const;

export function DocumentStatusBadge({ status, testId }: { status: DocumentStatus; testId?: string }) {
  const state = status in STATES ? STATES[status as keyof typeof STATES]
    : { label: 'Processing', icon: RefreshCw, style: 'border-amber-200 bg-amber-50 text-amber-800' };
  const Icon = state.icon;
  return <span data-testid={testId} data-status={status} className={'ui-badge whitespace-nowrap ' + state.style}>
    <Icon size={13} aria-hidden="true" />{state.label}
  </span>;
}
