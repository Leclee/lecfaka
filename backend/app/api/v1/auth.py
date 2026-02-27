"""
认证接口
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, or_

from ..deps import DbSession, CurrentUser
from ...models.user import User
from ...core.security import (
    get_password_hash, 
    verify_password,
    needs_rehash,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from ...core.exceptions import ValidationError, AuthenticationError
from ...plugins.sdk.hooks import hooks, Events


router = APIRouter()


# ============== Schemas ==============

class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    invite_code: Optional[str] = Field(None, description="邀请码/推广人ID")


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名/邮箱/手机号")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    email: Optional[str]
    phone: Optional[str]
    avatar: Optional[str]
    balance: float
    coin: float
    is_admin: bool
    business_level: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============== APIs ==============

@router.post("/register", response_model=TokenResponse, summary="用户注册")
async def register(
    request: RegisterRequest,
    db: DbSession,
    req: Request,
):
    """用户注册"""
    
    # 检查用户名是否存在
    result = await db.execute(
        select(User).where(User.username == request.username)
    )
    if result.scalar_one_or_none():
        raise ValidationError("用户名已存在")
    
    # 检查邮箱是否存在
    if request.email:
        result = await db.execute(
            select(User).where(User.email == request.email)
        )
        if result.scalar_one_or_none():
            raise ValidationError("邮箱已被注册")
    
    # 检查手机号是否存在
    if request.phone:
        result = await db.execute(
            select(User).where(User.phone == request.phone)
        )
        if result.scalar_one_or_none():
            raise ValidationError("手机号已被注册")
    
    # 处理推广关系
    parent_id = None
    if request.invite_code:
        try:
            parent_id = int(request.invite_code)
            result = await db.execute(
                select(User).where(User.id == parent_id)
            )
            if not result.scalar_one_or_none():
                parent_id = None
        except ValueError:
            pass
    
    # 创建用户
    password_hash, salt = get_password_hash(request.password)
    user = User(
        username=request.username,
        email=request.email,
        phone=request.phone,
        password_hash=password_hash,
        salt=salt,
        parent_id=parent_id,
        last_login_ip=req.client.host if req.client else None,
    )
    db.add(user)
    await db.flush()
    
    # 钩子：用户注册
    await hooks.emit(Events.USER_REGISTERED, {"user": user, "ip": req.client.host if req.client else None})
    
    # 生成Token
    token_data = {"sub": str(user.id)}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(
    request: LoginRequest,
    db: DbSession,
    req: Request,
):
    """用户登录"""
    
    # 查找用户
    result = await db.execute(
        select(User).where(
            or_(
                User.username == request.username,
                User.email == request.username,
                User.phone == request.username,
            )
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise AuthenticationError("用户名或密码错误")
    
    # 验证密码
    if not verify_password(request.password, user.password_hash, user.salt):
        raise AuthenticationError("用户名或密码错误")
    
    ## 透明升级：旧 SHA256 密码自动迁移到 bcrypt（用户无感知）
    if needs_rehash(user.password_hash):
        new_hash, new_salt = get_password_hash(request.password)
        user.password_hash = new_hash
        user.salt = new_salt
    
    # 检查状态
    if user.status != 1:
        raise AuthenticationError("账户已被禁用")
    
    # 更新登录信息
    user.last_login_at = datetime.now(timezone.utc)
    user.last_login_ip = req.client.host if req.client else None
    
    # 钩子：用户登录
    await hooks.emit(Events.USER_LOGIN, {"user": user, "ip": req.client.host if req.client else None})
    
    # 生成Token
    token_data = {"sub": str(user.id)}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=TokenResponse, summary="刷新Token")
async def refresh_token(
    request: RefreshRequest,
    db: DbSession,
):
    """刷新Token"""
    
    payload = verify_token(request.refresh_token, "refresh")
    if not payload:
        raise AuthenticationError("Token无效或已过期")
    
    user_id = payload.get("sub")
    
    # 验证用户存在
    result = await db.execute(
        select(User).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user or user.status != 1:
        raise AuthenticationError("用户不存在或已禁用")
    
    # 生成新Token
    token_data = {"sub": str(user.id)}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_me(
    user: CurrentUser,
):
    """获取当前登录用户信息"""
    return user


@router.post("/logout", summary="退出登录")
async def logout():
    """
    退出登录
    注：JWT无状态，客户端删除Token即可
    如需服务端失效，需实现Token黑名单
    """
    return {"message": "退出成功"}
