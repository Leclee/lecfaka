"""
操作日志模型
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .user import User


class OperationLog(Base):
    """操作日志"""
    __tablename__ = "operation_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 操作用户
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, comment="用户ID"
    )
    
    # 用户邮箱（冗余存储）
    email: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="用户邮箱"
    )
    
    # 操作描述
    action: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="操作描述"
    )
    
    # IP地址
    ip: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True, comment="IP地址"
    )
    
    # 用户代理
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="User-Agent"
    )
    
    # 风险等级 0=无风险 1=风险较高
    risk_level: Mapped[int] = mapped_column(
        Integer, default=0, comment="风险等级 0=无风险 1=高风险"
    )
    
    # 详细数据（JSON）
    detail: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="详细数据"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, comment="操作时间"
    )
    
    # 关系
    user: Mapped[Optional["User"]] = relationship("User")
    
    # 索引
    __table_args__ = (
        Index("idx_operation_logs_user_id", "user_id"),
        Index("idx_operation_logs_created_at", "created_at"),
        Index("idx_operation_logs_risk_level", "risk_level"),
    )
    
    def __repr__(self) -> str:
        return f"<OperationLog {self.id}>"
