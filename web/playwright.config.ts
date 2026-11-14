import { defineConfig, devices } from '@playwright/test'

/**
 * Browser smoke tests. They only read: no login, and every non-GET API request is
 * blocked by the fixtures in e2e/fixtures.ts, so they are safe to point at any
 * environment.
 *
 *   pnpm test:e2e                                         # local stack (API + pnpm dev running)
 *   E2E_BASE_URL=https://artificial-u.com pnpm test:e2e   # production, read-only
 */
const baseURL = process.env.E2E_BASE_URL ?? 'http://localhost:5173'

export default defineConfig({
  testDir: './e2e',
  globalSetup: './e2e/global-setup.ts',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  timeout: 30_000,
  use: {
    baseURL,
    locale: 'en-US',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
})
