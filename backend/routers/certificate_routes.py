import os
import hashlib
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors

from backend.database import get_db
from backend.models import (
    Certificate, User, Club, Event, ClubMembership, AttendanceRecord, AttendanceSession, Submission, Evaluation, AuditLog
)
from backend.schemas import CertificateOut
from backend.auth import get_current_user

router = APIRouter(prefix="/api/certificates", tags=["Certificates & Co-Curricular Transcripts"])

CERT_PDF_DIR = "./uploads/certificates"
os.makedirs(CERT_PDF_DIR, exist_ok=True)

def generate_verification_hash(cert_id: str, user_id: int, title: str, issue_date_str: str) -> str:
    raw = f"{cert_id}:{user_id}:{title}:{issue_date_str}:MSOT_OFFICIAL_STAMP_2026"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def create_certificate_pdf(cert: Certificate, student_name: str, roll_no: str, club_name: str, campus_name: str) -> str:
    file_name = f"cert_{cert.id}.pdf"
    pdf_path = os.path.join(CERT_PDF_DIR, file_name)

    c = canvas.Canvas(pdf_path, pagesize=landscape(letter))
    width, height = landscape(letter)

    # Background frame
    c.setStrokeColor(colors.HexColor("#1e293b"))
    c.setLineWidth(4)
    c.rect(20, 20, width - 40, height - 40)
    c.setStrokeColor(colors.HexColor("#f59e0b"))
    c.setLineWidth(1.5)
    c.rect(26, 26, width - 52, height - 52)

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawCentredString(width / 2.0, height - 70, f"MIRAI SCHOOL OF TECHNOLOGY ({campus_name.upper()})")

    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawCentredString(width / 2.0, height - 105, "CERTIFICATE OF RECOGNITION")

    c.setFont("Helvetica-Oblique", 13)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawCentredString(width / 2.0, height - 135, f"This is officially awarded to")

    # Recipient
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(colors.HexColor("#1d4ed8"))
    c.drawCentredString(width / 2.0, height - 175, student_name.upper())

    c.setFont("Helvetica", 12)
    c.setFillColor(colors.HexColor("#334155"))
    c.drawCentredString(width / 2.0, height - 195, f"Roll Number: {roll_no or 'N/A'}")

    # Body description
    c.setFont("Helvetica", 13)
    c.drawCentredString(
        width / 2.0, height - 240,
        f"for outstanding participation and achievement in {club_name}"
    )
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawCentredString(width / 2.0, height - 265, f'"{cert.title}"')

    # Footer Metadata & Signatures
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawString(50, 80, f"Certificate No: {cert.certificate_number}")
    c.drawString(50, 65, f"Issued Date: {cert.issue_date.strftime('%d %B %Y')}")
    c.drawString(50, 50, f"Hash ID: {cert.verification_hash[:20]}...")

    # Signatures
    c.line(width - 250, 75, width - 60, 75)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawCentredString(width - 155, 60, "Authorized Campus Official")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawCentredString(width - 155, 48, "MSOT Club Governance Council")

    # Verification Note
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(colors.HexColor("#2563eb"))
    c.drawCentredString(width / 2.0, 48, f"Verify authenticity at: http://localhost:8000/verify/{cert.id}")

    c.save()
    return f"/uploads/certificates/{file_name}"

