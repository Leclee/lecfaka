"""
管理后台 - 会员等级管理
"""

from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import select, func

from ...deps import DbSession, CurrentAdmin
from ....models.user import UserGroup
from ....core.exceptions import NotFoundError, ValidationError


router = APIRouter()


# ============== Schemas ==============

class UserGroupForm(BaseModel):
    """会员等级表单"""
    name: str = Field(..., max_length=50, description="等级名称")
    icon: Optional[str] = Field(None, description="图标URL")
    color: Optional[str] = Field(None, description="颜色代码")
    min_recharge: float = Field(0, description="最低充值金额")
    discount: float = Field(0, ge=0, le=1, description="折扣比例")
    sort: int = Field(0, description="排序")
    status: int = Field(1, description="状态")


# ============== APIs ==============

@router.get("", summary="获取会员等级列表")
async def get_user_groups(
    admin: CurrentAdmin,
    db: DbSession,
):
    """获取会员等级列表"""
    result = await db.execute(
        select(UserGroup).order_by(UserGroup.sort.asc(), UserGroup.id.asc())
    )
    items = result.scalars().all()
    
    return {
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "icon": item.icon,
                "color": item.color,
                "min_recharge": float(item.min_recharge),
                "discount": float(item.discount),
                "sort": item.sort,
                "status": item.status,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in items
        ],
    }


@router.post("", summary="创建会员等级")
async def create_user_group(
    data: UserGroupForm,
    admin: CurrentAdmin,
    db: DbSession,
):
    """创建会员等级"""
    # 检查名称是否重复
    result = await db.execute(
        select(UserGroup).where(UserGroup.name == data.name)
    )
    if result.scalar_one_or_none():
        raise ValidationError("等级名称已存在")
    
    group = UserGroup(
        name=data.name,
        icon=data.icon,
        color=data.color,
        min_recharge=data.min_recharge,
        discount=data.discount,
        sort=data.sort,
        status=data.status,
    )
    db.add(group)
    await db.flush()
    
    return {"id": group.id, "message": "创建成功"}


@router.put("/{group_id}", summary="更新会员等级")
async def update_user_group(
    group_id: int,
    data: UserGroupForm,
    admin: CurrentAdmin,
    db: DbSession,
):
    """更新会员等级"""
    result = await db.execute(
        select(UserGroup).where(UserGroup.id == group_id)
    )
    group = result.scalar_one_or_none()
    
    if not group:
        raise NotFoundError("等级不存在")
    
    # 检查名称是否重复
    result = await db.execute(
        select(UserGroup).where(UserGroup.name == data.name, UserGroup.id != group_id)
    )
    if result.scalar_one_or_none():
        raise ValidationError("等级名称已存在")
    
    group.name = data.name
    group.icon = data.icon
    group.color = data.color
    group.min_recharge = data.min_recharge
    group.discount = data.discount
    group.sort = data.sort
    group.status = data.status
    
    return {"message": "更新成功"}


@router.delete("/{group_id}", summary="删除会员等级")
async def delete_user_group(
    group_id: int,
    admin: CurrentAdmin,
    db: DbSession,
):
    """删除会员等级"""
    from ....models.user import User
    
    result = await db.execute(
        select(UserGroup).where(UserGroup.id == group_id)
    )
    group = result.scalar_one_or_none()
    
    if not group:
        raise NotFoundError("等级不存在")
    
    # 检查是否有用户使用此等级
    user_count = await db.execute(
        select(func.count()).select_from(User).where(User.group_id == group_id)
    )
    count = user_count.scalar()
    
    if count and count > 0:
        raise ValidationError(f"有 {count} 个用户使用此等级，无法删除")
    
    await db.delete(group)
    return {"message": "删除成功"}
