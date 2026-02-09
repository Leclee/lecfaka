"""
账单模型
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .user import User


class Bill(Base):
    """账单记录"""
    __tablename__ = "bills"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 用户
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="用户ID"
    )
    
    # 金额
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment="变动金额"
    )
    
    # 变动后余额
    balance: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment="变动后余额"
    )
    
    # 类型 0=支出 1=收入
    type: Mapped[int] = mapped_column(Integer, nullable=False, comment="类型 0=支出 1=收入")
    
    # 货币类型 0=余额 1=硬币/积分
    currency: Mapped[int] = mapped_column(Integer, default=0, comment="货币类型 0=余额 1=积分")
    
    # 描述
    description: Mapped[str] = mapped_column(String(255), nullable=False, comment="变动说明")
    
    # 关联订单号
    order_trade_no: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, comment="关联订单号"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="创建时间"
    )
    
    # 关系
    user: Mapped["User"] = relationship("User", back_populates="bills")
    
    # 索引
    __table_args__ = (
        Index("idx_bills_user_id", "user_id"),
        Index("idx_bills_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Bill {self.id}>"
