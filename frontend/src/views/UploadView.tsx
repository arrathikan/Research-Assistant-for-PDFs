import React, { useState } from 'react';
import { DocumentSummaryPanel } from '../components/summary/DocumentSummaryPanel';
import { UploadZone } from '../components/upload/UploadZone';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { DocumentMetadata, UploadResponse } from '../types';
import { api } from '../services/api';
import { ShieldCheck, Zap, Sparkles } from 'lucide-react';

interface UploadViewProps {
  onUploadSuccess: (doc: DocumentMetadata) => void;
}

export const UploadView: React.FC<UploadViewProps> = ({ onUploadSuccess }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [showSummary, setShowSummary] = useState(false);
  const [result, setResult] = useState<UploadResponse | null>(null);

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    setError(null);
    setResult(null);
    setShowSummary(false);

    try {
      const response = await api.uploadDocument(file);
      setResult(response);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 max-w-4xl mx-auto flex flex-col justify-center">
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-semibold mb-3 border border-blue-200">
          <Sparkles className="w-3.5 h-3.5 text-blue-600" />
          <span>Research Paper Upload</span>
        </div>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Upload Research Paper</h2>
        <p className="text-xs text-slate-500 mt-2 max-w-md mx-auto">
          Upload one academic PDF. Your original file is saved and checked for exact duplicates. Summary and chat become available after processing.
        </p>
      </div>

      {error && (
        <div className="mb-6 max-w-xl mx-auto">
          <ErrorMessage
            title="Upload Failed"
            message={error}
            onRetry={() => setError(null)}
          />
        </div>
      )}

      {result && (
        <div role="status" className="mb-6 p-4 max-w-xl w-full mx-auto bg-emerald-50 border border-emerald-200 rounded-xl text-sm text-emerald-900">
          <h3 className="font-semibold">{result.is_duplicate ? 'Duplicate detected' : 'Upload successful'}</h3>
          <p className="mt-1">{result.message}</p>
          <p className="mt-1">{result.document.filename} · Status: {result.document.status}</p>
          <p className="text-xs mt-1">Document ID: {result.document.id}</p>
          {result.document.status === 'PENDING' && (
            <p className="mt-2 text-xs">Your PDF is saved. Summary and chat will be available after processing.</p>
          )}
          {result.document.status === 'FAILED' && (
            <p className="mt-2 text-xs">This file is already stored, but its processing failed.</p>
          )}
          {result.document.id && (
            <a href={api.getPdfStreamUrl(result.document.id)} target="_blank" rel="noopener noreferrer" className="inline-block mt-3 underline">Open original PDF</a>
          )}
          {result.document.id && result.document.status !== 'READY' && (
            <button type="button" className="block mt-3 underline" onClick={() => setShowSummary(value => !value)}>
              {showSummary ? 'Hide summary' : 'View summary'}
            </button>
          )}
          {result.document.status === 'READY' && (
            <button className="block mt-3 underline" onClick={() => onUploadSuccess(result.document)}>Open workspace</button>
          )}
        </div>
      )}

      {showSummary && result?.document.id && (
        <DocumentSummaryPanel documentId={result.document.id} filename={result.document.filename} />
      )}

      <UploadZone onUpload={handleUpload} isUploading={isUploading} />

      {/* Feature highlights */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-xl mx-auto mt-10 text-xs text-slate-600">
        <div className="p-3.5 bg-white rounded-xl border border-slate-200 flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          <div>
            <span className="font-semibold text-slate-800">SHA-256 Deduplication</span>
            <p className="text-[11px] text-slate-500 mt-0.5">Identical papers are detected instantly to prevent redundant parsing and re-embedding.</p>
          </div>
        </div>

        <div className="p-3.5 bg-white rounded-xl border border-slate-200 flex items-start gap-3">
          <Zap className="w-5 h-5 text-amber-500 flex-shrink-0" />
          <div>
            <span className="font-semibold text-slate-800">Original PDF preserved</span>
            <p className="text-[11px] text-slate-500 mt-0.5">Open the original file after uploading. Its page count and processing status are stored with the document.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
