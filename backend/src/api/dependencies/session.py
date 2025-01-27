from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repository.database import async_db, AsyncSession

async def get_async_session() -> AsyncSession:
    async with async_db.async_session() as session:
        try:
            yield session
        except Exception as e:
            print(e)
            await session.rollback()
            raise
        finally:
            await session.close()


