import { useRef, useState } from 'react';
import { ArrowLeft, Files, ShieldCheck, Sparkles } from 'lucide-react';
import { ProcessingProgress } from '../components/upload/ProcessingProgress';
import { UploadStatusCard } from '../components/upload/UploadStatusCard';
import { UploadZone } from '../components/upload/UploadZone';
import { PageContainer } from '../components/layout/PageContainer';
import type { DocumentMetadata, UploadResponse, WorkspaceTab } from '../types';
import { api, ApiError } from '../services/api';

interface UploadViewProps {
  onUploadSuccess: (doc: DocumentMetadata, tab?: WorkspaceTab) => void;
}

export function UploadView({ onUploadSuccess }: UploadViewProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [failure, setFailure] = useState<{ message: string; retryable: boolean } | null>(null);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const inFlight = useRef(false);

  async function upload(selected: File) {
    if (inFlight.current) return;
    inFlight.current = true;
    setFile(selected);
    setIsUploading(true);
    setFailure(null);
    setResult(null);
    try {
      const response = await api.uploadDocument(selected);
      if (!response.document.id || !/^[0-9a-f]{24}$/i.test(response.document.id)) throw new Error('Invalid document response');
      setResult(response);
    } catch (error: unknown) {
      const invalid = error instanceof ApiError && [400, 413, 415, 422].includes(error.status);
      setFailure({
        message: error instanceof ApiError && error.status === 413
          ? 'This PDF exceeds the 25 MB limit. Please choose a smaller file.'
          : invalid
            ? 'This PDF could not be accepted. Choose a valid PDF that is not password-protected.'
            : 'We couldn’t upload your paper. Check your connection and try again.',
        retryable: !invalid,
      });
    } finally {
      setIsUploading(false);
      inFlight.current = false;
    }
  }

  function startAnother() {
    if (inFlight.current) return;
    setResult(null);
    setFile(null);
    setFailure(null);
  }

  return (
    <PageContainer>
      <div className="mx-auto min-w-0 w-full max-w-3xl">
        <header className="mb-6 text-center">
          <div className="mb-3 inline-flex items-center gap-1.5 rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
            <Sparkles size={14} aria-hidden="true" />Your research, made clearer
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">Upload a research paper</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">Turn your PDF into a structured summary and a conversation grounded in your sources.</p>
        </header>
        <div className="min-w-0 w-full">
          {result ? <ProcessingProgress document={result.document} onOpen={onUploadSuccess} />
            : file ? <UploadStatusCard filename={file.name} fileSize={file.size}
                stage={isUploading ? 'uploading' : 'failed'} busy={isUploading}
                description={isUploading ? 'Uploading your PDF. This may take a moment.' : failure?.message || 'The upload could not be completed.'}
                onRetry={failure?.retryable ? () => void upload(file) : undefined} retryLabel="Retry upload" />
            : <UploadZone onUpload={upload} />}
          {(result || failure) && <button type="button" onClick={startAnother}
            className="mt-4 inline-flex min-h-11 items-center gap-2 rounded-lg px-2 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2">
            <ArrowLeft size={15} aria-hidden="true" />{result ? 'Upload another paper' : 'Choose a different PDF'}
          </button>}
          <div className="mt-6 grid grid-cols-1 gap-4 border-t border-slate-200 pt-5 text-xs leading-5 text-slate-500 sm:grid-cols-2">
            <p className="flex items-start gap-2"><ShieldCheck size={17} aria-hidden="true" className="mt-0.5 shrink-0 text-blue-600" /><span><strong className="font-medium text-slate-700">Your original stays intact.</strong><br />Open the stored PDF at any time.</span></p>
            <p className="flex items-start gap-2"><Files size={17} aria-hidden="true" className="mt-0.5 shrink-0 text-blue-600" /><span><strong className="font-medium text-slate-700">Already uploaded? We’ll reuse it.</strong><br />Identical papers are recognized automatically.</span></p>
          </div>
        </div>
      </div>
    </PageContainer>
  );
}
