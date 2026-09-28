from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobCreatedResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    status: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None
    json_blob_path: str | None = None
    json_blob_url: str | None = None
    parquet_blob_path: str | None = None
    parquet_blob_url: str | None = None


class HealthResponse(BaseModel):
    status: str = "healthy"
