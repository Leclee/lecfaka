"""
插件管理 API
"""

import json
import os
import zipfile
import tempfile
import shutil
from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....database import get_db
from ....api.deps import get_current_admin
from ....models.plugin import Plugin
from ....plugins import plugin_manager
from ....plugins.license_client import verify_license, get_store_plugins, download_plugin, check_updates, purchase_plugin, APP_VERSION
from ....utils.request import get_base_url

router = APIRouter()


# ============== 版本检查 + 商店代理（必须在 /{plugin_id} 路由之前注册） ==============

@router.get("/check-updates")
async def get_updates(
    admin=Depends(get_current_admin),
):
    """检查主程序和已安装插件的更新"""
    installed = {}
    for pi in plugin_manager.get_all_plugins():
        installed[pi.meta.id] = pi.meta.version
    result = await check_updates(installed)
    result["app_version"] = APP_VERSION
    return result


@router.get("/store")
async def proxy_store(
    type: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    admin=Depends(get_current_admin),
):
    """代理获取插件商店列表"""
    return await get_store_plugins(type=type, keyword=keyword, category=category)


class PurchaseBody(BaseModel):
    plugin_id: str
    buyer_email: str = ""


@router.post("/store/purchase")
async def purchase_from_store(
    body: PurchaseBody,
    request: Request,
    admin=Depends(get_current_admin),
):
    """
    购买插件 → 自动生成授权码 → 返回给前端显示。
    域名从当前请求的 Host 自动获取。
    """
    domain = get_base_url(request).replace("https://", "").replace("http://", "").split("/")[0]
    result = await purchase_plugin(
        plugin_id=body.plugin_id,
        buyer_email=body.buyer_email,
        domain=domain,
    )
    return result


@router.post("/store/install")
async def install_from_store(
    plugin_id: str = Query(...),
    license_key: str = Query(""),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """从商店一键安装插件"""
    data = await download_plugin(plugin_id, license_key)
    if not data:
        return {"message": "插件下载失败"}

    # 保存为临时 zip 并安装
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        plugins_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "plugins", "installed")
        os.makedirs(plugins_dir, exist_ok=True)

        with zipfile.ZipFile(tmp_path, "r") as z:
            z.extractall(plugins_dir)

        return {"message": f"插件 {plugin_id} 安装成功，请重启服务生效"}
    except Exception as e:
        return {"message": f"安装失败: {e}"}
    finally:
        os.unlink(tmp_path)


# ============== 插件列表 ==============

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


# ============== 安装 / 卸载 ==============

@router.post("/install")
async def install_plugin(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """上传 zip 安装插件"""
    if not file.filename or not file.filename.endswith(".zip"):
        return {"message": "请上传 .zip 格式的插件包"}

    # 保存临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 解压到 installed/ 目录
        plugins_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "plugins", "installed")
        os.makedirs(plugins_dir, exist_ok=True)

        with zipfile.ZipFile(tmp_path, "r") as z:
            # 检查 plugin.json 是否存在
            names = z.namelist()
            plugin_json_path = None
            for n in names:
                if n.endswith("plugin.json"):
                    plugin_json_path = n
                    break

            if not plugin_json_path:
                return {"message": "插件包中缺少 plugin.json"}

            # 读取 plugin.json
            meta = json.loads(z.read(plugin_json_path))
            plugin_id = meta.get("id", "")
            if not plugin_id:
                return {"message": "plugin.json 中缺少 id 字段"}

            # 解压到以 plugin_id 命名的目录
            target_dir = os.path.join(plugins_dir, plugin_id)
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)

            # 解压（处理嵌套目录）
            z.extractall(plugins_dir)
            # 如果解压出来是一个子目录，重命名
            extracted = os.path.dirname(plugin_json_path)
            if extracted and extracted != plugin_id:
                src = os.path.join(plugins_dir, extracted)
                if os.path.exists(src):
                    if os.path.exists(target_dir):
                        shutil.rmtree(target_dir)
                    os.rename(src, target_dir)

        return {"message": f"插件 {plugin_id} 安装成功，请重启服务生效", "plugin_id": plugin_id}
    finally:
        os.unlink(tmp_path)


@router.delete("/{plugin_id}")
async def uninstall_plugin(
    plugin_id: str,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """卸载插件"""
    pi = plugin_manager.get_plugin(plugin_id)
    if not pi:
        return {"message": "插件不存在"}
    if pi.is_builtin:
        return {"message": "内置插件不可卸载"}

    # 禁用
    await plugin_manager.disable_plugin(plugin_id, db)

    # 删除文件
    plugins_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "plugins", "installed")
    target_dir = os.path.join(plugins_dir, plugin_id)
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)

    # 删除数据库记录
    result = await db.execute(select(Plugin).where(Plugin.plugin_id == plugin_id))
    db_plugin = result.scalar_one_or_none()
    if db_plugin:
        await db.delete(db_plugin)

    return {"message": f"插件 {plugin_id} 已卸载，请重启服务生效"}


# ============== 授权 ==============

class LicenseRequest(BaseModel):
    license_key: str


@router.post("/{plugin_id}/license")
async def activate_license(
    plugin_id: str,
    req: LicenseRequest,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """激活授权码"""
    # 获取当前域名
    domain = "localhost"
    if request:
        domain = request.headers.get("x-forwarded-host", request.headers.get("host", "localhost"))

    # 向 store 服务器验证
    result = await verify_license(plugin_id, req.license_key, domain)

    if result.get("valid"):
        # 更新数据库
        db_result = await db.execute(select(Plugin).where(Plugin.plugin_id == plugin_id))
        db_plugin = db_result.scalar_one_or_none()
        if db_plugin:
            db_plugin.license_key = req.license_key
            db_plugin.license_status = 1
            db_plugin.license_domain = domain

        return {"message": "授权激活成功", "expires_at": result.get("expires_at")}
    else:
        return {"message": result.get("message", "授权验证失败")}


