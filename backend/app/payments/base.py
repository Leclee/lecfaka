"""
支付插件基类
定义支付接口的标准规范
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


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


class PaymentBase(ABC):
    """
    支付插件基类
    所有支付方式需要继承此类并实现抽象方法
    """
    
    # 支付方式名称
    name: str = "未知支付"
    
    # 支持的通道 {"code": "名称"}
    channels: Dict[str, str] = {}
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化支付插件
        
        Args:
            config: 支付配置字典
        """
        self.config = config
    
    @abstractmethod
    async def create_payment(
        self,
        trade_no: str,
        amount: float,
        callback_url: str,
        return_url: str,
        channel: str = None,
        client_ip: str = None,
        **kwargs
    ) -> PaymentResult:
        """
        创建支付
        
        Args:
            trade_no: 订单号
            amount: 支付金额
            callback_url: 异步回调URL
            return_url: 同步跳转URL
            channel: 支付通道 (如 alipay, wxpay)
            client_ip: 客户端IP
            **kwargs: 其他参数
            
        Returns:
            PaymentResult: 支付结果
        """
        pass
    
    @abstractmethod
    async def verify_callback(self, data: Dict[str, Any]) -> CallbackResult:
        """
        验证支付回调
        
        Args:
            data: 回调数据
            
        Returns:
            CallbackResult: 验证结果
        """
        pass
    
    @abstractmethod
    def get_callback_response(self, success: bool) -> str:
        """
        获取回调响应内容
        
        Args:
            success: 是否处理成功
            
        Returns:
            str: 响应给支付平台的内容
        """
        pass
    
    def validate_config(self) -> bool:
        """
        验证配置是否完整
        子类可以重写此方法添加额外验证
        
        Returns:
            bool: 配置是否有效
        """
        return True
    
    def _log(self, message: str, level: str = "info") -> None:
        """记录日志"""
        # TODO: 实现日志记录
        print(f"[{level.upper()}] [{self.name}] {message}")
