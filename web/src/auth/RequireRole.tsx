import type { JSX } from 'solid-js'
import { Match, Switch } from 'solid-js'
import { useAuth } from './AuthProvider'

const ROLE_HIERARCHY = { viewer: 0, creator: 1, admin: 2 }

export function RequireRole(props: {
  minRole: 'viewer' | 'creator' | 'admin'
  children: JSX.Element
  fallback?: JSX.Element | null
  loadingFallback?: JSX.Element | null
}) {
  const auth = useAuth()
  const hasPermission = () => {
    const role = auth.role()
    const userLevel = ROLE_HIERARCHY[role as keyof typeof ROLE_HIERARCHY] || 0
    const requiredLevel = ROLE_HIERARCHY[props.minRole]
    return userLevel >= requiredLevel
  }

  return (
    <Switch>
      <Match when={auth.isLoading()}>{props.loadingFallback ?? null}</Match>
      <Match when={hasPermission()}>{props.children}</Match>
      <Match when={!hasPermission()}>{props.fallback ?? null}</Match>
    </Switch>
  )
}
