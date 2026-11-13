import { formatFileSize } from './formatFileSize';
export const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024;

/** One validation path for the page drop target and the modal's file picker. */
export function selectPdf(files: readonly File[] | FileList | null): { file: File | null; error: string | null } {
  if (!files?.length) return { file: null, error: null };
  if (files.length !== 1) return { file: null, error: 'Choose exactly one PDF at a time.' };
  const file = files[0];
  let error: string | null = null;
  if (!file.name.toLowerCase().endsWith('.pdf') || !['', 'application/pdf', 'application/octet-stream'].includes(file.type)) error = 'Invalid file format. Please upload an academic research paper in PDF format.';
  else if (!file.size) error = 'The PDF file is empty. Choose a non-empty PDF.';
  else if (file.size > MAX_FILE_SIZE_BYTES) error = 'File size (' + formatFileSize(file.size) + ') exceeds maximum allowed limit of 25 MB.';
  return { file: error ? null : file, error };
}
