"""
提现模型
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, Numeric, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .user import User


class Withdrawal(Base):
    """提现申请"""
    __tablename__ = "withdrawals"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 提现单号
    withdraw_no: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True, comment="提现单号"
    )
    
    # 用户
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="用户ID"
    )
    
    # 提现金额
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment="提现金额"
    )
    
    # 手续费
    fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=0, comment="手续费"
    )
    
    # 实际到账金额
    actual_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment="实际到账金额"
    )
    
    # 提现方式 alipay/wechat/bank
    method: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="提现方式"
    )
    
    # 收款账号信息
    account: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="收款账号"
    )
    account_name: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="收款人姓名"
    )
    
    # 状态 0=待审核 1=审核通过 2=已打款 3=已拒绝 4=已取消
    status: Mapped[int] = mapped_column(Integer, default=0, comment="状态")
    
    # 审核信息
    admin_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, comment="审核管理员ID"
    )
    admin_remark: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="管理员备注"
    )
    
    # 用户备注
    user_remark: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="用户备注"
    )
    
    # 时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="申请时间"
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="审核时间"
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="打款时间"
    )
    
    # 关系
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    admin: Mapped[Optional["User"]] = relationship("User", foreign_keys=[admin_id])
    
    # 索引
    __table_args__ = (
        Index("idx_withdrawals_user_id", "user_id"),
        Index("idx_withdrawals_status", "status"),
        Index("idx_withdrawals_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Withdrawal {self.withdraw_no}>"
