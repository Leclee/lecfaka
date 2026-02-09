"""
管理后台 - 订单管理
"""

from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func

from ...deps import DbSession, CurrentAdmin
from ....models.order import Order
from ....models.commodity import Commodity
from ....models.payment import PaymentMethod
from ....core.exceptions import NotFoundError, ValidationError


router = APIRouter()


# ============== Schemas ==============

class DeliverOrderRequest(BaseModel):
    """手动发货请求"""
    secret: str = Field(..., description="发货内容")


# ============== APIs ==============

@router.get("", summary="获取订单列表")
async def get_orders(
    admin: CurrentAdmin,
    db: DbSession,
    status: Optional[int] = Query(None, description="订单状态"),
    delivery_status: Optional[int] = Query(None, description="发货状态"),
    trade_no: Optional[str] = Query(None, description="订单号"),
    contact: Optional[str] = Query(None, description="联系方式"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """获取订单列表"""
    query = select(Order)
    
    if status is not None:
        query = query.where(Order.status == status)
    if delivery_status is not None:
        query = query.where(Order.delivery_status == delivery_status)
    if trade_no:
        query = query.where(Order.trade_no.contains(trade_no))
    if contact:
        query = query.where(Order.contact.contains(contact))
    
    query = query.order_by(Order.created_at.desc())
    
    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    orders = result.scalars().all()
    
    # 获取商品和支付方式名称
    commodity_ids = list(set(o.commodity_id for o in orders))
    payment_ids = list(set(o.payment_id for o in orders if o.payment_id))
    
    commodity_map = {}
    if commodity_ids:
        commodities_result = await db.execute(
            select(Commodity.id, Commodity.name)
            .where(Commodity.id.in_(commodity_ids))
        )
        commodity_map = {r.id: r.name for r in commodities_result}
    
    payment_map = {}
    if payment_ids:
        payments_result = await db.execute(
            select(PaymentMethod.id, PaymentMethod.name)
            .where(PaymentMethod.id.in_(payment_ids))
        )
        payment_map = {r.id: r.name for r in payments_result}
    
    items = [
        {
            "id": o.id,
            "trade_no": o.trade_no,
            "commodity_id": o.commodity_id,
            "commodity_name": commodity_map.get(o.commodity_id),
            "payment_name": payment_map.get(o.payment_id) if o.payment_id else None,
            "amount": float(o.amount),
            "quantity": o.quantity,
            "contact": o.contact,
            "status": o.status,
            "delivery_status": o.delivery_status,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "paid_at": o.paid_at.isoformat() if o.paid_at else None,
        }
        for o in orders
    ]
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": items,
    }


@router.get("/{order_id}", summary="获取订单详情")
async def get_order(
    order_id: int,
    admin: CurrentAdmin,
    db: DbSession,
):
    """获取订单详情"""
    result = await db.execute(
        select(Order).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise NotFoundError("订单不存在")
    
    # 获取商品名称
    commodity_result = await db.execute(
        select(Commodity.name).where(Commodity.id == order.commodity_id)
    )
    commodity_name = commodity_result.scalar()
    
    # 获取支付方式名称
    payment_name = None
    if order.payment_id:
        payment_result = await db.execute(
            select(PaymentMethod.name).where(PaymentMethod.id == order.payment_id)
        )
        payment_name = payment_result.scalar()
    
    return {
        "id": order.id,
        "trade_no": order.trade_no,
        "user_id": order.user_id,
        "commodity_id": order.commodity_id,
        "commodity_name": commodity_name,
        "payment_id": order.payment_id,
        "payment_name": payment_name,
        "amount": float(order.amount),
        "cost": float(order.cost),
        "quantity": order.quantity,
        "race": order.race,
        "contact": order.contact,
        "password": order.password,
        "secret": order.secret,
        "widget": order.widget,
        "status": order.status,
        "delivery_status": order.delivery_status,
        "create_ip": order.create_ip,
        "external_trade_no": order.external_trade_no,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
    }


@router.post("/{order_id}/deliver", summary="手动发货")
async def deliver_order(
    order_id: int,
    request: DeliverOrderRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """手动发货"""
    result = await db.execute(
        select(Order).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise NotFoundError("订单不存在")
    
    if order.status != 1:
        raise ValidationError("订单未支付，无法发货")
    
    if order.delivery_status == 1:
        raise ValidationError("订单已发货")
    
    order.secret = request.secret
    order.delivery_status = 1
    
    return {"message": "发货成功"}


@router.post("/{order_id}/refund", summary="订单退款")
async def refund_order(
    order_id: int,
    admin: CurrentAdmin,
    db: DbSession,
):
    """订单退款（仅标记状态，实际退款需人工处理）"""
    result = await db.execute(
        select(Order).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise NotFoundError("订单不存在")
    
    if order.status != 1:
        raise ValidationError("只有已支付的订单可以退款")
    
    order.status = 3  # 已退款
    
    return {"message": "退款成功（请人工处理实际退款）"}
