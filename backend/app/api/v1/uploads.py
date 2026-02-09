"""
文件访问接口（公开）
"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


router = APIRouter()


def get_upload_dir() -> str:
    """获取上传目录"""
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


@router.get("/{category}/{filename}", summary="获取上传的文件")
async def get_uploaded_file(
    category: str,
    filename: str,
):
    """获取上传的文件（公开访问）"""
    # 安全检查
    if ".." in category or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid path")
    
    upload_dir = get_upload_dir()
    filepath = os.path.join(upload_dir, category, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(filepath)
