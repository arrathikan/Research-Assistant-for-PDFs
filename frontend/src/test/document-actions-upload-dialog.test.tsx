import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import App from '../App';
import { DashboardView } from '../views/DashboardView';
import { UploadView } from '../views/UploadView';
import { api, ApiError } from '../services/api';
import type { UploadResponse } from '../types';
import { ID, PAPER, QUEUED, READY, STORED, SUMMARY } from './uploadFixtures';

beforeEach(() => {
  sessionStorage.clear();
  vi.useFakeTimers();
  vi.spyOn(api, 'uploadDocument').mockResolvedValue(STORED);
  vi.spyOn(api, 'getDocument').mockResolvedValue(PAPER);
  vi.spyOn(api, 'getProcessingStatus').mockResolvedValue(QUEUED);
  vi.spyOn(api, 'getDocumentSummary').mockResolvedValue(SUMMARY);
  vi.spyOn(api, 'deleteDocument').mockResolvedValue(undefined);
});
afterEach(() => { vi.useRealTimers(); vi.restoreAllMocks(); });
const file = (name = 'paper.pdf') => new File(['%PDF-1.7 synthetic'], name, { type: 'application/pdf' });
const nav = (name: string) => fireEvent.click(within(screen.getByRole('navigation', { name: 'Main Navigation' })).getByRole('button', { name }));
function openUpload() { fireEvent.click(screen.getByTestId('main-upload-trigger')); }
async function submit() {
  await act(async () => {
    fireEvent.change(screen.getByTestId('file-input'), { target: { files: [file()] } });
    fireEvent.click(screen.getByRole('button', { name: 'Upload paper' }));
  });
}
async function uploadIntoLibrary() {
  nav('Upload Paper'); openUpload(); await submit();
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Go to Dashboard' })); });
}
function askDelete() {
  fireEvent.click(screen.getByRole('button', { name: /Paper actions/ }));
  fireEvent.click(screen.getByRole('menuitem', { name: 'Delete Paper' }));
  return screen.getByRole('dialog', { name: 'Delete research paper?' });
}

it('opens one labelled native upload dialog, restores focus and keeps the main page uncluttered', async () => {
  render(<UploadView onUploadSuccess={vi.fn()} />);
  const trigger = screen.getByTestId('main-upload-trigger'); trigger.focus();
  expect(screen.queryByTestId('file-input')).not.toBeInTheDocument();
  openUpload();
  const dialog = screen.getByRole('dialog', { name: 'Upload Research Paper' });
  expect(dialog.tagName).toBe('DIALOG');
  expect(dialog).toContainElement(document.activeElement as HTMLElement);
  expect(within(dialog).getByRole('button', { name: 'Upload paper' })).toBeDisabled();
  await act(async () => { fireEvent.click(within(dialog).getByRole('button', { name: 'Cancel' })); });
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  expect(trigger).toHaveFocus();
});

it('opens the modal on a drop, keeps the selected file inside it and allows replacing/removing it', () => {
  render(<UploadView onUploadSuccess={vi.fn()} />);
  fireEvent.drop(screen.getByTestId('main-upload-trigger'), { dataTransfer: { files: [file('dropped.pdf')] } });
  const dialog = screen.getByRole('dialog');
  expect(dialog).toContainElement(screen.getByText('dropped.pdf'));
  const input = screen.getByTestId('file-input');
  const browse = vi.spyOn(input, 'click');
  fireEvent.click(screen.getByRole('button', { name: 'Browse Files' }));
  expect(browse).toHaveBeenCalledOnce();
  fireEvent.change(input, { target: { files: [file('replacement.pdf')] } });
  expect(screen.queryByText('dropped.pdf')).not.toBeInTheDocument();
  expect(screen.getAllByText('replacement.pdf')).toHaveLength(1);
  fireEvent.click(screen.getByRole('button', { name: 'Remove selected PDF' }));
  expect(screen.queryByText('replacement.pdf')).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Upload paper' })).toBeDisabled();
});

