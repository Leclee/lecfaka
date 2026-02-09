"""
插件数据模型
"""

from sqlalchemy import Column, Integer, String, Text, SmallInteger, Boolean, DateTime
from sqlalchemy.sql import func

from ..database import Base


class Plugin(Base):
    """插件安装记录"""
    __tablename__ = "plugins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plugin_id = Column(String(100), unique=True, nullable=False, index=True)  # 唯一标识
    name = Column(String(200), nullable=False)
    version = Column(String(20), nullable=False)
    type = Column(String(20), nullable=False, index=True)  # payment/theme/notify/delivery/extension
    author = Column(String(100), default="")
    description = Column(Text, default="")
    icon = Column(String(500), default="")

    # 状态
    status = Column(SmallInteger, default=0)  # 0=禁用 1=启用
    is_builtin = Column(Boolean, default=False)  # 是否内置插件

    # 授权
    license_key = Column(String(200), default="")
    license_status = Column(SmallInteger, default=0)  # 0=未授权 1=已授权 2=已过期
    license_domain = Column(String(200), default="")
    license_expires_at = Column(DateTime, nullable=True)
    last_verify_at = Column(DateTime, nullable=True)

    # 配置 (JSON)
    config = Column(Text, default="{}")

    # 时间
    installed_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
