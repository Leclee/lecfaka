"""
数据验证工具
"""

import re
from typing import Optional


def validate_phone(phone: str) -> bool:
    """
    验证中国大陆手机号
    """
    if not phone:
        return False
    
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))


def validate_email(email: str) -> bool:
    """
    验证邮箱格式
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_qq(qq: str) -> bool:
    """
    验证QQ号
    """
    if not qq:
        return False
    
    pattern = r'^[1-9]\d{4,11}$'
    return bool(re.match(pattern, qq))


def validate_contact(contact: str, contact_type: int) -> tuple[bool, str]:
    """
    根据类型验证联系方式
    
    Args:
        contact: 联系方式
        contact_type: 类型 0=任意 1=手机 2=邮箱 3=QQ
        
    Returns:
        (是否有效, 错误信息)
    """
    if not contact or len(contact.strip()) < 3:
        return False, "联系方式不能少于3个字符"
    
    contact = contact.strip()
    
    if contact_type == 1:
        if not validate_phone(contact):
            return False, "请输入正确的手机号"
    elif contact_type == 2:
        if not validate_email(contact):
            return False, "请输入正确的邮箱"
    elif contact_type == 3:
        if not validate_qq(contact):
            return False, "请输入正确的QQ号"
    
    return True, ""


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    验证密码强度
    
    Returns:
        (是否有效, 错误信息)
    """
    if len(password) < 6:
        return False, "密码长度不能少于6位"
    
    if len(password) > 50:
        return False, "密码长度不能超过50位"
    
    # 可选：更严格的密码要求
    # if not re.search(r'[A-Za-z]', password):
    #     return False, "密码必须包含字母"
    # if not re.search(r'\d', password):
    #     return False, "密码必须包含数字"
    
    return True, ""


def validate_username(username: str) -> tuple[bool, str]:
    """
    验证用户名
    
    Returns:
        (是否有效, 错误信息)
    """
    if len(username) < 3:
        return False, "用户名长度不能少于3位"
    
    if len(username) > 50:
        return False, "用户名长度不能超过50位"
    
    # 只允许字母数字下划线
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "用户名只能包含字母、数字和下划线"
    
    return True, ""


def sanitize_html(html: str) -> str:
    """
    简单的HTML清理（移除危险标签）
    生产环境建议使用专业库如 bleach
    """
    if not html:
        return ""
    
    # 移除 script 标签
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.IGNORECASE | re.DOTALL)
    
    # 移除 style 标签
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.IGNORECASE | re.DOTALL)
    
    # 移除事件处理器
    html = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)
    html = re.sub(r'\s*on\w+\s*=\s*[^\s>]+', '', html, flags=re.IGNORECASE)
    
    return html
