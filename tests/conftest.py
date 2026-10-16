import pytest_asyncio
from sqlalchemy import delete

from app.db.session import AsyncSessionLocal, engine
from app.models.job import Job
from app.models.outbox import OutboxEvent


@pytest_asyncio.fixture
async def session():
    await engine.dispose()

    async with AsyncSessionLocal() as session:
        await session.execute(delete(OutboxEvent))
        await session.execute(delete(Job))
        await session.commit()

        yield session

        await session.rollback()

    await engine.dispose()