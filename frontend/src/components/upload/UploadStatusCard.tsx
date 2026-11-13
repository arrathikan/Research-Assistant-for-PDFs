import { useId } from 'react';
import { ArrowUpRight, BookOpen, FileText, Loader2, MessageSquare, RefreshCw } from 'lucide-react';
import { formatFileSize } from './formatFileSize';

export type UploadStage = 'uploading' | 'uploaded' | 'queued' | 'processing' | 'ready' | 'failed';

interface Props {
  filename: string;
  fileSize?: number;
  stage: UploadStage;
  description: string;
  busy?: boolean;
  notice?: string;
  pdfUrl?: string;
  onSummary?: () => void;
  onChat?: () => void;
  onRetry?: () => void;
  retryLabel?: string;
  retrying?: boolean;
  onCheck?: () => void;
  showDocumentActions?: boolean;
}

const BADGES: Record<UploadStage, { label: string; style: string }> = {
  uploading: { label: 'Uploading', style: 'bg-brand-50 text-brand-700 ring-brand-200' },
  uploaded: { label: 'Uploaded', style: 'bg-stone-100 text-stone-700 ring-stone-200' },
  queued: { label: 'Queued', style: 'bg-stone-100 text-stone-700 ring-stone-200' },
  processing: { label: 'Processing', style: 'bg-brand-50 text-brand-700 ring-brand-200' },
  ready: { label: 'Ready', style: 'bg-emerald-50 text-emerald-800 ring-emerald-200' },
  failed: { label: 'Failed', style: 'bg-rose-50 text-rose-800 ring-rose-200' },
};

const ACTION = 'ui-button ui-button-secondary';
const TEXT_ACTION = 'ui-button ui-button-ghost text-brand-700';

export function UploadStatusCard({
  filename, fileSize, stage, description, busy = false, notice, pdfUrl,
  onSummary, onChat, onRetry, retryLabel = 'Retry processing', retrying = false, onCheck, showDocumentActions = true,
}: Props) {
  const headingId = useId();
  const badge = BADGES[stage];
  return (
    <section aria-labelledby={headingId} className="ui-card w-full p-5 sm:p-6">
      <div className="flex items-start gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
          <FileText size={22} aria-hidden="true" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 id={headingId} className="break-words text-sm font-semibold leading-6 text-stone-900 [overflow-wrap:anywhere]">{filename}</h3>
          <p className="mt-0.5 text-xs text-stone-500">PDF{fileSize !== undefined ? ' · ' + formatFileSize(fileSize) : ''}</p>
        </div>
      </div>
      <div role="status" aria-live="polite" aria-atomic="true" className="mt-4">
        <span className={'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ' + badge.style}>
          {busy && <Loader2 size={13} aria-hidden="true" className="motion-safe:animate-spin" />}
          {badge.label}
        </span>
        <p className="mt-2 text-sm leading-6 text-stone-600">{description}</p>
      </div>
      {notice && <p role="alert" className="mt-3 text-sm leading-6 text-rose-700">{notice}</p>}
      {showDocumentActions && <div className="mt-5 grid grid-cols-1 gap-2 border-t border-stone-100 pt-4 sm:grid-cols-3">
        <button type="button" disabled={!onSummary} onClick={onSummary} className={ACTION}><BookOpen size={16} aria-hidden="true" />View Summary</button>
        {pdfUrl
          ? <a href={pdfUrl} target="_blank" rel="noopener noreferrer" className={ACTION}><ArrowUpRight size={16} aria-hidden="true" />Open PDF<span className="sr-only"> (opens in a new tab)</span></a>
          : <button type="button" disabled className={ACTION}><FileText size={16} aria-hidden="true" />Open PDF</button>}
        <button type="button" disabled={!onChat} onClick={onChat} className={ACTION}><MessageSquare size={16} aria-hidden="true" />Chat with Paper</button>
      </div>}
      {(onRetry || onCheck) && <div className="mt-3 flex flex-wrap gap-2">
        {onRetry && <button type="button" disabled={retrying} onClick={onRetry} className={TEXT_ACTION}><RefreshCw size={15} aria-hidden="true" className={retrying ? 'motion-safe:animate-spin' : ''} />{retrying ? 'Restarting…' : retryLabel}</button>}
        {onCheck && <button type="button" disabled={retrying} onClick={onCheck} className={TEXT_ACTION}>Check status again</button>}
      </div>}
    </section>
  );
}
