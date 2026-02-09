"""
商品规格/变体模型

一个商品可以有多个规格，如：月卡、年卡、季卡等
每个规格有独立的价格和库存
卡密属于特定的规格
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    String, Integer, DateTime, ForeignKey, 
    Numeric, Text, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .commodity import Commodity
    from .card import Card


class CommodityVariant(Base):
    """商品规格/变体"""
    __tablename__ = "commodity_variants"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 所属商品
    commodity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("commodities.id"), nullable=False, comment="商品ID"
    )
    
    # 规格名称（如：月卡、年卡、季卡）
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="规格名称"
    )
    
    # 规格描述
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="规格描述"
    )
    
    # 价格（如果设置则覆盖商品价格）
    price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True, comment="游客价格"
    )
    user_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True, comment="会员价格"
    )
    
    # 手动发货时的库存数量（自动发货时从卡密表统计）
    stock: Mapped[int] = mapped_column(
        Integer, default=0, comment="库存数量（手动发货用）"
    )
    
    # 排序
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    
    # 状态 1=启用 0=禁用
    status: Mapped[int] = mapped_column(Integer, default=1, comment="状态")
    
    # 是否为默认规格（每个商品只能有一个默认规格）
    is_default: Mapped[int] = mapped_column(
        Integer, default=0, comment="是否默认 0=否 1=是"
    )
    
    # 时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="创建时间"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, onupdate=datetime.utcnow, comment="更新时间"
    )
    
    # 关系
    commodity: Mapped["Commodity"] = relationship("Commodity", back_populates="variants")
    cards: Mapped[List["Card"]] = relationship("Card", back_populates="variant")
    
    # 索引
    __table_args__ = (
        Index("idx_variants_commodity_id", "commodity_id"),
        Index("idx_variants_status", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<CommodityVariant {self.name}>"
