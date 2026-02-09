"""
用户相关Schema
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """用户注册"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    invite_code: Optional[str] = Field(None, description="邀请码")


class UserLogin(BaseModel):
    """用户登录"""
    username: str = Field(..., description="用户名/邮箱/手机号")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """刷新Token"""
    refresh_token: str


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    balance: float
    coin: float
    total_recharge: float
    is_admin: bool
    business_level: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """更新用户信息"""
    avatar: Optional[str] = None
    alipay: Optional[str] = None
    wechat: Optional[str] = None


class PasswordChange(BaseModel):
    """修改密码"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, description="新密码")


class PasswordReset(BaseModel):
    """重置密码"""
    password: str = Field(..., min_length=6, description="新密码")


class BalanceAdjust(BaseModel):
    """调整余额"""
    amount: float = Field(..., description="调整金额")
    description: str = Field(..., description="调整原因")
