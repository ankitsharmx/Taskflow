import asyncio

from app.db.session import AsyncSessionLocal
from app.queue.redis_queue import RedisQueue
from app.services.retry_scheduler_runner import RetrySchedulerRunner


async def main() -> None:
    queue = RedisQueue()

    print("[retry-scheduler] process starting")

    try:
        async with AsyncSessionLocal() as session:
            runner = RetrySchedulerRunner(
                session=session,
                queue=queue,
                interval=1,
            )

            await runner.run()

    finally:
        await queue.close()


if __name__ == "__main__":
    asyncio.run(main())