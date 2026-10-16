from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all ORM models.

    Every model subclasses Base. Alembic autogenerate discovers models
    by importing this module's subclasses via `app.models`.
    """
    pass

"""
Base class for all ORM models. Base becomes the parent class for all SQLAlchemy models. Later if we create class job(Base):
This allows SQLAlchemy to register the model's table metadata. The metadata becomes important for Alembic.
Base
 │
 ├── Job
 ├── User
"""