"""
店铺/分站模型
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    String, Integer, DateTime, ForeignKey, 
    Numeric, Text, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .user import User
    from .commodity import Commodity


class Shop(Base):
    """分站/店铺"""
    __tablename__ = "shops"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 所属用户
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), unique=True, nullable=False, comment="用户ID"
    )
    
    # 店铺名称
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="店铺名称")
    
    # 域名
    subdomain: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True, comment="子域名"
    )
    domain: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True, comment="独立域名"
    )
    
    # 店铺信息
    title: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="店铺标题"
    )
    notice: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="店铺公告")
    
    # 客服信息
    service_qq: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="客服QQ"
    )
    service_url: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="客服链接"
    )
    
    # 是否显示主站商品
    master_display: Mapped[int] = mapped_column(
        Integer, default=1, comment="显示主站商品 1=是 0=否"
    )
    
    # 状态
    status: Mapped[int] = mapped_column(Integer, default=1, comment="状态 1=正常 0=关闭")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="创建时间"
    )
    
    # 关系
    user: Mapped["User"] = relationship("User", back_populates="shop")
    
    def __repr__(self) -> str:
        return f"<Shop {self.name}>"


class ShopCommodity(Base):
    """分站商品自定义"""
    __tablename__ = "shop_commodities"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 分站用户ID
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="分站用户ID"
    )
    
    # 商品ID
    commodity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("commodities.id"), nullable=False, comment="商品ID"
    )
    
    # 自定义名称
    name: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="自定义名称"
    )
    
    # 加价 (百分比)
    premium: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=0, comment="加价百分比"
    )
    
    # 状态 1=显示 0=隐藏
    status: Mapped[int] = mapped_column(Integer, default=1, comment="状态 1=显示 0=隐藏")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="创建时间"
    )
    
    # 关系
    user: Mapped["User"] = relationship("User")
    commodity: Mapped["Commodity"] = relationship("Commodity")
    
    # 索引
    __table_args__ = (
        Index("idx_shop_commodities_user_id", "user_id"),
        Index("idx_shop_commodities_commodity_id", "commodity_id"),
    )
    
    def __repr__(self) -> str:
        return f"<ShopCommodity {self.user_id}-{self.commodity_id}>"
