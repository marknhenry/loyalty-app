"""Auth routes — login, token refresh, logout (Story A.1)."""

import logging
from datetime import timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Member
from app.schemas import LoginRequest, MemberOut, TokenResponse
from app.utils import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.config import settings

logger = logging.getLogger("loyalty_app")
router = APIRouter(prefix="/auth", tags=["auth"])

_COOKIE_MAX_AGE = int(timedelta(days=settings.refresh_token_expire_days).total_seconds())


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    result = await db.execute(select(Member).where(Member.email == body.email))
    member = result.scalar_one_or_none()

    if not member or not verify_password(body.password, member.hashed_password):
        logger.warning("Failed login attempt for %s", body.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Email or password incorrect",
            },
        )

    if not member.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ACCOUNT_DISABLED", "message": "Account is disabled"},
        )

    access_token = create_access_token(subject=member.id, role=member.role.value)
    refresh_token = create_refresh_token(subject=member.id)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        secure=False,  # set True in production behind HTTPS
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        max_age=_COOKIE_MAX_AGE,
        secure=False,
    )

    logger.info("Member %s logged in", member.id, extra={"user_id": member.id})
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "MISSING_REFRESH_TOKEN", "message": "Refresh token required"},
        )

    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Refresh token invalid or expired"},
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Not a refresh token"},
        )

    member_id = payload["sub"]
    result = await db.execute(select(Member).where(Member.id == member_id))
    member = result.scalar_one_or_none()

    if not member or not member.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "MEMBER_NOT_FOUND", "message": "Member not found"},
        )

    access_token = create_access_token(subject=member.id, role=member.role.value)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        secure=False,
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


@router.get("/me", response_model=MemberOut)
async def get_me(
    access_token: str | None = Cookie(None),
    authorization: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> MemberOut:
    """Return current user info — useful for frontend auth state hydration."""
    from fastapi import Header
    from app.middleware.auth import get_current_user

    # Inline token extraction for this route
    token = None
    if access_token:
        token = access_token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHENTICATED", "message": "Authentication required"},
        )

    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Token is invalid or expired"},
        )

    result = await db.execute(select(Member).where(Member.id == payload["sub"]))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Member not found"})

    return MemberOut.model_validate(member)
