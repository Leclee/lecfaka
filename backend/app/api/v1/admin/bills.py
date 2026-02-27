from datetime import timezone
"""
管理后台 - 账单管理
"""

from typing import Optional
from fastapi import APIRouter, Query
from sqlalchemy import select, func

from ...deps import DbSession, CurrentAdmin
from ....models.bill import Bill
from ....models.user import User


router = APIRouter()


# ============== APIs ==============

@router.get("", summary="获取账单列表")
async def get_bills(
    admin: CurrentAdmin,
    db: DbSession,
    user_id: Optional[int] = Query(None, description="用户ID"),
    type: Optional[int] = Query(None, description="类型 0=支出 1=收入"),
    currency: Optional[int] = Query(None, description="货币 0=余额 1=积分"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """获取账单列表"""
    query = select(Bill)
    
    if user_id:
        query = query.where(Bill.user_id == user_id)
    if type is not None:
        query = query.where(Bill.type == type)
    if currency is not None:
        query = query.where(Bill.currency == currency)
    
    query = query.order_by(Bill.created_at.desc())
    
    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    bills = result.scalars().all()
    
    # 获取用户信息
    user_ids = list(set(b.user_id for b in bills))
    user_map = {}
    if user_ids:
        users_result = await db.execute(
            select(User.id, User.username, User.avatar).where(User.id.in_(user_ids))
        )
        user_map = {r.id: {"username": r.username, "avatar": r.avatar} for r in users_result}
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [
            {
                "id": b.id,
                "user_id": b.user_id,
                "username": user_map.get(b.user_id, {}).get("username"),
                "avatar": user_map.get(b.user_id, {}).get("avatar"),
                "amount": float(b.amount),
                "balance": float(b.balance),
                "type": b.type,
                "currency": b.currency,
                "description": b.description,
                "order_trade_no": b.order_trade_no,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in bills
        ],
    }


@router.get("/stats", summary="获取账单统计")
async def get_bill_stats(
    admin: CurrentAdmin,
    db: DbSession,
):
    """获取账单统计"""
    from datetime import datetime, timedelta, timezone
    
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 今日收入（余额）
    today_income = (await db.execute(
        select(func.coalesce(func.sum(Bill.amount), 0))
        .where(Bill.type == 1)
        .where(Bill.currency == 0)
        .where(Bill.created_at >= today)
    )).scalar() or 0
    
    # 今日支出（余额）
    today_expense = (await db.execute(
        select(func.coalesce(func.sum(Bill.amount), 0))
        .where(Bill.type == 0)
        .where(Bill.currency == 0)
        .where(Bill.created_at >= today)
    )).scalar() or 0
    
    # 总收入
    total_income = (await db.execute(
        select(func.coalesce(func.sum(Bill.amount), 0))
        .where(Bill.type == 1)
        .where(Bill.currency == 0)
    )).scalar() or 0
    
    # 总支出
    total_expense = (await db.execute(
        select(func.coalesce(func.sum(Bill.amount), 0))
        .where(Bill.type == 0)
        .where(Bill.currency == 0)
    )).scalar() or 0
    
    return {
        "today_income": float(today_income),
        "today_expense": float(today_expense),
        "total_income": float(total_income),
        "total_expense": float(total_expense),
    }
