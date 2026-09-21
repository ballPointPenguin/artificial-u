import { useNavigate } from '@solidjs/router'
import { createEffect, createSignal } from 'solid-js'
import { useAuth } from '../auth/AuthProvider'
import { useI18n } from '../i18n/index.js'

const LoginPage = () => {
  const auth = useAuth()
  const navigate = useNavigate()
  const { t } = useI18n()

  const [loginInFlight, setLoginInFlight] = createSignal(false)

  // A concurrent second loginWithRedirect() call overwrites the first's
  // PKCE transaction in sessionStorage, so the browser can come back with a
  // code/state pair that no longer matches what's stored ("Invalid state").
  // Guard both the automatic and manual triggers behind a single in-flight flag.
  const triggerLogin = () => {
    if (loginInFlight()) return
    setLoginInFlight(true)
    void auth.login().catch(() => setLoginInFlight(false))
  }

  // Redirect authenticated users away from login page; otherwise kick off
  // login once auth state has settled (avoids re-triggering login while
  // the initial/post-redirect auth check is still in flight).
  createEffect(() => {
    if (auth.isLoading()) return
    if (auth.isAuthenticated()) {
      navigate('/', { replace: true })
    } else {
      triggerLogin()
    }
  })

  return (
    <div class="container mx-auto p-6 text-parchment-200">
      <p>{t().login.redirecting}</p>
      <button class="mt-4 underline" onClick={triggerLogin} disabled={loginInFlight()}>
        {t().login.clickIfNotRedirected}
      </button>
    </div>
  )
}

export default LoginPage
