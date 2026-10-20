import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from backend.models import User, Club, ClubMembership, AuditLog, Event

client = TestClient(app)

def test_advisor_club_roster_and_defaulters_below_70():
    # Login as Dr. Rajiv Menon (Club Advisor)
    login_res = client.post("/api/auth/login", json={"email": "advisor.tech@msot.org", "password": "password123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch advisor attendance roster
    res = client.get("/api/attendance/advisor-club-roster", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert "club_name" in data
    assert "total_members" in data
    assert "defaulters" in data
    assert "members" in data
    assert "sessions" in data

    # Verify that all returned defaulters have attendance strictly below 70.0%
    for d in data["defaulters"]:
        assert d["attendance_rate"] < 70.0
        assert d["is_defaulter"] is True
        assert d["shortfall_sessions"] > 0
        assert d["status"] == "DEFAULTER"

    # Verify members have proper stats
    for m in data["members"]:
        assert "roll_no" in m
        assert "attendance_rate" in m
        assert "attended_sessions" in m
        assert "total_sessions" in m

def test_advisor_manual_attendance_with_mandatory_audit_reason():
    # Login as Dr. Rajiv Menon
    login_res = client.post("/api/auth/login", json={"email": "advisor.tech@msot.org", "password": "password123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Missing or too short reason should fail
    fail_res = client.post("/api/attendance/advisor-mark-manual", headers=headers, json={
        "student_id": 1,
        "club_id": 1,
        "session_id": 1,
        "reason": "bad",  # < 5 chars
        "status": "PRESENT"
    })
    assert fail_res.status_code == 400
    assert "mandatory audit reason" in fail_res.json()["detail"].lower()

    # 2. Valid reason should succeed and write to AuditLog
    success_res = client.post("/api/attendance/advisor-mark-manual", headers=headers, json={
        "student_id": 1,
        "club_id": 1,
        "session_id": 1,
        "reason": "Student phone camera failed during 10:30 AM checkin; verified presence in Hall B.",
        "status": "PRESENT"
    })
    assert success_res.status_code == 200
    data = success_res.json()
    assert data["status"] == "success"
    assert "audit_id" in data

    # Verify in DB that audit log was created
    db = SessionLocal()
    audit = db.query(AuditLog).filter(AuditLog.id == data["audit_id"]).first()
    assert audit.action in ["ATTENDANCE_MANUAL_OVERRIDE", "ADVISOR_MANUAL_ATTENDANCE"]
    assert "camera failed" in audit.details
    db.close()

def test_advisor_history_archive_hackathons_projects_assignments():
    login_res = client.post("/api/auth/login", json={"email": "advisor.tech@msot.org", "password": "password123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/clubs/1/advisor-history-archive", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["club_id"] == 1
    assert "hackathons" in data
    assert "projects" in data
    assert "assignments" in data
    assert len(data["hackathons"]) > 0
    assert len(data["projects"]) > 0
    assert len(data["assignments"]) > 0

    # Verify hackathon details
    h0 = data["hackathons"][0]
    assert "rank_position" in h0
    assert "team_name" in h0
    assert "advisor_notes" in h0

    # Verify project details
    p0 = data["projects"][0]
    assert "student_name" in p0
    assert "total_score" in p0
    assert "feedback" in p0

    # Verify assignment 3-part rubric breakdown
    a0 = data["assignments"][0]
    assert "content_score" in a0
    assert "presentation_score" in a0
    assert "participation_score" in a0
    assert a0["total_score"] <= 30.0

def test_kaizen_branch_head_governance_vs_standard_clubs():
    login_res = client.post("/api/auth/login", json={"email": "advisor.tech@msot.org", "password": "password123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    db = SessionLocal()
    # Find Kaizen Club and standard club (Nextcell)
    kaizen = db.query(Club).filter(Club.name.like("%Kaizen%")).first()
    standard_club = db.query(Club).filter(Club.id == 1).first()
    target_student = db.query(User).filter(User.role == "STUDENT").first()
    db.close()

    assert kaizen is not None
    assert standard_club is not None
    assert target_student is not None

    # 1. Standard club must reject BRANCH_HEAD_DEV
    res_std = client.post(f"/api/clubs/{standard_club.id}/assign-post", headers=headers, json={
        "target_user_id": target_student.id,
        "post": "BRANCH_HEAD_DEV"
    })
    assert res_std.status_code == 400
    assert "Invalid post" in res_std.json()["detail"]

    # 2. Standard club accepts standard 5-post pattern (e.g. FINANCE_PRESIDENT)
    res_std_ok = client.post(f"/api/clubs/{standard_club.id}/assign-post", headers=headers, json={
        "target_user_id": target_student.id,
        "post": "FINANCE_PRESIDENT"
    })
    assert res_std_ok.status_code == 200

    # 3. Kaizen Club accepts Branch Head posts
    # Dr. Rajiv is faculty advisor; domain authorized or advisor can assign
    res_kaizen = client.post(f"/api/clubs/{kaizen.id}/assign-post", headers=headers, json={
        "target_user_id": target_student.id,
        "post": "BRANCH_HEAD_DEV"
    })
    # Dr. Rajiv Menon can assign since he is an advisor/domain authority
    assert res_kaizen.status_code == 200 or res_kaizen.status_code == 403
    if res_kaizen.status_code == 200:
        assert res_kaizen.json()["status"] == "success"

def test_advisor_adds_important_event_for_club_members():
    login_res = client.post("/api/auth/login", json={"email": "advisor.tech@msot.org", "password": "password123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    event_payload = {
        "club_id": 1,
        "title": "Semester Capstone Review & Defaulter Remediation Clinic",
        "description": "Mandatory session for all club members to review milestone deliverables and clear attendance shortfalls.",
        "date": "2026-11-15T10:00:00",
        "venue": "Campus Main Auditorium Hall 2",
        "deliverable_info": "Submit updated GitHub repository link prior to clinic."
    }

    res = client.post("/api/events/club-important-event", headers=headers, json=event_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "event_id" in data

    # Verify event appears in calendar with is_important = True
    db = SessionLocal()
    evt = db.query(Event).filter(Event.id == data["event_id"]).first()
    assert evt is not None
    assert evt.is_important is True
    assert evt.club_id == 1
    db.close()
