import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
vi.mock('react-pdf', async () => import('./pdfMock'));
import { DocumentWorkspace } from '../components/workspace/DocumentWorkspace';
import { api } from '../services/api';
import { PDF_CITATION, PDF_DOCUMENT } from './pdfFixtures';
import { SUMMARY } from './summaryFixtures';
import { pdfMock } from './pdfMock';

const { webcrypto } = await vi.importActual<{ webcrypto: Crypto }>('node:crypto');

const response = {
  document_id: PDF_CITATION.document_id, conversation_id: 'f'.repeat(32), turn_id: 'a'.repeat(32),
  answer: 'Synthetic answer [1]', is_out_of_scope: false, citations: [PDF_CITATION],
};
beforeEach(() => {
  sessionStorage.clear(); pdfMock.pages = 3; pdfMock.fail = false;
  vi.stubGlobal('innerWidth', 1280); vi.stubGlobal('crypto', webcrypto);
  vi.stubGlobal('ResizeObserver', class { observe() {} disconnect() {} });
  vi.spyOn(api, 'getDocumentSummary').mockResolvedValue(SUMMARY);
  vi.spyOn(api, 'sendChatQuery').mockResolvedValue(response);
  vi.spyOn(api, 'resolveCitation').mockImplementation(async (_id, citation) => ({
    ...citation, chunk_set_id: citation.chunk_set_id || 'd'.repeat(64), parse_run_id: 'e'.repeat(32),
  }));
});
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });
async function ask(page = 2) {
  fireEvent.click(screen.getByRole('tab', { name: 'AI Chatbot' }));
  fireEvent.change(screen.getByRole('textbox', { name: 'Question' }), { target: { value: 'Synthetic question?' } });
  fireEvent.click(screen.getByRole('button', { name: 'Send Message' }));
  return screen.findByRole('button', { name: 'Open citation 1, page ' + page });
}
const open = () => fireEvent.click(screen.getByRole('button', { name: 'View Original PDF' }));
const close = () => fireEvent.click(screen.getByRole('button', { name: 'Close PDF' }));
const pageInput = () => screen.getByRole('spinbutton', { name: 'PDF page number' });

it('starts full-width with no viewer, controls, placeholder or PDF request', async () => {
  const url = vi.spyOn(api, 'getPdfStreamUrl');
  render(<DocumentWorkspace document={PDF_DOCUMENT} />);
  await screen.findByText('Synthetic method.');
  expect(screen.queryByTestId('pdf-viewer-panel')).not.toBeInTheDocument();
  expect(screen.queryByRole('spinbutton', { name: 'PDF page number' })).not.toBeInTheDocument();
  expect(screen.queryByText('Upload a PDF to view its pages.')).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'View Original PDF' })).toHaveAttribute('aria-expanded', 'false');
  expect(screen.getByTestId('workspace-grid')).not.toHaveClass('md:grid-cols-[minmax(0,11fr)_minmax(0,9fr)]');
  expect(url).not.toHaveBeenCalled();
});

it('preserves the same PDF instance, page and zoom across close and reopen', async () => {
  render(<DocumentWorkspace document={PDF_DOCUMENT} />); open();
  await screen.findByText('of 3');
  const pdf = screen.getByTestId('pdf-document');
  expect(screen.getByTestId('workspace-grid')).toHaveClass('md:grid-cols-[minmax(0,11fr)_minmax(0,9fr)]');
  fireEvent.click(screen.getByRole('button', { name: 'Next Page' }));
  fireEvent.click(screen.getByRole('button', { name: 'Zoom In' })); close();
  expect(screen.queryByRole('region', { name: 'Original PDF' })).not.toBeInTheDocument();
  expect(pdf).not.toBeVisible();
  expect(screen.getByTestId('workspace-grid')).not.toHaveClass('md:grid-cols-[minmax(0,11fr)_minmax(0,9fr)]');
  open();
  expect(screen.getByTestId('pdf-document')).toBe(pdf);
  expect(pageInput()).toHaveValue(2);
  expect(screen.getByLabelText('PDF zoom')).toHaveTextContent('125%');
});

