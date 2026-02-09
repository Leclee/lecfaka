"""
Pydantic Schemas
用于API请求和响应的数据验证
"""

from .common import (
    ResponseModel,
    PaginatedResponse,
    MessageResponse,
)
from .user import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    PasswordChange,
)
from .commodity import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CommodityCreate,
    CommodityUpdate,
    CommodityResponse,
    CommodityListResponse,
)
from .order import (
    OrderCreate,
    OrderResponse,
    OrderDetailResponse,
    OrderQuery,
)
from .card import (
    CardImport,
    CardUpdate,
    CardResponse,
)

__all__ = [
    # Common
    "ResponseModel",
    "PaginatedResponse",
    "MessageResponse",
    # User
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "PasswordChange",
    # Commodity
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
    "CommodityCreate",
    "CommodityUpdate",
    "CommodityResponse",
    "CommodityListResponse",
    # Order
    "OrderCreate",
    "OrderResponse",
    "OrderDetailResponse",
    "OrderQuery",
    # Card
    "CardImport",
    "CardUpdate",
    "CardResponse",
]
