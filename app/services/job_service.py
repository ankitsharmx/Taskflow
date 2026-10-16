from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus
from app.services.job_state import transition
from app.services.retry import calculate_backoff


class JobService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_job(
        self,
        job_id: UUID,
    ) -> Job | None:

        result = await self.session.execute(
            select(Job).where(Job.id == job_id)
        )

        return result.scalar_one_or_none()

    async def transition_job(
        self,
        job_id: UUID,
        target_status: JobStatus,
    ) -> Job:

        job = await self.get_job(job_id)

        if job is None:
            raise ValueError(
                f"Job not found: {job_id}"
            )

        current_status = JobStatus(job.status)

        new_status = transition(
            current_status,
            target_status,
        )

        job.status = new_status

        await self.session.commit()
        await self.session.refresh(job)

        return job

    async def increment_attempts(
        self,
        job_id: UUID,
    ) -> Job:

        job = await self.get_job(job_id)

        if job is None:
            raise ValueError(
                f"Job not found: {job_id}"
            )

        job.attempts += 1

        await self.session.commit()
        await self.session.refresh(job)

        return job

    async def schedule_retry(
        self,
        job_id: UUID,
    ) -> Job:

        job = await self.get_job(job_id)

        if job is None:
            raise ValueError(
                f"Job not found: {job_id}"
            )

        if not self.can_retry(job):
            raise ValueError(
                f"Job has exhausted all retry attempts: {job_id}"
            )

        delay = calculate_backoff(job.attempts)

        job.next_retry_at = (
            datetime.now(timezone.utc)
            + timedelta(seconds=delay)
        )

        await self.session.commit()
        await self.session.refresh(job)

        return job

    async def list_jobs(self) -> list[Job]:

        result = await self.session.execute(
            select(Job)
            .order_by(Job.created_at.desc())
        )

        return list(result.scalars().all())

    def can_retry(self, job: Job) -> bool:
        return job.attempts < job.max_attempts