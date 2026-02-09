"""
应用配置管理
使用 pydantic-settings 管理环境变量
"""

from functools import lru_cache
from typing import Optional
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
    
    # 数据库配置
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/lecfaka"
    
    # Redis配置
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT配置
    jwt_secret_key: str = "your-jwt-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # 默认管理员（首次启动自动创建）
    admin_username: str = "admin"
    admin_password: str = "admin123"
    admin_email: str = "admin@lecfaka.com"
    
    # 插件商店服务器地址
    store_url: str = "https://store.lecfaka.com"
    
    # 站点配置（可选，留空则自动从请求头检测）
    # 仅在自动检测不可用时作为 fallback，如本地开发环境
    site_url: Optional[str] = None
    callback_url: Optional[str] = None
    
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
