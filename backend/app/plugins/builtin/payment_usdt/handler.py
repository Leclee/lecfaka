"""
USDT/TRC20 支付插件
从 payments/usdt.py 迁移为标准插件格式
"""

import hashlib
import time
from typing import Dict, Any, Optional

import httpx

from app.plugins.sdk.base import PluginMeta
from app.plugins.sdk.payment_base import (
    PaymentPluginBase,
    PaymentResult,
    PaymentType,
    CallbackResult,
)


class USDTPaymentPlugin(PaymentPluginBase):
    """USDT TRC20 支付"""

    channels = {"trc20": "TRC20"}

    _rate_cache: Optional[float] = None
    _rate_cache_time: float = 0
    RATE_CACHE_TTL = 300

    def __init__(self, meta: PluginMeta, config: Dict[str, Any]):
        super().__init__(meta, config)
        self.wallet_address = config.get("wallet_address", "")
        self.api_key = config.get("api_key", "")
        self.rate_api = config.get("rate_api", "")
        self.fixed_rate = config.get("fixed_rate", 0)
        self.callback_secret = config.get("callback_secret", "")

    def validate_config(self):
        errors = super().validate_config()
        if not self.wallet_address:
            errors.append("收款钱包地址不能为空")
        return errors

    async def _get_usdt_rate(self) -> float:
        if self.fixed_rate > 0:
            return self.fixed_rate

        if (
            self._rate_cache is not None
            and time.time() - self._rate_cache_time < self.RATE_CACHE_TTL
        ):
            return self._rate_cache

        try:
            if self.rate_api:
                async with httpx.AsyncClient() as client:
                    response = await client.get(self.rate_api, timeout=10)
                    data = response.json()
                    rate = float(data.get("rate", 7.0))
            else:
                rate = 7.0

            self._rate_cache = rate
            self._rate_cache_time = time.time()
            return rate
        except Exception as e:
            self.logger.error(f"Failed to get USDT rate: {e}")
            return 7.0

    def _generate_unique_amount(self, amount: float, trade_no: str) -> float:
        hash_val = int(hashlib.md5(trade_no.encode()).hexdigest()[:4], 16)
        suffix = (hash_val % 99 + 1) / 100
        return round(amount + suffix / 100, 4)

    async def create_payment(
        self,
        trade_no: str,
        amount: float,
        callback_url: str,
        return_url: str,
        channel: str = "trc20",
        client_ip: str = None,
        **kwargs,
    ) -> PaymentResult:
        errors = self.validate_config()
        if errors:
            return PaymentResult(success=False, error_msg="; ".join(errors))

        try:
            rate = await self._get_usdt_rate()
            usdt_amount = amount / rate
            usdt_amount = self._generate_unique_amount(usdt_amount, trade_no)
            expire_time = int(time.time()) + 1800

            return PaymentResult(
                success=True,
                payment_type=PaymentType.QRCODE,
                qrcode_url=self.wallet_address,
                extra={
                    "usdt_amount": usdt_amount,
                    "wallet_address": self.wallet_address,
                    "network": "TRC20",
                    "rate": rate,
                    "expire_time": expire_time,
                    "return_url": return_url,
                    "trade_no": trade_no,
                },
            )
        except Exception as e:
            self.logger.error(f"Create USDT payment failed: {e}")
            return PaymentResult(
                success=False, error_msg=f"创建支付失败: {str(e)}"
            )

    async def verify_callback(self, data: Dict[str, Any]) -> CallbackResult:
        if self.callback_secret:
            received_sign = data.get("sign", "")
            sign_data = {k: v for k, v in data.items() if k != "sign"}
            sign_str = "&".join(
                f"{k}={v}" for k, v in sorted(sign_data.items())
            )
            sign_str += self.callback_secret
            calculated_sign = hashlib.md5(sign_str.encode()).hexdigest()

            if received_sign.lower() != calculated_sign.lower():
                return CallbackResult(success=False, error_msg="签名验证失败")

        status = data.get("status", "")
        if status != "success":
            return CallbackResult(
                success=False, error_msg=f"交易状态异常: {status}"
            )

        return CallbackResult(
            success=True,
            trade_no=data.get("trade_no", ""),
            amount=float(data.get("amount", 0)),
            external_trade_no=data.get("txid", ""),
        )

    def get_callback_response(self, success: bool) -> str:
        return "success" if success else "fail"
