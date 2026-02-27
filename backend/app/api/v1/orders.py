"""
订单接口
"""

from typing import Optional
from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select

from ..deps import DbSession, CurrentUserOptional
from ...models.order import Order
from ...models.commodity import Commodity
from ...models.payment import PaymentMethod
from ...core.exceptions import NotFoundError, ValidationError
from ...services.order import OrderService


router = APIRouter()


# ============== Schemas ==============

class CreateOrderRequest(BaseModel):
    """创建订单请求"""
    commodity_id: int = Field(..., description="商品ID")
    quantity: int = Field(1, ge=1, description="购买数量")
    payment_id: int = Field(..., description="支付方式ID")
    contact: str = Field(..., min_length=1, description="联系方式")
    password: Optional[str] = Field(None, description="查单密码")
    race: Optional[str] = Field(None, description="商品种类")
    card_id: Optional[int] = Field(None, description="预选卡密ID")
    coupon: Optional[str] = Field(None, description="优惠券码")
    widget: Optional[dict] = Field(None, description="自定义控件数据")


class OrderResponse(BaseModel):
    """订单响应"""
    trade_no: str
    amount: float
    status: int
    payment_url: Optional[str] = None
    secret: Optional[str] = None  # 余额支付成功时返回卡密
    
    class Config:
        from_attributes = True


class OrderDetailResponse(BaseModel):
    """订单详情响应"""
    id: int
    trade_no: str
    amount: float
    quantity: int
    status: int
    delivery_status: int
    contact: str
    secret: Optional[str]
    created_at: str
    paid_at: Optional[str]
    commodity_name: Optional[str]
    payment_name: Optional[str]
    
    class Config:
        from_attributes = True


class QueryOrderRequest(BaseModel):
    """查询订单请求"""
    contact: str = Field(..., description="联系方式或订单号")


class GetSecretRequest(BaseModel):
    """获取卡密请求"""
    password: Optional[str] = Field(None, description="查单密码")


# ============== APIs ==============

@router.post("/create", summary="创建订单")
async def create_order(
    request: CreateOrderRequest,
    db: DbSession,
    user: CurrentUserOptional,
    req: Request,
):
    """创建订单 — 委托给 OrderService 统一处理"""
    from ...utils.request import get_callback_base_url
    
    cb_base = get_callback_base_url(req)
    
    svc = OrderService(db)
    result = await svc.create_order(
        commodity_id=request.commodity_id,
        quantity=request.quantity,
        payment_id=request.payment_id,
        contact=request.contact,
        user=user,
        password=request.password,
        race=request.race,
        card_id=request.card_id,
        coupon_code=request.coupon,
        widget=request.widget,
        client_ip=req.client.host if req.client else None,
        callback_url=cb_base,
        return_url=cb_base,
    )
    
    return result


@router.get("/{trade_no}", response_model=OrderDetailResponse, summary="查询订单")
async def get_order(
    trade_no: str,
    db: DbSession,
):
    """根据订单号查询订单"""
    
    result = await db.execute(
        select(Order).where(Order.trade_no == trade_no)
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
    
    # 未支付不返回卡密
    secret = order.secret if order.status == 1 else None
    
    # 有密码保护的订单不直接返回卡密
    if order.password:
        secret = None
    
    return {
        "id": order.id,
        "trade_no": order.trade_no,
        "amount": float(order.amount),
        "quantity": order.quantity,
        "status": order.status,
        "delivery_status": order.delivery_status,
        "contact": order.contact,
        "secret": secret,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        "commodity_name": commodity_name,
        "payment_name": payment_name,
    }


@router.post("/{trade_no}/secret", summary="获取卡密")
async def get_order_secret(
    trade_no: str,
    request: GetSecretRequest,
    db: DbSession,
):
    """获取订单卡密（需要密码验证）"""
    
    result = await db.execute(
        select(Order).where(Order.trade_no == trade_no)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise NotFoundError("订单不存在")
    
    if order.status != 1:
        raise ValidationError("订单未支付")
    
    # 验证密码
    if order.password and order.password != request.password:
        raise ValidationError("密码错误")
    
    return {
        "secret": order.secret,
    }


@router.post("/query", summary="查询订单列表")
async def query_orders(
    request: QueryOrderRequest,
    db: DbSession,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
):
    """根据联系方式查询订单列表"""
    
    contact = request.contact.strip()
    
    # 判断是订单号还是联系方式
    # 旧格式: 18位纯数字; 新格式: 24位(数字+十六进制字母)
    # 统一规则: 长度 >= 18 且仅包含十六进制字符
    _is_trade_no = len(contact) >= 18 and all(c in '0123456789abcdefABCDEF' for c in contact)
    if _is_trade_no:
        # 订单号查询
        query = select(Order).where(Order.trade_no == contact)
    else:
        # 联系方式查询
        query = select(Order).where(Order.contact == contact)
    
    query = query.order_by(Order.created_at.desc())
    
    result = await db.execute(query.offset((page - 1) * limit).limit(limit))
    orders = result.scalars().all()
    
    items = []
    for order in orders:
        # 获取商品名称
        commodity_result = await db.execute(
            select(Commodity.name).where(Commodity.id == order.commodity_id)
        )
        commodity_name = commodity_result.scalar()
        
        items.append({
            "trade_no": order.trade_no,
            "amount": float(order.amount),
            "quantity": order.quantity,
            "status": order.status,
            "delivery_status": order.delivery_status,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "commodity_name": commodity_name,
            "has_password": bool(order.password),
        })
    
    return {
        "items": items,
    }
