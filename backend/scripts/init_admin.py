#!/usr/bin/env python
"""
初始化管理员账户脚本
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import async_session_maker
from app.models import User, Category, PaymentMethod
from app.core.security import get_password_hash


async def init_admin():
    """创建管理员账户和初始数据"""
    async with async_session_maker() as session:
        # 检查是否已存在管理员
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        if result.scalar_one_or_none():
            print("[Skip] Admin user already exists")
        else:
            # 创建管理员
            password_hash, salt = get_password_hash("admin123")
            admin = User(
                username="admin",
                email="admin@lecfaka.com",
                password_hash=password_hash,
                salt=salt,
                is_admin=True,
                status=1,
                balance=1000,
            )
            session.add(admin)
            print("[OK] Admin user created: admin / admin123")
        
        # 创建示例分类
        result = await session.execute(select(Category))
        if not result.scalars().first():
            categories = [
                Category(name="游戏账号", sort=1, status=1),
                Category(name="软件激活码", sort=2, status=1),
                Category(name="会员充值", sort=3, status=1),
                Category(name="虚拟物品", sort=4, status=1),
            ]
            session.add_all(categories)
            print("[OK] Sample categories created")
        else:
            print("[Skip] Categories already exist")
        
        # 创建余额支付方式
        result = await session.execute(
            select(PaymentMethod).where(PaymentMethod.handler == "#balance")
        )
        if not result.scalar_one_or_none():
            balance_pay = PaymentMethod(
                name="余额支付",
                handler="#balance",
                icon="/icons/balance.png",
                commodity=1,
                recharge=0,
                status=1,
                sort=0,
            )
            session.add(balance_pay)
            print("[OK] Balance payment method created")
        else:
            print("[Skip] Balance payment already exists")
        
        await session.commit()
        print("\n=== Init Complete ===")
        print("Admin Login: admin / admin123")


if __name__ == "__main__":
    asyncio.run(init_admin())
