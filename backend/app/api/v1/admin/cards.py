from datetime import timezone
"""
管理后台 - 卡密管理
"""

from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, or_

from ...deps import DbSession, CurrentAdmin
from ....models.card import Card
from ....models.commodity import Commodity
from ....models.order import Order
from ....core.exceptions import NotFoundError, ValidationError


router = APIRouter()


# ============== Schemas ==============

class ImportCardsRequest(BaseModel):
    """导入卡密请求"""
    commodity_id: int = Field(..., description="商品ID")
    cards: str = Field(..., description="卡密内容，每行一个")
    race: Optional[str] = Field(None, description="商品种类")
    draft: Optional[str] = Field(None, description="预选信息")
    draft_premium: Optional[float] = Field(0, description="预选加价")
    note: Optional[str] = Field(None, description="备注")
    delimiter: str = Field("\n", description="分隔符")


class UpdateCardRequest(BaseModel):
    """更新卡密请求"""
    secret: Optional[str] = None
    draft: Optional[str] = None
    draft_premium: Optional[float] = None
    race: Optional[str] = None
    note: Optional[str] = None


class BatchUpdateStatusRequest(BaseModel):
    """批量更新状态请求"""
    ids: List[int] = Field(..., description="卡密ID列表")
    status: int = Field(..., description="目标状态 0=未出售 1=已出售 2=已锁定")


# ============== APIs ==============

@router.get("", summary="获取卡密列表")
async def get_cards(
    admin: CurrentAdmin,
    db: DbSession,
    commodity_id: Optional[int] = None,
    status: Optional[int] = None,
    race: Optional[str] = None,
    secret: Optional[str] = Query(None, description="精确搜索卡密"),
    secret_fuzzy: Optional[str] = Query(None, description="模糊搜索卡密"),
    note: Optional[str] = Query(None, description="搜索备注"),
    owner_id: Optional[int] = Query(None, description="所属用户ID"),
    start_time: Optional[str] = Query(None, description="开始时间"),
    end_time: Optional[str] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """获取卡密列表"""
    query = select(Card)
    
    if commodity_id:
        query = query.where(Card.commodity_id == commodity_id)
    if status is not None:
        query = query.where(Card.status == status)
    if race:
        query = query.where(Card.race == race)
    if secret:
        query = query.where(Card.secret == secret)
    if secret_fuzzy:
        query = query.where(Card.secret.contains(secret_fuzzy))
    if note:
        query = query.where(Card.note.contains(note))
    if owner_id is not None:
        query = query.where(Card.owner_id == owner_id)
    if start_time:
        try:
            start_dt = datetime.strptime(start_time, "%Y-%m-%d")
            query = query.where(Card.created_at >= start_dt)
        except ValueError:
            pass
    if end_time:
        try:
            end_dt = datetime.strptime(end_time, "%Y-%m-%d")
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            query = query.where(Card.created_at <= end_dt)
        except ValueError:
            pass
    
    query = query.order_by(Card.id.desc())
    
    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    cards = result.scalars().all()
    
    # 获取商品信息
    commodity_ids = list(set(c.commodity_id for c in cards))
    if commodity_ids:
        commodities_result = await db.execute(
            select(Commodity.id, Commodity.name, Commodity.cover)
            .where(Commodity.id.in_(commodity_ids))
        )
        commodity_map = {r.id: {"name": r.name, "cover": r.cover} for r in commodities_result}
    else:
        commodity_map = {}
    
    # 获取订单号
    order_ids = [c.order_id for c in cards if c.order_id]
    order_map = {}
    if order_ids:
        orders_result = await db.execute(
            select(Order.id, Order.trade_no).where(Order.id.in_(order_ids))
        )
        order_map = {r.id: r.trade_no for r in orders_result}
    
    items = [
        {
            "id": c.id,
            "commodity_id": c.commodity_id,
            "commodity_name": commodity_map.get(c.commodity_id, {}).get("name"),
            "commodity_cover": commodity_map.get(c.commodity_id, {}).get("cover"),
            "secret": c.secret,
            "draft": c.draft,
            "draft_premium": float(c.draft_premium),
            "race": c.race,
            "sku": c.sku,
            "note": c.note,
            "status": c.status,
            "order_id": c.order_id,
            "order_trade_no": order_map.get(c.order_id) if c.order_id else None,
            "owner_id": c.owner_id,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "sold_at": c.sold_at.isoformat() if c.sold_at else None,
        }
        for c in cards
    ]
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": items,
    }


