from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobPriority, JobStatus
from app.queue.redis_queue import RedisQueue
from app.services.job_service import JobService


class RetryScheduler:
    def __init__(
        self,
        session: AsyncSession,
        queue: RedisQueue,
    ) -> None:
        self.session = session
        self.queue = queue

    async def schedule_due_retries(self) -> int:
        now = datetime.now(timezone.utc)

        result = await self.session.execute(
            select(Job)
            .where(
                Job.status == JobStatus.FAILED,
                Job.next_retry_at.is_not(None),
                Job.next_retry_at <= now,
            )
            .order_by(Job.next_retry_at)
        )

        jobs = result.scalars().all()

        scheduled_count = 0
        service = JobService(self.session)

        for job in jobs:
            priority = JobPriority(job.priority)

            # FAILED -> QUEUED
            await service.transition_job(
                job.id,
                JobStatus.QUEUED,
            )

            await self.queue.enqueue(
                priority,
                {
                    "job_id": str(job.id),
                    "job_type": job.job_type,
                    "payload": job.payload,
                    "priority": priority.value,
                },
            )

            job.next_retry_at = None

            scheduled_count += 1

        if scheduled_count > 0:
            await self.session.commit()

        return scheduled_count