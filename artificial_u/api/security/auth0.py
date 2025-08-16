from functools import lru_cache
from typing import Any, Dict, List, Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError

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

        # Pass RSA key params dict directly (kty,n,e) to python-jose
        rsa_key = {
            "kty": jwk_data.get("kty"),
            "kid": jwk_data.get("kid"),
            "use": jwk_data.get("use"),
            "n": jwk_data.get("n"),
            "e": jwk_data.get("e"),
        }

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=[settings.AUTH0_ALG],
            audience=settings.AUTH0_AUDIENCE,
            issuer=f"https://{settings.AUTH0_DOMAIN}/",
        )
        return payload  # contains sub, scope, etc.
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except JWTClaimsError as e:
        # covers audience/issuer and other claims problems
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid claims: {e}")
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")


def require_scope(scope: str):
    def _checker(payload: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
        scopes = (payload.get("scope") or "").split()
        if scope not in scopes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient scope")
        return payload

    return _checker
