import type { JSX } from 'solid-js'
import { createSignal, Match, Show, Switch } from 'solid-js'
import { Button } from '../components/ui/Button'
import { useAuth } from './AuthProvider'

export function RequireAuth(props: {
  children: JSX.Element
  fallback?: JSX.Element | null
  loadingFallback?: JSX.Element | null
}) {
  const auth = useAuth()
  return (
    <Switch>
      <Match when={auth.isLoading()}>{props.loadingFallback ?? null}</Match>
      <Match when={auth.isAuthenticated()}>{props.children}</Match>
      <Match when={!auth.isAuthenticated()}>{props.fallback ?? null}</Match>
    </Switch>
  )
}

export function LoginPrompt() {
  const auth = useAuth()
  const [isLoggingIn, setIsLoggingIn] = createSignal(false)
  const [error, setError] = createSignal<string | null>(null)

  const handleLogin = async () => {
    setIsLoggingIn(true)
    setError(null)
    try {
      await auth.login()
    } catch (err) {
      console.error('Login error:', err)
      setError('Failed to initiate login. Please try again.')
      setIsLoggingIn(false)
    }
  }

  return (
    <Show when={!auth.isLoading()}>
      <div class="min-h-[60vh] flex items-center justify-center px-4 sm:px-6 lg:px-8">
        <div class="relative z-10 text-center max-w-2xl w-full">
          {/* Decorative background element */}
          <div class="absolute inset-0 opacity-10 pointer-events-none" aria-hidden="true">
            <div class="absolute top-0 left-1/2 transform -translate-x-1/2 w-64 h-64 bg-primary/20 rounded-full filter blur-3xl" />
          </div>

          {/* Icon decoration */}
          <div class="flex justify-center mb-6">
            <div class="relative">
              <div class="absolute inset-0 bg-primary/20 rounded-full blur-xl" />
              <div class="relative w-16 h-16 rounded-full bg-primary/10 border-2 border-primary/30 flex items-center justify-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="w-8 h-8 text-primary"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                  />
                </svg>
              </div>
            </div>
          </div>

          {/* Heading */}
          <h2 class="text-3xl sm:text-4xl md:text-5xl font-display text-foreground tracking-wider mb-4 text-shadow-golden">
            Log In or Sign Up
          </h2>
          <p class="text-xl sm:text-2xl font-serif text-muted mb-8">to use this feature</p>

          {/* Error message */}
          <Show when={error()}>
            <div class="mb-6 text-danger text-sm">{error()}</div>
          </Show>

          {/* Login Button */}
          <div class="flex justify-center relative z-20">
            <Show
              when={!isLoggingIn()}
              fallback={
                <div class="text-muted font-serif">
                  <p>Redirecting to login…</p>
                </div>
              }
            >
              <Button
                type="button"
                variant="primary"
                size="lg"
                onClick={() => void handleLogin()}
                class="text-shadow-golden"
              >
                Continue with Authentication
              </Button>
            </Show>
          </div>

          {/* Subtle decorative element */}
          <div class="absolute -bottom-8 left-1/2 transform -translate-x-1/2 w-16 h-16 flex items-center justify-center opacity-30 pointer-events-none">
            <div class="w-8 h-8 border-b-2 border-r-2 border-muted transform rotate-45" />
          </div>
        </div>
      </div>
    </Show>
  )
}