it('opens citations without losing chat or draft and repeats jumps after manual navigation', async () => {
  render(<DocumentWorkspace document={PDF_DOCUMENT} />);
  const link = await ask(), messages = screen.getByLabelText('Chat messages');
  const sources = screen.getByText('Sources (1)').closest('details');
  expect(sources).not.toHaveAttribute('open');
  fireEvent.change(screen.getByRole('textbox', { name: 'Question' }), { target: { value: 'Unsent follow-up' } });
  fireEvent.click(link);
  await waitFor(() => expect(pageInput()).toHaveValue(2));
  expect(screen.getAllByTestId('pdf-viewer-panel')).toHaveLength(1);
  expect(messages).toBeVisible();
  expect(sources).not.toHaveAttribute('open');
  fireEvent.click(screen.getByRole('button', { name: 'Next Page' })); fireEvent.click(link);
  await waitFor(() => expect(pageInput()).toHaveValue(2)); close();
  expect(screen.getByLabelText('Chat messages')).toBe(messages);
  expect(screen.getByRole('textbox', { name: 'Question' })).toHaveValue('Unsent follow-up');
  expect(api.sendChatQuery).toHaveBeenCalledTimes(1);
  expect(api.resolveCitation).toHaveBeenCalledTimes(2);
  expect(api.resolveCitation).toHaveBeenLastCalledWith(PDF_DOCUMENT.id, PDF_CITATION);
});

it('navigates to page 7 and then page 3 in the existing viewer', async () => {
  pdfMock.pages = 9;
  const seven = { ...PDF_CITATION, page_number: 7, citation_id: '7'.repeat(64) };
  const three = { ...PDF_CITATION, page_number: 3, citation_id: '3'.repeat(64) };
  vi.mocked(api.sendChatQuery).mockResolvedValue({ ...response, answer: 'Finding [1]. Another [2].', citations: [seven, three] });
  render(<DocumentWorkspace document={{ ...PDF_DOCUMENT, page_count: 9 }} />);
  fireEvent.click(await ask(7)); await waitFor(() => expect(pageInput()).toHaveValue(7));
  const pdf = screen.getByTestId('pdf-document');
  fireEvent.click(screen.getByRole('button', { name: 'Open citation 2, page 3' }));
  await waitFor(() => expect(pageInput()).toHaveValue(3));
  expect(screen.getByTestId('pdf-document')).toBe(pdf);
});

it('opens summary sources in the same viewer and preserves summary across toggles and tabs', async () => {
  render(<DocumentWorkspace document={PDF_DOCUMENT} />);
  const method = await screen.findByText('Synthetic method.');
  fireEvent.click(screen.getByRole('button', { name: 'Open source for Methodology, page 2' }));
  await waitFor(() => expect(pageInput()).toHaveValue(2));
  expect(api.resolveCitation).toHaveBeenCalledWith(PDF_DOCUMENT.id, expect.objectContaining({
    document_id: SUMMARY.document_id, chunk_id: SUMMARY.sources[0].chunk_id,
    chunk_set_id: SUMMARY.chunk_set_id, page_number: 2, quote_snippet: SUMMARY.sources[0].quote,
  }));
  close();
  fireEvent.click(screen.getByRole('tab', { name: 'AI Chatbot' }));
  fireEvent.click(screen.getByRole('tab', { name: 'Structured Summary' }));
  expect(screen.getByText('Synthetic method.')).toBe(method);
  expect(api.getDocumentSummary).toHaveBeenCalledTimes(1);
});

it('opens an accessible full-screen mobile viewer and restores conversation and focus', async () => {
  vi.stubGlobal('innerWidth', 375);
  render(<DocumentWorkspace document={PDF_DOCUMENT} />);
  const link = await ask(); fireEvent.click(link);
  const dialog = await screen.findByRole('dialog', { name: 'Original PDF' });
  expect(dialog).toHaveAttribute('aria-modal', 'true'); expect(dialog).toHaveClass('fixed', 'inset-0');
  const closeButton = within(dialog).getByRole('button', { name: 'Close PDF' });
  expect(closeButton).toHaveFocus(); expect(screen.getByLabelText('Chat messages')).not.toBeVisible();
  await screen.findByText('Source — Page 2');
  fireEvent.keyDown(document, { key: 'Tab', shiftKey: true });
  expect(within(dialog).getByRole('button', { name: 'Clear source' })).toHaveFocus();
  fireEvent.keyDown(document, { key: 'Tab' }); expect(closeButton).toHaveFocus();
  closeButton.blur(); fireEvent.keyDown(document, { key: 'Tab' });
  expect(closeButton).toHaveFocus();
  fireEvent.keyDown(document, { key: 'Escape' });
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  expect(link).toBeVisible(); expect(link).toHaveFocus();
  expect(api.sendChatQuery).toHaveBeenCalledTimes(1);
});

it.each([0, 9, 1.5])('rejects source page %s before loading a PDF', async page => {
  vi.mocked(api.sendChatQuery).mockResolvedValue({ ...response, citations: [{ ...PDF_CITATION, page_number: page }] });
  render(<DocumentWorkspace document={PDF_DOCUMENT} />); fireEvent.click(await ask(page));
  expect(screen.getByRole('alert')).toHaveTextContent('That source page is not available');
  expect(screen.queryByTestId('pdf-viewer-panel')).not.toBeInTheDocument();
  expect(api.resolveCitation).not.toHaveBeenCalled();
});

