import { useEffect, useRef, useState } from 'react';
import { Files, UploadCloud } from 'lucide-react';
import { Modal } from '../components/common/Modal';
import { ProcessingProgress } from '../components/upload/ProcessingProgress';
import { UploadStatusCard } from '../components/upload/UploadStatusCard';
import { UploadZone } from '../components/upload/UploadZone';
import { PageContainer } from '../components/layout/PageContainer';
import type { DocumentMetadata, UploadResponse, WorkspaceTab } from '../types';
import { api, ApiError } from '../services/api';

interface UploadViewProps {
  active?: boolean;
  onUploadSuccess: (doc: DocumentMetadata, tab?: WorkspaceTab) => void;
  onStored?: (doc: DocumentMetadata) => void;
  onGoToDashboard?: () => void;
  onModalChange?: (open: boolean) => void;
}

/** App keeps this controller mounted so closing a dialog never cancels an upload. */
export function UploadView({ active = true, onUploadSuccess, onStored, onGoToDashboard, onModalChange }: UploadViewProps) {
  const [open, setOpen] = useState(false);
  const [initialFiles, setInitialFiles] = useState<File[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [failure, setFailure] = useState<{ message: string; retryable: boolean } | null>(null);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [ready, setReady] = useState<DocumentMetadata | null>(null);
  const inFlight = useRef(false);
  useEffect(() => { onModalChange?.(open); return () => onModalChange?.(false); }, [open, onModalChange]);

  function begin(files: File[] = []) {
    if (!inFlight.current) {
      setInitialFiles(files); setFile(null); setResult(null); setFailure(null); setReady(null);
    }
    setOpen(true);
  }
  async function upload(selected: File) {
    if (inFlight.current) return;
    inFlight.current = true; setFile(selected); setIsUploading(true); setFailure(null); setResult(null); setReady(null);
    try {
      const response = await api.uploadDocument(selected);
      if (!response.document.id || !/^[0-9a-f]{24}$/i.test(response.document.id)) throw new Error('Invalid document response');
      setResult(response);
      onStored?.(response.document);
    } catch (error: unknown) {
      const invalid = error instanceof ApiError && [400, 413, 415, 422].includes(error.status);
      setFailure({ message: error instanceof ApiError && error.status === 413
        ? 'This PDF exceeds the 25 MB limit. Please choose a smaller file.'
        : invalid ? 'This PDF could not be accepted. Choose a valid PDF that is not password-protected.'
        : 'We couldn’t upload your paper. Check your connection and try again.', retryable: !invalid });
    } finally { setIsUploading(false); inFlight.current = false; }
  }
  function updateDocument(document: DocumentMetadata, confirmedReady: boolean) {
    onStored?.(document); setReady(confirmedReady ? document : null);
  }
  function openWorkspace(document: DocumentMetadata, tab: WorkspaceTab = 'summary') {
    setOpen(false); onUploadSuccess(document, tab);
  }
  return <>
    {active && <PageContainer>
      <div className="mx-auto min-w-0 w-full max-w-5xl">
        <header className="mb-6">
          <p className="ui-eyebrow mb-2">Add to your library</p>
          <h1 className="ui-page-title">Upload a research paper</h1>
          <p className="mt-2 text-sm leading-6 text-stone-600">Turn your PDF into a structured summary and a conversation grounded in your sources.</p>
        </header>
        <button type="button" data-testid="main-upload-trigger" aria-haspopup="dialog" onClick={() => begin()}
          onDragOver={event => event.preventDefault()} onDrop={event => { event.preventDefault(); begin(Array.from(event.dataTransfer.files)); }}
          className="flex min-h-56 w-full flex-col items-center justify-center gap-4 rounded-xl border-2 border-dashed border-stone-400 bg-white p-6 text-center hover:border-brand-400 hover:bg-brand-50/40 sm:p-10">
          <span className="flex h-14 w-14 items-center justify-center rounded-xl bg-brand-50 text-brand-700"><UploadCloud size={26} aria-hidden="true" /></span>
          <span className="text-base font-semibold text-stone-900">Drag &amp; Drop your research paper here</span>
          <span className="ui-button ui-button-primary">{isUploading ? 'View upload progress' : 'Choose PDF'}</span>
          <span className="text-xs text-stone-500">PDF format only · Max 25 MB · One paper at a time</span>
        </button>
        {isUploading && !open && <p role="status" className="mt-3 text-sm text-stone-600">Your upload is continuing in the background.</p>}
        <p className="mt-5 flex items-start gap-2 text-xs leading-6 text-stone-600">
          <Files size={16} aria-hidden="true" className="mt-1 shrink-0" />
          We keep your original PDF and reuse identical papers already in your library.
        </p>
      </div>
    </PageContainer>}
    <Modal open={open} onClose={() => setOpen(false)} closeLabel="Close upload"
      title={result ? 'Paper uploaded successfully' : 'Upload Research Paper'}
      description={result ? 'Your research paper has been added to your library.' : 'Add a PDF to your research library.'}>
      {open && (result ? <>
        <ProcessingProgress document={result.document} onOpen={openWorkspace} onUpdate={updateDocument} showDocumentActions={false} />
        <div className="mt-5 flex flex-wrap justify-end gap-2">
          {ready && <button type="button" onClick={() => openWorkspace(ready)} className="ui-button ui-button-secondary">Open Workspace</button>}
          {onGoToDashboard && <button type="button" onClick={() => { setOpen(false); onGoToDashboard(); }} className="ui-button ui-button-secondary">Go to Dashboard</button>}
          <button type="button" onClick={() => setOpen(false)} className="ui-button ui-button-primary">Done</button>
        </div>
      </> : file ? <>
        <UploadStatusCard filename={file.name} fileSize={file.size} stage={isUploading ? 'uploading' : 'failed'} busy={isUploading} showDocumentActions={false}
          description={isUploading ? 'Uploading your PDF. You can close this window; your upload will continue.' : failure?.message || 'The upload could not be completed.'}
          onRetry={failure?.retryable ? () => void upload(file) : undefined} retryLabel="Retry upload" />
        {!isUploading && <button type="button" onClick={() => { setFile(null); setFailure(null); setInitialFiles([]); }} className="ui-button ui-button-secondary mt-4">Choose a different PDF</button>}
      </> : <UploadZone initialFiles={initialFiles} pickerLabel="Browse Files" onUpload={upload} onCancel={() => setOpen(false)} />)}
    </Modal>
  </>;
}
