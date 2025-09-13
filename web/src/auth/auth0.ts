import { type Auth0Client, createAuth0Client } from '@auth0/auth0-spa-js'

export function createClient(): Promise<Auth0Client> {
  return createAuth0Client({
    domain: import.meta.env.VITE_AUTH0_DOMAIN,
    clientId: import.meta.env.VITE_AUTH0_CLIENT_ID,
    authorizationParams: {
      audience: import.meta.env.VITE_AUTH0_AUDIENCE,
      redirect_uri: window.location.origin,
      scope: 'openid profile email',
    },
    useRefreshTokens: true,
    // Persist tokens across refreshes and tabs (accepting localStorage XSS trade-offs)
    cacheLocation: 'localstorage',
  })
}
