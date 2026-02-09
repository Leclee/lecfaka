"""
商城接口
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from ..deps import DbSession, CurrentUserOptional
from ...models.category import Category
from ...models.commodity import Commodity
from ...models.card import Card
from ...models.payment import PaymentMethod
from ...models.order import Order
from ...services import OrderService
from ...core.exceptions import ValidationError, NotFoundError


router = APIRouter()


# ============== Schemas ==============

class CategoryResponse(BaseModel):
    """分类响应"""
    id: int
    name: str
    icon: Optional[str]
    sort: int
    
    class Config:
        from_attributes = True


class CommodityListResponse(BaseModel):
    """商品列表响应"""
    id: int
    name: str
    cover: Optional[str]
    price: float
    user_price: float
    category_id: int
    stock: int
    sold_count: int
    delivery_way: int
    recommend: int
    
    class Config:
        from_attributes = True


class CategoryConfigItem(BaseModel):
    """商品种类配置项"""
    name: str
    price: float

class WholesaleConfigItem(BaseModel):
    """批发配置项"""
    quantity: int
    price: Optional[float] = None  # 固定价格
    discount_percent: Optional[float] = None  # 百分比折扣（如90表示9折）
    type: str = "fixed"  # "fixed" 或 "percent"

class SkuConfigItem(BaseModel):
    """SKU配置项"""
    group: str
    option: str
    extra_price: float

class CommodityDetailResponse(BaseModel):
    """商品详情响应"""
    id: int
    name: str
    description: Optional[str]
    cover: Optional[str]
    price: float
    user_price: float
    category_id: int
    stock: int
    sold_count: int
    delivery_way: int
    contact_type: int
    password_status: int
    draft_status: int
    draft_premium: float
    minimum: int
    maximum: int
    only_user: int
    widget: Optional[str]
    leave_message: Optional[str]
    wholesale_config: Optional[str]
    # 解析后的配置参数
    categories: Optional[List[CategoryConfigItem]] = None
    wholesale: Optional[List[WholesaleConfigItem]] = None
    sku_config: Optional[List[SkuConfigItem]] = None
    category_wholesale: Optional[Dict[str, List[WholesaleConfigItem]]] = None
    
    class Config:
        from_attributes = True


class CardDraftResponse(BaseModel):
    """预选卡密响应"""
    id: int
    draft: Optional[str]
    draft_premium: float
    
    class Config:
        from_attributes = True


class PaymentMethodResponse(BaseModel):
    """支付方式响应"""
    id: int
    name: str
    icon: Optional[str]
    handler: str
    code: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============== APIs ==============

@router.get("/categories", response_model=List[CategoryResponse], summary="获取分类列表")
async def get_categories(
    db: DbSession,
    user: CurrentUserOptional,
):
    """获取商品分类列表"""
    
    query = (
        select(Category)
        .where(Category.status == 1)
        .where(Category.owner_id.is_(None))  # 主站分类
        .order_by(Category.sort.asc())
    )
    
    result = await db.execute(query)
    categories = result.scalars().all()
    
    return categories


@router.get("/commodities", summary="获取商品列表")
async def get_commodities(
    db: DbSession,
    user: CurrentUserOptional,
    category_id: Optional[int] = Query(None, description="分类ID"),
    keywords: Optional[str] = Query(None, description="搜索关键词"),
    recommend: Optional[int] = Query(None, description="只看推荐"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """获取商品列表"""
    
    query = (
        select(Commodity)
        .where(Commodity.status == 1)
        .where(Commodity.hide == 0)
        .where(Commodity.owner_id.is_(None))  # 主站商品
    )
    
    # 分类筛选
    if category_id:
        query = query.where(Commodity.category_id == category_id)
    
    # 关键词搜索
    if keywords:
        query = query.where(Commodity.name.contains(keywords))
    
    # 推荐筛选
    if recommend == 1:
        query = query.where(Commodity.recommend == 1)
    
    # 排序
    query = query.order_by(Commodity.sort.asc(), Commodity.id.desc())
    
    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    commodities = result.scalars().all()
    
    # 获取库存和销量
    items = []
    for c in commodities:
        stock = 0
        
        if not c.shared_id:
            # 统计可用卡密数量（无论发货方式）
            card_count_result = await db.execute(
                select(func.count())
                .select_from(Card)
                .where(Card.commodity_id == c.id)
                .where(Card.status == 0)
            )
            card_stock = card_count_result.scalar() or 0
            
            # 如果有卡密，使用卡密数量；否则使用商品表的 stock 字段
            stock = card_stock if card_stock > 0 else c.stock
        else:
            stock = c.stock
        
        # 统计销量 (TODO: 优化查询)
        sold_count = 0
        
        items.append({
            "id": c.id,
            "name": c.name,
            "cover": c.cover,
            "price": float(c.price),
            "user_price": float(c.user_price) if user else float(c.price),
            "category_id": c.category_id,
            "stock": stock,
            "sold_count": sold_count,
            "delivery_way": c.delivery_way,
            "recommend": c.recommend,
        })
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": items,
    }


@router.get("/commodities/{commodity_id}", response_model=CommodityDetailResponse, summary="获取商品详情")
async def get_commodity_detail(
    commodity_id: int,
    db: DbSession,
    user: CurrentUserOptional,
):
    """获取商品详情"""
    
    result = await db.execute(
        select(Commodity)
        .where(Commodity.id == commodity_id)
        .where(Commodity.status == 1)
    )
    commodity = result.scalar_one_or_none()
    
    if not commodity:
        from ...core.exceptions import NotFoundError
        raise NotFoundError("商品不存在")
    
    # 计算库存：统计可用卡密数量，如果没有卡密则使用商品表的 stock 字段
    stock = 0
    if not commodity.shared_id:
        card_count_result = await db.execute(
            select(func.count())
            .select_from(Card)
            .where(Card.commodity_id == commodity.id)
            .where(Card.status == 0)
        )
        card_stock = card_count_result.scalar() or 0
        stock = card_stock if card_stock > 0 else commodity.stock
    else:
        stock = commodity.stock
    
    # 解析商品配置参数（种类、批发等）
    categories = []  # 商品种类 [category]
    wholesale = []   # 批发规则 [wholesale]
    sku_config = []  # SKU规格 [sku]
    category_wholesale = {}  # 种类批发 [category_wholesale]
    
    if commodity.config:
        config_text = commodity.config
        current_section = None
        for line in config_text.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):  # 跳过空行和注释
                continue
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1].lower()
            elif '=' in line and current_section:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                try:
                    if current_section == 'category':
                        # 种类=价格
                        categories.append({
                            "name": key,
                            "price": float(value)
                        })
                    elif current_section == 'wholesale':
                        # 全局批发规则（仅当商品无种类时使用）
                        # 支持两种格式：数量=价格 或 数量=百分比%
                        if value.endswith('%'):
                            # 百分比折扣
                            wholesale.append({
                                "quantity": int(key),
                                "discount_percent": float(value[:-1]),
                                "type": "percent"
                            })
                        else:
                            # 固定价格
                            wholesale.append({
                                "quantity": int(key),
                                "price": float(value),
                                "type": "fixed"
                            })
                    elif current_section == 'sku':
                        # 规格组.选项=加价
                        if '.' in key:
                            group, option = key.split('.', 1)
                            sku_config.append({
                                "group": group,
                                "option": option,
                                "extra_price": float(value)
                            })
                    elif current_section == 'category_wholesale':
                        # 种类批发规则：种类.数量=价格 或 种类.数量=百分比%
                        if '.' in key:
                            cat_name, qty = key.split('.', 1)
                            if cat_name not in category_wholesale:
                                category_wholesale[cat_name] = []
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
                except (ValueError, TypeError):
                    pass
    
    # 按数量排序批发规则
    wholesale.sort(key=lambda x: x['quantity'])
    for cat_name in category_wholesale:
        category_wholesale[cat_name].sort(key=lambda x: x['quantity'])
    
    # 统计销量
    sold_result = await db.execute(
        select(func.count())
        .select_from(Order)
        .where(Order.commodity_id == commodity.id)
        .where(Order.status == 1)  # 已支付
    )
    sold_count = sold_result.scalar() or 0
    
    result = {
        "id": commodity.id,
        "name": commodity.name,
        "description": commodity.description,
        "cover": commodity.cover,
        "price": float(commodity.price),
        "user_price": float(commodity.user_price) if user else float(commodity.price),
        "category_id": commodity.category_id,
        "stock": stock,
        "sold_count": sold_count,
        "delivery_way": commodity.delivery_way,
        "contact_type": commodity.contact_type,
        "password_status": commodity.password_status,
        "draft_status": commodity.draft_status,
        "draft_premium": float(commodity.draft_premium),
        "minimum": commodity.minimum,
        "maximum": commodity.maximum,
        "only_user": commodity.only_user,
        "widget": commodity.widget,
        "leave_message": commodity.leave_message,
        "wholesale_config": commodity.wholesale_config,
        # 解析后的配置参数
        "categories": categories if categories else None,
        "wholesale": wholesale if wholesale else None,
        "sku_config": sku_config if sku_config else None,
        "category_wholesale": category_wholesale if category_wholesale else None,
    }
    return result


@router.get("/commodities/{commodity_id}/cards", summary="获取预选卡密")
async def get_commodity_cards(
    commodity_id: int,
    db: DbSession,
    race: Optional[str] = Query(None, description="商品种类"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
):
    """获取可预选的卡密列表"""
    
    # 检查商品是否支持预选
    result = await db.execute(
        select(Commodity).where(Commodity.id == commodity_id)
    )
    commodity = result.scalar_one_or_none()
    
    if not commodity or commodity.draft_status != 1:
        from ...core.exceptions import ValidationError
        raise ValidationError("该商品不支持预选")
    
    # 查询可用卡密
    query = (
        select(Card)
        .where(Card.commodity_id == commodity_id)
        .where(Card.status == 0)
    )
    
    if race:
        query = query.where(Card.race == race)
    
    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    cards = result.scalars().all()
    
    items = [
        {
            "id": c.id,
            "draft": c.draft,
            "draft_premium": float(c.draft_premium),
        }
        for c in cards
    ]
    
    return {
        "total": total,
        "items": items,
    }


@router.get("/payments", response_model=List[PaymentMethodResponse], summary="获取支付方式")
async def get_payments(
    db: DbSession,
    user: CurrentUserOptional,
):
    """获取可用的支付方式列表"""
    
    query = (
        select(PaymentMethod)
        .where(PaymentMethod.status == 1)
        .where(PaymentMethod.commodity == 1)
        .order_by(PaymentMethod.sort.asc())
    )
    
    # 未登录用户隐藏余额支付
    if not user:
        query = query.where(PaymentMethod.handler != "#balance")
    
    result = await db.execute(query)
    payments = result.scalars().all()
    
    return payments


# ============== 订单相关 ==============

class CreateOrderRequest(BaseModel):
    """创建订单请求"""
    commodity_id: int
    quantity: int = 1
    payment_id: int
    contact: str
    password: Optional[str] = None
    race: Optional[str] = None
    card_id: Optional[int] = None
    coupon_code: Optional[str] = None
    widget: Optional[Dict[str, Any]] = None


class OrderResponse(BaseModel):
    """订单响应"""
    trade_no: str
    commodity_name: str
    amount: float
    quantity: int
    status: int
    delivery_status: int
    payment_url: Optional[str] = None
    created_at: Optional[str] = None


@router.post("/orders", summary="创建订单")
async def create_order(
    request: Request,
    data: CreateOrderRequest,
    db: DbSession,
    user: CurrentUserOptional,
):
    """创建订单"""
    order_service = OrderService(db)
    
    # 获取客户端IP
    client_ip = request.client.host if request.client else None
    
    # 从请求头自动检测回调 URL
    from ...utils.request import get_callback_base_url
    cb_base = get_callback_base_url(request)
    
    result = await order_service.create_order(
        commodity_id=data.commodity_id,
        quantity=data.quantity,
        payment_id=data.payment_id,
        contact=data.contact,
        user=user,
        password=data.password,
        race=data.race,
        card_id=data.card_id,
        coupon_code=data.coupon_code,
        widget=data.widget,
        client_ip=client_ip,
        callback_url=cb_base,
        return_url=cb_base,
    )
    
    # OrderService.create_order() 内部已 commit，无需重复
    return result


@router.get("/orders/{trade_no}", summary="查询订单")
async def get_order(
    trade_no: str,
    contact: str = Query(..., description="联系方式"),
    db: DbSession = None,
):
    """根据订单号和联系方式查询订单"""
    result = await db.execute(
        select(Order)
        .where(Order.trade_no == trade_no)
        .where(Order.contact == contact)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise NotFoundError("订单不存在或联系方式不匹配")
    
    # 获取商品名称
    commodity_result = await db.execute(
        select(Commodity).where(Commodity.id == order.commodity_id)
    )
    commodity = commodity_result.scalar_one_or_none()
    
    response = {
        "trade_no": order.trade_no,
        "commodity_name": commodity.name if commodity else "未知商品",
        "amount": float(order.amount),
        "quantity": order.quantity,
        "status": order.status,
        "delivery_status": order.delivery_status,
        "secret": order.secret if order.delivery_status == 1 else None,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
    }
    
    return response
