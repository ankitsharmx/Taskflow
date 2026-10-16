import json

import redis.asyncio as redis

from app.config import settings
from app.models.job import JobPriority


class RedisQueue:
    def __init__(
        self,
        redis_url: str | None = None,
    ) -> None:
        self.redis = redis.from_url(
            redis_url or settings.redis_url,
            decode_responses=True,
        )

    async def enqueue(
        self,
        priority: JobPriority,
        job_data: dict,
    ) -> None:
        queue_name = self._queue_name(priority)

        await self.redis.rpush(
            queue_name,
            json.dumps(job_data),
        )

    async def dequeue(self) -> dict | None:
        result = await self.redis.blpop(
            [
                settings.queue_high,
                settings.queue_normal,
                settings.queue_low,
            ],
            timeout=1,
        )

        if result is None:
            return None

        _, value = result

        return json.loads(value)

    async def close(self) -> None:
        await self.redis.aclose()

    @staticmethod
    def _queue_name(priority: JobPriority) -> str:
        if priority == JobPriority.HIGH:
            return settings.queue_high

        if priority == JobPriority.NORMAL:
            return settings.queue_normal

        if priority == JobPriority.LOW:
            return settings.queue_low

        raise ValueError(
            f"Unsupported priority: {priority}"
        )