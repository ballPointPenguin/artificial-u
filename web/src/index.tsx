/* @refresh reload */

import { init } from '@plausible-analytics/tracker'
import { Router } from '@solidjs/router'
import { render } from 'solid-js/web'
import App from './App.tsx'
import { AuthProvider } from './auth/AuthProvider.tsx'
import { I18nProvider } from './i18n'
import { AudioPlayerProvider } from './utils/audio-player-context.jsx'
import './index.css'

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

if (root) {
  render(
    () => (
      <I18nProvider>
        <AuthProvider>
          <AudioPlayerProvider>
            <Router>
              <App />
            </Router>
          </AudioPlayerProvider>
        </AuthProvider>
      </I18nProvider>
    ),
    root
  )
} else {
  console.error('Root element not found')
}
