import type { Auth0Client, User } from '@auth0/auth0-spa-js'
import { useNavigate } from '@solidjs/router'
import {
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
import type { Student } from '../api/types'
import { createClient, isAuthRequiredError } from './auth0'

type AuthContextValue = {
  isAuthenticated: () => boolean
  isLoading: () => boolean
  user: () => User | null
  student: () => Student | null
  role: () => string
  canGenerate: () => boolean
  isCreator: () => boolean
  isAdmin: () => boolean
  canModify: (createdBy: number | null | undefined) => boolean
  getAccessToken: () => Promise<string | null>
  login: () => Promise<void>
  logout: () => Promise<void>
  /** Force a re-check of auth state (useful after errors) */
  checkAuth: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue>()

// How often to check if tokens are still valid when user is active (in ms)
const TOKEN_CHECK_INTERVAL = 5 * 60 * 1000 // 5 minutes

export function AuthProvider(props: { children: JSX.Element }) {
  const [client, setClient] = createSignal<Auth0Client | null>(null)
  const [isAuthenticated, setIsAuthenticated] = createSignal(false)
  const [isLoading, setIsLoading] = createSignal(true)
  const [user, setUser] = createSignal<User | null>(null)
  const [student, setStudent] = createSignal<Student | null>(null)

  // Store listener functions for cleanup
  let storageListener: ((e: StorageEvent) => void) | null = null
  let visibilityListener: (() => void) | null = null
  let tokenCheckInterval: ReturnType<typeof setInterval> | null = null

  const navigate = useNavigate()

  onMount(() => {
    void (async () => {
      const c = await createClient()
      setClient(c)

      /**
       * Refresh the authentication state by checking with Auth0.
       * This will also attempt to silently refresh tokens if needed.
       */
      const refreshState = async () => {
        try {
          // First check basic auth state
          const authedNow = await c.isAuthenticated()

          if (authedNow) {
            // Try to get a fresh token - this will trigger refresh if needed
            try {
              await c.getTokenSilently()
              setIsAuthenticated(true)
              setUser((await c.getUser()) ?? null)

              // Fetch student profile
              try {
                const studentData = await studentService.getCurrentStudent()
                setStudent(studentData)
              } catch (error) {
                console.error('Failed to fetch student profile:', error)
                setStudent(null)
              }
            } catch (tokenError) {
              // Token refresh failed - check if it's a "needs login" error
              if (isAuthRequiredError(tokenError)) {
                console.warn('Token refresh failed, clearing auth state:', tokenError)
                setIsAuthenticated(false)
                setUser(null)
                setStudent(null)
              } else {
                // Some other error (network, etc.) - keep current state but log it
                console.error('Token refresh error:', tokenError)
              }
            }
          } else {
            setIsAuthenticated(false)
            setUser(null)
            setStudent(null)
          }
        } catch (error) {
          console.error('Error checking auth state:', error)
          setIsAuthenticated(false)
          setUser(null)
          setStudent(null)
        } finally {
          setIsLoading(false)
        }
      }

      // Register token provider with proper error handling
      setTokenProvider(async () => {
        try {
          const token = await c.getTokenSilently()
          return token
        } catch (error) {
          if (isAuthRequiredError(error)) {
            // Token is truly expired/invalid - update UI state
            console.warn('Token expired, clearing auth state')
            setIsAuthenticated(false)
            setUser(null)
            setStudent(null)
          }
          return null
        }
      })

      // Register auth error handler for API errors (401/403)
      setAuthErrorHandler(async () => {
        console.warn('API auth error received, rechecking auth state')
        // Don't immediately clear state - try to refresh first
        await refreshState()
      })

      // Handle OAuth redirect callback
      if (location.search.includes('code=') && location.search.includes('state=')) {
        try {
          const result = await c.handleRedirectCallback()
          const targetUrl =
            (result.appState as { targetUrl?: string } | undefined)?.targetUrl ?? location.pathname
          navigate(targetUrl, { replace: true })
        } catch (error) {
          console.error('Error handling redirect callback:', error)
        }
      }

      // Initial state check
      await refreshState()

      // Cross-tab sync: listen for Auth0 localStorage updates
      storageListener = (e: StorageEvent) => {
        if (!e.key) return
        if (e.key.includes('auth0')) {
          void refreshState()
        }
      }
      window.addEventListener('storage', storageListener)

      // Visibility change: recheck auth when user returns to tab
      visibilityListener = () => {
        // Use untrack() since we're in an event handler, not a reactive context
        if (document.visibilityState === 'visible' && untrack(isAuthenticated)) {
          // User came back to the tab and was authenticated - verify token is still valid
          void refreshState()
        }
      }
      document.addEventListener('visibilitychange', visibilityListener)

      // Periodic token check while user is active
      tokenCheckInterval = setInterval(() => {
        // Use untrack() since we're in a timer callback, not a reactive context
        if (untrack(isAuthenticated) && document.visibilityState === 'visible') {
          void refreshState()
        }
      }, TOKEN_CHECK_INTERVAL)
    })()
  })

  // Cleanup all listeners
  onCleanup(() => {
    if (storageListener) {
      window.removeEventListener('storage', storageListener)
    }
    if (visibilityListener) {
      document.removeEventListener('visibilitychange', visibilityListener)
    }
    if (tokenCheckInterval) {
      clearInterval(tokenCheckInterval)
    }
  })

  // Expose checkAuth for manual refresh
  const checkAuth = async () => {
    const c = client()
    if (!c) return
    setIsLoading(true)
    try {
      const authedNow = await c.isAuthenticated()
      if (authedNow) {
        try {
          await c.getTokenSilently()
          setIsAuthenticated(true)
          setUser((await c.getUser()) ?? null)
          const studentData = await studentService.getCurrentStudent()
          setStudent(studentData)
        } catch (tokenError) {
          if (isAuthRequiredError(tokenError)) {
            setIsAuthenticated(false)
            setUser(null)
            setStudent(null)
          }
        }
      } else {
        setIsAuthenticated(false)
        setUser(null)
        setStudent(null)
      }
    } finally {
      setIsLoading(false)
    }
  }

  const value: AuthContextValue = {
    isAuthenticated,
    isLoading,
    user,
    student,
    role: () => student()?.role ?? 'viewer',
    canGenerate: () => ['creator', 'admin'].includes(student()?.role ?? 'viewer'),
    isCreator: () => student()?.role === 'creator',
    isAdmin: () => student()?.role === 'admin',
    canModify: (createdBy: number | null | undefined) => {
      const currentStudent = student()
      const currentRole = currentStudent?.role ?? 'viewer'

      // Admins can modify anything
      if (currentRole === 'admin') return true

      // System-created assets (created_by is null/undefined) can only be modified by admins
      if (createdBy == null) return false

      // Non-admins can only modify assets they created
      return currentStudent?.id === createdBy
    },
    getAccessToken: async () => {
      const c = client()
      if (!c) return null
      try {
        return await c.getTokenSilently()
      } catch (error) {
        if (isAuthRequiredError(error)) {
          setIsAuthenticated(false)
          setUser(null)
          setStudent(null)
        }
        return null
      }
    },
    login: async () => {
      const c = client()
      if (!c) return
      await c.loginWithRedirect({
        appState: { targetUrl: window.location.pathname + window.location.search },
      })
    },
    logout: async () => {
      const c = client()
      if (!c) return
      await c.logout({ logoutParams: { returnTo: window.location.origin } })
    },
    checkAuth,
  }

  return <AuthContext.Provider value={value}>{props.children}</AuthContext.Provider>
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>')
  return ctx
}
