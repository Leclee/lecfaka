"""
通用响应模式
"""

from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """统一响应模型"""
    code: int = 200
    message: str = "success"
    data: Optional[T] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    total: int
    page: int
    limit: int
    items: List[T]


class MessageResponse(BaseModel):
    """消息响应"""
    message: str


class IdResponse(BaseModel):
    """ID响应"""
    id: int
    message: str = "success"
