"""
鍟嗗煄鎺ュ彛
"""

import json as json_lib
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
    """鍒嗙被鍝嶅簲"""
    id: int
    name: str
    icon: Optional[str]
    sort: int
    
    class Config:
        from_attributes = True


class CommodityListResponse(BaseModel):
    """鍟嗗搧鍒楄〃鍝嶅簲"""
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
    """Category config item"""
    name: str
    price: float

class WholesaleConfigItem(BaseModel):
    """Wholesale config item"""
    quantity: int
    price: Optional[float] = None  # 鍥哄畾浠锋牸
    discount_percent: Optional[float] = None  # 鐧惧垎姣旀姌鎵ｏ紙濡?0琛ㄧず9鎶橈級
    type: str = "fixed"  # "fixed" 鎴?"percent"

class SkuConfigItem(BaseModel):
    """SKU???"""
    group: str
    option: str
    extra_price: float

class CommodityDetailResponse(BaseModel):
    """鍟嗗搧璇︽儏鍝嶅簲"""
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
    # 瑙ｆ瀽鍚庣殑閰嶇疆鍙傛暟
    categories: Optional[List[CategoryConfigItem]] = None
    wholesale: Optional[List[WholesaleConfigItem]] = None
    sku_config: Optional[List[SkuConfigItem]] = None
    category_wholesale: Optional[Dict[str, List[WholesaleConfigItem]]] = None
    
    class Config:
        from_attributes = True


class CardDraftResponse(BaseModel):
    """Card draft response"""
    id: int
    draft: Optional[str]
    draft_premium: float
    
    class Config:
        from_attributes = True


class PaymentMethodResponse(BaseModel):
    """鏀粯鏂瑰紡鍝嶅簲"""
    id: int
    name: str
    icon: Optional[str]
    handler: str
    code: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============== APIs ==============

@router.get("/categories", response_model=List[CategoryResponse], summary="鑾峰彇鍒嗙被鍒楄〃")
async def get_categories(
    db: DbSession,
    user: CurrentUserOptional,
):
    """鑾峰彇鍟嗗搧鍒嗙被鍒楄〃"""
    
    query = (
        select(Category)
        .where(Category.status == 1)
        .where(Category.owner_id.is_(None))  # 涓荤珯鍒嗙被
        .order_by(Category.sort.asc())
    )
    
    result = await db.execute(query)
    categories = result.scalars().all()
    
    return categories


@router.get("/commodities", summary="鑾峰彇鍟嗗搧鍒楄〃")
async def get_commodities(
    db: DbSession,
    user: CurrentUserOptional,
    category_id: Optional[int] = Query(None, description="鍒嗙被ID"),
    keywords: Optional[str] = Query(None, description="Search keyword"),
    recommend: Optional[int] = Query(None, description="鍙湅鎺ㄨ崘"),
    page: int = Query(1, ge=1, description="椤电爜"),
    limit: int = Query(20, ge=1, le=100, description="姣忛〉鏁伴噺"),
):
    """鑾峰彇鍟嗗搧鍒楄〃"""
    
    query = (
        select(Commodity)
        .where(Commodity.status == 1)
        .where(Commodity.hide == 0)
        .where(Commodity.owner_id.is_(None))  # 涓荤珯鍟嗗搧
    )
    # Category filter
    if category_id:
        query = query.where(Commodity.category_id == category_id)
    # Keyword filter
    if keywords:
        query = query.where(Commodity.name.contains(keywords))
    # Recommend filter
    if recommend == 1:
        query = query.where(Commodity.recommend == 1)
    
    # 鎺掑簭
    query = query.order_by(Commodity.sort.asc(), Commodity.id.desc())
    
    # 缁熻鎬绘暟
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 鍒嗛〉
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    commodities = result.scalars().all()
    
    # Build commodity list
    items = []
    for c in commodities:
        stock = 0
        
        if not c.shared_id:
            # 缁熻鍙敤鍗″瘑鏁伴噺锛堟棤璁哄彂璐ф柟寮忥級
            card_count_result = await db.execute(
                select(func.count())
                .select_from(Card)
                .where(Card.commodity_id == c.id)
                .where(Card.status == 0)
            )
            card_stock = card_count_result.scalar() or 0
            
            # 濡傛灉鏈夊崱瀵嗭紝浣跨敤鍗″瘑鏁伴噺锛涘惁鍒欎娇鐢ㄥ晢鍝佽〃鐨?stock 瀛楁
            stock = card_stock if card_stock > 0 else c.stock
        else:
            stock = c.stock
        
        # 缁熻閿€閲?(TODO: 浼樺寲鏌ヨ)
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


