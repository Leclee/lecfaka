"""
管理后台 - 文件上传
"""

import os
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from ...deps import DbSession, CurrentAdmin


router = APIRouter()

# 允许的文件类型
ALLOWED_IMAGE_TYPES = {
    'image/jpeg': '.jpg',
    'image/png': '.png', 
    'image/gif': '.gif',
    'image/webp': '.webp',
    'image/x-icon': '.ico',
    'image/vnd.microsoft.icon': '.ico',
}

# 最大文件大小 (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024


def get_upload_dir() -> str:
    """获取上传目录"""
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def get_upload_subdir(category: str) -> str:
    """获取分类子目录"""
    upload_dir = get_upload_dir()
    subdir = os.path.join(upload_dir, category)
    os.makedirs(subdir, exist_ok=True)
    return subdir


@router.post("", summary="上传文件")
async def upload_file(
    admin: CurrentAdmin,
    file: UploadFile = File(...),
    category: str = Form(default="images"),
):
    """
    上传文件
    - category: 分类 (images, logos, backgrounds, icons)
    """
    # 检查文件类型
    content_type = file.content_type
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {content_type}，支持: {', '.join(ALLOWED_IMAGE_TYPES.keys())}"
        )
    
    # 读取文件内容
    content = await file.read()
    
    # 检查文件大小
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大，最大支持 {MAX_FILE_SIZE // 1024 // 1024}MB"
        )
    
    # 生成文件名
    ext = ALLOWED_IMAGE_TYPES[content_type]
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
    
    # 保存文件
    subdir = get_upload_subdir(category)
    filepath = os.path.join(subdir, filename)
    
    with open(filepath, "wb") as f:
        f.write(content)
    
    # 返回URL
    url = f"/api/v1/uploads/{category}/{filename}"
    
    return {
        "url": url,
        "filename": filename,
        "size": len(content),
        "content_type": content_type,
    }


@router.get("/{category}/{filename}", summary="获取文件")
async def get_file(
    category: str,
    filename: str,
):
    """获取上传的文件"""
    # 安全检查
    if ".." in category or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid path")
    
    subdir = get_upload_subdir(category)
    filepath = os.path.join(subdir, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(filepath)


@router.delete("/{category}/{filename}", summary="删除文件")
async def delete_file(
    category: str,
    filename: str,
    admin: CurrentAdmin,
):
    """删除上传的文件"""
    # 安全检查
    if ".." in category or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid path")
    
    subdir = get_upload_subdir(category)
    filepath = os.path.join(subdir, filename)
    
    if os.path.exists(filepath):
        os.remove(filepath)
    
    return {"message": "删除成功"}
