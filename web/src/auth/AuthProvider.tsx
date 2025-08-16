import type { Auth0Client, User } from '@auth0/auth0-spa-js'
import { createContext, createSignal, JSX, onMount, useContext } from 'solid-js'
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
      const authed = await c.isAuthenticated()
      setIsAuthenticated(authed)
      if (authed) setUser((await c.getUser()) ?? null)
    })()
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
