import { useId, useRef, useState, type ChangeEvent, type DragEvent } from 'react';
import { FileText, Loader2, UploadCloud, X } from 'lucide-react';
import { formatFileSize } from './formatFileSize';

const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024;

interface UploadZoneProps {
  onUpload: (file: File) => Promise<void>;
  isUploading?: boolean;
}

export function UploadZone({ onUpload, isUploading = false }: UploadZoneProps) {
  const validationId = useId();
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const submitting = useRef(false);

  function selectFiles(files: FileList | null) {
    setValidationError(null);
    setSelectedFile(null);
    if (!files?.length) return;
    if (files.length > 1) {
      setValidationError('Choose exactly one PDF at a time.');
      return;
    }
    const file = files[0];
    if (!file.name.toLowerCase().endsWith('.pdf') || !['', 'application/pdf', 'application/octet-stream'].includes(file.type)) {
      setValidationError('Invalid file format. Please upload an academic research paper in PDF format.');
    } else if (file.size === 0) {
      setValidationError('The PDF file is empty. Choose a non-empty PDF.');
    } else if (file.size > MAX_FILE_SIZE_BYTES) {
      setValidationError('File size (' + formatFileSize(file.size) + ') exceeds maximum allowed limit of 25 MB.');
    } else {
      setSelectedFile(file);
    }
  }

  function drop(event: DragEvent<HTMLButtonElement>) {
    event.preventDefault();
    setIsDragOver(false);
    if (!isUploading) selectFiles(event.dataTransfer.files);
  }

  function choose(event: ChangeEvent<HTMLInputElement>) {
    selectFiles(event.target.files);
    // Browsers must allow choosing the same file again after removing it.
    event.target.value = '';
  }

  async function submit() {
    if (!selectedFile || isUploading || submitting.current) return;
    submitting.current = true;
    try { await onUpload(selectedFile); }
    catch { /* The parent displays API failures; preserve the selected file. */ }
    finally { submitting.current = false; }
  }

  return (
    <div className="w-full space-y-4">
      {validationError && <p id={validationId} role="alert" className="rounded-lg border border-rose-200 bg-white px-4 py-3 text-sm leading-6 text-rose-700">{validationError}</p>}
      <input ref={fileInputRef} type="file" accept=".pdf,application/pdf" aria-label="Choose a PDF file" tabIndex={-1}
        data-testid="file-input" onChange={choose} hidden disabled={isUploading} />
      <button type="button" data-testid="dropzone" disabled={isUploading}
        aria-label="Choose PDF" aria-describedby={validationError ? validationId : undefined} aria-invalid={!!validationError}
        onDragOver={event => { event.preventDefault(); if (!isUploading) setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)} onDrop={drop} onClick={() => fileInputRef.current?.click()}
        className={'flex min-h-56 w-full flex-col items-center justify-center rounded-2xl border-2 border-dashed p-6 text-center transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-4 disabled:cursor-wait sm:p-10 '
          + (isDragOver ? 'border-blue-500 bg-blue-50' : 'border-slate-300 bg-white hover:border-blue-400 hover:bg-blue-50/40')}>
        {isUploading ? <>
          <Loader2 size={24} aria-hidden="true" className="text-blue-600 motion-safe:animate-spin" />
          <span role="status" className="mt-3 text-sm font-medium text-slate-700">Uploading your paper…</span>
        </> : <>
          <span className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-600"><UploadCloud size={26} aria-hidden="true" /></span>
          <span className="text-base font-semibold text-slate-900">Drag & Drop your research paper here</span>
          <span className="mt-1 text-sm text-slate-500"><span className="ui-button ui-button-primary mt-2">Choose PDF</span></span>
          <span className="mt-5 text-xs leading-6 text-slate-500">PDF format only · Max 25 MB · One paper at a time</span>
        </>}
      </button>
      {selectedFile && !isUploading && <div className="ui-card flex flex-wrap items-center gap-3 p-4">
        <FileText size={22} aria-hidden="true" className="shrink-0 text-blue-700" />
        <div className="min-w-0 flex-1">
          <p className="break-words text-sm font-medium text-slate-900 [overflow-wrap:anywhere]">{selectedFile.name}</p>
          <p className="mt-0.5 text-xs text-slate-500">{formatFileSize(selectedFile.size)}</p>
        </div>
        <button type="button" aria-label="Remove selected PDF" onClick={() => setSelectedFile(null)}
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600"><X size={18} aria-hidden="true" /></button>
        <button type="button" onClick={() => void submit()}
          className="ui-button ui-button-primary w-full sm:w-auto"><UploadCloud size={16} aria-hidden="true" />Upload paper</button>
      </div>}
    </div>
  );
}
