import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { DashboardView } from '../views/DashboardView';
import { visiblePapers } from '../components/dashboard/library';
import { UploadStatusCard } from '../components/upload/UploadStatusCard';
import { READY, PAPER } from './uploadFixtures';
import type { DocumentMetadata } from '../types';

const papers: DocumentMetadata[] = [
  { ...READY, filename: 'Zebra.pdf', created_at: '2026-11-10T00:00:00Z' },
  { ...PAPER, id: '2'.repeat(24), sha256: '2'.repeat(64), filename: 'Alpha 10.pdf', status: 'PARSING', created_at: '2026-11-11T00:00:00Z' },
  { ...PAPER, id: '3'.repeat(24), sha256: '3'.repeat(64), filename: 'Alpha 2.pdf', status: 'FAILED' },
  { ...PAPER, id: '4'.repeat(24), sha256: '4'.repeat(64), filename: 'Queued.pdf' },
];
function dashboard() { return render(<DashboardView documents={papers} onSelectDocument={vi.fn()} onNavigateUpload={vi.fn()} />); }

describe('reference paper library', () => {
  it('counts actual ready and active states without treating queued or failed as processing', () => {
    dashboard();
    const statistics = within(screen.getByRole('region', { name: 'Library statistics' }));
    for (const [label, value] of [['Total Papers', '4'], ['Ready to Explore', '1'], ['Processing', '1'], ['Storage Used', '4.0 MB']]) {
      expect(statistics.getByText(label).parentElement?.firstElementChild).toHaveTextContent(value);
    }
    expect(screen.getAllByRole('table')).toHaveLength(1);
    expect(screen.getByRole('columnheader', { name: 'Paper' })).toBeInTheDocument();
  });
  it('combines filename search and status filtering and restores input focus when cleared', () => {
    dashboard();
    fireEvent.change(screen.getByRole('combobox', { name: 'Filter by status' }), { target: { value: 'processing' } });
    expect(screen.getAllByTestId('document-card')).toHaveLength(1);
    expect(screen.getByTestId('document-card')).toHaveTextContent('Alpha 10.pdf');
    fireEvent.change(screen.getByRole('searchbox', { name: 'Search papers' }), { target: { value: 'zebra' } });
    expect(screen.getByRole('heading', { name: 'No matching papers found' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Clear search' }));
    expect(screen.getByRole('searchbox', { name: 'Search papers' })).toHaveFocus();
    expect(screen.getAllByTestId('document-card')).toHaveLength(1);
  });
  it('sorts dates numerically and filenames naturally without mutating input documents', () => {
    const original = [...papers];
    expect(visiblePapers(papers, '', 'all', 'oldest')[0].filename).toBe('Zebra.pdf');
    expect(visiblePapers(papers, '', 'all', 'name').map(doc => doc.filename)).toEqual(['Alpha 2.pdf', 'Alpha 10.pdf', 'Queued.pdf', 'Zebra.pdf']);
    expect(papers).toEqual(original);
    dashboard();
    fireEvent.change(screen.getByRole('combobox', { name: 'Sort papers' }), { target: { value: 'oldest' } });
    expect(screen.getAllByTestId('document-card')[0]).toHaveTextContent('Zebra.pdf');
    expect(screen.getByRole('columnheader', { name: 'Uploaded' })).toHaveAttribute('aria-sort', 'ascending');
  });
  it('enables each shortcut only when its underlying data is available', () => {
    dashboard();
    const ready = within(screen.getAllByTestId('document-card').find(row => row.textContent?.includes('Zebra.pdf'))!);
    expect(ready.getByRole('button', { name: 'Summary' })).toBeEnabled();
    expect(ready.getByRole('button', { name: 'Chat' })).toBeEnabled();
    const processing = within(screen.getAllByTestId('document-card').find(row => row.textContent?.includes('Alpha 10.pdf'))!);
    expect(processing.getByRole('button', { name: 'Summary' })).toBeDisabled();
    expect(processing.getByRole('button', { name: 'Chat' })).toBeDisabled();
  });
  it.each(['queued', 'processing', 'ready', 'failed'] as const)('uses the supplied stage illustration only for the actual %s upload state', stage => {
    const { container } = render(<UploadStatusCard filename="paper.pdf" stage={stage} description="Current backend status" />);
    expect(container.querySelector('[data-art-kind]')).toHaveAttribute('data-art-kind', stage === 'processing' || stage === 'ready' ? stage : 'paper');
  });
});
