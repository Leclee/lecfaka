"""
用户模型
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    String, Integer, DateTime, ForeignKey, 
    Numeric, Boolean, Text, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .order import Order
    from .bill import Bill
    from .shop import Shop


class UserGroup(Base):
    """用户等级组"""
    __tablename__ = "user_groups"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="等级名称")
    
    # 等级图标/标识
    icon: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="图标URL")
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="颜色代码")
    
    # 升级条件
    min_recharge: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=0, comment="最低累计充值金额"
    )
    
    # 优惠
    discount: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), default=0, comment="折扣比例 0-1"
    )
    
    # 排序
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    
    # 状态
    status: Mapped[int] = mapped_column(Integer, default=1, comment="状态 0=禁用 1=启用")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="创建时间"
    )
    
    # 关系
    users: Mapped[List["User"]] = relationship("User", back_populates="group")


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="用户名"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True, index=True, comment="邮箱"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20), unique=True, nullable=True, index=True, comment="手机号"
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")
    salt: Mapped[str] = mapped_column(String(32), nullable=False, comment="密码盐")
    
    # 头像
    avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="头像URL")
    
    # 余额
    balance: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=0, comment="账户余额"
    )
    coin: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=0, comment="硬币/积分"
    )
    total_recharge: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=0, comment="累计充值"
    )
    
    # 推广关系
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, comment="上级用户ID"
    )
    
    # 用户等级
    group_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("user_groups.id"), nullable=True, comment="用户等级ID"
    )
    
    # 商户等级ID
    business_level_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("business_levels.id"), nullable=True, comment="商户等级ID"
    )
    
    # 兼容旧字段
    business_level: Mapped[int] = mapped_column(
        Integer, default=0, comment="商户等级 0=普通用户(已弃用)"
    )
    
    # QQ号
    qq: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="QQ号")
    
    # 收款信息
    alipay: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="支付宝账号")
    wechat: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="微信账号")
    
    # 状态
    status: Mapped[int] = mapped_column(Integer, default=1, comment="状态 1=正常 0=禁用")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否管理员")
    
    # 时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="注册时间"
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="最后登录时间"
    )
    last_login_ip: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True, comment="最后登录IP"
    )
    
    # 关系
    parent: Mapped[Optional["User"]] = relationship(
        "User", remote_side=[id], foreign_keys=[parent_id]
    )
    children: Mapped[List["User"]] = relationship(
        "User", foreign_keys=[parent_id], back_populates="parent"
    )
    group: Mapped[Optional["UserGroup"]] = relationship(
        "UserGroup", back_populates="users"
    )
    orders: Mapped[List["Order"]] = relationship(
        "Order", back_populates="user", foreign_keys="Order.user_id"
    )
    bills: Mapped[List["Bill"]] = relationship("Bill", back_populates="user")
    shop: Mapped[Optional["Shop"]] = relationship("Shop", back_populates="user", uselist=False)
    
    # 索引
    __table_args__ = (
        Index("idx_users_parent_id", "parent_id"),
        Index("idx_users_status", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<User {self.username}>"
