"""
API 依赖注入
"""

from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models.user import User
from ..core.security import verify_token
from ..core.exceptions import AuthenticationError, AuthorizationError


# HTTP Bearer认证
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials], 
        Depends(security)
    ],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Optional[User]:
    """
    获取当前用户（可选）
    未登录返回None
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = verify_token(token, "access")
    
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    result = await db.execute(
        select(User).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()
    
    if user and user.status == 1:
        return user
    
    return None


async def get_current_user(
    user: Annotated[Optional[User], Depends(get_current_user_optional)]
) -> User:
    """
    获取当前用户（必须）
    未登录抛出异常
    """
    if not user:
        raise AuthenticationError("请先登录")
    return user


async def get_current_admin(
    user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    获取当前管理员用户
    非管理员抛出异常
    """
    if not user.is_admin:
        raise AuthorizationError("需要管理员权限")
    return user


async def get_current_merchant(
    user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    获取当前商户用户
    非商户抛出异常
    """
    if user.business_level <= 0:
        raise AuthorizationError("需要商户权限")
    return user


# 类型别名
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserOptional = Annotated[Optional[User], Depends(get_current_user_optional)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]
CurrentMerchant = Annotated[User, Depends(get_current_merchant)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
