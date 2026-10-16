import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.queue.redis_queue import RedisQueue
from app.services.retry_scheduler import RetryScheduler


class RetrySchedulerRunner:
    def __init__(
        self,
        session: AsyncSession,
        queue: RedisQueue,
        interval: int = 1,
    ) -> None:
        self.scheduler = RetryScheduler(
            session=session,
            queue=queue,
        )
        self.interval = interval

    async def run(self) -> None:
        print("[retry-scheduler] starting")

        while True:
            try:
                scheduled = (
                    await self.scheduler.schedule_due_retries()
                )

                if scheduled > 0:
                    print(
                        f"[retry-scheduler] "
                        f"scheduled {scheduled} retry(s)"
                    )
                else:
                    await asyncio.sleep(self.interval)

            except Exception as exc:
                print(
                    f"[retry-scheduler] error: {exc}"
                )
                await asyncio.sleep(self.interval)