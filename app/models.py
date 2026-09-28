import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    status: Mapped[str] = mapped_column(String(20), default=JobStatus.PENDING.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    json_blob_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    json_blob_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    parquet_blob_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    parquet_blob_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
