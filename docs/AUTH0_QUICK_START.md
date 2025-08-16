# Auth0 Quick Start

## Quickstarts from Auth0

Use both quickstarts—“JavaScript SPA” for your SolidJS frontend and “Python API” for your FastAPI backend—because they solve different pieces of the same puzzle.

Here’s the mental model and a crisp recommendation, with alternatives if you want different trade‑offs.

⸻

The default, sensible setup (SPA + API, OAuth 2.0 Authorization Code w/ PKCE)

When to choose this: You’ve got a browser SPA that talks to a JSON API. You want stateless, simple infra, and you’re okay with bearer tokens on API calls.

Pieces:
 • Auth0 “Application” type: SPA
 • Auth0 “API” resource: your FastAPI service (define an audience)
 • Frontend (SolidJS): Use auth0-spa-js to log in (Auth Code + PKCE), keep tokens in memory, and call your API with Authorization: Bearer ….
 • Backend (FastAPI): Treat itself as a resource server. Validate incoming JWT access tokens (issuer, audience, signature via JWKS). Enforce scopes/roles per route.

Why this is the default: Clean separation of concerns; no server session to manage; scales easily; aligns with Auth0 docs and SDKs.

### My Domains

Public: <https://artificial-u.com>

Local: <http://localhost:5173>

Dev Proxy: <https://aliencyborg.share.zrok.io>

### Auth0 Configuration

- Application Login URI: <https://artificial-u.com/login>
- Allowed Callback URLs: <http://localhost:5173>, <https://aliencyborg.share.zrok.io>, <https://artificial-u.com>
- Allowed Logout URLs: <http://localhost:5173>, <https://aliencyborg.share.zrok.io>, <https://artificial-u.com>
- Allowed Web Origins: <http://localhost:5173>, <https://aliencyborg.share.zrok.io>, <https://artificial-u.com>, <https://*.artificial-u.com>
- Allowed Origins (CORS): <http://localhost:5173>, <https://aliencyborg.share.zrok.io>, <https://artificial-u.com>, <https://*.artificial-u.com>
- Identifier (Audience): <https://artificial-u.com/>
- Algorithms: RS256

### SolidJS (using @auth0/auth0-spa-js)

```javascript
import createAuth0Client from '@auth0/auth0-spa-js';

const auth0 = await createAuth0Client({
  domain: import.meta.env.VITE_AUTH0_DOMAIN,
  clientId: import.meta.env.VITE_AUTH0_CLIENT_ID,
  authorizationParams: {
    redirect_uri: window.location.origin,
    audience: import.meta.env.VITE_AUTH0_AUDIENCE, // your FastAPI API identifier
    scope: 'openid profile email read:things write:things'
  },
  useRefreshTokens: true,           // enables Refresh Token Rotation
  cacheLocation: 'memory'           // avoid localStorage unless you accept its risks
});

// login
await auth0.loginWithRedirect();

// get access token for API calls
const token = await auth0.getTokenSilently();
const res = await fetch('/api/things', {
  headers: { Authorization: `Bearer ${token}` }
});
```

### FastAPI (verify JWT access tokens)

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
import requests

AUTH0_DOMAIN = "your-auth0-tenant.auth0.com"
API_AUDIENCE = "https://artificial-u.com/"
ALGS = ["RS256"]
```

Fetch JWKS once and cache it (refresh occasionally)

```python
jwks = requests.get(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json").json()

app = FastAPI()
auth_scheme = HTTPBearer()

def _get_signing_key(kid: str):
    for key in jwks["keys"]:
        if key["kid"] == kid:
            return key
    return None

def require_auth(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    token = credentials.credentials
    try:
        unverified_header = jwt.get_unverified_header(token)
        key =_get_signing_key(unverified_header["kid"])
        if key is None:
            raise Exception("Signing key not found")
        payload = jwt.decode(
            token,
            key,
            algorithms=ALGS,
            audience=API_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )
        return payload  # contains sub, scope, etc.
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def require_scope(scope: str):
    def_checker(payload=Depends(require_auth)):
        scopes = (payload.get("scope") or "").split()
        if scope not in scopes:
            raise HTTPException(status_code=403, detail="Insufficient scope")
        return payload
    return _checker

@app.get("/api/things", dependencies=[Depends(require_scope("read:things"))])
def list_things(payload=Depends(require_auth)):
    return [{"id": 1, "name": "example"}]
```

## Auth0 Dashboard setup

 1. Create a SPA application (get domain + client ID).
 2. Create an API (Identifier = your audience, e.g. <https://yourapi.example.com>), enable RBAC and “Add Permissions in the Access Token”.
 3. Define scopes like read:things, write:things; assign via roles if helpful.
 4. In the SPA, request the audience and scopes so the Access Token contains them.
 5. In FastAPI, verify issuer and audience, and check scopes per route.

### Security notes (practical)

 • Keep tokens in memory, not localStorage. If you must persist (e.g., for multi‑tab), acknowledge the XSS trade‑off.
 • Prefer Refresh Token Rotation (useRefreshTokens: true) over legacy silent iframes. Rotation mitigates theft by invalidating used RTs.
 • Add a small clock skew leeway on the API (e.g., 60s) to reduce edge‑case 401s.
 • Lock CORS tightly: allow_origins to your SPA origin; don’t wildcard in prod.

⸻

### Common integration snags to avoid

 • Forgetting the audience in the SPA: you’ll get an opaque token that your API can’t validate. Always request the API audience.
 • Using the Management SDK on your API path: auth0-python is for Auth0’s own Management/Authentication endpoints, not for validating resource tokens. For JWT validation, stick to python-jose or PyJWT with JWKS.
 • Over‑permissive CORS: lock it down to your SPA origin and needed headers.
 • Missing scopes: define and request them; enforce on the API.

⸻

## Quick checklist to finish wiring

 1. In Auth0:
 • Create SPA app → capture domain + client ID.
 • Create API → identifier becomes your audience; add scopes; enable RBAC.
 2. In SolidJS:
 • Install @auth0/auth0-spa-js.
 • Initialize with domain, clientId, audience, useRefreshTokens: true.
 • Wrap your data‑fetcher to inject Authorization: Bearer ${token}.
 3. In FastAPI:
 • Add JWT validation dependency (issuer, audience, RS256 via JWKS).
 • Add require_scope("...") dependencies per route.
 • Configure CORS for your SPA origin.
 4. Locally:
 • Set callback/logout URLs in Auth0 to <http://localhost:5173> (or your dev port) and API base to <http://localhost:8000>.
