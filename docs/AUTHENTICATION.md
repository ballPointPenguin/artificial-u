## Auth0 Authentication Plan (FastAPI API + SolidJS SPA)

**Approach:** OAuth 2.0 Authorization Code with PKCE. The SolidJS SPA obtains an Access Token from Auth0 (audience = API identifier) and sends it as `Authorization: Bearer <token>` to the FastAPI API. The API validates the JWT (issuer, audience, signature via JWKS) and enforces scopes/roles per route.

See also: `docs/AUTH0_QUICK_START.md` for condensed examples and dashboard settings.

### What we will add

- **Frontend (SolidJS)**: Lightweight Auth0 SPA client, an `AuthProvider` (Solid context), route guards, and transparent token injection into API requests.
- **Backend (FastAPI)**: Auth dependencies that validate JWTs against Auth0 JWKS, simple helpers for checking scopes/roles, and optional public/protected route setup.
- **Config**: Environment variables in both apps for domain, client ID, and audience; CORS tuned to the SPA origins.

## Environments and URLs

- **Local SPA**: `http://localhost:5173`
- **Local API**: `http://localhost:8000`
- **Dev proxy**: `https://aliencyborg.share.zrok.io`
- **Public site**: `https://artificial-u.com`

Configure these in Auth0 (Allowed Callback URLs, Allowed Logout URLs, Allowed Web Origins). Details are in `docs/AUTH0_QUICK_START.md`.

## Backend (FastAPI) implementation

### 1) Dependencies

- Add Python deps:
  - `python-jose[cryptography]` (JWT validation)
  - `httpx` (already present) or `requests` for fetching JWKS

### 2) Settings

Add to `artificial_u/config/settings.py` and `.env`:

```bash
# FastAPI / Auth0
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_AUDIENCE=https://yourapi.example.com
AUTH0_ALG=RS256
```

Expose these in `Settings` (e.g., `AUTH0_DOMAIN: str | None`, `AUTH0_AUDIENCE: str | None`, `AUTH0_ALG: str = "RS256"`).

### 3) Auth helpers

Create `artificial_u/api/security/auth0.py`:

```python
from typing import Any, Dict, List, Optional
from functools import lru_cache

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwk, jwt
from jose.utils import base64url_decode

from artificial_u.config.settings import get_settings


auth_scheme = HTTPBearer(auto_error=True)


@lru_cache
def get_jwks() -> Dict[str, Any]:
    settings = get_settings()
    jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
    with httpx.Client(timeout=5.0) as client:
        return client.get(jwks_url).json()


def _get_signing_key(kid: str) -> Optional[Dict[str, Any]]:
    keys: List[Dict[str, Any]] = get_jwks().get("keys", [])
    for key in keys:
        if key.get("kid") == kid:
            return key
    return None


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)) -> Dict[str, Any]:
    settings = get_settings()
    token = credentials.credentials
    try:
        unverified = jwt.get_unverified_header(token)
        jwk_data = _get_signing_key(unverified["kid"])  # type: ignore[reportGeneralTypeIssues]
        if not jwk_data:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Signing key not found")

        # python-jose supports passing JWKS directly for RS256
        payload = jwt.decode(
            token,
            jwk.construct(jwk_data),  # type: ignore[arg-type]
            algorithms=[settings.AUTH0_ALG],
            audience=settings.AUTH0_AUDIENCE,
            issuer=f"https://{settings.AUTH0_DOMAIN}/",
        )
        return payload  # contains sub, scope, etc.
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def require_scope(scope: str):
    def _checker(payload: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
        scopes = (payload.get("scope") or "").split()
        if scope not in scopes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient scope")
        return payload
    return _checker
```

Add a simple identity endpoint (optional) in a new router:

```python
from fastapi import APIRouter, Depends
from artificial_u.api.security.auth0 import require_auth

router = APIRouter(tags=["auth"])

@router.get("/me")
def who_am_i(payload = Depends(require_auth)):
    return {"sub": payload.get("sub"), "scope": payload.get("scope"), "claims": payload}
```

Include this router under `/api/v1` in `artificial_u/api/app.py`.

### 4) Route protection

- Public endpoints: leave as-is.
- Protected endpoints: add `Depends(require_auth)` and/or `Depends(require_scope("read:things"))`.
- If you want everything protected by default, add a global dependency or apply dependencies to specific routers.

### 5) CORS

- `setup_cors` already exists. Ensure `settings.cors_origins` includes the SPA origins you use during development and production. See `AUTH0_QUICK_START.md` for a reference list.

## Frontend (SolidJS) implementation

### 1) Dependencies

```bash
pnpm add @auth0/auth0-spa-js
```

### 2) Env vars

Create `web/.env` or use Vite envs:

```bash
VITE_AUTH0_DOMAIN=your-tenant.auth0.com
VITE_AUTH0_CLIENT_ID=xxxxx
VITE_AUTH0_AUDIENCE=https://yourapi.example.com
```

### 3) Auth client and provider

Create `web/src/auth/auth0.ts`:

```ts
import createAuth0Client, { type Auth0Client } from '@auth0/auth0-spa-js'

export async function createClient(): Promise<Auth0Client> {
  return createAuth0Client({
    domain: import.meta.env.VITE_AUTH0_DOMAIN,
    clientId: import.meta.env.VITE_AUTH0_CLIENT_ID,
    authorizationParams: {
      audience: import.meta.env.VITE_AUTH0_AUDIENCE,
      redirect_uri: window.location.origin,
      scope: 'openid profile email',
    },
    useRefreshTokens: true,
    cacheLocation: 'memory',
  })
}
```

