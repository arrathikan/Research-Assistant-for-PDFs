import { expect, type Page } from '@playwright/test';
import { PAPER, QUEUED, READY, SUMMARY } from '../src/test/uploadFixtures';
import type { ChatCitation, ChatResponse } from '../src/types/chat';
import type { DocumentMetadata } from '../src/types';
import type { ProcessingStatus } from '../src/types/processing';

// Generated in memory: no real papers, credentials or provider calls in browser CI.
export function syntheticPdf(): Buffer {
  const objects = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    '<< /Type /Pages /Kids [3 0 R 5 0 R 7 0 R 9 0 R 11 0 R 13 0 R 15 0 R] /Count 7 >>',
  ];
  for (let page = 1; page <= 7; page++) {
    const text = `BT /F1 14 Tf 40 700 Td (Synthetic evidence on page ${page}.) Tj ET`;
    objects.push(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 800] /Resources << /Font << /F1 17 0 R >> >> /Contents ${objects.length + 2} 0 R >>`);
    objects.push(`<< /Length ${Buffer.byteLength(text)} >>\nstream\n${text}\nendstream`);
  }
  objects.push('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>');
  let pdf = '%PDF-1.4\n';
  const offsets = [0];
  objects.forEach((object, index) => {
    offsets.push(Buffer.byteLength(pdf));
    pdf += `${index + 1} 0 obj\n${object}\nendobj\n`;
  });
  const start = Buffer.byteLength(pdf);
  pdf += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  pdf += offsets.slice(1).map(offset => `${String(offset).padStart(10, '0')} 00000 n \n`).join('');
  pdf += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${start}\n%%EOF\n`;
  return Buffer.from(pdf);
}

export function citation(page: number): ChatCitation {
  return {
    document_id: PAPER.id!, citation_id: String(page).repeat(64), chunk_id: 'c'.repeat(64),
    chunk_set_id: 'd'.repeat(64), parse_run_id: 'e'.repeat(32), page_number: page,
    quote_snippet: `Synthetic evidence on page ${page}.`, bounding_boxes: [],
  };
}

export async function mockPaperApi(page: Page) {
  const state: { document: DocumentMetadata; job: ProcessingStatus; uploadFails: boolean; resolveFails: boolean; uploads: number; pdfLoads: number; summaryLoads: number; response: ChatResponse } = {
    document: { ...READY, page_count: 7 }, job: { ...QUEUED, status: 'COMPLETED' },
    uploadFails: false, resolveFails: false, uploads: 0, pdfLoads: 0, summaryLoads: 0,
    response: { document_id: PAPER.id!, conversation_id: 'f'.repeat(32), turn_id: '1'.repeat(32),
      answer: 'The first finding is supported here [1]. Another finding is supported here [2].',
      citations: [citation(7), citation(2)], is_out_of_scope: false },
  };
  const stored = new Map<string, DocumentMetadata>();
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname.replace('/api/v1', '');
    const method = route.request().method();
    const fulfill = (json: unknown, status = 200) => route.fulfill({ status, json });
    if (path === '/health') return fulfill({ status: 'ok', service: 'gateway' });
    if (path === '/documents' && method === 'POST') {
      state.uploads++;
      if (state.uploadFails) return fulfill({ detail: 'Synthetic network failure' }, 503);
      stored.set(state.document.id!, { ...state.document });
      return fulfill({ document: state.document, message: 'Internal message', is_duplicate: false });
    }
    if (path.endsWith('/pdf')) {
      state.pdfLoads++;
      return route.fulfill({ contentType: 'application/pdf', body: syntheticPdf() });
    }
    if (path.endsWith('/processing/retry')) return fulfill(state.job);
    if (path.endsWith('/processing')) return fulfill(state.job);
    if (path.endsWith('/summary')) { state.summaryLoads++; return fulfill(SUMMARY); }
    if (path.endsWith('/citations/resolve')) {
      return state.resolveFails ? fulfill({ detail: 'Unavailable citation' }, 404) : fulfill(route.request().postDataJSON());
    }
    if (path.endsWith('/chat') && method === 'POST') return fulfill(state.response);
    if (path === '/documents/' + state.document.id) return fulfill(state.document);
    const record = stored.get(path.replace('/documents/', ''));
    if (record) return fulfill(record);
    throw new Error(`Unexpected browser API request: ${method} ${path}`);
  });
  await page.goto('/');
  return state;
}

export async function selectFile(page: Page, name = 'paper.pdf') {
  await page.getByRole('navigation', { name: 'Main Navigation' }).getByRole('button', { name: 'Upload Paper', exact: true }).click();
  await page.getByTestId('main-upload-trigger').click();
  await page.getByTestId('file-input').setInputFiles({ name, mimeType: 'application/pdf', buffer: syntheticPdf() });
  await page.getByRole('button', { name: 'Upload paper', exact: true }).click();
}

export async function openWorkspace(page: Page) {
  await selectFile(page);
  await page.getByRole('button', { name: 'Open Workspace', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Synthetic research paper' })).toBeVisible();
}

export async function expectNoOverflow(page: Page) {
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
}
