"""
订单模型
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
    from .user import User
    from .commodity import Commodity
    from .payment import PaymentMethod
    from .card import Card
    from .coupon import Coupon


class Order(Base):
    """订单"""
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 订单号 (18位)
    trade_no: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True, comment="订单号"
    )
    
    # 购买用户 (游客为None)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, default=None, comment="购买用户ID"
    )
    
    # 商品
    commodity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("commodities.id"), nullable=False, comment="商品ID"
    )
    
    # 支付方式
    payment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("payment_methods.id"), nullable=True, comment="支付方式ID"
    )
    
    # 金额
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment="订单金额"
    )
    cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=0, comment="成本/手续费"
    )
    pay_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=0, comment="支付手续费"
    )
    
    # 购买数量
    quantity: Mapped[int] = mapped_column(Integer, default=1, comment="购买数量")
    
    # 种类
    race: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="商品种类"
    )
    
    # SKU (JSON)
    sku: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="SKU属性JSON"
    )
    
    # 联系方式
    contact: Mapped[str] = mapped_column(String(200), nullable=False, comment="联系方式")
    
    # 查单密码
    password: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="查单密码"
    )
    
    # 卡密
    secret: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="发放的卡密")
    
    # 预选卡密ID
    card_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("cards.id", use_alter=True), nullable=True, comment="预选卡密ID"
    )
    
    # 自定义控件数据 (JSON)
    widget: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="自定义控件数据JSON"
    )
    
    # 优惠券
    coupon_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("coupons.id"), nullable=True, comment="优惠券ID"
    )
    
    # 订单状态 0=待支付 1=已支付 2=已取消 3=已退款
    status: Mapped[int] = mapped_column(Integer, default=0, comment="订单状态")
    
    # 发货状态 0=未发货 1=已发货
    delivery_status: Mapped[int] = mapped_column(
        Integer, default=0, comment="发货状态 0=未发货 1=已发货"
    )
    
    # 推广/分销
    from_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, comment="推广人ID"
    )
    rebate: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=0, comment="返佣金额"
    )
    premium: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=0, comment="分站加价"
    )
    
    # 分站订单
    substation_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, comment="分站用户ID"
    )
    
    # 商品所属用户 (便于商户查询)
    owner_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, default=None, comment="商品所属用户ID"
    )
    
    # 成本价
    rent: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=0, comment="成本价"
    )
    
    # 第三方订单号
    external_trade_no: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="第三方订单号"
    )
    
    # 支付链接
    pay_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="支付链接"
    )
    
    # API请求号 (用于幂等)
    request_no: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, unique=True, comment="API请求号"
    )
    
    # 客户端信息
    create_ip: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True, comment="下单IP"
    )
    create_device: Mapped[int] = mapped_column(
        Integer, default=0, comment="下单设备 0=未知 1=手机 2=PC 3=微信"
    )
    
    # 时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="创建时间"
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="支付时间"
    )
    
    # 关系 - 明确指定 foreign_keys
    user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[user_id], back_populates="orders"
    )
    commodity: Mapped["Commodity"] = relationship("Commodity", back_populates="orders")
    payment: Mapped[Optional["PaymentMethod"]] = relationship("PaymentMethod")
    
    # Card.order_id -> Order.id 的反向关系（发货的卡密）
    delivered_cards: Mapped[List["Card"]] = relationship(
        "Card",
        foreign_keys="[Card.order_id]",
        back_populates="order"
    )
    
    # Order.card_id -> Card.id 的关系（预选卡密）
    selected_card: Mapped[Optional["Card"]] = relationship(
        "Card",
        foreign_keys=[card_id],
        post_update=True
    )
    
    coupon: Mapped[Optional["Coupon"]] = relationship("Coupon")
    from_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[from_user_id])
    owner: Mapped[Optional["User"]] = relationship("User", foreign_keys=[owner_id])
    substation_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[substation_user_id])
    
    # 索引
    __table_args__ = (
        Index("idx_orders_user_id", "user_id"),
        Index("idx_orders_commodity_id", "commodity_id"),
        Index("idx_orders_status", "status"),
        Index("idx_orders_contact", "contact"),
        Index("idx_orders_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Order {self.trade_no}>"