@router.get("/commodities/{commodity_id}", response_model=CommodityDetailResponse, summary="鑾峰彇鍟嗗搧璇︽儏")
async def get_commodity_detail(
    commodity_id: int,
    db: DbSession,
    user: CurrentUserOptional,
):
    """鑾峰彇鍟嗗搧璇︽儏"""
    
    result = await db.execute(
        select(Commodity)
        .where(Commodity.id == commodity_id)
        .where(Commodity.status == 1)
    )
    commodity = result.scalar_one_or_none()
    
    if not commodity:
        from ...core.exceptions import NotFoundError
        raise NotFoundError("Commodity not found")
    
    # 璁＄畻搴撳瓨锛氱粺璁″彲鐢ㄥ崱瀵嗘暟閲忥紝濡傛灉娌℃湁鍗″瘑鍒欎娇鐢ㄥ晢鍝佽〃鐨?stock 瀛楁
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
    
    # 瑙ｆ瀽鍟嗗搧閰嶇疆鍙傛暟锛堢绫汇€佹壒鍙戠瓑锛?
    categories = []  # 鍟嗗搧绉嶇被 [category]
    wholesale = []   # 鎵瑰彂瑙勫垯 [wholesale]
    sku_config = []  # SKU瑙勬牸 [sku]
    category_wholesale = {}  # 绉嶇被鎵瑰彂 [category_wholesale]
    has_wholesale_from_json = False

    # 优先读取新的 wholesale_config（JSON）
    if commodity.wholesale_config:
        try:
            config_items = json_lib.loads(commodity.wholesale_config)
            if isinstance(config_items, list):
                for item in config_items:
                    if not isinstance(item, dict):
                        continue

                    quantity = int(item.get("quantity", 0))
                    if quantity <= 0:
                        continue

                    if item.get("type") == "percent" or item.get("discount_percent") is not None:
                        wholesale.append({
                            "quantity": quantity,
                            "discount_percent": float(item.get("discount_percent")),
                            "type": "percent"
                        })
                    elif item.get("price") is not None:
                        wholesale.append({
                            "quantity": quantity,
                            "price": float(item.get("price")),
                            "type": "fixed"
                        })

                has_wholesale_from_json = len(wholesale) > 0
        except (TypeError, ValueError):
            pass

    if commodity.config:
        config_text = commodity.config
        current_section = None
        for line in config_text.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):  # 璺宠繃绌鸿鍜屾敞閲?
                continue
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1].lower()
            elif "=" in line and current_section:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                try:
                    if current_section == "category":
                        # 绉嶇被=浠锋牸
                        categories.append({
                            "name": key,
                            "price": float(value)
                        })
                    elif current_section == "wholesale":
                        if has_wholesale_from_json:
                            continue
                        # 鍏ㄥ眬鎵瑰彂瑙勫垯锛堜粎褰撳晢鍝佹棤绉嶇被鏃朵娇鐢級
                        # 鏀寔涓ょ鏍煎紡锛氭暟閲?浠锋牸 鎴?鏁伴噺=鐧惧垎姣?
                        if value.endswith("%"):
                            # 鐧惧垎姣旀姌鎵?
                            wholesale.append({
                                "quantity": int(key),
                                "discount_percent": float(value[:-1]),
                                "type": "percent"
                            })
                        else:
                            # 鍥哄畾浠锋牸
                            wholesale.append({
                                "quantity": int(key),
                                "price": float(value),
                                "type": "fixed"
                            })
                    elif current_section == "sku":
                        # 瑙勬牸缁?閫夐」=鍔犱环
                        if "." in key:
                            group, option = key.split(".", 1)
                            sku_config.append({
                                "group": group,
                                "option": option,
                                "extra_price": float(value)
                            })
                    elif current_section == "category_wholesale":
                        # 绉嶇被鎵瑰彂瑙勫垯锛氱绫?鏁伴噺=浠锋牸 鎴?绉嶇被.鏁伴噺=鐧惧垎姣?
                        if "." in key:
                            cat_name, qty = key.split(".", 1)
                            if cat_name not in category_wholesale:
                                category_wholesale[cat_name] = []
                            if value.endswith("%"):
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
    # Sort wholesale rules by quantity
    wholesale.sort(key=lambda x: x["quantity"] )
    for cat_name in category_wholesale:
        category_wholesale[cat_name].sort(key=lambda x: x['quantity'])
    # Count paid orders
    sold_result = await db.execute(
        select(func.count())
        .select_from(Order)
        .where(Order.commodity_id == commodity.id)
        .where(Order.status == 1)
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
        # 瑙ｆ瀽鍚庣殑閰嶇疆鍙傛暟
        "categories": categories if categories else None,
        "wholesale": wholesale if wholesale else None,
        "sku_config": sku_config if sku_config else None,
        "category_wholesale": category_wholesale if category_wholesale else None,
    }
    return result


