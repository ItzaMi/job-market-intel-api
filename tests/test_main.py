import pytest
from fastapi.testclient import TestClient

JOB_PAYLOAD = {
    "title": "Senior Backend Engineer",
    "description": "Build and scale our API platform",
    "salary": 100000,
    "location": "Remote",
    "company": "Acme Corp",
    "company_location": "San Francisco, CA",
}


def test_health(client: TestClient):
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_jobs_empty(client: TestClient):
    response = client.get("/jobs/")
    assert response.status_code == 200
    assert response.json() == []


def test_get_job_not_found(client: TestClient):
    response = client.get("/jobs/550e8400-e29b-41d4-a716-446655440000/")
    assert response.status_code == 404
    assert response.json() == {"detail": "Job not found"}


def test_create_job(client: TestClient):
    response = client.post("/jobs/", json=JOB_PAYLOAD)
    assert response.status_code == 200

    data = response.json()
    assert data.pop("id")
    assert data == JOB_PAYLOAD


def test_create_list_and_get_job(client: TestClient):
    create = client.post("/jobs/", json=JOB_PAYLOAD)
    job_id = create.json()["id"]

    listed = client.get("/jobs/")
    assert len(listed.json()) == 1
    assert listed.json()[0]["id"] == job_id

    fetched = client.get(f"/jobs/{job_id}/")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == JOB_PAYLOAD["title"]


def test_create_job_missing_required_field(client: TestClient):
    payload = {**JOB_PAYLOAD, "title": None}
    response = client.post("/jobs/", json=payload)
    assert response.status_code == 422


def test_create_job_invalid_payload(client: TestClient):
    payload = {**JOB_PAYLOAD, "salary": "invalid"}
    response = client.post("/jobs/", json=payload)
    assert response.status_code == 422


def test_list_multiple_jobs(client: TestClient):
    client.post("/jobs/", json=JOB_PAYLOAD)
    client.post("/jobs/", json={**JOB_PAYLOAD, "title": "Second Job"})
    assert len(client.get("/jobs/").json()) == 2


def test_delete_job(client: TestClient):
    create = client.post("/jobs/", json=JOB_PAYLOAD)
    job_id = create.json()["id"]

    delete = client.delete(f"/jobs/{job_id}/")
    assert delete.status_code == 200
    assert delete.json()["id"] == job_id
    assert len(client.get("/jobs/").json()) == 0


def test_delete_nonexistent_job(client: TestClient):
    response = client.delete("/jobs/550e8400-e29b-41d4-a716-446655440000/")
    assert response.status_code == 404


def test_filter_by_title(client: TestClient):
    client.post("/jobs/", json=JOB_PAYLOAD)
    client.post(
        "/jobs/",
        json={**JOB_PAYLOAD, "title": "Frontend Developer", "company": "Other Co"},
    )

    response = client.get("/jobs/", params={"title": "backend"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == JOB_PAYLOAD["title"]


def test_filter_by_company(client: TestClient):
    client.post("/jobs/", json=JOB_PAYLOAD)
    client.post(
        "/jobs/",
        json={**JOB_PAYLOAD, "title": "Other Role", "company": "StartupXYZ"},
    )

    response = client.get("/jobs/", params={"company": "acme"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["company"] == "Acme Corp"


def test_filter_by_location(client: TestClient):
    client.post("/jobs/", json=JOB_PAYLOAD)
    client.post(
        "/jobs/",
        json={**JOB_PAYLOAD, "title": "Local Role", "location": "Lisbon"},
    )

    response = client.get("/jobs/", params={"location": "remote"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["location"] == "Remote"


@pytest.mark.parametrize(
    ("salary", "salary_range", "decoy_salary", "expected_count"),
    [
        (35000, "under_40k", 100000, 1),
        (50000, "40k_60k", 100000, 1),
        (70000, "60k_80k", 100000, 1),
        (90000, "80k_plus", 50000, 1),
    ],
)
def test_filter_by_salary_range(
    client: TestClient,
    salary: int,
    salary_range: str,
    decoy_salary: int,
    expected_count: int,
):
    client.post("/jobs/", json={**JOB_PAYLOAD, "salary": salary})
    client.post(
        "/jobs/",
        json={**JOB_PAYLOAD, "title": "Other Job", "salary": decoy_salary},
    )

    response = client.get("/jobs/", params={"salary_range": salary_range})
    assert response.status_code == 200
    assert len(response.json()) == expected_count
    assert response.json()[0]["salary"] == salary


def test_pagination(client: TestClient):
    for index in range(3):
        client.post(
            "/jobs/",
            json={**JOB_PAYLOAD, "title": f"Job {index}"},
        )

    page = client.get("/jobs/", params={"limit": 2, "offset": 1})
    assert page.status_code == 200
    assert len(page.json()) == 2
