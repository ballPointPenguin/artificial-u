import type { JSX } from 'solid-js'
import { Match, Show, Switch } from 'solid-js'
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
  return (
    <Show when={!auth.isLoading()}>
      <button onClick={() => void auth.login()}>Login</button>
    </Show>
  )
}
