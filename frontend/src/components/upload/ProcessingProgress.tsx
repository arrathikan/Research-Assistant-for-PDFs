import { useEffect, useRef, useState } from 'react';
import { api, ApiError } from '../../services/api';
import type { DocumentMetadata, WorkspaceTab } from '../../types';
import type { ProcessingStatus } from '../../types/processing';
import { UploadStatusCard, type UploadStage } from './UploadStatusCard';

interface Props {
  document: DocumentMetadata;
  onOpen: (document: DocumentMetadata, tab: WorkspaceTab) => void;
  onUpdate?: (document: DocumentMetadata, ready: boolean) => void;
  showDocumentActions?: boolean;
}

const STEPS: Record<string, string> = {
  parsing: 'Reading your PDF and organizing its content.',
  chunking: 'Preparing your paper for analysis.',
  embedding: 'Preparing your paper for search and questions.',
  summary: 'Writing your research summary. Chat is available once search is ready.',
};

// Keyed state also protects callers that switch documents without unmounting.
export function ProcessingProgress(props: Props) {
  return <DocumentProcessing key={props.document.id} {...props} />;
}

function DocumentProcessing({ document: initialDocument, onOpen, onUpdate, showDocumentActions = true }: Props) {
  const updateCallback = useRef(onUpdate);
  updateCallback.current = onUpdate;
  const [document, setDocument] = useState(initialDocument);
  const [job, setJob] = useState<ProcessingStatus | null>(null);
  const [summaryAvailable, setSummaryAvailable] = useState(false);
  const [notice, setNotice] = useState('');
  const [refresh, setRefresh] = useState(0);
  const [retrying, setRetrying] = useState(false);
  const mounted = useRef(true);
  const documentId = initialDocument.id;

  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    if (!documentId || retrying) return;
    const id = documentId;

    async function load() {
      try {
        const [current, metadata] = await Promise.all([api.getProcessingStatus(id), api.getDocument(id)]);
        if (cancelled) return;
        if (current.document_id !== id || metadata.id !== id) throw new Error('Document mismatch');
        setJob(current);
        setDocument(metadata);
        setNotice('');
        setSummaryAvailable(false);
        updateCallback.current?.(metadata, false);
        const completed = current.status === 'COMPLETED' || current.status === 'NOT_SCHEDULED';
        if (metadata.status === 'READY' && completed) {
          // A READY label alone does not guarantee the current summary can be read.
          const summary = await api.getDocumentSummary(id);
          if (cancelled) return;
          if (summary.document_id !== id) throw new Error('Document mismatch');
          setSummaryAvailable(true);
          if (metadata.embedding_status === 'COMPLETED') { updateCallback.current?.(metadata, true); return; }
        }
        if (current.status === 'DEAD_LETTER' || current.status === 'NOT_SCHEDULED') return;
      } catch (failure: unknown) {
        if (cancelled) return;
        setNotice('We couldn’t confirm the latest status. Your PDF is saved. Please check again shortly.');
        if (failure instanceof ApiError && failure.status === 404) return;
      }
      if (!cancelled) timer = setTimeout(load, 2000);
    }
    timer = setTimeout(load, 2000);
    return () => { cancelled = true; if (timer) clearTimeout(timer); };
  }, [documentId, refresh, retrying]);

  async function retry() {
    if (!documentId || retrying) return;
    setRetrying(true);
    setNotice('');
    try {
      const result = await api.retryProcessing(documentId);
      if (!mounted.current) return;
      if (result.document_id !== documentId) throw new Error('Document mismatch');
      setJob(result);
      setSummaryAvailable(false);
      setRefresh(value => value + 1);
    } catch {
      if (mounted.current) setNotice('Analysis couldn’t be restarted. Check the current status before trying again.');
    } finally {
      if (mounted.current) setRetrying(false);
    }
  }

  const activeJob = job && ['QUEUED', 'RUNNING', 'RETRY_WAIT'].includes(job.status);
  const completed = job?.status === 'COMPLETED' || job?.status === 'NOT_SCHEDULED';
  const ready = document.status === 'READY' && completed && summaryAvailable && document.embedding_status === 'COMPLETED';
  const failed = job?.status === 'DEAD_LETTER' || (document.status === 'FAILED' && !activeJob);
  let stage: UploadStage = 'uploaded';
  let description = 'Your PDF is saved. Checking its processing status…';
  if (ready) {
    stage = 'ready';
    description = 'Your paper is ready. Explore the summary or ask a question.';
  } else if (failed) {
    stage = 'failed';
    description = job?.requires_review
      ? 'Processing was interrupted and needs review before it can continue. Your PDF is saved.'
      : 'We couldn’t finish analyzing this paper. Your original PDF is saved.';
  } else if (job?.status === 'NOT_SCHEDULED') {
    description = 'Your PDF is saved. Start analysis to prepare your summary and chat.';
  } else if (job?.status === 'QUEUED' && job.stage !== 'summary') {
    stage = 'queued';
    description = 'Your paper is saved and waiting to be analyzed.';
  } else if (job?.status === 'RETRY_WAIT') {
    stage = 'processing';
    description = 'Analysis will retry automatically. Your PDF is saved.';
  } else if (job?.status === 'RUNNING' || job?.status === 'COMPLETED' || job?.stage === 'summary' || document.status !== 'PENDING') {
    stage = 'processing';
    description = (job?.step && STEPS[job.step]) || 'Your paper is being analyzed. Summary and chat will be available shortly.';
  }

  const canRetry = job?.status === 'NOT_SCHEDULED' && document.status !== 'READY'
    || job?.status === 'DEAD_LETTER' && !job.requires_review;
  return <UploadStatusCard
    showDocumentActions={showDocumentActions}
    filename={document.filename}
    fileSize={document.file_size_bytes}
    stage={stage}
    description={description}
    busy={retrying || (!notice && !failed && !ready && job?.status !== 'NOT_SCHEDULED')}
    notice={notice}
    pdfUrl={documentId ? api.getPdfStreamUrl(documentId) : undefined}
    onSummary={summaryAvailable ? () => onOpen(document, 'summary') : undefined}
    onChat={document.embedding_status === 'COMPLETED' ? () => onOpen(document, 'chat') : undefined}
    onRetry={canRetry ? () => void retry() : undefined}
    retryLabel={job?.status === 'NOT_SCHEDULED' ? 'Start processing' : 'Retry processing'}
    retrying={retrying}
    onCheck={notice ? () => { setNotice(''); setRefresh(value => value + 1); } : undefined}
  />;
}
