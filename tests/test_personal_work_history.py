import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from backend.models import User, Submission, AttendanceRecord, Certificate, ClubMembership, ClubBudget

client = TestClient(app)

def get_user_by_username(username: str) -> User:
    db = SessionLocal()
    u = db.query(User).filter(User.username == username).first()
    db.close()
    if not u:
        raise ValueError(f"User {username} not found")
    return u

def test_work_history_unauthenticated_fails():
    """Accessing personal work history without credentials must return 401 Unauthorized."""
    res = client.get("/api/users/me/work-history")
    assert res.status_code in [401, 403], f"Expected 401/403, got {res.status_code}"

def test_work_history_privacy_isolation():
    """
    User A's work history contains only User A's data.
    User B cannot access or view User A's personal data.
    """
    student1 = get_user_by_username("student_1")
    student2 = get_user_by_username("student_2")

    # Fetch User 1 history
    res1 = client.get(
        "/api/users/me/work-history",
        headers={"x-user-id": str(student1.id)}
    )
    assert res1.status_code == 200, res1.text
    data1 = res1.json()
    assert data1["status"] == "success"
    assert data1["privacy"] == "CONFIDENTIAL_PERSONAL_DATA"
    assert data1["user"]["id"] == student1.id

    # Fetch User 2 history
    res2 = client.get(
        "/api/users/me/work-history",
        headers={"x-user-id": str(student2.id)}
    )
    assert res2.status_code == 200, res2.text
    data2 = res2.json()
    assert data2["status"] == "success"
    assert data2["user"]["id"] == student2.id

    # Verify no data leakage: IDs and titles are specific to the caller
    user1_history_ids = [item["id"] for item in data1["history"]]
    for item in data2["history"]:
        # If an item is an attendance or submission, it must not belong to user1
        if item["type"] in ["SUBMISSION", "ATTENDANCE"]:
            assert item["id"] not in user1_history_ids

def test_work_history_category_filter():
    """Category filtering returns only requested item types."""
    student = get_user_by_username("student_1")
    res = client.get(
        "/api/users/me/work-history?category=PROJECT_DELIVERABLE",
        headers={"x-user-id": str(student.id)}
    )
    assert res.status_code == 200
    data = res.json()
    for item in data["history"]:
        assert item["category"] == "PROJECT_DELIVERABLE" or item["type"] == "PROJECT_DELIVERABLE"
