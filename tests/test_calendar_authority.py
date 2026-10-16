import pytest
import datetime
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from backend.models import User, Club, ClubMembership, Event, AssignmentProject

client = TestClient(app)

def get_user_by_username(username: str) -> User:
    db = SessionLocal()
    u = db.query(User).filter(User.username == username).first()
    db.close()
    if not u:
        raise ValueError(f"User {username} not found")
    return u

def test_common_calendar_public_read_access():
    """Common calendar must be viewable by anyone, with authority=False for guests."""
    res = client.get("/api/events/common-calendar")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["user_has_authority"] is False
    assert "events" in data
    assert isinstance(data["events"], list)

def test_common_calendar_authority_flag():
    """Verify authority flag accurately detects leadership vs regular student."""
    student = get_user_by_username("student_3")
    res_student = client.get("/api/events/common-calendar", headers={"x-user-id": str(student.id)})
    assert res_student.status_code == 200
    assert res_student.json()["user_has_authority"] is False

    admin = get_user_by_username("admin_alok")
    res_admin = client.get("/api/events/common-calendar", headers={"x-user-id": str(admin.id)})
    assert res_admin.status_code == 200
    assert res_admin.json()["user_has_authority"] is True
    assert len(res_admin.json()["authorized_clubs"]) >= 4

def test_common_calendar_scheduling_gating():
    """Only Presidents and Advisors can schedule Common Calendar events."""
    student = get_user_by_username("student_3")
    payload = {
        "club_id": 1,
        "title": "Unauthorized Student Event",
        "description": "Attempted by regular member",
        "event_type": "WORKSHOP",
        "visibility": "PUBLIC_CAMPUS",
        "date": (datetime.datetime.utcnow() + datetime.timedelta(days=5)).isoformat(),
        "venue": "Campus Grounds"
    }
    # Regular student -> 403 Forbidden
    res_student = client.post("/api/events", headers={"x-user-id": str(student.id)}, json=payload)
    assert res_student.status_code == 403
    assert "authority to add or update events on the Common Calendar" in res_student.json()["detail"]

    # Admin -> 200 OK
    admin = get_user_by_username("admin_alok")
    payload["title"] = "Authorized Leadership Summit"
    res_admin = client.post("/api/events", headers={"x-user-id": str(admin.id)}, json=payload)
    assert res_admin.status_code == 200
    assert res_admin.json()["title"] == "Authorized Leadership Summit"

def test_push_important_event_to_club_members_and_verify_personal_calendar():
    """
    Test user request:
    1. Only president and club advisor can add important event to club members.
    2. Student gets it in their personal calendar for their specific ID.
    """
    # 1. Regular student attempts to push an event -> 403 Forbidden
    student = get_user_by_username("student_3")
    push_payload = {
        "club_id": 1,
        "title": "Student Fake Push",
        "description": "Student trying to add event to members",
        "date": (datetime.datetime.utcnow() + datetime.timedelta(days=2)).isoformat(),
        "venue": "Nexcell Incubation Room"
    }
    res_stud = client.post("/api/events/club-important-event", headers={"x-user-id": str(student.id)}, json=push_payload)
    assert res_stud.status_code == 403
    assert "Only Club Presidents and Club Advisors" in res_stud.json()["detail"]

    # 2. Admin / President pushes important event -> 200 OK
    admin = get_user_by_username("admin_alok")
    push_payload["title"] = "⭐ Nexcell Mandatory Pitch Demo"
    push_payload["deliverable"] = "Bring working MVP prototype"
    res_admin = client.post("/api/events/club-important-event", headers={"x-user-id": str(admin.id)}, json=push_payload)
    assert res_admin.status_code == 200
    res_data = res_admin.json()
    assert res_data["title"] == "⭐ Nexcell Mandatory Pitch Demo"
    assert res_data["event_id"] is not None

    # 3. Enrolled student (student_3 is enrolled in Club 1) checks their personal calendar by their ID
    res_personal = client.get("/api/events/personal-calendar", headers={"x-user-id": str(student.id)})
    assert res_personal.status_code == 200
    p_data = res_personal.json()
    assert p_data["user_id"] == student.id
    assert p_data["user_name"] == student.name

    # Verify that the pushed important event is present in the student's personal calendar
    titles = [item["title"] for item in p_data["items"]]
    assert "⭐ Nexcell Mandatory Pitch Demo" in titles

    # Check the specific item properties
    matching = [i for i in p_data["items"] if i["title"] == "⭐ Nexcell Mandatory Pitch Demo"][0]
    assert matching["is_important"] is True
    assert matching["category"] == "CLUB_IMPORTANT_EVENT"
    assert matching["created_by_name"] == admin.name
