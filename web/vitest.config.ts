import path from 'node:path'
import { fileURLToPath } from 'node:url'
import solid from '@solidjs/vite-plugin'
import { configDefaults, defineConfig, type Plugin } from 'vitest/config'

const rootDir = path.dirname(fileURLToPath(import.meta.url))
const splitPropsShim = path.resolve(rootDir, 'src/shims/split-props.ts')

function lucideSolidSolid2Compat(): Plugin {
  return {
    name: 'lucide-solid-solid2-compat',
    enforce: 'pre',
    transform(code, id) {
      if (!id.includes(`${path.sep}lucide-solid${path.sep}`)) return null
      let next = code
      next = next.replaceAll(`from "solid-js/web"`, `from "@solidjs/web"`)
      next = next.replaceAll(`from 'solid-js/web'`, `from '@solidjs/web'`)
      next = next.replace(
        /import\s*\{([^}]*)\}\s*from\s*["']solid-js["']\s*;?/,
        (match, imports: string) => {
          if (!imports.includes('splitProps')) return match
          const cleaned = imports
            .split(',')
            .map((part) => part.trim())
            .filter((part) => part && part !== 'splitProps')
            .join(', ')
          const solidImport = cleaned ? `import { ${cleaned} } from "solid-js";\n` : ''
          return `${solidImport}import { splitProps } from ${JSON.stringify(splitPropsShim)};`
        }
      )
      next = next.replace(/(\w+)\.Provider\b/g, '$1')
      return next === code ? null : next
    },
  }
}

export default defineConfig({
  plugins: [lucideSolidSolid2Compat(), solid()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    // Playwright specs in e2e/ run with `pnpm test:e2e`, not vitest
    exclude: [...configDefaults.exclude, 'e2e/**'],
    server: {
      deps: {
        inline: [/solid-js/, /@solidjs\/web/, /lucide-solid/],
      },
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      exclude: ['node_modules/', 'src/test/setup.ts'],
    },
  },
})
