"""
管理后台 - 商品管理
"""

from typing import Optional, List
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func

from ...deps import DbSession, CurrentAdmin
from ....models.commodity import Commodity
from ....models.category import Category
from ....models.card import Card
from ....core.exceptions import NotFoundError, ValidationError


router = APIRouter()


# ============== Schemas ==============

class CreateCategoryRequest(BaseModel):
    """创建分类请求"""
    name: str = Field(..., min_length=1, max_length=100)
    icon: Optional[str] = None
    description: Optional[str] = None
    sort: int = 0
    status: int = 1
    level_config: Optional[str] = None


class UpdateCategoryRequest(BaseModel):
    """更新分类请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    icon: Optional[str] = None
    description: Optional[str] = None
    sort: Optional[int] = None
    status: Optional[int] = None
    level_config: Optional[str] = None


class BatchCategoryRequest(BaseModel):
    """批量操作分类请求"""
    ids: List[int] = Field(..., min_length=1)
    action: str = Field(..., description="enable / disable / delete")


class CreateCommodityRequest(BaseModel):
    """创建商品请求"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    cover: Optional[str] = None
    category_id: int
    price: float = Field(..., gt=0)
    user_price: float = Field(..., gt=0)
    factory_price: float = 0
    delivery_way: int = 0
    delivery_auto_mode: int = 0
    delivery_message: Optional[str] = None
    contact_type: int = 0
    send_email: int = 0
    password_status: int = 0
    draft_status: int = 0
    draft_premium: float = 0
    purchase_count: int = 0
    minimum: int = 0
    maximum: int = 0
    only_user: int = 0
    coupon: int = 1
    api_status: int = 0
    recommend: int = 0
    hide: int = 0
    inventory_hidden: int = 0
    seckill_status: int = 0
    level_disable: int = 0
    level_price: Optional[str] = None
    wholesale_config: Optional[str] = None
    widget: Optional[str] = None
    leave_message: Optional[str] = None
    sort: int = 0
    status: int = 1


