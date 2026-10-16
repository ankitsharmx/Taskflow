import uuid
import pytest
from sqlalchemy import select

from app.models.job import Job, JobStatus
from app.models.outbox import OutboxEvent

async def test_job_and_outbox_are_atomic(session):
    job_id = uuid.uuid4()
    job = Job(
        id=job_id,
        job_type="email",
        payload={
            "to": "rollback@example.com",
        },
        status=JobStatus.PENDING,
    )
    session.add(job)
    #Stimulate an invalid OutboxEvent
    #event_type is required, but we deliberately don't provide it.
    outbox_event = OutboxEvent(
        job_id=job_id,
        payload={
            "job_id": str(job_id)
        },
    )
    session.add(outbox_event)
    with pytest.raises(Exception):
        await session.commit()
    #the failed transaction must be rolled back
    await session.rollback()
    #job must not exist
    result = await session.execute(
        select(Job).where(Job.id == job_id)
    )
    assert result.scalar_one_or_none() is None

    #outbox_event must not exist
    result = await session.execute(
        select(OutboxEvent).where(OutboxEvent.job_id == job_id)
    )
    assert result.scalar_one_or_none() is None