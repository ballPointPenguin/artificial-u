/* @refresh reload */

import { init } from '@plausible-analytics/tracker'
import { Router } from '@solidjs/router'
import { render } from 'solid-js/web'
import App from './App.tsx'
import { AuthProvider } from './auth/AuthProvider.tsx'
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
      <AuthProvider>
        <Router>
          <App />
        </Router>
      </AuthProvider>
    ),
    root
  )
} else {
  console.error('Root element not found')
}
