import pytest
from sqlalchemy import select

from app.models.job import Job, JobPriority, JobStatus
from app.worker.main import process_job


async def create_job(
    session,
    job_type="email",
    attempts=0,
    max_attempts=3,
):
    job = Job(
        job_type=job_type,
        payload={
            "to": "test@example.com",
        },
        status=JobStatus.PENDING,
        priority=JobPriority.NORMAL,
        attempts=attempts,
        max_attempts=max_attempts,
    )

    session.add(job)
    await session.commit()
    await session.refresh(job)

    return job


async def get_job(
    session,
    job_id,
):
    result = await session.execute(
        select(Job).where(Job.id == job_id)
    )

    return result.scalar_one()


# ---------------------------------------------------------
# Successful Job Tests
# ---------------------------------------------------------


async def test_successful_job_reaches_done(session):
    job = await create_job(session)

    await process_job(
        {
            "job_id": str(job.id),
            "job_type": "email",
            "payload": {
                "to": "test@example.com",
            },
        }
    )

    await session.refresh(job)

    assert job.status == JobStatus.DONE
    assert job.attempts == 1
    assert job.next_retry_at is None


# ---------------------------------------------------------
# Retry Tests
# ---------------------------------------------------------


async def test_failed_job_schedules_retry(session):
    job = await create_job(
        session,
        job_type="unsupported",
        attempts=0,
        max_attempts=3,
    )

    with pytest.raises(
        ValueError,
        match="Unsupported job type",
    ):
        await process_job(
            {
                "job_id": str(job.id),
                "job_type": "unsupported",
                "payload": {},
            }
        )

    await session.refresh(job)

    assert job.status == JobStatus.FAILED
    assert job.attempts == 1
    assert job.next_retry_at is not None


async def test_failed_job_does_not_retry_when_exhausted(
    session,
):
    job = await create_job(
        session,
        job_type="unsupported",
        attempts=2,
        max_attempts=3,
    )

    with pytest.raises(
        ValueError,
        match="Unsupported job type",
    ):
        await process_job(
            {
                "job_id": str(job.id),
                "job_type": "unsupported",
                "payload": {},
            }
        )

    await session.refresh(job)

    assert job.status == JobStatus.FAILED
    assert job.attempts == 3
    assert job.next_retry_at is None


async def test_retry_attempt_increments_correctly(
    session,
):
    job = await create_job(
        session,
        job_type="unsupported",
        attempts=1,
        max_attempts=3,
    )

    with pytest.raises(
        ValueError,
        match="Unsupported job type",
    ):
        await process_job(
            {
                "job_id": str(job.id),
                "job_type": "unsupported",
                "payload": {},
            }
        )

    await session.refresh(job)

    assert job.attempts == 2
    assert job.status == JobStatus.FAILED
    assert job.next_retry_at is not None