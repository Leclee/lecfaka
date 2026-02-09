"""
自定义异常
"""

from typing import Any, Optional, Dict


class AppException(Exception):
    """应用基础异常"""
    
    def __init__(
        self,
        message: str = "Internal Server Error",
        code: int = 500,
        data: Optional[Any] = None
    ):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "data": self.data
        }


class AuthenticationError(AppException):
    """认证错误"""
    
    def __init__(self, message: str = "认证失败"):
        super().__init__(message=message, code=401)


class AuthorizationError(AppException):
    """授权错误"""
    
    def __init__(self, message: str = "权限不足"):
        super().__init__(message=message, code=403)


class NotFoundError(AppException):
    """资源不存在"""
    
    def __init__(self, message: str = "资源不存在"):
        super().__init__(message=message, code=404)


class ValidationError(AppException):
    """验证错误"""
    
    def __init__(self, message: str = "数据验证失败", data: Any = None):
        super().__init__(message=message, code=400, data=data)


class PaymentError(AppException):
    """支付错误"""
    
    def __init__(self, message: str = "支付失败"):
        super().__init__(message=message, code=400)


class InsufficientBalanceError(AppException):
    """余额不足"""
    
    def __init__(self, message: str = "余额不足"):
        super().__init__(message=message, code=400)


class StockError(AppException):
    """库存错误"""
    
    def __init__(self, message: str = "库存不足"):
        super().__init__(message=message, code=400)
