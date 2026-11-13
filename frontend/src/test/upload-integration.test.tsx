import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen } from '@testing-library/react';
import { UploadView } from '../views/UploadView';
import { api, ApiError } from '../services/api';
import type { UploadResponse } from '../types';
import type { ProcessingStatus } from '../types/processing';
import { ID, OTHER_ID, PAPER, QUEUED, READY, STORED, SUMMARY } from './uploadFixtures';

beforeEach(() => {
  vi.useFakeTimers();
  vi.spyOn(api, 'uploadDocument').mockResolvedValue(STORED);
  vi.spyOn(api, 'getDocument').mockResolvedValue(PAPER);
  vi.spyOn(api, 'getProcessingStatus').mockResolvedValue(QUEUED);
  vi.spyOn(api, 'getDocumentSummary').mockResolvedValue(SUMMARY);
});
afterEach(() => { vi.useRealTimers(); vi.restoreAllMocks(); });
async function selectAndUpload(name = 'paper.pdf') {
  fireEvent.click(screen.getByTestId('main-upload-trigger'));
  const file = new File(['%PDF-1.7 synthetic'], name, { type: 'application/pdf' });
  await act(async () => {
    fireEvent.change(screen.getByTestId('file-input'), { target: { files: [file] } });
    fireEvent.click(screen.getByRole('button', { name: 'Upload paper' }));
  });
  return file;
}

describe('upload status card', () => {
  it('shows one compact saved file with no raw IDs, API messages or repeated upload actions', async () => {
    const open = vi.fn();
    render(<UploadView onUploadSuccess={open} />);
    const file = await selectAndUpload();
    expect(screen.getByText('Uploaded')).toBeInTheDocument();
    expect(screen.getAllByText('paper.pdf')).toHaveLength(1);
    expect(screen.getByText('PDF · 1.0 MB')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Open Workspace' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Done' })).toBeEnabled();
    expect(screen.queryByText(/Raw internal|PENDING|Document ID|Upload successful|100%/)).not.toBeInTheDocument();
    expect(screen.queryByTestId('dropzone')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Upload paper' })).not.toBeInTheDocument();
    expect(api.uploadDocument).toHaveBeenCalledWith(file);
    expect(open).not.toHaveBeenCalled();
  });

  it('uses real completed data for duplicate uploads and opens the requested workspace panel', async () => {
    vi.mocked(api.uploadDocument).mockResolvedValue({ ...STORED, document: READY, is_duplicate: true });
    vi.mocked(api.getDocument).mockResolvedValue(READY);
    vi.mocked(api.getProcessingStatus).mockResolvedValue({ ...QUEUED, status: 'COMPLETED' });
    const open = vi.fn();
    render(<UploadView onUploadSuccess={open} />);
    await selectAndUpload();
    expect(screen.queryByText('Ready')).not.toBeInTheDocument();
    await act(async () => { await vi.advanceTimersByTimeAsync(2000); });
    expect(screen.getByText('Ready')).toBeInTheDocument();
    expect(screen.getAllByText('paper.pdf')).toHaveLength(1);
    fireEvent.click(screen.getByRole('button', { name: 'Open Workspace' }));
    expect(open).toHaveBeenLastCalledWith(READY, 'summary');
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('shows uploading until the actual upload response and prevents another submission', async () => {
    let finish!: (result: UploadResponse) => void;
    vi.mocked(api.uploadDocument).mockImplementation(() => new Promise(resolve => { finish = resolve; }));
    render(<UploadView onUploadSuccess={vi.fn()} />);
    await selectAndUpload();
    expect(screen.getByText('Uploading')).toBeInTheDocument();
    expect(screen.getAllByText('paper.pdf')).toHaveLength(1);
    expect(screen.queryByTestId('file-input')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Upload another paper' })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Open PDF/ })).not.toBeInTheDocument();
    expect(api.getProcessingStatus).not.toHaveBeenCalled();
    await act(async () => { finish(STORED); });
    expect(screen.getByText('Uploaded')).toBeInTheDocument();
  });

  it('retries a failed upload using the retained file and a real upload call', async () => {
    vi.mocked(api.uploadDocument).mockRejectedValueOnce(new ApiError(503, 'private details ' + ID)).mockResolvedValueOnce(STORED);
    const open = vi.fn();
    render(<UploadView onUploadSuccess={open} />);
    const file = await selectAndUpload();
    expect(screen.getByText('Failed')).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent('Check your connection');
    expect(screen.queryByText(/private details/)).not.toBeInTheDocument();
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Retry upload' })); });
    expect(screen.getByText('Uploaded')).toBeInTheDocument();
    expect(api.uploadDocument).toHaveBeenNthCalledWith(2, file);
    expect(open).not.toHaveBeenCalled();
  });

  it('asks for a different file instead of retrying an invalid PDF', async () => {
    vi.mocked(api.uploadDocument).mockRejectedValue(new ApiError(400, 'corrupt'));
    render(<UploadView onUploadSuccess={vi.fn()} />);
    await selectAndUpload();
    expect(screen.getByText('Failed')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Retry upload' })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Choose a different PDF' }));
    expect(screen.getByTestId('file-input')).toBeInTheDocument();
    expect(screen.queryByText('paper.pdf')).not.toBeInTheDocument();
  });

  it('isolates repeated uploads from a previous document’s late ready response', async () => {
    let oldStatus!: (value: ProcessingStatus) => void;
    let newUpload!: (value: UploadResponse) => void;
    vi.mocked(api.getProcessingStatus).mockImplementationOnce(() => new Promise(resolve => { oldStatus = resolve; }));
    vi.mocked(api.getDocument).mockResolvedValue(READY);
    render(<UploadView onUploadSuccess={vi.fn()} />);
    await selectAndUpload();
    await act(async () => { vi.advanceTimersByTime(2000); });
    fireEvent.click(screen.getByRole('button', { name: 'Done' }));
    vi.mocked(api.uploadDocument).mockImplementationOnce(() => new Promise(resolve => { newUpload = resolve; }));
    await selectAndUpload('new-paper.pdf');
    await act(async () => { oldStatus({ ...QUEUED, status: 'COMPLETED' }); });
    expect(screen.queryByText('Ready')).not.toBeInTheDocument();
    expect(screen.queryByText('paper.pdf')).not.toBeInTheDocument();
    expect(screen.getAllByText('new-paper.pdf')).toHaveLength(1);
    expect(api.getDocumentSummary).not.toHaveBeenCalled();
    await act(async () => { newUpload({ ...STORED, document: { ...PAPER, id: OTHER_ID, filename: 'new-paper.pdf' } }); });
    expect(screen.getByText('Uploaded')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Open Workspace' })).not.toBeInTheDocument();
  });
});
