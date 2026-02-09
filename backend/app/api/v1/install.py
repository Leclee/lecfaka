"""
安装向导 API
首次部署时通过 Web 页面完成管理员创建和基础配置。
数据库中存在管理员用户即视为已安装，安装接口自动关闭。
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ...database import get_db
from ...models.user import User
from ...models.config import SystemConfig
from ...core.security import get_password_hash
from ...core.exceptions import ValidationError

router = APIRouter()


# ============== Schemas ==============

class InstallStatusResponse(BaseModel):
    installed: bool
    app_version: str = "1.0.0"


class InstallRequest(BaseModel):
    admin_username: str = Field(..., min_length=3, max_length=50)
    admin_password: str = Field(..., min_length=6, max_length=50)
    admin_email: Optional[EmailStr] = Field(None)
    site_name: str = Field("LecFaka", max_length=100)


# ============== Helpers ==============

async def _is_installed(db: AsyncSession) -> bool:
    """检查是否已安装（是否存在管理员用户）"""
    result = await db.execute(
        select(User.id).where(User.is_admin == True).limit(1)
    )
    return result.scalar_one_or_none() is not None


# ============== APIs ==============

@router.get("/status", response_model=InstallStatusResponse, summary="检查安装状态")
async def install_status(db: AsyncSession = Depends(get_db)):
    """检查系统是否已安装。前端根据此接口决定显示安装向导还是正常页面。"""
    installed = await _is_installed(db)
    return InstallStatusResponse(installed=installed)


@router.post("", summary="执行安装")
async def do_install(
    request: InstallRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    执行首次安装：创建管理员用户 + 保存站点配置。
    仅在未安装时可调用，已安装后此接口返回 403。
    """
    if await _is_installed(db):
        raise ValidationError("系统已安装，无法重复安装")

    # 检查用户名是否存在
    result = await db.execute(
        select(User).where(User.username == request.admin_username)
    )
    if result.scalar_one_or_none():
        raise ValidationError("用户名已存在")

    # 创建管理员
    password_hash, salt = get_password_hash(request.admin_password)
    admin = User(
        username=request.admin_username,
        email=request.admin_email,
        password_hash=password_hash,
        salt=salt,
        is_admin=True,
        status=1,
        balance=0,
        coin=0,
        total_recharge=0,
        business_level=0,
    )
    db.add(admin)
    await db.flush()

    # 保存站点名称
    await SystemConfig.set_value(db, "site_name", request.site_name)

    await db.commit()

    return {
        "success": True,
        "message": "安装完成",
        "admin_username": request.admin_username,
    }
