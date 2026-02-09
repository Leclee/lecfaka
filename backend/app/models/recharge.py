"""
充值订单模型
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .user import User
    from .payment import PaymentMethod


class RechargeOrder(Base):
    """充值订单"""
    __tablename__ = "recharge_orders"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 订单号
    trade_no: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True, comment="订单号"
    )
    
    # 用户
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="用户ID"
    )
    
    # 支付方式
    payment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("payment_methods.id"), nullable=True, comment="支付方式ID"
    )
    
    # 充值金额
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment="充值金额"
    )
    
    # 实际到账金额（扣除手续费后）
    actual_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment="实际到账金额"
    )
    
    # 第三方订单号
    external_trade_no: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="第三方订单号"
    )
    
    # 状态 0=待支付 1=已支付 2=已取消 3=支付失败
    status: Mapped[int] = mapped_column(Integer, default=0, comment="状态")
    
    # IP信息
    create_ip: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True, comment="下单IP"
    )
    
    # 时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="创建时间"
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="支付时间"
    )
    
    # 关系
    user: Mapped["User"] = relationship("User")
    payment: Mapped[Optional["PaymentMethod"]] = relationship("PaymentMethod")
    
    # 索引
    __table_args__ = (
        Index("idx_recharge_orders_user_id", "user_id"),
        Index("idx_recharge_orders_status", "status"),
        Index("idx_recharge_orders_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<RechargeOrder {self.trade_no}>"
