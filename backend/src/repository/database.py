import pydantic
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config.manager import settings


class AsyncDatabase:
    def __init__(self) -> None:
        # Construct the URL components - note the postgresql+asyncpg:// scheme
        self.postgres_uri: pydantic.AnyUrl = pydantic.AnyUrl.build(
            scheme="postgresql+asyncpg",  # Changed from postgres to postgresql+asyncpg
            username=settings.DB_POSTGRES_USERNAME,
            password=settings.DB_POSTGRES_PASSWORD,
            host=settings.DB_POSTGRES_HOST,
            port=settings.DB_POSTGRES_PORT,
            path=settings.DB_POSTGRES_NAME,
        )

        self.async_engine: AsyncEngine = create_async_engine(
            url=str(self.postgres_uri),
            echo=settings.DB_ECHO_LOG,
        )

        self.async_session: sessionmaker = sessionmaker(
            bind=self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def get_db(self) -> AsyncSession:
        async with self.async_session() as session:
            yield session
            await session.commit()


async_db: AsyncDatabase = AsyncDatabase()
