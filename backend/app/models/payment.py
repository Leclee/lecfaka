"""
支付方式模型
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class PaymentMethod(Base):
    """支付方式"""
    __tablename__ = "payment_methods"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 名称
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="支付名称")
    
    # 图标
    icon: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="图标URL")
    
    # 处理器标识 (如 epay, usdt, balance)
    handler: Mapped[str] = mapped_column(String(50), nullable=False, comment="处理器标识")
    
    # 通道编码 (如 alipay, wxpay)
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="通道编码")
    
    # 配置 (JSON)
    config: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="支付配置JSON"
    )
    
    # 手续费
    cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), default=0, comment="手续费"
    )
    cost_type: Mapped[int] = mapped_column(
        Integer, default=0, comment="手续费类型 0=固定 1=百分比"
    )
    
    # 适用场景 1=商品购买 0=不可用
    commodity: Mapped[int] = mapped_column(
        Integer, default=1, comment="商品购买 1=可用 0=不可用"
    )
    # 适用场景 1=充值 0=不可用
    recharge: Mapped[int] = mapped_column(
        Integer, default=1, comment="余额充值 1=可用 0=不可用"
    )
    
    # 设备限制 0=全部 1=手机 2=PC 3=微信
    equipment: Mapped[int] = mapped_column(
        Integer, default=0, comment="设备限制 0=全部"
    )
    
    # 排序
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    
    # 状态
    status: Mapped[int] = mapped_column(Integer, default=1, comment="状态 1=启用 0=禁用")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="创建时间"
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, onupdate=datetime.utcnow, comment="更新时间"
    )
    
    def __repr__(self) -> str:
        return f"<PaymentMethod {self.name}>"
