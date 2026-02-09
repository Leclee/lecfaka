"""
商品分类模型
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .commodity import Commodity
    from .user import User


class Category(Base):
    """商品分类"""
    __tablename__ = "categories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="分类名称")
    icon: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="分类图标")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="分类描述")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    status: Mapped[int] = mapped_column(Integer, default=1, comment="状态 1=显示 0=隐藏")
    
    # 所属用户 (NULL=主站)
    owner_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, default=None, comment="所属用户ID"
    )
    
    # 会员等级配置 (JSON)
    level_config: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="会员等级配置JSON"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="创建时间"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, onupdate=datetime.utcnow, comment="更新时间"
    )
    
    # 关系
    commodities: Mapped[List["Commodity"]] = relationship(
        "Commodity", back_populates="category"
    )
    owner: Mapped[Optional["User"]] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<Category {self.name}>"
