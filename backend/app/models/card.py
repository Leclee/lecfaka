"""
卡密模型
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
    from .commodity import Commodity
    from .variant import CommodityVariant
    from .order import Order
    from .user import User


class Card(Base):
    """卡密"""
    __tablename__ = "cards"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 所属商品
    commodity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("commodities.id"), nullable=False, comment="商品ID"
    )
    
    # 所属规格（可选，如果商品有多个规格）
    variant_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("commodity_variants.id"), nullable=True, comment="规格ID"
    )
    
    # 卡密内容
    secret: Mapped[str] = mapped_column(Text, nullable=False, comment="卡密内容")
    
    # 预选信息 (用于展示给用户选择)
    draft: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="预选展示信息"
    )
    draft_premium: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=0, comment="预选加价"
    )
    
    # 种类 (如商品有多种类别) - 保留兼容旧数据，新数据使用 variant_id
    race: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="商品种类(已废弃，使用variant_id)"
    )
    
    # SKU属性 (JSON)
    sku: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="SKU属性JSON"
    )
    
    # 备注
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")
    
    # 状态 0=待售 1=已售
    status: Mapped[int] = mapped_column(Integer, default=0, comment="状态 0=待售 1=已售")
    
    # 售出订单
    order_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("orders.id"), nullable=True, comment="售出订单ID"
    )
    
    # 所属用户 (0=主站)
    owner_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, default=None, comment="所属用户ID"
    )
    
    # 时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="创建时间"
    )
    sold_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="售出时间"
    )
    
    # 关系 - 明确指定 foreign_keys 解决双向外键问题
    commodity: Mapped["Commodity"] = relationship(
        "Commodity", back_populates="cards"
    )
    # Card -> CommodityVariant 关系
    variant: Mapped[Optional["CommodityVariant"]] = relationship(
        "CommodityVariant", back_populates="cards"
    )
    # Card.order_id -> Order.id 关系
    order: Mapped[Optional["Order"]] = relationship(
        "Order",
        foreign_keys=[order_id],
        back_populates="delivered_cards"
    )
    owner: Mapped[Optional["User"]] = relationship("User")
    
    # 索引
    __table_args__ = (
        Index("idx_cards_commodity_id", "commodity_id"),
        Index("idx_cards_variant_id", "variant_id"),
        Index("idx_cards_status", "status"),
        Index("idx_cards_race", "race"),
    )
    
    def __repr__(self) -> str:
        return f"<Card {self.id}>"
