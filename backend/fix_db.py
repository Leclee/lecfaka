"""Fix payment method names and check data"""
import asyncio
from sqlalchemy import text
from app.database import async_session_maker


async def fix():
    async with async_session_maker() as db:
        # Fix payment method names
        await db.execute(text(
            "UPDATE payment_methods SET name='Balance' WHERE handler='#balance'"
        ))
        await db.execute(text(
            "UPDATE payment_methods SET name='WeChat' WHERE handler='payment_epay' AND code='wxpay'"
        ))
        await db.execute(text(
            "UPDATE payment_methods SET name='Alipay' WHERE handler='payment_epay' AND code='alipay'"
        ))
        await db.commit()
        
        # Show current state
        result = await db.execute(text(
            "SELECT id, name, handler, code, status FROM payment_methods ORDER BY id"
        ))
        rows = result.fetchall()
        for r in rows:
            print(f"  id={r[0]} name={r[1]} handler={r[2]} code={r[3]} status={r[4]}")


if __name__ == "__main__":
    asyncio.run(fix())
