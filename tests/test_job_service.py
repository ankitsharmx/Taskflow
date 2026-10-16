from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models.job import Job, JobPriority, JobStatus
from app.services.job_service import JobService


async def create_job(session):
    job = Job(
        job_type="email",
        payload={
            "to": "service@example.com",
        },
        status=JobStatus.PENDING,
        priority=JobPriority.NORMAL,
    )

    session.add(job)
    await session.commit()
    await session.refresh(job)

    return job


# ---------------------------------------------------------
# Job State Transition Tests
# ---------------------------------------------------------


async def test_transition_pending_to_queued(session):
    job = await create_job(session)

    service = JobService(session)

    updated_job = await service.transition_job(
        job.id,
        JobStatus.QUEUED,
    )

    assert updated_job.status == JobStatus.QUEUED


async def test_transition_queued_to_running(session):
    job = await create_job(session)

    service = JobService(session)

    await service.transition_job(
        job.id,
        JobStatus.QUEUED,
    )

    updated_job = await service.transition_job(
        job.id,
        JobStatus.RUNNING,
    )

    assert updated_job.status == JobStatus.RUNNING


async def test_transition_running_to_done(session):
    job = await create_job(session)

    service = JobService(session)

    await service.transition_job(
        job.id,
        JobStatus.QUEUED,
    )

    await service.transition_job(
        job.id,
        JobStatus.RUNNING,
    )

    updated_job = await service.transition_job(
        job.id,
        JobStatus.DONE,
    )

    assert updated_job.status == JobStatus.DONE


async def test_invalid_transition_is_rejected(session):
    job = await create_job(session)

    service = JobService(session)

    with pytest.raises(ValueError):
        await service.transition_job(
            job.id,
            JobStatus.RUNNING,
        )


async def test_done_job_cannot_transition(session):
    job = await create_job(session)

    service = JobService(session)

    await service.transition_job(
        job.id,
        JobStatus.QUEUED,
    )

    await service.transition_job(
        job.id,
        JobStatus.RUNNING,
    )

    await service.transition_job(
        job.id,
        JobStatus.DONE,
    )

    with pytest.raises(ValueError):
        await service.transition_job(
            job.id,
            JobStatus.RUNNING,
        )


async def test_missing_job_is_rejected(session):
    service = JobService(session)

    with pytest.raises(
        ValueError,
        match="Job not found",
    ):
        await service.transition_job(
            uuid4(),
            JobStatus.QUEUED,
        )


# ---------------------------------------------------------
# Attempt Counter Tests
# ---------------------------------------------------------


async def test_increment_attempts(session):
    job = Job(
        job_type="email",
        payload={
            "to": "test@example.com",
        },
        status=JobStatus.PENDING,
        priority=JobPriority.NORMAL,
        attempts=0,
        max_attempts=3,
    )

    session.add(job)
    await session.commit()
    await session.refresh(job)

    service = JobService(session)

    updated_job = await service.increment_attempts(
        job.id
    )

    assert updated_job.attempts == 1


async def test_increment_attempts_multiple_times(session):
    job = Job(
        job_type="email",
        payload={
            "to": "test@example.com",
        },
        status=JobStatus.PENDING,
        priority=JobPriority.NORMAL,
        attempts=0,
        max_attempts=3,
    )

    session.add(job)
    await session.commit()
    await session.refresh(job)

    service = JobService(session)

    await service.increment_attempts(job.id)
    await service.increment_attempts(job.id)

    updated_job = await service.increment_attempts(
        job.id
    )

    assert updated_job.attempts == 3


async def test_increment_attempts_missing_job(session):
    service = JobService(session)

    with pytest.raises(
        ValueError,
        match="Job not found",
    ):
        await service.increment_attempts(uuid4())


# ---------------------------------------------------------
# Retry Eligibility Tests
# ---------------------------------------------------------


async def test_can_retry_when_attempts_are_below_limit(session):
    job = Job(
        job_type="email",
        payload={
            "to": "test@example.com",
        },
        status=JobStatus.FAILED,
        priority=JobPriority.NORMAL,
        attempts=1,
        max_attempts=3,
    )

    session.add(job)
    await session.commit()
    await session.refresh(job)

    service = JobService(session)

    assert service.can_retry(job) is True


