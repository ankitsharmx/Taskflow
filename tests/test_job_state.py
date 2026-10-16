import pytest

from app.models.job import JobStatus
from app.services.job_state import can_transition, transition


def test_valid_transitions():
    assert can_transition(
        JobStatus.PENDING,
        JobStatus.QUEUED,
    )

    assert can_transition(
        JobStatus.QUEUED,
        JobStatus.RUNNING,
    )

    assert can_transition(
        JobStatus.RUNNING,
        JobStatus.DONE,
    )

    assert can_transition(
        JobStatus.RUNNING,
        JobStatus.FAILED,
    )

    assert can_transition(
        JobStatus.FAILED,
        JobStatus.QUEUED,
    )


def test_invalid_transitions():
    assert not can_transition(
        JobStatus.PENDING,
        JobStatus.DONE,
    )

    assert not can_transition(
        JobStatus.DONE,
        JobStatus.RUNNING,
    )

    assert not can_transition(
        JobStatus.DONE,
        JobStatus.QUEUED,
    )

    assert not can_transition(
        JobStatus.RUNNING,
        JobStatus.QUEUED,
    )


def test_transition_returns_new_state():
    new_status = transition(
        JobStatus.PENDING,
        JobStatus.QUEUED,
    )

    assert new_status == JobStatus.QUEUED


def test_invalid_transition_raises_error():
    with pytest.raises(ValueError):
        transition(
            JobStatus.DONE,
            JobStatus.RUNNING,
        )