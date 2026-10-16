import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, String, Text, func, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
class JobPriority(str,Enum):
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"

class JobStatus(str,Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    job_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    status: Mapped[JobStatus] = mapped_column(
        String(50),
        nullable=False,
        default=JobStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    priority: Mapped[JobPriority] = mapped_column(
        String(20),
        nullable=False,
        default=JobPriority.NORMAL,
    )
    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
    )
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

"""
We are defining jobs with id, job_type, payload, status, and created_at. The id is a UUID primary key that is generated automatically. The job_type is a string that indicates the type of job. The payload is a JSONB column that stores the job's data. The status is a string that indicates the job's current status (e.g., pending, in_progress, completed). The created_at is a timestamp that records when the job was created.
id are like 550e8400-e29b-41d4-a716-446655440000. UUIDs are useful for distributed systems because IDs don't have to come from one centralized sequential counter.
UUID = Globally unique identifier.
A job can have different data like email, url, product_id, quantity. Instead of creating seperate columns for each possible job payload, we store structured JSON.


Alembic
class Job(Base): does'nt automatically mean postgres will create a table for it. Alembic is used to manage database migrations. When we run alembic commands, it looks for models that inherit from Base and generates migration scripts based on the differences between the current database schema and the models defined in the code. Alembic uses the metadata from the Base class to determine what tables and columns should exist in the database.

Why migration
If version 1 : job(id,status), version 2 : job(id,status,priority). We have to do alter tabsle and add column. Instead of doing it manually, we use alembic to generate migration scripts that can be applied to the database. This ensures that the database schema is always in sync with the application's models and allows for version control of the database schema.
alembic init alembic : initializes a new Alembic environment in the project. It creates an alembic directory with configuration files and a versions directory for migration scripts.

We need alembic to know about Job through Base.metadata. That's why we create Base and models inherit from it. Alembic will compare SQLAlchemy metadata with current database schema and generate migrations.


"""