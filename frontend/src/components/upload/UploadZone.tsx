import { useId, useRef, useState, type ChangeEvent, type DragEvent } from 'react';
import { FileText, Loader2, UploadCloud, X } from 'lucide-react';
import { formatFileSize } from './formatFileSize';

import { selectPdf } from './selection';

interface UploadZoneProps {
  onUpload: (file: File) => Promise<void>;
  isUploading?: boolean;
  initialFiles?: File[];
  onCancel?: () => void;
  pickerLabel?: string;
}

export function UploadZone({ onUpload, isUploading = false, initialFiles = [], onCancel, pickerLabel = 'Choose PDF' }: UploadZoneProps) {
  const validationId = useId();
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(() => selectPdf(initialFiles).file);
  const [validationError, setValidationError] = useState<string | null>(() => selectPdf(initialFiles).error);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const submitting = useRef(false);

  function selectFiles(files: FileList | null) {
    const selection = selectPdf(files);
    setValidationError(selection.error);
    setSelectedFile(selection.file);
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
        aria-label={pickerLabel} aria-describedby={validationError ? validationId : undefined} aria-invalid={!!validationError}
        onDragOver={event => { event.preventDefault(); if (!isUploading) setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)} onDrop={drop} onClick={() => fileInputRef.current?.click()}
        className={'flex min-h-44 w-full flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 text-center transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-4 disabled:cursor-wait sm:p-7 '
          + (isDragOver ? 'border-brand-500 bg-brand-50' : 'border-stone-400 bg-white hover:border-brand-400 hover:bg-brand-50/40')}>
        {isUploading ? <>
          <Loader2 size={24} aria-hidden="true" className="text-brand-600 motion-safe:animate-spin" />
          <span role="status" className="mt-3 text-sm font-medium text-stone-700">Uploading your paper…</span>
        </> : <>
          <span className="mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-brand-50 text-brand-600"><UploadCloud size={26} aria-hidden="true" /></span>
          <span className="text-base font-semibold text-stone-900">Drag & Drop your research paper here</span>
          <span className="mt-1 text-sm text-stone-500"><span className="ui-button ui-button-primary mt-2">{pickerLabel}</span></span>
          <span className="mt-5 text-xs leading-6 text-stone-500">PDF format only · Max 25 MB · One paper at a time</span>
        </>}
      </button>
      {selectedFile && !isUploading && <div className="ui-card flex flex-wrap items-center gap-3 p-4">
        <FileText size={22} aria-hidden="true" className="shrink-0 text-brand-700" />
        <div className="min-w-0 flex-1">
          <p className="break-words text-sm font-medium text-stone-900 [overflow-wrap:anywhere]">{selectedFile.name}</p>
          <p className="mt-0.5 text-xs text-stone-500">{formatFileSize(selectedFile.size)}</p>
        </div>
        <button type="button" aria-label="Remove selected PDF" onClick={() => setSelectedFile(null)}
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-stone-500 hover:bg-stone-100 hover:text-stone-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600"><X size={18} aria-hidden="true" /></button>

      </div>}
      <div className="flex flex-wrap justify-end gap-2 border-t border-stone-200 pt-4">
        {onCancel && <button type="button" onClick={onCancel} className="ui-button ui-button-secondary">Cancel</button>}
        <button type="button" disabled={!selectedFile || isUploading} onClick={() => void submit()} className="ui-button ui-button-primary"><UploadCloud size={16} aria-hidden="true" />Upload paper</button>
      </div>
    </div>
  );
}
