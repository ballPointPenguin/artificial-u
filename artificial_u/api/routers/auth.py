from fastapi import APIRouter, Depends

from artificial_u.api.security.auth0 import require_auth

router = APIRouter(tags=["auth"])


@router.get("/me")
def who_am_i(payload=Depends(require_auth)):
    return {
        "sub": payload.get("sub"),
        "scope": payload.get("scope"),
        "claims": payload,
    }
