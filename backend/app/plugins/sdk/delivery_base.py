"""
发货插件基类
"""

from abc import abstractmethod
from typing import Dict, Any, Optional

from .base import PluginBase, PluginMeta


class DeliveryPluginBase(PluginBase):
    """
    发货插件基类。
    用于实现自定义发货逻辑（如 API 发货、自动充值等）。
    """

    def __init__(self, meta: PluginMeta, config: Dict[str, Any]):
        super().__init__(meta, config)

    @abstractmethod
    async def deliver(
        self,
        order_trade_no: str,
        commodity_id: int,
        quantity: int,
        contact: str,
        race: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        执行发货。

        Args:
            order_trade_no: 订单号
            commodity_id: 商品 ID
            quantity: 数量
            contact: 联系方式
            race: 商品种类
        
        Returns:
            {"success": bool, "secret": str, "message": str}
        """
        pass
