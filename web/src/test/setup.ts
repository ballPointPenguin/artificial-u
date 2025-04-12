import '@testing-library/jest-dom/vitest'
import { cleanup } from '@solidjs/testing-library'
import { afterEach } from 'vitest'

// Automatically clean up after each test
afterEach(() => {
  cleanup()
})
