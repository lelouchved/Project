import pytest
import pyotp
import uuid
import datetime
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal, Base, engine
from backend.models import (
    User, Club, ClubMembership, AttendanceSession, AttendanceRecord,
    AssignmentProject, Submission, Evaluation, Certificate, AuditLog
)
from backend.routers.certificate_routes import generate_verification_hash

client = TestClient(app)

def get_user(username: str) -> User:
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()
    if not user:
        raise ValueError(f"User with username '{username}' not found in database.")
    return user

def test_01_institution_2_club_limit():
    """
    Test Area: Enrolment Policy
    Verifies that students can join up to 2 clubs only,
    and attempting to join a 3rd club is strictly rejected.
    """
    stud = get_user("student_3")
    headers = {"x-user-id": str(stud.id)}

    # Join Club 1 (Nextcell)
    r1 = client.post("/api/clubs/1/join", headers=headers)
    assert r1.status_code in [200, 400] # Might already be joined or succeeds

    # Join Club 2 (Kaizen)
    r2 = client.post("/api/clubs/2/join", headers=headers)
    assert r2.status_code in [200, 400]

    # Attempt to join 3rd Club (Sports Club) -> MUST BE REJECTED
    r3 = client.post("/api/clubs/4/join", headers=headers)
    assert r3.status_code == 400
    assert "maximum of 2 clubs only" in r3.json()["detail"]

def test_02_dynamic_qr_checkin_and_anti_spoofing():
    """
    Test Area: Check-in Integrity
    Verifies that:
    1. A valid live TOTP code succeeds.
    2. An expired / fake screenshot code fails with 400 Bad Request.
    """
    pres = get_user("aarav_lead")
    stud = get_user("student_4")
    fake_stud = get_user("student_5")

    # 1. Start or fetch active session
    res = client.get("/api/attendance/qr-token/1", headers={"x-user-id": str(pres.id)})
    assert res.status_code == 200
    token_data = res.json()
    live_token = token_data["current_token"]

    # 2. Student Candidate checks in with live valid token
    headers_student = {"x-user-id": str(stud.id)}
    checkin_res = client.post("/api/attendance/check-in", headers=headers_student, json={
        "session_id": 1,
        "token": live_token
    })
    assert checkin_res.status_code == 200
    assert "checked in" in checkin_res.json()["message"].lower()

    # 3. ANTI-SPOOFING: Expired or fake screenshot code
    fake_res = client.post("/api/attendance/check-in", headers={"x-user-id": str(fake_stud.id)}, json={
        "session_id": 1,
        "token": "000000" # Invalid expired token
    })
    assert fake_res.status_code == 400
    assert "Invalid or expired QR token" in fake_res.json()["detail"]

def test_03_attendance_manual_override_with_audit_trail():
    """
    Test Area: Coordinator Manual Override
    Coordinators can correct attendance for camera failures,
    requiring a mandatory written reason stored in AuditLog.
    """
    pres = get_user("aarav_lead")
    stud = get_user("student_5")
    headers_pres = {"x-user-id": str(pres.id)}
    reason = "Student phone battery died during presentation, verified in person by coordinator."
    
    res = client.post("/api/attendance/override", headers=headers_pres, json={
        "session_id": 1,
        "student_id": stud.id,
        "reason": reason
    })
    assert res.status_code == 200
    assert res.json()["status"] == "MANUAL_OVERRIDE"

    # Verify audit log
    db = SessionLocal()
    audit = db.query(AuditLog).filter(
        AuditLog.action == "ATTENDANCE_MANUAL_OVERRIDE",
        AuditLog.target_id == str(stud.id)
    ).first()
    assert audit is not None
    assert reason in audit.details
    db.close()

def test_04_deliverable_submission_and_3_part_rubric():
    """
    Test Area: Submissions & Rubric Evaluation
    Student uploads deliverable; coordinator grades across:
    1. Content Score (/10)
    2. Presentation Score (/10)
    3. Participation Score (/10)
    Total score (/30)
    """
    stud1 = get_user("student_1")
    adv = get_user("advisor_menon")

    # Submit deliverable
    sub_res = client.post("/api/assignments/submit", headers={"x-user-id": str(stud1.id)}, data={
        "assignment_id": 1,
        "external_link": "https://github.com/msot/distributed-queue",
        "notes": "Completed queue consumer with exponential backoff."
    })
    assert sub_res.status_code == 200
    sub_id = sub_res.json()["id"]

    # Grade on 3-part rubric by Faculty Advisor (Dr. Rajiv Menon)
    eval_res = client.post("/api/assignments/evaluate", headers={"x-user-id": str(adv.id)}, json={
        "submission_id": sub_id,
        "content_score": 9.0,
        "presentation_score": 9.5,
        "participation_score": 8.5,
        "comments": "Superb architecture and clear documentation."
    })
    assert eval_res.status_code == 200
    assert eval_res.json()["total_score"] == 27.0

