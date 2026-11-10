import React, { useState, useRef, DragEvent, ChangeEvent } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertTriangle, X } from 'lucide-react';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorMessage } from '../common/ErrorMessage';

const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024; // 25 MB

interface UploadZoneProps {
  onUpload: (file: File) => Promise<void>;
  isUploading?: boolean;
}

export const UploadZone: React.FC<UploadZoneProps> = ({ onUpload, isUploading = false }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): boolean => {
    setValidationError(null);

    // Validate MIME type and extension
    const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
    if (!isPdf) {
      setValidationError('Invalid file format. Please upload an academic research paper in PDF format.');
      return false;
    }

    // Validate size limit (25 MB)
    if (file.size > MAX_FILE_SIZE_BYTES) {
      const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
      setValidationError(`File size (${sizeMB} MB) exceeds maximum allowed limit of 25 MB.`);
      return false;
    }

    return true;
  };

  const handleFileSelection = (file: File) => {
    if (validateFile(file)) {
      setSelectedFile(file);
    } else {
      setSelectedFile(null);
    }
  };

  const onDragOverHandler = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isUploading) setIsDragOver(true);
  };

  const onDragLeaveHandler = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const onDropHandler = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (isUploading) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const onFileInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelection(e.target.files[0]);
    }
  };

  const handleSubmit = async () => {
    if (!selectedFile || isUploading) return;
    try {
      await onUpload(selectedFile);
    } catch {
      // Error handled by caller
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="w-full max-w-xl mx-auto space-y-4">
      {validationError && (
        <ErrorMessage
          title="Validation Notice"
          message={validationError}
          onRetry={() => setValidationError(null)}
        />
      )}

      <div
        data-testid="dropzone"
        onDragOver={onDragOverHandler}
        onDragLeave={onDragLeaveHandler}
        onDrop={onDropHandler}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-200 ${
          isDragOver
            ? 'border-blue-500 bg-blue-50/70 scale-[1.01]'
            : 'border-slate-300 hover:border-slate-400 bg-white hover:bg-slate-50/50'
        } ${isUploading ? 'pointer-events-none opacity-80' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          data-testid="file-input"
          onChange={onFileInputChange}
          className="hidden"
          disabled={isUploading}
        />

        {isUploading ? (
          <div className="py-6 flex flex-col items-center">
            <LoadingSpinner size="lg" label="Uploading and analyzing research PDF..." />
            <p className="text-xs text-slate-400 mt-2">Computing SHA-256 hash & checking duplicates</p>
          </div>
        ) : (
          <>
            <div className="w-14 h-14 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mb-4 shadow-xs">
              <UploadCloud className="w-7 h-7" />
            </div>

            <h3 className="text-sm font-semibold text-slate-800">
              Drag & Drop your research paper here
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              or <span className="text-blue-600 font-medium underline">browse your local files</span>
            </p>

            <div className="mt-4 flex items-center gap-3 text-[11px] text-slate-400">
              <span>PDF format only</span>
              <span>•</span>
              <span>Max 25 MB</span>
              <span>•</span>
              <span>One paper at a time</span>
            </div>
          </>
        )}
      </div>

      {selectedFile && !isUploading && (
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs flex items-center justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2 bg-blue-50 text-blue-600 rounded-lg flex-shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold text-slate-800 truncate">{selectedFile.name}</p>
              <p className="text-[11px] text-slate-400">{formatFileSize(selectedFile.size)}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setSelectedFile(null)}
              className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
              title="Remove file"
            >
              <X className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-xs transition-colors flex items-center gap-1.5"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Process Paper</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
