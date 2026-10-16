from app.models.job import JobStatus


ALLOWED_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.PENDING: {
        JobStatus.QUEUED,
    },

    JobStatus.QUEUED: {
        JobStatus.RUNNING,
    },

    JobStatus.RUNNING: {
        JobStatus.DONE,
        JobStatus.FAILED,
    },

    JobStatus.FAILED: {
        JobStatus.QUEUED,
    },

    JobStatus.DONE: set(),
}


def can_transition(
    current: JobStatus,
    target: JobStatus,
) -> bool:
    return target in ALLOWED_TRANSITIONS[current]


def transition(
    current: JobStatus,
    target: JobStatus,
) -> JobStatus:
    if not can_transition(current, target):
        raise ValueError(
            f"Invalid job transition: "
            f"{current.value} -> {target.value}"
        )

    return target