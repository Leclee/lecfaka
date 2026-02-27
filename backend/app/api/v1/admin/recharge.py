"""
管理后台 - 充值订单管理
"""

from typing import Optional
from fastapi import APIRouter, Query
from sqlalchemy import select, func

from ...deps import DbSession, CurrentAdmin
from ....models.recharge import RechargeOrder
from ....models.user import User
from ....models.payment import PaymentMethod
from ....core.exceptions import NotFoundError


router = APIRouter()


# ============== APIs ==============

@router.get("", summary="获取充值订单列表")
async def get_recharge_orders(
    admin: CurrentAdmin,
    db: DbSession,
    status: Optional[int] = Query(None, description="状态"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    trade_no: Optional[str] = Query(None, description="订单号"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """获取充值订单列表"""
    query = select(RechargeOrder)
    
    if status is not None:
        query = query.where(RechargeOrder.status == status)
    if user_id:
        query = query.where(RechargeOrder.user_id == user_id)
    if trade_no:
        query = query.where(RechargeOrder.trade_no.contains(trade_no))
    
    query = query.order_by(RechargeOrder.created_at.desc())
    
    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    orders = result.scalars().all()
    
    # 获取用户和支付方式信息
    user_ids = list(set(o.user_id for o in orders))
    payment_ids = list(set(o.payment_id for o in orders if o.payment_id))
    
    user_map = {}
    if user_ids:
        users_result = await db.execute(
            select(User.id, User.username).where(User.id.in_(user_ids))
        )
        user_map = {r.id: r.username for r in users_result}
    
    payment_map = {}
    if payment_ids:
        payments_result = await db.execute(
            select(PaymentMethod.id, PaymentMethod.name).where(PaymentMethod.id.in_(payment_ids))
        )
        payment_map = {r.id: r.name for r in payments_result}
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [
            {
                "id": o.id,
                "trade_no": o.trade_no,
                "user_id": o.user_id,
                "username": user_map.get(o.user_id),
                "payment_id": o.payment_id,
                "payment_name": payment_map.get(o.payment_id) if o.payment_id else None,
                "amount": float(o.amount),
                "actual_amount": float(o.actual_amount),
                "status": o.status,
                "create_ip": o.create_ip,
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "paid_at": o.paid_at.isoformat() if o.paid_at else None,
            }
            for o in orders
        ],
    }


@router.get("/stats", summary="获取充值统计")
async def get_recharge_stats(
    admin: CurrentAdmin,
    db: DbSession,
):
    """获取充值统计"""
    from datetime import datetime, timezone, timedelta, timezone
    
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 总订单数
    total_count = await db.execute(
        select(func.count()).select_from(RechargeOrder)
    )
    
    # 总金额（已支付）
    total_amount = await db.execute(
        select(func.sum(RechargeOrder.amount))
        .where(RechargeOrder.status == 1)
    )
    
    # 今日订单数
    today_count = await db.execute(
        select(func.count()).select_from(RechargeOrder)
        .where(RechargeOrder.created_at >= today)
    )
    
    # 今日金额
    today_amount = await db.execute(
        select(func.sum(RechargeOrder.amount))
        .where(RechargeOrder.status == 1)
        .where(RechargeOrder.created_at >= today)
    )
    
    return {
        "total_count": total_count.scalar() or 0,
        "total_amount": float(total_amount.scalar() or 0),
        "today_count": today_count.scalar() or 0,
        "today_amount": float(today_amount.scalar() or 0),
    }


@router.post("/{order_id}/complete", summary="手动完成充值")
async def complete_recharge(
    order_id: int,
    admin: CurrentAdmin,
    db: DbSession,
):
    """手动完成充值订单"""
    from datetime import datetime, timezone, timezone
    from ....models.bill import Bill
    
    result = await db.execute(
        select(RechargeOrder).where(RechargeOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise NotFoundError("订单不存在")
    
    if order.status == 1:
        return {"message": "订单已完成"}
    
    # 更新订单状态
    order.status = 1
    order.paid_at = datetime.now(timezone.utc)
    
    # 增加用户余额
    user_result = await db.execute(
        select(User).where(User.id == order.user_id)
    )
    user = user_result.scalar_one_or_none()
    
    if user:
        user.balance = float(user.balance) + float(order.actual_amount)
        user.total_recharge = float(user.total_recharge) + float(order.amount)
        
        # 记录账单
        bill = Bill(
            user_id=user.id,
            amount=float(order.actual_amount),
            balance=float(user.balance),
            type=1,
            currency=0,
            description=f"充值到账[{order.trade_no}]",
            order_trade_no=order.trade_no,
        )
        db.add(bill)
        
        # 钩子：用户充值
        from ....plugins.sdk.hooks import hooks, Events
        await hooks.emit(Events.USER_RECHARGED, {
            "user": user,
            "recharge_order": order,
            "amount": float(order.actual_amount),
        })
    
    return {"message": "操作成功"}
