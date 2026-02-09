"""
辅助工具函数
"""

import time
import random
import string
import json
from typing import Any, Dict, Optional


def generate_trade_no() -> str:
    """
    生成18位订单号
    格式：13位时间戳 + 5位随机数
    """
    timestamp = int(time.time() * 1000)
    random_part = random.randint(10000, 99999)
    return f"{timestamp}{random_part}"


def generate_random_string(length: int = 16, chars: str = None) -> str:
    """
    生成随机字符串
    
    Args:
        length: 字符串长度
        chars: 可选字符集，默认为字母数字
    """
    if chars is None:
        chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def mask_string(s: str, show_start: int = 3, show_end: int = 4, mask_char: str = "*") -> str:
    """
    字符串脱敏
    
    Args:
        s: 原始字符串
        show_start: 显示前几位
        show_end: 显示后几位
        mask_char: 掩码字符
    """
    if not s or len(s) <= show_start + show_end:
        return s
    
    start = s[:show_start]
    end = s[-show_end:] if show_end > 0 else ""
    middle = mask_char * (len(s) - show_start - show_end)
    
    return start + middle + end


def parse_config(config_str: Optional[str]) -> Dict[str, Any]:
    """
    解析配置字符串（支持JSON和INI格式）
    
    原系统使用的INI风格配置格式：
    [category]
    标准版=10
    专业版=20
    
    [wholesale]
    10=9
    50=8
    """
    if not config_str:
        return {}
    
    # 尝试JSON解析
    try:
        return json.loads(config_str)
    except json.JSONDecodeError:
        pass
    
    # INI风格解析
    result = {}
    current_section = None
    
    for line in config_str.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith(';'):
            continue
        
        # 检测节
        if line.startswith('[') and line.endswith(']'):
            current_section = line[1:-1]
            result[current_section] = {}
            continue
        
        # 解析键值对
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # 尝试转换数值
            try:
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass
            
            if current_section:
                result[current_section][key] = value
            else:
                result[key] = value
    
    return result


def config_to_string(config: Dict[str, Any]) -> str:
    """
    将配置字典转换为字符串（INI格式）
    """
    lines = []
    
    for key, value in config.items():
        if isinstance(value, dict):
            lines.append(f"[{key}]")
            for k, v in value.items():
                lines.append(f"{k}={v}")
            lines.append("")
        else:
            lines.append(f"{key}={value}")
    
    return '\n'.join(lines)


def calculate_wholesale_price(
    base_price: float,
    quantity: int,
    wholesale_config: Dict[str, float]
) -> float:
    """
    计算批发价格
    
    Args:
        base_price: 基础价格
        quantity: 购买数量
        wholesale_config: 批发配置 {"数量": 价格}
    """
    if not wholesale_config:
        return base_price
    
    # 按数量降序排列
    thresholds = sorted(
        [(int(k), v) for k, v in wholesale_config.items()],
        key=lambda x: x[0],
        reverse=True
    )
    
    for min_qty, price in thresholds:
        if quantity >= min_qty:
            return float(price)
    
    return base_price


def format_money(amount: float) -> str:
    """格式化金额"""
    return f"¥{amount:.2f}"


def get_client_ip(request) -> str:
    """获取客户端IP"""
    # 尝试从代理头获取
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 直接连接
    if request.client:
        return request.client.host
    
    return "0.0.0.0"


def get_device_type(user_agent: str) -> int:
    """
    判断设备类型
    
    Returns:
        0: 未知
        1: 手机
        2: PC
        3: 微信
    """
    user_agent = user_agent.lower()
    
    if "micromessenger" in user_agent:
        return 3  # 微信
    
    mobile_keywords = [
        "mobile", "android", "iphone", "ipad", "ipod",
        "windows phone", "blackberry", "symbian"
    ]
    
    for keyword in mobile_keywords:
        if keyword in user_agent:
            return 1  # 手机
    
    return 2  # PC
