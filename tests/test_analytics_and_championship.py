import pytest
import datetime
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from backend.models import User, Club, HackathonAchievement, ClubAdvisorAudit

client = TestClient(app)

def get_user_by_username(username: str) -> User:
    db = SessionLocal()
    u = db.query(User).filter(User.username == username).first()
    db.close()
    if not u:
        raise ValueError(f"User {username} not found")
    return u

def test_club_performance_tracker_dimensions():
    """
    Verifies that the club performance tracker monitors clubs across:
    1. Project completion rate (bache kitne poore kare)
    2. Hackathon achievements & ranks
    3. Activity & event execution
    4. Budget management efficiency
    """
    res = client.get("/api/analytics/club-performance-tracker?campus_id=1")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["total_clubs_tracked"] == 4

    club_names = [c["club_name"] for c in data["clubs"]]
    assert "Nextcell Club" in club_names
    assert "Kaizen Club" in club_names
    assert "Malhar Club" in club_names
    assert "Sports Club" in club_names

    # Check Nextcell dimensions
    nextcell = [c for c in data["clubs"] if c["club_name"] == "Nextcell Club"][0]
    assert "project_metrics" in nextcell
    assert "total_members" in nextcell["project_metrics"]
    assert "distinct_completed" in nextcell["project_metrics"]
    assert "completion_rate_pct" in nextcell["project_metrics"]

    assert "hackathon_metrics" in nextcell
    assert "achievements_list" in nextcell["hackathon_metrics"]
    assert nextcell["hackathon_metrics"]["total_achievements"] >= 1

    assert "activity_metrics" in nextcell
    assert "activity_execution_score" in nextcell["activity_metrics"]

    assert "budget_metrics" in nextcell
    assert "budget_governance_score" in nextcell["budget_metrics"]

    assert "composite_score" in nextcell
    assert 0 <= nextcell["composite_score"] <= 1000

def test_inter_campus_championship_joint_coalition():
    """
    Verifies that HIET's 4 clubs join forces and compete as a joint campus
    against other campuses (RIT, JU).
    """
    res = client.get("/api/analytics/inter-campus-championship")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["campuses_count"] >= 3

    campus_codes = [c["campus_code"] for c in data["leaderboard"]]
    assert "HIET" in campus_codes
    assert "RIT" in campus_codes
    assert "JU" in campus_codes

    hiet = [c for c in data["leaderboard"] if c["campus_code"] == "HIET"][0]
    assert hiet["is_home_campus"] is True
    assert "HIET 4-Clubs Joint Coalition" in hiet["joint_coalition_title"]
    assert len(hiet["clubs_contribution"]) == 4

    # Verify that all 4 HIET clubs are present in contribution breakdown
    hiet_contrib_names = [c["club_name"] for c in hiet["clubs_contribution"]]
    assert "Nextcell Club" in hiet_contrib_names
    assert "Kaizen Club" in hiet_contrib_names
    assert "Malhar Club" in hiet_contrib_names
    assert "Sports Club" in hiet_contrib_names

    # Verify championship ranks
    ranks = [c["rank"] for c in data["leaderboard"]]
    assert ranks == [1, 2, 3]

def test_respective_club_advisor_authority_gating():
    """
    Verifies that only the designated Faculty Advisor of each respective club
    can record hackathon ranks and audit club performance.
    """
    student = get_user_by_username("student_3")
    advisor_nextcell = get_user_by_username("advisor_menon") # User 3, Advisor for Club 1 (Nextcell)
    advisor_kaizen = get_user_by_username("advisor_sen")     # User 4, Advisor for Club 2 (Kaizen)

    hackathon_payload = {
        "club_id": 1,
        "title": "National Innovate India Hackathon",
        "rank_position": "1st Place (National Champions)",
        "level": "National",
        "team_name": "Nextcell Pioneers",
        "team_members": "Aarav Sharma, Rohan Gupta",
        "points_awarded": 150,
        "advisor_notes": "First prize winner in open innovation track."
    }

    # 1. Regular student attempts to record -> 403 Forbidden
    res_student = client.post(
        "/api/analytics/hackathon-achievement",
        headers={"x-user-id": str(student.id)},
        json=hackathon_payload
    )
    assert res_student.status_code == 403
    assert "Only the designated Faculty Advisor" in res_student.json()["detail"]

    # 2. Advisor of Kaizen (Club 2) attempts to record for Nextcell (Club 1) -> 403 Forbidden
    res_cross_advisor = client.post(
        "/api/analytics/hackathon-achievement",
        headers={"x-user-id": str(advisor_kaizen.id)},
        json=hackathon_payload
    )
    assert res_cross_advisor.status_code == 403
    assert "Only the designated Faculty Advisor of Nextcell Club" in res_cross_advisor.json()["detail"]

    # 3. Respective Advisor of Nextcell (Dr. Rajiv Menon) records -> 200 OK
    res_auth = client.post(
        "/api/analytics/hackathon-achievement",
        headers={"x-user-id": str(advisor_nextcell.id)},
        json=hackathon_payload
    )
    assert res_auth.status_code == 200
    assert res_auth.json()["status"] == "success"
    assert res_auth.json()["club_name"] == "Nextcell Club"

    # 4. Respective Advisor updates performance audit -> 200 OK
    audit_payload = {
        "activity_execution_score": 95.0,
        "activity_feedback": "Exceptional weekend hackathon performance and pitch defense.",
        "budget_governance_score": 98.0,
        "budget_audit_notes": "Clean ledger with zero deficit.",
        "project_quality_score": 94.0
    }
    res_audit = client.put(
        "/api/analytics/club/1/advisor-audit",
        headers={"x-user-id": str(advisor_nextcell.id)},
        json=audit_payload
    )
    assert res_audit.status_code == 200
    assert res_audit.json()["status"] == "success"
    assert res_audit.json()["activity_execution_score"] == 95.0