it('uses the same PDF, single-file and size validation for main-page drops and modal selection', () => {
  render(<UploadView onUploadSuccess={vi.fn()} />);
  fireEvent.drop(screen.getByTestId('main-upload-trigger'), { dataTransfer: { files: [new File(['x'], 'bad.txt')] } });
  expect(screen.getByRole('alert')).toHaveTextContent('Invalid file format');
  const huge = file(); Object.defineProperty(huge, 'size', { value: 26 * 1024 * 1024 });
  fireEvent.change(screen.getByTestId('file-input'), { target: { files: [huge] } });
  expect(screen.getByRole('alert')).toHaveTextContent('25 MB');
  fireEvent.drop(screen.getByTestId('dropzone'), { dataTransfer: { files: [file(), file()] } });
  expect(screen.getByRole('alert')).toHaveTextContent('exactly one');
  expect(api.uploadDocument).not.toHaveBeenCalled();
});

it('preserves an active HTTP upload when closed and navigated away, then adds its actual stored result', async () => {
  let finish!: (response: UploadResponse) => void;
  vi.mocked(api.uploadDocument).mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  render(<App />); nav('Upload Paper'); openUpload(); await submit();
  expect(screen.getByText('Uploading')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Close upload' }));
  expect(screen.getByText(/upload is continuing in the background/)).toBeInTheDocument();
  nav('Dashboard');
  await act(async () => { finish(STORED); });
  expect(screen.getByTestId('document-card')).toHaveTextContent('paper.pdf');
  expect(api.uploadDocument).toHaveBeenCalledOnce();
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
});

it('adds a queued upload immediately, closes with Done and polls real metadata after returning to Dashboard', async () => {
  render(<App />); nav('Upload Paper'); openUpload(); await submit();
  await act(async () => { await vi.advanceTimersByTimeAsync(2000); });
  expect(screen.getByText('Queued')).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Open Workspace' })).not.toBeInTheDocument();
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Done' })); });
  nav('Dashboard');
  expect(screen.getByTestId('document-card')).toHaveTextContent('Uploaded');
  vi.mocked(api.getDocument).mockResolvedValue({ ...PAPER, status: 'PARSING' });
  await act(async () => { await vi.advanceTimersByTimeAsync(3000); });
  expect(screen.getByTestId('document-card')).toHaveTextContent('Processing');
  vi.mocked(api.getDocument).mockResolvedValue(READY);
  await act(async () => { await vi.advanceTimersByTimeAsync(3000); });
  expect(screen.getByTestId('document-card')).toHaveTextContent('Ready');
  expect(api.uploadDocument).toHaveBeenCalledOnce();
  expect(api.deleteDocument).not.toHaveBeenCalled();
});

it('keeps retrying metadata reads after a temporary failure without inventing readiness or removing the paper', async () => {
  render(<App />); await uploadIntoLibrary();
  vi.mocked(api.getDocument).mockRejectedValueOnce(new ApiError(503, 'private failure'));
  await act(async () => { await vi.advanceTimersByTimeAsync(3000); });
  expect(screen.getByTestId('document-card')).toHaveTextContent('Uploaded');
  vi.mocked(api.getDocument).mockResolvedValue(READY);
  await act(async () => { await vi.advanceTimersByTimeAsync(3000); });
  expect(screen.getByTestId('document-card')).toHaveTextContent('Ready');
});

it('opens paper actions by keyboard with Workspace, original PDF and destructive Delete entries', async () => {
  render(<DashboardView documents={[PAPER]} onSelectDocument={vi.fn()} onNavigateUpload={vi.fn()} onDeleteDocument={paper => api.deleteDocument(paper.id!)} />);
  const trigger = screen.getByRole('button', { name: /Paper actions/ }); trigger.focus();
  fireEvent.keyDown(trigger, { key: 'ArrowDown' });
  await act(async () => { await vi.advanceTimersByTimeAsync(20); });
  const workspace = screen.getByRole('menuitem', { name: 'Open Workspace' });
  expect(workspace).toHaveFocus();
  fireEvent.keyDown(workspace, { key: 'End' });
  expect(screen.getByRole('menuitem', { name: 'Delete Paper' })).toHaveFocus();
  fireEvent.keyDown(document.activeElement!, { key: 'ArrowUp' });
  expect(screen.getByRole('menuitem', { name: /View Original PDF/ })).toHaveFocus();
  expect(screen.getByRole('menuitem', { name: /View Original PDF/ })).toHaveAttribute('href', api.getPdfStreamUrl(ID));
  fireEvent.keyDown(document.activeElement!, { key: 'Escape' });
  expect(screen.queryByRole('menu')).not.toBeInTheDocument();
  expect(trigger).toHaveFocus();
});

it('opens a confirmation with safe Cancel focus; Cancel never calls the API', async () => {
  render(<App />); await uploadIntoLibrary();
  const dialog = askDelete();
  expect(within(dialog).getByRole('button', { name: 'Cancel' })).toHaveFocus();
  expect(dialog).toHaveTextContent('paper.pdf');
  expect(api.deleteDocument).not.toHaveBeenCalled();
  await act(async () => { fireEvent.click(within(dialog).getByRole('button', { name: 'Cancel' })); });
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  expect(screen.getByTestId('document-card')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /Paper actions/ })).toHaveFocus();
  expect(api.deleteDocument).not.toHaveBeenCalled();
});

