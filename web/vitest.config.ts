import solid from '@solidjs/vite-plugin'
import { configDefaults, defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [solid()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    // Playwright specs in e2e/ run with `pnpm test:e2e`, not vitest
    exclude: [...configDefaults.exclude, 'e2e/**'],
    // Add ThreadLocal to fix solidjs/testing-library
    deps: {
      inline: [/solid-js/],
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      exclude: ['node_modules/', 'src/test/setup.ts'],
    },
  },
})
