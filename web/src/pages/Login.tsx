import { useNavigate } from '@solidjs/router'
import { createEffect, onMount } from 'solid-js'
import { useAuth } from '../auth/AuthProvider'

const LoginPage = () => {
  const auth = useAuth()
  const navigate = useNavigate()

  // Redirect authenticated users away from login page
  createEffect(() => {
    if (!auth.isLoading() && auth.isAuthenticated()) {
      navigate('/', { replace: true })
    }
  })

  onMount(() => {
    // Only trigger login if not already authenticated
    if (!auth.isAuthenticated()) {
      void auth.login()
    }
  })

  return (
    <div class="container mx-auto p-6 text-parchment-200">
      <p>Redirecting to login…</p>
      <button class="mt-4 underline" onClick={() => void auth.login()}>
        Click here if not redirected
      </button>
    </div>
  )
}

export default LoginPage
