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
from ....plugins.license_client import (
    verify_domain, get_store_plugins, download_plugin, check_updates,
    purchase_plugin, store_login, store_register, get_my_plugins,
    create_payment_order, query_payment_status, get_payment_gateways,
    APP_VERSION,
)
from ....utils.request import get_base_url

router = APIRouter()


# ============== Store 账号代理 API ==============

class StoreLoginBody(BaseModel):
    account: str
    password: str


class StoreRegisterBody(BaseModel):
    username: str
    email: str
    password: str


@router.post("/store/login")
async def proxy_store_login(body: StoreLoginBody, admin=Depends(get_current_admin)):
    """代理登录 Store 账号"""
    return await store_login(body.account, body.password)


@router.post("/store/register")
async def proxy_store_register(body: StoreRegisterBody, admin=Depends(get_current_admin)):
    """代理注册 Store 账号"""
    return await store_register(body.username, body.email, body.password)


# ============== 版本检查 + 商店代理 ==============

@router.get("/check-updates")
async def get_updates(admin=Depends(get_current_admin)):
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
    store_token: Optional[str] = Query(None),
    admin=Depends(get_current_admin),
):
    """代理获取插件商店列表（传入 store_token 可标记已购状态）"""
    return await get_store_plugins(type=type, keyword=keyword, category=category, store_token=store_token)


class PurchaseBody(BaseModel):
    plugin_id: str
    store_token: str = ""


@router.post("/store/purchase")
async def purchase_from_store(
    body: PurchaseBody,
    request: Request,
    admin=Depends(get_current_admin),
):
    """
    通过 Store 账号购买插件（免费插件直接购买）。

    付费插件会返回 require_payment=True，前端需要走支付流程。
    """
    return await purchase_plugin(
        plugin_id=body.plugin_id,
        store_token=body.store_token,
    )


# ============== 支付代理 API ==============

class CreatePaymentBody(BaseModel):
    plugin_id: str
    store_token: str
    gateway: str = "epay"
    pay_type: str = "alipay"


@router.post("/store/pay/create-order")
async def proxy_create_payment(body: CreatePaymentBody, admin=Depends(get_current_admin)):
    """代理创建支付订单 → 返回支付链接"""
    return await create_payment_order(
        plugin_id=body.plugin_id,
        store_token=body.store_token,
        gateway=body.gateway,
        pay_type=body.pay_type,
    )


@router.get("/store/pay/status")
async def proxy_payment_status(
    order_no: str = Query(...),
    store_token: str = Query(""),
    admin=Depends(get_current_admin),
):
    """代理查询支付订单状态"""
    if not store_token:
        return {"success": False, "message": "请先登录 Store 账号"}
    return await query_payment_status(order_no, store_token)


@router.get("/store/pay/gateways")
async def proxy_payment_gateways(admin=Depends(get_current_admin)):
    """代理获取可用支付网关列表"""
    return await get_payment_gateways()


@router.get("/store/my-plugins")
async def proxy_my_plugins(
    store_token: str = Query(""),
    admin=Depends(get_current_admin),
):
    """代理获取用户在商店已购买的插件"""
    if not store_token:
        return {"items": [], "message": "请先登录 Store 账号"}
    return await get_my_plugins(store_token)


