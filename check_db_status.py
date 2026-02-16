
import asyncio
from sqlalchemy import create_async_engine, text
from sqlalchemy.ext.asyncio import AsyncSession

async def check():
    engine = create_async_engine('postgresql+asyncpg://thinkbank:thinkbank123@localhost:5432/thinkbank')
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, processing_status, file_name, caption FROM assets ORDER BY created_at DESC LIMIT 10"))
        rows = res.fetchall()
        print("Latest Assets:")
        for row in rows:
            print(f"ID: {row[0]} | Status: {row[1]} | File: {row[2]} | Caption: {row[3][:50] if row[3] else 'N/A'}")

if __name__ == '__main__':
    asyncio.run(check())