def test_05_certificate_generation_and_tamper_detection():
    """
    Test Area: Certificates & Verification (20 Samples)
    Generates 20 unique certificates, verifies public lookup,
    and confirms that altered payloads fail verification.
    """
    stud1 = get_user("student_1")
    db = SessionLocal()
    cert_ids = []

    # Generate 20 certificates
    prefix = uuid.uuid4().hex[:6]
    for i in range(20):
        c_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow()
        v_hash = generate_verification_hash(c_id, stud1.id, f"Certificate Sample {i+1}", now.strftime("%Y-%m-%d"))
        cert = Certificate(
            id=c_id,
            certificate_number=f"MSOT-TEST-{prefix}-{i+1:03d}",
            user_id=stud1.id,
            club_id=1,
            cert_type="ACHIEVEMENT",
            title=f"Certificate Sample {i+1}",
            issue_date=now,
            verification_hash=v_hash
        )
        db.add(cert)
        cert_ids.append(c_id)
    db.commit()

    # 1. Verify authentic certificates
    sample_id = cert_ids[0]
    verify_res = client.get(f"/api/certificates/verify/{sample_id}")
    assert verify_res.status_code == 200
    assert verify_res.json()["valid"] is True
    assert verify_res.json()["status"] == "VERIFIED_AUTHENTIC"

    # 2. Verify tampered certificate (corrupted hash)
    tampered_cert = db.query(Certificate).filter(Certificate.id == cert_ids[1]).first()
    tampered_cert.verification_hash = "fake_corrupted_tampered_hash_123"
    db.commit()

    tampered_res = client.get(f"/api/certificates/verify/{cert_ids[1]}")
    assert tampered_res.status_code == 200
    assert tampered_res.json()["valid"] is False
    assert tampered_res.json()["status"] == "TAMPERED_WARNING"

    # 3. Non-existent certificate
    fake_res = client.get(f"/api/certificates/verify/non-existent-uuid-999")
    assert fake_res.json()["valid"] is False
    assert fake_res.json()["status"] == "NOT_FOUND_OR_REVOKED"
    db.close()

def test_06_finance_president_budget_workflow():
    """
    Test Area: Scale-based Budget Workflow
    Finance President requests ₹25,000 for event supplies.
    Campus Manager reviews and approves the request.
    """
    priya = get_user("priya_fin")
    cm = get_user("cm_sunita")

    # 1. Finance President Priya Patel submits request
    budget_res = client.post("/api/budgets", headers={"x-user-id": str(priya.id)}, json={
        "club_id": 1,
        "title": "Robotics Sensor Kit Bulk Procurement",
        "amount": 25000.0,
        "category": "Equipment",
        "purpose": "Procuring 15 ultrasonic and LiDAR sensor kits for the inter-campus challenge.",
        "scale": "Flagship Event"
    })
    assert budget_res.status_code == 200
    b_id = budget_res.json()["id"]
    assert budget_res.json()["status"] == "PENDING"

    # 2. Campus Manager Prof. Sunita Rao approves
    approve_res = client.put(f"/api/budgets/{b_id}/review", headers={"x-user-id": str(cm.id)}, json={
        "status": "APPROVED",
        "admin_notes": "Approved from Q4 Institutional Co-Curricular Fund."
    })
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "APPROVED"

def test_07_monthly_academic_csv_export():
    """
    Test Area: Monthly Academic Reports
    Verifies that the CSV report exports successfully with valid headers.
    """
    cm = get_user("cm_sunita")
    res = client.get("/api/reports/export-monthly-csv", headers={"x-user-id": str(cm.id)})
    assert res.status_code == 200
    assert res.headers["content-type"] == "text/csv; charset=utf-8"
    assert "Student ID,Student Name,Roll Number" in res.text

def test_08_registration_otp_and_domain_passkey_yuzuru():
    """
    Test Area: Dynamic Registration with OTP and Domain Exception Passkey ('Yuzuru')
    1. Request OTP for a new user.
    2. Register user WITH passkey 'Yuzuru' -> becomes domain authorized (ADMIN/Authorized Lead).
    3. Successfully reassigns club posts for any club.
    4. Register user WITHOUT passkey -> becomes regular student/member without authority.
    """
    stud1 = get_user("student_1")

    # 1. Request OTP
    rand_tag = uuid.uuid4().hex[:6]
    email1 = f"lead_{rand_tag}@msot.org"
    otp_res = client.post("/api/auth/otp/request", json={"identifier": email1})
    assert otp_res.status_code == 200
    otp = otp_res.json()["simulated_otp"]

    # 2. Register WITH passkey 'Yuzuru'
    reg_res = client.post("/api/auth/register", json={
        "email": email1,
        "name": "Yuzuru Authorised Lead",
        "phone": f"+91 99999 {rand_tag[:5]}",
        "student_id": f"MSOT-{rand_tag[:4].upper()}",
        "username": f"yuzuru_{rand_tag}",
        "password": "securepassword",
        "otp": otp,
        "domain_passkey": "Yuzuru",
        "campus_id": 1
    })
    assert reg_res.status_code == 200
    data = reg_res.json()
    assert data["user"]["is_domain_authorized"] is True
    assert data["user"]["role"] == "ADMIN"
    auth_user_id = data["user"]["id"]

    # 3. Use this newly authorized user to reassign club posts in Club 1
    reassign_res = client.put(f"/api/clubs/1/assign-post?target_user_id={stud1.id}&post=VICE_PRESIDENT", headers={"x-user-id": str(auth_user_id)})
    assert reassign_res.status_code == 200
    assert reassign_res.json()["post"] == "VICE_PRESIDENT"

    # 4. Register WITHOUT passkey
    email2 = f"norm_{rand_tag}@msot.org"
    otp_res2 = client.post("/api/auth/otp/request", json={"identifier": email2})
    otp2 = otp_res2.json()["simulated_otp"]

    reg_normal = client.post("/api/auth/register", json={
        "email": email2,
        "name": "Normal MSOT Student",
        "phone": f"+91 88888 {rand_tag[:5]}",
        "student_id": f"NORM-{rand_tag[:4].upper()}",
        "username": f"norm_{rand_tag}",
        "password": "securepassword",
        "otp": otp2,
        "domain_passkey": "", # No passkey
        "campus_id": 1
    })
    assert reg_normal.status_code == 200
    norm_data = reg_normal.json()
    assert norm_data["user"]["is_domain_authorized"] is False
    assert norm_data["user"]["role"] == "STUDENT"
