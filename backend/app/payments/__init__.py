"""
支付插件模块
"""

from .base import PaymentBase, PaymentResult, CallbackResult
from .epay import EpayPayment
from .usdt import USDTPayment
from .balance import BalancePayment

# 支付处理器注册表
PAYMENT_HANDLERS = {
    "epay": EpayPayment,
    "usdt": USDTPayment,
    "#balance": BalancePayment,  # 余额支付使用特殊标识
}


def get_payment_handler(handler: str):
    """获取支付处理器类"""
    return PAYMENT_HANDLERS.get(handler)


__all__ = [
    "PaymentBase",
    "PaymentResult",
    "CallbackResult",
    "EpayPayment",
    "USDTPayment",
    "BalancePayment",
    "PAYMENT_HANDLERS",
    "get_payment_handler",
]
