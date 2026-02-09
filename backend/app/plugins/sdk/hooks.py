"""
钩子/事件系统
允许插件在业务流程的关键节点注入自定义逻辑
"""

import logging
from typing import Callable, Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("plugins.hooks")


class Events:
    """所有可用的钩子事件"""

    # --- 应用生命周期 ---
    APP_STARTUP = "app.startup"
    APP_SHUTDOWN = "app.shutdown"

    # --- 订单流程 ---
    ORDER_CREATING = "order.creating"      # 订单创建前（可拦截）
    ORDER_CREATED = "order.created"        # 订单创建后
    ORDER_PAID = "order.paid"              # 支付成功
    ORDER_DELIVERED = "order.delivered"     # 发货完成
    ORDER_CANCELLED = "order.cancelled"    # 订单取消

    # --- 支付 ---
    PAYMENT_CREATING = "payment.creating"
    PAYMENT_CALLBACK = "payment.callback"

    # --- 用户 ---
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_RECHARGED = "user.recharged"

    # --- 商品/卡密 ---
    CARD_IMPORTED = "card.imported"
    COMMODITY_CREATED = "commodity.created"

    # --- 通知 ---
    NOTIFY_SEND = "notify.send"


@dataclass
class EventContext:
    """传递给钩子处理函数的上下文"""
    event: str
    data: Dict[str, Any] = field(default_factory=dict)
    cancelled: bool = False
    cancel_reason: str = ""
    results: List[Any] = field(default_factory=list)

    def cancel(self, reason: str = ""):
        """取消当前操作（仅 creating 类事件有效）"""
        self.cancelled = True
        self.cancel_reason = reason

    def add_result(self, result: Any):
        """添加处理结果"""
        self.results.append(result)


class HookManager:
    """
    全局钩子管理器。

    注册钩子（插件中）:
        hooks.on(Events.ORDER_PAID, my_handler)

    触发钩子（核心代码中）:
        ctx = await hooks.emit(Events.ORDER_PAID, {"order": order})
    """

    def __init__(self):
        self._handlers: Dict[str, List[tuple]] = {}
        self._handler_owners: Dict[str, List[str]] = {}  # event -> [plugin_id, ...]

    def on(
        self,
        event: str,
        handler: Callable,
        priority: int = 10,
        owner: Optional[str] = None,
    ):
        """
        注册事件处理函数。

        Args:
            event: 事件名称
            handler: 异步处理函数 async def handler(ctx: EventContext)
            priority: 优先级，数字越小越先执行
            owner: 所属插件 ID（用于按插件移除）
        """
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append((priority, handler, owner))
        self._handlers[event].sort(key=lambda x: x[0])

        if owner:
            if event not in self._handler_owners:
                self._handler_owners[event] = []
            self._handler_owners[event].append(owner)

        logger.debug(f"Hook registered: {event} <- {handler.__name__} (owner={owner})")

    def off(self, event: str, handler: Callable):
        """移除指定处理函数"""
        if event in self._handlers:
            self._handlers[event] = [
                (p, h, o) for p, h, o in self._handlers[event] if h != handler
            ]

    def off_by_owner(self, owner: str):
        """移除指定插件的所有钩子"""
        for event in list(self._handlers.keys()):
            self._handlers[event] = [
                (p, h, o) for p, h, o in self._handlers[event] if o != owner
            ]
        logger.debug(f"All hooks removed for plugin: {owner}")

    async def emit(self, event: str, data: Dict[str, Any] = None) -> EventContext:
        """
        触发事件。

        Args:
            event: 事件名称
            data: 事件数据

        Returns:
            EventContext（可检查 .cancelled 判断是否被拦截）
        """
        ctx = EventContext(event=event, data=data or {})

        handlers = self._handlers.get(event, [])
        if not handlers:
            return ctx

        logger.debug(f"Emitting {event} to {len(handlers)} handler(s)")

        for priority, handler, owner in handlers:
            try:
                result = await handler(ctx)
                if result is not None:
                    ctx.add_result(result)
            except Exception as e:
                logger.error(
                    f"Hook error in {event} (handler={handler.__name__}, "
                    f"plugin={owner}): {e}",
                    exc_info=True,
                )

            if ctx.cancelled:
                logger.info(
                    f"Event {event} cancelled by {owner}: {ctx.cancel_reason}"
                )
                break

        return ctx

    def get_handlers(self, event: str) -> List[tuple]:
        """获取某事件的所有处理函数（调试用）"""
        return self._handlers.get(event, [])

    def get_all_events(self) -> List[str]:
        """获取所有注册了处理函数的事件"""
        return list(self._handlers.keys())

    def clear(self):
        """清除所有钩子"""
        self._handlers.clear()
        self._handler_owners.clear()


# 全局单例
hooks = HookManager()
