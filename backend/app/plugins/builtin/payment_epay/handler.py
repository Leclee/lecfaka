"""
易支付插件
支持页面跳转支付 (submit.php) 和 API接口支付 (mapi.php)
"""

import hashlib
from typing import Dict, Any
import httpx

from app.plugins.sdk.base import PluginMeta
from app.plugins.sdk.payment_base import (
    PaymentPluginBase,
    PaymentResult,
    PaymentType,
    CallbackResult,
)


class EpayPaymentPlugin(PaymentPluginBase):
    """易支付"""

    channels = {
        "alipay": "支付宝",
        "wxpay": "微信支付",
        "qqpay": "QQ钱包",
    }

    def __init__(self, meta: PluginMeta, config: Dict[str, Any]):
        super().__init__(meta, config)
        self.url = config.get("url", "").rstrip("/")
        self.pid = config.get("pid", "")
        self.key = config.get("key", "")
        self.use_mapi = config.get("use_mapi", False)

    def validate_config(self):
        errors = super().validate_config()
        if not self.url:
            errors.append("接口地址不能为空")
        if not self.pid:
            errors.append("商户ID不能为空")
        if not self.key:
            errors.append("商户密钥不能为空")
        return errors

    def _generate_sign(self, params: Dict[str, Any]) -> str:
        """
        MD5签名算法:
        1. 所有参数按参数名ASCII码从小到大排序 (a-z)
        2. sign、sign_type、空值不参与签名
        3. 拼接成 a=b&c=d&e=f 格式（参数值不URL编码）
        4. 末尾拼接商户密钥KEY后MD5
        """
        filtered = {
            k: v
            for k, v in params.items()
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
        **kwargs,
    ) -> PaymentResult:
        errors = self.validate_config()
        if errors:
            return PaymentResult(success=False, error_msg="; ".join(errors))

        # 从 kwargs 获取商品名称，没有则用订单号
        product_name = kwargs.get("product_name") or trade_no

        # 构建基础参数（严格按文档）
        params = {
            "pid": self.pid,
            "type": channel,
            "out_trade_no": trade_no,
            "notify_url": callback_url,
            "return_url": return_url,
            "name": product_name,
            "money": f"{amount:.2f}",
        }

        # ---- MAPI 模式: 通过API获取支付链接/二维码 ----
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
                        error_msg=result.get("msg", "支付请求失败"),
                    )

                # payurl -> 直接跳转
                if result.get("payurl"):
                    return PaymentResult(
                        success=True,
                        payment_type=PaymentType.REDIRECT,
                        payment_url=result["payurl"],
                    )

                # qrcode -> 二维码
                if result.get("qrcode"):
                    qrcode_val = result["qrcode"]
                    if qrcode_val.startswith("/"):
                        qrcode_val = f"{self.url}{qrcode_val}"
                    return PaymentResult(
                        success=True,
                        payment_type=PaymentType.QRCODE,
                        qrcode_url=qrcode_val,
                        extra={
                            "return_url": return_url,
                            "epay_trade_no": result.get("trade_no", ""),
                            "channel": channel,
                        },
                    )

                # img -> 二维码图片
                if result.get("img"):
                    img_val = result["img"]
                    if img_val.startswith("/"):
                        img_val = f"{self.url}{img_val}"
                    return PaymentResult(
                        success=True,
                        payment_type=PaymentType.QRCODE,
                        qrcode_url=img_val,
                        extra={
                            "return_url": return_url,
                            "epay_trade_no": result.get("trade_no", ""),
                            "channel": channel,
                        },
                    )

                return PaymentResult(
                    success=False, error_msg="未知的响应格式"
                )

            except Exception as e:
                self.logger.error(f"MAPI request failed: {e}")
                return PaymentResult(
                    success=False, error_msg=f"支付请求失败: {str(e)}"
                )

        # ---- 页面跳转模式: submit.php ----
        params["sign"] = self._generate_sign(params)
        params["sign_type"] = "MD5"

        # 文档要求: 参数值不要进行url编码，手动拼接查询字符串
        query_parts = []
        for k, v in params.items():
            query_parts.append(f"{k}={v}")
        redirect_url = f"{self.url}/submit.php?{'&'.join(query_parts)}"

        return PaymentResult(
            success=True,
            payment_type=PaymentType.REDIRECT,
            payment_url=redirect_url,
        )

    async def verify_callback(self, data: Dict[str, Any]) -> CallbackResult:
        """验证支付回调签名"""
        received_sign = data.get("sign", "")
        calculated_sign = self._generate_sign(data)

        if received_sign.lower() != calculated_sign.lower():
            self.logger.error(f"Signature mismatch: received={received_sign}, calculated={calculated_sign}")
            return CallbackResult(success=False, error_msg="签名验证失败")

        trade_status = data.get("trade_status", "")
        if trade_status != "TRADE_SUCCESS":
            return CallbackResult(
                success=False, error_msg=f"交易状态异常: {trade_status}"
            )

        try:
            amount = float(data.get("money", 0))
        except (ValueError, TypeError):
            return CallbackResult(success=False, error_msg="回调金额格式错误")
        
        return CallbackResult(
            success=True,
            trade_no=data.get("out_trade_no", ""),
            amount=amount,
            external_trade_no=data.get("trade_no", ""),
        )

    def get_callback_response(self, success: bool) -> str:
        return "success" if success else "fail"