Create `web/src/auth/AuthProvider.tsx`:

```tsx
import { createSignal, createContext, useContext, onMount, JSX } from 'solid-js'
import type { Auth0Client, User } from '@auth0/auth0-spa-js'
import { createClient } from './auth0'

type AuthContextValue = {
  isAuthenticated: () => boolean
  user: () => User | null
  getAccessToken: () => Promise<string | null>
  login: () => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue>()

export function AuthProvider(props: { children: JSX.Element }) {
  const [client, setClient] = createSignal<Auth0Client | null>(null)
  const [isAuthenticated, setIsAuthenticated] = createSignal(false)
  const [user, setUser] = createSignal<User | null>(null)

  onMount(async () => {
    const c = await createClient()
    setClient(c)
    if (location.search.includes('code=') && location.search.includes('state=')) {
      await c.handleRedirectCallback()
      history.replaceState({}, document.title, location.pathname)
    }
    setIsAuthenticated(await c.isAuthenticated())
    if (isAuthenticated()) setUser((await c.getUser()) ?? null)
  })

  const value: AuthContextValue = {
    isAuthenticated,
    user,
    getAccessToken: async () => (await client())?.getTokenSilently() ?? null,
    login: async () => void (await client())?.loginWithRedirect(),
    logout: () => (client())?.logout({ logoutParams: { returnTo: window.location.origin } }),
  }

  return <AuthContext.Provider value={value}>{props.children}</AuthContext.Provider>
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>')
  return ctx
}
```

Wrap your app in `AuthProvider` in `web/src/index.tsx`.

### 4) Inject token into API client

Option A (quick): pass `Authorization` per call where needed.

```ts
// example service call
const token = await auth.getAccessToken()
await httpClient.get('/v1/lectures', {
  headers: token ? { Authorization: `Bearer ${token}` } : undefined,
})
```

Option B (preferred): add a token provider hook into `web/src/api/client.ts` so all requests include the token automatically when available.

Minimal change sketch inside `client.ts`:

```ts
let getAuthToken: null | (() => Promise<string | null>) = null
export const setTokenProvider = (fn: () => Promise<string | null>) => { getAuthToken = fn }

// before each request
if (getAuthToken) {
  const token = await getAuthToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
}
```

Call `setTokenProvider(() => auth.getAccessToken())` once in app bootstrap.

### 5) Route guards (optional)

Create a simple guard component:

```tsx
import { Show, JSX } from 'solid-js'
import { useAuth } from '../auth/AuthProvider'

export function RequireAuth(props: { children: JSX.Element }) {
  const auth = useAuth()
  return <Show when={auth.isAuthenticated()} fallback={<button onClick={auth.login}>Login</button>}>{props.children}</Show>
}
```

Wrap protected pages/routes with `RequireAuth`.

## Security notes

- Keep tokens in memory only; avoid `localStorage` unless you accept XSS trade-offs.
- Enable Refresh Token Rotation (default in our config) for better resilience.
- Validate audience and issuer on the API, and check scopes per endpoint.
- Lock down CORS to only the SPA origins in non-dev environments.

## Rollout plan

1) Land settings and dependencies (no behavior change yet).
2) Implement backend `require_auth` + `/me` endpoint; add protection to a small set of endpoints.
3) Wire Solid `AuthProvider`, manual token on a single API call; verify end-to-end.
4) Add token provider to `httpClient` for transparent coverage.
5) Expand route protections and scope checks where appropriate.

## Task list

- [x] Backend: add deps `python-jose[cryptography]` (and ensure `httpx` present) in `pyproject.toml`
- [x] Backend: add `AUTH0_DOMAIN`, `AUTH0_AUDIENCE`, `AUTH0_ALG` to `Settings` and `.env`
- [x] Backend: create `artificial_u/api/security/auth0.py` with `require_auth` and `require_scope`
- [x] Backend: add `/api/v1/me` endpoint and include router in `app.py`
- [x] Backend: apply `Depends(require_auth)`/`require_scope(...)` to protected routes
- [x] Backend: tighten `cors_origins` to match actual SPA hosts
- [ ] Frontend: `pnpm add @auth0/auth0-spa-js`
- [ ] Frontend: add `VITE_AUTH0_DOMAIN`, `VITE_AUTH0_CLIENT_ID`, `VITE_AUTH0_AUDIENCE`
- [ ] Frontend: create `src/auth/auth0.ts` and `src/auth/AuthProvider.tsx`, wrap app
- [ ] Frontend: implement token injection (Option B) in `src/api/client.ts`, expose `setTokenProvider`
- [ ] Frontend: optionally add `RequireAuth` guard for protected pages
- [ ] Verify: login flow, token in requests, API validation, scope enforcement
- [ ] Tests: unit test JWT dependency with a mocked token; smoke test a protected endpoint, fix api tests

## Alternatives (later, if needed)

- **BFF/Session**: Instead of SPA bearer tokens, run a backend-for-frontend that manages a server session and sets `HttpOnly` cookies. More setup, fewer token exposures in the browser.
- **Solid/Router integrations**: You can integrate login redirects at the router level for a more opinionated UX.
