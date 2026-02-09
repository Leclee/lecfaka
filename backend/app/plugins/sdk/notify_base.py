"""
通知插件基类
"""

from abc import abstractmethod
from typing import Dict, Any, Optional

from .base import PluginBase, PluginMeta


class NotifyPluginBase(PluginBase):
    """
    通知插件基类。
    用于实现邮件、Telegram、企业微信等通知渠道。
    """

    def __init__(self, meta: PluginMeta, config: Dict[str, Any]):
        super().__init__(meta, config)

    @abstractmethod
    async def send(
        self,
        title: str,
        content: str,
        to: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """
        发送通知。

        Args:
            title: 通知标题
            content: 通知内容
            to: 接收方（邮箱/Chat ID 等，为空则用插件配置的默认接收方）
        
        Returns:
            是否发送成功
        """
        pass
