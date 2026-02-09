"""
插件管理 API
"""

import json
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....database import get_db
from ....api.deps import get_current_admin
from ....models.plugin import Plugin
from ....plugins import plugin_manager

router = APIRouter()


@router.get("")
async def get_plugins(
    type: Optional[str] = Query(None, description="插件类型"),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """获取所有已安装的插件"""
    plugins = plugin_manager.get_all_plugins()
    
    items = []
    for pi in plugins:
        # 获取数据库中的额外信息
        result = await db.execute(
            select(Plugin).where(Plugin.plugin_id == pi.meta.id)
        )
        db_plugin = result.scalar_one_or_none()
        
        if type and pi.meta.type != type:
            continue
        
        item = {
            "id": pi.meta.id,
            "name": pi.meta.name,
            "version": pi.meta.version,
            "type": pi.meta.type,
            "author": pi.meta.author,
            "description": pi.meta.description,
            "icon": pi.meta.icon,
            "is_builtin": pi.is_builtin,
            "enabled": pi.enabled,
            "license_required": pi.meta.license_required,
            "license_status": pi.license_status,
            "price": pi.meta.price,
            "config_schema": pi.meta.config_schema,
            "config": pi.config,
            "channels": getattr(pi.instance, "channels", {}) if pi.instance else {},
            "installed_at": db_plugin.installed_at.isoformat() if db_plugin and db_plugin.installed_at else None,
        }
        items.append(item)
    
    return {"items": items, "total": len(items)}


@router.post("/{plugin_id}/enable")
async def enable_plugin(
    plugin_id: str,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """启用插件"""
    try:
        success = await plugin_manager.enable_plugin(plugin_id, db)
        if success:
            return {"message": f"插件 {plugin_id} 已启用"}
        return {"message": "插件不存在"}
    except ValueError as e:
        return {"message": str(e)}


@router.post("/{plugin_id}/disable")
async def disable_plugin(
    plugin_id: str,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """禁用插件"""
    success = await plugin_manager.disable_plugin(plugin_id, db)
    if success:
        return {"message": f"插件 {plugin_id} 已禁用"}
    return {"message": "插件不存在或未启用"}


@router.put("/{plugin_id}/config")
async def update_config(
    plugin_id: str,
    config: dict,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """更新插件配置"""
    success = await plugin_manager.update_plugin_config(plugin_id, config, db)
    if success:
        return {"message": "配置已更新"}
    return {"message": "插件不存在"}


@router.get("/{plugin_id}")
async def get_plugin_detail(
    plugin_id: str,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """获取插件详情"""
    pi = plugin_manager.get_plugin(plugin_id)
    if not pi:
        return {"message": "插件不存在"}
    
    result = await db.execute(
        select(Plugin).where(Plugin.plugin_id == plugin_id)
    )
    db_plugin = result.scalar_one_or_none()
    
    return {
        "id": pi.meta.id,
        "name": pi.meta.name,
        "version": pi.meta.version,
        "type": pi.meta.type,
        "author": pi.meta.author,
        "description": pi.meta.description,
        "icon": pi.meta.icon,
        "is_builtin": pi.is_builtin,
        "enabled": pi.enabled,
        "license_required": pi.meta.license_required,
        "license_status": pi.license_status,
        "price": pi.meta.price,
        "config_schema": pi.meta.config_schema,
        "config": pi.config,
        "changelog": pi.meta.changelog,
        "dependencies": pi.meta.dependencies,
        "backend": pi.meta.backend,
        "frontend": pi.meta.frontend,
        "license_key": db_plugin.license_key if db_plugin else "",
        "installed_at": db_plugin.installed_at.isoformat() if db_plugin and db_plugin.installed_at else None,
    }
