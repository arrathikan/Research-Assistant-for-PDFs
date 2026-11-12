import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
vi.mock('react-pdf', async () => import('./pdfMock'));
import { PdfViewerPanel } from '../components/pdf/PdfViewerPanel';
import { api, ApiError } from '../services/api';
import { PDF_CITATION, PDF_DOCUMENT, PDF_ID } from './pdfFixtures';
import { pdfMock } from './pdfMock';
import type { ChatCitation } from '../types/chat';
beforeEach(() => {
  pdfMock.pages = 3; pdfMock.fail = false; pdfMock.text = 'Synthetic evidence.';
  vi.stubGlobal('ResizeObserver', class { observe() {} disconnect() {} });
  vi.stubGlobal('requestAnimationFrame', (callback: FrameRequestCallback) => window.setTimeout(() => callback(0), 0));
  vi.stubGlobal('cancelAnimationFrame', (id: number) => window.clearTimeout(id));
  vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue(new DOMRect(0, 0, 600, 800));
  Object.defineProperty(HTMLElement.prototype, 'scrollTo', { configurable: true, value: vi.fn() });
  Object.defineProperty(Range.prototype, 'getClientRects', { configurable: true, value: () => [new DOMRect(60, 80, 180, 20)] });
  vi.spyOn(api, 'resolveCitation').mockResolvedValue(PDF_CITATION);
});
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });
it('renders the uploaded PDF and uses its actual page count', async () => {
  render(<PdfViewerPanel document={{ ...PDF_DOCUMENT, page_count: 99 }} />);
  expect(await screen.findByText('of 3')).toBeInTheDocument();
  expect(screen.getByTestId('pdf-document')).toHaveAttribute('data-file', api.getPdfStreamUrl(PDF_ID));
  fireEvent.click(screen.getByRole('button', { name: 'Next Page' }));
  expect(screen.getByRole('spinbutton', { name: 'PDF page number' })).toHaveValue(2);
  fireEvent.click(screen.getByRole('button', { name: 'Zoom In' }));
  expect(screen.getByLabelText('PDF zoom')).toHaveTextContent('125%');
  fireEvent.click(screen.getByRole('button', { name: 'Reset Zoom' }));
  expect(screen.getByLabelText('PDF zoom')).toHaveTextContent('100%');
});
it('verifies, jumps, highlights exact rendered text, and reopens the same source', async () => {
  const view = render(<PdfViewerPanel document={PDF_DOCUMENT} activeCitation={PDF_CITATION} />);
  await waitFor(() => expect(screen.getByTestId('pdf-source-highlight')).toBeInTheDocument());
  expect(screen.getByRole('spinbutton', { name: 'PDF page number' })).toHaveValue(2);
  expect(screen.getByTestId('pdf-source-highlight')).toHaveStyle({ left: '60px', top: '80px' });
  fireEvent.click(screen.getByRole('button', { name: 'Next Page' }));
  await waitFor(() => expect(screen.queryByTestId('pdf-source-highlight')).not.toBeInTheDocument());
  view.rerender(<PdfViewerPanel document={PDF_DOCUMENT} activeCitation={{ ...PDF_CITATION }} />);
  await waitFor(() => expect(screen.getByTestId('pdf-source-highlight')).toBeInTheDocument());
  expect(api.resolveCitation).toHaveBeenCalledTimes(2);
});
it('uses verified source regions when rendered text cannot be matched', async () => {
  pdfMock.text = 'Different extraction';
  render(<PdfViewerPanel document={PDF_DOCUMENT} activeCitation={PDF_CITATION} />);
  await waitFor(() => expect(screen.getByTestId('pdf-source-highlight')).toBeInTheDocument());
  expect(screen.queryByText(/highlight is unavailable/)).not.toBeInTheDocument();
  expect(screen.getByTestId('pdf-source-highlight')).toHaveStyle({ width: '180px', height: '20px' });
});
it('opens the cited page quietly when exact text and geometry are unavailable', async () => {
  pdfMock.text = '';
  vi.mocked(api.resolveCitation).mockResolvedValue({ ...PDF_CITATION, bounding_boxes: [] });
  render(<PdfViewerPanel document={PDF_DOCUMENT} activeCitation={PDF_CITATION} />);
  expect(await screen.findByText('Source — Page 2')).toBeInTheDocument();
  expect(screen.queryByText(/highlight is unavailable/)).not.toBeInTheDocument();
  expect(screen.queryByText(PDF_CITATION.quote_snippet)).not.toBeInTheDocument();
  expect(screen.queryByTestId('pdf-source-highlight')).not.toBeInTheDocument();
  expect(screen.getByText('Source — Page 2')).toBeInTheDocument();
});
it('rejects stale and cross-document sources', async () => {
  vi.mocked(api.resolveCitation).mockRejectedValue(new ApiError(409, 'stale'));
  const view = render(<PdfViewerPanel document={PDF_DOCUMENT} activeCitation={PDF_CITATION} />);
  expect(await screen.findByRole('alert')).toHaveTextContent('This source changed.');
  expect(screen.queryByTestId('pdf-source-highlight')).not.toBeInTheDocument();
  view.rerender(<PdfViewerPanel document={PDF_DOCUMENT} activeCitation={{ ...PDF_CITATION, document_id: '507f1f77bcf86cd799439012' }} />);
  expect(await screen.findByRole('alert')).toHaveTextContent('different document');
  expect(api.resolveCitation).toHaveBeenCalledTimes(1);
});
it('ignores late source resolution after switching documents', async () => {
  let finish: (value: ChatCitation) => void = () => {};
  vi.mocked(api.resolveCitation).mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  const view = render(<PdfViewerPanel document={PDF_DOCUMENT} activeCitation={PDF_CITATION} />);
  view.rerender(<PdfViewerPanel document={{ ...PDF_DOCUMENT, id: '507f1f77bcf86cd799439012' }} />);
  await act(async () => { finish(PDF_CITATION); });
  expect(screen.queryByText('Source — Page 2')).not.toBeInTheDocument();
  expect(screen.getByRole('spinbutton', { name: 'PDF page number' })).toHaveValue(1);
});
it('rejects mismatched canonical answers and out-of-range pages', async () => {
  vi.mocked(api.resolveCitation).mockResolvedValue({ ...PDF_CITATION, quote_snippet: 'Wrong quote' });
  const view = render(<PdfViewerPanel document={PDF_DOCUMENT} activeCitation={PDF_CITATION} />);
  expect(await screen.findByRole('alert')).toHaveTextContent('We couldn’t open this source');
  vi.mocked(api.resolveCitation).mockResolvedValue({ ...PDF_CITATION, page_number: 9 });
  view.rerender(<PdfViewerPanel document={PDF_DOCUMENT} activeCitation={{ ...PDF_CITATION, page_number: 9 }} />);
  expect(await screen.findByRole('alert')).toHaveTextContent('not available in this PDF');
  expect(screen.queryByTestId('pdf-source-highlight')).not.toBeInTheDocument();
  expect(screen.getByRole('spinbutton', { name: 'PDF page number' })).toHaveValue(1);
});
it('offers retry for a failed PDF and shows no invented pages for demo identifiers', async () => {
  pdfMock.fail = true;
  const view = render(<PdfViewerPanel document={PDF_DOCUMENT} />);
  expect(await screen.findByRole('button', { name: 'Retry PDF' })).toBeInTheDocument();
  pdfMock.fail = false;
  fireEvent.click(screen.getByRole('button', { name: 'Retry PDF' }));
  expect(await screen.findByText('of 3')).toBeInTheDocument();
  view.rerender(<PdfViewerPanel document={{ ...PDF_DOCUMENT, id: 'sample-paper' }} />);
  expect(screen.getByText('Upload a PDF to view its pages.')).toBeInTheDocument();
  expect(screen.queryByTestId('pdf-document')).not.toBeInTheDocument();
});
