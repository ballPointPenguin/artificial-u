import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'
import solid from 'vite-plugin-solid'

export default defineConfig({
  plugins: [solid(), tailwindcss()],
  server: {
    allowedHosts: ['aliencyborg.share.zrok.io', 'localhost'],
  },
  build: {
    target: 'esnext',
  },
})
