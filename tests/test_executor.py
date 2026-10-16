import pytest
from app.worker.executor import execute_job

async def test_email_job_executes():
    await execute_job(
        "email",
        {
            "to": "test@example.com",
        },
    )

async def test_unsupported_job_type_fails():
    with pytest.raises(
        ValueError,
        match="Unsupported job type",
    ):
        await execute_job(
            "unknown",
            {},
        )