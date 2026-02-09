"""
公告模型
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Announcement(Base):
    """系统公告"""
    __tablename__ = "announcements"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 公告标题
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="公告标题")
    
    # 公告内容
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="公告内容")
    
    # 公告类型 0=普通 1=重要 2=紧急
    type: Mapped[int] = mapped_column(Integer, default=0, comment="类型 0=普通 1=重要 2=紧急")
    
    # 是否置顶
    is_top: Mapped[int] = mapped_column(Integer, default=0, comment="是否置顶 0=否 1=是")
    
    # 排序
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    
    # 状态 0=隐藏 1=显示
    status: Mapped[int] = mapped_column(Integer, default=1, comment="状态 0=隐藏 1=显示")
    
    # 时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="创建时间"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, onupdate=datetime.utcnow, comment="更新时间"
    )
    
    def __repr__(self) -> str:
        return f"<Announcement {self.title}>"
