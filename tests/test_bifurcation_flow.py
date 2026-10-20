import pytest
import uuid
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_full_bifurcation_and_governance_flow():
    unique_suffix = uuid.uuid4().hex[:6]
    # 1. Register a fresh user with master dev OTP "999999"
    reg_resp = client.post("/api/auth/register", json={
        "name": f"Test User {unique_suffix}",
        "email": f"test.{unique_suffix}@msot.org",
        "phone": f"+9198765{unique_suffix[:5]}",
        "student_id": f"MSOT{unique_suffix.upper()}",
        "username": f"user_{unique_suffix}",
        "password": "password123",
        "otp": "999999",
        "campus_id": 1
    })
    assert reg_resp.status_code == 200
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Step 1 Non-Mirai bifurcation
    bif_non_mirai = client.post("/api/auth/bifurcate", headers=headers, json={
        "is_mirai_entity": False,
        "user_category": "NON_MIRAI"
    })
    assert bif_non_mirai.status_code == 200
    assert bif_non_mirai.json()["user"]["user_category"] == "NON_MIRAI"

    # 3. Step 2 & 3 Case 1 (Teacher -> Normal Teacher)
    bif_teacher = client.post("/api/auth/bifurcate", headers=headers, json={
        "is_mirai_entity": True,
        "teacher_type": "TEACHER",
        "user_category": "TEACHER"
    })
    assert bif_teacher.status_code == 200
    assert bif_teacher.json()["user"]["user_category"] == "TEACHER"

    # 4. Step 2 & 3 Case 1 (Teacher -> Club Advisor)
    bif_advisor = client.post("/api/auth/bifurcate", headers=headers, json={
        "is_mirai_entity": True,
        "teacher_type": "CLUB_ADVISOR",
        "user_category": "CLUB_ADVISOR"
    })
    assert bif_advisor.status_code == 200
    assert bif_advisor.json()["user"]["user_category"] == "CLUB_ADVISOR"

    # 5. Step 2 & 3 Case 2 (Student -> Non-Club Member)
    bif_student_non = client.post("/api/auth/bifurcate", headers=headers, json={
        "is_mirai_entity": True,
        "student_type": "NON_CLUB_MEMBER",
        "user_category": "STUDENT_NON_MEMBER"
    })
    assert bif_student_non.status_code == 200
    assert bif_student_non.json()["user"]["user_category"] == "STUDENT_NON_MEMBER"

    # 6. Step 2 & 3 Case 2 (Student -> Club Member)
    bif_student_mem = client.post("/api/auth/bifurcate", headers=headers, json={
        "is_mirai_entity": True,
        "student_type": "CLUB_MEMBER",
        "user_category": "STUDENT_MEMBER"
    })
    assert bif_student_mem.status_code == 200
    assert bif_student_mem.json()["user"]["user_category"] == "STUDENT_MEMBER"

def test_advisor_authority_and_kaizen_governance():
    # Login as Dr. Rajiv Menon (Advisor of Nextcell Club, ID 1)
    advisor_resp = client.post("/api/auth/login", json={
        "email": "advisor.tech@msot.org",
        "password": "password123"
    })
    assert advisor_resp.status_code == 200
    adv_token = advisor_resp.json()["access_token"]
    adv_headers = {"Authorization": f"Bearer {adv_token}"}

    # Nextcell Club has 5 leadership posts: appoint General Secretary
    assign_resp = client.post("/api/clubs/1/assign-post", headers=adv_headers, json={
        "target_user_id": 2, # student_1
        "post": "GENERAL_SECRETARY"
    })
    assert assign_resp.status_code == 200
    assert "GENERAL_SECRETARY" in assign_resp.json()["message"]

    # Test Kaizen 2-leader restriction
    # Try assigning Finance President in Kaizen Club (ID 2) -> Should fail with 400
    kaizen_fail = client.post("/api/clubs/2/assign-post", headers=adv_headers, json={
        "target_user_id": 2,
        "post": "FINANCE_PRESIDENT"
    })
    assert kaizen_fail.status_code == 400
    assert "Kaizen" in kaizen_fail.json()["detail"]

    # Assign valid President in Kaizen -> Succeeds
    kaizen_success = client.post("/api/clubs/2/assign-post", headers=adv_headers, json={
        "target_user_id": 2,
        "post": "PRESIDENT"
    })
    assert kaizen_success.status_code == 200

def test_kaizen_special_network_branches():
    # Login as Student 1
    stud_resp = client.post("/api/auth/login", json={
        "email": "student1@msot.org",
        "password": "password123"
    })
    assert stud_resp.status_code == 200
    stud_token = stud_resp.json()["access_token"]
    stud_headers = {"Authorization": f"Bearer {stud_token}"}

    # Verify branches list
    branches_resp = client.get("/api/clubs/2/branches", headers=stud_headers)
    assert branches_resp.status_code == 200
    branches = branches_resp.json()
    assert len(branches) == 4
    branch_names = [b["name"] for b in branches]
    assert "CPP Club" in branch_names
    assert "Dev Club" in branch_names
    assert "Kaizen Intelligence" in branch_names
    assert "Media Club" in branch_names

    # Select Dev Club branch
    sel_resp = client.post("/api/clubs/2/select-branch", headers=stud_headers, json={
        "branch": "Dev Club"
    })
    assert sel_resp.status_code == 200
    assert "Dev Club" in sel_resp.json()["message"]

def test_president_report_submission_and_advisor_review():
    # Login as Aarav Sharma (President of Nextcell Club)
    pres_resp = client.post("/api/auth/login", json={
        "email": "aarav.pres@msot.org",
        "password": "password123"
    })
    assert pres_resp.status_code == 200
    pres_token = pres_resp.json()["access_token"]
    pres_headers = {"Authorization": f"Bearer {pres_token}"}

    # Submit Vision Report
    report_resp = client.post("/api/clubs/1/president-report", headers=pres_headers, json={
        "title": "Q3 Technical Roadmap: Autonomous Systems",
        "vision_statement": "Deploy 3 robotic arm prototypes and complete 50 LeetCode sprints.",
        "vp_operational_orders": "Coordinate Lab 304 bookings with Campus Manager.",
        "finance_budget_overview": "₹35,000 requested for microcontrollers and sensors.",
        "media_campaign_plan": "Ship weekly Dev Reels on YouTube and Instagram.",
        "general_secretary_notes": "All compliance forms signed by 65 club members."
    })
    assert report_resp.status_code == 200
    report_id = report_resp.json()["id"]

    # Login as Dr. Rajiv Menon (Advisor)
    adv_resp = client.post("/api/auth/login", json={
        "email": "advisor.tech@msot.org",
        "password": "password123"
    })
    adv_headers = {"Authorization": f"Bearer {adv_resp.json()['access_token']}"}

    # Read reports
    reports_list = client.get("/api/clubs/1/president-reports", headers=adv_headers)
    assert reports_list.status_code == 200
    assert any(r["id"] == report_id for r in reports_list.json())

    # Advisor reviews vision report
    review_resp = client.put(f"/api/clubs/1/president-reports/{report_id}/feedback", headers=adv_headers, json={
        "status": "APPROVED",
        "advisor_feedback": "Excellent roadmap! Approved. Proceed with Saturday tracks."
    })
    assert review_resp.status_code == 200
    assert review_resp.json()["status"] == "success"
    assert "Excellent roadmap!" in review_resp.json()["advisor_feedback"]
