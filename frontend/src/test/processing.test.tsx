import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { ProcessingProgress } from '../components/upload/ProcessingProgress';
import { api } from '../services/api';
import { PDF_DOCUMENT, PDF_ID } from './pdfFixtures';
import type { ProcessingStatus } from '../types/processing';
const QUEUED: ProcessingStatus = { document_id: PDF_ID, job_id: 'a'.repeat(64), status: 'QUEUED', stage: 'ingestion', step: null,
  generation: 1, attempt: 1, max_attempts: 3, retry_at: null, error_code: null, requires_review: false };
beforeEach(() => {
  vi.useFakeTimers();
  vi.spyOn(api, 'getProcessingStatus').mockResolvedValue(QUEUED);
  vi.spyOn(api, 'getDocument').mockResolvedValue({ ...PDF_DOCUMENT, status: 'PENDING' });
});
afterEach(() => { vi.useRealTimers(); vi.restoreAllMocks(); });
async function tick() { await act(async () => { await vi.advanceTimersByTimeAsync(2000); }); }
it('polls saved progress, keeps automatic retries pending, and reports real readiness', async () => {
  const ready = vi.fn();
  render(<ProcessingProgress documentId={PDF_ID} onReady={ready} />);
  expect(api.getProcessingStatus).not.toHaveBeenCalled();
  await tick(); expect(screen.getByText('Queued for processing…')).toBeInTheDocument();
  vi.mocked(api.getProcessingStatus).mockResolvedValue({ ...QUEUED, status: 'RUNNING', step: 'parsing' });
  await tick(); expect(screen.getByText('Reading the PDF…')).toBeInTheDocument();
  vi.mocked(api.getProcessingStatus).mockResolvedValue({ ...QUEUED, status: 'RETRY_WAIT', attempt: 2 });
  vi.mocked(api.getDocument).mockResolvedValue({ ...PDF_DOCUMENT, status: 'FAILED' });
  await tick(); expect(screen.getByText(/retry automatically/)).toBeInTheDocument();
  expect(ready).not.toHaveBeenCalled();
  vi.mocked(api.getProcessingStatus).mockResolvedValue({ ...QUEUED, status: 'COMPLETED' });
  vi.mocked(api.getDocument).mockResolvedValue(PDF_DOCUMENT);
  await tick(); expect(ready).toHaveBeenCalledWith(PDF_DOCUMENT);
});
it('offers explicit retry for a terminal failure', async () => {
  vi.mocked(api.getProcessingStatus).mockResolvedValue({ ...QUEUED, status: 'DEAD_LETTER', attempt: 3 });
  vi.spyOn(api, 'retryProcessing').mockResolvedValue({ ...QUEUED, generation: 2 });
  render(<ProcessingProgress documentId={PDF_ID} onReady={vi.fn()} />); await tick();
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Retry processing' })); });
  expect(api.retryProcessing).toHaveBeenCalledWith(PDF_ID);
  expect(screen.getByText('Waiting for background processing…')).toBeInTheDocument();
});
it('requires review for interrupted work and never retries it automatically', async () => {
  vi.mocked(api.getProcessingStatus).mockResolvedValue({ ...QUEUED, status: 'DEAD_LETTER', requires_review: true });
  const retry = vi.spyOn(api, 'retryProcessing');
  render(<ProcessingProgress documentId={PDF_ID} onReady={vi.fn()} />); await tick();
  expect(screen.getByText(/needs review/)).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Retry processing' })).not.toBeInTheDocument();
  expect(retry).not.toHaveBeenCalled();
});
it('does not invent readiness after errors or replies for another document', async () => {
  const ready = vi.fn();
  vi.mocked(api.getProcessingStatus).mockRejectedValue(new Error('private provider data'));
  render(<ProcessingProgress documentId={PDF_ID} onReady={ready} />); await tick();
  expect(screen.getByRole('alert')).not.toHaveTextContent('private provider data');
  vi.mocked(api.getProcessingStatus).mockResolvedValue({ ...QUEUED, document_id: '507f1f77bcf86cd799439012', status: 'COMPLETED' });
  vi.mocked(api.getDocument).mockResolvedValue(PDF_DOCUMENT);
  await tick(); expect(ready).not.toHaveBeenCalled();
});
it('stops polling after unmount', async () => {
  const view = render(<ProcessingProgress documentId={PDF_ID} onReady={vi.fn()} />);
  view.unmount(); await tick(); expect(api.getProcessingStatus).not.toHaveBeenCalled();
});
