import { afterEach, expect, it, vi } from 'vitest';
import { api } from '../services/api';
import { PDF_CITATION, PDF_ID } from './pdfFixtures';
afterEach(() => { vi.unstubAllGlobals(); });
it('sends only source identity fields and uses canonical geometry from the response', async () => {
  const request = vi.fn().mockResolvedValue({ ok: true, json: async () => PDF_CITATION });
  vi.stubGlobal('fetch', request);
  expect(await api.resolveCitation(PDF_ID, { ...PDF_CITATION, page_width: 99999 })).toEqual(PDF_CITATION);
  const [url, options] = request.mock.calls[0];
  expect(url).toContain(`/documents/${PDF_ID}/citations/resolve`);
  expect(options.method).toBe('POST');
  expect(JSON.parse(options.body)).toEqual({ document_id: PDF_ID, citation_id: PDF_CITATION.citation_id,
    chunk_id: PDF_CITATION.chunk_id, page_number: 2, quote_snippet: PDF_CITATION.quote_snippet,
    chunk_set_id: PDF_CITATION.chunk_set_id, parse_run_id: PDF_CITATION.parse_run_id });
});
it('retains source-conflict status for a useful stale citation message', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 409, json: async () => ({ detail: 'Source changed' }) }));
  await expect(api.resolveCitation(PDF_ID, PDF_CITATION)).rejects.toMatchObject({ status: 409 });
});
