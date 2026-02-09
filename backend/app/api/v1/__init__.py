"""
API v1 路由汇总
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .shop import router as shop_router
from .orders import router as orders_router
from .users import router as users_router
from .payments import router as payments_router
from .admin import router as admin_router
from .uploads import router as uploads_router

api_router = APIRouter()

# 认证
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])

# 商城
api_router.include_router(shop_router, prefix="/shop", tags=["商城"])

# 订单
api_router.include_router(orders_router, prefix="/orders", tags=["订单"])

# 用户
api_router.include_router(users_router, prefix="/users", tags=["用户"])

# 支付回调
api_router.include_router(payments_router, prefix="/payments", tags=["支付"])

# 管理后台
api_router.include_router(admin_router, prefix="/admin", tags=["管理后台"])

# 文件访问
api_router.include_router(uploads_router, prefix="/uploads", tags=["文件"])
