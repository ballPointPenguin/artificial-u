import type { Page } from '@playwright/test'
import { apiURL } from './env'
import { expect, test } from './fixtures'

/**
 * Read-only smoke tests for the public pages. They make no assumptions about which
 * courses exist beyond "there is at least one published course", and skip the parts
 * that need data the environment does not have.
 */

/** Open the first course in the catalogue and return its path (e.g. /courses/12). */
async function openFirstCourse(page: Page): Promise<string> {
  await page.goto('/courses')
  const firstCourse = page.getByRole('main').locator('table tbody tr a').first()
  await expect(firstCourse, 'the catalogue lists at least one course').toBeVisible()
  await firstCourse.click()
  await expect(page).toHaveURL(/\/courses\/\d+$/)
  return new URL(page.url()).pathname
}

test('home page renders and links to browsing', async ({ page }) => {
  await page.goto('/')

  await expect(page).toHaveTitle(/Artificial University/)
  const nav = page.getByRole('navigation').first()
  await expect(nav.getByRole('link', { name: 'Browse' })).toBeVisible()
  await expect(nav.getByRole('link', { name: 'Login' })).toBeVisible()

  await nav.getByRole('link', { name: 'Browse' }).click()
  await expect(page).toHaveURL(/\/browse/)
  await expect(page.getByRole('heading', { level: 1, name: 'Browse' })).toBeVisible()
})

test('course catalogue opens a course with its details', async ({ page }) => {
  await openFirstCourse(page)

  const main = page.getByRole('main')
  // Course headings read "CODE: Title"
  await expect(main.getByRole('heading', { level: 1 })).toContainText(':')
  await expect(main.getByRole('heading', { name: 'Course Details' })).toBeVisible()
  await expect(main.getByRole('heading', { name: 'Department' })).toBeVisible()
  await expect(main.getByRole('heading', { name: 'Professor' })).toBeVisible()
  await expect(main.getByRole('heading', { name: 'Course Topics' })).toBeVisible()
})

test('a lecture page shows the lecture and plays its audio', async ({ page, request }) => {
  // Ask the API for a recent lecture that has audio, so this works with any data set
  const recent = await request.get(`${apiURL}/v1/lectures/recent?limit=12`)
  expect(recent.ok()).toBe(true)
  const lectures = (await recent.json()) as { id: number; course_id: number; audio_url?: string }[]
  const lecture = lectures.find((candidate) => candidate.audio_url)
  test.skip(!lecture, 'no lecture with audio exists in this environment')
  if (!lecture) return

  await page.goto(`/courses/${String(lecture.course_id)}/lectures/${String(lecture.id)}`)
  const main = page.getByRole('main')
  await expect(main.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(main.getByRole('link', { name: '← Back to Course' })).toBeVisible()

  await main.getByRole('button', { name: 'Play', exact: true }).click()
  await expect(page.getByRole('complementary', { name: 'Now Playing' })).toBeVisible()
  // The audio element is actually playing, not just mounted
  await expect
    .poll(() =>
      page.evaluate(() => {
        const audio = document.querySelector('audio')
        return audio !== null && !audio.paused && audio.currentTime > 0
      })
    )
    .toBe(true)
})

test('search returns results for a course code', async ({ page }) => {
  await openFirstCourse(page)
  const heading = await page.getByRole('main').getByRole('heading', { level: 1 }).innerText()
  const courseCode = heading.split(':')[0].trim()

  await page.goto('/search')
  const searchBox = page.getByRole('searchbox')
  await searchBox.fill(courseCode)
  await searchBox.press('Enter')

  await expect(page).toHaveURL(/\/search\?q=/)
  await expect(page.getByRole('heading', { level: 1, name: /^Results for/ })).toBeVisible()
  await expect(page.getByRole('main').locator('a[href^="/courses/"]').first()).toBeVisible()
})

test('departments list opens a department', async ({ page }) => {
  await page.goto('/departments')
  await expect(page.getByRole('heading', { level: 1, name: 'Departments' })).toBeVisible()

  const firstDepartment = page.getByRole('main').locator('a[href^="/departments/"]').first()
  await expect(firstDepartment, 'at least one department exists').toBeVisible()
  const name = await firstDepartment.getByRole('heading').innerText()

  await firstDepartment.click()
  await expect(page).toHaveURL(/\/departments\/\d+$/)
  await expect(page.getByRole('heading', { name }).first()).toBeVisible()
})

test('pages that need an account ask the visitor to log in', async ({ page }) => {
  await page.goto('/profile')

  await expect(page.getByRole('heading', { name: 'Log In or Sign Up' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Continue with Authentication' })).toBeVisible()
})

for (const path of ['/about', '/about/ai-ethics', '/about/privacy', '/about/terms', '/about/faq']) {
  test(`static page ${path} renders`, async ({ page }) => {
    await page.goto(path)
    await expect(page.getByRole('main').getByRole('heading').first()).toBeVisible()
  })
}

test.describe('API', () => {
  test('health check reports ok', async ({ request }) => {
    const response = await request.get(`${apiURL}/v1/health`)

    expect(response.ok()).toBe(true)
    expect(await response.json()).toMatchObject({ status: 'ok' })
  })

  test('generation is refused without a login', async ({ request }) => {
    // Rejected by authentication before any provider could be called
    const response = await request.post(`${apiURL}/v1/departments/generate`, { data: {} })

    expect([401, 403]).toContain(response.status())
  })
})
