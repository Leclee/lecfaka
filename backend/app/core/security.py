"""
安全相关工具
包含密码加密、JWT Token生成验证等
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt

from ..config import settings


def generate_salt(length: int = 16) -> str:
    """生成随机盐值"""
    return secrets.token_hex(length)


def get_password_hash(password: str, salt: str = None) -> tuple[str, str]:
    """
    生成密码哈希 (使用SHA256 + Salt)
    返回: (hash, salt)
    """
    if salt is None:
        salt = generate_salt()
    # 使用SHA256哈希，实际生产环境建议使用 argon2 或 bcrypt
    salted_password = f"{password}{salt}{settings.secret_key}"
    password_hash = hashlib.sha256(salted_password.encode()).hexdigest()
    return password_hash, salt


def verify_password(plain_password: str, hashed_password: str, salt: str) -> bool:
    """验证密码"""
    salted_password = f"{plain_password}{salt}{settings.secret_key}"
    check_hash = hashlib.sha256(salted_password.encode()).hexdigest()
    return check_hash == hashed_password


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """创建访问Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """创建刷新Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.jwt_refresh_token_expire_days
        )
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    验证Token
    返回: 解码后的payload 或 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None


def generate_trade_no() -> str:
    """生成18位订单号"""
    import time
    import random
    timestamp = int(time.time() * 1000)  # 13位毫秒时间戳
    random_part = random.randint(10000, 99999)  # 5位随机数
    return f"{timestamp}{random_part}"


def generate_api_key() -> str:
    """生成API密钥"""
    return secrets.token_urlsafe(32)