@router.post("/issue")
def issue_certificate(
    user_id: int,
    title: str,
    club_id: Optional[int] = None,
    event_id: Optional[int] = None,
    cert_type: str = "ACHIEVEMENT", # PARTICIPATION, ACHIEVEMENT, LEADERSHIP
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Faculty Advisor, Campus Manager, or President issues an official certificate."""
    student = db.query(User).filter(User.id == user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    club = db.query(Club).filter(Club.id == club_id).first() if club_id else None
    
    cert_id = str(uuid.uuid4())
    now = datetime.utcnow()
    prefix = "CLB" if club else "GEN"
    hex_code = uuid.uuid4().hex[:6].upper()
    cert_num = f"MSOT-{now.year}-{prefix}-{hex_code}"
    v_hash = generate_verification_hash(cert_id, student.id, title, now.strftime("%Y-%m-%d"))

    cert = Certificate(
        id=cert_id,
        certificate_number=cert_num,
        user_id=student.id,
        club_id=club.id if club else None,
        event_id=event_id,
        cert_type=cert_type,
        title=title,
        issue_date=now,
        verification_hash=v_hash
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)

    # Generate PDF
    pdf_rel_path = create_certificate_pdf(
        cert=cert,
        student_name=student.name,
        roll_no=student.roll_no or "N/A",
        club_name=club.name if club else "MSOT Activities",
        campus_name=student.campus.name if student.campus else "MSOT Campus"
    )
    cert.pdf_url = pdf_rel_path
    db.commit()

    # Log audit
    audit = AuditLog(
        user_id=current_user.id,
        action="ISSUE_CERTIFICATE",
        target_type="CERTIFICATE",
        target_id=cert.id,
        details=f"Issued {cert_type} certificate to {student.name} for {title}"
    )
    db.add(audit)
    db.commit()

    return {
        "message": "Certificate generated successfully!",
        "certificate_id": cert.id,
        "certificate_number": cert.certificate_number,
        "pdf_url": cert.pdf_url,
        "verification_url": f"/verify/{cert.id}"
    }

@router.get("/verify/{cert_id}")
def verify_certificate_public(cert_id: str, db: Session = Depends(get_db)):
    """
    Public Verification Page Endpoint (No login required).
    Scanned by recruiters, faculty or students.
    Checks SHA-256 cryptographic hash to flag any tampered records.
    """
    cert = db.query(Certificate).filter(Certificate.id == cert_id).first()
    if not cert:
        return {
            "valid": False,
            "status": "NOT_FOUND_OR_REVOKED",
            "message": "Certificate record not found in MSOT database. This credential may be counterfeit or revoked."
        }

    # Verify cryptographic signature
    expected_hash = generate_verification_hash(
        cert.id, cert.user_id, cert.title, cert.issue_date.strftime("%Y-%m-%d")
    )
    is_tamper_free = (cert.verification_hash == expected_hash)

    return {
        "valid": is_tamper_free,
        "status": "VERIFIED_AUTHENTIC" if is_tamper_free else "TAMPERED_WARNING",
        "certificate_id": cert.id,
        "certificate_number": cert.certificate_number,
        "student_name": cert.user.name,
        "roll_no": cert.user.roll_no,
        "campus": cert.user.campus.name if cert.user.campus else "MSOT",
        "club_name": cert.club.name if cert.club else "MSOT Central",
        "title": cert.title,
        "cert_type": cert.cert_type,
        "issue_date": cert.issue_date.strftime("%d %B %Y"),
        "verification_hash": cert.verification_hash,
        "pdf_url": cert.pdf_url
    }

@router.get("/my-transcript")
def get_my_co_curricular_transcript(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Complete co-curricular transcript for student resume and placement portfolio.
    Itemizes:
    - Enrolled Clubs & Leadership Tenures
    - Attendance summary
    - Deliverables & Rubric Grades
    - Certificates & Honors
    """
    memberships = db.query(ClubMembership).filter(ClubMembership.user_id == current_user.id).all()
    records = db.query(AttendanceRecord).filter(AttendanceRecord.user_id == current_user.id).all()
    submissions = db.query(Submission).filter(Submission.student_id == current_user.id).all()
    certs = db.query(Certificate).filter(Certificate.user_id == current_user.id).all()

    # Formatted transcript entries
    club_entries = []
    for m in memberships:
        total_sessions = db.query(AttendanceSession).filter(AttendanceSession.club_id == m.club_id).count()
        attended = db.query(AttendanceRecord).join(AttendanceSession).filter(
            AttendanceSession.club_id == m.club_id,
            AttendanceRecord.user_id == current_user.id
        ).count()
        rate = round((attended / total_sessions * 100), 1) if total_sessions > 0 else 100.0

        club_entries.append({
            "club_name": m.club.name,
            "category": m.club.category,
            "role_post": m.post,
            "faculty_advisor": m.club.faculty_advisor.name if m.club.faculty_advisor else None,
            "joined_at": m.joined_at.strftime("%d %b %Y"),
            "attendance_rate": f"{rate}% ({attended}/{total_sessions} sessions)"
        })

    submission_entries = []
    for s in submissions:
        sub_info = {
            "assignment_title": s.assignment.title,
            "club_name": s.assignment.club.name,
            "submitted_at": s.submitted_at.strftime("%d %b %Y"),
            "status": s.status
        }
        if s.evaluation:
            sub_info["score"] = f"{s.evaluation.total_score}/30"
            sub_info["rubric_breakdown"] = f"Content: {s.evaluation.content_score}/10, Presentation: {s.evaluation.presentation_score}/10, Participation: {s.evaluation.participation_score}/10"
            sub_info["feedback"] = s.evaluation.feedback_comments
        submission_entries.append(sub_info)

    cert_entries = [
        {
            "id": c.id,
            "cert_number": c.certificate_number,
            "title": c.title,
            "type": c.cert_type,
            "issue_date": c.issue_date.strftime("%d %b %Y"),
            "pdf_url": c.pdf_url,
            "verification_url": f"/verify/{c.id}"
        }
        for c in certs
    ]

    return {
        "student": {
            "name": current_user.name,
            "roll_no": current_user.roll_no,
            "email": current_user.email,
            "campus": current_user.campus.name if current_user.campus else "MSOT"
        },
        "clubs": club_entries,
        "submissions_and_grades": submission_entries,
        "certificates": cert_entries,
        "total_attended_sessions": len(records),
        "transcript_generated_at": datetime.utcnow().strftime("%d %B %Y, %H:%M UTC")
    }
