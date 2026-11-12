import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import App from '../App';
import { api } from '../services/api';
import { ID, QUEUED, READY, STORED, SUMMARY } from './uploadFixtures';

vi.mock('react-pdf', async () => import('./pdfMock'));
beforeEach(() => {
  sessionStorage.clear(); vi.useFakeTimers();
  vi.spyOn(api, 'uploadDocument').mockResolvedValue({ ...STORED, document: READY });
  vi.spyOn(api, 'getDocument').mockResolvedValue(READY);
  vi.spyOn(api, 'getProcessingStatus').mockResolvedValue({ ...QUEUED, status: 'COMPLETED' });
  vi.spyOn(api, 'getDocumentSummary').mockResolvedValue(SUMMARY);
});
afterEach(() => { vi.useRealTimers(); vi.restoreAllMocks(); });
const navigate = (name: string) => fireEvent.click(within(screen.getByRole('navigation', { name: 'Main Navigation' })).getByRole('button', { name }));
async function upload() {
  navigate('Upload Paper');
  await act(async () => {
    fireEvent.change(screen.getByTestId('file-input'), { target: { files: [new File(['%PDF-1.7'], 'paper.pdf', { type: 'application/pdf' })] } });
    fireEvent.click(screen.getByRole('button', { name: 'Upload paper' }));
  });
  await act(async () => { await vi.advanceTimersByTimeAsync(2000); });
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'View Summary' })); });
}

it('starts with an honest empty library and an actionable first-upload state', () => {
  render(<App />);
  expect(screen.getByRole('heading', { name: 'No research papers uploaded yet' })).toBeInTheDocument();
  expect(screen.queryByTestId('document-card')).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Workspace' })).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Upload First Paper' })).toBeInTheDocument();
  expect(api.getDocument).not.toHaveBeenCalled();
});

it('opens Summary and Chat from their library shortcuts for the real selected document', async () => {
  render(<App />); await upload(); navigate('Dashboard');
  expect(screen.getAllByTestId('document-card')).toHaveLength(1);
  const card = screen.getByTestId('document-card');
  await act(async () => { fireEvent.click(within(card).getByRole('button', { name: 'Chat' })); });
  expect(screen.getByRole('tab', { name: 'AI Chatbot' })).toHaveAttribute('aria-selected', 'true');
  expect(screen.getByRole('textbox', { name: 'Question' })).toBeInTheDocument();
  navigate('Dashboard');
  await act(async () => { fireEvent.click(within(screen.getByTestId('document-card')).getByRole('button', { name: 'Summary' })); });
  expect(screen.getByRole('tab', { name: 'Structured Summary' })).toHaveAttribute('aria-selected', 'true');
  expect(api.getDocumentSummary).toHaveBeenCalledWith(ID);
});

it('keeps one library card after uploading the same stored document again', async () => {
  render(<App />); await upload(); navigate('Dashboard');
  expect(screen.getAllByTestId('document-card')).toHaveLength(1);
  vi.mocked(api.uploadDocument).mockResolvedValue({ ...STORED, document: READY, is_duplicate: true });
  await upload(); navigate('Dashboard');
  expect(screen.getAllByTestId('document-card')).toHaveLength(1);
  expect(within(screen.getByRole('region', { name: 'Library statistics' })).getByText('Total Research Papers').parentElement?.firstElementChild).toHaveTextContent('1');
});
