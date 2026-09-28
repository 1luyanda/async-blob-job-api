# Async Blob Job API

A FastAPI service that queues dataset jobs, processes them with Celery, tracks state in SQLite, and writes JSON plus Parquet outputs to Azure Blob Storage.

## What is implemented

- `POST /jobs` queues a job (`202` + pending record)
- `GET /jobs` lists jobs newest first
- `GET /jobs/{id}` returns status and blob paths
- Celery worker runs the job body
- JSON and Parquet uploaded to Azure Blob Storage when connection strings are set
- Health endpoint

## Technology stack

Python, FastAPI, Celery, Redis, SQLAlchemy, Azure Blob Storage, pandas, pyarrow, pytest.

```text
HTTP -> FastAPI -> SQLite job row -> Celery worker -> Azure Blob (JSON + Parquet)
```

## Installation (Windows PowerShell)

```powershell
cd path\to\async-blob-job-api
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill `.env`. Do not commit it.

| Variable | Purpose |
| --- | --- |
| `AZURE_JSON_STORAGE_CONNECTION_STRING` / `AZURE_JSON_STORAGE_CONTAINER` | JSON blobs |
| `AZURE_PARQUET_STORAGE_CONNECTION_STRING` / `AZURE_PARQUET_STORAGE_CONTAINER` | Parquet blobs |
| `AZURE_STORAGE_CONNECTION_STRING` / `AZURE_STORAGE_CONTAINER` | Single-account fallback |
| `DATABASE_URL` | Default `sqlite:///./jobs.db` |
| `CELERY_BROKER_URL` | Default Redis `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Default Redis |

## Run Redis

```powershell
docker compose up -d
```

## Run the API and worker

```powershell
uvicorn app.main:app --reload --port 8000
celery -A app.celery_app worker --loglevel=info --pool=solo
```

On Windows, `--pool=solo` avoids Celery prefork issues.

API docs: http://127.0.0.1:8000/docs

## Sample behaviour

```powershell
curl.exe -X POST http://127.0.0.1:8000/jobs
curl.exe http://127.0.0.1:8000/jobs
```

The create call returns `202` with `status: pending`. After the worker runs, the job record should include blob paths when Azure storage is configured.

## Tests

```powershell
pytest
```

API tests mock Celery `.delay` and use an in-memory SQLite database. They do not upload to Azure.

## Limitations

- Azure Blob Storage is required for real file output
- Redis (or another broker) is required for a live worker
- Blob storage and compute may incur cloud cost

## Attribution

Built by Luyanda Ndaba as academy coursework (Python async jobs / Azure storage). This repository is the runnable API, not written exam answers or named cloud accounts.
