import { createHash } from 'node:crypto';
import { expect, test, type Page } from '@playwright/test';
import { expectNoOverflow, mockPaperApi, openWorkspace } from './fixtures';

function contrast(foreground: string, background: string) {
  const luminance = (value: string) => {
    const [r, g, b] = (value.match(/[\d.]+/g) ?? []).slice(0, 3).map(channel => {
      const n = Number(channel) / 255;
      return n <= 0.04045 ? n / 12.92 : ((n + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const values = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
  return (values[0] + 0.05) / (values[1] + 0.05);
}

async function screenshot(page: Page, name: string) {
  const directory = process.env.RESEARCHAI_QA_SCREENSHOTS;
  if (directory) await page.screenshot({ path: `${directory}/${name}.png` });
}

test('exact transparent logo, favicon and requested brand colors load in the browser', async ({ page }) => {
  await mockPaperApi(page);
  await expect(page).toHaveTitle('Paper Library | ResearchAI');
  const logo = page.getByTestId('brand-logo');
  await expect.poll(() => logo.evaluate((image: HTMLImageElement) => image.naturalWidth)).toBe(1254);
  const source = await logo.getAttribute('src');
  expect(source).toBeTruthy();
  const response = await page.request.get(source!);
  expect(createHash('sha256').update(await response.body()).digest('hex')).toBe('4e419b0878e838ff7b3bc3cda453de62bbfb873979c970682aca202f1384a7da');
  await expect(page.locator('link[rel="icon"]')).toHaveAttribute('href', '/src/assets/researchai-logo.png');
  const button = page.getByRole('main').getByRole('button', { name: 'Upload Paper', exact: true });
  const colors = await button.evaluate(element => ({ color: getComputedStyle(element).color, background: getComputedStyle(element).backgroundColor }));
  expect(colors.background).toBe('rgb(198, 54, 10)');
  expect(contrast(colors.color, colors.background)).toBeGreaterThanOrEqual(4.5);
  await button.hover();
  await expect.poll(() => button.evaluate(element => getComputedStyle(element).backgroundColor)).toBe('rgb(168, 46, 10)');
  await expectNoOverflow(page);
});

test('library rows retain search, metadata, shortcuts and safe paper actions at desktop and mobile widths', async ({ page }) => {
  await mockPaperApi(page);
  await openWorkspace(page);
  await page.getByRole('navigation', { name: 'Main Navigation' }).getByRole('button', { name: 'Dashboard', exact: true }).click();
  for (const width of [1440, 375]) {
    await page.setViewportSize({ width, height: 900 });
    const paper = page.getByTestId('document-card');
    await expect(paper).toContainText('paper.pdf');
    await expect(paper).toContainText('1.0 MB');
    await expect(paper).toContainText('Uploaded');
    await expect(paper.getByRole('button', { name: 'Summary', exact: true })).toBeVisible();
    await expect(paper.getByRole('button', { name: 'Chat', exact: true })).toBeVisible();
    const search = page.getByRole('searchbox', { name: 'Search papers' });
    await search.fill('no-match');
    await expect(page.getByRole('heading', { name: 'No matching papers found' })).toBeVisible();
    await search.fill('paper');
    await expect(paper).toBeVisible();
    await expectNoOverflow(page);
    await screenshot(page, `library-populated-${width}`);
  }
});

test('reading sections adapt to pane width and page-number chips keep their verified targets', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await mockPaperApi(page);
  await openWorkspace(page);
  const section = page.getByRole('heading', { name: 'Methodology', exact: true }).locator('..');
  await expect.poll(() => section.evaluate(element => getComputedStyle(element).display)).toBe('grid');
  await expect(page.getByText('Synthetic research paper', { exact: true })).toHaveCount(1);
  await page.getByRole('button', { name: 'View Original PDF', exact: true }).click();
  await expect.poll(() => section.evaluate(element => getComputedStyle(element).display)).toBe('block');
  await page.getByRole('button', { name: 'Close PDF', exact: true }).click();
  await page.getByRole('tab', { name: 'AI Chatbot' }).click();
  await screenshot(page, 'chat-empty-1440');
  await page.getByRole('textbox', { name: 'Question', exact: true }).fill('What are the findings?');
  await page.getByRole('button', { name: 'Send Message' }).click();
  const source = page.getByRole('button', { name: 'Open citation 1, page 7' });
  await expect(source).toHaveText('[Page 7]');
  const colors = await source.evaluate(element => ({ color: getComputedStyle(element).color, background: getComputedStyle(element).backgroundColor }));
  expect(contrast(colors.color, colors.background)).toBeGreaterThanOrEqual(4.5);
  await expect(page.getByRole('list', { name: 'Supporting sources' })).not.toBeVisible();
  await source.click();
  await expect(page.getByRole('spinbutton', { name: 'PDF page number' })).toHaveValue('7');
  await expect(page.getByTestId('pdf-source-highlight').first()).toBeVisible();
  await screenshot(page, 'chat-citation-1440');
  await page.setViewportSize({ width: 375, height: 900 });
  await expect(page.getByRole('dialog', { name: 'Original PDF' })).toBeVisible();
  await page.getByRole('button', { name: 'Close PDF', exact: true }).click();
  await expectNoOverflow(page);
  await screenshot(page, 'chat-answer-375');
});

test('reduced motion and keyboard focus remain usable with the new theme', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await mockPaperApi(page);
  await page.getByRole('navigation', { name: 'Main Navigation' }).getByRole('button', { name: 'Upload Paper', exact: true }).click();
  const trigger = page.getByTestId('main-upload-trigger');
  await trigger.focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('dialog', { name: 'Upload Research Paper' })).toBeVisible();
  await screenshot(page, 'upload-modal-1280');
  await page.keyboard.press('Escape');
  await expect(trigger).toBeFocused();
  const styles = await trigger.evaluate(element => ({ outline: getComputedStyle(element).outlineStyle, transition: getComputedStyle(element).transitionDuration }));
  expect(styles.outline).not.toBe('none');
  expect(styles.transition).toBe('0s');
});
