import pytest
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models.job import Job, JobPriority, JobStatus
from app.queue.redis_queue import RedisQueue
from app.services.retry_scheduler import RetryScheduler
from app.config import settings


async def create_job(
    session,
    status=JobStatus.FAILED,
    attempts=1,
    max_attempts=3,
    next_retry_at=None,
    priority=JobPriority.NORMAL,
):
    job = Job(
        job_type="email",
        payload={
            "to": "test@example.com",
        },
        status=status,
        priority=priority,
        attempts=attempts,
        max_attempts=max_attempts,
        next_retry_at=next_retry_at,
    )

    session.add(job)
    await session.commit()
    await session.refresh(job)

    return job


# ---------------------------------------------------------
# Due Retry Tests
# ---------------------------------------------------------


async def test_due_retry_is_scheduled(session):
    queue = RedisQueue(settings.redis_test_url)

    try:
        job = await create_job(
            session,
            next_retry_at=(
                datetime.now(timezone.utc)
                - timedelta(seconds=10)
            ),
        )

        scheduler = RetryScheduler(
            session=session,
            queue=queue,
        )

        count = await scheduler.schedule_due_retries()

        assert count == 1

        await session.refresh(job)

        assert job.status == JobStatus.QUEUED
        assert job.next_retry_at is None

    finally:
        await queue.close()


# ---------------------------------------------------------
# Future Retry Tests
# ---------------------------------------------------------


async def test_future_retry_is_not_scheduled(session):
    queue = RedisQueue(settings.redis_test_url)

    try:
        job = await create_job(
            session,
            next_retry_at=(
                datetime.now(timezone.utc)
                + timedelta(minutes=5)
            ),
        )

        scheduler = RetryScheduler(
            session=session,
            queue=queue,
        )

        count = await scheduler.schedule_due_retries()

        assert count == 0

        await session.refresh(job)

        assert job.status == JobStatus.FAILED
        assert job.next_retry_at is not None

    finally:
        await queue.close()


# ---------------------------------------------------------
# Jobs Without Retry Time
# ---------------------------------------------------------


async def test_job_without_retry_time_is_ignored(session):
    queue = RedisQueue(settings.redis_test_url)

    try:
        job = await create_job(
            session,
            next_retry_at=None,
        )

        scheduler = RetryScheduler(
            session=session,
            queue=queue,
        )

        count = await scheduler.schedule_due_retries()

        assert count == 0

        await session.refresh(job)

        assert job.status == JobStatus.FAILED
        assert job.next_retry_at is None

    finally:
        await queue.close()


# ---------------------------------------------------------
# Multiple Due Jobs
# ---------------------------------------------------------


async def test_multiple_due_retries_are_scheduled(session):
    queue = RedisQueue(settings.redis_test_url)

    try:
        job1 = await create_job(
            session,
            next_retry_at=(
                datetime.now(timezone.utc)
                - timedelta(seconds=10)
            ),
            priority=JobPriority.HIGH,
        )

        job2 = await create_job(
            session,
            next_retry_at=(
                datetime.now(timezone.utc)
                - timedelta(seconds=5)
            ),
            priority=JobPriority.LOW,
        )

        scheduler = RetryScheduler(
            session=session,
            queue=queue,
        )

        count = await scheduler.schedule_due_retries()

        assert count == 2

        await session.refresh(job1)
        await session.refresh(job2)

        assert job1.status == JobStatus.QUEUED
        assert job2.status == JobStatus.QUEUED

        assert job1.next_retry_at is None
        assert job2.next_retry_at is None

    finally:
        await queue.close()


# ---------------------------------------------------------
# Non-Failed Jobs
# ---------------------------------------------------------


async def test_non_failed_job_is_ignored(session):
    queue = RedisQueue(settings.redis_test_url)

    try:
        job = await create_job(
            session,
            status=JobStatus.DONE,
            next_retry_at=(
                datetime.now(timezone.utc)
                - timedelta(seconds=10)
            ),
        )

        scheduler = RetryScheduler(
            session=session,
            queue=queue,
        )

        count = await scheduler.schedule_due_retries()

        assert count == 0

        await session.refresh(job)

        assert job.status == JobStatus.DONE

    finally:
        await queue.close()