async def test_cannot_retry_when_attempts_reach_limit(session):
    job = Job(
        job_type="email",
        payload={
            "to": "test@example.com",
        },
        status=JobStatus.FAILED,
        priority=JobPriority.NORMAL,
        attempts=3,
        max_attempts=3,
    )

    session.add(job)
    await session.commit()
    await session.refresh(job)

    service = JobService(session)

    assert service.can_retry(job) is False


async def test_cannot_retry_when_attempts_exceed_limit(session):
    job = Job(
        job_type="email",
        payload={
            "to": "test@example.com",
        },
        status=JobStatus.FAILED,
        priority=JobPriority.NORMAL,
        attempts=4,
        max_attempts=3,
    )

    session.add(job)
    await session.commit()
    await session.refresh(job)

    service = JobService(session)

    assert service.can_retry(job) is False


# ---------------------------------------------------------
# Retry Scheduling Tests
# ---------------------------------------------------------


async def test_schedule_retry_sets_next_retry_at(session):
    before = datetime.now(timezone.utc)

    job = Job(
        job_type="email",
        payload={
            "to": "test@example.com",
        },
        status=JobStatus.FAILED,
        priority=JobPriority.NORMAL,
        attempts=1,
        max_attempts=3,
    )

    session.add(job)
    await session.commit()
    await session.refresh(job)

    service = JobService(session)

    updated_job = await service.schedule_retry(job.id)

    after = datetime.now(timezone.utc)

    assert updated_job.next_retry_at is not None

    expected_min = before + timedelta(seconds=1)
    expected_max = after + timedelta(seconds=1)

    assert (
        expected_min
        <= updated_job.next_retry_at
        <= expected_max
    )


async def test_schedule_retry_uses_exponential_backoff(
    session,
):
    job = Job(
        job_type="email",
        payload={
            "to": "test@example.com",
        },
        status=JobStatus.FAILED,
        priority=JobPriority.NORMAL,
        attempts=2,
        max_attempts=3,
    )

    session.add(job)
    await session.commit()
    await session.refresh(job)

    service = JobService(session)

    before = datetime.now(timezone.utc)

    updated_job = await service.schedule_retry(job.id)

    after = datetime.now(timezone.utc)

    assert updated_job.next_retry_at is not None

    expected_min = before + timedelta(seconds=2)
    expected_max = after + timedelta(seconds=2)

    assert (
        expected_min
        <= updated_job.next_retry_at
        <= expected_max
    )


async def test_schedule_retry_persists_to_database(
    session,
):
    job = Job(
        job_type="email",
        payload={
            "to": "test@example.com",
        },
        status=JobStatus.FAILED,
        priority=JobPriority.NORMAL,
        attempts=1,
        max_attempts=3,
    )

    session.add(job)
    await session.commit()
    await session.refresh(job)

    service = JobService(session)

    await service.schedule_retry(job.id)

    result = await session.execute(
        select(Job).where(Job.id == job.id)
    )

    saved_job = result.scalar_one()

    assert saved_job.next_retry_at is not None


async def test_schedule_retry_rejects_exhausted_job(
    session,
):
    job = Job(
        job_type="email",
        payload={
            "to": "test@example.com",
        },
        status=JobStatus.FAILED,
        priority=JobPriority.NORMAL,
        attempts=3,
        max_attempts=3,
    )

    session.add(job)
    await session.commit()
    await session.refresh(job)

    service = JobService(session)

    with pytest.raises(
        ValueError,
        match="exhausted all retry attempts",
    ):
        await service.schedule_retry(job.id)


async def test_schedule_retry_missing_job(session):
    service = JobService(session)

    with pytest.raises(
        ValueError,
        match="Job not found",
    ):
        await service.schedule_retry(uuid4())


async def test_exhausted_job_does_not_get_retry_time(
    session,
):
    job = Job(
        job_type="email",
        payload={
            "to": "test@example.com",
        },
        status=JobStatus.FAILED,
        priority=JobPriority.NORMAL,
        attempts=3,
        max_attempts=3,
        next_retry_at=None,
    )

    session.add(job)
    await session.commit()
    await session.refresh(job)

    service = JobService(session)

    with pytest.raises(
        ValueError,
        match="exhausted all retry attempts",
    ):
        await service.schedule_retry(job.id)

    assert job.next_retry_at is None