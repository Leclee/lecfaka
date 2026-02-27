from datetime import timezone
"""
管理后台 - 优惠券管理
"""

import secrets
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, or_

from ...deps import DbSession, CurrentAdmin
from ....models.coupon import Coupon
from ....models.commodity import Commodity
from ....models.category import Category
from ....core.exceptions import NotFoundError, ValidationError


router = APIRouter()


# ============== Schemas ==============

class CouponCreateRequest(BaseModel):
    """创建优惠券"""
    count: int = Field(1, ge=1, le=100, description="生成数量")
    money: float = Field(..., gt=0, description="面值")
    mode: int = Field(0, description="优惠模式 0=固定 1=按件")
    life: int = Field(1, ge=1, description="可用次数")
    commodity_id: Optional[int] = Field(None, description="限制商品ID")
    category_id: Optional[int] = Field(None, description="限制分类ID")
    expires_days: Optional[int] = Field(None, description="有效天数")
    remark: Optional[str] = Field(None, description="备注")


class CouponUpdateRequest(BaseModel):
    """更新优惠券"""
    money: Optional[float] = Field(None, gt=0, description="面值")
    mode: Optional[int] = Field(None, description="优惠模式")
    life: Optional[int] = Field(None, ge=1, description="可用次数")
    status: Optional[int] = Field(None, description="状态")
    remark: Optional[str] = Field(None, description="备注")


class BatchActionRequest(BaseModel):
    """批量操作"""
    ids: List[int] = Field(..., description="优惠券ID列表")
    action: str = Field(..., description="操作: delete/lock/unlock")


# ============== APIs ==============

