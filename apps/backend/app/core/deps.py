from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis_client import get_redis
from app.core.security import decode_access_token
from app.models.models import User, UserRole

security = HTTPBearer()
RBAC_CACHE_TTL = 1800


async def _cache_user_role(user_id: UUID, role: UserRole) -> None:
    redis = await get_redis()
    await redis.setex(f"rbac:user:{user_id}", RBAC_CACHE_TTL, role.value)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    uid = UUID(user_id)
    redis = await get_redis()
    cached_role = await redis.get(f"rbac:user:{uid}")
    if cached_role:
        role_val = cached_role.decode() if isinstance(cached_role, bytes) else cached_role
        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if user and user.is_active:
            user.role = UserRole(role_val)
            return user

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    await _cache_user_role(user.id, user.role)
    return user


def require_roles(*roles: UserRole):
    async def checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        allowed = {r.value for r in roles}
        allowed.add(UserRole.SUPER_ADMIN.value)
        if user.role.value not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return checker


HR_ROLES = (UserRole.SUPER_ADMIN, UserRole.HR_MANAGER)
MANAGER_ROLES = (UserRole.SUPER_ADMIN, UserRole.HR_MANAGER, UserRole.TEAM_MANAGER)
