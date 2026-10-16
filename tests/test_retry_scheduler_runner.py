from unittest.mock import AsyncMock

import pytest

from app.services.retry_scheduler_runner import (
    RetrySchedulerRunner,
)


@pytest.mark.asyncio
async def test_runner_initializes_scheduler(
    session,
):
    queue = AsyncMock()

    runner = RetrySchedulerRunner(
        session=session,
        queue=queue,
        interval=1,
    )

    assert runner.scheduler is not None
    assert runner.interval == 1