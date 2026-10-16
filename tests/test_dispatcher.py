import json
from datetime import datetime

import redis.asyncio as redis
from sqlalchemy import select

from app.config import settings
from app.models.job import Job, JobPriority, JobStatus
from app.models.outbox import OutboxEvent
from app.queue.redis_queue import RedisQueue
from app.services.dispatcher import Dispatcher


async def test_dispatcher_publishes_outbox_event(session):
    job = Job(
        job_type="email",
        payload={
            "to": "dispatcher@example.com",
        },
        status=JobStatus.PENDING,
        priority=JobPriority.HIGH,
    )

    session.add(job)
    await session.flush()

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

    published = await dispatcher.publish_one()

    assert published is True

    result = await session.execute(
        select(OutboxEvent).where(
            OutboxEvent.id == event.id
        )
    )

    published_event = result.scalar_one()

    assert published_event.published_at is not None
    assert isinstance(
        published_event.published_at,
        datetime,
    )

    value = await redis_client.lpop(
        settings.queue_high
    )

    assert value is not None

    data = json.loads(value)

    assert data["job_id"] == str(job.id)
    assert data["job_type"] == "email"
    assert data["priority"] == "HIGH"

    await redis_client.aclose()
    await queue.close()


async def test_dispatcher_returns_false_when_no_events(session):
    queue = RedisQueue(settings.redis_test_url)

    dispatcher = Dispatcher(
        session=session,
        queue=queue,
    )

    result = await dispatcher.publish_one()

    assert result is False

    await queue.close()