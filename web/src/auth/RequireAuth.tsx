import type { JSX } from 'solid-js'
import { Show } from 'solid-js'
import { useAuth } from './AuthProvider'

export function RequireAuth(props: { children: JSX.Element; fallback?: JSX.Element | null }) {
  const auth = useAuth()
  return (
    <Show when={auth.isAuthenticated()} fallback={props.fallback ?? null}>
      {props.children}
    </Show>
  )
}

export function LoginPrompt() {
  const auth = useAuth()
  return <button onClick={() => void auth.login()}>Login</button>
}
