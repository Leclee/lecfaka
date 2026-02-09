"""
USDT/TRC20 支付实现
支持USDT加密货币支付
"""

import hashlib
import time
from decimal import Decimal
from typing import Dict, Any, Optional

import httpx

from .base import PaymentBase, PaymentResult, PaymentType, CallbackResult


class USDTPayment(PaymentBase):
    """USDT TRC20 支付"""
    
    name = "USDT支付"
    channels = {
        "trc20": "TRC20",
    }
    
    # 汇率缓存
    _rate_cache: Optional[float] = None
    _rate_cache_time: float = 0
    RATE_CACHE_TTL = 300  # 汇率缓存5分钟
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.wallet_address = config.get("wallet_address", "")
        self.api_key = config.get("api_key", "")  # TRON API Key
        self.rate_api = config.get("rate_api", "")  # 汇率API
        self.fixed_rate = config.get("fixed_rate", 0)  # 固定汇率 (0则使用实时汇率)
        self.callback_secret = config.get("callback_secret", "")  # 回调验证密钥
    
    def validate_config(self) -> bool:
        """验证配置"""
        return bool(self.wallet_address)
    
    async def _get_usdt_rate(self) -> float:
        """获取USDT汇率 (CNY/USDT)"""
        
        # 使用固定汇率
        if self.fixed_rate > 0:
            return self.fixed_rate
        
        # 检查缓存
        if (
            self._rate_cache is not None and
            time.time() - self._rate_cache_time < self.RATE_CACHE_TTL
        ):
            return self._rate_cache
        
        # 获取实时汇率
        try:
            if self.rate_api:
                async with httpx.AsyncClient() as client:
                    response = await client.get(self.rate_api, timeout=10)
                    data = response.json()
                    rate = float(data.get("rate", 7.0))
            else:
                # 默认使用Binance API
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://api.binance.com/api/v3/ticker/price",
                        params={"symbol": "USDTCNY"},
                        timeout=10
                    )
                    # Binance可能没有USDTCNY，使用默认汇率
                    rate = 7.0
            
            self._rate_cache = rate
            self._rate_cache_time = time.time()
            return rate
            
        except Exception as e:
            self._log(f"获取汇率失败: {e}", "error")
            return 7.0  # 默认汇率
    
    def _generate_unique_amount(self, amount: float, trade_no: str) -> float:
        """
        生成唯一金额 (通过添加微小尾数区分不同订单)
        """
        # 使用订单号生成唯一后缀 (0.01-0.99)
        hash_val = int(hashlib.md5(trade_no.encode()).hexdigest()[:4], 16)
        suffix = (hash_val % 99 + 1) / 100  # 0.01 - 0.99
        return round(amount + suffix / 100, 4)  # 精确到0.0001
    
    async def create_payment(
        self,
        trade_no: str,
        amount: float,
        callback_url: str,
        return_url: str,
        channel: str = "trc20",
        client_ip: str = None,
        **kwargs
    ) -> PaymentResult:
        """创建USDT支付"""
        
        if not self.validate_config():
            return PaymentResult(
                success=False,
                error_msg="支付配置不完整"
            )
        
        try:
            # 获取汇率
            rate = await self._get_usdt_rate()
            
            # 计算USDT金额
            usdt_amount = amount / rate
            
            # 添加唯一尾数
            usdt_amount = self._generate_unique_amount(usdt_amount, trade_no)
            
            # 过期时间 (30分钟)
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
                }
            )
            
        except Exception as e:
            self._log(f"创建USDT支付失败: {e}", "error")
            return PaymentResult(
                success=False,
                error_msg=f"创建支付失败: {str(e)}"
            )
    
    async def verify_callback(self, data: Dict[str, Any]) -> CallbackResult:
        """
        验证USDT支付回调
        注意: USDT支付通常需要后台轮询链上交易确认
        这里假设使用第三方服务推送回调
        """
        
        # 验证签名 (如果配置了回调密钥)
        if self.callback_secret:
            received_sign = data.get("sign", "")
            sign_data = {k: v for k, v in data.items() if k != "sign"}
            sign_str = "&".join(f"{k}={v}" for k, v in sorted(sign_data.items()))
            sign_str += self.callback_secret
            calculated_sign = hashlib.md5(sign_str.encode()).hexdigest()
            
            if received_sign.lower() != calculated_sign.lower():
                return CallbackResult(
                    success=False,
                    error_msg="签名验证失败"
                )
        
        # 验证交易状态
        status = data.get("status", "")
        if status != "success":
            return CallbackResult(
                success=False,
                error_msg=f"交易状态异常: {status}"
            )
        
        return CallbackResult(
            success=True,
            trade_no=data.get("trade_no", ""),
            amount=float(data.get("amount", 0)),  # CNY金额
            external_trade_no=data.get("txid", "")  # 链上交易ID
        )
    
    def get_callback_response(self, success: bool) -> str:
        """获取回调响应"""
        return "success" if success else "fail"
    
    async def check_transaction(self, trade_no: str, usdt_amount: float) -> bool:
        """
        检查链上交易 (用于后台轮询)
        
        Args:
            trade_no: 订单号
            usdt_amount: 预期的USDT金额
            
        Returns:
            bool: 是否已收到付款
        """
        if not self.api_key:
            return False
        
        try:
            # 查询TRC20 USDT交易
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.trongrid.io/v1/accounts/{self.wallet_address}/transactions/trc20",
                    headers={"TRON-PRO-API-KEY": self.api_key},
                    timeout=30
                )
                data = response.json()
            
            # USDT合约地址 (主网)
            usdt_contract = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
            
            for tx in data.get("data", []):
                # 检查是否是USDT转入
                if (
                    tx.get("token_info", {}).get("address") == usdt_contract and
                    tx.get("to") == self.wallet_address
                ):
                    # 检查金额 (精度6位)
                    tx_amount = float(tx.get("value", 0)) / 1000000
                    if abs(tx_amount - usdt_amount) < 0.001:
                        return True
            
            return False
            
        except Exception as e:
            self._log(f"检查链上交易失败: {e}", "error")
            return False
