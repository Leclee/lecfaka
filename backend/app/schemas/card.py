"""
卡密相关Schema
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CardImport(BaseModel):
    """批量导入卡密"""
    commodity_id: int = Field(..., description="商品ID")
    cards: str = Field(..., description="卡密内容，每行一个")
    race: Optional[str] = Field(None, description="商品种类")
    delimiter: str = Field("\n", description="分隔符")


class CardUpdate(BaseModel):
    """更新卡密"""
    secret: Optional[str] = Field(None, description="卡密内容")
    draft: Optional[str] = Field(None, description="预选展示信息")
    draft_premium: Optional[float] = Field(None, ge=0, description="预选加价")
    race: Optional[str] = Field(None, description="商品种类")
    note: Optional[str] = Field(None, description="备注")


class CardResponse(BaseModel):
    """卡密响应"""
    id: int
    commodity_id: int
    commodity_name: Optional[str] = None
    secret: str
    draft: Optional[str] = None
    draft_premium: float
    race: Optional[str] = None
    sku: Optional[Dict[str, Any]] = None
    note: Optional[str] = None
    status: int
    order_id: Optional[int] = None
    created_at: Optional[datetime] = None
    sold_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CardDraftResponse(BaseModel):
    """预选卡密响应"""
    id: int
    draft: Optional[str] = None
    draft_premium: float
    
    class Config:
        from_attributes = True


class CardBatchDelete(BaseModel):
    """批量删除卡密"""
    ids: List[int] = Field(..., min_length=1, description="卡密ID列表")


class ImportResult(BaseModel):
    """导入结果"""
    count: int = Field(..., description="成功导入数量")
    duplicates: int = Field(0, description="重复数量")
    message: str = "导入成功"
