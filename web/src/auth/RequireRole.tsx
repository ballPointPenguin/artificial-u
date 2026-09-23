import { type JSX, Show } from 'solid-js'
import { type Role, useAuth } from './AuthProvider'

export function RequireRole(props: {
  minRole: Role
  children: JSX.Element
  fallback?: JSX.Element | null
  loadingFallback?: JSX.Element | null
}) {
  const auth = useAuth()
  return (
    <Show when={!auth.isLoading()} fallback={props.loadingFallback ?? null}>
      <Show when={auth.hasRole(props.minRole)} fallback={props.fallback ?? null}>
        {props.children}
      </Show>
    </Show>
  )
}
