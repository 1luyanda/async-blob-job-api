def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_job_returns_202_and_pending_record(client):
    response = client.post("/jobs")
    assert response.status_code == 202

    payload = response.json()
    assert payload["status"] == "pending"
    assert payload["job_id"]
    assert payload["created_at"]

    listed = client.get("/jobs")
    assert listed.status_code == 200
    jobs = listed.json()
    assert len(jobs) == 1
    assert jobs[0]["job_id"] == payload["job_id"]
    assert jobs[0]["status"] == "pending"


def test_list_jobs_newest_first(client):
    first = client.post("/jobs").json()
    second = client.post("/jobs").json()

    listed = client.get("/jobs")
    assert listed.status_code == 200
    jobs = listed.json()
    assert [job["job_id"] for job in jobs] == [second["job_id"], first["job_id"]]


def test_get_job_by_id(client):
    created = client.post("/jobs").json()
    response = client.get(f"/jobs/{created['job_id']}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"] == created["job_id"]
    assert payload["status"] == "pending"
    assert payload["started_at"] is None
    assert payload["finished_at"] is None
    assert payload["error_message"] is None
    assert payload["json_blob_path"] is None
    assert payload["parquet_blob_path"] is None


def test_unknown_job_returns_404(client):
    response = client.get("/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found."
