import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { ProcessingProgress } from '../components/upload/ProcessingProgress';
import { api, ApiError } from '../services/api';
import { ID, OTHER_ID, PAPER, QUEUED, READY, SUMMARY } from './uploadFixtures';

beforeEach(() => {
  vi.useFakeTimers();
  vi.spyOn(api, 'getProcessingStatus').mockResolvedValue(QUEUED);
  vi.spyOn(api, 'getDocument').mockResolvedValue(PAPER);
  vi.spyOn(api, 'getDocumentSummary').mockResolvedValue(SUMMARY);
});
afterEach(() => { vi.useRealTimers(); vi.restoreAllMocks(); });
async function tick() { await act(async () => { await vi.advanceTimersByTimeAsync(2000); }); }

it('uses queued and processing statuses without percentages or raw identifiers', async () => {
  const open = vi.fn();
  render(<ProcessingProgress document={PAPER} onOpen={open} />);
  expect(screen.getByText('Uploaded')).toBeInTheDocument();
  await tick();
  expect(screen.getByText('Queued')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /Open PDF/ })).toHaveAttribute('href', api.getPdfStreamUrl(ID));
  expect(screen.getByRole('button', { name: 'View Summary' })).toBeDisabled();
  expect(screen.getByRole('button', { name: 'Chat with Paper' })).toBeDisabled();
  vi.mocked(api.getProcessingStatus).mockResolvedValue({ ...QUEUED, status: 'RUNNING', step: 'parsing' });
  await tick();
  expect(screen.getByText('Processing')).toBeInTheDocument();
  expect(screen.getByRole('status')).toHaveTextContent('Reading your PDF');
  expect(screen.queryByText(ID, { exact: false })).not.toBeInTheDocument();
  expect(screen.queryByText(/PENDING|100%/)).not.toBeInTheDocument();
  expect(open).not.toHaveBeenCalled();
});

it('keeps automatic retries processing even when metadata temporarily says FAILED', async () => {
  vi.mocked(api.getProcessingStatus).mockResolvedValue({ ...QUEUED, status: 'RETRY_WAIT', attempt: 2 });
  vi.mocked(api.getDocument).mockResolvedValue({ ...PAPER, status: 'FAILED' });
  render(<ProcessingProgress document={PAPER} onOpen={vi.fn()} />);
  await tick();
  expect(screen.getByText('Processing')).toBeInTheDocument();
  expect(screen.getByRole('status')).toHaveTextContent('retry automatically');
  expect(screen.queryByRole('button', { name: 'Retry processing' })).not.toBeInTheDocument();
});

it('requires matching completion, current summary data and embeddings before showing Ready', async () => {
  const open = vi.fn();
  vi.mocked(api.getDocument).mockResolvedValue(READY);
  render(<ProcessingProgress document={PAPER} onOpen={open} />);
  await tick();
  expect(screen.queryByText('Ready')).not.toBeInTheDocument();
  expect(api.getDocumentSummary).not.toHaveBeenCalled();
  vi.mocked(api.getProcessingStatus).mockResolvedValue({ ...QUEUED, status: 'COMPLETED' });
  vi.mocked(api.getDocumentSummary).mockRejectedValueOnce(new ApiError(409, 'not yet available'));
  await tick();
  expect(screen.queryByText('Ready')).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'View Summary' })).toBeDisabled();
  await tick();
  expect(screen.getByText('Ready')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'View Summary' }));
  expect(open).toHaveBeenLastCalledWith(READY, 'summary');
  fireEvent.click(screen.getByRole('button', { name: 'Chat with Paper' }));
  expect(open).toHaveBeenLastCalledWith(READY, 'chat');
  const calls = vi.mocked(api.getProcessingStatus).mock.calls.length;
  await tick();
  expect(api.getProcessingStatus).toHaveBeenCalledTimes(calls);
});

it('does not enable chat or label Ready when embeddings are incomplete', async () => {
  vi.mocked(api.getDocument).mockResolvedValue({ ...READY, embedding_status: 'RUNNING' });
  vi.mocked(api.getProcessingStatus).mockResolvedValue({ ...QUEUED, status: 'COMPLETED' });
  render(<ProcessingProgress document={PAPER} onOpen={vi.fn()} />);
  await tick();
  expect(screen.queryByText('Ready')).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Chat with Paper' })).toBeDisabled();
});

it('can open chat while a summary is still being generated when embeddings are complete', async () => {
  const current = { ...PAPER, status: 'SUMMARIZING' as const, embedding_status: 'COMPLETED' as const };
  vi.mocked(api.getDocument).mockResolvedValue(current);
  vi.mocked(api.getProcessingStatus).mockResolvedValue({ ...QUEUED, status: 'RUNNING', stage: 'summary', step: 'summary' });
  const open = vi.fn();
  render(<ProcessingProgress document={PAPER} onOpen={open} />);
  await tick();
  expect(screen.getByRole('button', { name: 'View Summary' })).toBeDisabled();
  fireEvent.click(screen.getByRole('button', { name: 'Chat with Paper' }));
  expect(open).toHaveBeenCalledWith(current, 'chat');
  expect(screen.queryByText('Ready')).not.toBeInTheDocument();
});

