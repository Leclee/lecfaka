"""
优惠券模型
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    String, Integer, DateTime, ForeignKey, 
    Numeric, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .user import User
    from .commodity import Commodity
    from .category import Category


class Coupon(Base):
    """优惠券"""
    __tablename__ = "coupons"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 优惠券码
    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="优惠券码"
    )
    
    # 所属用户 (创建者)
    owner_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, default=None, comment="所属用户ID"
    )
    
    # 限制商品 (None=不限)
    commodity_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("commodities.id"), nullable=True, default=None, comment="限制商品ID"
    )
    
    # 限制分类 (None=不限)
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=True, default=None, comment="限制分类ID"
    )
    
    # 限制商品种类
    race: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="限制商品种类"
    )
    
    # 优惠金额
    money: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment="优惠金额"
    )
    
    # 优惠模式 0=固定金额 1=按件优惠
    mode: Mapped[int] = mapped_column(
        Integer, default=0, comment="优惠模式 0=固定 1=按件"
    )
    
    # 可用次数
    life: Mapped[int] = mapped_column(Integer, default=1, comment="可用次数")
    
    # 已使用次数
    use_life: Mapped[int] = mapped_column(Integer, default=0, comment="已使用次数")
    
    # 状态 0=可用 1=已失效 2=已锁定
    status: Mapped[int] = mapped_column(Integer, default=0, comment="状态 0=可用 1=失效 2=锁定")
    
    # 备注信息
    remark: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="备注信息"
    )
    
    # 最后使用的订单号
    trade_no: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, comment="最后使用订单号"
    )
    
    # 过期时间
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="过期时间"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="创建时间"
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="最后使用时间"
    )
    
    # 关系
    owner: Mapped[Optional["User"]] = relationship("User")
    commodity: Mapped[Optional["Commodity"]] = relationship("Commodity")
    category: Mapped[Optional["Category"]] = relationship("Category")
    
    # 索引
    __table_args__ = (
        Index("idx_coupons_owner_id", "owner_id"),
        Index("idx_coupons_status", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<Coupon {self.code}>"
