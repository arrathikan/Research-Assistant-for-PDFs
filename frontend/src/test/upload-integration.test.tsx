import { afterEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { UploadView } from '../views/UploadView';
import { api } from '../services/api';
import { UploadResponse } from '../types';

const stored: UploadResponse = {
  document: {
    id: '507f1f77bcf86cd799439011', sha256: 'a'.repeat(64), filename: 'paper.pdf',
    file_size_bytes: 200, page_count: 1, status: 'PENDING',
    created_at: '2026-11-10T00:00:00Z', updated_at: '2026-11-10T00:00:00Z',
  },
  message: 'PDF stored; processing pending', is_duplicate: false,
};

afterEach(() => { vi.restoreAllMocks(); });

function selectAndUpload() {
  const file = new File(['%PDF-1.7 test'], 'paper.pdf', { type: 'application/pdf' });
  fireEvent.change(screen.getByTestId('file-input'), { target: { files: [file] } });
  fireEvent.click(screen.getByText('Process Paper'));
  return file;
}

describe('live upload states', () => {
  it('shows persisted status and an original-file link without opening a pending workspace', async () => {
    const upload = vi.spyOn(api, 'uploadDocument').mockResolvedValue(stored);
    const onSuccess = vi.fn();
    render(<UploadView onUploadSuccess={onSuccess} />);
    const file = selectAndUpload();
    expect(await screen.findByText('Upload successful')).toBeInTheDocument();
    expect(screen.getByText(/Status: PENDING/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Open original PDF' })).toHaveAttribute('href', api.getPdfStreamUrl(stored.document.id!));
    expect(upload).toHaveBeenCalledWith(file);
    expect(onSuccess).not.toHaveBeenCalled();
  });

  it('shows duplicate status and opens a workspace only when the stored document is READY', async () => {
    const response = { ...stored, is_duplicate: true, document: { ...stored.document, status: 'READY' as const } };
    vi.spyOn(api, 'uploadDocument').mockResolvedValue(response);
    const onSuccess = vi.fn();
    render(<UploadView onUploadSuccess={onSuccess} />);
    selectAndUpload();
    expect(await screen.findByText('Duplicate detected')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Open workspace' }));
    expect(onSuccess).toHaveBeenCalledWith(response.document);
  });

  it('reports failure without inventing a document and allows retry', async () => {
    const upload = vi.spyOn(api, 'uploadDocument').mockRejectedValueOnce(new Error('Document storage temporarily unavailable')).mockResolvedValueOnce(stored);
    const onSuccess = vi.fn();
    render(<UploadView onUploadSuccess={onSuccess} />);
    selectAndUpload();
    expect(await screen.findByRole('alert')).toHaveTextContent('Document storage temporarily unavailable');
    expect(onSuccess).not.toHaveBeenCalled();
    expect(screen.queryByText('Upload successful')).not.toBeInTheDocument();
    fireEvent.click(screen.getByText('Process Paper'));
    expect(await screen.findByText('Upload successful')).toBeInTheDocument();
    expect(upload).toHaveBeenCalledTimes(2);
  });

  it('shows uploading until the real request resolves', async () => {
    let finish: (result: UploadResponse) => void = () => {};
    vi.spyOn(api, 'uploadDocument').mockImplementation(() => new Promise(resolve => { finish = resolve; }));
    render(<UploadView onUploadSuccess={vi.fn()} />);
    selectAndUpload();
    expect(screen.getByText('Uploading and checking research PDF...')).toBeInTheDocument();
    expect(screen.getByTestId('file-input')).toBeDisabled();
    finish(stored);
    await waitFor(() => expect(screen.getByText('Upload successful')).toBeInTheDocument());
  });
});
