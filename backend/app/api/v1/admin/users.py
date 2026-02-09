"""
管理后台 - 用户管理
"""

from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func

from ...deps import DbSession, CurrentAdmin
from ....models.user import User
from ....core.exceptions import NotFoundError, ValidationError
from ....core.security import get_password_hash


router = APIRouter()


# ============== Schemas ==============

class UpdateUserRequest(BaseModel):
    """更新用户请求"""
    status: Optional[int] = Field(None, description="状态 1=正常 0=禁用")
    balance: Optional[float] = Field(None, description="余额")
    is_admin: Optional[bool] = Field(None, description="是否管理员")
    business_level: Optional[int] = Field(None, description="商户等级")


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    password: str = Field(..., min_length=6, description="新密码")


class AdjustBalanceRequest(BaseModel):
    """调整余额请求"""
    amount: float = Field(..., description="调整金额（正数增加，负数减少）")
    description: str = Field(..., description="调整原因")


# ============== APIs ==============

@router.get("", summary="获取用户列表")
async def get_users(
    admin: CurrentAdmin,
    db: DbSession,
    status: Optional[int] = Query(None, description="状态"),
    keywords: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """获取用户列表"""
    query = select(User)
    
    if status is not None:
        query = query.where(User.status == status)
    if keywords:
        query = query.where(
            User.username.contains(keywords) |
            User.email.contains(keywords) |
            User.phone.contains(keywords)
        )
    
    query = query.order_by(User.id.desc())
    
    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    
    items = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "phone": u.phone,
            "balance": float(u.balance),
            "coin": float(u.coin),
            "total_recharge": float(u.total_recharge),
            "status": u.status,
            "is_admin": u.is_admin,
            "business_level": u.business_level,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        }
        for u in users
    ]
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": items,
    }


@router.get("/{user_id}", summary="获取用户详情")
async def get_user(
    user_id: int,
    admin: CurrentAdmin,
    db: DbSession,
):
    """获取用户详情"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise NotFoundError("用户不存在")
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "avatar": user.avatar,
        "balance": float(user.balance),
        "coin": float(user.coin),
        "total_recharge": float(user.total_recharge),
        "parent_id": user.parent_id,
        "status": user.status,
        "is_admin": user.is_admin,
        "business_level": user.business_level,
        "alipay": user.alipay,
        "wechat": user.wechat,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "last_login_ip": user.last_login_ip,
    }


@router.put("/{user_id}", summary="更新用户")
async def update_user(
    user_id: int,
    request: UpdateUserRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """更新用户信息"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise NotFoundError("用户不存在")
    
    if request.status is not None:
        user.status = request.status
    if request.balance is not None:
        user.balance = request.balance
    if request.is_admin is not None:
        user.is_admin = request.is_admin
    if request.business_level is not None:
        user.business_level = request.business_level
    
    return {"message": "更新成功"}


@router.post("/{user_id}/reset-password", summary="重置密码")
async def reset_password(
    user_id: int,
    request: ResetPasswordRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """重置用户密码"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise NotFoundError("用户不存在")
    
    password_hash, salt = get_password_hash(request.password)
    user.password_hash = password_hash
    user.salt = salt
    
    return {"message": "密码重置成功"}


@router.post("/{user_id}/adjust-balance", summary="调整余额")
async def adjust_balance(
    user_id: int,
    request: AdjustBalanceRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """调整用户余额"""
    from ....models.bill import Bill
    from datetime import datetime
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise NotFoundError("用户不存在")
    
    new_balance = float(user.balance) + request.amount
    if new_balance < 0:
        raise ValidationError("余额不足")
    
    user.balance = new_balance
    
    # 记录账单
    bill = Bill(
        user_id=user.id,
        amount=abs(request.amount),
        balance=new_balance,
        type=1 if request.amount > 0 else 0,
        description=f"[管理员调整] {request.description}",
    )
    db.add(bill)
    
    return {
        "message": "余额调整成功",
        "balance": new_balance,
    }