@router.get("", summary="获取优惠券列表")
async def get_coupons(
    admin: CurrentAdmin,
    db: DbSession,
    status: Optional[int] = Query(None, description="状态"),
    code: Optional[str] = Query(None, description="优惠券码"),
    commodity_id: Optional[int] = Query(None, description="商品ID"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """获取优惠券列表"""
    query = select(Coupon)
    
    if status is not None:
        query = query.where(Coupon.status == status)
    if code:
        query = query.where(Coupon.code.contains(code))
    if commodity_id:
        query = query.where(Coupon.commodity_id == commodity_id)
    if category_id:
        query = query.where(Coupon.category_id == category_id)
    
    query = query.order_by(Coupon.id.desc())
    
    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    coupons = result.scalars().all()
    
    # 获取关联信息
    commodity_ids = list(set(c.commodity_id for c in coupons if c.commodity_id))
    category_ids = list(set(c.category_id for c in coupons if c.category_id))
    
    commodity_map = {}
    if commodity_ids:
        res = await db.execute(
            select(Commodity.id, Commodity.name).where(Commodity.id.in_(commodity_ids))
        )
        commodity_map = {r.id: r.name for r in res}
    
    category_map = {}
    if category_ids:
        res = await db.execute(
            select(Category.id, Category.name).where(Category.id.in_(category_ids))
        )
        category_map = {r.id: r.name for r in res}
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [
            {
                "id": c.id,
                "code": c.code,
                "money": float(c.money),
                "mode": c.mode,
                "life": c.life,
                "use_life": c.use_life,
                "status": c.status,
                "remark": c.remark,
                "commodity_id": c.commodity_id,
                "commodity_name": commodity_map.get(c.commodity_id) if c.commodity_id else None,
                "category_id": c.category_id,
                "category_name": category_map.get(c.category_id) if c.category_id else None,
                "expires_at": c.expires_at.isoformat() if c.expires_at else None,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "used_at": c.used_at.isoformat() if c.used_at else None,
            }
            for c in coupons
        ],
    }


@router.get("/stats", summary="获取优惠券统计")
async def get_coupon_stats(
    admin: CurrentAdmin,
    db: DbSession,
):
    """获取优惠券统计"""
    # 总数
    total = (await db.execute(
        select(func.count()).select_from(Coupon)
    )).scalar() or 0
    
    # 可用
    available = (await db.execute(
        select(func.count()).select_from(Coupon).where(Coupon.status == 0)
    )).scalar() or 0
    
    # 已失效
    expired = (await db.execute(
        select(func.count()).select_from(Coupon).where(Coupon.status == 1)
    )).scalar() or 0
    
    # 已锁定
    locked = (await db.execute(
        select(func.count()).select_from(Coupon).where(Coupon.status == 2)
    )).scalar() or 0
    
    return {
        "total": total,
        "available": available,
        "expired": expired,
        "locked": locked,
    }


@router.post("", summary="批量生成优惠券")
async def create_coupons(
    data: CouponCreateRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """批量生成优惠券"""
    created_codes = []
    expires_at = None
    if data.expires_days:
        expires_at = datetime.now() + timedelta(days=data.expires_days)
    
    for _ in range(data.count):
        # 生成唯一优惠券码
        code = f"COUPON{secrets.token_hex(8).upper()}"
        
        coupon = Coupon(
            code=code,
            owner_id=None,
            money=data.money,
            mode=data.mode,
            life=data.life,
            commodity_id=data.commodity_id,
            category_id=data.category_id,
            expires_at=expires_at,
            remark=data.remark,
        )
        db.add(coupon)
        created_codes.append(code)
    
    await db.flush()
    
    return {
        "count": len(created_codes),
        "codes": created_codes,
        "message": f"成功生成 {len(created_codes)} 张优惠券",
    }


@router.put("/{coupon_id}", summary="更新优惠券")
async def update_coupon(
    coupon_id: int,
    data: CouponUpdateRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """更新优惠券"""
    result = await db.execute(
        select(Coupon).where(Coupon.id == coupon_id)
    )
    coupon = result.scalar_one_or_none()
    
    if not coupon:
        raise NotFoundError("优惠券不存在")
    
    if data.money is not None:
        coupon.money = data.money
    if data.mode is not None:
        coupon.mode = data.mode
    if data.life is not None:
        coupon.life = data.life
    if data.status is not None:
        coupon.status = data.status
    if data.remark is not None:
        coupon.remark = data.remark
    
    return {"message": "更新成功"}


@router.delete("/{coupon_id}", summary="删除优惠券")
async def delete_coupon(
    coupon_id: int,
    admin: CurrentAdmin,
    db: DbSession,
):
    """删除优惠券"""
    result = await db.execute(
        select(Coupon).where(Coupon.id == coupon_id)
    )
    coupon = result.scalar_one_or_none()
    
    if not coupon:
        raise NotFoundError("优惠券不存在")
    
    await db.delete(coupon)
    return {"message": "删除成功"}


@router.post("/batch", summary="批量操作优惠券")
async def batch_action_coupons(
    data: BatchActionRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """批量操作优惠券"""
    if not data.ids:
        raise ValidationError("请选择优惠券")
    
    result = await db.execute(
        select(Coupon).where(Coupon.id.in_(data.ids))
    )
    coupons = result.scalars().all()
    
    if not coupons:
        raise NotFoundError("优惠券不存在")
    
    count = 0
    if data.action == "delete":
        for coupon in coupons:
            await db.delete(coupon)
            count += 1
    elif data.action == "lock":
        for coupon in coupons:
            if coupon.status == 0:
                coupon.status = 2
                count += 1
    elif data.action == "unlock":
        for coupon in coupons:
            if coupon.status == 2:
                coupon.status = 0
                count += 1
    else:
        raise ValidationError("无效的操作")
    
    return {"message": f"成功操作 {count} 张优惠券"}


@router.get("/export", summary="导出优惠券")
async def export_coupons(
    admin: CurrentAdmin,
    db: DbSession,
    ids: str = Query(..., description="优惠券ID列表，逗号分隔"),
):
    """导出优惠券"""
    id_list = [int(x.strip()) for x in ids.split(",") if x.strip().isdigit()]
    
    if not id_list:
        raise ValidationError("请选择优惠券")
    
    result = await db.execute(
        select(Coupon).where(Coupon.id.in_(id_list))
    )
    coupons = result.scalars().all()
    
    return {
        "items": [
            {
                "code": c.code,
                "money": float(c.money),
                "life": c.life,
                "status": c.status,
            }
            for c in coupons
        ],
    }
