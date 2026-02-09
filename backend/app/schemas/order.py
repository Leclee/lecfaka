"""
订单相关Schema
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    """创建订单"""
    commodity_id: int = Field(..., description="商品ID")
    quantity: int = Field(1, ge=1, description="购买数量")
    payment_id: int = Field(..., description="支付方式ID")
    contact: str = Field(..., min_length=1, description="联系方式")
    password: Optional[str] = Field(None, description="查单密码")
    race: Optional[str] = Field(None, description="商品种类")
    card_id: Optional[int] = Field(None, description="预选卡密ID")
    coupon: Optional[str] = Field(None, description="优惠券码")
    widget: Optional[Dict[str, Any]] = Field(None, description="自定义控件数据")


class OrderResponse(BaseModel):
    """订单创建响应"""
    trade_no: str
    amount: float
    status: int
    payment_url: Optional[str] = None
    payment_type: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None
    secret: Optional[str] = None


class OrderDetailResponse(BaseModel):
    """订单详情响应"""
    id: int
    trade_no: str
    amount: float
    quantity: int
    status: int
    delivery_status: int
    contact: str
    secret: Optional[str] = None
    commodity_name: Optional[str] = None
    payment_name: Optional[str] = None
    created_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    has_password: bool = False
    
    class Config:
        from_attributes = True


class OrderQuery(BaseModel):
    """订单查询"""
    contact: str = Field(..., description="联系方式或订单号")


class GetSecretRequest(BaseModel):
    """获取卡密"""
    password: Optional[str] = Field(None, description="查单密码")


class DeliverOrderRequest(BaseModel):
    """手动发货"""
    secret: str = Field(..., description="发货内容")
