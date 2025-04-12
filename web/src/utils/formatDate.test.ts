import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { formatDate, getRelativeTimeString } from './formatDate'

describe('formatDate', () => {
  it('formats a date correctly', () => {
    const date = new Date(2023, 0, 15) // January 15, 2023
    expect(formatDate(date)).toBe('January 15, 2023')
  })
})

describe('getRelativeTimeString', () => {
  beforeEach(() => {
    // Mock the current date to be fixed at January 20, 2023
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2023, 0, 20))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('returns "Today" for the current day', () => {
    const today = new Date(2023, 0, 20)
    expect(getRelativeTimeString(today)).toBe('Today')
  })

  it('returns "Yesterday" for the previous day', () => {
    const yesterday = new Date(2023, 0, 19)
    expect(getRelativeTimeString(yesterday)).toBe('Yesterday')
  })

  it('returns "X days ago" for days within the last week', () => {
    const twoDaysAgo = new Date(2023, 0, 18)
    expect(getRelativeTimeString(twoDaysAgo)).toBe('2 days ago')
  })

  it('returns a formatted date for dates older than a week', () => {
    const twoWeeksAgo = new Date(2023, 0, 6)
    expect(getRelativeTimeString(twoWeeksAgo)).toBe('January 6, 2023')
  })
})
