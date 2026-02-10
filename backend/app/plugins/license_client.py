"""
授权客户端 - 与远程插件商店 (lecfaka-store) 通信

商店是独立部署的中心化服务，所有发卡网实例通过 STORE_URL 远程连接。
"""

import logging
import httpx
from typing import Optional, Dict, Any

from ..config import settings

logger = logging.getLogger("plugins.store_client")

# 主程序版本号（用于更新检查）
APP_VERSION = "1.0.0"

STORE_URL = getattr(settings, "store_url", None) or "https://plugins.leclee.top"


async def verify_license(plugin_id: str, license_key: str, domain: str) -> Dict[str, Any]:
    """向 store 服务器验证授权"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{STORE_URL}/api/v1/license/verify",
                json={
                    "plugin_id": plugin_id,
                    "license_key": license_key,
                    "domain": domain,
                },
            )
            return resp.json()
    except Exception as e:
        return {"valid": False, "message": f"授权服务器连接失败: {e}"}


async def get_store_plugins(
    type: Optional[str] = None,
    keyword: Optional[str] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """从 store 获取插件列表"""
    try:
        params = {}
        if type:
            params["type"] = type
        if keyword:
            params["keyword"] = keyword
        if category:
            params["category"] = category

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{STORE_URL}/api/v1/store/plugins",
                params=params,
            )
            return resp.json()
    except Exception as e:
        return {"items": [], "error": f"商店连接失败: {e}"}


async def download_plugin(plugin_id: str, license_key: str = "") -> Optional[bytes]:
    """从 store 下载插件 zip"""
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(
                f"{STORE_URL}/api/v1/store/download/{plugin_id}",
                headers={"Authorization": f"Bearer {license_key}"} if license_key else {},
            )
            if resp.status_code == 200:
                return resp.content
            return None
    except Exception:
        return None


async def check_updates(installed_plugins: Dict[str, str]) -> Dict[str, Any]:
    """
    向商店检查主程序和插件更新。

    Args:
        installed_plugins: {"plugin_id": "version", ...}

    Returns:
        {
            "plugin_updates": [{"id", "name", "current_version", "latest_version"}, ...],
            "app_update": {"latest_version", "current_version", "message"} or None,
        }
    """
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{STORE_URL}/api/v1/store/check-updates",
                json={
                    "plugins": installed_plugins,
                    "app_version": APP_VERSION,
                },
            )
            data = resp.json()
            updates = data.get("plugin_updates", [])
            app_update = data.get("app_update")
            if updates:
                logger.info(f"Available plugin updates: {[u['id'] for u in updates]}")
            if app_update:
                logger.info(f"App update available: {app_update['latest_version']}")
            return data
    except Exception as e:
        logger.debug(f"Update check failed: {e}")
        return {"plugin_updates": [], "app_update": None}


async def rebind_license(license_key: str, new_domain: str) -> Dict[str, Any]:
    """向 store 服务器请求换绑域名"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{STORE_URL}/api/v1/license/rebind",
                json={
                    "license_key": license_key,
                    "new_domain": new_domain,
                },
            )
            return resp.json()
    except Exception as e:
        return {"success": False, "message": f"授权服务器连接失败: {e}"}


async def get_license_info(license_key: str) -> Dict[str, Any]:
    """向 store 查询授权码的绑定状态"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{STORE_URL}/api/v1/license/info",
                json={"license_key": license_key},
            )
            return resp.json()
    except Exception as e:
        return {"found": False, "message": f"授权服务器连接失败: {e}"}
