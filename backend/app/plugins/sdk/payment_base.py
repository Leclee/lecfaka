"""
支付插件基类
从原有 payments/base.py 迁移并增强
"""

from abc import abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from .base import PluginBase, PluginMeta


class PaymentType(Enum):
    """支付类型"""
    REDIRECT = "redirect"      # 跳转支付
    QRCODE = "qrcode"          # 二维码支付
    FORM = "form"              # 表单提交


@dataclass
class PaymentResult:
    """支付创建结果"""
    success: bool
    payment_type: PaymentType = PaymentType.REDIRECT
    payment_url: Optional[str] = None
    qrcode_url: Optional[str] = None
    form_data: Optional[Dict[str, Any]] = None
    form_action: Optional[str] = None
    error_msg: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CallbackResult:
    """支付回调结果"""
    success: bool
    trade_no: str = ""
    amount: float = 0.0
    external_trade_no: str = ""
    error_msg: Optional[str] = None


class PaymentPluginBase(PluginBase):
    """
    支付插件基类。
    所有支付方式插件需继承此类并实现抽象方法。

    与 PluginBase 的关系:
    - PluginBase 管理生命周期（安装/启用/禁用）
    - PaymentPluginBase 定义支付接口（创建支付/验证回调）
    """

    # 支持的支付通道 {"code": "名称"}
    channels: Dict[str, str] = {}

    def __init__(self, meta: PluginMeta, config: Dict[str, Any]):
        super().__init__(meta, config)

    @abstractmethod
    async def create_payment(
        self,
        trade_no: str,
        amount: float,
        callback_url: str,
        return_url: str,
        channel: str = None,
        client_ip: str = None,
        **kwargs,
    ) -> PaymentResult:
        """
        创建支付。

        Args:
            trade_no: 订单号
            amount: 支付金额
            callback_url: 异步回调 URL
            return_url: 同步跳转 URL
            channel: 支付通道
            client_ip: 客户端 IP
        """
        pass

    @abstractmethod
    async def verify_callback(self, data: Dict[str, Any]) -> CallbackResult:
        """验证支付回调"""
        pass

    @abstractmethod
    def get_callback_response(self, success: bool) -> str:
        """获取回调响应内容（返回给支付平台的字符串）"""
        pass
