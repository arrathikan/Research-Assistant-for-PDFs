import { defineConfig, devices } from '@playwright/test';

const live = process.env.RESEARCHAI_LIVE_QA === '1';
const origin = live ? 'http://localhost:5173' : 'http://127.0.0.1:4173';

export default defineConfig({
  testDir: './e2e',
  testMatch: live ? '**/*.live.ts' : '**/*.spec.ts',
  outputDir: live ? 'test-results/live' : 'test-results/browser',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,
  timeout: 45_000,
  reporter: 'list',
  use: {
    baseURL: origin,
    channel: process.env.PLAYWRIGHT_CHROMIUM_CHANNEL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: `npm run dev -- --host ${live ? 'localhost' : '127.0.0.1'} --port ${live ? 5173 : 4173} --strictPort`,
    url: origin,
    reuseExistingServer: false,
    env: { VITE_API_BASE_URL: live ? 'http://localhost:8000/api/v1' : '/api/v1' },
  },
});
