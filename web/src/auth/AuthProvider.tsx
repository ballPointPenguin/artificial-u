import type { Auth0Client, User } from '@auth0/auth0-spa-js'
import { createContext, createSignal, type JSX, onCleanup, onMount, useContext } from 'solid-js'
import { setTokenProvider } from '../api/client'
import { createClient } from './auth0'

type AuthContextValue = {
  isAuthenticated: () => boolean
  user: () => User | null
  getAccessToken: () => Promise<string | null>
  login: () => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue>()

export function AuthProvider(props: { children: JSX.Element }) {
  const [client, setClient] = createSignal<Auth0Client | null>(null)
  const [isAuthenticated, setIsAuthenticated] = createSignal(false)
  const [user, setUser] = createSignal<User | null>(null)

  // Store the storage listener function in a ref so we can remove it in cleanup
  let storageListener: ((e: StorageEvent) => void) | null = null

  onMount(() => {
    void (async () => {
      const c = await createClient()
      setClient(c)
      // Register token provider once the client is available
      setTokenProvider(async () => {
        try {
          return await c.getTokenSilently()
        } catch {
          return null
        }
      })
      if (location.search.includes('code=') && location.search.includes('state=')) {
        await c.handleRedirectCallback()
        history.replaceState({}, document.title, location.pathname)
      }
      const refreshState = async () => {
        const authedNow = await c.isAuthenticated()
        setIsAuthenticated(authedNow)
        setUser(authedNow ? ((await c.getUser()) ?? null) : null)
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
