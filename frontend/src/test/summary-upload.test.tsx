import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { api, ApiError } from '../services/api';
import { UploadView } from '../views/UploadView';

afterEach(() => { vi.restoreAllMocks(); });

it('opens a read-only summary for an uploaded document that is still pending', async () => {
  const document = {
    id: '507f1f77bcf86cd799439011', sha256: 'a'.repeat(64), filename: 'synthetic.pdf',
    file_size_bytes: 200, page_count: 1, status: 'PENDING' as const,
    created_at: '2026-11-11T00:00:00Z', updated_at: '2026-11-11T00:00:00Z',
  };
  vi.spyOn(api, 'uploadDocument').mockResolvedValue({ document, is_duplicate: false, message: 'PDF stored' });
  const read = vi.spyOn(api, 'getDocumentSummary').mockRejectedValue(new ApiError(409, 'pending'));
  const selectWorkspace = vi.fn();
  render(<UploadView onUploadSuccess={selectWorkspace} />);
  const file = new File(['%PDF-1.7 synthetic'], 'synthetic.pdf', { type: 'application/pdf' });
  fireEvent.change(screen.getByTestId('file-input'), { target: { files: [file] } });
  fireEvent.click(screen.getByText('Process Paper'));
  const view = await screen.findByRole('button', { name: 'View summary' });
  expect(read).not.toHaveBeenCalled();
  fireEvent.click(view);
  expect(await screen.findByText('Summary not ready yet. Checking for updates…')).toBeInTheDocument();
  expect(read).toHaveBeenCalledWith(document.id);
  expect(screen.getByRole('heading', { name: 'Key Results' })).toBeInTheDocument();
  expect(selectWorkspace).not.toHaveBeenCalled();
});