@router.post("/store/install")
async def install_from_store(
    plugin_id: str = Query(...),
    license_key: str = Query(""),
    store_token: str = Query(""),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """从商店一键安装插件"""
    import logging
    logger = logging.getLogger("plugins.store_install")

    logger.info(f"[store_install] 开始安装插件: {plugin_id}, has_store_token={bool(store_token)}, has_license_key={bool(license_key)}")

    ## 1. 从商店下载插件 zip（优先使用 store_token 认证）
    data, error = await download_plugin(plugin_id, license_key, store_token=store_token)
    if not data:
        logger.error(f"[store_install] 下载失败: {error}")
        return {"message": f"插件下载失败: {error or '未知原因'}", "success": False}

    logger.info(f"[store_install] 下载完成，大小: {len(data)} bytes")

    ## 2. 写入临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        ## 3. 确定安装目录
        plugins_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "plugins", "installed")
        os.makedirs(plugins_dir, exist_ok=True)
        logger.info(f"[store_install] 安装目录: {plugins_dir}")

        ## 4. 验证 zip 并解析 plugin.json
        with zipfile.ZipFile(tmp_path, "r") as z:
            names = z.namelist()
            logger.info(f"[store_install] zip 内文件列表: {names[:20]}")

            ## 查找 plugin.json
            plugin_json_path = None
            for n in names:
                if n.endswith("plugin.json"):
                    plugin_json_path = n
                    break

            if not plugin_json_path:
                logger.error("[store_install] zip 中没有 plugin.json")
                return {"message": "插件包中缺少 plugin.json，请联系插件开发者", "success": False}

            ## 读取 plugin.json 获取实际 plugin_id
            meta = json.loads(z.read(plugin_json_path))
            actual_plugin_id = meta.get("id", "")
            if not actual_plugin_id:
                logger.error("[store_install] plugin.json 中缺少 id 字段")
                return {"message": "plugin.json 中缺少 id 字段", "success": False}

            logger.info(f"[store_install] 解析到 plugin_id={actual_plugin_id}, version={meta.get('version', '?')}")

            ## 5. 清理已有目录（覆盖安装）
            target_dir = os.path.join(plugins_dir, actual_plugin_id)
            if os.path.exists(target_dir):
                logger.info(f"[store_install] 已存在同名目录，先删除: {target_dir}")
                shutil.rmtree(target_dir)

            ## 6. 解压
            z.extractall(plugins_dir)

            ## 7. 处理解压后目录名不一致的情况
            extracted = os.path.dirname(plugin_json_path)
            if extracted and extracted != actual_plugin_id:
                src = os.path.join(plugins_dir, extracted)
                if os.path.exists(src):
                    if os.path.exists(target_dir):
                        shutil.rmtree(target_dir)
                    os.rename(src, target_dir)
                    logger.info(f"[store_install] 重命名目录: {extracted} -> {actual_plugin_id}")

        ## 8. 验证安装结果
        final_plugin_json = os.path.join(plugins_dir, actual_plugin_id, "plugin.json")
        if not os.path.exists(final_plugin_json):
            ## 尝试查找一级子目录
            for item in os.listdir(plugins_dir):
                candidate = os.path.join(plugins_dir, item, "plugin.json")
                if os.path.exists(candidate):
                    logger.info(f"[store_install] 在子目录找到 plugin.json: {item}")
                    break
            else:
                logger.error(f"[store_install] 安装后找不到 plugin.json: {final_plugin_json}")
                return {"message": f"安装异常：解压后找不到 plugin.json", "success": False}

        logger.info(f"[store_install] 插件 {actual_plugin_id} 安装成功!")
        return {"message": f"插件 {actual_plugin_id} 安装成功，请重启服务生效", "success": True, "plugin_id": actual_plugin_id}
    except zipfile.BadZipFile:
        logger.error("[store_install] 下载的文件不是有效的 zip 格式")
        return {"message": "下载的文件不是有效的 zip 格式，请联系管理员", "success": False}
    except Exception as e:
        logger.error(f"[store_install] 安装异常: {e}", exc_info=True)
        return {"message": f"安装失败: {e}", "success": False}
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


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
    
    details = {
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

    if pi.meta.type == "theme" and pi.instance and hasattr(pi.instance, 'all_themes'):
        themes = pi.instance.all_themes
        details["theme_variations"] = [{"id": tid, "name": t.name} for tid, t in themes.items()]
        details["active_theme_id"] = pi.instance._active_theme_id if hasattr(pi.instance, '_active_theme_id') else "default"

    return details


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

    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        plugins_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "plugins", "installed")
        os.makedirs(plugins_dir, exist_ok=True)

        with zipfile.ZipFile(tmp_path, "r") as z:
            names = z.namelist()
            plugin_json_path = None
            for n in names:
                if n.endswith("plugin.json"):
                    plugin_json_path = n
                    break

            if not plugin_json_path:
                return {"message": "插件包中缺少 plugin.json"}

            meta = json.loads(z.read(plugin_json_path))
            plugin_id = meta.get("id", "")
            if not plugin_id:
                return {"message": "plugin.json 中缺少 id 字段"}

            target_dir = os.path.join(plugins_dir, plugin_id)
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)

            z.extractall(plugins_dir)
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

    await plugin_manager.disable_plugin(plugin_id, db)

    plugins_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "plugins", "installed")
    target_dir = os.path.join(plugins_dir, plugin_id)
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)

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
    """激活授权（兼容旧版授权码，新版通过域名验证）"""
    domain = "localhost"
    if request:
        domain = request.headers.get("x-forwarded-host", request.headers.get("host", "localhost"))

    result = await verify_domain(plugin_id, domain)

    if result.get("valid"):
        db_result = await db.execute(select(Plugin).where(Plugin.plugin_id == plugin_id))
        db_plugin = db_result.scalar_one_or_none()
        if db_plugin:
            db_plugin.license_key = req.license_key
            db_plugin.license_status = 1
            db_plugin.license_domain = domain

        return {"message": "授权激活成功", "expires_at": result.get("expires_at")}
    else:
        return {"message": result.get("message", result.get("error", "授权验证失败"))}
