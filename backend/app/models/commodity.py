"""
商品模型
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    String, Integer, DateTime, ForeignKey, 
    Numeric, Text, Boolean, JSON, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .category import Category
    from .card import Card
    from .variant import CommodityVariant
    from .order import Order
    from .user import User


class Commodity(Base):
    """商品"""
    __tablename__ = "commodities"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="商品名称")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="商品描述")
    cover: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="封面图")
    
    # 分类
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=False, comment="分类ID"
    )
    
    # 价格
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment="游客价格"
    )
    user_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment="会员价格"
    )
    factory_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=0, comment="成本价"
    )
    
    # 库存 (仅用于手动发货或显示)
    stock: Mapped[int] = mapped_column(Integer, default=0, comment="库存数量")
    
    # 发货方式 0=自动发货 1=手动发货
    delivery_way: Mapped[int] = mapped_column(
        Integer, default=0, comment="发货方式 0=自动 1=手动"
    )
    # 自动发货模式 0=顺序 1=随机 2=倒序
    delivery_auto_mode: Mapped[int] = mapped_column(
        Integer, default=0, comment="自动发货模式"
    )
    # 手动发货提示
    delivery_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="手动发货提示"
    )
    
    # 联系方式类型 0=任意 1=手机 2=邮箱 3=QQ
    contact_type: Mapped[int] = mapped_column(
        Integer, default=0, comment="联系方式类型"
    )
    
    # 查单密码
    password_status: Mapped[int] = mapped_column(
        Integer, default=0, comment="是否需要查单密码 0=否 1=是"
    )
    
    # 预选卡密
    draft_status: Mapped[int] = mapped_column(
        Integer, default=0, comment="是否开启预选 0=否 1=是"
    )
    draft_premium: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=0, comment="预选加价"
    )
    
    # 秒杀
    seckill_status: Mapped[int] = mapped_column(
        Integer, default=0, comment="是否秒杀 0=否 1=是"
    )
    seckill_start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="秒杀开始时间"
    )
    seckill_end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="秒杀结束时间"
    )
    
    # 限购
    minimum: Mapped[int] = mapped_column(Integer, default=0, comment="最少购买数量")
    maximum: Mapped[int] = mapped_column(Integer, default=0, comment="最多购买数量")
    purchase_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="每人限购数量 0=不限"
    )
    
    # 仅登录用户可购买
    only_user: Mapped[int] = mapped_column(
        Integer, default=0, comment="仅登录可购买 0=否 1=是"
    )
    
    # 是否发送邮件
    send_email: Mapped[int] = mapped_column(
        Integer, default=0, comment="发送邮件 0=否 1=是"
    )
    
    # 是否隐藏库存
    inventory_hidden: Mapped[int] = mapped_column(
        Integer, default=0, comment="隐藏库存 0=否 1=是"
    )
    
    # 优惠券
    coupon: Mapped[int] = mapped_column(
        Integer, default=1, comment="是否可用优惠券 0=否 1=是"
    )
    
    # API对接
    api_status: Mapped[int] = mapped_column(
        Integer, default=0, comment="是否开放API 0=否 1=是"
    )
    
    # 推荐
    recommend: Mapped[int] = mapped_column(
        Integer, default=0, comment="是否推荐 0=否 1=是"
    )
    
    # 隐藏商品
    hide: Mapped[int] = mapped_column(
        Integer, default=0, comment="是否隐藏 0=否 1=是"
    )
    
    # 自定义配置 (JSON) - 种类、批发等
    config: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="自定义配置JSON"
    )
    
    # 批量优惠配置 (JSON) - [{quantity: 10, price: 5.5}, ...]
    wholesale_config: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="批量优惠配置JSON"
    )
    
    # 会员等级价格配置 (JSON)
    level_price: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="会员等级价格JSON"
    )
    
    # 是否禁用等级折扣
    level_disable: Mapped[int] = mapped_column(
        Integer, default=0, comment="禁用等级折扣 0=否 1=是"
    )
    
    # 自定义控件 (JSON)
    widget: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="自定义控件JSON"
    )
    
    # 售后留言
    leave_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="售后留言"
    )
    
    # 排序
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    
    # 状态
    status: Mapped[int] = mapped_column(Integer, default=1, comment="状态 1=上架 0=下架")
    
    # 所属用户 (NULL=主站)
    owner_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, default=None, comment="所属用户ID"
    )
    
    # 共享店铺ID (如果是对接的商品)
    shared_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="共享店铺ID"
    )
    shared_code: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="共享商品编码"
    )
    shared_premium: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=0, comment="共享加价"
    )
    shared_premium_type: Mapped[int] = mapped_column(
        Integer, default=0, comment="加价类型 0=固定 1=百分比"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="创建时间"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, onupdate=datetime.utcnow, comment="更新时间"
    )
    
    # 关系
    category: Mapped["Category"] = relationship("Category", back_populates="commodities")
    cards: Mapped[List["Card"]] = relationship("Card", back_populates="commodity")
    variants: Mapped[List["CommodityVariant"]] = relationship("CommodityVariant", back_populates="commodity")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="commodity")
    owner: Mapped[Optional["User"]] = relationship("User")
    
    # 索引
    __table_args__ = (
        Index("idx_commodities_category_id", "category_id"),
        Index("idx_commodities_owner_id", "owner_id"),
        Index("idx_commodities_status", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<Commodity {self.name}>"
