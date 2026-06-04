"""JWT authentication dependency + role-based access guard (Story A.1 / A.2)."""

from fastapi import Cookie, Depends, Header, HTTPException, status
from jose import JWTError

from app.utils import decode_token


def _extract_token(
    authorization: str | None = Header(None),
    access_token: str | None = Cookie(None),
) -> str:
    """Pull JWT from Bearer header or httpOnly cookie."""
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    if access_token:
        return access_token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "UNAUTHENTICATED", "message": "Authentication required"},
    )


def get_current_user(token: str = Depends(_extract_token)) -> dict:
    """Decode JWT and return payload. Raises 401 on invalid/expired token."""
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Token is invalid or expired"},
        )
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Not an access token"},
        )
    return payload


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Guard: reject non-admin callers with 403."""
    if current_user.get("role") not in ("admin", "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Admin access required"},
        )
    return current_user