it('offers Retry only for a retryable terminal failure and keeps the returned queued state', async () => {
  vi.mocked(api.getProcessingStatus).mockResolvedValue({ ...QUEUED, status: 'DEAD_LETTER', attempt: 3 });
  vi.mocked(api.getDocument).mockResolvedValue({ ...PAPER, status: 'FAILED' });
  vi.spyOn(api, 'retryProcessing').mockResolvedValue({ ...QUEUED, generation: 2 });
  render(<ProcessingProgress document={PAPER} onOpen={vi.fn()} />);
  await tick();
  expect(screen.getByText('Failed')).toBeInTheDocument();
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Retry processing' })); });
  expect(api.retryProcessing).toHaveBeenCalledWith(ID);
  expect(screen.getByText('Queued')).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Retry processing' })).not.toBeInTheDocument();
});

it('requires review for interrupted work and never offers an unsupported retry', async () => {
  vi.mocked(api.getProcessingStatus).mockResolvedValue({ ...QUEUED, status: 'DEAD_LETTER', requires_review: true });
  const retry = vi.spyOn(api, 'retryProcessing');
  render(<ProcessingProgress document={PAPER} onOpen={vi.fn()} />);
  await tick();
  expect(screen.getByRole('status')).toHaveTextContent('needs review');
  expect(screen.queryByRole('button', { name: 'Retry processing' })).not.toBeInTheDocument();
  expect(retry).not.toHaveBeenCalled();
});

it('supports scheduling an unscheduled stored document', async () => {
  vi.mocked(api.getProcessingStatus).mockResolvedValue({ ...QUEUED, status: 'NOT_SCHEDULED' });
  vi.spyOn(api, 'retryProcessing').mockResolvedValue(QUEUED);
  render(<ProcessingProgress document={PAPER} onOpen={vi.fn()} />);
  await tick();
  expect(screen.getByText('Uploaded')).toBeInTheDocument();
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Start processing' })); });
  expect(api.retryProcessing).toHaveBeenCalledWith(ID);
});

it('sanitizes poll errors and retries the status read without starting processing', async () => {
  vi.mocked(api.getProcessingStatus).mockRejectedValueOnce(new ApiError(404, 'private provider data ' + ID));
  const retry = vi.spyOn(api, 'retryProcessing');
  render(<ProcessingProgress document={PAPER} onOpen={vi.fn()} />);
  await tick();
  expect(screen.getByRole('alert')).not.toHaveTextContent('private provider data');
  expect(screen.queryByText('Ready')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Check status again' }));
  await tick();
  expect(screen.getByText('Queued')).toBeInTheDocument();
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  expect(retry).not.toHaveBeenCalled();
});

it('rejects mismatched document and summary responses', async () => {
  vi.mocked(api.getDocument).mockResolvedValue(READY);
  vi.mocked(api.getProcessingStatus).mockResolvedValue({ ...QUEUED, document_id: OTHER_ID, status: 'COMPLETED' });
  render(<ProcessingProgress document={PAPER} onOpen={vi.fn()} />);
  await tick();
  expect(screen.queryByText('Ready')).not.toBeInTheDocument();
  vi.mocked(api.getProcessingStatus).mockResolvedValue({ ...QUEUED, status: 'COMPLETED' });
  vi.mocked(api.getDocumentSummary).mockResolvedValue({ ...SUMMARY, document_id: OTHER_ID });
  await tick();
  expect(screen.getByRole('button', { name: 'View Summary' })).toBeDisabled();
  expect(screen.queryByText('Ready')).not.toBeInTheDocument();
});

it('handles a rejected retry without pretending that processing restarted', async () => {
  vi.mocked(api.getProcessingStatus).mockResolvedValue({ ...QUEUED, status: 'DEAD_LETTER' });
  vi.spyOn(api, 'retryProcessing').mockRejectedValue(new ApiError(409, 'private failure'));
  render(<ProcessingProgress document={PAPER} onOpen={vi.fn()} />);
  await tick();
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Retry processing' })); });
  expect(screen.getByText('Failed')).toBeInTheDocument();
  expect(screen.getByRole('alert')).toHaveTextContent('couldn’t be restarted');
  expect(screen.getByRole('alert')).not.toHaveTextContent('private failure');
});

it('stops pending polls on unmount', async () => {
  const view = render(<ProcessingProgress document={PAPER} onOpen={vi.fn()} />);
  view.unmount();
  await tick();
  expect(api.getProcessingStatus).not.toHaveBeenCalled();
});

it('resets ready state immediately when its document changes', async () => {
  vi.mocked(api.getProcessingStatus).mockResolvedValue({ ...QUEUED, status: 'COMPLETED' });
  vi.mocked(api.getDocument).mockResolvedValue(READY);
  const view = render(<ProcessingProgress document={READY} onOpen={vi.fn()} />);
  await tick();
  expect(screen.getByText('Ready')).toBeInTheDocument();
  view.rerender(<ProcessingProgress document={{ ...PAPER, id: OTHER_ID, filename: 'new.pdf' }} onOpen={vi.fn()} />);
  expect(screen.getByText('new.pdf')).toBeInTheDocument();
  expect(screen.queryByText('Ready')).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'View Summary' })).toBeDisabled();
  expect(screen.getByRole('button', { name: 'Chat with Paper' })).toBeDisabled();
});

it('keeps a completed job processing until document readiness is confirmed', async () => {
  vi.mocked(api.getProcessingStatus).mockResolvedValue({ ...QUEUED, status: 'COMPLETED' });
  render(<ProcessingProgress document={PAPER} onOpen={vi.fn()} />);
  await tick();
  expect(screen.getByText('Processing')).toBeInTheDocument();
  expect(screen.queryByText('Ready')).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'View Summary' })).toBeDisabled();
});
