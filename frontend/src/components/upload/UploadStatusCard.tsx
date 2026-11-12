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
}

const BADGES: Record<UploadStage, { label: string; style: string }> = {
  uploading: { label: 'Uploading', style: 'bg-blue-50 text-blue-700 ring-blue-200' },
  uploaded: { label: 'Uploaded', style: 'bg-slate-100 text-slate-700 ring-slate-200' },
  queued: { label: 'Queued', style: 'bg-slate-100 text-slate-700 ring-slate-200' },
  processing: { label: 'Processing', style: 'bg-blue-50 text-blue-700 ring-blue-200' },
  ready: { label: 'Ready', style: 'bg-emerald-50 text-emerald-800 ring-emerald-200' },
  failed: { label: 'Failed', style: 'bg-rose-50 text-rose-800 ring-rose-200' },
};

const ACTION = 'inline-flex min-h-11 items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:border-slate-200 disabled:bg-slate-50 disabled:text-slate-400';
const TEXT_ACTION = 'inline-flex min-h-11 items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-blue-700 hover:bg-blue-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 disabled:cursor-wait disabled:opacity-60';

export function UploadStatusCard({
  filename, fileSize, stage, description, busy = false, notice, pdfUrl,
  onSummary, onChat, onRetry, retryLabel = 'Retry processing', retrying = false, onCheck,
}: Props) {
  const headingId = useId();
  const badge = BADGES[stage];
  return (
    <section aria-labelledby={headingId} className="w-full rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
      <div className="flex items-start gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
          <FileText size={22} aria-hidden="true" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 id={headingId} className="break-words text-sm font-semibold leading-6 text-slate-900 [overflow-wrap:anywhere]">{filename}</h3>
          <p className="mt-0.5 text-xs text-slate-500">PDF{fileSize !== undefined ? ' · ' + formatFileSize(fileSize) : ''}</p>
        </div>
      </div>
      <div role="status" aria-live="polite" aria-atomic="true" className="mt-4">
        <span className={'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ' + badge.style}>
          {busy && <Loader2 size={13} aria-hidden="true" className="motion-safe:animate-spin" />}
          {badge.label}
        </span>
        <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
      </div>
      {notice && <p role="alert" className="mt-3 text-sm leading-6 text-rose-700">{notice}</p>}
      <div className="mt-5 grid grid-cols-1 gap-2 border-t border-slate-100 pt-4 sm:grid-cols-3">
        <button type="button" disabled={!onSummary} onClick={onSummary} className={ACTION}><BookOpen size={16} aria-hidden="true" />View Summary</button>
        {pdfUrl
          ? <a href={pdfUrl} target="_blank" rel="noopener noreferrer" className={ACTION}><ArrowUpRight size={16} aria-hidden="true" />Open PDF<span className="sr-only"> (opens in a new tab)</span></a>
          : <button type="button" disabled className={ACTION}><FileText size={16} aria-hidden="true" />Open PDF</button>}
        <button type="button" disabled={!onChat} onClick={onChat} className={ACTION}><MessageSquare size={16} aria-hidden="true" />Chat with Paper</button>
      </div>
      {(onRetry || onCheck) && <div className="mt-3 flex flex-wrap gap-2">
        {onRetry && <button type="button" disabled={retrying} onClick={onRetry} className={TEXT_ACTION}><RefreshCw size={15} aria-hidden="true" className={retrying ? 'motion-safe:animate-spin' : ''} />{retrying ? 'Restarting…' : retryLabel}</button>}
        {onCheck && <button type="button" disabled={retrying} onClick={onCheck} className={TEXT_ACTION}>Check status again</button>}
      </div>}
    </section>
  );
}
