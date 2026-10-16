import json
from unittest.mock import AsyncMock

import redis.asyncio as redis
from sqlalchemy import select

from app.config import settings
from app.db.session import AsyncSessionLocal
from app.models.job import Job, JobPriority, JobStatus
from app.models.outbox import OutboxEvent
from app.queue.redis_queue import RedisQueue
from app.services.dispatcher import Dispatcher


async def test_redis_enqueue_can_happen_before_db_commit_failure(session):
    # ---------------------------------------------------------
    # 1. Create a job
    # ---------------------------------------------------------
    job = Job(
        job_type="email",
        payload={
            "to": "failure@example.com",
        },
        status=JobStatus.PENDING,
        priority=JobPriority.HIGH,
    )

    session.add(job)
    await session.flush()

    # ---------------------------------------------------------
    # 2. Create the corresponding outbox event
    # ---------------------------------------------------------
    event = OutboxEvent(
        job_id=job.id,
        event_type="JOB_CREATED",
        payload={
            "job_id": str(job.id),
            "job_type": job.job_type,
            "payload": job.payload,
            "priority": job.priority.value,
        },
    )

    session.add(event)

    await session.commit()
    await session.refresh(event)

    # IMPORTANT:
    # Save IDs before rollback.
    #
    # After rollback, SQLAlchemy may expire ORM attributes.
    # Accessing event.id or job.id afterward can trigger
    # unexpected database I/O.
    event_id = event.id
    job_id = job.id

    # ---------------------------------------------------------
    # 3. Start with an empty Redis queue
    # ---------------------------------------------------------
    redis_client = redis.from_url(
        settings.redis_test_url,
        decode_responses=True,
    )

    await redis_client.delete(settings.queue_high)

    queue = RedisQueue(settings.redis_test_url)

    dispatcher = Dispatcher(
        session=session,
        queue=queue,
    )

    # ---------------------------------------------------------
    # 4. Simulate PostgreSQL commit failure
    # ---------------------------------------------------------
    session.commit = AsyncMock(
        side_effect=RuntimeError(
            "simulated database failure"
        )
    )

    # ---------------------------------------------------------
    # 5. Dispatcher should fail at the DB commit
    # ---------------------------------------------------------
    try:
        await dispatcher.publish_one()

        # If we reach this line, the expected exception
        # did not happen.
        assert False, "Expected database failure"

    except RuntimeError as exc:
        assert str(exc) == "simulated database failure"

    # ---------------------------------------------------------
    # 6. Redis enqueue already happened
    # ---------------------------------------------------------
    value = await redis_client.lpop(
        settings.queue_high
    )

    assert value is not None

    data = json.loads(value)

    assert data["job_id"] == str(job_id)
    assert data["job_type"] == "email"
    assert data["priority"] == "HIGH"

    # ---------------------------------------------------------
    # 7. Roll back the failed SQLAlchemy transaction
    # ---------------------------------------------------------
    await session.rollback()

    # ---------------------------------------------------------
    # 8. Verify using a completely fresh DB session
    # ---------------------------------------------------------
    async with AsyncSessionLocal() as verify_session:
        result = await verify_session.execute(
            select(OutboxEvent).where(
                OutboxEvent.id == event_id
            )
        )

        stored_event = result.scalar_one()

        # Because the DB commit failed,
        # published_at was NOT persisted.
        assert stored_event.published_at is None

    # ---------------------------------------------------------
    # 9. Clean up Redis connections
    # ---------------------------------------------------------
    await redis_client.aclose()
    await queue.close()