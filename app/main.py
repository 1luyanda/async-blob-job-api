from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app.database import create_tables, get_db
from app.models import Job, JobStatus
from app.schemas import HealthResponse, JobCreatedResponse, JobResponse
from app.tasks import process_job


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def job_to_response(job: Job) -> JobResponse:
    return JobResponse(
        job_id=job.id,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        error_message=job.error_message,
        json_blob_path=job.json_blob_path,
        json_blob_url=job.json_blob_url,
        parquet_blob_path=job.parquet_blob_path,
        parquet_blob_url=job.parquet_blob_url,
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title="Asynchronous Data Processing API",
    description="Queues dataset jobs to Celery and stores outputs in Azure Blob Storage.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.post(
    "/jobs",
    response_model=JobCreatedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_job(db: Session = Depends(get_db)) -> JobCreatedResponse:
    job = Job(status=JobStatus.PENDING.value, created_at=utc_now())
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        process_job.delay(job.id)
    except Exception as exc:
        job.status = JobStatus.FAILED.value
        job.finished_at = utc_now()
        job.error_message = f"Failed to queue job: {type(exc).__name__}: {exc}"
        db.commit()
        db.refresh(job)

    return JobCreatedResponse(
        job_id=job.id,
        status=job.status,
        created_at=job.created_at,
    )


@app.get("/jobs", response_model=list[JobResponse])
def list_jobs(db: Session = Depends(get_db)) -> list[JobResponse]:
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return [job_to_response(job) for job in jobs]


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)) -> JobResponse:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return job_to_response(job)
