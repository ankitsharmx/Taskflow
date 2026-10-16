import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.models.job import JobStatus, JobPriority
from datetime import datetime

class JobCreate(BaseModel):
    job_type: str
    payload: dict
    priority: JobPriority = JobPriority.NORMAL
    max_attempts: int = Field(default=3, ge=1)

class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_type: str
    payload: dict
    status: JobStatus
    priority: JobPriority
    attempts: int
    max_attempts: int
    next_retry_at: datetime | None