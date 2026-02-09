"""
授权客户端 - 与 lecfaka-store 授权服务器通信
"""

import httpx
from typing import Optional, Dict, Any

from ..config import settings


STORE_URL = getattr(settings, "store_url", None) or "https://store.lecfaka.com"


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
