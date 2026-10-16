from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import app
from app.models.job import Job
from app.models.outbox import OutboxEvent


async def test_create_job(session):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/jobs",
            json={
                "job_type": "email",
                "payload": {
                    "to": "test@example.com",
                    "subject": "Test TaskFlow",
                },
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["job_type"] == "email"
    assert data["status"] == "PENDING"
    assert data["priority"] == "NORMAL"
    assert data["id"] is not None

    job_id = data["id"]

    # Verify Job exists in PostgreSQL.
    result = await session.execute(
        select(Job).where(Job.id == job_id)
    )

    job = result.scalar_one()

    assert str(job.id) == job_id
    assert job.status == "PENDING"
    assert job.priority == "NORMAL"

    # Verify OutboxEvent exists in PostgreSQL.
    result = await session.execute(
        select(OutboxEvent).where(
            OutboxEvent.job_id == job.id
        )
    )

    outbox_event = result.scalar_one()

    assert outbox_event.event_type == "JOB_CREATED"
    assert outbox_event.job_id == job.id
    assert outbox_event.payload["job_id"] == job_id
    assert outbox_event.payload["priority"] == "NORMAL"
    assert outbox_event.published_at is None


async def test_create_high_priority_job(session):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/jobs",
            json={
                "job_type": "email",
                "payload": {
                    "to": "important@example.com",
                },
                "priority": "HIGH",
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["priority"] == "HIGH"

    result = await session.execute(
        select(Job).where(Job.id == data["id"])
    )

    job = result.scalar_one()

    assert job.priority == "HIGH"

    # Verify the priority is also available to the dispatcher.
    result = await session.execute(
        select(OutboxEvent).where(
            OutboxEvent.job_id == job.id
        )
    )

    outbox_event = result.scalar_one()

    assert outbox_event.event_type == "JOB_CREATED"
    assert outbox_event.payload["priority"] == "HIGH"