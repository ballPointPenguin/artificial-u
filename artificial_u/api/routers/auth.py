from fastapi import APIRouter, Depends

from artificial_u.api.dependencies import ensure_student
from artificial_u.api.security.auth0 import require_auth

router = APIRouter(tags=["auth"])


@router.get("/me")
def who_am_i(payload=Depends(require_auth), student=Depends(ensure_student)):
    return {
        "sub": payload.get("sub"),
        "scope": payload.get("scope"),
        "claims": payload,
        "student": {
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "auth0_sub": student.auth0_sub,
        },
    }
