import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { DocumentSummaryPanel } from '../components/summary/DocumentSummaryPanel';
import { SUMMARY as RESULT } from './summaryFixtures';
import { api, ApiError } from '../services/api';
import type { SummaryResponse } from '../types/summary';

const ID = '507f1f77bcf86cd799439011';
const OTHER_ID = '507f1f77bcf86cd799439012';


afterEach(() => { vi.restoreAllMocks(); vi.useRealTimers(); });

describe('DocumentSummaryPanel', () => {
  it('shows loading then five saved sections and source quotes', async () => {
    vi.spyOn(api, 'getDocumentSummary').mockResolvedValue(RESULT);
    render(<DocumentSummaryPanel documentId={ID} filename="synthetic.pdf" />);
    expect(screen.getByText('Loading summary…')).toBeInTheDocument();
    expect(await screen.findByText('Synthetic method.')).toBeInTheDocument();
    for (const title of ['Title, Authors and Abstract', 'Problem Statement', 'Methodology', 'Key Results', 'Conclusion']) {
      expect(screen.getByRole('heading', { name: title })).toBeInTheDocument();
    }
    expect(screen.getByText('Authors: Ada Example')).toBeInTheDocument();
    expect(screen.getByText('Page 2')).toBeInTheDocument();
    expect(screen.getByText('A synthetic source quote.')).not.toBeVisible();
    fireEvent.click(screen.getByText('Supporting passages'));
    expect(screen.getByText('A synthetic source quote.')).toBeVisible();
  });

  it('keeps missing information explicit without sample authors', async () => {
    vi.spyOn(api, 'getDocumentSummary').mockResolvedValue({ ...RESULT, authors: [], unavailable_fields: ['authors'] });
    render(<DocumentSummaryPanel documentId={ID} filename="synthetic.pdf" />);
    expect(await screen.findByText('Authors: Not stated in the document.')).toBeInTheDocument();
    expect(screen.queryByText('Authors: Ada Example')).not.toBeInTheDocument();
  });

  it('polls a pending summary without starting generation', async () => {
    vi.useFakeTimers();
    const get = vi.spyOn(api, 'getDocumentSummary').mockRejectedValueOnce(new ApiError(409, 'pending')).mockResolvedValueOnce(RESULT);
    await act(async () => { render(<DocumentSummaryPanel documentId={ID} filename="synthetic.pdf" />); });
    expect(screen.getByText('Summary not ready yet. Checking for updates…')).toBeInTheDocument();
    await act(async () => { await vi.advanceTimersByTimeAsync(5000); });
    expect(screen.getByText('Synthetic method.')).toBeInTheDocument();
    expect(get).toHaveBeenCalledTimes(2);
  });

  it('shows failure and can recheck without fabricated content', async () => {
    const get = vi.spyOn(api, 'getDocumentSummary').mockRejectedValueOnce(new ApiError(503, 'failed')).mockResolvedValueOnce(RESULT);
    render(<DocumentSummaryPanel documentId={ID} filename="synthetic.pdf" />);
    expect(await screen.findByRole('alert')).toHaveTextContent('The summary is unavailable.');
    expect(screen.queryByText('Synthetic method.')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Check again' }));
    expect(await screen.findByText('Synthetic method.')).toBeInTheDocument();
    expect(get).toHaveBeenCalledTimes(2);
  });

  it('ignores a late response after switching documents', async () => {
    let finish: (result: SummaryResponse) => void = () => {};
    vi.spyOn(api, 'getDocumentSummary').mockImplementationOnce(() => new Promise(resolve => { finish = resolve; })).mockResolvedValueOnce({ ...RESULT, document_id: OTHER_ID, title: 'New paper' });
    const view = render(<DocumentSummaryPanel documentId={ID} filename="old.pdf" />);
    view.rerender(<DocumentSummaryPanel documentId={OTHER_ID} filename="new.pdf" />);
    await waitFor(() => expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('New paper'));
    await act(async () => { finish(RESULT); });
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('New paper');
    expect(screen.queryByText('Synthetic paper')).not.toBeInTheDocument();
  });

  it('rejects a response for a different document', async () => {
    vi.spyOn(api, 'getDocumentSummary').mockResolvedValue({ ...RESULT, document_id: OTHER_ID });
    render(<DocumentSummaryPanel documentId={ID} filename="synthetic.pdf" />);
    expect(await screen.findByRole('alert')).toHaveTextContent('could not be matched');
    expect(screen.queryByText('Synthetic method.')).not.toBeInTheDocument();
  });

  it('does not fetch a sample or missing document ID', () => {
    const get = vi.spyOn(api, 'getDocumentSummary');
    render(<DocumentSummaryPanel documentId="doc_sample" filename="sample.pdf" />);
    expect(screen.getByText('Upload a PDF to view its generated summary.')).toBeInTheDocument();
    expect(get).not.toHaveBeenCalled();
  });
});
