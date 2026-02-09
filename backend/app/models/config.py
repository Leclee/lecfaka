"""
系统配置模型
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class SystemConfig(Base):
    """系统配置"""
    __tablename__ = "system_configs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 配置键
    key: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True, comment="配置键"
    )
    
    # 配置值
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="配置值")
    
    # 配置类型 (用于前端展示)
    type: Mapped[str] = mapped_column(
        String(20), default="text", comment="类型 text/number/boolean/json"
    )
    
    # 配置组
    group: Mapped[str] = mapped_column(
        String(50), default="basic", comment="配置组"
    )
    
    # 配置描述
    description: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="配置描述"
    )
    
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, onupdate=datetime.utcnow, comment="更新时间"
    )
    
    def __repr__(self) -> str:
        return f"<SystemConfig {self.key}>"
    
    @classmethod
    async def get_value(cls, session, key: str, default: str = None) -> Optional[str]:
        """获取配置值"""
        from sqlalchemy import select
        result = await session.execute(
            select(cls).where(cls.key == key)
        )
        config = result.scalar_one_or_none()
        return config.value if config else default
    
    @classmethod
    async def set_value(cls, session, key: str, value: str) -> None:
        """设置配置值"""
        from sqlalchemy import select
        result = await session.execute(
            select(cls).where(cls.key == key)
        )
        config = result.scalar_one_or_none()
        if config:
            config.value = value
        else:
            config = cls(key=key, value=value)
            session.add(config)
