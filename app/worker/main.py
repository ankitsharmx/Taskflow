import asyncio
from uuid import UUID

from app.db.session import AsyncSessionLocal
from app.models.job import JobStatus
from app.queue.redis_queue import RedisQueue
from app.services.job_service import JobService
from app.worker.executor import execute_job


async def process_job(job_data: dict) -> None:
    job_id = UUID(job_data["job_id"])

    async with AsyncSessionLocal() as session:
        service = JobService(session)

        # Get the current job from PostgreSQL
        job = await service.get_job(job_id)

        if job is None:
            raise ValueError(f"Job not found: {job_id}")

        # New jobs start in PENDING.
        # They need to move to QUEUED first.
        if job.status == JobStatus.PENDING:
            await service.transition_job(
                job_id,
                JobStatus.QUEUED,
            )

        # A retry is already QUEUED.
        # Therefore, we should NOT do QUEUED -> QUEUED.
        elif job.status != JobStatus.QUEUED:
            raise ValueError(
                f"Job {job_id} is not executable "
                f"from status {job.status}"
            )

        # QUEUED -> RUNNING
        await service.transition_job(
            job_id,
            JobStatus.RUNNING,
        )

        # Count this execution attempt.
        job = await service.increment_attempts(job_id)

        try:
            await execute_job(
                job_data["job_type"],
                job_data["payload"],
                attempt=job.attempts,
            )

        except Exception:
            # RUNNING -> FAILED
            await service.transition_job(
                job_id,
                JobStatus.FAILED,
            )

            # Schedule another attempt if allowed.
            if service.can_retry(job):
                await service.schedule_retry(job_id)

            raise

        else:
            # RUNNING -> DONE
            await service.transition_job(
                job_id,
                JobStatus.DONE,
            )


async def run() -> None:
    queue = RedisQueue()

    print("[worker] starting")

    try:
        while True:
            job_data = await queue.dequeue()

            if job_data is None:
                continue

            print(
                f"[worker] received job "
                f"{job_data['job_id']}"
            )

            try:
                await process_job(job_data)

            except Exception as exc:
                print(f"[worker] job failed: {exc}")

    finally:
        await queue.close()


if __name__ == "__main__":
    asyncio.run(run())