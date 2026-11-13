import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { PdfViewerBoundary } from '../components/pdf/PdfViewerBoundary';
import { api } from '../services/api';
import { DocumentCard } from '../components/dashboard/DocumentCard';
import { DocumentStatusBadge } from '../components/common/DocumentStatusBadge';
import { PDF_DOCUMENT } from './pdfFixtures';

describe('ResearchAI controls', () => {
  it.each([['PENDING', 'Uploaded'], ['PARSING', 'Processing'], ['EMBEDDING', 'Processing'], ['SUMMARIZING', 'Processing'], ['READY', 'Ready'], ['FAILED', 'Failed']] as const)('uses friendly text for %s without changing the underlying status', (status, label) => {
    render(<DocumentStatusBadge status={status} testId="status" />);
    expect(screen.getByTestId('status')).toHaveTextContent(label);
    expect(screen.getByTestId('status')).toHaveAttribute('data-status', status);
  });
  it('opens a document title with the keyboard using a real button', async () => {
    const select = vi.fn();
    render(<DocumentCard document={PDF_DOCUMENT} onOpen={select} />);
    const title = screen.getByRole('button', { name: PDF_DOCUMENT.filename });
    title.focus(); await userEvent.keyboard('{Enter}');
    expect(select).toHaveBeenCalledWith(PDF_DOCUMENT);
    fireEvent.click(screen.getByRole('button', { name: /Paper actions/ }));
    await screen.findByRole('menuitem', { name: 'Open Workspace' });
    fireEvent.click(screen.getByRole('menuitem', { name: 'Open Workspace' }));
    expect(select).toHaveBeenCalledTimes(2);
  });
});


it('contains optional PDF code/render failures without removing the conversation', () => {
  const error = vi.spyOn(console, 'error').mockImplementation(() => {});
  const Broken = (): never => { throw new Error('Synthetic viewer download failure'); };
  try {
    render(<><p>Existing conversation</p><PdfViewerBoundary documentId={PDF_DOCUMENT.id}><Broken /></PdfViewerBoundary></>);
    expect(screen.getByText('Existing conversation')).toBeVisible();
    expect(screen.getByRole('alert')).toHaveTextContent('The PDF viewer couldn’t open');
    expect(screen.getByRole('link', { name: /Open original PDF/ })).toHaveAttribute('href', api.getPdfStreamUrl(PDF_DOCUMENT.id!));
  } finally { error.mockRestore(); }
});