@router.post("/import", summary="批量导入卡密")
async def import_cards(
    request: ImportCardsRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """批量导入卡密"""
    
    # 检查商品是否存在
    result = await db.execute(
        select(Commodity).where(Commodity.id == request.commodity_id)
    )
    commodity = result.scalar_one_or_none()
    
    if not commodity:
        raise NotFoundError("商品不存在")
    
    # 解析卡密
    cards_text = request.cards.strip()
    if not cards_text:
        raise ValidationError("卡密内容不能为空")
    
    # 分割卡密
    card_list = cards_text.split(request.delimiter)
    card_list = [c.strip() for c in card_list if c.strip()]
    
    if not card_list:
        raise ValidationError("没有有效的卡密")
    
    # 去重
    card_list = list(dict.fromkeys(card_list))
    
    # 批量创建
    created_count = 0
    for line in card_list:
        # 支持格式：卡密----预选信息（用四个短横线分隔）
        parts = line.split('----')
        secret = parts[0].strip()
        draft = parts[1].strip() if len(parts) > 1 else request.draft
        
        if not secret:
            continue
        
        card = Card(
            commodity_id=request.commodity_id,
            secret=secret,
            race=request.race,
            draft=draft,
            draft_premium=request.draft_premium or 0,
            note=request.note,
            owner_id=commodity.owner_id,
            status=0,
        )
        db.add(card)
        created_count += 1
    
    await db.flush()
    
    # 钩子：卡密导入
    from ....plugins.sdk.hooks import hooks, Events
    await hooks.emit(Events.CARD_IMPORTED, {
        "commodity_id": request.commodity_id,
        "count": created_count,
    })
    
    return {
        "message": f"成功导入 {created_count} 条卡密",
        "count": created_count,
    }


@router.post("/batch-update-status", summary="批量更新卡密状态")
async def batch_update_cards_status(
    request: BatchUpdateStatusRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """批量更新卡密状态（锁定、解锁、标记已出售）"""
    if request.status not in [0, 1, 2]:
        raise ValidationError("无效的状态值")
    
    result = await db.execute(
        select(Card).where(Card.id.in_(request.ids))
    )
    cards = result.scalars().all()
    
    updated_count = 0
    for card in cards:
        # 已售出的卡密不能修改状态
        if card.status == 1 and request.status != 1:
            continue
        card.status = request.status
        if request.status == 1:
            card.sold_at = datetime.now(timezone.utc)
        updated_count += 1
    
    await db.flush()
    
    status_text = {0: "未出售", 1: "已出售", 2: "已锁定"}
    return {
        "message": f"成功将 {updated_count} 条卡密状态更新为 {status_text.get(request.status)}",
        "count": updated_count,
    }


@router.get("/{card_id}", summary="获取卡密详情")
async def get_card(
    card_id: int,
    admin: CurrentAdmin,
    db: DbSession,
):
    """获取卡密详情"""
    result = await db.execute(
        select(Card).where(Card.id == card_id)
    )
    card = result.scalar_one_or_none()
    
    if not card:
        raise NotFoundError("卡密不存在")
    
    return {
        "id": card.id,
        "commodity_id": card.commodity_id,
        "secret": card.secret,
        "draft": card.draft,
        "draft_premium": float(card.draft_premium),
        "race": card.race,
        "sku": card.sku,
        "note": card.note,
        "status": card.status,
        "order_id": card.order_id,
        "created_at": card.created_at.isoformat() if card.created_at else None,
        "sold_at": card.sold_at.isoformat() if card.sold_at else None,
    }


@router.put("/{card_id}", summary="更新卡密")
async def update_card(
    card_id: int,
    request: UpdateCardRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """更新卡密"""
    result = await db.execute(
        select(Card).where(Card.id == card_id)
    )
    card = result.scalar_one_or_none()
    
    if not card:
        raise NotFoundError("卡密不存在")
    
    if card.status == 1:
        raise ValidationError("已售出的卡密不能修改")
    
    if request.secret is not None:
        card.secret = request.secret
    if request.draft is not None:
        card.draft = request.draft
    if request.draft_premium is not None:
        card.draft_premium = request.draft_premium
    if request.race is not None:
        card.race = request.race
    if request.note is not None:
        card.note = request.note
    
    return {"message": "更新成功"}


@router.delete("/{card_id}", summary="删除卡密")
async def delete_card(
    card_id: int,
    admin: CurrentAdmin,
    db: DbSession,
):
    """删除卡密"""
    result = await db.execute(
        select(Card).where(Card.id == card_id)
    )
    card = result.scalar_one_or_none()
    
    if not card:
        raise NotFoundError("卡密不存在")
    
    if card.status == 1:
        raise ValidationError("已售出的卡密不能删除")
    
    await db.delete(card)
    return {"message": "删除成功"}


@router.post("/batch-delete", summary="批量删除卡密")
async def batch_delete_cards(
    ids: List[int],
    admin: CurrentAdmin,
    db: DbSession,
):
    """批量删除卡密（仅删除未售出的）"""
    result = await db.execute(
        select(Card)
        .where(Card.id.in_(ids))
        .where(Card.status == 0)
    )
    cards = result.scalars().all()
    
    deleted_count = 0
    for card in cards:
        await db.delete(card)
        deleted_count += 1
    
    return {
        "message": f"成功删除 {deleted_count} 条卡密",
        "count": deleted_count,
    }
