#!/usr/bin/env python
"""
数据库重置脚本
删除所有表并重新创建
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import engine, Base
from app.models import *  # 导入所有模型


async def reset_database():
    """重置数据库"""
    print("[1/3] Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("[OK] All tables dropped")
    
    print("[2/3] Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] All tables created")
    
    await engine.dispose()
    print("[3/3] Database reset complete!")


if __name__ == "__main__":
    asyncio.run(reset_database())
