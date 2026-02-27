"""
应用配置管理
使用 pydantic-settings 管理环境变量

密钥说明：
  secret_key 和 jwt_secret_key 不再由 .env 或代码默认值管理，
  改为在应用启动时从数据库 system_configs 表自动加载。
  首次启动时自动生成强随机密钥并持久化到数据库。
  参见 main.py 中的 _init_secret_keys() 函数。
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
    
    ## 密钥（启动时由 main.py 从数据库加载，不要在 .env 中配置）
    secret_key: str = ""
    jwt_secret_key: str = ""
    
    # 数据库配置（默认值与 docker-compose.yml 一致）
    database_url: str = "postgresql+asyncpg://lecfaka:lecfaka123@localhost:5432/lecfaka"
    
    # Redis配置
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT配置
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
