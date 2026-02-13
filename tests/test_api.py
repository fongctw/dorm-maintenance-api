from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    db_path = Path("test.db")
    if db_path.exists():
        db_path.unlink()

    test_engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    if db_path.exists():
        db_path.unlink()


def test_ticket_flow_with_roles_and_transitions(client: TestClient) -> None:
    category_resp = client.post(
        "/categories",
        json={"name": "Electrical", "description": "Power related issues"},
    )
    assert category_resp.status_code == 201
    category_id = category_resp.json()["id"]

    ticket_resp = client.post(
        "/tickets",
        json={
            "title": "Air conditioner broken",
            "description": "The air conditioner has stopped cooling for two days.",
            "room": "A-1207",
            "priority": "high",
            "category_id": category_id,
        },
    )
    assert ticket_resp.status_code == 201
    ticket_id = ticket_resp.json()["id"]

    list_resp = client.get("/tickets", params={"status": "open", "limit": 5, "sort_by": "created_at"})
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["id"] == ticket_id

    by_id_resp = client.get(f"/tickets/{ticket_id}")
    assert by_id_resp.status_code == 200
    assert by_id_resp.json()["title"] == "Air conditioner broken"

    student_update = client.put(
        f"/tickets/{ticket_id}",
        headers={"X-Role": "student"},
        json={"description": "Updated details while still open and waiting for technician."},
    )
    assert student_update.status_code == 200
    assert student_update.json()["description"].startswith("Updated details")

    comment_resp = client.post(
        f"/tickets/{ticket_id}/comments",
        headers={"X-Role": "student"},
        json={"message": "Please come after 6 PM."},
    )
    assert comment_resp.status_code == 201
    assert comment_resp.json()["author_role"] == "student"

    status_update = client.put(
        f"/tickets/{ticket_id}/status",
        headers={"X-Role": "technician"},
        json={"status": "in_progress"},
    )
    assert status_update.status_code == 200
    assert status_update.json()["status"] == "in_progress"

    invalid_transition = client.put(
        f"/tickets/{ticket_id}/status",
        headers={"X-Role": "technician"},
        json={"status": "open"},
    )
    assert invalid_transition.status_code == 409
    assert invalid_transition.json()["code"] == "INVALID_STATUS_TRANSITION"

    student_status_update = client.put(
        f"/tickets/{ticket_id}/status",
        headers={"X-Role": "student"},
        json={"status": "done"},
    )
    assert student_status_update.status_code == 403
    assert student_status_update.json()["code"] == "FORBIDDEN"
