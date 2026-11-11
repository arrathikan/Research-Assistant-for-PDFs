import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
vi.mock('react-pdf', async () => import('./pdfMock'));
import { DocumentWorkspace } from '../components/workspace/DocumentWorkspace';
import { api } from '../services/api';
import { PDF_CITATION, PDF_DOCUMENT } from './pdfFixtures';
import { pdfMock } from './pdfMock';
const response = { document_id: PDF_CITATION.document_id, conversation_id: 'f'.repeat(32), turn_id: 'a'.repeat(32),
  answer: 'Synthetic answer [1]', is_out_of_scope: false, citations: [PDF_CITATION] };
beforeEach(() => {
  sessionStorage.clear(); pdfMock.pages = 3; pdfMock.fail = false;
  vi.stubGlobal('ResizeObserver', class { observe() {} disconnect() {} });
  vi.spyOn(api, 'getDocumentSummary').mockImplementation(() => new Promise(() => {}));
  vi.spyOn(api, 'sendChatQuery').mockResolvedValue(response);
  vi.spyOn(api, 'resolveCitation').mockResolvedValue(PDF_CITATION);
});
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });
async function ask() {
  fireEvent.click(screen.getByRole('button', { name: 'AI Chatbot' }));
  fireEvent.change(screen.getByRole('textbox', { name: 'Question' }), { target: { value: 'Synthetic question?' } });
  fireEvent.click(screen.getByRole('button', { name: 'Send Message' }));
  return screen.findByRole('button', { name: 'Open citation 1, page 2' });
}
it('opens a source in one viewer and repeats the jump after manual navigation', async () => {
  render(<DocumentWorkspace document={PDF_DOCUMENT} />);
  fireEvent.click(await ask());
  expect(await screen.findByText('Source — Page 2')).toBeInTheDocument();
  expect(screen.getAllByTestId('pdf-viewer-panel')).toHaveLength(1);
  expect(screen.getByRole('spinbutton', { name: 'PDF page number' })).toHaveValue(2);
  fireEvent.click(screen.getByRole('button', { name: 'Next Page' }));
  expect(screen.getByRole('spinbutton', { name: 'PDF page number' })).toHaveValue(3);
  fireEvent.click(screen.getByRole('button', { name: 'Page 2' }));
  await waitFor(() => expect(screen.getByRole('spinbutton', { name: 'PDF page number' })).toHaveValue(2));
  expect(api.resolveCitation).toHaveBeenCalledTimes(2);
  fireEvent.click(screen.getByRole('button', { name: 'Clear source' }));
  expect(screen.queryByText('Source — Page 2')).not.toBeInTheDocument();
});
it('reveals the PDF pane on mobile and preserves the conversation when returning', async () => {
  vi.stubGlobal('innerWidth', 390);
  render(<DocumentWorkspace document={PDF_DOCUMENT} />);
  fireEvent.click(await ask());
  expect(await screen.findByText('Source — Page 2')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'PDF Viewer' })).toHaveAttribute('aria-pressed', 'true');
  fireEvent.click(screen.getByRole('button', { name: 'AI Chatbot' }));
  expect(screen.getByRole('button', { name: 'Open citation 1, page 2' })).toBeInTheDocument();
  expect(screen.getAllByTestId('pdf-viewer-panel')).toHaveLength(1);
  expect(api.sendChatQuery).toHaveBeenCalledTimes(1);
});
it('clears source and conversation when a different document is selected', async () => {
  const view = render(<DocumentWorkspace document={PDF_DOCUMENT} />);
  fireEvent.click(await ask());
  expect(await screen.findByText('Source — Page 2')).toBeInTheDocument();
  await act(async () => { view.rerender(<DocumentWorkspace document={{ ...PDF_DOCUMENT, id: '507f1f77bcf86cd799439012' }} />); });
  expect(screen.queryByText('Source — Page 2')).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Open citation 1, page 2' })).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Structured Summary' })).toHaveAttribute('aria-pressed', 'true');
});
