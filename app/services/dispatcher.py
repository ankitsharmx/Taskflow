from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import JobPriority
from app.models.outbox import OutboxEvent
from app.queue.redis_queue import RedisQueue


class Dispatcher:
    def __init__(
        self,
        session: AsyncSession,
        queue: RedisQueue,
    ) -> None:
        self.session = session
        self.queue = queue

    async def publish_one(self) -> bool:
        """
        Publish one unpublished outbox event to Redis.

        Returns:
            True  -> an event was published
            False -> no unpublished event was available
        """

        result = await self.session.execute(
            select(OutboxEvent)
            .where(
                OutboxEvent.published_at.is_(None)
            )
            .order_by(OutboxEvent.created_at)
            .limit(1)
        )

        event = result.scalar_one_or_none()

        if event is None:
            return False

        try:
            priority = JobPriority(
                event.payload["priority"]
            )

            await self.queue.enqueue(
                priority,
                event.payload,
            )

            event.published_at = datetime.now(
                timezone.utc
            )

            await self.session.commit()

            return True

        except Exception:
            await self.session.rollback()
            raise


"""
OutboxEvent -> Dispatcher reads event -> Publish to Redis -> Mark published_at -> COMMIT
If something fails, Exeption -> ROLLBACK
This prevents the SQLAlchemy session from being left in a failed transaction state.
Publish to Redis ✓
Mark published_at ✓
Commit ✗      Then the same event can be published again.
Therefore the dispatcher provides at-least-once delivery, not exactly-once delivery.
"""