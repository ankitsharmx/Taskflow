import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.queue.redis_queue import RedisQueue
from app.services.dispatcher import Dispatcher

class DispatcherRunner:
    def __init__(
        self,
        session: AsyncSession,
        queue: RedisQueue,
    ) -> None:
        self.dispatcher = Dispatcher(
            session=session,
            queue=queue,
        )

    async def run(self) -> None:
        print("[dispatcher] starting")

        while True:
            try:
                published = await self.dispatcher.publish_one()

                if published:
                    print("[dispatcher] published event")
                else:
                    print("[dispatcher] no event to publish")
                    await asyncio.sleep(1)
            except Exception as exc:
                print(f"[dispatcher] error: {exc}")
                await asyncio.sleep(1)