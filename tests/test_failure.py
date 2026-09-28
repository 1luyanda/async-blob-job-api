from datetime import datetime, timezone
from unittest.mock import patch

from app.database import SessionLocal
from app.models import Job, JobStatus
from app.tasks import dataframe_to_parquet_bytes, execute_job, generate_sales_dataset


def _create_pending_job() -> str:
    db = SessionLocal()
    try:
        job = Job(status=JobStatus.PENDING.value, created_at=datetime.now(timezone.utc))
        db.add(job)
        db.commit()
        db.refresh(job)
        return job.id
    finally:
        db.close()


def test_failure_handling_marks_job_failed():
    job_id = _create_pending_job()

    with patch(
        "app.tasks.upload_job_outputs",
        side_effect=RuntimeError("Azure Blob Storage unavailable"),
    ):
        execute_job(job_id)

    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        assert job is not None
        assert job.status == JobStatus.FAILED.value
        assert job.started_at is not None
        assert job.finished_at is not None
        assert job.error_message is not None
        assert "Azure Blob Storage unavailable" in job.error_message
        assert job.json_blob_path is None
        assert job.parquet_blob_path is None
    finally:
        db.close()


def test_missing_job_does_not_raise():
    execute_job("00000000-0000-0000-0000-000000000000")


def test_dataset_generation_is_parquet_ready():
    frame = generate_sales_dataset("abc12345-test")
    assert len(frame) == 40
    assert "transaction_id" in frame.columns
    parquet_bytes = dataframe_to_parquet_bytes(frame)
    assert parquet_bytes.startswith(b"PAR1")
