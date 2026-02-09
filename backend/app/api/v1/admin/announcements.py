"""
管理后台 - 公告管理
"""

from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func

from ...deps import DbSession, CurrentAdmin
from ....models.announcement import Announcement
from ....core.exceptions import NotFoundError


router = APIRouter()


# ============== Schemas ==============

class AnnouncementForm(BaseModel):
    """公告表单"""
    title: str = Field(..., max_length=200, description="标题")
    content: str = Field(..., description="内容")
    type: int = Field(0, description="类型 0=普通 1=重要 2=紧急")
    is_top: int = Field(0, description="是否置顶")
    sort: int = Field(0, description="排序")
    status: int = Field(1, description="状态")


# ============== APIs ==============

@router.get("", summary="获取公告列表")
async def get_announcements(
    admin: CurrentAdmin,
    db: DbSession,
    status: Optional[int] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """获取公告列表"""
    query = select(Announcement)
    
    if status is not None:
        query = query.where(Announcement.status == status)
    
    query = query.order_by(Announcement.is_top.desc(), Announcement.sort.desc(), Announcement.id.desc())
    
    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [
            {
                "id": item.id,
                "title": item.title,
                "content": item.content,
                "type": item.type,
                "is_top": item.is_top,
                "sort": item.sort,
                "status": item.status,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in items
        ],
    }


@router.post("", summary="创建公告")
async def create_announcement(
    data: AnnouncementForm,
    admin: CurrentAdmin,
    db: DbSession,
):
    """创建公告"""
    announcement = Announcement(
        title=data.title,
        content=data.content,
        type=data.type,
        is_top=data.is_top,
        sort=data.sort,
        status=data.status,
    )
    db.add(announcement)
    await db.flush()
    
    return {"id": announcement.id, "message": "创建成功"}


@router.put("/{announcement_id}", summary="更新公告")
async def update_announcement(
    announcement_id: int,
    data: AnnouncementForm,
    admin: CurrentAdmin,
    db: DbSession,
):
    """更新公告"""
    result = await db.execute(
        select(Announcement).where(Announcement.id == announcement_id)
    )
    announcement = result.scalar_one_or_none()
    
    if not announcement:
        raise NotFoundError("公告不存在")
    
    announcement.title = data.title
    announcement.content = data.content
    announcement.type = data.type
    announcement.is_top = data.is_top
    announcement.sort = data.sort
    announcement.status = data.status
    
    return {"message": "更新成功"}


@router.delete("/{announcement_id}", summary="删除公告")
async def delete_announcement(
    announcement_id: int,
    admin: CurrentAdmin,
    db: DbSession,
):
    """删除公告"""
    result = await db.execute(
        select(Announcement).where(Announcement.id == announcement_id)
    )
    announcement = result.scalar_one_or_none()
    
    if not announcement:
        raise NotFoundError("公告不存在")
    
    await db.delete(announcement)
    return {"message": "删除成功"}
