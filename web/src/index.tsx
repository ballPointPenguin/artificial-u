/* @refresh reload */

import { init } from '@plausible-analytics/tracker'
import { Router } from '@solidjs/router'
import type { JSX } from 'solid-js'
import { render } from 'solid-js/web'
import App from './App.tsx'
import { AuthProvider } from './auth/AuthProvider.tsx'
import { I18nProvider } from './i18n'
import './index.css'
import { AudioPlayerProvider } from './utils/audio-player-context.jsx'

// Initialize Plausible Analytics
const plausibleDomain = import.meta.env.VITE_PLAUSIBLE_DOMAIN as string | undefined
if (plausibleDomain) {
  init({
    domain: plausibleDomain,
    fileDownloads: true,
    formSubmissions: true,
  })
}

const root = document.getElementById('root')

const Root = (props: { children?: JSX.Element }) => (
  <AuthProvider>
    <AudioPlayerProvider>{props.children}</AudioPlayerProvider>
  </AuthProvider>
)

if (root) {
  render(
    () => (
      <I18nProvider>
        <Router root={Root}>
          <App />
        </Router>
      </I18nProvider>
    ),
    root
  )
} else {
  console.error('Root element not found')
}
