import type { User } from '@auth0/auth0-spa-js'
import { useNavigate } from '@solidjs/router'
import {
  batch,
  createContext,
  createSignal,
  type JSX,
  onCleanup,
  onMount,
  untrack,
  useContext,
} from 'solid-js'
import { setAuthErrorHandler, setTokenProvider } from '../api/client'
import { studentService } from '../api/services'
import type { Student, StudentUpdate } from '../api/types'
import { createClient, isAuthRequiredError } from './auth0'

export type Role = Student['role']

const ROLE_LEVEL: Record<Role, number> = { viewer: 0, creator: 1, admin: 2 }

type AuthContextValue = {
  isAuthenticated: () => boolean
  /** True only until the initial auth check settles; background refreshes don't toggle it */
  isLoading: () => boolean
  user: () => User | null
  student: () => Student | null
  /** Set when authenticated but the student profile (and therefore role) failed to load */
  profileError: () => string | null
  role: () => Role
  hasRole: (minRole: Role) => boolean
  isAdmin: () => boolean
  canModify: (createdBy: number | null | undefined) => boolean
  login: () => Promise<void>
  logout: () => Promise<void>
  /** Re-check auth state and reload the student profile */
  refresh: () => Promise<void>
  updateProfile: (data: StudentUpdate) => Promise<Student>
}

const AuthContext = createContext<AuthContextValue>()

// How often to check if tokens are still valid when user is active (in ms)
const TOKEN_CHECK_INTERVAL = 5 * 60 * 1000 // 5 minutes

const hasCallbackParams = () =>
  location.search.includes('code=') && location.search.includes('state=')

export function AuthProvider(props: { children: JSX.Element }) {
  const [isAuthenticated, setIsAuthenticated] = createSignal(false)
  const [isLoading, setIsLoading] = createSignal(true)
  const [user, setUser] = createSignal<User | null>(null)
  const [student, setStudent] = createSignal<Student | null>(null)
  const [profileError, setProfileError] = createSignal<string | null>(null)

  const navigate = useNavigate()

  const clearAuth = () => {
    batch(() => {
      setIsAuthenticated(false)
      setUser(null)
      setStudent(null)
      setProfileError(null)
    })
  }

  // Resolves with the Auth0 client once any OAuth redirect callback has been handled.
  // Everything that touches tokens awaits this, so no API call can race the
  // callback's code exchange (a concurrent getTokenSilently() with no cached
  // token yet would fail and clear auth state out from under the callback).
  let postCallbackTargetUrl: string | null = null
  const clientReady = (async () => {
    const c = await createClient()
    if (hasCallbackParams()) {
      try {
        const result = await c.handleRedirectCallback()
        postCallbackTargetUrl =
          (result.appState as { targetUrl?: string } | undefined)?.targetUrl ?? location.pathname
      } catch (error) {
        // Leaving the stale code/state params in the URL would otherwise strand
        // the user on a dirty URL with no way to retry (a refresh just replays
        // the same failed exchange). Send them back to /login to try again.
        console.error('Error handling redirect callback:', error)
        postCallbackTargetUrl = '/login'
      }
    }
    return c
  })()

  // Registered synchronously (not in onMount) so that API requests fired by
  // children during their first render still wait for, and carry, a token.
  setTokenProvider(async () => {
    const c = await clientReady
    try {
      return (await c.getTokenSilently()) ?? null
    } catch (error) {
      if (isAuthRequiredError(error)) {
        console.warn('Token expired, clearing auth state')
        clearAuth()
      }
      return null
    }
  })

  const loadStudent = async () => {
    try {
      setStudent(await studentService.getCurrentStudent())
      setProfileError(null)
    } catch (error) {
      // Keep any previously loaded profile so a transient failure during a
      // background refresh doesn't silently demote the user to viewer.
      console.error('Failed to fetch student profile:', error)
      setProfileError(error instanceof Error ? error.message : String(error))
    }
  }

  const doRefresh = async () => {
    try {
      const c = await clientReady
      if (!(await c.isAuthenticated())) {
        clearAuth()
        return
      }
      // Get a fresh token - this will trigger a refresh if needed
      try {
        await c.getTokenSilently()
      } catch (tokenError) {
        if (isAuthRequiredError(tokenError)) {
          console.warn('Token refresh failed, clearing auth state:', tokenError)
          clearAuth()
        } else {
          // Some other error (network, etc.) - keep current state but log it
          console.error('Token refresh error:', tokenError)
        }
        return
      }
      const currentUser = (await c.getUser()) ?? null
      batch(() => {
        setUser(currentUser)
        setIsAuthenticated(true)
      })
      await loadStudent()
    } catch (error) {
      console.error('Error checking auth state:', error)
      clearAuth()
    } finally {
      setIsLoading(false)
    }
  }

  // Coalesce concurrent refreshes (timer, tab focus, storage events, 401s).
  // This also stops a 401 from the refresh's own profile fetch from
  // re-triggering refresh in a loop.
  let refreshInFlight: Promise<void> | null = null
  const refresh = () => {
    refreshInFlight ??= doRefresh().finally(() => {
      refreshInFlight = null
    })
    return refreshInFlight
  }

  // A 401 means our token was rejected; re-check before trusting current state
  setAuthErrorHandler(() => {
    console.warn('API auth error received, rechecking auth state')
    return refresh()
  })

  onMount(() => {
    void refresh().then(() => {
      if (postCallbackTargetUrl) navigate(postCallbackTargetUrl, { replace: true })
    })

    // Cross-tab sync: listen for Auth0 localStorage updates
    const onStorage = (e: StorageEvent) => {
      if (e.key?.includes('auth0')) void refresh()
    }
    // Recheck when the user returns to the tab, and periodically while active.
    // untrack() since these run outside a reactive context.
    const recheckIfActive = () => {
      if (document.visibilityState === 'visible' && untrack(isAuthenticated)) void refresh()
    }
    const tokenCheckInterval = setInterval(recheckIfActive, TOKEN_CHECK_INTERVAL)

    window.addEventListener('storage', onStorage)
    document.addEventListener('visibilitychange', recheckIfActive)
    onCleanup(() => {
      window.removeEventListener('storage', onStorage)
      document.removeEventListener('visibilitychange', recheckIfActive)
      clearInterval(tokenCheckInterval)
    })
  })

  const role = (): Role => student()?.role ?? 'viewer'

  const value: AuthContextValue = {
    isAuthenticated,
    isLoading,
    user,
    student,
    profileError,
    role,
    hasRole: (minRole) => ROLE_LEVEL[role()] >= ROLE_LEVEL[minRole],
    isAdmin: () => role() === 'admin',
    // Mirrors can_modify_asset() in artificial_u/api/security/auth0.py
    canModify: (createdBy) => {
      if (role() === 'admin') return true
      // System-created assets (created_by is null/undefined) can only be modified by admins
      if (createdBy == null) return false
      return student()?.id === createdBy
    },
    login: async () => {
      const c = await clientReady
      await c.loginWithRedirect({
        appState: { targetUrl: window.location.pathname + window.location.search },
      })
    },
    logout: async () => {
      const c = await clientReady
      await c.logout({ logoutParams: { returnTo: window.location.origin } })
    },
    refresh,
    updateProfile: async (data) => {
      const updated = await studentService.updateCurrentStudent(data)
      setStudent(updated)
      return updated
    },
  }

  return <AuthContext.Provider value={value}>{props.children}</AuthContext.Provider>
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>')
  return ctx
}
