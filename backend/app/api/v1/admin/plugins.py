"""
插件管理 API
"""

import json
import logging
import os
from pathlib import Path
import zipfile
import tempfile
import shutil
from typing import Optional, Dict, Any
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
logger = logging.getLogger("plugins.install")

## 解压时需要忽略的文件/目录
_IGNORED_NAMES = {"__pycache__", ".DS_Store", "Thumbs.db", ".git"}


# ============== 通用工具函数 ==============

def _get_plugins_dir() -> str:
    """
    @brief 获取插件安装目录的绝对路径
    @return plugins/installed 的绝对路径
    """
    ## backend/app/api/v1/admin/plugins.py → parents[4] = backend/
    backend_root = Path(__file__).resolve().parents[4]
    plugins_dir = backend_root / "plugins" / "installed"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    return str(plugins_dir)


def _find_plugin_json_in_zip(names: list) -> Optional[str]:
    """
    @brief 在 zip 文件名列表中查找 plugin.json
    @param names zip 内所有条目名称
    @return plugin.json 的完整条目路径，未找到返回 None

    优先返回层级最浅的 plugin.json
    """
    candidates = []
    for n in names:
        if n.endswith("/"):
            continue
        parts = n.replace("\\", "/").split("/")
        if parts[-1] == "plugin.json":
            candidates.append((len(parts), n))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def _locate_plugin_root(extract_tmp: str, plugin_json_entry: str) -> Optional[str]:
    """
    @brief 根据 zip 内 plugin.json 的路径，定位解压后的插件根目录
    @param extract_tmp       解压临时目录
    @param plugin_json_entry zip 内 plugin.json 的路径
    @return 插件根目录的绝对路径，失败返回 None
    """
    local_rel = plugin_json_entry.replace("/", os.sep)
    prefix_dir = os.path.dirname(local_rel)

    if prefix_dir:
        source_dir = os.path.join(extract_tmp, prefix_dir)
    else:
        source_dir = extract_tmp

    if os.path.exists(os.path.join(source_dir, "plugin.json")):
        return source_dir

    ## 兜底: 递归搜索
    logger.warning(f"[locate] 按路径未找到, 递归搜索: {extract_tmp}")
    for root, dirs, files in os.walk(extract_tmp):
        dirs[:] = [d for d in dirs if d not in _IGNORED_NAMES]
        if "plugin.json" in files:
            logger.info(f"[locate] 搜索找到: {root}")
            return root

    return None


def _extract_plugin_zip(zip_path: str, plugins_dir: str) -> Dict[str, Any]:
    """
    @brief 从 zip 文件解压并安装插件到 plugins_dir/{plugin_id}/
    @param zip_path    zip 文件的绝对路径
    @param plugins_dir 插件安装根目录 (plugins/installed)
    @return dict 包含 success, message, plugin_id 字段

    兼容以下 zip 内部结构:
      1. 扁平结构:   plugin.json 直接在 zip 根目录
      2. 单目录包裹: some_dir/plugin.json
      3. 多层嵌套:   a/b/plugin.json

    流程: 解压到临时目录 -> 搜索 plugin.json -> copytree 到目标目录
    """
    extract_tmp = None
    try:
        ## 1. 打开并验证 zip
        with zipfile.ZipFile(zip_path, "r") as z:
            names = z.namelist()
            logger.info(f"[extract] zip 文件列表 ({len(names)} 项): {names[:20]}")

            ## 2. 在 zip 内查找 plugin.json
            plugin_json_entry = _find_plugin_json_in_zip(names)
            if not plugin_json_entry:
                return {"message": "插件包中缺少 plugin.json", "success": False}

            ## 3. 读取 plugin.json 元数据
            raw = z.read(plugin_json_entry)
            try:
                meta = json.loads(raw)
            except json.JSONDecodeError as e:
                return {"message": f"plugin.json 格式错误: {e}", "success": False}

            plugin_id = meta.get("id", "").strip()
            if not plugin_id:
                return {"message": "plugin.json 中缺少 id 字段", "success": False}

            version = meta.get("version", "unknown")
            logger.info(f"[extract] plugin_id={plugin_id}, version={version}, entry={plugin_json_entry}")

            ## 4. 解压到临时目录
            extract_tmp = tempfile.mkdtemp(prefix="plugin_extract_")
            z.extractall(extract_tmp)

        ## 5. 定位 plugin.json 所在的目录
        source_dir = _locate_plugin_root(extract_tmp, plugin_json_entry)
        if not source_dir:
            return {"message": "解压后无法定位 plugin.json", "success": False}

        logger.info(f"[extract] 插件根目录: {source_dir}, 内容: {os.listdir(source_dir)}")

        ## 6. 覆盖安装到最终目录
        target_dir = os.path.join(plugins_dir, plugin_id)
        if os.path.exists(target_dir):
            logger.info(f"[extract] 覆盖已有目录: {target_dir}")
            shutil.rmtree(target_dir)

        shutil.copytree(
            source_dir,
            target_dir,
            ignore=shutil.ignore_patterns(*_IGNORED_NAMES),
        )

        ## 7. 最终验证
        if not os.path.exists(os.path.join(target_dir, "plugin.json")):
            logger.error(f"[extract] 最终验证失败: {target_dir}")
            return {"message": "安装异常：最终目录中找不到 plugin.json", "success": False}

        installed_files = os.listdir(target_dir)
        logger.info(f"[extract] {plugin_id} v{version} 安装成功, 文件: {installed_files}")
        return {
            "message": f"插件 {plugin_id} 安装成功，请重启服务生效",
            "success": True,
            "plugin_id": plugin_id,
        }

    except zipfile.BadZipFile:
        return {"message": "文件不是有效的 zip 格式", "success": False}
    except Exception as e:
        logger.error(f"[extract] 安装异常: {e}", exc_info=True)
        return {"message": f"安装失败: {e}", "success": False}
    finally:
        if extract_tmp and os.path.exists(extract_tmp):
            shutil.rmtree(extract_tmp, ignore_errors=True)


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
    """代理创建支付订单 -> 返回支付链接"""
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


# ============== 商店安装 ==============

@router.post("/store/install")
async def install_from_store(
    plugin_id: str = Query(...),
    license_key: str = Query(""),
    store_token: str = Query(""),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """从商店下载并安装插件"""
    logger.info(f"[store_install] 开始: plugin_id={plugin_id}, has_token={bool(store_token)}")

    ## 1. 下载
    data, error = await download_plugin(plugin_id, license_key, store_token=store_token)
    if not data:
        logger.error(f"[store_install] 下载失败: {error}")
        return {"message": f"插件下载失败: {error or '未知原因'}", "success": False}

    logger.info(f"[store_install] 下载完成, {len(data)} bytes")

    ## 2. 写临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    ## 3. 解压安装（调用通用函数）
    try:
        return _extract_plugin_zip(tmp_path, _get_plugins_dir())
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
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


# ============== 手动上传安装 / 卸载 ==============

@router.post("/install")
async def install_plugin(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """上传 zip 安装插件"""
    if not file.filename or not file.filename.endswith(".zip"):
        return {"message": "请上传 .zip 格式的插件包", "success": False}

    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        return _extract_plugin_zip(tmp_path, _get_plugins_dir())
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


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

    target_dir = os.path.join(_get_plugins_dir(), plugin_id)
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
