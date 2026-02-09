"""
控制台通知插件
展示如何使用 Hook 系统构建一个 extension 类型插件
"""

from typing import Dict, Any
from datetime import datetime

from app.plugins.sdk.base import PluginBase, PluginMeta
from app.plugins.sdk.hooks import hooks, Events, EventContext


class ConsoleNotifyPlugin(PluginBase):
    """
    控制台通知插件。
    监听订单和用户事件，在控制台打印日志。
    这是一个示范插件，展示 Hook 的完整用法。
    """

    def __init__(self, meta: PluginMeta, config: Dict[str, Any]):
        super().__init__(meta, config)
        self.emoji = config.get("emoji_enabled", True)

    async def on_enable(self) -> None:
        await super().on_enable()
        # 注册所有钩子 - 注意 owner 参数，用于插件禁用时自动清理
        hooks.on(Events.ORDER_CREATED, self._on_order_created, owner=self.id)
        hooks.on(Events.ORDER_PAID, self._on_order_paid, owner=self.id)
        hooks.on(Events.ORDER_DELIVERED, self._on_order_delivered, owner=self.id)
        hooks.on(Events.USER_REGISTERED, self._on_user_registered, owner=self.id)
        hooks.on(Events.APP_STARTUP, self._on_startup, owner=self.id)
        self.logger.info("Console notify hooks registered")

    async def on_disable(self) -> None:
        # hooks.off_by_owner 会在 PluginManager.disable_plugin 中调用
        # 这里也可以手动清理
        self.logger.info("Console notify hooks will be removed")
        await super().on_disable()

    def _prefix(self, emoji: str) -> str:
        ts = datetime.now().strftime("%H:%M:%S")
        if self.emoji:
            return f"[{ts}] {emoji}"
        return f"[{ts}] [NOTIFY]"

    async def _on_startup(self, ctx: EventContext):
        self.logger.info(
            f"{self._prefix('🚀')} Console Notify Plugin is active!"
        )

    async def _on_order_created(self, ctx: EventContext):
        order = ctx.data.get("order")
        commodity = ctx.data.get("commodity")
        if order and commodity:
            self.logger.info(
                f"{self._prefix('📦')} New order: {order.trade_no} "
                f"| {commodity.name} x{order.quantity} "
                f"| ¥{order.amount}"
            )

    async def _on_order_paid(self, ctx: EventContext):
        order = ctx.data.get("order")
        if order:
            self.logger.info(
                f"{self._prefix('💰')} Order paid: {order.trade_no} "
                f"| ¥{order.amount}"
            )

    async def _on_order_delivered(self, ctx: EventContext):
        order = ctx.data.get("order")
        secret = ctx.data.get("secret", "")
        if order:
            preview = secret[:30] + "..." if len(secret) > 30 else secret
            self.logger.info(
                f"{self._prefix('📬')} Order delivered: {order.trade_no} "
                f"| secret: {preview}"
            )

    async def _on_user_registered(self, ctx: EventContext):
        user = ctx.data.get("user")
        if user:
            self.logger.info(
                f"{self._prefix('👤')} New user: {user.username}"
            )
