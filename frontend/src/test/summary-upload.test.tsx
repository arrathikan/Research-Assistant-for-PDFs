import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { api } from '../services/api';
import { UploadView } from '../views/UploadView';
import { PAPER, QUEUED, STORED } from './uploadFixtures';

afterEach(() => { vi.restoreAllMocks(); vi.useRealTimers(); });

it('does not open or poll a summary while uploaded data is still pending', async () => {
  vi.useFakeTimers();
  vi.spyOn(api, 'uploadDocument').mockResolvedValue(STORED);
  vi.spyOn(api, 'getDocument').mockResolvedValue(PAPER);
  vi.spyOn(api, 'getProcessingStatus').mockResolvedValue(QUEUED);
  const read = vi.spyOn(api, 'getDocumentSummary');
  const open = vi.fn();
  render(<UploadView onUploadSuccess={open} />);
  fireEvent.click(screen.getByTestId('main-upload-trigger'));
  await act(async () => {
    fireEvent.change(screen.getByTestId('file-input'), { target: { files: [new File(['%PDF-1.7'], 'paper.pdf', { type: 'application/pdf' })] } });
    fireEvent.click(screen.getByRole('button', { name: 'Upload paper' }));
  });
  await act(async () => { await vi.advanceTimersByTimeAsync(2000); });
  expect(screen.queryByRole('button', { name: 'Open Workspace' })).not.toBeInTheDocument();
  expect(read).not.toHaveBeenCalled();
  expect(open).not.toHaveBeenCalled();
  expect(screen.queryByText('Summary not ready yet. Checking for updates…')).not.toBeInTheDocument();
});
