import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { summaryCitation } from '../services/citations';
import { DocumentSummaryPanel } from '../components/summary/DocumentSummaryPanel';
import { api } from '../services/api';
import { SUMMARY } from './summaryFixtures';

const { webcrypto } = await vi.importActual<{ webcrypto: Crypto }>('node:crypto');

beforeEach(() => { vi.stubGlobal('crypto', webcrypto); vi.spyOn(api, 'getDocumentSummary').mockResolvedValue(SUMMARY); });
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });
it('builds the existing backend SHA-256 citation identity from real summary fields', async () => {
  const citation = await summaryCitation(SUMMARY, SUMMARY.sources[0]);
  expect(citation).toEqual({
    citation_id: '8354e65555ac71e523e60374a3d867ff17113fa3f97d9954a7b599250b210f99', document_id: SUMMARY.document_id, chunk_id: SUMMARY.sources[0].chunk_id,
    page_number: 2, quote_snippet: SUMMARY.sources[0].quote, chunk_set_id: SUMMARY.chunk_set_id,
  });
});
it('shows a friendly source error when secure hashing is unavailable', async () => {
  vi.stubGlobal('crypto', {});
  render(<DocumentSummaryPanel documentId={SUMMARY.document_id} filename="paper.pdf" onCitationClick={vi.fn()} />);
  fireEvent.click(await screen.findByRole('button', { name: 'Open source for Methodology, page 2' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('You can still view the original PDF');
});
it('ignores a pending summary-source selection after the document changes', async () => {
  let finish: (value: ArrayBuffer) => void = () => {};
  vi.stubGlobal('crypto', { subtle: { digest: () => new Promise<ArrayBuffer>(resolve => { finish = resolve; }) } });
  const select = vi.fn();
  const view = render(<DocumentSummaryPanel documentId={SUMMARY.document_id} filename="old.pdf" onCitationClick={select} />);
  fireEvent.click(await screen.findByRole('button', { name: 'Open source for Methodology, page 2' }));
  const other = '507f1f77bcf86cd799439012';
  vi.mocked(api.getDocumentSummary).mockResolvedValue({ ...SUMMARY, document_id: other });
  await act(async () => { view.rerender(<DocumentSummaryPanel documentId={other} filename="new.pdf" onCitationClick={select} />); });
  await act(async () => { finish(new Uint8Array(32).buffer); });
  expect(select).not.toHaveBeenCalled();
});
