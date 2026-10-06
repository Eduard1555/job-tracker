import pytest
from fastapi.testclient import TestClient

from backend import database
from backend.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A test client backed by a fresh, empty database for every test."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    with TestClient(app) as test_client:  # "with" runs startup, which creates the table
        yield test_client


def add(client, company="Acme", role="Developer", status="Applied", date_applied="2026-10-01"):
    response = client.post(
        "/api/applications",
        json={"company": company, "role": role, "status": status, "date_applied": date_applied},
    )
    assert response.status_code == 201
    return response.json()


# --- Create ---

def test_create_application(client):
    created = add(client, company="Google", role="Backend Engineer", status="Interviewing")

    assert created["id"] == 1
    assert created["company"] == "Google"
    assert created["role"] == "Backend Engineer"
    assert created["status"] == "Interviewing"
    assert created["date_applied"] == "2026-10-01"


def test_create_defaults_status_to_applied(client):
    response = client.post(
        "/api/applications",
        json={"company": "Acme", "role": "Dev", "date_applied": "2026-10-01"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "Applied"


def test_create_trims_whitespace(client):
    created = add(client, company="  Acme  ", role="  Dev  ")
    assert created["company"] == "Acme"
    assert client.get("/api/applications").json()[0]["company"] == "Acme"


@pytest.mark.parametrize(
    "payload",
    [
        {"company": "", "role": "Dev", "date_applied": "2026-10-01"},                         # empty company
        {"company": "   ", "role": "Dev", "date_applied": "2026-10-01"},                      # only spaces
        {"company": "Acme", "role": "", "date_applied": "2026-10-01"},                        # empty role
        {"role": "Dev", "date_applied": "2026-10-01"},                                        # missing company
        {"company": "Acme", "role": "Dev"},                                                   # missing date
        {"company": "Acme", "role": "Dev", "date_applied": "2026-02-30"},                     # impossible date
        {"company": "Acme", "role": "Dev", "date_applied": "yesterday"},                      # not a date
        {"company": "Acme", "role": "Dev", "status": "Ghosted", "date_applied": "2026-10-01"},  # unknown status
    ],
)
def test_create_rejects_invalid_input(client, payload):
    response = client.post("/api/applications", json=payload)
    assert response.status_code == 422
    assert client.get("/api/applications").json() == []  # nothing was saved


# --- List and filter ---

def test_list_is_empty_at_start(client):
    response = client.get("/api/applications")
    assert response.status_code == 200
    assert response.json() == []


def test_list_is_sorted_newest_first(client):
    add(client, company="Old", date_applied="2026-09-01")
    add(client, company="New", date_applied="2026-10-05")
    add(client, company="Middle", date_applied="2026-09-20")

    companies = [a["company"] for a in client.get("/api/applications").json()]
    assert companies == ["New", "Middle", "Old"]


def test_list_shows_latest_added_first_within_the_same_day(client):
    add(client, company="Older day", date_applied="2026-10-06")
    add(client, company="First", date_applied="2026-10-07")
    add(client, company="Second", date_applied="2026-10-07")
    add(client, company="Just added", date_applied="2026-10-07")

    companies = [a["company"] for a in client.get("/api/applications").json()]
    assert companies == ["Just added", "Second", "First", "Older day"]


def test_filter_by_status(client):
    add(client, company="A", status="Applied")
    add(client, company="B", status="Rejected")
    add(client, company="C", status="Rejected")

    rejected = client.get("/api/applications", params={"status": "Rejected"}).json()
    assert sorted(a["company"] for a in rejected) == ["B", "C"]

    offers = client.get("/api/applications", params={"status": "Offer"}).json()
    assert offers == []


def test_filter_rejects_unknown_status(client):
    response = client.get("/api/applications", params={"status": "Ghosted"})
    assert response.status_code == 422


# --- Update status ---

def test_update_status(client):
    created = add(client, status="Applied")

    response = client.patch(f"/api/applications/{created['id']}", json={"status": "Offer"})
    assert response.status_code == 200
    assert response.json() == {**created, "status": "Offer"}  # only the status changed

    assert client.get("/api/applications").json()[0]["status"] == "Offer"


def test_update_status_rejects_unknown_status(client):
    created = add(client)
    response = client.patch(f"/api/applications/{created['id']}", json={"status": "Ghosted"})
    assert response.status_code == 422
    assert client.get("/api/applications").json()[0]["status"] == "Applied"  # unchanged


def test_update_status_of_missing_application_returns_404(client):
    response = client.patch("/api/applications/999", json={"status": "Offer"})
    assert response.status_code == 404


# --- Delete ---

def test_delete_application(client):
    keep = add(client, company="Keep")
    remove = add(client, company="Remove")

    response = client.delete(f"/api/applications/{remove['id']}")
    assert response.status_code == 204

    remaining = client.get("/api/applications").json()
    assert [a["id"] for a in remaining] == [keep["id"]]


def test_delete_missing_application_returns_404(client):
    response = client.delete("/api/applications/999")
    assert response.status_code == 404


def test_delete_twice_returns_404_the_second_time(client):
    created = add(client)
    assert client.delete(f"/api/applications/{created['id']}").status_code == 204
    assert client.delete(f"/api/applications/{created['id']}").status_code == 404


# --- Stats ---

def test_stats_on_empty_database(client):
    assert client.get("/api/stats").json() == {"total": 0, "rejected": 0, "waiting": 0}


def test_stats_counts_each_status_correctly(client):
    add(client, status="Applied")
    add(client, status="Applied")
    add(client, status="Interviewing")
    add(client, status="Offer")
    add(client, status="Rejected")

    # waiting = Applied + Interviewing; Offer counts toward total only
    assert client.get("/api/stats").json() == {"total": 5, "rejected": 1, "waiting": 3}


def test_stats_follow_status_changes_and_deletes(client):
    first = add(client, status="Applied")
    second = add(client, status="Applied")
    assert client.get("/api/stats").json() == {"total": 2, "rejected": 0, "waiting": 2}

    client.patch(f"/api/applications/{first['id']}", json={"status": "Rejected"})
    assert client.get("/api/stats").json() == {"total": 2, "rejected": 1, "waiting": 1}

    client.delete(f"/api/applications/{second['id']}")
    assert client.get("/api/stats").json() == {"total": 1, "rejected": 1, "waiting": 0}


# --- Frontend ---

def test_frontend_is_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Job Tracker" in response.text
