from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)

from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo = False,
    pool_pre_ping = True,
    pool_size = 10,
    max_overflow = 20
)

"""
Creates the asynchronous SQLAlchemy engine. It uses DATABASE_URL i.e postgresql+asyncpg://taskflow:taskflow@postgres:5432/taskflow
database_dialect+driver://username:password@host:port/database_name  postgresql+asyncpg means use postgreSQL through the asyncpg driver.

pool_pre_ping = True: This option enables connection pool pre-ping. It checks the health of connections before using them, which helps prevent issues with stale or closed connections.
pool_size = 10: This sets the maximum number of connections that can be maintained in the connection pool. In this case, it allows up to 10 connections to be open simultaneously.
max_overflow = 20: This option specifies the maximum number of connections that can be created beyond the pool_size. In this case, it allows up to 20 additional connections to be created if the pool is exhausted. This can be useful for handling occasional spikes in database traffic.
"""


AsyncSessionLocal = async_sessionmaker(       #creates a factory for creating sessions.
    bind = engine,
    class_ = AsyncSession,
    expire_on_commit = False,          # Prevents the session from expiring objects after a commit. 
    autoflush = False
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency. Yields a session, gurantees close."""
    async with AsyncSessionLocal() as session:
        yield session