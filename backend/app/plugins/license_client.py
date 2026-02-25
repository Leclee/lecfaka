"""
授权客户端 - 与远程插件商店 (lecfaka-store) 通信

v2.0: 改为用户系统 + 域名验证，不再使用授权码。
v2.1: 集成支付流程（创建支付订单、查询支付状态）。
"""

import logging
import httpx
from typing import Optional, Dict, Any

from ..config import settings

logger = logging.getLogger("plugins.store_client")

## 主程序版本号（用于更新检查）
APP_VERSION = "1.0.0"

STORE_URL = getattr(settings, "store_url", None) or "https://plugins.leclee.top"

## 共享 HTTP 客户端（复用 TCP 连接，避免重复 DNS + TLS 握手）
_http_client: Optional[httpx.AsyncClient] = None
_DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0"}


def _get_client(timeout: int = 15) -> httpx.AsyncClient:
    """
    @brief 获取共享的 httpx AsyncClient 实例
    @details 使用模块级单例，复用底层连接池以提升性能
    """
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            headers=_DEFAULT_HEADERS,
            timeout=timeout,
        )
    return _http_client


def _safe_json(resp) -> Dict[str, Any]:
    """
    安全地解析 HTTP 响应的 JSON。
    如果 Store 返回非 JSON（如 500 Internal Server Error），
    不会抛出异常，而是返回包含错误信息的字典。
    """
    try:
        return resp.json()
    except Exception:
        return {"error": f"Store 返回异常 (HTTP {resp.status_code}): {resp.text[:200]}"}


async def verify_domain(plugin_id: str, domain: str) -> Dict[str, Any]:
    """
    向 store 验证域名是否有权使用某插件。

    新版本不再需要授权码，直接用 plugin_id + domain 验证。
    """
    try:
        client = _get_client()
        resp = await client.post(
            f"{STORE_URL}/api/v1/license/verify",
            json={"plugin_id": plugin_id, "domain": domain},
        )
        return _safe_json(resp)
    except Exception as e:
        return {"valid": False, "message": f"授权服务器连接失败: {e}"}


async def verify_license(plugin_id: str, license_key: str, domain: str) -> Dict[str, Any]:
    """[兼容旧版] 向 store 服务器验证授权 — 内部转为域名验证"""
    return await verify_domain(plugin_id, domain)


