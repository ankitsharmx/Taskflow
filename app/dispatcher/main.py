import asyncio

from pytest import main

from app.db.session import AsyncSessionLocal
from app.queue.redis_queue import RedisQueue
from app.services.dispatcher_runner import DispatcherRunner
async def main() -> None:
    queue = RedisQueue()
    async with AsyncSessionLocal() as session:
        runner = DispatcherRunner(
            session=session,
            queue=queue,
        )
        try:
            await runner.run()
        finally:
            await queue.close()

if __name__ == "__main__":
    asyncio.run(main())