"""
支付服务
"""

from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import PaymentMethod
from ..payments import PAYMENT_HANDLERS as LEGACY_HANDLERS


class PaymentService:
    """支付服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_available_payments(
        self,
        for_commodity: bool = True,
        for_recharge: bool = False,
        equipment: int = 0,
        user_logged_in: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        获取可用的支付方式
        
        Args:
            for_commodity: 用于商品购买
            for_recharge: 用于余额充值
            equipment: 设备类型 0=全部 1=手机 2=PC 3=微信
            user_logged_in: 用户是否已登录
        """
        query = select(PaymentMethod).where(PaymentMethod.status == 1)
        
        if for_commodity:
            query = query.where(PaymentMethod.commodity == 1)
        if for_recharge:
            query = query.where(PaymentMethod.recharge == 1)
        
        # 设备限制
        if equipment > 0:
            query = query.where(
                (PaymentMethod.equipment == 0) | 
                (PaymentMethod.equipment == equipment)
            )
        
        query = query.order_by(PaymentMethod.sort.asc())
        
        result = await self.db.execute(query)
        payments = result.scalars().all()
        
        items = []
        for p in payments:
            # 余额支付需要登录
            if p.handler == "#balance" and not user_logged_in:
                continue
            
            items.append({
                "id": p.id,
                "name": p.name,
                "icon": p.icon,
                "handler": p.handler,
                "code": p.code,
            })
        
        return items
    
    def get_supported_handlers(self) -> List[Dict[str, Any]]:
        """获取支持的支付处理器列表（合并插件系统和旧模块）"""
        from ..plugins import PAYMENT_HANDLERS as PLUGIN_HANDLERS
        
        handlers = []
        seen = set()
        
        # 插件系统优先
        for handler_id, handler_class in PLUGIN_HANDLERS.items():
            handlers.append({
                "id": handler_id,
                "name": getattr(handler_class, "name", handler_id),
                "channels": getattr(handler_class, "channels", {}),
            })
            seen.add(handler_id)
        
        # 旧模块 fallback
        for handler_id, handler_class in LEGACY_HANDLERS.items():
            if handler_id not in seen:
                handlers.append({
                    "id": handler_id,
                    "name": getattr(handler_class, "name", handler_id),
                    "channels": getattr(handler_class, "channels", {}),
                })
        
        return handlers
    
    async def create_payment_method(
        self,
        name: str,
        handler: str,
        code: Optional[str] = None,
        icon: Optional[str] = None,
        config: Optional[Dict] = None,
        cost: float = 0,
        cost_type: int = 0,
        commodity: int = 1,
        recharge: int = 1,
        equipment: int = 0,
        sort: int = 0,
        status: int = 1,
    ) -> PaymentMethod:
        """创建支付方式"""
        import json
        
        payment = PaymentMethod(
            name=name,
            handler=handler,
            code=code,
            icon=icon,
            config=json.dumps(config) if config else None,
            cost=cost,
            cost_type=cost_type,
            commodity=commodity,
            recharge=recharge,
            equipment=equipment,
            sort=sort,
            status=status,
        )
        
        self.db.add(payment)
        await self.db.flush()
        
        return payment
    
    async def update_payment_method(
        self,
        payment_id: int,
        **kwargs
    ) -> PaymentMethod:
        """更新支付方式"""
        import json
        from ..core.exceptions import NotFoundError
        
        result = await self.db.execute(
            select(PaymentMethod).where(PaymentMethod.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        
        if not payment:
            raise NotFoundError("支付方式不存在")
        
        for key, value in kwargs.items():
            if value is not None:
                if key == "config" and isinstance(value, dict):
                    value = json.dumps(value)
                setattr(payment, key, value)
        
        return payment
