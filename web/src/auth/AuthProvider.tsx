import type { Auth0Client, User } from '@auth0/auth0-spa-js'
import { createContext, createSignal, type JSX, onCleanup, onMount, useContext } from 'solid-js'
import { setAuthErrorHandler, setTokenProvider } from '../api/client'
import { studentService } from '../api/services'
import type { Student } from '../api/types'
import { createClient } from './auth0'

type AuthContextValue = {
  isAuthenticated: () => boolean
  user: () => User | null
  student: () => Student | null
  role: () => string
  canGenerate: () => boolean
  isCreator: () => boolean
  isAdmin: () => boolean
  getAccessToken: () => Promise<string | null>
  login: () => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue>()

export function AuthProvider(props: { children: JSX.Element }) {
  const [client, setClient] = createSignal<Auth0Client | null>(null)
  const [isAuthenticated, setIsAuthenticated] = createSignal(false)
  const [user, setUser] = createSignal<User | null>(null)
  const [student, setStudent] = createSignal<Student | null>(null)

  // Store the storage listener function in a ref so we can remove it in cleanup
  let storageListener: ((e: StorageEvent) => void) | null = null

  onMount(() => {
    void (async () => {
      const c = await createClient()
      setClient(c)

      const refreshState = async () => {
        const authedNow = await c.isAuthenticated()
        setIsAuthenticated(authedNow)
        setUser(authedNow ? ((await c.getUser()) ?? null) : null)

        // Fetch student profile if authenticated
        if (authedNow) {
          try {
            const studentData = await studentService.getCurrentStudent()
            setStudent(studentData)
          } catch (error) {
            console.error('Failed to fetch student profile:', error)
            setStudent(null)
          }
        } else {
          setStudent(null)
        }
      }

      // Register token provider once the client is available
      setTokenProvider(async () => {
        try {
          return await c.getTokenSilently()
        } catch {
          return null
        }
      })

      // Register auth error handler to handle expired/invalid tokens
      setAuthErrorHandler(() => {
        // Clear authentication state when receiving 403
        setIsAuthenticated(false)
        setUser(null)
        // Optionally redirect to login page
        // Uncomment the next line to auto-redirect on auth errors
        // void c.loginWithRedirect()
      })

      if (location.search.includes('code=') && location.search.includes('state=')) {
        await c.handleRedirectCallback()
        history.replaceState({}, document.title, location.pathname)
      }
      await refreshState()

      // Cross-tab sync: listen for Auth0 localStorage updates
      storageListener = (e: StorageEvent) => {
        // Auth0 SDK keys usually contain "auth0." or start with "@@auth0"
        if (!e.key) return
        if (e.key.includes('auth0')) {
          void refreshState()
        }
      }
      window.addEventListener('storage', storageListener)
    })()
  })

  // Register cleanup at the component level
  onCleanup(() => {
    if (storageListener) {
      window.removeEventListener('storage', storageListener)
    }
  })

  const value: AuthContextValue = {
    isAuthenticated,
    user,
    student,
    role: () => student()?.role ?? 'viewer',
    canGenerate: () => ['creator', 'admin'].includes(student()?.role ?? 'viewer'),
    isCreator: () => student()?.role === 'creator',
    isAdmin: () => student()?.role === 'admin',
    getAccessToken: async () => {
      const c = client()
      if (!c) return null
      try {
        return await c.getTokenSilently()
      } catch {
        return null
      }
    },
    login: async () => {
      const c = client()
      if (!c) return
      await c.loginWithRedirect()
    },
    logout: async () => {
      const c = client()
      if (!c) return
      await c.logout({ logoutParams: { returnTo: window.location.origin } })
    },
  }

  return <AuthContext.Provider value={value}>{props.children}</AuthContext.Provider>
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>')
  return ctx
}
