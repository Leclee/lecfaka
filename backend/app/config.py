"""
应用配置管理
使用 pydantic-settings 管理环境变量
"""

from functools import lru_cache
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # 应用配置
    app_name: str = "LecFaka"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-this-in-production"
    
    # 数据库配置（默认值与 docker-compose.yml 一致）
    database_url: str = "postgresql+asyncpg://lecfaka:lecfaka123@localhost:5432/lecfaka"
    
    # Redis配置
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT配置
    jwt_secret_key: str = "your-jwt-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # CORS 白名单（逗号分隔，如: https://shop.leclee.top,https://admin.leclee.top）
    cors_origins: str = "*"
    
    # 插件商店服务器地址
    store_url: str = "https://plugins.leclee.top"
    
    # 站点配置（可选，留空则自动从请求头检测）
    site_url: Optional[str] = None
    callback_url: Optional[str] = None
    
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """解析 CORS 白名单为列表"""
        if self.cors_origins == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()

## 启动时检查弱密钥并警告（不再自动替换，避免破坏现有数据）
_WEAK_KEYS = {"change-this-in-production", "your-jwt-secret-key", ""}
if settings.secret_key in _WEAK_KEYS or settings.jwt_secret_key in _WEAK_KEYS:
    import logging as _log
    _log.warning(
        "[config] ⚠️ 检测到弱密钥！请在 .env 中设置强随机值：\n"
        "  SECRET_KEY=<随机字符串>\n"
        "  JWT_SECRET_KEY=<随机字符串>\n"
        "  可用命令生成: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    )
