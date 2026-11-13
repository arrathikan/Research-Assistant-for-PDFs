import { expect, test, type Locator, type Page } from '@playwright/test';
import { mockPaperApi, expectNoOverflow, selectFile, openWorkspace } from './fixtures';
import { PAPER, READY, QUEUED } from '../src/test/uploadFixtures';
import type { DocumentMetadata } from '../src/types';

const PRIMARY = 'rgb(198, 54, 10)', SOFT = 'rgb(255, 241, 235)', HOVER = 'rgb(168, 46, 10)';
async function color(element: Locator, property: string) {
  return element.evaluate((node, name) => getComputedStyle(node).getPropertyValue(name), property);
}
async function shot(page: Page, name: string) {
  if (process.env.RESEARCHAI_QA_SCREENSHOTS) await page.screenshot({ path: `${process.env.RESEARCHAI_QA_SCREENSHOTS}/${name}.png` });
}
const navigation = (page: Page) => page.getByRole('navigation', { name: 'Main Navigation' });

// Browser fixtures exercise API contracts; no provider calls or fabricated production documents.
test('reference dashboard uses real metadata, semantic colors and responsive table controls', async ({ page }) => {
  const errors: string[] = []; page.on('pageerror', error => errors.push(error.message));
  const state = await mockPaperApi(page);
  const records: DocumentMetadata[] = [
    { ...READY, filename: 'Ready paper.pdf' },
    { ...PAPER, id: '2'.repeat(24), sha256: '2'.repeat(64), filename: 'Processing paper.pdf', status: 'PARSING', created_at: '2026-11-11T00:00:00Z' },
    { ...PAPER, id: '3'.repeat(24), sha256: '3'.repeat(64), filename: 'Queued paper.pdf', created_at: '2026-11-10T00:00:00Z' },
    { ...PAPER, id: '4'.repeat(24), sha256: '4'.repeat(64), filename: 'Failed paper.pdf', status: 'FAILED', created_at: '2026-11-09T00:00:00Z' },
  ];
  for (const record of records) {
    state.document = record;
    state.job = { ...QUEUED, document_id: record.id!, status: record.status === 'READY' ? 'COMPLETED' : record.status === 'FAILED' ? 'DEAD_LETTER' : record.status === 'PENDING' ? 'QUEUED' : 'RUNNING' };
    await selectFile(page, record.filename);
    await expect(page.getByRole('dialog')).toContainText(record.filename);
    await page.getByRole('button', { name: 'Done', exact: true }).click();
  }
  await navigation(page).getByRole('button', { name: 'Dashboard', exact: true }).click();
  const stats = page.getByRole('region', { name: 'Library statistics' });
  await expect(stats.getByText('Total Papers').locator('..')).toContainText('4');
  await expect(stats.getByText('Ready to Explore').locator('..')).toContainText('1');
  await expect(stats.getByText('Processing', { exact: true }).locator('..')).toContainText('1');
  await expect(stats.getByText('Storage Used').locator('..')).toContainText('4.0 MB');
  await expect(page.getByTestId('document-card')).toHaveCount(4);
  for (const width of [375, 768, 1024, 1280, 1440, 1920]) {
    await page.setViewportSize({ width, height: 960 });
    await expectNoOverflow(page);
    await expect(page.getByRole('table')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Ready paper.pdf', exact: true })).toBeVisible();
    await shot(page, `reference-library-${width}`);
    if (width === 375) {
      await page.getByTestId('document-card').first().scrollIntoViewIfNeeded();
      await shot(page, 'reference-library-papers-375');
      await page.getByRole('heading', { name: 'Paper Library', exact: true }).scrollIntoViewIfNeeded();
    }
  }
  const active = navigation(page).getByRole('button', { name: 'Dashboard', exact: true });
  expect(await color(active, 'background-color')).toBe(SOFT);
  expect(await color(active, 'color')).toBe(HOVER);
  expect(await color(stats.locator('.ui-card').first(), 'background-color')).toBe('rgb(255, 255, 255)');
  const search = page.getByRole('searchbox', { name: 'Search papers' });
  await search.fill('paper'); await search.focus();
  expect(await color(search, 'border-top-color')).toBe(PRIMARY);
  await page.getByRole('button', { name: 'Clear search' }).click();
  await expect(search).toBeFocused(); await expect(search).toHaveValue('');
  const filter = page.getByRole('combobox', { name: 'Filter by status' });
  await filter.selectOption('processing'); await filter.focus();
  expect(await color(filter, 'border-top-color')).toBe(PRIMARY);
  await expect(page.getByTestId('document-card')).toHaveCount(1);
  await expect(page.getByTestId('document-card')).toContainText('Processing paper.pdf');
  await expect(page.getByTestId('document-card').getByRole('button', { name: 'Summary', exact: true })).toBeDisabled();
  const badge = page.getByTestId('document-card').locator('[data-status="PARSING"]');
  expect(await color(badge, 'background-color')).toBe('rgb(255, 251, 235)');
  await filter.selectOption('all');
  await page.getByRole('combobox', { name: 'Sort papers' }).selectOption('oldest');
  await expect(page.getByTestId('document-card').first()).toContainText('Failed paper.pdf');
  const primary = page.getByRole('main').getByRole('button', { name: 'Upload Paper', exact: true });
  await primary.hover(); await expect.poll(() => color(primary, 'background-color')).toBe(HOVER);
  await page.mouse.down(); await expect.poll(() => color(primary, 'background-color')).toBe('rgb(143, 38, 8)');
  await page.mouse.move(0, 0); await page.mouse.up();
  const ready = page.getByTestId('document-card').filter({ hasText: 'Ready paper.pdf' });
  expect(await color(ready.getByRole('button', { name: 'Chat', exact: true }), 'color')).toBe(PRIMARY);
  await ready.getByRole('button', { name: 'Paper actions for Ready paper.pdf' }).click();
  await page.getByLabel('Actions for Ready paper.pdf', { exact: true }).getByText('Delete Paper', { exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Delete research paper?' });
  await expect(dialog).toBeVisible();
  expect(await color(dialog.getByRole('button', { name: 'Delete Paper', exact: true }), 'background-color')).toBe('rgb(220, 38, 38)');
  await shot(page, 'reference-delete-modal');
  await page.getByRole('button', { name: 'Cancel', exact: true }).click();
  expect(errors).toEqual([]);
});

test('shared orange controls work throughout upload, summary, chat, citations and PDF', async ({ page }) => {
  const errors: string[] = []; page.on('pageerror', error => errors.push(error.message));
  await page.setViewportSize({ width: 1440, height: 960 });
  const state = await mockPaperApi(page);
  await navigation(page).getByRole('button', { name: 'Upload Paper', exact: true }).click();
  await shot(page, 'reference-upload-1440');
  await page.getByTestId('main-upload-trigger').click();
  await shot(page, 'reference-upload-modal');
  await page.keyboard.press('Escape');
  await openWorkspace(page);
  await expect(page.getByTestId('pdf-viewer-panel')).toHaveCount(0);
  const summaryTab = page.getByRole('tab', { name: 'Structured Summary' });
  expect(await color(summaryTab, 'background-color')).toBe(SOFT);
  await shot(page, 'reference-summary-1440');
  const pdfToggle = page.getByRole('button', { name: 'View Original PDF', exact: true });
  expect(await color(pdfToggle, 'color')).toBe(PRIMARY);
  await page.getByRole('tab', { name: 'AI Chatbot' }).click();
  const question = page.getByRole('textbox', { name: 'Question', exact: true });
  await question.fill('What are the findings?');
  expect(await color(question, 'border-top-color')).toBe(PRIMARY);
  const send = page.getByRole('button', { name: 'Send Message' });
  expect(await color(send, 'background-color')).toBe(PRIMARY);
  await shot(page, 'reference-chat-1440');
  await send.click();
  const source = page.getByRole('button', { name: 'Open citation 1, page 7' });
  expect(await color(source, 'color')).toBe(PRIMARY);
  await source.click();
  const number = page.getByRole('spinbutton', { name: 'PDF page number' });
  await expect(number).toHaveValue('7'); await expect(page.getByTestId('pdf-source-highlight').first()).toBeVisible();
  await number.focus(); expect(await color(number, 'border-top-color')).toBe(PRIMARY);
  await page.getByRole('button', { name: 'Zoom In', exact: true }).click();
  await expect(page.getByLabel('PDF zoom')).toHaveText('125%');
  await shot(page, 'reference-citation-pdf-1440');
  await page.getByRole('button', { name: 'Close PDF', exact: true }).click();
  await source.click(); await expect(number).toHaveValue('7');
  expect(state.pdfLoads).toBe(1);
  await page.setViewportSize({ width: 375, height: 960 });
  await expect(page.getByRole('dialog', { name: 'Original PDF' })).toBeVisible();
  await expect(page.locator('[data-app-navigation]')).toHaveAttribute('inert', '');
  await shot(page, 'reference-citation-pdf-375');
  await page.keyboard.press('Escape');
  await expect(page.locator('[data-app-navigation]')).not.toHaveAttribute('inert', '');
  await expect(page.getByText('The first finding is supported here', { exact: false })).toBeVisible();
  await expectNoOverflow(page); expect(errors).toEqual([]);
});
