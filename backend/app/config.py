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
    secret_key: str = ""  ## 留空 → 首次启动自动生成
    
    # 数据库配置（默认值与 docker-compose.yml 一致）
    database_url: str = "postgresql+asyncpg://lecfaka:lecfaka123@localhost:5432/lecfaka"
    
    # Redis配置
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT配置
    jwt_secret_key: str = ""  ## 留空 → 首次启动自动生成
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

## 密钥自动生成：为空时生成随机密钥并写入 .env
## 仅在首次安装（.env 中未配置密钥）时触发
## 已有部署请确保 .env 中已包含 SECRET_KEY 和 JWT_SECRET_KEY
_keys_to_generate = []
if not settings.secret_key:
    _keys_to_generate.append("SECRET_KEY")
if not settings.jwt_secret_key:
    _keys_to_generate.append("JWT_SECRET_KEY")

if _keys_to_generate:
    import secrets as _secrets
    import os as _os
    import logging as _log
    
    _env_path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), ".env")
    _lines_to_append = []
    
    for _key_name in _keys_to_generate:
        _generated = _secrets.token_urlsafe(32)
        setattr(settings, _key_name.lower(), _generated)
        _lines_to_append.append(f"{_key_name}={_generated}")
    
    try:
        with open(_env_path, "a", encoding="utf-8") as _f:
            _f.write("\n## 自动生成的签名密钥（请勿删除）\n")
            for _line in _lines_to_append:
                _f.write(f"{_line}\n")
        _log.info(f"[config] 密钥已自动生成并写入 {_env_path}")
    except Exception as _e:
        _log.warning(f"[config] 密钥已自动生成但无法写入 .env: {_e}（本次运行有效，重启后会重新生成）")
