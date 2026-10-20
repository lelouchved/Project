import pyotp
import time
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    Event, AttendanceSession, AttendanceRecord, Club, ClubMembership, User, AuditLog
)
from backend.schemas import (
    AttendanceSessionStart, AttendanceCheckIn, AttendanceOverride, AttendanceRecordOut
)
from backend.auth import get_current_user

router = APIRouter(prefix="/api/attendance", tags=["Dynamic QR Attendance"])

@router.post("/start-session")
def start_attendance_session(
    data: AttendanceSessionStart,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Coordinators with assigned posts or Faculty Advisor start a live attendance session.
    Generates a secure TOTP secret that rotates dynamic QR codes every 20 seconds.
    """
    event = db.query(Event).filter(Event.id == data.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Check permission
    if event.club_id:
        membership = db.query(ClubMembership).filter(
            ClubMembership.club_id == event.club_id,
            ClubMembership.user_id == current_user.id
        ).first()
        is_lead = membership and membership.post in ["PRESIDENT", "VICE_PRESIDENT", "MEDIA_PRESIDENT", "FINANCE_PRESIDENT"]
        is_advisor = current_user.id == event.club.faculty_advisor_id or current_user.role in ["ADMIN", "CAMPUS_MANAGER"]
        if not (is_lead or is_advisor):
            raise HTTPException(status_code=403, detail="Only Club Officers or Faculty Advisors can open attendance.")

    # Check if an active session already exists
    session = db.query(AttendanceSession).filter(
        AttendanceSession.event_id == event.id,
        AttendanceSession.is_active == True
    ).first()

    now = datetime.utcnow()
    closes = now + timedelta(minutes=data.duration_minutes)

    if not session:
        secret = pyotp.random_base32()
        session = AttendanceSession(
            event_id=event.id,
            club_id=event.club_id,
            totp_secret=secret,
            opens_at=now,
            closes_at=closes,
            is_active=True
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    else:
        # Extend closing time
        session.closes_at = closes
        db.commit()

    return {
        "session_id": session.id,
        "event_id": event.id,
        "event_title": event.title,
        "totp_secret": session.totp_secret,
        "opens_at": session.opens_at,
        "closes_at": session.closes_at,
        "message": "Live dynamic QR session started."
    }

@router.get("/qr-token/{session_id}")
def get_rotating_qr_token(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the live TOTP token for this 20-second interval.
    The projector / coordinator phone updates this code every 20 seconds.
    Any screenshot older than 20-40 seconds becomes completely invalid.
    """
    session = db.query(AttendanceSession).filter(
        AttendanceSession.id == session_id,
        AttendanceSession.is_active == True
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Active attendance session not found")

    # Enforce session window
    if datetime.utcnow() > session.closes_at:
        session.is_active = False
        db.commit()
        raise HTTPException(status_code=400, detail="Attendance session has concluded.")

    totp = pyotp.TOTP(session.totp_secret, interval=20)
    current_token = totp.now()
    seconds_remaining = 20 - (int(time.time()) % 20)

    return {
        "session_id": session.id,
        "current_token": current_token,
        "seconds_remaining": seconds_remaining,
        "qr_payload": f"MSOT_ATTEND:{session.id}:{current_token}",
        "closes_at": session.closes_at
    }

@router.get("/active-session")
def get_current_active_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns the currently active live attendance session for student check-in."""
    now = datetime.utcnow()
    session = db.query(AttendanceSession).filter(
        AttendanceSession.is_active == True,
        AttendanceSession.closes_at > now
    ).order_by(AttendanceSession.id.desc()).first()
    
    if not session:
        session = db.query(AttendanceSession).order_by(AttendanceSession.id.desc()).first()

    if not session:
        return {"has_active_session": False}

    totp = pyotp.TOTP(session.totp_secret, interval=20)
    current_token = totp.now()

    return {
        "has_active_session": True,
        "session_id": session.id,
        "event_id": session.event_id,
        "event_title": session.event.title if session.event else "Saturday Session",
        "club_name": session.event.club.name if session.event and session.event.club else "Institutional Saturday",
        "opens_at": session.opens_at,
        "closes_at": session.closes_at,
        "is_active": session.is_active and (session.closes_at > now),
        "demo_live_pin": current_token
    }

@router.post("/check-in")
def student_check_in(
    checkin: AttendanceCheckIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Student scans the dynamic QR or enters the 6-digit one-time code.
    Checks anti-spoofing TOTP token with 1-step drift allowance.
    """
    session = None
    if checkin.session_id and checkin.session_id > 0:
        session = db.query(AttendanceSession).filter(AttendanceSession.id == checkin.session_id).first()
    
    if not session:
        now = datetime.utcnow()
        session = db.query(AttendanceSession).filter(
            AttendanceSession.is_active == True,
            AttendanceSession.closes_at > now
        ).order_by(AttendanceSession.id.desc()).first()

    if not session:
        session = db.query(AttendanceSession).order_by(AttendanceSession.id.desc()).first()

    if not session or not session.is_active:
        raise HTTPException(status_code=400, detail="This attendance session is no longer active.")

    if datetime.utcnow() > session.closes_at:
        session.is_active = False
        db.commit()
        raise HTTPException(status_code=400, detail="Attendance window has closed.")

    # Validate TOTP (with 1 interval = 20s leeway)
    totp = pyotp.TOTP(session.totp_secret, interval=20)
    # Extract token if user scanned raw QR payload "MSOT_ATTEND:sessionId:token"
    token_str = checkin.token.strip()
    if ":" in token_str:
        parts = token_str.split(":")
        token_str = parts[-1]

    is_valid = totp.verify(token_str, valid_window=1)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired QR token! Screenshots are not accepted. Scan the live rotating QR."
        )

    # Check if already marked
    existing = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == session.id,
        AttendanceRecord.user_id == current_user.id
    ).first()
    if existing:
        return {
            "message": "Already checked in!",
            "status": existing.status,
            "checkin_time": existing.checkin_time
        }

    # Record attendance
    record = AttendanceRecord(
        session_id=session.id,
        user_id=current_user.id,
        checkin_time=datetime.utcnow(),
        status="PRESENT"
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "message": f"Successfully checked in for {session.event.title}!",
        "student_name": current_user.name,
        "roll_no": current_user.roll_no,
        "status": "PRESENT",
        "checkin_time": record.checkin_time
    }

