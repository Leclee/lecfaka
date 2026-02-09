"""
管理后台 - 商户等级管理
"""

from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import select

from ...deps import DbSession, CurrentAdmin
from ....models.business_level import BusinessLevel
from ....core.exceptions import NotFoundError, ValidationError


router = APIRouter()


# ============== Schemas ==============

class BusinessLevelForm(BaseModel):
    """商户等级表单"""
    name: str = Field(..., max_length=50, description="等级名称")
    icon: Optional[str] = Field(None, description="图标URL")
    price: float = Field(0, description="购买价格")
    supplier_fee: float = Field(0, ge=0, le=1, description="供货商手续费比例")
    can_supply: int = Field(1, description="供货权限")
    can_substation: int = Field(1, description="分站权限")
    can_bindomain: int = Field(0, description="绑定独立域名")
    max_commodities: int = Field(100, description="最大商品数量")
    max_substations: int = Field(0, description="最大分站数量")
    description: Optional[str] = Field(None, description="描述")
    sort: int = Field(0, description="排序")
    status: int = Field(1, description="状态")


# ============== APIs ==============

@router.get("", summary="获取商户等级列表")
async def get_business_levels(
    admin: CurrentAdmin,
    db: DbSession,
):
    """获取商户等级列表"""
    result = await db.execute(
        select(BusinessLevel).order_by(BusinessLevel.sort.asc(), BusinessLevel.id.asc())
    )
    items = result.scalars().all()
    
    return {
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "icon": item.icon,
                "price": float(item.price),
                "supplier_fee": float(item.supplier_fee),
                "can_supply": item.can_supply,
                "can_substation": item.can_substation,
                "can_bindomain": item.can_bindomain,
                "max_commodities": item.max_commodities,
                "max_substations": item.max_substations,
                "description": item.description,
                "sort": item.sort,
                "status": item.status,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in items
        ],
    }


@router.post("", summary="创建商户等级")
async def create_business_level(
    data: BusinessLevelForm,
    admin: CurrentAdmin,
    db: DbSession,
):
    """创建商户等级"""
    # 检查名称是否重复
    result = await db.execute(
        select(BusinessLevel).where(BusinessLevel.name == data.name)
    )
    if result.scalar_one_or_none():
        raise ValidationError("等级名称已存在")
    
    level = BusinessLevel(
        name=data.name,
        icon=data.icon,
        price=data.price,
        supplier_fee=data.supplier_fee,
        can_supply=data.can_supply,
        can_substation=data.can_substation,
        can_bindomain=data.can_bindomain,
        max_commodities=data.max_commodities,
        max_substations=data.max_substations,
        description=data.description,
        sort=data.sort,
        status=data.status,
    )
    db.add(level)
    await db.flush()
    
    return {"id": level.id, "message": "创建成功"}


@router.put("/{level_id}", summary="更新商户等级")
async def update_business_level(
    level_id: int,
    data: BusinessLevelForm,
    admin: CurrentAdmin,
    db: DbSession,
):
    """更新商户等级"""
    result = await db.execute(
        select(BusinessLevel).where(BusinessLevel.id == level_id)
    )
    level = result.scalar_one_or_none()
    
    if not level:
        raise NotFoundError("等级不存在")
    
    # 检查名称是否重复
    result = await db.execute(
        select(BusinessLevel).where(BusinessLevel.name == data.name, BusinessLevel.id != level_id)
    )
    if result.scalar_one_or_none():
        raise ValidationError("等级名称已存在")
    
    level.name = data.name
    level.icon = data.icon
    level.price = data.price
    level.supplier_fee = data.supplier_fee
    level.can_supply = data.can_supply
    level.can_substation = data.can_substation
    level.can_bindomain = data.can_bindomain
    level.max_commodities = data.max_commodities
    level.max_substations = data.max_substations
    level.description = data.description
    level.sort = data.sort
    level.status = data.status
    
    return {"message": "更新成功"}


@router.delete("/{level_id}", summary="删除商户等级")
async def delete_business_level(
    level_id: int,
    admin: CurrentAdmin,
    db: DbSession,
):
    """删除商户等级"""
    result = await db.execute(
        select(BusinessLevel).where(BusinessLevel.id == level_id)
    )
    level = result.scalar_one_or_none()
    
    if not level:
        raise NotFoundError("等级不存在")
    
    await db.delete(level)
    return {"message": "删除成功"}
