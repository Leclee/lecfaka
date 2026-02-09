"""
订单接口
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, func

from ..deps import DbSession, CurrentUserOptional, CurrentUser
from ...models.order import Order
from ...models.commodity import Commodity
from ...models.card import Card
from ...models.user import User
from ...models.bill import Bill
from ...models.payment import PaymentMethod
from ...core.exceptions import ValidationError, NotFoundError
from ...core.security import generate_trade_no


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
    """创建订单"""
    
    # 获取商品
    result = await db.execute(
        select(Commodity).where(Commodity.id == request.commodity_id)
    )
    commodity = result.scalar_one_or_none()
    
    if not commodity or commodity.status != 1:
        raise NotFoundError("商品不存在或已下架")
    
    # 检查是否需要登录
    if commodity.only_user == 1 and not user:
        raise ValidationError("请先登录后再购买")
    
    # 检查购买数量限制
    if commodity.minimum > 0 and request.quantity < commodity.minimum:
        raise ValidationError(f"最少购买 {commodity.minimum} 件")
    if commodity.maximum > 0 and request.quantity > commodity.maximum:
        raise ValidationError(f"最多购买 {commodity.maximum} 件")
    
    # 获取支付方式
    result = await db.execute(
        select(PaymentMethod).where(PaymentMethod.id == request.payment_id)
    )
    payment = result.scalar_one_or_none()
    
    if not payment or payment.status != 1 or payment.commodity != 1:
        raise ValidationError("支付方式不可用")
    
    # 余额支付需要登录
    if payment.handler == "#balance" and not user:
        raise ValidationError("余额支付需要登录")
    
    # 计算金额 - 解析商品配置中的种类价格和批发规则
    base_price = float(commodity.user_price) if user else float(commodity.price)
    category_wholesale = {}  # 种类批发规则
    has_categories = False
    
    # 解析配置
    if commodity.config:
        config_text = commodity.config
        current_section = None
        for line in config_text.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1].lower()
            elif '=' in line and current_section:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                if current_section == 'category':
                    has_categories = True
                    # 如果选择了该种类，更新基础价格
                    if request.race and key == request.race:
                        try:
                            base_price = float(value)
                        except ValueError:
                            pass
                            
                elif current_section == 'category_wholesale':
                    # 解析种类批发规则
                    if '.' in key:
                        cat_name, qty = key.split('.', 1)
                        if cat_name not in category_wholesale:
                            category_wholesale[cat_name] = []
                        try:
                            if value.endswith('%'):
                                category_wholesale[cat_name].append({
                                    "quantity": int(qty),
                                    "discount_percent": float(value[:-1]),
                                    "type": "percent"
                                })
                            else:
                                category_wholesale[cat_name].append({
                                    "quantity": int(qty),
                                    "price": float(value),
                                    "type": "fixed"
                                })
                        except ValueError:
                            pass
    
    # 计算最终单价
    unit_price = base_price
    
    # 如果选择了种类，只应用该种类的批发规则
    if request.race and request.race in category_wholesale:
        rules = sorted(category_wholesale[request.race], key=lambda x: x['quantity'])
        for rule in rules:
            if request.quantity >= rule['quantity']:
                if rule['type'] == 'percent':
                    unit_price = base_price * rule['discount_percent'] / 100
                else:
                    unit_price = rule['price']
    
    amount = round(unit_price * request.quantity, 2)
    
    # 检查库存（自动发货商品）
    if commodity.delivery_way == 0:
        card_query = select(func.count()).select_from(Card).where(
            Card.commodity_id == commodity.id,
            Card.status == 0
        )
        if request.race:
            card_query = card_query.where(Card.race == request.race)
        
        stock_result = await db.execute(card_query)
        stock = stock_result.scalar() or 0
        
        if stock < request.quantity:
            raise ValidationError(f"库存不足，当前库存: {stock}")
    
    # 生成订单号
    trade_no = generate_trade_no()
    
    # 创建订单
    order = Order(
        trade_no=trade_no,
        user_id=user.id if user else None,
        commodity_id=commodity.id,
        payment_id=payment.id,
        amount=amount,
        quantity=request.quantity,
        contact=request.contact,
        password=request.password,
        race=request.race,
        card_id=request.card_id,
        widget=str(request.widget) if request.widget else None,
        owner_id=commodity.owner_id,
        rent=float(commodity.factory_price) * request.quantity,
        create_ip=req.client.host if req.client else None,
        status=0,
        delivery_status=0,
    )
    
    db.add(order)
    await db.flush()
    
    payment_url = None
    payment_type = None
    extra = {}
    secret = None
    
    # 如果是余额支付，直接扣款并发货
    if payment.handler == "#balance":
        # 重新获取用户以确保余额是最新的
        user_result = await db.execute(
            select(User).where(User.id == user.id)
        )
        current_user = user_result.scalar_one()
        
        # 检查余额
        if float(current_user.balance) < amount:
            raise ValidationError(f"余额不足，当前余额: {current_user.balance}，需要: {amount}")
        
        # 扣除余额
        current_user.balance = float(current_user.balance) - amount
        
        # 记录账单
        bill = Bill(
            user_id=current_user.id,
            amount=amount,
            balance=float(current_user.balance),
            type=0,  # 支出
            description=f"购买商品[{commodity.name}]",
            order_trade_no=trade_no,
        )
        db.add(bill)
        
        # 更新订单状态为已支付
        order.status = 1
        order.paid_at = datetime.utcnow()
        
        # 自动发货
        if commodity.delivery_way == 0:
            # 拉取卡密
            card_query = (
                select(Card)
                .where(Card.commodity_id == commodity.id)
                .where(Card.status == 0)
            )
            if request.race:
                card_query = card_query.where(Card.race == request.race)
            
            # 排序方式
            if commodity.delivery_auto_mode == 0:
                card_query = card_query.order_by(Card.id.asc())
            elif commodity.delivery_auto_mode == 1:
                card_query = card_query.order_by(func.random())
            else:
                card_query = card_query.order_by(Card.id.desc())
            
            card_query = card_query.limit(request.quantity)
            
            cards_result = await db.execute(card_query)
            cards = cards_result.scalars().all()
            
            if len(cards) < request.quantity:
                # 回滚余额
                current_user.balance = float(current_user.balance) + amount
                order.status = 0
                raise ValidationError("库存不足，请重试")
            
            # 标记卡密已售
            secrets = []
            for card in cards:
                card.status = 1
                card.order_id = order.id
                card.sold_at = datetime.utcnow()
                secrets.append(card.secret)
            
            secret = "\n".join(secrets)
            order.secret = secret
            order.delivery_status = 1
        else:
            # 手动发货
            order.secret = commodity.delivery_message or "您的订单正在处理中，请耐心等待..."
            order.delivery_status = 0
            secret = order.secret
    
    else:
        # 第三方支付 - 调用支付插件
        import json as json_lib
        from ...payments import get_payment_handler as legacy_get_handler
        from ...plugins import plugin_manager
        from ...plugins.sdk.payment_base import PaymentPluginBase
        
        # 先从插件系统查找，再 fallback 到旧模块
        handler_id = payment.handler
        payment_class = None
        
        # 查插件系统
        pi = plugin_manager.get_plugin(handler_id)
        if pi and pi.instance and isinstance(pi.instance, PaymentPluginBase):
            # 使用已启用的插件实例
            payment_instance = pi.instance
        else:
            # Fallback: 旧的 payments/ 模块或插件类
            payment_class = legacy_get_handler(handler_id)
            if not payment_class:
                # 尝试从插件注册表获取类
                from ...plugins import PAYMENT_HANDLERS
                payment_class = PAYMENT_HANDLERS.get(handler_id)
            
            if payment_class:
                config = json_lib.loads(payment.config) if payment.config else {}
                # 判断是新插件还是旧 PaymentBase
                from ...payments.base import PaymentBase as LegacyPaymentBase
                if issubclass(payment_class, PaymentPluginBase):
                    from ...plugins.sdk.base import PluginMeta
                    meta = PluginMeta(id=handler_id, name=payment.name, version="1.0.0", type="payment")
                    payment_instance = payment_class(meta, config)
                elif issubclass(payment_class, LegacyPaymentBase):
                    payment_instance = payment_class(config)
                else:
                    payment_instance = None
            else:
                payment_instance = None
        
        if not payment_instance:
            raise ValidationError(f"支付方式 {handler_id} 未找到对应处理器")
        
        # 构建回调 URL（从请求头自动检测域名）
        from ...utils.request import get_callback_base_url
        
        cb_base = get_callback_base_url(req)
        
        # notify_url (异步回调) - 支付网关服务器会主动请求此地址
        callback_url = f"{cb_base}/api/v1/payments/{handler_id}/callback"
        
        # return_url (同步跳转) - 支付完成后浏览器跳转
        return_url = f"{cb_base}/api/v1/payments/{handler_id}/return"
        
        # 手续费
        pay_amount = amount
        if payment.cost and float(payment.cost) > 0:
            if payment.cost_type == 0:
                order.pay_cost = float(payment.cost)
            else:
                order.pay_cost = pay_amount * float(payment.cost)
            pay_amount += float(order.pay_cost)
            pay_amount = round(pay_amount, 2)
            order.amount = pay_amount
        
        # 调用支付接口
        payment_result = await payment_instance.create_payment(
            trade_no=trade_no,
            amount=pay_amount,
            callback_url=callback_url,
            return_url=return_url,
            channel=payment.code or "alipay",
            client_ip=req.client.host if req.client else None,
            product_name=commodity.name,  # 传递商品名称
        )
        
        if not payment_result.success:
            raise ValidationError(f"支付创建失败: {payment_result.error_msg}")
        
        payment_url = payment_result.payment_url
        payment_type = payment_result.payment_type.value  # "redirect", "qrcode", "form" 等
        extra = payment_result.extra or {}
        
        # 二维码模式 - 把 qrcode_url 放入 extra 给前端展示
        if payment_type == "qrcode" and payment_result.qrcode_url:
            payment_url = payment_result.qrcode_url
            extra["qrcode_url"] = payment_result.qrcode_url
        
        # 如果是表单提交类型
        if payment_result.form_action:
            payment_url = payment_result.form_action
            payment_type = "form"
            extra = {"form_data": payment_result.form_data}
        
        order.pay_url = payment_url or payment_result.qrcode_url
    
    await db.commit()
    
    return {
        "trade_no": trade_no,
        "amount": float(order.amount),
        "status": order.status,
        "payment_url": payment_url,
        "payment_type": payment_type,
        "extra": extra,
        "secret": secret,
    }


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
    if len(contact) == 18 and contact.isdigit():
        # 订单号
        query = select(Order).where(Order.trade_no == contact)
    else:
        # 联系方式
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
