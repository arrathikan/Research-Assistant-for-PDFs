import { useEffect, useState } from 'react';
import { api, ApiError } from '../../services/api';
import type { DocumentMetadata } from '../../types';
import type { ProcessingStatus } from '../../types/processing';

interface Props { documentId: string; onReady: (document: DocumentMetadata) => void; }
const STEPS: Record<string, string> = { parsing: 'Reading the PDF…', chunking: 'Preparing the paper text…', embedding: 'Preparing document search…', summary: 'Generating the five-part summary…' };

export function ProcessingProgress({ documentId, onReady }: Props) {
  const [job, setJob] = useState<ProcessingStatus | null>(null);
  const [error, setError] = useState('');
  const [refresh, setRefresh] = useState(0);
  const [retrying, setRetrying] = useState(false);
  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    setJob(null); setError('');
    async function load() {
      try {
        const [current, document] = await Promise.all([api.getProcessingStatus(documentId), api.getDocument(documentId)]);
        if (cancelled) return;
        if (current.document_id !== documentId || document.id !== documentId) throw new Error('Document mismatch');
        setJob(current); setError('');
        if (document.status === 'READY' && (current.status === 'COMPLETED' || current.status === 'NOT_SCHEDULED')) {
          onReady(document);
          return;
        }
        if (current.status === 'DEAD_LETTER' || current.status === 'NOT_SCHEDULED') return;
      } catch (failure: unknown) {
        if (cancelled) return;
        setError('Processing status is unavailable. Your stored PDF is preserved.');
        if (failure instanceof ApiError && failure.status === 404) return;
      }
      if (!cancelled) timer = setTimeout(load, 2000);
    }
    timer = setTimeout(load, 2000);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [documentId, onReady, refresh]);

  async function retry() {
    setRetrying(true); setError('');
    try {
      const result = await api.retryProcessing(documentId);
      if (result.document_id !== documentId) throw new Error('Document mismatch');
      setJob(result); setRefresh(value => value + 1);
    } catch {
      setError('Processing could not be restarted. Check the current status before trying again.');
    } finally { setRetrying(false); }
  }
  const description = !job ? 'Waiting for background processing…'
    : job.status === 'RUNNING' ? (job.step && STEPS[job.step]) || 'Processing your PDF…'
    : job.status === 'RETRY_WAIT' ? `Processing will retry automatically (attempt ${job.attempt} of ${job.max_attempts}).`
    : job.status === 'DEAD_LETTER' ? job.requires_review ? 'Processing was interrupted. This document needs review before continuing.' : `Processing failed after ${job.attempt} attempt(s).`
    : job.status === 'NOT_SCHEDULED' ? 'This PDF is stored and has not been scheduled for processing.'
    : job.status === 'COMPLETED' ? 'Checking that the document is ready…'
    : job.stage === 'summary' ? 'Waiting to generate the summary…' : 'Queued for processing…';
  return <div className="mt-3 rounded-lg border border-emerald-200 bg-white/70 p-3 text-xs">
    <p role="status">{description}</p>
    {error && <p role="alert" className="mt-2 text-red-700">{error}</p>}
    {(job?.status === 'NOT_SCHEDULED' || (job?.status === 'DEAD_LETTER' && !job.requires_review)) && <button type="button" disabled={retrying} onClick={() => void retry()} className="mt-2 underline disabled:opacity-50">{retrying ? 'Scheduling…' : job.status === 'NOT_SCHEDULED' ? 'Start processing' : 'Retry processing'}</button>}
    {error && <button type="button" onClick={() => setRefresh(value => value + 1)} className="mt-2 ml-2 underline">Check status again</button>}
  </div>;
}
