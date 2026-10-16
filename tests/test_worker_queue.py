import pytest

from app.config import settings
from app.models.job import JobPriority
from app.queue.redis_queue import RedisQueue


@pytest.mark.parametrize(
    "priority,queue_name",
    [
        (JobPriority.HIGH, settings.queue_high),
        (JobPriority.NORMAL, settings.queue_normal),
        (JobPriority.LOW, settings.queue_low),
    ],
)
async def test_dequeue_returns_job(
    priority,
    queue_name,
):
    queue = RedisQueue(settings.redis_test_url)

    await queue.redis.delete(
        settings.queue_high,
        settings.queue_normal,
        settings.queue_low,
    )

    job_data = {
        "job_id": "worker-test-123",
        "job_type": "email",
        "payload": {
            "to": "worker@example.com",
        },
        "priority": priority.value,
    }

    await queue.enqueue(
        priority,
        job_data,
    )

    result = await queue.dequeue()

    assert result is not None
    assert result["job_id"] == "worker-test-123"
    assert result["job_type"] == "email"
    assert result["priority"] == priority.value

    await queue.close()


async def test_high_priority_is_selected_first():
    queue = RedisQueue(settings.redis_test_url)

    await queue.redis.delete(
        settings.queue_high,
        settings.queue_normal,
        settings.queue_low,
    )

    await queue.enqueue(
        JobPriority.NORMAL,
        {
            "job_id": "normal-job",
            "priority": "NORMAL",
        },
    )

    await queue.enqueue(
        JobPriority.HIGH,
        {
            "job_id": "high-job",
            "priority": "HIGH",
        },
    )

    result = await queue.dequeue()

    assert result is not None
    assert result["job_id"] == "high-job"

    await queue.close()