it('confirms deletion once, waits for success, then updates filtered cards, counts, storage and selected Workspace', async () => {
  let finish!: () => void;
  vi.mocked(api.deleteDocument).mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  render(<App />); await uploadIntoLibrary();
  fireEvent.click(within(screen.getByTestId('document-card')).getByRole('button', { name: 'paper.pdf' }));
  nav('Dashboard'); sessionStorage.setItem('researchai.chat.' + ID, 'synthetic-conversation');
  fireEvent.change(screen.getByRole('searchbox', { name: 'Search papers' }), { target: { value: 'paper' } });
  const dialog = askDelete(), confirm = within(dialog).getByRole('button', { name: 'Delete Paper' });
  fireEvent.click(confirm); fireEvent.click(confirm);
  expect(api.deleteDocument).toHaveBeenCalledOnce();
  expect(api.deleteDocument).toHaveBeenCalledWith(ID);
  expect(within(dialog).getByRole('button', { name: 'Deleting…' })).toBeDisabled();
  expect(within(dialog).getByRole('button', { name: 'Cancel' })).toBeDisabled();
  const cancel = new Event('cancel', { cancelable: true }); fireEvent(dialog, cancel);
  expect(cancel.defaultPrevented).toBe(true);
  expect(screen.getByTestId('document-card')).toBeInTheDocument();
  await act(async () => { finish(); });
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  expect(screen.queryByTestId('document-card')).not.toBeInTheDocument();
  const stats = within(screen.getByRole('region', { name: 'Library statistics' }));
  expect(stats.getByText('Total Research Papers').parentElement?.firstElementChild).toHaveTextContent('0');
  expect(stats.getByText('PDF Storage').parentElement?.firstElementChild).toHaveTextContent('0.0 KB');
  expect(within(screen.getByRole('navigation')).queryByRole('button', { name: 'Workspace' })).not.toBeInTheDocument();
  expect(sessionStorage.getItem('researchai.chat.' + ID)).toBeNull();
});

it.each([409, 503])('keeps the paper after a %s delete failure and allows an explicit retry', async status => {
  vi.mocked(api.deleteDocument).mockRejectedValueOnce(new ApiError(status, 'private details')).mockResolvedValueOnce(undefined);
  render(<App />); await uploadIntoLibrary();
  const dialog = askDelete();
  await act(async () => { fireEvent.click(within(dialog).getByRole('button', { name: 'Delete Paper' })); });
  expect(within(dialog).getByRole('alert')).not.toHaveTextContent('private details');
  expect(screen.getByTestId('document-card')).toBeInTheDocument();
  await act(async () => { fireEvent.click(within(dialog).getByRole('button', { name: 'Delete Paper' })); });
  expect(api.deleteDocument).toHaveBeenCalledTimes(2);
  expect(screen.queryByTestId('document-card')).not.toBeInTheDocument();
});

it('does not resurrect a deleted paper when an older metadata request finishes late', async () => {
  let stale!: (paper: typeof PAPER) => void;
  vi.mocked(api.getDocument).mockImplementationOnce(() => new Promise(resolve => { stale = resolve; }));
  render(<App />); await uploadIntoLibrary();
  const dialog = askDelete();
  await act(async () => { fireEvent.click(within(dialog).getByRole('button', { name: 'Delete Paper' })); });
  await act(async () => { stale(PAPER); });
  expect(screen.queryByTestId('document-card')).not.toBeInTheDocument();
});
