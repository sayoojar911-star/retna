from datetime import datetime
from sqlalchemy import Column, DateTime, Integer
from backend.app.core.database import Base


class TimestampedModel(Base):
    """Abstract base model adding created_at and updated_at timestamps."""
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
