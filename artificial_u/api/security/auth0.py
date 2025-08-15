from functools import lru_cache
from typing import Any, Dict, List, Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwk, jwt

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


def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
) -> Dict[str, Any]:
    settings = get_settings()
    token = credentials.credentials
    try:
        unverified = jwt.get_unverified_header(token)
        jwk_data = _get_signing_key(unverified["kid"])  # type: ignore[reportGeneralTypeIssues]
        if not jwk_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Signing key not found"
            )

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
