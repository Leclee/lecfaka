"""
商品相关Schema
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    """创建分类"""
    name: str = Field(..., min_length=1, max_length=100, description="分类名称")
    icon: Optional[str] = Field(None, description="图标URL")
    sort: int = Field(0, description="排序")
    status: int = Field(1, description="状态 1=显示 0=隐藏")


class CategoryUpdate(BaseModel):
    """更新分类"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    icon: Optional[str] = None
    sort: Optional[int] = None
    status: Optional[int] = None


class CategoryResponse(BaseModel):
    """分类响应"""
    id: int
    name: str
    icon: Optional[str] = None
    sort: int
    status: int
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CommodityCreate(BaseModel):
    """创建商品"""
    name: str = Field(..., min_length=1, max_length=200, description="商品名称")
    description: Optional[str] = Field(None, description="商品描述")
    cover: Optional[str] = Field(None, description="封面图URL")
    category_id: int = Field(..., description="分类ID")
    price: float = Field(..., gt=0, description="游客价格")
    user_price: float = Field(..., gt=0, description="会员价格")
    factory_price: float = Field(0, ge=0, description="成本价")
    delivery_way: int = Field(0, description="发货方式 0=自动 1=手动")
    delivery_auto_mode: int = Field(0, description="自动发货模式")
    delivery_message: Optional[str] = Field(None, description="手动发货提示")
    contact_type: int = Field(0, description="联系方式类型")
    password_status: int = Field(0, description="是否需要查单密码")
    draft_status: int = Field(0, description="是否开启预选")
    draft_premium: float = Field(0, description="预选加价")
    minimum: int = Field(0, description="最少购买数量")
    maximum: int = Field(0, description="最多购买数量")
    purchase_count: int = Field(0, description="限购数量")
    only_user: int = Field(0, description="仅登录可购买")
    send_email: int = Field(0, description="发送邮件")
    inventory_hidden: int = Field(0, description="隐藏库存")
    coupon: int = Field(1, description="可用优惠券")
    recommend: int = Field(0, description="是否推荐")
    sort: int = Field(0, description="排序")
    status: int = Field(1, description="状态 1=上架 0=下架")
    widget: Optional[str] = Field(None, description="自定义控件JSON")
    leave_message: Optional[str] = Field(None, description="售后留言")


class CommodityUpdate(BaseModel):
    """更新商品"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    cover: Optional[str] = None
    category_id: Optional[int] = None
    price: Optional[float] = Field(None, gt=0)
    user_price: Optional[float] = Field(None, gt=0)
    factory_price: Optional[float] = Field(None, ge=0)
    delivery_way: Optional[int] = None
    delivery_auto_mode: Optional[int] = None
    delivery_message: Optional[str] = None
    contact_type: Optional[int] = None
    password_status: Optional[int] = None
    draft_status: Optional[int] = None
    draft_premium: Optional[float] = None
    minimum: Optional[int] = None
    maximum: Optional[int] = None
    purchase_count: Optional[int] = None
    only_user: Optional[int] = None
    send_email: Optional[int] = None
    inventory_hidden: Optional[int] = None
    coupon: Optional[int] = None
    recommend: Optional[int] = None
    sort: Optional[int] = None
    status: Optional[int] = None
    widget: Optional[str] = None
    leave_message: Optional[str] = None


class CommodityResponse(BaseModel):
    """商品详情响应"""
    id: int
    name: str
    description: Optional[str] = None
    cover: Optional[str] = None
    category_id: int
    price: float
    user_price: float
    factory_price: float
    stock: int
    delivery_way: int
    contact_type: int
    password_status: int
    draft_status: int
    draft_premium: float
    minimum: int
    maximum: int
    only_user: int
    widget: Optional[str] = None
    leave_message: Optional[str] = None
    sort: int
    status: int
    recommend: int
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CommodityListResponse(BaseModel):
    """商品列表项响应"""
    id: int
    name: str
    cover: Optional[str] = None
    price: float
    user_price: float
    category_id: int
    stock: int
    sold_count: int = 0
    delivery_way: int
    recommend: int
    
    class Config:
        from_attributes = True
