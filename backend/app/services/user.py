"""
用户服务
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User, UserGroup, Bill
from ..core.exceptions import ValidationError, NotFoundError, InsufficientBalanceError
from ..core.security import get_password_hash, verify_password


class UserService:
    """用户服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_group(self, user: User) -> Optional[UserGroup]:
        """获取用户等级组"""
        if not user.group_id:
            # 根据累计充值自动匹配
            result = await self.db.execute(
                select(UserGroup)
                .where(UserGroup.min_recharge <= user.total_recharge)
                .order_by(UserGroup.min_recharge.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()
        
        result = await self.db.execute(
            select(UserGroup).where(UserGroup.id == user.group_id)
        )
        return result.scalar_one_or_none()
    
    async def change_password(
        self,
        user: User,
        old_password: str,
        new_password: str,
    ):
        """修改密码"""
        if not verify_password(old_password, user.password_hash, user.salt):
            raise ValidationError("旧密码错误")
        
        password_hash, salt = get_password_hash(new_password)
        user.password_hash = password_hash
        user.salt = salt
    
    async def reset_password(
        self,
        user_id: int,
        new_password: str,
    ):
        """重置密码（管理员）"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError("用户不存在")
        
        password_hash, salt = get_password_hash(new_password)
        user.password_hash = password_hash
        user.salt = salt
    
    async def adjust_balance(
        self,
        user_id: int,
        amount: float,
        description: str,
        currency: int = 0,
    ) -> Dict[str, Any]:
        """
        调整用户余额
        
        Args:
            user_id: 用户ID
            amount: 金额（正数增加，负数减少）
            description: 变动说明
            currency: 货币类型 0=余额 1=积分
            
        Returns:
            {"balance": 新余额}
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError("用户不存在")
        
        if currency == 0:
            new_balance = float(user.balance) + amount
            if new_balance < 0:
                raise InsufficientBalanceError("余额不足")
            user.balance = new_balance
            balance_after = new_balance
        else:
            new_coin = float(user.coin) + amount
            if new_coin < 0:
                raise InsufficientBalanceError("积分不足")
            user.coin = new_coin
            balance_after = new_coin
        
        # 记录账单
        bill = Bill(
            user_id=user.id,
            amount=abs(amount),
            balance=balance_after,
            type=1 if amount > 0 else 0,
            currency=currency,
            description=description,
        )
        self.db.add(bill)
        
        # 累计充值
        if amount > 0 and currency == 0:
            user.total_recharge = float(user.total_recharge) + amount
        
        return {"balance": balance_after}
    
    async def get_invite_stats(self, user_id: int) -> Dict[str, Any]:
        """获取推广统计"""
        from sqlalchemy import func
        from ..models import Order
        
        # 直接下级数量
        result = await self.db.execute(
            select(func.count())
            .select_from(User)
            .where(User.parent_id == user_id)
        )
        direct_count = result.scalar()
        
        # 推广订单数
        result = await self.db.execute(
            select(func.count())
            .select_from(Order)
            .where(Order.from_user_id == user_id)
            .where(Order.status == 1)
        )
        order_count = result.scalar()
        
        # 累计佣金
        result = await self.db.execute(
            select(func.coalesce(func.sum(Order.rebate), 0))
            .where(Order.from_user_id == user_id)
            .where(Order.status == 1)
        )
        total_rebate = float(result.scalar() or 0)
        
        return {
            "direct_count": direct_count,
            "order_count": order_count,
            "total_rebate": total_rebate,
        }
