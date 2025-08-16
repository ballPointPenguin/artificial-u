/* @refresh reload */

import { Router } from '@solidjs/router'
import { render } from 'solid-js/web'
import './index.css'
import App from './App.tsx'
import { AuthProvider } from './auth/AuthProvider.tsx'

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