class UpdateCommodityRequest(BaseModel):
    """更新商品请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    cover: Optional[str] = None
    category_id: Optional[int] = None
    price: Optional[float] = Field(None, gt=0)
    user_price: Optional[float] = Field(None, gt=0)
    factory_price: Optional[float] = None
    delivery_way: Optional[int] = None
    delivery_auto_mode: Optional[int] = None
    delivery_message: Optional[str] = None
    contact_type: Optional[int] = None
    send_email: Optional[int] = None
    password_status: Optional[int] = None
    draft_status: Optional[int] = None
    draft_premium: Optional[float] = None
    purchase_count: Optional[int] = None
    minimum: Optional[int] = None
    maximum: Optional[int] = None
    only_user: Optional[int] = None
    coupon: Optional[int] = None
    api_status: Optional[int] = None
    recommend: Optional[int] = None
    hide: Optional[int] = None
    inventory_hidden: Optional[int] = None
    seckill_status: Optional[int] = None
    level_disable: Optional[int] = None
    level_price: Optional[str] = None
    wholesale_config: Optional[str] = None
    widget: Optional[str] = None
    leave_message: Optional[str] = None
    sort: Optional[int] = None
    status: Optional[int] = None


# ============== Category APIs ==============

@router.get("/categories", summary="获取分类列表")
async def get_categories(
    admin: CurrentAdmin,
    db: DbSession,
    status: Optional[int] = Query(None, description="状态筛选 0=隐藏 1=显示"),
    keyword: Optional[str] = Query(None, description="分类名称搜索"),
):
    """获取所有分类（支持筛选和搜索）"""
    from ....models.user import User
    
    query = select(Category).order_by(Category.sort.asc(), Category.id.asc())
    
    if status is not None:
        query = query.where(Category.status == status)
    if keyword:
        query = query.where(Category.name.contains(keyword))
    
    result = await db.execute(query)
    categories = result.scalars().all()
    
    # 批量获取 owner 用户名
    owner_ids = [c.owner_id for c in categories if c.owner_id]
    owner_map = {}
    if owner_ids:
        owners_result = await db.execute(
            select(User.id, User.username).where(User.id.in_(owner_ids))
        )
        owner_map = {row.id: row.username for row in owners_result.all()}
    
    return {"items": [
        {
            "id": c.id,
            "name": c.name,
            "icon": c.icon,
            "description": c.description,
            "sort": c.sort,
            "status": c.status,
            "owner_id": c.owner_id,
            "owner_name": owner_map.get(c.owner_id, "主站") if c.owner_id else "主站",
            "level_config": c.level_config,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in categories
    ]}


@router.post("/categories", summary="创建分类")
async def create_category(
    request: CreateCategoryRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """创建分类"""
    category = Category(
        name=request.name,
        icon=request.icon,
        description=request.description,
        sort=request.sort,
        status=request.status,
        level_config=request.level_config,
        owner_id=None,
    )
    db.add(category)
    await db.flush()
    
    return {"id": category.id, "message": "创建成功"}


@router.put("/categories/{category_id}", summary="更新分类")
async def update_category(
    category_id: int,
    request: UpdateCategoryRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """更新分类"""
    result = await db.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise NotFoundError("分类不存在")
    
    if request.name is not None:
        category.name = request.name
    if request.icon is not None:
        category.icon = request.icon
    if request.description is not None:
        category.description = request.description
    if request.sort is not None:
        category.sort = request.sort
    if request.status is not None:
        category.status = request.status
    if request.level_config is not None:
        category.level_config = request.level_config
    
    return {"message": "更新成功"}


@router.delete("/categories/{category_id}", summary="删除分类")
async def delete_category(
    category_id: int,
    admin: CurrentAdmin,
    db: DbSession,
):
    """删除分类"""
    result = await db.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise NotFoundError("分类不存在")
    
    # 检查是否有商品
    count_result = await db.execute(
        select(func.count()).select_from(Commodity)
        .where(Commodity.category_id == category_id)
    )
    if count_result.scalar() > 0:
        raise ValidationError("该分类下还有商品，无法删除")
    
    await db.delete(category)
    return {"message": "删除成功"}


@router.post("/categories/batch", summary="批量操作分类")
async def batch_update_categories(
    request: BatchCategoryRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """批量启用/停用/删除分类"""
    result = await db.execute(
        select(Category).where(Category.id.in_(request.ids))
    )
    categories = result.scalars().all()
    
    if not categories:
        raise NotFoundError("未找到指定分类")
    
    if request.action == "enable":
        for c in categories:
            c.status = 1
        return {"message": f"已启用 {len(categories)} 个分类"}
    
    elif request.action == "disable":
        for c in categories:
            c.status = 0
        return {"message": f"已停用 {len(categories)} 个分类"}
    
    elif request.action == "delete":
        # 检查是否有商品
        for c in categories:
            count_result = await db.execute(
                select(func.count()).select_from(Commodity)
                .where(Commodity.category_id == c.id)
            )
            if count_result.scalar() > 0:
                raise ValidationError(f"分类「{c.name}」下还有商品，无法删除")
        
        for c in categories:
            await db.delete(c)
        return {"message": f"已删除 {len(categories)} 个分类"}
    
    else:
        raise ValidationError("无效的操作类型")


# ============== Commodity APIs ==============

@router.get("", summary="获取商品列表")
async def get_commodities(
    admin: CurrentAdmin,
    db: DbSession,
    category_id: Optional[int] = None,
    status: Optional[int] = None,
    keywords: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """获取商品列表"""
    query = select(Commodity).where(Commodity.owner_id.is_(None))
    
    if category_id:
        query = query.where(Commodity.category_id == category_id)
    if status is not None:
        query = query.where(Commodity.status == status)
    if keywords:
        query = query.where(Commodity.name.contains(keywords))
    
    query = query.order_by(Commodity.sort.asc(), Commodity.id.desc())
    
    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    commodities = result.scalars().all()
    
    # 预加载分类名称
    cat_result = await db.execute(select(Category))
    cat_map = {c.id: c.name for c in cat_result.scalars().all()}
    
    items = []
    for c in commodities:
        # 统计库存
        stock_result = await db.execute(
            select(func.count()).select_from(Card)
            .where(Card.commodity_id == c.id)
            .where(Card.status == 0)
        )
        stock = stock_result.scalar()
        
        items.append({
            "id": c.id,
            "name": c.name,
            "cover": c.cover,
            "category_id": c.category_id,
            "category_name": cat_map.get(c.category_id, ""),
            "price": float(c.price),
            "user_price": float(c.user_price),
            "stock": stock,
            "delivery_way": c.delivery_way,
            "status": c.status,
            "sort": c.sort,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": items,
    }


@router.get("/{commodity_id}", summary="获取商品详情")
async def get_commodity(
    commodity_id: int,
    admin: CurrentAdmin,
    db: DbSession,
):
    """获取商品详情"""
    result = await db.execute(
        select(Commodity).where(Commodity.id == commodity_id)
    )
    commodity = result.scalar_one_or_none()
    
    if not commodity:
        raise NotFoundError("商品不存在")
    
    return {
        "id": commodity.id,
        "name": commodity.name,
        "description": commodity.description,
        "cover": commodity.cover,
        "category_id": commodity.category_id,
        "price": float(commodity.price),
        "user_price": float(commodity.user_price),
        "factory_price": float(commodity.factory_price),
        "delivery_way": commodity.delivery_way,
        "delivery_auto_mode": commodity.delivery_auto_mode,
        "delivery_message": commodity.delivery_message,
        "contact_type": commodity.contact_type,
        "send_email": commodity.send_email,
        "password_status": commodity.password_status,
        "draft_status": commodity.draft_status,
        "draft_premium": float(commodity.draft_premium),
        "purchase_count": commodity.purchase_count,
        "minimum": commodity.minimum,
        "maximum": commodity.maximum,
        "only_user": commodity.only_user,
        "coupon": commodity.coupon,
        "api_status": commodity.api_status,
        "recommend": commodity.recommend,
        "hide": commodity.hide,
        "inventory_hidden": commodity.inventory_hidden,
        "seckill_status": commodity.seckill_status,
        "level_disable": commodity.level_disable,
        "level_price": commodity.level_price,
        "wholesale_config": commodity.wholesale_config,
        "widget": commodity.widget,
        "leave_message": commodity.leave_message,
        "sort": commodity.sort,
        "status": commodity.status,
        "created_at": commodity.created_at.isoformat() if commodity.created_at else None,
    }


@router.post("", summary="创建商品")
async def create_commodity(
    request: CreateCommodityRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """创建商品"""
    # 检查分类是否存在
    result = await db.execute(
        select(Category).where(Category.id == request.category_id)
    )
    if not result.scalar_one_or_none():
        raise ValidationError("分类不存在")
    
    commodity = Commodity(
        name=request.name,
        description=request.description,
        cover=request.cover,
        category_id=request.category_id,
        price=request.price,
        user_price=request.user_price,
        factory_price=request.factory_price,
        delivery_way=request.delivery_way,
        delivery_auto_mode=request.delivery_auto_mode,
        delivery_message=request.delivery_message,
        contact_type=request.contact_type,
        send_email=request.send_email,
        password_status=request.password_status,
        draft_status=request.draft_status,
        draft_premium=request.draft_premium,
        purchase_count=request.purchase_count,
        minimum=request.minimum,
        maximum=request.maximum,
        only_user=request.only_user,
        coupon=request.coupon,
        api_status=request.api_status,
        recommend=request.recommend,
        hide=request.hide,
        inventory_hidden=request.inventory_hidden,
        seckill_status=request.seckill_status,
        level_disable=request.level_disable,
        level_price=request.level_price,
        wholesale_config=request.wholesale_config,
        widget=request.widget,
        leave_message=request.leave_message,
        sort=request.sort,
        status=request.status,
        owner_id=None,
    )
    db.add(commodity)
    await db.flush()
    
    # 钩子：商品创建
    from ....plugins.sdk.hooks import hooks, Events
    await hooks.emit(Events.COMMODITY_CREATED, {"commodity": commodity})
    
    return {"id": commodity.id, "message": "创建成功"}


@router.put("/{commodity_id}", summary="更新商品")
async def update_commodity(
    commodity_id: int,
    request: UpdateCommodityRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """更新商品"""
    result = await db.execute(
        select(Commodity).where(Commodity.id == commodity_id)
    )
    commodity = result.scalar_one_or_none()
    
    if not commodity:
        raise NotFoundError("商品不存在")
    
    # 更新字段
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(commodity, field, value)
    
    return {"message": "更新成功"}


@router.delete("/{commodity_id}", summary="删除商品")
async def delete_commodity(
    commodity_id: int,
    admin: CurrentAdmin,
    db: DbSession,
):
    """删除商品"""
    from ....models.order import Order
    from sqlalchemy import delete
    
    result = await db.execute(
        select(Commodity).where(Commodity.id == commodity_id)
    )
    commodity = result.scalar_one_or_none()
    
    if not commodity:
        raise NotFoundError("商品不存在")
    
    # 检查是否有关联订单
    order_result = await db.execute(
        select(func.count()).select_from(Order).where(Order.commodity_id == commodity_id)
    )
    order_count = order_result.scalar()
    
    if order_count > 0:
        raise ValidationError(f"该商品有 {order_count} 个关联订单，无法删除。请先处理相关订单。")
    
    # 先删除关联的卡密（未售出的）
    await db.execute(
        delete(Card).where(Card.commodity_id == commodity_id).where(Card.status == 0)
    )
    
    # 检查是否有已售出的卡密
    sold_result = await db.execute(
        select(func.count()).select_from(Card).where(Card.commodity_id == commodity_id)
    )
    sold_count = sold_result.scalar()
    
    if sold_count > 0:
        raise ValidationError(f"该商品有 {sold_count} 张已售出的卡密，无法删除")
    
    await db.delete(commodity)
    return {"message": "删除成功"}
