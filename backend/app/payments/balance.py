"""
余额支付实现
使用用户账户余额进行支付
"""

from typing import Dict, Any

from .base import PaymentBase, PaymentResult, PaymentType, CallbackResult


class BalancePayment(PaymentBase):
    """余额支付"""
    
    name = "余额支付"
    channels = {}
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
    
    def validate_config(self) -> bool:
        """余额支付不需要额外配置"""
        return True
    
    async def create_payment(
        self,
        trade_no: str,
        amount: float,
        callback_url: str,
        return_url: str,
        channel: str = None,
        client_ip: str = None,
        user_id: int = None,
        **kwargs
    ) -> PaymentResult:
        """
        余额支付
        注意: 实际的余额扣除在订单服务中处理
        这里只返回支付信息
        """
        
        if not user_id:
            return PaymentResult(
                success=False,
                error_msg="余额支付需要登录"
            )
        
        # 余额支付不需要跳转，直接返回成功
        # 实际的余额验证和扣除在OrderService中处理
        return PaymentResult(
            success=True,
            payment_type=PaymentType.REDIRECT,
            payment_url=return_url,
            extra={
                "payment_method": "balance",
                "user_id": user_id,
                "amount": amount,
            }
        )
    
    async def verify_callback(self, data: Dict[str, Any]) -> CallbackResult:
        """余额支付不需要回调验证"""
        return CallbackResult(
            success=True,
            trade_no=data.get("trade_no", ""),
            amount=float(data.get("amount", 0))
        )
    
    def get_callback_response(self, success: bool) -> str:
        """余额支付不需要回调响应"""
        return "success"
