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


def get_user_info(access_token: str) -> Dict[str, Any]:
    """
    Fetch user profile information from Auth0's /userinfo endpoint.

    This is needed because the access token may not contain user profile claims
    unless explicitly configured in Auth0 Actions.

    Args:
        access_token: The OAuth2 access token

    Returns:
        Dict containing user profile information (sub, email, name, etc.)
    """
    settings = get_settings()
    userinfo_url = f"https://{settings.AUTH0_DOMAIN}/userinfo"

    with httpx.Client(timeout=5.0) as client:
        response = client.get(userinfo_url, headers={"Authorization": f"Bearer {access_token}"})
        response.raise_for_status()
        return response.json()


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


# Mock JWT payload for testing
MOCK_JWT_PAYLOAD = {
    "sub": "test-user-123",
    "email": "test@example.com",
    "name": "Test User",
    "nickname": "testuser",
    "scope": "read:courses write:courses read:professors write:professors read:departments write:departments "
    + "read:lectures write:lectures read:topics write:topics",
}


def mock_require_auth() -> Dict[str, Any]:
    """Mock authentication function that returns test JWT payload."""
    return MOCK_JWT_PAYLOAD


def require_scope(scope: str):
    def _checker(payload: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
        scopes = (payload.get("scope") or "").split()
        if scope not in scopes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient scope")
        return payload

    return _checker


def require_role(min_role: str):
    """
    Dependency factory that checks if user has the required role.

    Role hierarchy: viewer < creator < admin

    Args:
        min_role: Minimum role required (viewer, creator, admin)

    Returns:
        Dependency function that returns Student if authorized

    Raises:
        HTTPException: If user lacks required role or account is inactive
    """
    from artificial_u.models.core import Student

    ROLE_HIERARCHY = {"viewer": 0, "creator": 1, "admin": 2}

    def _checker(student: Student) -> Student:
        if not student.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

        user_level = ROLE_HIERARCHY.get(student.role, 0)
        required_level = ROLE_HIERARCHY.get(min_role, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"Requires {min_role} role or higher"
            )
        return student

    # Import ensure_student to use as dependency
    from artificial_u.api.dependencies import ensure_student

    return Depends(lambda s=Depends(ensure_student): _checker(s))


def require_coins(cost: int):
    """
    Dependency factory that checks and deducts coins for operations.

    Admin users bypass coin checks (unlimited).

    Args:
        cost: Number of coins required for the operation

    Returns:
        Dependency function that returns Student after deducting coins

    Raises:
        HTTPException: If user has insufficient coins (402 Payment Required)
    """
    from artificial_u.models.core import Student
    from artificial_u.models.repositories import RepositoryFactory

    def _checker(student: Student, repository_factory: RepositoryFactory) -> Student:
        # Admin users have unlimited coins
        if student.role == "admin":
            return student

        # All generation requires at least 'creator' role
        if student.role not in ["creator", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Generation features require creator role or higher",
            )

        # Check and deduct coins atomically (for non-admins)
        try:
            updated_student = repository_factory.student.deduct_coins(student.id, cost)
            return updated_student
        except ValueError as e:
            # Insufficient coins or student not found
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(e))

    # Import dependencies at module scope
    from artificial_u.api.dependencies import ensure_student, get_repository_factory

    return Depends(
        lambda s=Depends(ensure_student), rf=Depends(get_repository_factory): _checker(s, rf)
    )
