import pytest
import io
import datetime
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from backend.models import User, Club, ClubMembership, Event

client = TestClient(app)

def get_user_by_username(username: str) -> User:
    db = SessionLocal()
    u = db.query(User).filter(User.username == username).first()
    db.close()
    if not u:
        raise ValueError(f"User {username} not found")
    return u

def test_user_profile_photo_upload_for_every_member():
    """Any member/student can set and update their profile photo."""
    student = get_user_by_username("student_3")
    
    # 1. Upload profile photo via file
    fake_img = io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRfake_avatar_content")
    files = {"file": ("my_avatar.png", fake_img, "image/png")}
    
    res = client.post(
        "/api/users/profile-photo",
        headers={"x-user-id": str(student.id)},
        files=files
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "success"
    assert "avatar_url" in data
    assert data["avatar_url"].startswith("/uploads/avatars/")

    # 2. Update profile via PUT
    update_res = client.put(
        "/api/users/profile",
        headers={"x-user-id": str(student.id)},
        json={"name": "Kavya S. Updated", "phone": "+91 91111 22222"}
    )
    assert update_res.status_code == 200
    updated_user = update_res.json()["user"]
    assert updated_user["name"] == "Kavya S. Updated"
    assert updated_user["phone"] == "+91 91111 22222"

    # 3. Verify /api/auth/me returns updated avatar_url
    me_res = client.get("/api/auth/me", headers={"x-user-id": str(student.id)})
    assert me_res.status_code == 200
    assert me_res.json()["avatar_url"] == data["avatar_url"]

def test_president_club_logo_update():
    """
    Club Presidents can update their club's logo.
    Students without presidential authority receive 403 Forbidden.
    """
    db = SessionLocal()
    nextcell = db.query(Club).filter(Club.name.ilike("%Nextcell%")).first()
    db.close()
    assert nextcell is not None

    aarav_pres = get_user_by_username("aarav_lead")
    student = get_user_by_username("student_3")

    # 1. Non-president student attempts to update club logo -> 403 Forbidden
    fake_logo = io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRfake_logo_content")
    unauth_res = client.post(
        f"/api/clubs/{nextcell.id}/logo",
        headers={"x-user-id": str(student.id)},
        files={"file": ("unauth_logo.png", fake_logo, "image/png")}
    )
    assert unauth_res.status_code == 403
    assert "Only Club Presidents" in unauth_res.json()["detail"]

    # 2. President uploads new official club logo -> 200 OK
    pres_logo = io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRofficial_nextcell_logo")
    pres_res = client.post(
        f"/api/clubs/{nextcell.id}/logo",
        headers={"x-user-id": str(aarav_pres.id)},
        files={"file": ("nextcell_2026_logo.png", pres_logo, "image/png")}
    )
    assert pres_res.status_code == 200
    pres_data = pres_res.json()
    assert pres_data["status"] == "success"
    assert pres_data["logo_url"].startswith("/uploads/logos/")

    # 3. President updates via URL -> 200 OK
    url_res = client.put(
        f"/api/clubs/{nextcell.id}/logo",
        headers={"x-user-id": str(aarav_pres.id)},
        json={"logo_url": "https://miraisot.com/assets/nextcell_shield.png"}
    )
    assert url_res.status_code == 200
    assert url_res.json()["logo_url"] == "https://miraisot.com/assets/nextcell_shield.png"

def test_student_candidate_calendar_permissions():
    """
    Student candidate cannot change or publish important/common events,
    but CAN edit their personal calendar with private notes/reminders.
    """
    student = get_user_by_username("student_3")

    # 1. Student attempts to publish an IMPORTANT event -> 403 Forbidden
    unauth_payload = {
        "club_id": 1,
        "title": "Student Imposter Important Event",
        "description": "Student attempting to publish important event",
        "event_type": "IMPORTANT_DATE",
        "visibility": "PUBLIC",
        "is_important": True,
        "date": (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat(),
        "venue": "Main Stage"
    }
    unauth_res = client.post("/api/events", headers={"x-user-id": str(student.id)}, json=unauth_payload)
    assert unauth_res.status_code == 403
    assert "Student candidates cannot publish" in unauth_res.json()["detail"]

    # 2. Student adds a private personal note/reminder to their own calendar -> 200 OK
    note_payload = {
        "title": "Study Algorithm Complexity & Prep Pitch",
        "description": "Review Chapter 4 Big-O before Saturday session",
        "date": (datetime.datetime.utcnow() + datetime.timedelta(days=3)).isoformat(),
        "venue": "Library Study Room B",
        "deliverable_info": "Personal Milestone"
    }
    note_res = client.post(
        "/api/events/personal-note",
        headers={"x-user-id": str(student.id)},
        json=note_payload
    )
    assert note_res.status_code == 200
    note_data = note_res.json()
    assert note_data["status"] == "success"
    assert note_data["is_personal"] is True
    event_id = note_data["event_id"]

    # 3. Verify personal calendar contains this private note
    cal_res = client.get(f"/api/events/personal-calendar?user_id={student.id}", headers={"x-user-id": str(student.id)})
    assert cal_res.status_code == 200
    cal_data = cal_res.json()
    my_notes = [i for i in cal_data["items"] if i.get("category") == "PERSONAL_NOTE"]
    assert any(n["title"] == "Study Algorithm Complexity & Prep Pitch" for n in my_notes)

    # 4. Student can delete their own personal note -> 200 OK
    del_res = client.delete(f"/api/events/{event_id}", headers={"x-user-id": str(student.id)})
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"
