import { afterEach, beforeEach, describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DocumentWorkspaceView } from '../views/DocumentWorkspaceView';
import { api } from '../services/api';
vi.mock('react-pdf', async () => import('./pdfMock'));
import { pdfMock } from './pdfMock';
import type { DocumentMetadata } from '../types';
import type { ChatResponse } from '../types/chat';

const ID = '507f1f77bcf86cd799439011';
const mockDoc: DocumentMetadata = { id: ID, sha256: 'a'.repeat(64), filename: 'synthetic.pdf', file_size_bytes: 200,
  page_count: 7, status: 'READY', created_at: '2026-11-11T00:00:00Z', updated_at: '2026-11-11T00:00:00Z' };
const response: ChatResponse = { document_id: ID, conversation_id: 'b'.repeat(32), turn_id: 'c'.repeat(32),
  answer: 'Synthetic answer [1]', is_out_of_scope: false, citations: [{ document_id: ID, citation_id: 'd'.repeat(64), chunk_id: 'e'.repeat(64), page_number: 7, quote_snippet: 'Synthetic evidence.' }] };
beforeEach(() => { pdfMock.pages = 7; vi.stubGlobal('ResizeObserver', class { observe() {} disconnect() {} }); sessionStorage.clear(); vi.spyOn(api, 'resolveCitation').mockResolvedValue({ ...response.citations[0], chunk_set_id: 'f'.repeat(64), parse_run_id: 'g'.repeat(32) }); vi.spyOn(api, 'getDocumentSummary').mockImplementation(() => new Promise(() => {})); });
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });

describe('DocumentWorkspaceView', () => {
  it('keeps all five summary section headings', async () => {
    render(<DocumentWorkspaceView document={mockDoc} />);
    expect(screen.queryByTestId('pdf-viewer-panel')).not.toBeInTheDocument();
    for (const title of ['Title, Authors and Abstract', 'Problem Statement', 'Methodology', 'Key Results', 'Conclusion']) {
      expect(screen.getByRole('heading', { name: title })).toBeInTheDocument();
    }
  });
  it('switches to the real chatbot', async () => {
    render(<DocumentWorkspaceView document={mockDoc} />);
    expect(screen.queryByTestId('pdf-viewer-panel')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('tab', { name: /AI Chatbot/i }));
    expect(screen.getByPlaceholderText(/Ask a question about this research paper/i)).toBeInTheDocument();
  });
  it('sends a question and shows the actual API response', async () => {
    vi.spyOn(api, 'sendChatQuery').mockResolvedValue(response);
    render(<DocumentWorkspaceView document={mockDoc} />);
    expect(screen.queryByTestId('pdf-viewer-panel')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('tab', { name: /AI Chatbot/i }));
    fireEvent.change(screen.getByRole('textbox', { name: 'Question' }), { target: { value: 'Synthetic question?' } });
    fireEvent.click(screen.getByRole('button', { name: 'Send Message' }));
    expect(await screen.findByText('Synthetic answer', { exact: false })).toBeInTheDocument();
    expect(screen.getByText('Synthetic question?')).toBeInTheDocument();
  });
  it('passes returned source references to the existing PDF panel', async () => {
    vi.spyOn(api, 'sendChatQuery').mockResolvedValue(response);
    render(<DocumentWorkspaceView document={mockDoc} />);
    expect(screen.queryByTestId('pdf-viewer-panel')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('tab', { name: /AI Chatbot/i }));
    fireEvent.change(screen.getByRole('textbox', { name: 'Question' }), { target: { value: 'Synthetic question?' } });
    fireEvent.click(screen.getByRole('button', { name: 'Send Message' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Open citation 1, page 7' }));
    expect(await screen.findByText('Source — Page 7')).toBeInTheDocument();
  });
});
