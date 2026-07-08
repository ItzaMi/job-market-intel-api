import pytest
from fastapi.testclient import TestClient

from main import app, jobs

JOB_PAYLOAD = {
    "title": "Test Job",
    "description": "Test Description",
    "salary": 100000,
    "location": "Test Location",
    "company": "Test Company",
    "company_url": "https://test.com",
    "company_logo": "https://test.com/logo.png",
    "company_description": "Test Company Description",
    "company_location": "Test Company Location",
}


@pytest.fixture
def client():
    jobs.clear()
    return TestClient(app)


def test_health(client):
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_jobs(client):
    response = client.get("/jobs/")
    assert response.status_code == 200
    assert response.json() == []


def test_get_job(client):
    response = client.get("/jobs/1/")
    assert response.status_code == 404
    assert response.json() == {"detail": "Job not found"}


def test_create_job(client):
    response = client.post("/jobs/", json=JOB_PAYLOAD)
    assert response.status_code == 200

    data = response.json()
    assert data.pop("id")
    assert data == JOB_PAYLOAD

def test_create_list_and_get_job(client):
    create = client.post("/jobs/", json=JOB_PAYLOAD)
    job_id = create.json()["id"]

    listed = client.get("/jobs/")
    assert len(listed.json()) == 1
    assert listed.json()[0]["id"] == job_id

    fetched = client.get(f"/jobs/{job_id}/")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == JOB_PAYLOAD["title"]

def test_create_job_missing_required_field(client):
    payload = {**JOB_PAYLOAD, 'title': None}
    response = client.post("/jobs/", json=payload)
    assert response.status_code == 422

def test_create_job_invalid_payload(client):
    payload = {**JOB_PAYLOAD, 'salary': "invalid"}
    response = client.post("/jobs/", json=payload)
    assert response.status_code == 422

def test_list_multiple_jobs(client):
    client.post("/jobs/", json=JOB_PAYLOAD)
    client.post("/jobs/", json={**JOB_PAYLOAD, "title": "Second Job"})
    assert len(client.get("/jobs/").json()) == 2

def test_delete_job(client):
    create = client.post("/jobs/", json=JOB_PAYLOAD)
    job_id = create.json()["id"]

    delete = client.delete(f"/jobs/{job_id}/")
    assert delete.status_code == 200
    assert delete.json()["id"] == job_id
    assert len(client.get("/jobs/").json()) == 0

def test_delete_nonexistent_job(client):
    response = client.delete("/jobs/123/")
    assert response.status_code == 404