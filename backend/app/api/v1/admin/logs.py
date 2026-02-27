"""
管理后台 - 操作日志
"""

from typing import Optional
from fastapi import APIRouter, Query
from sqlalchemy import select, func

from ...deps import DbSession, CurrentAdmin
from ....models.log import OperationLog
from ....models.user import User


router = APIRouter()


# ============== APIs ==============

@router.get("", summary="获取操作日志列表")
async def get_logs(
    admin: CurrentAdmin,
    db: DbSession,
    user_id: Optional[int] = Query(None, description="用户ID"),
    email: Optional[str] = Query(None, description="邮箱"),
    risk_level: Optional[int] = Query(None, description="风险等级"),
    action: Optional[str] = Query(None, description="操作"),
    ip: Optional[str] = Query(None, description="IP地址"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """获取操作日志列表"""
    query = select(OperationLog)
    
    if user_id:
        query = query.where(OperationLog.user_id == user_id)
    if email:
        query = query.where(OperationLog.email.contains(email))
    if risk_level is not None:
        query = query.where(OperationLog.risk_level == risk_level)
    if action:
        query = query.where(OperationLog.action.contains(action))
    if ip:
        query = query.where(OperationLog.ip.contains(ip))
    
    query = query.order_by(OperationLog.created_at.desc())
    
    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "email": log.email,
                "action": log.action,
                "ip": log.ip,
                "user_agent": log.user_agent,
                "risk_level": log.risk_level,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
    }


@router.get("/stats", summary="获取日志统计")
async def get_log_stats(
    admin: CurrentAdmin,
    db: DbSession,
):
    """获取日志统计"""
    from datetime import datetime, timedelta
    
    today , timezone= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 总数
    total = (await db.execute(
        select(func.count()).select_from(OperationLog)
    )).scalar() or 0
    
    # 今日
    today_count = (await db.execute(
        select(func.count()).select_from(OperationLog)
        .where(OperationLog.created_at >= today)
    )).scalar() or 0
    
    # 高风险
    high_risk = (await db.execute(
        select(func.count()).select_from(OperationLog)
        .where(OperationLog.risk_level == 1)
    )).scalar() or 0
    
    return {
        "total": total,
        "today": today_count,
        "high_risk": high_risk,
    }