@router.post("/override")
def coordinator_manual_override(
    override: AttendanceOverride,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Coordinators can manually correct attendance for students who had genuine camera issues.
    MANDATORY requirement: must provide a written reason stored in the audit log.
    """
    session = db.query(AttendanceSession).filter(AttendanceSession.id == override.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Attendance session not found")

    student = db.query(User).filter(User.id == override.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if not override.reason or len(override.reason.strip()) < 5:
        raise HTTPException(status_code=400, detail="A detailed mandatory reason is required for manual attendance override.")

    # Check permissions
    membership = db.query(ClubMembership).filter(
        ClubMembership.club_id == session.club_id,
        ClubMembership.user_id == current_user.id
    ).first()
    is_lead = membership and membership.post in ["PRESIDENT", "VICE_PRESIDENT"]
    is_mgmt = current_user.role in ["ADMIN", "CAMPUS_MANAGER", "FACULTY_ADVISOR"]
    if not (is_lead or is_mgmt):
        raise HTTPException(status_code=403, detail="Unauthorized to override attendance.")

    record = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == session.id,
        AttendanceRecord.user_id == student.id
    ).first()

    if not record:
        record = AttendanceRecord(
            session_id=session.id,
            user_id=student.id,
            checkin_time=datetime.utcnow(),
            status="MANUAL_OVERRIDE",
            override_reason=override.reason,
            override_by_id=current_user.id
        )
        db.add(record)
    else:
        record.status = "MANUAL_OVERRIDE"
        record.override_reason = override.reason
        record.override_by_id = current_user.id

    # Mandatory Audit Trail
    audit = AuditLog(
        user_id=current_user.id,
        action="ATTENDANCE_MANUAL_OVERRIDE",
        target_type="ATTENDANCE_RECORD",
        target_id=str(student.id),
        details=f"Overrode attendance for {student.name} ({student.roll_no}) in session {session.id}. Reason: {override.reason}"
    )
    db.add(audit)
    db.commit()

    return {
        "message": f"Manual override saved for {student.name}.",
        "status": "MANUAL_OVERRIDE",
        "reason": override.reason
    }

@router.get("/records/{session_id}", response_model=List[AttendanceRecordOut])
def get_session_attendance(
    session_id: int,
    db: Session = Depends(get_db)
):
    records = db.query(AttendanceRecord).filter(AttendanceRecord.session_id == session_id).all()
    results = []
    for r in records:
        results.append(AttendanceRecordOut(
            id=r.id,
            session_id=r.session_id,
            user_id=r.user_id,
            user_name=r.user.name,
            roll_no=r.user.roll_no,
            checkin_time=r.checkin_time,
            status=r.status,
            override_reason=r.override_reason
        ))
    return results

@router.get("/my-attendance")
def get_my_attendance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Students track their personal attendance history and rate."""
    records = db.query(AttendanceRecord).filter(AttendanceRecord.user_id == current_user.id).all()
    
    # Calculate attendance rate per enrolled club
    my_memberships = db.query(ClubMembership).filter(
        ClubMembership.user_id == current_user.id,
        ClubMembership.status == "ACTIVE"
    ).all()

    club_stats = []
    for m in my_memberships:
        total_sessions = db.query(AttendanceSession).filter(AttendanceSession.club_id == m.club_id).count()
        attended = db.query(AttendanceRecord).join(AttendanceSession).filter(
            AttendanceSession.club_id == m.club_id,
            AttendanceRecord.user_id == current_user.id
        ).count()
        rate = round((attended / total_sessions * 100), 1) if total_sessions > 0 else 100.0
        club_stats.append({
            "club_id": m.club_id,
            "club_name": m.club.name,
            "total_sessions": total_sessions,
            "attended": attended,
            "attendance_rate": rate
        })

    return {
        "student_name": current_user.name,
        "total_attended": len(records),
        "clubs": club_stats,
        "recent_records": [
            {
                "id": r.id,
                "event_title": r.session.event.title,
                "club_name": r.session.event.club.name if r.session.event.club else "College Wide",
                "checkin_time": r.checkin_time,
                "status": r.status,
                "reason": r.override_reason
            }
            for r in records[-10:]
        ]
    }
