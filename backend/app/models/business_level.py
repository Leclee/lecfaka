"""
商户等级模型
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class BusinessLevel(Base):
    """商户等级"""
    __tablename__ = "business_levels"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 等级名称
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="等级名称")
    
    # 等级图标
    icon: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="图标URL")
    
    # 购买价格
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=0, comment="购买价格"
    )
    
    # 供货商手续费比例 (0-1)
    supplier_fee: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), default=0, comment="供货商手续费比例"
    )
    
    # 权限设置
    can_supply: Mapped[int] = mapped_column(
        Integer, default=1, comment="供货权限 0=否 1=是"
    )
    can_substation: Mapped[int] = mapped_column(
        Integer, default=1, comment="分站权限 0=否 1=是"
    )
    can_bindomain: Mapped[int] = mapped_column(
        Integer, default=0, comment="绑定独立域名 0=否 1=是"
    )
    
    # 商品数量限制
    max_commodities: Mapped[int] = mapped_column(
        Integer, default=100, comment="最大商品数量"
    )
    
    # 分站数量限制
    max_substations: Mapped[int] = mapped_column(
        Integer, default=0, comment="最大分站数量"
    )
    
    # 描述
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="等级描述"
    )
    
    # 排序
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    
    # 状态
    status: Mapped[int] = mapped_column(Integer, default=1, comment="状态 0=禁用 1=启用")
    
    # 时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="创建时间"
    )
    
    def __repr__(self) -> str:
        return f"<BusinessLevel {self.name}>"
