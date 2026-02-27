"""
管理后台 - 提现管理
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func

from ...deps import DbSession, CurrentAdmin
from ....models.withdrawal import Withdrawal
from ....models.user import User
from ....models.bill import Bill
from ....core.exceptions import NotFoundError, ValidationError


router = APIRouter()


# ============== Schemas ==============

class ReviewWithdrawalRequest(BaseModel):
    """审核提现请求"""
    action: str = Field(..., description="操作 approve=通过 reject=拒绝")
    remark: Optional[str] = Field(None, description="备注")


class PaidWithdrawalRequest(BaseModel):
    """打款确认请求"""
    remark: Optional[str] = Field(None, description="备注")


# ============== APIs ==============

@router.get("", summary="获取提现列表")
async def get_withdrawals(
    admin: CurrentAdmin,
    db: DbSession,
    status: Optional[int] = Query(None, description="状态"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """获取提现列表"""
    query = select(Withdrawal)
    
    if status is not None:
        query = query.where(Withdrawal.status == status)
    if user_id:
        query = query.where(Withdrawal.user_id == user_id)
    
    query = query.order_by(Withdrawal.created_at.desc())
    
    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    
    # 获取用户信息
    user_ids = list(set(w.user_id for w in items))
    user_map = {}
    if user_ids:
        users_result = await db.execute(
            select(User.id, User.username).where(User.id.in_(user_ids))
        )
        user_map = {r.id: r.username for r in users_result}
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [
            {
                "id": w.id,
                "withdraw_no": w.withdraw_no,
                "user_id": w.user_id,
                "username": user_map.get(w.user_id),
                "amount": float(w.amount),
                "fee": float(w.fee),
                "actual_amount": float(w.actual_amount),
                "method": w.method,
                "account": w.account,
                "account_name": w.account_name,
                "status": w.status,
                "user_remark": w.user_remark,
                "admin_remark": w.admin_remark,
                "created_at": w.created_at.isoformat() if w.created_at else None,
                "reviewed_at": w.reviewed_at.isoformat() if w.reviewed_at else None,
                "paid_at": w.paid_at.isoformat() if w.paid_at else None,
            }
            for w in items
        ],
    }


@router.get("/stats", summary="获取提现统计")
async def get_withdrawal_stats(
    admin: CurrentAdmin,
    db: DbSession,
):
    """获取提现统计"""
    # 待审核数量
    pending_count = await db.execute(
        select(func.count()).select_from(Withdrawal).where(Withdrawal.status == 0)
    )
    
    # 待打款数量
    approved_count = await db.execute(
        select(func.count()).select_from(Withdrawal).where(Withdrawal.status == 1)
    )
    
    # 已完成金额
    completed_amount = await db.execute(
        select(func.sum(Withdrawal.actual_amount)).where(Withdrawal.status == 2)
    )
    
    return {
        "pending_count": pending_count.scalar() or 0,
        "approved_count": approved_count.scalar() or 0,
        "completed_amount": float(completed_amount.scalar() or 0),
    }


@router.post("/{withdrawal_id}/review", summary="审核提现")
async def review_withdrawal(
    withdrawal_id: int,
    data: ReviewWithdrawalRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """审核提现申请"""
    result = await db.execute(
        select(Withdrawal).where(Withdrawal.id == withdrawal_id)
    )
    withdrawal = result.scalar_one_or_none()
    
    if not withdrawal:
        raise NotFoundError("提现记录不存在")
    
    if withdrawal.status != 0:
        raise ValidationError("只能审核待审核的提现申请")
    
    if data.action == "approve":
        withdrawal.status = 1
    elif data.action == "reject":
        withdrawal.status = 3
        
        # 退还用户余额
        user_result = await db.execute(
            select(User).where(User.id == withdrawal.user_id)
        )
        user = user_result.scalar_one_or_none()
        if user:
            user.balance = float(user.balance) + float(withdrawal.amount)
            
            # 记录账单
            bill = Bill(
                user_id=user.id,
                amount=float(withdrawal.amount),
                balance=float(user.balance),
                type=1,
                currency=0,
                description=f"提现拒绝退还[{withdrawal.withdraw_no}]",
            )
            db.add(bill)
    else:
        raise ValidationError("无效的操作")
    
    withdrawal.admin_id = admin.id
    withdrawal.admin_remark = data.remark
    withdrawal.reviewed_at = datetime.now(timezone.utc)
    
    return {"message": "操作成功"}


@router.post("/{withdrawal_id}/paid", summary="确认打款")
async def paid_withdrawal(
    withdrawal_id: int,
    data: PaidWithdrawalRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """确认已打款"""
    result = await db.execute(
        select(Withdrawal).where(Withdrawal.id == withdrawal_id)
    )
    withdrawal = result.scalar_one_or_none()
    
    if not withdrawal:
        raise NotFoundError("提现记录不存在")
    
    if withdrawal.status != 1:
        raise ValidationError("只能对已审核的提现进行打款确认")
    
    withdrawal.status = 2
    withdrawal.paid_at = datetime.now(timezone.utc)
    if data.remark:
        withdrawal.admin_remark = data.remark
    
    return {"message": "操作成功"}
