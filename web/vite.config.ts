import path from 'node:path'
import { fileURLToPath } from 'node:url'
import solid from '@solidjs/vite-plugin'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig, type Plugin } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

const rootDir = path.dirname(fileURLToPath(import.meta.url))
const splitPropsShim = path.resolve(rootDir, 'src/shims/split-props.ts')

/**
 * lucide-solid@1.x still imports Solid 1 APIs (`solid-js/web`, `splitProps`,
 * `Context.Provider`). Rewrite those until an official Solid 2 release ships.
 */
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

export default defineConfig(({ mode }) => ({
  plugins: [
    lucideSolidSolid2Compat(),
    solid(),
    tailwindcss(),
    VitePWA({
      registerType: 'prompt',
      includeAssets: ['favicon.ico', 'robots.txt', 'images/**/*'],
      manifest: false, // Using public/manifest.json instead
      workbox: {
        // Disable precaching in dev mode since files are served from memory
        globPatterns: mode === 'development' ? [] : ['**/*.{js,css,html,ico,png,svg,woff2}'],
        // For SPA navigations, serve the app shell (when online) and show a branded
        // offline fallback when the network is unavailable.
        navigateFallback: '/offline.html',
        navigateFallbackDenylist: [/^\/api\//],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365, // 365 days
              },
              cacheableResponse: {
                statuses: [0, 200],
              },
            },
          },
          {
            urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'gstatic-fonts-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365, // 365 days
              },
              cacheableResponse: {
                statuses: [0, 200],
              },
            },
          },
          {
            // Cache only safe-ish API reads (GET), and explicitly exclude user-specific/streaming endpoints.
            method: 'GET',
            urlPattern:
              /\/api\/(?!v1\/students\/me(?:\?|$))(?!v1\/preferences\/)(?!v1\/jobs\/stream(?:\?|$)).*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              networkTimeoutSeconds: 10,
              cacheableResponse: {
                statuses: [0, 200],
              },
              expiration: {
                // Keep this intentionally small: API data can be user-specific and mutable.
                maxEntries: 50,
                maxAgeSeconds: 60 * 5, // 5 minutes
              },
            },
          },
          {
            urlPattern: /\.(png|jpg|jpeg|svg|gif|webp)$/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'images-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
              },
            },
          },
        ],
      },
      devOptions: {
        enabled: false,
        type: 'module',
      },
    }),
  ],
  server: {
    allowedHosts: ['aliencyborg.share.zrok.io', 'localhost', 'artificial-u.com'],
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/share': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    target: 'esnext',
  },
}))