async def get_store_plugins(
    type: Optional[str] = None,
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    store_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    从 store 获取插件列表。

    如果提供了 store_token，会传递给 Store 以标记已购买状态。
    """
    try:
        params = {}
        if type:
            params["type"] = type
        if keyword:
            params["keyword"] = keyword
        if category:
            params["category"] = category

        headers = {}
        if store_token:
            headers["Authorization"] = f"Bearer {store_token}"

        client = _get_client()
        resp = await client.get(
            f"{STORE_URL}/api/v1/store/plugins",
            params=params,
            headers=headers,
        )
        return _safe_json(resp)
    except Exception as e:
        return {"items": [], "error": f"商店连接失败: {e}"}


async def download_plugin(plugin_id: str, license_key: str = "", store_token: str = ""):
    """
    从 store 下载插件 zip

    @param plugin_id: 插件 ID
    @param license_key: 旧版授权码（兼容）
    @param store_token: Store 用户 JWT token（优先使用）
    @return: (bytes, None) 成功时返回文件内容 | (None, error_msg) 失败时返回错误信息
    """
    try:
        ## 构建认证 header：优先使用 store_token，其次使用 license_key
        headers = {'User-Agent': 'Mozilla/5.0'}
        auth_token = store_token or license_key
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        download_url = f"{STORE_URL}/api/v1/store/download/{plugin_id}"
        logger.info(f"[download_plugin] 开始下载: {download_url}, has_token={bool(auth_token)}")

        ## 下载使用独立客户端：超时 120s，避免影响共享连接池
        async with httpx.AsyncClient(headers=_DEFAULT_HEADERS, timeout=120) as dl_client:
            resp = await dl_client.get(download_url, headers=headers)

            logger.info(f"[download_plugin] 响应状态: {resp.status_code}, content-type: {resp.headers.get('content-type', 'unknown')}, content-length: {len(resp.content)}")

            if resp.status_code == 200:
                ct = resp.headers.get("content-type", "")
                if "json" in ct:
                    ## 服务端返回了 JSON 错误（200 状态但 content-type 为 json）
                    error_detail = _safe_json(resp).get("detail", "未知错误")
                    logger.error(f"[download_plugin] 返回了 JSON 而非文件: {error_detail}")
                    return None, error_detail
                if len(resp.content) < 100:
                    logger.error(f"[download_plugin] 下载文件过小 ({len(resp.content)} bytes)，可能不是有效的 zip")
                    return None, f"下载的文件过小 ({len(resp.content)} bytes)，可能不是有效插件包"
                logger.info(f"[download_plugin] 下载成功，文件大小: {len(resp.content)} bytes")
                return resp.content, None
            ## 非 200
            try:
                detail = _safe_json(resp).get("detail", resp.text[:200])
            except Exception:
                detail = resp.text[:200]
            logger.error(f"[download_plugin] 下载失败 status={resp.status_code}, detail={detail}")
            return None, f"商店返回 {resp.status_code}: {detail}"
    except httpx.TimeoutException:
        logger.error(f"[download_plugin] 下载超时: {plugin_id}")
        return None, "下载超时，请稍后重试"
    except Exception as e:
        logger.error(f"[download_plugin] 异常: {e}")
        return None, f"网络错误: {e}"


async def check_updates(installed_plugins: Dict[str, str]) -> Dict[str, Any]:
    """向商店检查主程序和插件更新"""
    try:
        client = _get_client()
        resp = await client.post(
            f"{STORE_URL}/api/v1/store/check-updates",
            json={"plugins": installed_plugins, "app_version": APP_VERSION},
        )
        return _safe_json(resp)
    except Exception as e:
        logger.debug(f"Update check failed: {e}")
        return {"plugin_updates": [], "app_update": None}


async def purchase_plugin(
    plugin_id: str,
    store_token: str = "",
    domain: str = "",
) -> Dict[str, Any]:
    """
    通过 Store 用户 token 购买插件。

    - 免费插件：直接购买
    - 付费插件：返回 require_payment=True 提示前端走支付流程
    """
    try:
        headers = {}
        if store_token:
            headers["Authorization"] = f"Bearer {store_token}"

        client = _get_client()
        resp = await client.post(
            f"{STORE_URL}/api/v1/store/purchase",
            json={"plugin_id": plugin_id},
            headers=headers,
        )
        data = _safe_json(resp)
        if resp.status_code >= 400:
            return {"success": False, "message": data.get("detail", "购买失败")}
        return data
    except Exception as e:
        return {"success": False, "message": f"商店连接失败: {e}"}


async def create_payment_order(
    plugin_id: str,
    store_token: str,
    gateway: str = "epay",
    pay_type: str = "alipay",
) -> Dict[str, Any]:
    """
    创建支付订单（付费插件）

    调用 Store 的支付 API，返回支付链接给前端跳转。
    """
    try:
        headers = {"Authorization": f"Bearer {store_token}"}
        client = _get_client()
        resp = await client.post(
            f"{STORE_URL}/api/v1/pay/create-order",
            json={
                "plugin_id": plugin_id,
                "gateway": gateway,
                "pay_type": pay_type,
            },
            headers=headers,
        )
        data = _safe_json(resp)
        if resp.status_code >= 400:
            return {"success": False, "message": data.get("detail", "创建支付订单失败")}
        return data
    except Exception as e:
        return {"success": False, "message": f"商店连接失败: {e}"}


async def query_payment_status(order_no: str, store_token: str) -> Dict[str, Any]:
    """查询支付订单状态"""
    try:
        headers = {"Authorization": f"Bearer {store_token}"}
        client = _get_client()
        resp = await client.get(
            f"{STORE_URL}/api/v1/pay/status/{order_no}",
            headers=headers,
        )
        data = _safe_json(resp)
        if resp.status_code >= 400:
            return {"success": False, "message": data.get("detail", "查询失败")}
        return data
    except Exception as e:
        return {"success": False, "message": f"查询失败: {e}"}


async def get_payment_gateways() -> Dict[str, Any]:
    """获取可用的支付网关列表"""
    try:
        client = _get_client(timeout=10)
        resp = await client.get(f"{STORE_URL}/api/v1/pay/gateways")
        return _safe_json(resp)
    except Exception as e:
        return {"gateways": []}


async def store_login(account: str, password: str) -> Dict[str, Any]:
    """登录 Store 账号，获取 JWT token"""
    try:
        client = _get_client()
        resp = await client.post(
            f"{STORE_URL}/api/v1/auth/login",
            json={"account": account, "password": password},
        )
        data = _safe_json(resp)
        if resp.status_code >= 400:
            return {"success": False, "message": data.get("detail", "登录失败")}
        return {"success": True, **data}
    except Exception as e:
        return {"success": False, "message": f"商店连接失败: {e}"}


async def store_register(username: str, email: str, password: str) -> Dict[str, Any]:
    """注册 Store 账号"""
    try:
        client = _get_client()
        resp = await client.post(
            f"{STORE_URL}/api/v1/auth/register",
            json={"username": username, "email": email, "password": password},
        )
        data = _safe_json(resp)
        if resp.status_code >= 400:
            return {"success": False, "message": data.get("detail", "注册失败")}
        return {"success": True, **data}
    except Exception as e:
        return {"success": False, "message": f"商店连接失败: {e}"}


async def get_my_plugins(store_token: str) -> Dict[str, Any]:
    """获取用户在商店购买的插件列表"""
    try:
        client = _get_client()
        resp = await client.get(
            f"{STORE_URL}/api/v1/store/my-plugins",
            headers={"Authorization": f"Bearer {store_token}"},
        )
        return _safe_json(resp)
    except Exception as e:
        return {"items": [], "error": f"商店连接失败: {e}"}
