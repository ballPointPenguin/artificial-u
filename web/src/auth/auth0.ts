import { type Auth0Client, createAuth0Client } from '@auth0/auth0-spa-js'

export function createClient(): Promise<Auth0Client> {
  return createAuth0Client({
    domain: import.meta.env.VITE_AUTH0_DOMAIN,
    clientId: import.meta.env.VITE_AUTH0_CLIENT_ID,
    authorizationParams: {
      audience: import.meta.env.VITE_AUTH0_AUDIENCE,
      redirect_uri: window.location.origin,
      scope: 'openid profile email offline_access',
    },
    useRefreshTokens: true,
    // Persist tokens across refreshes and tabs (accepting localStorage XSS trade-offs)
    cacheLocation: 'localstorage',
    // Use refresh tokens for rotation (more secure, longer sessions)
    useRefreshTokensFallback: true,
  })
}

/**
 * Auth0 error types that indicate the user needs to re-authenticate
 */
export const AUTH_REQUIRED_ERRORS = [
  'login_required',
  'consent_required',
  'interaction_required',
  'invalid_grant', // Refresh token expired or revoked
  'missing_refresh_token',
]

/**
 * Check if an error indicates the user needs to log in again
 */
export function isAuthRequiredError(error: unknown): boolean {
  if (error instanceof Error) {
    // Auth0 SDK errors have an 'error' property with the error code
    const authError = error as { error?: string; message?: string }
    if (authError.error && AUTH_REQUIRED_ERRORS.includes(authError.error)) {
      return true
    }
    // Check error message as fallback
    if (authError.message) {
      return AUTH_REQUIRED_ERRORS.some((e) => authError.message?.includes(e))
    }
  }
  return false
}
