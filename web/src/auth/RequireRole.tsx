import type { JSX } from 'solid-js'
import { Show } from 'solid-js'
import { useAuth } from './AuthProvider'

const ROLE_HIERARCHY = { viewer: 0, creator: 1, admin: 2 }

export function RequireRole(props: {
  minRole: 'viewer' | 'creator' | 'admin'
  children: JSX.Element
  fallback?: JSX.Element | null
}) {
  const auth = useAuth()
  const hasPermission = () => {
    const role = auth.role()
    const userLevel = ROLE_HIERARCHY[role as keyof typeof ROLE_HIERARCHY] || 0
    const requiredLevel = ROLE_HIERARCHY[props.minRole]
    return userLevel >= requiredLevel
  }

  return (
    <Show when={hasPermission()} fallback={props.fallback ?? null}>
      {props.children}
    </Show>
  )
}
