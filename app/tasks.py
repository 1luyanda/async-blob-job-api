import io
from datetime import datetime, timedelta, timezone

import pandas as pd
from celery.signals import worker_ready

from app.celery_app import celery_app
from app.database import SessionLocal, create_tables
from app.models import Job, JobStatus
from app.storage import upload_job_outputs


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@worker_ready.connect
def _create_tables_on_worker_start(**_: object) -> None:
    create_tables()


def generate_sales_dataset(job_id: str, row_count: int = 40) -> pd.DataFrame:
    products = [
        ("WIDGET-100", "Widget", 19.99),
        ("GADGET-200", "Gadget", 49.50),
        ("CABLE-010", "USB-C Cable", 8.25),
        ("DOCK-300", "Laptop Dock", 129.00),
        ("MOUSE-050", "Wireless Mouse", 24.99),
    ]
    regions = ["London", "Manchester", "Birmingham", "Edinburgh", "Cardiff"]
    channels = ["web", "store", "partner"]
    started = utc_now() - timedelta(days=14)

    rows: list[dict[str, object]] = []
    for index in range(row_count):
        sku, product_name, unit_price = products[index % len(products)]
        quantity = (index % 5) + 1
        rows.append(
            {
                "job_id": job_id,
                "transaction_id": f"{job_id[:8]}-{index:04d}",
                "sku": sku,
                "product_name": product_name,
                "quantity": quantity,
                "unit_price_gbp": unit_price,
                "line_total_gbp": round(unit_price * quantity, 2),
                "region": regions[index % len(regions)],
                "channel": channels[index % len(channels)],
                "sold_at": (started + timedelta(hours=index * 3)).isoformat(),
            }
        )
    return pd.DataFrame(rows)


def dataframe_to_json_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_json(orient="records", date_format="iso").encode("utf-8")


def dataframe_to_parquet_bytes(frame: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    frame.to_parquet(buffer, engine="pyarrow", index=False)
    return buffer.getvalue()


def execute_job(job_id: str) -> None:
    """Process a job outside the FastAPI process. Failures are persisted."""
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is None:
            return

        job.status = JobStatus.RUNNING.value
        job.started_at = utc_now()
        job.error_message = None
        db.commit()

        try:
            frame = generate_sales_dataset(job_id)
            json_bytes = dataframe_to_json_bytes(frame)
            parquet_bytes = dataframe_to_parquet_bytes(frame)
            outputs = upload_job_outputs(job_id, json_bytes, parquet_bytes)

            job.status = JobStatus.COMPLETED.value
            job.finished_at = utc_now()
            job.json_blob_path = outputs["json_blob_path"]
            job.json_blob_url = outputs["json_blob_url"]
            job.parquet_blob_path = outputs["parquet_blob_path"]
            job.parquet_blob_url = outputs["parquet_blob_url"]
            db.commit()
        except Exception as exc:
            db.rollback()
            job = db.get(Job, job_id)
            if job is None:
                return
            job.status = JobStatus.FAILED.value
            job.finished_at = utc_now()
            job.error_message = f"{type(exc).__name__}: {exc}"
            db.commit()
    finally:
        db.close()


@celery_app.task(name="app.tasks.process_job")
def process_job(job_id: str) -> None:
    execute_job(job_id)