it('rejects returned citations from another document', async () => {
  vi.mocked(api.sendChatQuery).mockResolvedValue({ ...response, citations: [{ ...PDF_CITATION, document_id: '507f1f77bcf86cd799439012' }] });
  render(<DocumentWorkspace document={PDF_DOCUMENT} />);
  fireEvent.click(screen.getByRole('tab', { name: 'AI Chatbot' }));
  fireEvent.change(screen.getByRole('textbox', { name: 'Question' }), { target: { value: 'Question?' } });
  fireEvent.click(screen.getByRole('button', { name: 'Send Message' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Chat is unavailable');
  expect(screen.queryByTestId('pdf-viewer-panel')).not.toBeInTheDocument();
  expect(api.resolveCitation).not.toHaveBeenCalled();
});

it('resets navigation and ignores late source replies when selecting another document', async () => {
  let finish: (value: typeof PDF_CITATION) => void = () => {};
  vi.mocked(api.resolveCitation).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  const view = render(<DocumentWorkspace document={PDF_DOCUMENT} />);
  fireEvent.click(await ask()); fireEvent.click(await screen.findByRole('button', { name: 'Zoom In' }));
  await act(async () => { view.rerender(<DocumentWorkspace document={{ ...PDF_DOCUMENT, id: '507f1f77bcf86cd799439012' }} />); finish(PDF_CITATION); });
  expect(screen.queryByTestId('pdf-viewer-panel')).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Open citation 1, page 2' })).not.toBeInTheDocument();
  expect(screen.getByRole('tab', { name: 'Structured Summary' })).toHaveAttribute('aria-selected', 'true');
  open(); await screen.findByText('of 3');
  expect(pageInput()).toHaveValue(1);
  expect(screen.getByLabelText('PDF zoom')).toHaveTextContent('100%');
});

it('preserves an explicitly requested chat tab while toggling PDF', async () => {
  await act(async () => { render(<DocumentWorkspace document={PDF_DOCUMENT} initialTab="chat" />); });
  await act(async () => { open(); });
  await screen.findByText('of 3'); close();
  expect(screen.getByRole('tab', { name: 'AI Chatbot' })).toHaveAttribute('aria-selected', 'true');
  expect(screen.getByRole('textbox', { name: 'Question' })).toBeInTheDocument();
});


it('supports arrow keys, Home and End on the Workspace tabs without discarding the summary', async () => {
  render(<DocumentWorkspace document={PDF_DOCUMENT} />);
  const method = await screen.findByText('Synthetic method.');
  const summary = screen.getByRole('tab', { name: 'Structured Summary' });
  const chat = screen.getByRole('tab', { name: 'AI Chatbot' });
  summary.focus(); fireEvent.keyDown(summary, { key: 'ArrowRight' });
  expect(chat).toHaveFocus(); expect(chat).toHaveAttribute('aria-selected', 'true');
  expect(summary).toHaveAttribute('tabindex', '-1');
  fireEvent.keyDown(chat, { key: 'Home' });
  expect(summary).toHaveFocus(); expect(method).toBeVisible();
  fireEvent.keyDown(summary, { key: 'End' }); expect(chat).toHaveFocus();
  expect(api.getDocumentSummary).toHaveBeenCalledTimes(1);
});

it('makes the global header inert only while the mobile PDF overlay is open', async () => {
  vi.stubGlobal('innerWidth', 375);
  const view = render(<><header data-app-header><button>Global navigation</button></header><DocumentWorkspace document={PDF_DOCUMENT} /></>);
  open();
  expect(document.querySelector('[data-app-header]')).toHaveAttribute('inert');
  close(); expect(document.querySelector('[data-app-header]')).not.toHaveAttribute('inert');
  open(); view.unmount();
  expect(document.querySelector('[data-app-header]')).toBeNull();
});


it('keeps the PDF open with the same page and zoom across responsive changes', async () => {
  render(<DocumentWorkspace document={PDF_DOCUMENT} />); open();
  await screen.findByText('of 3');
  fireEvent.click(screen.getByRole('button', { name: 'Next Page' }));
  fireEvent.click(screen.getByRole('button', { name: 'Zoom In' }));
  const pdf = screen.getByTestId('pdf-document');
  for (const width of [375, 768, 1024, 1280, 1440, 1920]) {
    act(() => { vi.stubGlobal('innerWidth', width); fireEvent(window, new Event('resize')); });
    expect(screen.getByTestId('pdf-document')).toBe(pdf);
    expect(pageInput()).toHaveValue(2);
    expect(screen.getByLabelText('PDF zoom')).toHaveTextContent('125%');
    expect(screen.getByRole(width < 768 ? 'dialog' : 'region', { name: 'Original PDF' })).toBeVisible();
  }
});
