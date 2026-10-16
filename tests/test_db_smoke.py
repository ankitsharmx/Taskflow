from sqlalchemy import text

from app.models.job import Job


async def test_select_one(session):
    result = await session.execute(text("SELECT 1"))
    value = result.scalar_one()

    assert value == 1


async def test_postgres_version(session):
    result = await session.execute(text("SELECT version()"))
    version = result.scalar_one()

    assert "PostgreSQL" in version


async def test_create_and_read_job(session):
    job = Job(
        job_type="email",
        payload={
            "to": "user@example.com",
            "subject": "Hello TaskFlow",
        },
        status="PENDING",
    )

    session.add(job)
    await session.commit()
    await session.refresh(job)

    assert job.id is not None
    assert job.job_type == "email"
    assert job.payload["to"] == "user@example.com"
    assert job.status == "PENDING"

    result = await session.execute(
        text("SELECT job_type, status FROM jobs WHERE id = :job_id"),
        {"job_id": job.id},
    )

    row = result.one()

    assert row.job_type == "email"
    assert row.status == "PENDING"
