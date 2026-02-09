"""
请求工具函数
从 HTTP 请求头自动检测域名、协议，构建 base URL
"""

from fastapi import Request
from typing import Optional

from ..config import settings


def get_base_url(request: Request) -> str:
    """
    从请求头自动检测并构建完整的 base URL。
    
    优先级：
    1. X-Forwarded-Proto + X-Forwarded-Host（Nginx 反向代理场景）
    2. Request 自带的 URL 信息
    3. settings.site_url 作为 fallback
    
    Returns:
        完整的 base URL，如 "https://shop.example.com"（末尾无斜杠）
    """
    scheme = (
        request.headers.get("x-forwarded-proto")
        or request.url.scheme
        or "http"
    )
    host = (
        request.headers.get("x-forwarded-host")
        or request.headers.get("host")
        or ""
    )
    
    if host:
        return f"{scheme}://{host}".rstrip("/")
    
    # fallback 到配置
    if settings.site_url:
        return settings.site_url.rstrip("/")
    
    return "http://localhost"


def get_callback_base_url(request: Request) -> str:
    """
    获取支付回调的 base URL。
    
    支付回调 URL 需要公网可达。通常与 base_url 相同，
    因为 Nginx 反向代理后，前端和后端共用同一个域名。
    
    优先级：
    1. 自动从请求头检测
    2. settings.callback_url 作为 fallback（向后兼容）
    3. settings.site_url 作为最终 fallback
    
    Returns:
        回调 base URL，如 "https://shop.example.com"（末尾无斜杠）
    """
    # 自动检测
    base = get_base_url(request)
    
    # 如果检测到的是 localhost 且配置了 callback_url，优先用配置
    # （本地开发时，支付回调需要公网地址）
    if "localhost" in base or "127.0.0.1" in base:
        if settings.callback_url:
            return settings.callback_url.rstrip("/")
    
    return base
