import { test as base, expect } from '@playwright/test'
import { apiURL } from './env'

/**
 * Test fixtures for read-only smoke tests.
 *
 * - Every non-GET request to the API is refused inside the browser and fails the test.
 *   Nothing is created, changed or generated, whatever environment the tests point at.
 * - Uncaught page errors fail the test.
 */
export const test = base.extend<{ readOnlyGuard: undefined }>({
  readOnlyGuard: [
    async ({ page }, use) => {
      const blockedWrites: string[] = []
      const pageErrors: string[] = []

      await page.route(`${apiURL}/**`, (route) => {
        const request = route.request()
        if (request.method() === 'GET') return route.continue()
        blockedWrites.push(`${request.method()} ${request.url()}`)
        return route.fulfill({
          status: 403,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Blocked: smoke tests are read-only' }),
        })
      })
      page.on('pageerror', (error) => pageErrors.push(error.message))

      await use(undefined)

      expect(blockedWrites, 'the page attempted to write to the API').toEqual([])
      expect(pageErrors, 'uncaught errors in the page').toEqual([])
    },
    { auto: true },
  ],
})

export { expect }
