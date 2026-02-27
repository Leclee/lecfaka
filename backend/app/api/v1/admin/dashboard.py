from datetime import timezone
"""
管理后台 - 仪表盘
"""

from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter
from sqlalchemy import select, func, text

from ...deps import DbSession, CurrentAdmin
from ....models.order import Order
from ....models.user import User
from ....models.commodity import Commodity
from ....models.card import Card
from ....models.withdrawal import Withdrawal
from ....models.recharge import RechargeOrder
from ....models.announcement import Announcement


router = APIRouter()


@router.get("", summary="获取仪表盘数据")
async def get_dashboard(
    admin: CurrentAdmin,
    db: DbSession,
):
    """获取管理后台仪表盘统计数据"""
    
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    this_week = today - timedelta(days=today.weekday())
    this_month = today.replace(day=1)
    
    # ======== 订单统计 ========
    total_orders = (await db.execute(
        select(func.count()).select_from(Order)
    )).scalar() or 0
    
    paid_orders = (await db.execute(
        select(func.count()).select_from(Order).where(Order.status == 1)
    )).scalar() or 0
    
    today_orders = (await db.execute(
        select(func.count()).select_from(Order)
        .where(Order.created_at >= today)
    )).scalar() or 0
    
    pending_orders = (await db.execute(
        select(func.count()).select_from(Order).where(Order.status == 0)
    )).scalar() or 0
    
    # ======== 销售统计 ========
    today_sales = float((await db.execute(
        select(func.coalesce(func.sum(Order.amount), 0))
        .where(Order.status == 1)
        .where(Order.paid_at >= today)
    )).scalar() or 0)
    
    yesterday_sales = float((await db.execute(
        select(func.coalesce(func.sum(Order.amount), 0))
        .where(Order.status == 1)
        .where(Order.paid_at >= yesterday)
        .where(Order.paid_at < today)
    )).scalar() or 0)
    
    week_sales = float((await db.execute(
        select(func.coalesce(func.sum(Order.amount), 0))
        .where(Order.status == 1)
        .where(Order.paid_at >= this_week)
    )).scalar() or 0)
    
    month_sales = float((await db.execute(
        select(func.coalesce(func.sum(Order.amount), 0))
        .where(Order.status == 1)
        .where(Order.paid_at >= this_month)
    )).scalar() or 0)
    
    total_sales = float((await db.execute(
        select(func.coalesce(func.sum(Order.amount), 0))
        .where(Order.status == 1)
    )).scalar() or 0)
    
    # ======== 用户统计 ========
    total_users = (await db.execute(
        select(func.count()).select_from(User)
    )).scalar() or 0
    
    today_users = (await db.execute(
        select(func.count()).select_from(User)
        .where(User.created_at >= today)
    )).scalar() or 0
    
    # 商户数量
    merchant_count = (await db.execute(
        select(func.count()).select_from(User)
        .where(User.business_level > 0)
    )).scalar() or 0
    
    # 用户总余额
    total_balance = float((await db.execute(
        select(func.coalesce(func.sum(User.balance), 0))
    )).scalar() or 0)
    
    # 用户总充值
    total_recharge = float((await db.execute(
        select(func.coalesce(func.sum(User.total_recharge), 0))
    )).scalar() or 0)
    
    # ======== 商品卡密统计 ========
    total_commodities = (await db.execute(
        select(func.count()).select_from(Commodity)
    )).scalar() or 0
    
    online_commodities = (await db.execute(
        select(func.count()).select_from(Commodity).where(Commodity.status == 1)
    )).scalar() or 0
    
    card_stock = (await db.execute(
        select(func.count()).select_from(Card).where(Card.status == 0)
    )).scalar() or 0
    
    card_sold = (await db.execute(
        select(func.count()).select_from(Card).where(Card.status == 1)
    )).scalar() or 0
    
    # ======== 提现统计 ========
    pending_withdrawals = (await db.execute(
        select(func.count()).select_from(Withdrawal).where(Withdrawal.status == 0)
    )).scalar() or 0
    
    pending_withdrawal_amount = float((await db.execute(
        select(func.coalesce(func.sum(Withdrawal.amount), 0))
        .where(Withdrawal.status.in_([0, 1]))
    )).scalar() or 0)
    
    # ======== 充值统计 ========
    today_recharge = float((await db.execute(
        select(func.coalesce(func.sum(RechargeOrder.amount), 0))
        .where(RechargeOrder.status == 1)
        .where(RechargeOrder.paid_at >= today)
    )).scalar() or 0)
    
    return {
        "orders": {
            "total": total_orders,
            "paid": paid_orders,
            "today": today_orders,
            "pending": pending_orders,
        },
        "sales": {
            "today": today_sales,
            "yesterday": yesterday_sales,
            "week": week_sales,
            "month": month_sales,
            "total": total_sales,
        },
        "users": {
            "total": total_users,
            "today": today_users,
            "merchants": merchant_count,
            "total_balance": total_balance,
            "total_recharge": total_recharge,
        },
        "commodities": {
            "total": total_commodities,
            "online": online_commodities,
        },
        "cards": {
            "stock": card_stock,
            "sold": card_sold,
        },
        "withdrawals": {
            "pending": pending_withdrawals,
            "pending_amount": pending_withdrawal_amount,
        },
        "recharge": {
            "today": today_recharge,
        },
    }


@router.get("/announcements", summary="获取公告列表")
async def get_announcements(
    db: DbSession,
):
    """获取最新公告（前台和仪表盘使用）"""
    result = await db.execute(
        select(Announcement)
        .where(Announcement.status == 1)
        .order_by(Announcement.is_top.desc(), Announcement.created_at.desc())
        .limit(10)
    )
    items = result.scalars().all()
    
    return {
        "items": [
            {
                "id": item.id,
                "title": item.title,
                "content": item.content,
                "type": item.type,
                "is_top": item.is_top,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in items
        ],
    }


@router.get("/chart", summary="获取图表数据")
async def get_chart_data(
    admin: CurrentAdmin,
    db: DbSession,
    days: int = 7,
):
    """获取近N天的销售图表数据"""
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    chart_data = []
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        next_day = day + timedelta(days=1)
        
        # 当日销售额
        sales = (await db.execute(
            select(func.coalesce(func.sum(Order.amount), 0))
            .where(Order.status == 1)
            .where(Order.paid_at >= day)
            .where(Order.paid_at < next_day)
        )).scalar() or 0
        
        # 当日充值
        recharge = (await db.execute(
            select(func.coalesce(func.sum(RechargeOrder.amount), 0))
            .where(RechargeOrder.status == 1)
            .where(RechargeOrder.paid_at >= day)
            .where(RechargeOrder.paid_at < next_day)
        )).scalar() or 0
        
        # 当日提现
        withdrawal = (await db.execute(
            select(func.coalesce(func.sum(Withdrawal.actual_amount), 0))
            .where(Withdrawal.status == 2)
            .where(Withdrawal.paid_at >= day)
            .where(Withdrawal.paid_at < next_day)
        )).scalar() or 0
        
        chart_data.append({
            "date": day.strftime("%m-%d"),
            "sales": float(sales),
            "recharge": float(recharge),
            "withdrawal": float(withdrawal),
        })
    
    return {"data": chart_data}
