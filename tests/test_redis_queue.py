import json

import redis.asyncio as redis

from app.config import settings
from app.models.job import JobPriority
from app.queue.redis_queue import RedisQueue


async def test_enqueue_high_priority_job():
    queue = RedisQueue(settings.redis_test_url)

    redis_client = redis.from_url(
        settings.redis_test_url,
        decode_responses=True,
    )

    queue_name = settings.queue_high

    await redis_client.delete(queue_name)

    await queue.enqueue(
        JobPriority.HIGH,
        {
            "job_id": "test-job-123",
            "job_type": "email",
        },
    )

    value = await redis_client.lpop(queue_name)

    assert value is not None

    data = json.loads(value)

    assert data["job_id"] == "test-job-123"
    assert data["job_type"] == "email"

    await redis_client.aclose()
    await queue.close()