import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import App from '../App';
import { api, ApiError } from '../services/api';
import { LIBRARY_SESSION_KEY } from '../services/librarySession';
import { ID, OTHER_ID, READY, SUMMARY } from './uploadFixtures';

vi.mock('react-pdf', async () => import('./pdfMock'));
beforeEach(() => {
  sessionStorage.clear();
  vi.spyOn(api, 'getDocumentSummary').mockResolvedValue(SUMMARY);
});
afterEach(() => { vi.restoreAllMocks(); });
function saved(activeTab = 'dashboard', ids = [ID]) {
  sessionStorage.setItem(LIBRARY_SESSION_KEY, JSON.stringify({ ids, activeId: ID, activeTab, workspaceTab: 'summary' }));
}

it('restores a selected paper and saved summary from current API data after a reload', async () => {
  saved('workspace');
  vi.spyOn(api, 'getDocument').mockResolvedValue(READY);
  render(<App />);
  expect(await screen.findByRole('heading', { name: SUMMARY.title }, { timeout: 5000 })).toBeVisible();
  expect(api.getDocumentSummary).toHaveBeenCalledWith(ID);
  expect(screen.getByRole('button', { name: 'Workspace' })).toHaveAttribute('aria-current', 'page');
  expect(screen.queryByTestId('pdf-viewer-panel')).not.toBeInTheDocument();
});

it('restores the actual selected Chat tab and stores references without cached metadata', async () => {
  saved('workspace'); vi.spyOn(api, 'getDocument').mockResolvedValue(READY);
  render(<App />);
  await screen.findByRole('heading', { name: SUMMARY.title }, { timeout: 5000 });
  fireEvent.click(screen.getByRole('tab', { name: 'AI Chatbot' }));
  const state = JSON.parse(sessionStorage.getItem(LIBRARY_SESSION_KEY)!);
  expect(state.workspaceTab).toBe('chat'); expect(state.ids).toEqual([ID]);
  expect(state).not.toHaveProperty('filename'); expect(state).not.toHaveProperty('status');
});

it('removes deleted references and falls back to Dashboard instead of reopening a deleted paper', async () => {
  saved('workspace'); vi.spyOn(api, 'getDocument').mockRejectedValue(new ApiError(404, 'deleted'));
  render(<App />);
  expect(await screen.findByRole('heading', { name: 'No research papers uploaded yet' })).toBeVisible();
  expect(screen.getByRole('button', { name: 'Workspace' })).toBeDisabled();
  expect(JSON.parse(sessionStorage.getItem(LIBRARY_SESSION_KEY)!).ids).toEqual([]);
});

it('retains references on a temporary error and retries the real metadata request', async () => {
  saved();
  const get = vi.spyOn(api, 'getDocument').mockRejectedValueOnce(new ApiError(503, 'unavailable')).mockResolvedValueOnce(READY);
  render(<App />);
  expect(await screen.findByRole('alert')).toHaveTextContent('saved papers have not been removed');
  expect(JSON.parse(sessionStorage.getItem(LIBRARY_SESSION_KEY)!).ids).toEqual([ID]);
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Retry loading papers' })); });
  expect(await screen.findByTestId('document-card')).toHaveTextContent(READY.filename);
  expect(get).toHaveBeenCalledTimes(2);
});

it('does not overwrite a navigation choice during restoration', async () => {
  saved('workspace');
  let finish!: (document: typeof READY) => void;
  vi.spyOn(api, 'getDocument').mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  render(<App />);
  fireEvent.click(within(screen.getByRole('navigation', { name: 'Main Navigation' })).getByRole('button', { name: 'Upload Paper' }));
  await act(async () => finish(READY));
  expect(screen.getByRole('heading', { name: 'Upload a research paper' })).toBeInTheDocument();
});

it('ignores corrupt session data and avoids fetching arbitrary identifiers', () => {
  sessionStorage.setItem(LIBRARY_SESSION_KEY, '{bad json');
  const get = vi.spyOn(api, 'getDocument'); render(<App />);
  expect(screen.getByRole('heading', { name: 'No research papers uploaded yet' })).toBeInTheDocument();
  expect(get).not.toHaveBeenCalled();
});

it('rejects another document returned during session restoration', async () => {
  saved(); vi.spyOn(api, 'getDocument').mockResolvedValue({ ...READY, id: OTHER_ID });
  render(<App />);
  expect(await screen.findByRole('alert')).toHaveTextContent('couldn’t restore');
  expect(screen.queryByTestId('document-card')).not.toBeInTheDocument();
});
