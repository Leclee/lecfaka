"""
易支付实现
支持页面跳转支付 (submit.php) 和 API接口支付 (mapi.php)
"""

import hashlib
from typing import Dict, Any
import httpx

from .base import PaymentBase, PaymentResult, PaymentType, CallbackResult


class EpayPayment(PaymentBase):
    """易支付"""
    
    name = "易支付"
    channels = {
        "alipay": "支付宝",
        "wxpay": "微信支付",
        "qqpay": "QQ钱包",
        "usdt": "USDT",
    }
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.url = config.get("url", "").rstrip("/")
        self.pid = config.get("pid", "")
        self.key = config.get("key", "")
        self.use_mapi = config.get("use_mapi", False)
    
    def validate_config(self) -> bool:
        return bool(self.url and self.pid and self.key)
    
    def _generate_sign(self, params: Dict[str, Any]) -> str:
        """MD5签名: 按key排序, 过滤空值和sign/sign_type, 拼接后加KEY做MD5"""
        filtered = {
            k: v for k, v in params.items()
            if v is not None and str(v) != "" and k not in ("sign", "sign_type")
        }
        sorted_params = sorted(filtered.items())
        sign_str = "&".join(f"{k}={v}" for k, v in sorted_params)
        sign_str += self.key
        return hashlib.md5(sign_str.encode("utf-8")).hexdigest()
    
    async def create_payment(
        self,
        trade_no: str,
        amount: float,
        callback_url: str,
        return_url: str,
        channel: str = "alipay",
        client_ip: str = None,
        **kwargs
    ) -> PaymentResult:
        if not self.validate_config():
            return PaymentResult(success=False, error_msg="支付配置不完整")
        
        channel = (channel or "alipay").strip().lower()
        product_name = kwargs.get("product_name") or trade_no
        
        params = {
            "pid": self.pid,
            "type": channel,
            "out_trade_no": trade_no,
            "notify_url": callback_url,
            "return_url": return_url,
            "name": product_name,
            "money": f"{amount:.2f}",
        }
        
        # MAPI 模式
        if self.use_mapi:
            try:
                params["clientip"] = client_ip or "127.0.0.1"
                params["sign"] = self._generate_sign(params)
                params["sign_type"] = "MD5"
                
                async with httpx.AsyncClient(verify=False) as client:
                    response = await client.post(
                        f"{self.url}/mapi.php", data=params, timeout=30
                    )
                    try:
                        result = response.json()
                    except (ValueError, Exception):
                        return PaymentResult(success=False, error_msg=f"支付平台响应格式错误: {response.text[:200]}")
                
                if result.get("code") != 1:
                    return PaymentResult(
                        success=False,
                        error_msg=result.get("msg", "支付请求失败")
                    )
                
                qrcode_val = result.get("qrcode") or result.get("img")
                if isinstance(qrcode_val, str) and qrcode_val:
                    if qrcode_val.startswith("/"):
                        qrcode_val = f"{self.url}{qrcode_val}"
                    return PaymentResult(
                        success=True,
                        payment_type=PaymentType.QRCODE,
                        qrcode_url=qrcode_val,
                        extra={"return_url": return_url, "epay_trade_no": result.get("trade_no", ""), "channel": channel}
                    )

                if result.get("payurl"):
                    payurl_val = result["payurl"]
                    if isinstance(payurl_val, str) and payurl_val.startswith("/"):
                        payurl_val = f"{self.url}{payurl_val}"
                    return PaymentResult(
                        success=True,
                        payment_type=PaymentType.REDIRECT,
                        payment_url=payurl_val
                    )
                
                if result.get("qrcode"):
                    qrcode_val = result["qrcode"]
                    if qrcode_val.startswith("/"):
                        qrcode_val = f"{self.url}{qrcode_val}"
                    return PaymentResult(
                        success=True,
                        payment_type=PaymentType.QRCODE,
                        qrcode_url=qrcode_val,
                        extra={"return_url": return_url, "epay_trade_no": result.get("trade_no", ""), "channel": channel}
                    )
                
                if result.get("img"):
                    img_val = result["img"]
                    if img_val.startswith("/"):
                        img_val = f"{self.url}{img_val}"
                    return PaymentResult(
                        success=True,
                        payment_type=PaymentType.QRCODE,
                        qrcode_url=img_val,
                        extra={"return_url": return_url, "epay_trade_no": result.get("trade_no", ""), "channel": channel}
                    )
                
                return PaymentResult(success=False, error_msg="未知的响应格式")
                
            except Exception as e:
                self._log(f"MAPI请求失败: {e}", "error")
                return PaymentResult(success=False, error_msg=f"支付请求失败: {str(e)}")
        
        # 页面跳转模式 (submit.php) - 文档要求参数值不要url编码
        params["sign"] = self._generate_sign(params)
        params["sign_type"] = "MD5"
        
        query_parts = []
        for k, v in params.items():
            query_parts.append(f"{k}={v}")
        redirect_url = f"{self.url}/submit.php?{'&'.join(query_parts)}"
        
        return PaymentResult(
            success=True,
            payment_type=PaymentType.REDIRECT,
            payment_url=redirect_url
        )
    
    async def verify_callback(self, data: Dict[str, Any]) -> CallbackResult:
        received_sign = data.get("sign", "")
        calculated_sign = self._generate_sign(data)
        
        if received_sign.lower() != calculated_sign.lower():
            self._log(f"签名验证失败: {data}", "error")
            return CallbackResult(success=False, error_msg="签名验证失败")
        
        trade_status = data.get("trade_status", "")
        if trade_status != "TRADE_SUCCESS":
            return CallbackResult(
                success=False,
                error_msg=f"交易状态异常: {trade_status}"
            )
        
        try:
            amount = float(data.get("money", 0))
        except (ValueError, TypeError):
            return CallbackResult(success=False, error_msg="回调金额格式错误")
        
        return CallbackResult(
            success=True,
            trade_no=data.get("out_trade_no", ""),
            amount=amount,
            external_trade_no=data.get("trade_no", "")
        )
    
    def get_callback_response(self, success: bool) -> str:
        return "success" if success else "fail"
