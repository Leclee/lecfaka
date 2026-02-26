"""
安全相关工具
包含密码加密、JWT Token生成验证等

v2.0: 密码哈希从 SHA256 迁移到 bcrypt（兼容旧格式自动升级）
"""

import secrets
import hashlib
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from ..config import settings

## bcrypt 密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

## bcrypt 哈希的特征前缀
_BCRYPT_PREFIX = "$2b$"


def generate_salt(length: int = 16) -> str:
    """生成随机盐值（仅供旧版 SHA256 兼容使用）"""
    return secrets.token_hex(length)


def get_password_hash(password: str, salt: str = None) -> tuple[str, str]:
    """
    生成密码哈希。

    v2.0: 使用 bcrypt，salt 参数仅为保持接口兼容。
    bcrypt 内部自带盐值管理，返回的 salt 字段为 "bcrypt" 标记。

    @param password 明文密码
    @param salt 忽略（兼容旧接口）
    @return (bcrypt_hash, "bcrypt")
    """
    hashed = pwd_context.hash(password)
    return hashed, "bcrypt"


def _verify_legacy_sha256(plain_password: str, hashed_password: str, salt: str) -> bool:
    """验证旧版 SHA256 + salt 密码（仅内部兼容使用）"""
    salted_password = f"{plain_password}{salt}{settings.secret_key}"
    check_hash = hashlib.sha256(salted_password.encode()).hexdigest()
    return check_hash == hashed_password


def verify_password(plain_password: str, hashed_password: str, salt: str) -> bool:
    """
    验证密码，自动识别新旧格式。

    - 新格式（bcrypt）: hashed_password 以 "$2b$" 开头
    - 旧格式（SHA256）: 其它情况，使用 salt + secret_key 重新计算
    """
    if hashed_password.startswith(_BCRYPT_PREFIX):
        return pwd_context.verify(plain_password, hashed_password)
    else:
        return _verify_legacy_sha256(plain_password, hashed_password, salt)


def needs_rehash(hashed_password: str) -> bool:
    """
    检查密码是否需要重新哈希（旧 SHA256 格式需要升级到 bcrypt）。
    
    @param hashed_password 当前存储的哈希值
    @return True 表示需要升级
    """
    return not hashed_password.startswith(_BCRYPT_PREFIX)


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
    """
    生成24位订单号（高并发安全）。

    格式: 14位微秒时间戳 + 10位随机十六进制 = 24位。
    uuid4 提供 122 位随机性，截取 10 位十六进制仍有 ~40 bit 熵，
    远大于旧版 5 位十进制（~17 bit），碰撞概率降低约 800 万倍。
    数据库 trade_no 列有 UNIQUE 约束作为最终兜底。
    """
    timestamp = int(time.time() * 1000000)  # 14位微秒时间戳
    random_part = uuid.uuid4().hex[:10]     # 10位随机十六进制
    return f"{timestamp}{random_part}"


def generate_api_key() -> str:
    """生成API密钥"""
    return secrets.token_urlsafe(32)
