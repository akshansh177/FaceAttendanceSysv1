from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.redis_client import get_redis
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models.models import Employee, User
from app.schemas.schemas import LoginRequest, MessageResponse, PasswordChangeRequest, RefreshRequest, TokenResponse, UserResponse
from app.services.audit import log_audit
from app.services.rate_limit import check_rate_limit

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    login_key = body.email or body.employee_code or "unknown"
    allowed = await check_rate_limit(f"rl:login:{login_key}", 10, 60)
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many login attempts")

    user = None
    if body.email:
        result = await db.execute(select(User).where(User.email == body.email))
        user = result.scalar_one_or_none()
    elif body.employee_code:
        emp_result = await db.execute(select(Employee).where(Employee.employee_code == body.employee_code))
        emp = emp_result.scalar_one_or_none()
        if emp:
            result = await db.execute(select(User).where(User.employee_id == emp.id))
            user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    access = create_access_token(str(user.id), user.role.value)
    refresh, jti = create_refresh_token(str(user.id))
    redis = await get_redis()
    await redis.setex(f"refresh:{jti}", 7 * 86400, str(user.id))

    await log_audit(db, user.id, "login", "auth", request.client.host if request.client else None)
    return TokenResponse(access_token=access, refresh_token=refresh, role=user.role)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        payload = decode_refresh_token(body.refresh_token)
        jti = payload.get("jti")
        user_id = payload.get("sub")
        if not jti or not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        redis = await get_redis()
        stored = await redis.get(f"refresh:{jti}")
        if not stored:
            raise HTTPException(status_code=401, detail="Refresh token revoked")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")

    access = create_access_token(str(user.id), user.role.value)
    new_refresh, new_jti = create_refresh_token(str(user.id))
    await redis.delete(f"refresh:{jti}")
    await redis.setex(f"refresh:{new_jti}", 7 * 86400, str(user.id))
    return TokenResponse(access_token=access, refresh_token=new_refresh, role=user.role)


@router.post("/logout", response_model=MessageResponse)
async def logout(body: RefreshRequest, user: Annotated[User, Depends(get_current_user)]):
    try:
        payload = decode_refresh_token(body.refresh_token)
        jti = payload.get("jti")
        if jti:
            redis = await get_redis()
            await redis.delete(f"refresh:{jti}")
    except Exception:
        pass
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=UserResponse)
async def me(user: Annotated[User, Depends(get_current_user)]):
    return user


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    body: PasswordChangeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(400, "Current password is incorrect")
    user.password_hash = hash_password(body.new_password)
    await log_audit(db, user.id, "auth.password_changed", "users")
    return MessageResponse(message="Password updated")
