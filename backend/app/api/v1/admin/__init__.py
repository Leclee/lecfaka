"""
管理后台API
"""

from fastapi import APIRouter

from .dashboard import router as dashboard_router
from .commodities import router as commodities_router
from .cards import router as cards_router
from .orders import router as orders_router
from .users import router as users_router
from .settings import router as settings_router
from .announcements import router as announcements_router
from .user_groups import router as user_groups_router
from .business_levels import router as business_levels_router
from .recharge import router as recharge_router
from .withdrawals import router as withdrawals_router
from .coupons import router as coupons_router
from .bills import router as bills_router
from .logs import router as logs_router
from .upload import router as upload_router
from .plugins import router as plugins_router

router = APIRouter()

router.include_router(dashboard_router, prefix="/dashboard")
router.include_router(commodities_router, prefix="/commodities")
router.include_router(cards_router, prefix="/cards")
router.include_router(orders_router, prefix="/orders")
router.include_router(users_router, prefix="/users")
router.include_router(settings_router, prefix="/settings")
router.include_router(announcements_router, prefix="/announcements")
router.include_router(user_groups_router, prefix="/user-groups")
router.include_router(business_levels_router, prefix="/business-levels")
router.include_router(recharge_router, prefix="/recharge")
router.include_router(withdrawals_router, prefix="/withdrawals")
router.include_router(coupons_router, prefix="/coupons")
router.include_router(bills_router, prefix="/bills")
router.include_router(logs_router, prefix="/logs")
router.include_router(upload_router, prefix="/upload")
router.include_router(plugins_router, prefix="/plugins")