@router.get("/commodities/{commodity_id}/cards", summary="Get commodity draft cards")
async def get_commodity_cards(
    commodity_id: int,
    db: DbSession,
    race: Optional[str] = Query(None, description="鍟嗗搧绉嶇被"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
):
    """鑾峰彇鍙閫夌殑鍗″瘑鍒楄〃"""
    
    # Check draft purchase is enabled
    result = await db.execute(
        select(Commodity).where(Commodity.id == commodity_id)
    )
    commodity = result.scalar_one_or_none()
    
    if not commodity or commodity.draft_status != 1:
        from ...core.exceptions import ValidationError
        raise ValidationError("This commodity does not support draft selection")
    
    # 鏌ヨ鍙敤鍗″瘑
    query = (
        select(Card)
        .where(Card.commodity_id == commodity_id)
        .where(Card.status == 0)
    )
    
    if race:
        query = query.where(Card.race == race)
    
    # 缁熻鎬绘暟
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 鍒嗛〉
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


@router.get("/payments", response_model=List[PaymentMethodResponse], summary="鑾峰彇鏀粯鏂瑰紡")
async def get_payments(
    db: DbSession,
    user: CurrentUserOptional,
):
    """Get available payment methods"""
    
    query = (
        select(PaymentMethod)
        .where(PaymentMethod.status == 1)
        .where(PaymentMethod.commodity == 1)
        .order_by(PaymentMethod.sort.asc())
    )
    # Hide balance payment for guests
    if not user:
        query = query.where(PaymentMethod.handler != "#balance")
    
    result = await db.execute(query)
    payments = result.scalars().all()
    
    return payments


# ============== 璁㈠崟鐩稿叧 ==============

class CreateOrderRequest(BaseModel):
    """鍒涘缓璁㈠崟璇锋眰"""
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
    """璁㈠崟鍝嶅簲"""
    trade_no: str
    commodity_name: str
    amount: float
    quantity: int
    status: int
    delivery_status: int
    payment_url: Optional[str] = None
    created_at: Optional[str] = None


@router.post("/orders", summary="鍒涘缓璁㈠崟")
async def create_order(
    request: Request,
    data: CreateOrderRequest,
    db: DbSession,
    user: CurrentUserOptional,
):
    """鍒涘缓璁㈠崟"""
    order_service = OrderService(db)
    
    # 鑾峰彇瀹㈡埛绔疘P
    client_ip = request.client.host if request.client else None
    
    # 浠庤姹傚ご鑷姩妫€娴嬪洖璋?URL
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
    
    # OrderService.create_order() 鍐呴儴宸?commit锛屾棤闇€閲嶅
    return result


@router.get("/orders/{trade_no}", summary="鏌ヨ璁㈠崟")
async def get_order(
    trade_no: str,
    contact: str = Query(..., description="鑱旂郴鏂瑰紡"),
    db: DbSession = None,
):
    """鏍规嵁璁㈠崟鍙峰拰鑱旂郴鏂瑰紡鏌ヨ璁㈠崟"""
    result = await db.execute(
        select(Order)
        .where(Order.trade_no == trade_no)
        .where(Order.contact == contact)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise NotFoundError("Order not found or contact does not match")
    
    # 鑾峰彇鍟嗗搧鍚嶇О
    commodity_result = await db.execute(
        select(Commodity).where(Commodity.id == order.commodity_id)
    )
    commodity = commodity_result.scalar_one_or_none()
    
    response = {
        "trade_no": order.trade_no,
        "commodity_name": commodity.name if commodity else "鏈煡鍟嗗搧",
        "amount": float(order.amount),
        "quantity": order.quantity,
        "status": order.status,
        "delivery_status": order.delivery_status,
        "secret": order.secret if order.delivery_status == 1 else None,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
    }
    
    return response
