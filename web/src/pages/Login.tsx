import { onMount } from 'solid-js'
import { useAuth } from '../auth/AuthProvider'

const LoginPage = () => {
  const auth = useAuth()

  onMount(() => {
    void auth.login()
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
