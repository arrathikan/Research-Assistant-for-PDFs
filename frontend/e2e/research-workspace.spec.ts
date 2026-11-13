import { expect, test } from '@playwright/test';
import { OTHER_ID, PAPER, QUEUED } from '../src/test/uploadFixtures';
import { citation, expectNoOverflow, mockPaperApi, openWorkspace, selectFile } from './fixtures';

const pageErrors = new WeakMap<import('@playwright/test').Page, string[]>();
test.beforeEach(({ page }) => {
  const errors: string[] = [];
  pageErrors.set(page, errors);
  page.on('pageerror', error => errors.push(error.message));
});
test.afterEach(({ page }) => { expect(pageErrors.get(page)).toEqual([]); });

test('upload dialog supports keyboard dismissal and restores focus', async ({ page }) => {
  await mockPaperApi(page);
  await page.getByRole('navigation', { name: 'Main Navigation' }).getByRole('button', { name: 'Upload Paper', exact: true }).click();
  const trigger = page.getByTestId('main-upload-trigger');
  await trigger.focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('dialog', { name: 'Upload Research Paper' })).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).not.toBeVisible();
  await expect(trigger).toBeFocused();
});

test('queued and processing stay unready until completed metadata and summary', async ({ page }) => {
  const state = await mockPaperApi(page);
  state.document = { ...PAPER, page_count: 7 };
  state.job = { ...QUEUED };
  await selectFile(page);
  await expect(page.getByText('Queued', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Open Workspace', exact: true })).toHaveCount(0);
  state.job = { ...QUEUED, status: 'RUNNING', step: 'parsing' };
  await expect(page.getByText('Processing', { exact: true })).toBeVisible();
  state.document = { ...state.document, status: 'READY', embedding_status: 'COMPLETED' };
  state.job = { ...state.job, status: 'COMPLETED' };
  await expect(page.getByRole('button', { name: 'Open Workspace', exact: true })).toBeVisible();
  await expect(page.getByText(PAPER.id!, { exact: false })).toHaveCount(0);
});

test('processing failure offers supported retry without claiming completion', async ({ page }) => {
  const state = await mockPaperApi(page);
  state.document = { ...PAPER, status: 'FAILED' };
  state.job = { ...QUEUED, status: 'DEAD_LETTER', error_code: 'SUMMARY_FAILED' };
  await selectFile(page);
  await expect(page.getByRole('button', { name: 'Retry processing' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Open Workspace', exact: true })).toHaveCount(0);
  state.job = { ...QUEUED, stage: 'summary' };
  await page.getByRole('button', { name: 'Retry processing' }).click();
  await expect(page.getByText('Processing', { exact: true })).toBeVisible();
});

test('failed upload can retry; a new upload clears previous file state', async ({ page }) => {
  const state = await mockPaperApi(page);
  state.uploadFails = true;
  await selectFile(page, 'first.pdf');
  await expect(page.getByRole('button', { name: 'Retry upload' })).toBeVisible();
  state.uploadFails = false;
  await page.getByRole('button', { name: 'Retry upload' }).click();
  await expect(page.getByRole('button', { name: 'Open Workspace', exact: true })).toBeVisible();
  expect(state.uploads).toBe(2);
  await page.getByRole('button', { name: 'Done', exact: true }).click();
  await page.getByTestId('main-upload-trigger').click();
  await expect(page.getByText('first.pdf', { exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Browse Files' })).toBeVisible();
});

test('citations open actual PDF pages; exact highlight, page fallback, zoom and chat survive toggles', async ({ page }) => {
  const state = await mockPaperApi(page);
  state.response.citations.push({ ...citation(3), quote_snippet: 'Extracted Markdown with different formatting.' });
  state.response.answer += ' A source with different PDF text formatting [3].';
  await openWorkspace(page);
  await expect(page.getByTestId('pdf-viewer-panel')).toHaveCount(0);
  await page.getByRole('tab', { name: 'AI Chatbot' }).click();
  await page.getByRole('textbox', { name: 'Question', exact: true }).fill('What are the findings?');
  await page.getByRole('button', { name: 'Send Message' }).click();
  await expect(page.getByRole('log')).toContainText('The first finding');
  await page.getByRole('textbox', { name: 'Question', exact: true }).fill('Keep my draft');
  await page.getByRole('button', { name: 'Open citation 1, page 7' }).click();
  const number = page.getByRole('spinbutton', { name: 'PDF page number' });
  await expect(number).toHaveValue('7');
  await expect(page.getByTestId('pdf-source-highlight').first()).toBeVisible();
  await expect(page.locator('[data-highlight-kind="text"]')).toBeVisible();
  await page.getByRole('button', { name: 'Open citation 2, page 2' }).click();
  await expect(number).toHaveValue('2');
  await page.getByRole('button', { name: 'Zoom in' }).click();
  await expect(page.getByLabel('PDF zoom')).toContainText('125%');
  const loads = state.pdfLoads;
  const summaryLoads = state.summaryLoads;
  await page.getByRole('button', { name: 'Close PDF', exact: true }).click();
  await expect(page.getByTestId('pdf-viewer-panel')).not.toBeVisible();
  await expect(page.getByRole('textbox', { name: 'Question', exact: true })).toHaveValue('Keep my draft');
  await expect(page.getByRole('log')).toContainText('The first finding');
  await page.getByRole('button', { name: 'View Original PDF', exact: true }).click();
  await expect(number).toHaveValue('2');
  await expect(page.getByLabel('PDF zoom')).toContainText('125%');
  expect(state.pdfLoads).toBe(loads);
  await page.getByRole('button', { name: 'Open citation 3, page 3' }).click();
  await expect(number).toHaveValue('3');
  await expect(page.locator('[data-highlight-kind="page"]')).toBeVisible();
  await expect(page.getByText(/coordinate|exact highlighting unavailable/i)).toHaveCount(0);
  state.resolveFails = true;
  await page.getByRole('button', { name: 'Open citation 1, page 7' }).click();
  await expect(page.getByRole('alert')).toContainText('We couldn’t open this source');
  await expect(number).toHaveValue('3');
  await page.getByRole('button', { name: 'Close PDF', exact: true }).click();
  await page.getByRole('tab', { name: 'Structured Summary' }).click();
  await expect(page.getByText('Synthetic method.', { exact: true })).toBeVisible();
  expect(state.summaryLoads).toBe(summaryLoads); // PDF/tab toggles do not reload the summary.
});

test('invalid page and foreign-document citations are handled safely', async ({ page }) => {
  const state = await mockPaperApi(page);
  state.response.citations = [citation(99)];
  state.response.answer = 'Synthetic invalid source [1].';
  await openWorkspace(page);
  await page.getByRole('tab', { name: 'AI Chatbot' }).click();
  await page.getByRole('textbox', { name: 'Question', exact: true }).fill('Invalid source');
  await page.getByRole('button', { name: 'Send Message' }).click();
  await page.getByRole('button', { name: 'Open citation 1, page 99' }).click();
  await expect(page.getByRole('alert')).toContainText('source page is not available');
  await expect(page.getByTestId('pdf-viewer-panel')).toHaveCount(0);
  state.response.citations = [{ ...citation(1), document_id: OTHER_ID }];
  await page.getByRole('textbox', { name: 'Question', exact: true }).fill('Foreign source');
  await page.getByRole('button', { name: 'Send Message' }).click();
  await expect(page.getByRole('alert').filter({ hasText: 'Chat is unavailable' })).toBeVisible();
  await expect(page.getByTestId('pdf-viewer-panel')).toHaveCount(0);
});

for (const width of [375, 768, 1024, 1280, 1440, 1920]) {
  test(`dashboard, upload, summary and PDF layout at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await mockPaperApi(page);
    await expectNoOverflow(page);
    const shots = process.env.RESEARCHAI_QA_SCREENSHOTS;
    if (shots) await page.screenshot({ path: `${shots}/dashboard-${width}.png` });
    await page.getByRole('navigation', { name: 'Main Navigation' }).getByRole('button', { name: 'Upload Paper', exact: true }).click();
    if (shots) await page.screenshot({ path: `${shots}/upload-${width}.png` });
    await openWorkspace(page);
    if (shots) await page.screenshot({ path: `${shots}/summary-${width}.png` });
    if (width >= 1280) {
      const card = page.locator('header').filter({ has: page.getByRole('heading', { name: 'Synthetic research paper' }) });
      const bounds = await card.boundingBox();
      const available = await page.getByTestId('page-container').boundingBox();
      expect(bounds?.width).toBeGreaterThanOrEqual(Math.min(1100, available!.width - 66));
      expect(bounds?.width).toBeLessThanOrEqual(1200);
    }
    await expectNoOverflow(page);
    await page.getByRole('button', { name: 'View Original PDF', exact: true }).click();
    await expect(page.getByRole('spinbutton', { name: 'PDF page number' })).toBeVisible();
    await expect(page.locator('canvas')).toBeVisible();
    if (shots) await page.screenshot({ path: `${shots}/pdf-${width}.png` });
    await expectNoOverflow(page);
    if (width < 768) {
      await expect(page.getByRole('dialog', { name: 'Original PDF' })).toBeVisible();
      await expect(page.getByRole('button', { name: 'Close PDF', exact: true })).toBeFocused();
      await page.keyboard.press('Escape');
    } else {
      const columns = await page.getByTestId('workspace-grid').evaluate(element => getComputedStyle(element).gridTemplateColumns.split(' ').map(Number.parseFloat));
      expect(columns[0] / columns[1]).toBeCloseTo(11 / 9, 1);
      await page.getByRole('button', { name: 'Close PDF', exact: true }).click();
    }
    await expect(page.getByRole('heading', { name: 'Synthetic research paper' })).toBeVisible();
    await expectNoOverflow(page);
    await page.getByRole('tab', { name: 'AI Chatbot' }).click();
    await expect(page.getByRole('textbox', { name: 'Question', exact: true })).toBeVisible();
    await expectNoOverflow(page);
  });
}


test('paper menu and delete dialog cancel preserve the document', async ({ page }) => {
  await mockPaperApi(page);
  await openWorkspace(page);
  await page.getByRole('navigation', { name: 'Main Navigation' }).getByRole('button', { name: 'Dashboard', exact: true }).click();
  const trigger = page.getByRole('button', { name: 'Paper actions for paper.pdf' });
  for (let attempt = 0; attempt < 2; attempt++) {
    await trigger.click();
    await page.getByText('Delete Paper', { exact: true }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Cancel', exact: true })).toBeFocused();
    await page.getByRole('button', { name: 'Cancel', exact: true }).click();
    await expect(page.getByRole('dialog')).not.toBeVisible();
    await expect(trigger).toBeFocused();
    await expect(page.getByTestId('document-card')).toHaveCount(1);
  }
});


test('dragging a PDF into the upload page selects it without a duplicate upload', async ({ page }) => {
  const state = await mockPaperApi(page);
  await page.getByRole('navigation', { name: 'Main Navigation' }).getByRole('button', { name: 'Upload Paper', exact: true }).click();
  const transfer = await page.evaluateHandle(() => {
    const data = new DataTransfer();
    data.items.add(new File(['%PDF-1.4 synthetic drop selection'], 'dropped.pdf', { type: 'application/pdf' }));
    return data;
  });
  await page.getByTestId('main-upload-trigger').dispatchEvent('drop', { dataTransfer: transfer });
  await transfer.dispose();
  await expect(page.getByText('dropped.pdf', { exact: true })).toBeVisible();
  expect(state.uploads).toBe(0);
  await page.getByRole('button', { name: 'Upload paper', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Open Workspace', exact: true })).toBeVisible();
  expect(state.uploads).toBe(1);
});
