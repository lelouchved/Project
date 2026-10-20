from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
import os
import shutil

from backend.database import get_db, LOGOS_DIR
from backend.models import Club, ClubMembership, User, AuditLog, ClubPresidentReport
from backend.schemas import (
    ClubCreate, ClubOut, MembershipOut, KaizenBranchSelect,
    PresidentReportCreate, PresidentReportReview, PresidentReportOut,
    AssignPostRequest
)
from backend.auth import get_current_user, get_optional_user

router = APIRouter(prefix="/api/clubs", tags=["Clubs Management"])

UPLOAD_DIR = LOGOS_DIR

@router.get("", response_model=List[ClubOut])
def get_clubs(
    campus_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Club)
    if campus_id:
        query = query.filter(Club.campus_id == campus_id)
    clubs = query.all()
    
    output = []
    for c in clubs:
        memberships = db.query(ClubMembership).filter(ClubMembership.club_id == c.id).all()
        # Extract executive posts (Standard: President, VP, Finance, Media, General Secretary)
        posts_map = {
            "president": None,
            "vice_president": None,
            "finance_president": None,
            "media_president": None,
            "general_secretary": None
        }
        for m in memberships:
            key = m.post.lower()
            if key in posts_map:
                posts_map[key] = {
                    "user_id": m.user.id,
                    "name": m.user.name,
                    "email": m.user.email,
                    "roll_no": m.user.roll_no
                }
        
        output.append(ClubOut(
            id=c.id,
            name=c.name,
            category=c.category,
            logo_url=c.logo_url,
            description=c.description,
            campus_id=c.campus_id,
            campus_name=c.campus.name if c.campus else None,
            faculty_advisor_id=c.faculty_advisor_id,
            faculty_advisor_name=c.faculty_advisor.name if c.faculty_advisor else None,
            faculty_advisor_email=c.faculty_advisor.email if c.faculty_advisor else None,
            capacity=c.capacity,
            member_count=len(memberships),
            is_recruiting=c.is_recruiting,
            recruitment_deadline=c.recruitment_deadline,
            meeting_rules=c.meeting_rules,
            posts=posts_map
        ))
    return output

@router.get("/my-status")
def get_my_club_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns all club memberships for current user (both ACTIVE and PENDING)."""
    memberships = db.query(ClubMembership).filter(ClubMembership.user_id == current_user.id).all()
    results = {}
    for m in memberships:
        results[str(m.club_id)] = {
            "membership_id": m.id,
            "club_id": m.club_id,
            "status": m.status,
            "post": m.post,
            "joined_at": m.joined_at.isoformat() if m.joined_at else None
        }
    return results

@router.get("/{club_id}", response_model=ClubOut)
def get_club(club_id: int, db: Session = Depends(get_db)):
    c = db.query(Club).filter(Club.id == club_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Club not found")
    
    memberships = db.query(ClubMembership).filter(ClubMembership.club_id == c.id).all()
    posts_map = {
        "president": None,
        "vice_president": None,
        "finance_president": None,
        "media_president": None,
        "general_secretary": None
    }
    for m in memberships:
        key = m.post.lower()
        if key in posts_map:
            posts_map[key] = {
                "user_id": m.user.id,
                "name": m.user.name,
                "email": m.user.email,
                "roll_no": m.user.roll_no
            }

    return ClubOut(
        id=c.id,
        name=c.name,
        category=c.category,
        logo_url=c.logo_url,
        description=c.description,
        campus_id=c.campus_id,
        campus_name=c.campus.name if c.campus else None,
        faculty_advisor_id=c.faculty_advisor_id,
        faculty_advisor_name=c.faculty_advisor.name if c.faculty_advisor else None,
        faculty_advisor_email=c.faculty_advisor.email if c.faculty_advisor else None,
        capacity=c.capacity,
        member_count=len(memberships),
        is_recruiting=c.is_recruiting,
        recruitment_deadline=c.recruitment_deadline,
        meeting_rules=c.meeting_rules,
        posts=posts_map
    )

@router.post("", response_model=ClubOut)
def create_club(
    club_in: ClubCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only Admin, Campus Manager or Faculty Advisor can create clubs
    if current_user.role not in ["ADMIN", "CAMPUS_MANAGER", "FACULTY_ADVISOR"]:
        raise HTTPException(status_code=403, detail="Not authorized to create a club")

    # Verify faculty advisor is valid
    advisor = db.query(User).filter(User.id == club_in.faculty_advisor_id).first()
    if not advisor or advisor.role not in ["FACULTY_ADVISOR", "ADMIN"]:
        raise HTTPException(status_code=400, detail="Assigned Faculty Advisor must have a valid Teacher/Advisor account")

    club = Club(
        name=club_in.name,
        category=club_in.category,
        description=club_in.description,
        campus_id=club_in.campus_id,
        faculty_advisor_id=club_in.faculty_advisor_id,
        capacity=club_in.capacity or 60,
        is_recruiting=club_in.is_recruiting if club_in.is_recruiting is not None else True,
        recruitment_deadline=club_in.recruitment_deadline,
        meeting_rules=club_in.meeting_rules or "Every Saturday 10:00 AM - 1:00 PM"
    )
    db.add(club)
    db.commit()
    db.refresh(club)
    return get_club(club.id, db)

from pydantic import BaseModel

class ClubLogoUpdate(BaseModel):
    logo_url: str

def check_club_president_authority(club: Club, current_user: User, db: Session) -> bool:
    is_domain_auth = getattr(current_user, "is_domain_authorized", False) or current_user.role in ["ADMIN", "CAMPUS_MANAGER"]
    if is_domain_auth:
        return True

    # Check if user is President or Vice President of this club
    membership = db.query(ClubMembership).filter(
        ClubMembership.club_id == club.id,
        ClubMembership.user_id == current_user.id
    ).first()
    if membership and membership.post in ["PRESIDENT", "VICE_PRESIDENT"]:
        return True

    # Check if user is the Faculty Advisor
    if current_user.id == club.faculty_advisor_id:
        return True
    if current_user.role == "FACULTY_ADVISOR" and any(c.id == club.id for c in current_user.advised_clubs):
        return True

    return False

@router.post("/{club_id}/logo")
def upload_club_logo(
    club_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    if not check_club_president_authority(club, current_user, db):
        raise HTTPException(
            status_code=403,
            detail="Only Club Presidents, Faculty Advisors, and Campus Leadership have authority to update this club's logo."
        )

    # Save file
    file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ".png"
    if file_ext not in [".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"]:
        file_ext = ".png"
    safe_name = f"club_{club_id}_{int(datetime.utcnow().timestamp())}{file_ext}"
    dest_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    club.logo_url = f"/uploads/logos/{safe_name}"
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="UPDATE_CLUB_LOGO",
        target_type="CLUB",
        target_id=str(club_id),
        details=f"Updated official logo for {club.name}"
    )
    db.add(audit)
    db.commit()

    return {"status": "success", "message": f"Official logo for {club.name} updated successfully!", "logo_url": club.logo_url}

@router.put("/{club_id}/logo")
def update_club_logo_url(
    club_id: int,
    data: ClubLogoUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    if not check_club_president_authority(club, current_user, db):
        raise HTTPException(
            status_code=403,
            detail="Only Club Presidents, Faculty Advisors, and Campus Leadership have authority to update this club's logo."
        )

    club.logo_url = data.logo_url.strip()
    
    audit = AuditLog(
        user_id=current_user.id,
        action="UPDATE_CLUB_LOGO_URL",
        target_type="CLUB",
        target_id=str(club_id),
        details=f"Updated logo URL for {club.name}"
    )
    db.add(audit)
    db.commit()

    return {"status": "success", "message": f"Official logo for {club.name} updated successfully!", "logo_url": club.logo_url}

@router.put("/{club_id}/recruitment")
def toggle_recruitment(
    club_id: int,
    is_recruiting: bool,
    deadline: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # Check permissions (Faculty Advisor, President, VP, or Admin)
    membership = db.query(ClubMembership).filter(
        ClubMembership.club_id == club_id,
        ClubMembership.user_id == current_user.id
    ).first()
    is_lead = membership and membership.post in ["PRESIDENT", "VICE_PRESIDENT"]
    is_mgmt = current_user.role in ["ADMIN", "CAMPUS_MANAGER"] or current_user.id == club.faculty_advisor_id

    if not (is_lead or is_mgmt):
        raise HTTPException(status_code=403, detail="Only Club Leadership or Faculty Advisor can change recruitment status")

    club.is_recruiting = is_recruiting
    if deadline is not None:
        club.recruitment_deadline = deadline
    db.commit()
    return {"message": "Recruitment updated", "is_recruiting": club.is_recruiting, "deadline": club.recruitment_deadline}

@router.post("/{club_id}/join")
def join_club(
    club_id: int,
    post: Optional[str] = "MEMBER",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enforces student joining limits:
    1. Maximum 2 clubs per student.
    2. Capacity check (50-70 members).
    3. Prevents duplicate joining.
    """
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # 1. Check if already a member
    existing = db.query(ClubMembership).filter(
        ClubMembership.user_id == current_user.id,
        ClubMembership.club_id == club_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You are already a member or have a pending request for this club.")

    # 2. STRICT RULE: Every student can join up to 2 clubs only
    active_count = db.query(ClubMembership).filter(
        ClubMembership.user_id == current_user.id,
        ClubMembership.status == "ACTIVE"
    ).count()
    if active_count >= 2:
        raise HTTPException(
            status_code=400,
            detail="Limit reached: Each student can join a maximum of 2 clubs only."
        )

    # 3. Capacity check (50-70)
    current_members = db.query(ClubMembership).filter(
        ClubMembership.club_id == club_id,
        ClubMembership.status == "ACTIVE"
    ).count()
    if current_members >= club.capacity:
        raise HTTPException(
            status_code=400,
            detail=f"This club has reached its maximum recruitment capacity ({club.capacity} members)."
        )

    # 4. Check recruitment status
    if not club.is_recruiting and current_user.role == "STUDENT":
        raise HTTPException(
            status_code=400,
            detail="Recruitment is currently closed for this club."
        )

    membership = ClubMembership(
        user_id=current_user.id,
        club_id=club_id,
        post=post if current_user.role != "STUDENT" else "MEMBER",
        status="ACTIVE"
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)

    return {
        "message": f"Successfully joined {club.name}!",
        "club_id": club.id,
        "club_name": club.name,
        "post": membership.post,
        "remaining_slots_for_student": 2 - (active_count + 1)
    }

@router.post("/{club_id}/apply")
def apply_to_club(
    club_id: int,
    data: Optional[dict] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submits a membership application to the Club President:
    1. Checks if already member (ACTIVE) or already applied (PENDING).
    2. Enforces maximum 2 clubs rule.
    3. Enforces capacity and recruitment status.
    4. Creates ClubMembership with status='PENDING'.
    """
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # 1. Existing membership check
    existing = db.query(ClubMembership).filter(
        ClubMembership.user_id == current_user.id,
        ClubMembership.club_id == club_id
    ).first()
    if existing:
        if existing.status == "ACTIVE":
            raise HTTPException(status_code=400, detail=f"You are already an active enrolled member of {club.name}.")
        else:
            raise HTTPException(status_code=400, detail=f"You have already applied to {club.name}. Your application is pending President review.")

    # 2. Maximum 2 clubs limit (active + pending)
    enrolled_or_pending = db.query(ClubMembership).filter(
        ClubMembership.user_id == current_user.id,
        ClubMembership.status.in_(["ACTIVE", "PENDING"])
    ).count()
    if enrolled_or_pending >= 2:
        raise HTTPException(
            status_code=400,
            detail="Limit reached: Each student can be enrolled in or apply to a maximum of 2 clubs only."
        )

    # 3. Capacity check
    active_members = db.query(ClubMembership).filter(
        ClubMembership.club_id == club_id,
        ClubMembership.status == "ACTIVE"
    ).count()
    if active_members >= club.capacity:
        raise HTTPException(
            status_code=400,
            detail=f"This club has reached its maximum recruitment capacity ({club.capacity} members)."
        )

    # 4. Recruitment status check
    if not club.is_recruiting and current_user.role == "STUDENT":
        raise HTTPException(
            status_code=400,
            detail="Recruitment is currently closed for this club."
        )

    statement = (data or {}).get("statement", "Student application for membership")
    skills = (data or {}).get("skills", "")

    membership = ClubMembership(
        user_id=current_user.id,
        club_id=club_id,
        post="MEMBER",
        status="PENDING"
    )
    db.add(membership)

    audit = AuditLog(
        user_id=current_user.id,
        action="CLUB_MEMBERSHIP_APPLICATION",
        target_type="CLUB",
        target_id=str(club_id),
        details=f"Student {current_user.name} ({current_user.roll_no or current_user.email}) submitted application for {club.name}. Statement: {statement} | Skills: {skills}"
    )
    db.add(audit)
    db.commit()
    db.refresh(membership)

    return {
        "status": "success",
        "message": f"Application to join {club.name} submitted successfully! Your request has been sent to the Club President for approval.",
        "club_id": club.id,
        "club_name": club.name,
        "membership_id": membership.id,
        "membership_status": "PENDING"
    }

@router.get("/{club_id}/pending-applications")
def get_pending_applications(
    club_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetches all pending applications for a club (for President / Advisor / Campus Manager)."""
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    my_m = db.query(ClubMembership).filter(
        ClubMembership.club_id == club_id,
        ClubMembership.user_id == current_user.id
    ).first()
    is_lead = my_m and my_m.post in ["PRESIDENT", "VICE_PRESIDENT"]
    is_mgmt = current_user.role in ["ADMIN", "CAMPUS_MANAGER"] or current_user.id == club.faculty_advisor_id or getattr(current_user, "is_domain_authorized", False)

    if not (is_lead or is_mgmt):
        raise HTTPException(status_code=403, detail="Only Club Leadership or Faculty Advisors can review applications.")

    pending = db.query(ClubMembership).filter(
        ClubMembership.club_id == club_id,
        ClubMembership.status == "PENDING"
    ).all()

    return [
        {
            "membership_id": m.id,
            "user_id": m.user.id,
            "user_name": m.user.name,
            "user_email": m.user.email,
            "roll_no": m.user.roll_no,
            "applied_at": m.joined_at.isoformat() if m.joined_at else None
        }
        for m in pending
    ]

@router.post("/{club_id}/applications/{membership_id}/approve")
def approve_club_application(
    club_id: int,
    membership_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Club President or Advisor approves a pending membership application."""
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    my_m = db.query(ClubMembership).filter(
        ClubMembership.club_id == club_id,
        ClubMembership.user_id == current_user.id
    ).first()
    is_lead = my_m and my_m.post in ["PRESIDENT", "VICE_PRESIDENT"]
    is_mgmt = current_user.role in ["ADMIN", "CAMPUS_MANAGER"] or current_user.id == club.faculty_advisor_id or getattr(current_user, "is_domain_authorized", False)

    if not (is_lead or is_mgmt):
        raise HTTPException(status_code=403, detail="Only Club Leadership or Faculty Advisors can approve applications.")

    membership = db.query(ClubMembership).filter(
        ClubMembership.id == membership_id,
        ClubMembership.club_id == club_id
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Application not found")

    membership.status = "ACTIVE"
    audit = AuditLog(
        user_id=current_user.id,
        action="APPROVE_CLUB_APPLICATION",
        target_type="CLUB_MEMBERSHIP",
        target_id=str(membership.id),
        details=f"Leader {current_user.name} approved {membership.user.name} into {club.name}"
    )
    db.add(audit)
    db.commit()

    return {"status": "success", "message": f"{membership.user.name} is now an active member of {club.name}!"}

@router.post("/{club_id}/applications/{membership_id}/reject")
def reject_club_application(
    club_id: int,
    membership_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Club President rejects a pending application."""
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    my_m = db.query(ClubMembership).filter(
        ClubMembership.club_id == club_id,
        ClubMembership.user_id == current_user.id
    ).first()
    is_lead = my_m and my_m.post in ["PRESIDENT", "VICE_PRESIDENT"]
    is_mgmt = current_user.role in ["ADMIN", "CAMPUS_MANAGER"] or current_user.id == club.faculty_advisor_id or getattr(current_user, "is_domain_authorized", False)

    if not (is_lead or is_mgmt):
        raise HTTPException(status_code=403, detail="Only Club Leadership or Faculty Advisors can reject applications.")

    membership = db.query(ClubMembership).filter(
        ClubMembership.id == membership_id,
        ClubMembership.club_id == club_id
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Application not found")

    applicant_name = membership.user.name
    db.delete(membership)
    audit = AuditLog(
        user_id=current_user.id,
        action="REJECT_CLUB_APPLICATION",
        target_type="CLUB_MEMBERSHIP",
        target_id=str(membership_id),
        details=f"Leader {current_user.name} declined application from {applicant_name} for {club.name}"
    )
    db.add(audit)
    db.commit()

    return {"status": "success", "message": f"Application from {applicant_name} has been declined."}

@router.put("/{club_id}/assign-post")
@router.post("/{club_id}/assign-post")
def assign_club_post(
    club_id: int,
    data: Optional[AssignPostRequest] = None,
    target_user_id: Optional[int] = None,
    post: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    actual_target_user_id = data.target_user_id if data and data.target_user_id is not None else target_user_id
    actual_post = data.post if data and data.post is not None else post

    if actual_target_user_id is None or not actual_post:
        raise HTTPException(status_code=400, detail="target_user_id and post are required")

    # Governance Rule: Only Club Advisor (or Domain Authority / Admin) can assign leadership posts
    is_domain_auth = getattr(current_user, "is_domain_authorized", False) or current_user.role in ["ADMIN", "CAMPUS_MANAGER"]
    is_advisor = current_user.id == club.faculty_advisor_id or (current_user.role == "FACULTY_ADVISOR" and any(c.id == club.id for c in current_user.advised_clubs))

    if not (is_advisor or is_domain_auth):
        raise HTTPException(
            status_code=403,
            detail="Governance Policy: Only the assigned Club Advisor (or Domain Authority) has the authority to appoint students to leadership posts."
        )

    post_upper = actual_post.upper()
    is_kaizen = "kaizen" in club.name.lower()

    if is_kaizen:
        # Kaizen Club only has 2 executive posts: President and Vice President
        valid_posts = ["PRESIDENT", "VICE_PRESIDENT", "MEMBER"]
        if post_upper not in valid_posts:
            raise HTTPException(
                status_code=400,
                detail="Kaizen Club Special Governance Rule: Kaizen only permits 2 leadership posts (President and Vice President). Specialized operations are managed across its 4 branches (CPP Club, Dev Club, Kaizen Intelligence, Media Club)."
            )
    else:
        # Standard clubs have 5 leaders: President, VP, Finance President, Media President, General Secretary
        valid_posts = ["PRESIDENT", "VICE_PRESIDENT", "FINANCE_PRESIDENT", "MEDIA_PRESIDENT", "GENERAL_SECRETARY", "MEMBER"]
        if post_upper not in valid_posts:
            raise HTTPException(status_code=400, detail=f"Invalid post. Valid posts for standard clubs are: {', '.join(valid_posts)}")

    membership = db.query(ClubMembership).filter(
        ClubMembership.club_id == club_id,
        ClubMembership.user_id == actual_target_user_id
    ).first()
    if not membership:
        if is_domain_auth or is_advisor:
            membership = ClubMembership(
                club_id=club_id,
                user_id=actual_target_user_id,
                post=post_upper,
                status="ACTIVE"
            )
            db.add(membership)
            old_post = "NEW_ENROLLEE"
        else:
            raise HTTPException(status_code=404, detail="Student is not a member of this club")
    else:
        old_post = membership.post
        membership.post = post_upper

    # Log audit
    log = AuditLog(
        user_id=current_user.id,
        action="ASSIGN_CLUB_POST",
        target_type="CLUB_MEMBERSHIP",
        target_id=str(membership.id if membership.id else "new"),
        details=f"Advisor/Officer {current_user.name} changed user {target_user_id} post from {old_post} to {post_upper} in club {club.name}"
    )
    db.add(log)
    db.commit()

    return {"message": f"Successfully updated post to {post_upper} for member", "post": post_upper}

@router.delete("/{club_id}/members/{target_user_id}")
def remove_club_member(
    club_id: int,
    target_user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    is_domain_auth = getattr(current_user, "is_domain_authorized", False) or current_user.role in ["ADMIN", "CAMPUS_MANAGER"]
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    if not is_domain_auth and current_user.id != club.faculty_advisor_id:
        raise HTTPException(status_code=403, detail="Only Domain Authorized Officers can remove members.")

    membership = db.query(ClubMembership).filter(
        ClubMembership.club_id == club_id,
        ClubMembership.user_id == target_user_id
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    db.delete(membership)
    db.commit()
    return {"message": "Member removed successfully"}

@router.get("/{club_id}/members", response_model=List[MembershipOut])
def get_club_members(club_id: int, db: Session = Depends(get_db)):
    members = db.query(ClubMembership).filter(ClubMembership.club_id == club_id).all()
    results = []
    for m in members:
        results.append(MembershipOut(
            id=m.id,
            user_id=m.user.id,
            user_name=m.user.name,
            user_email=m.user.email,
            roll_no=m.user.roll_no,
            club_id=m.club.id,
            club_name=m.club.name,
            post=m.post,
            branch=m.branch,
            status=m.status,
            joined_at=m.joined_at
        ))
    return results

# ==================== KAIZEN SPECIAL BRANCH NETWORK ====================
KAIZEN_BRANCHES = [
    {
        "id": "cpp-club",
        "name": "CPP Club",
        "category": "DSA & Competitive Programming",
        "focus": "DSA, Competitive Programming, Hackathons",
        "description": "Mastering algorithms, data structures, Codeforces/LeetCode tracks, and national hackathon preparations.",
        "badge": "⚡ Algorithmic Track"
    },
    {
        "id": "dev-club",
        "name": "Dev Club",
        "category": "Web Dev & Full-Stack Coding",
        "focus": "Web Development, Full-Stack Architecture, Pure Coding",
        "description": "Pure coding, frontend UI engineering, robust APIs, scalable databases, and shipping web products.",
        "badge": "💻 Dev & Architecture"
    },
    {
        "id": "kaizen-intelligence",
        "name": "Kaizen Intelligence",
        "category": "AI Models & Robotics",
        "focus": "AI Models, Robotics, ML Pipelines & Data Science",
        "description": "Deep learning models, computer vision, natural language processing, intelligent bots, and autonomous robotics.",
        "badge": "🤖 AI & Autonomous"
    },
    {
        "id": "media-club",
        "name": "Media Club",
        "category": "Advertising & Social Content",
        "focus": "Advertising, Content Creation, Social Branding & Video Production",
        "description": "Promotional campaigns, campus event trailers, social branding, cinematic reels, and digital brand elevation.",
        "badge": "🎨 Brand & Media"
    }
]

@router.get("/{club_id}/branches")
def get_club_branches(club_id: int, db: Session = Depends(get_db)):
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    if "kaizen" in club.name.lower():
        return KAIZEN_BRANCHES
    return []

@router.post("/{club_id}/select-branch")
def select_kaizen_branch(
    club_id: int,
    data: KaizenBranchSelect,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    if "kaizen" not in club.name.lower():
        raise HTTPException(status_code=400, detail="Branch selection is only applicable to Kaizen Club.")

    membership = db.query(ClubMembership).filter(
        ClubMembership.club_id == club_id,
        ClubMembership.user_id == current_user.id
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="You must be an active enrolled member of Kaizen Club to choose a branch.")

    valid_branch_names = [b["name"] for b in KAIZEN_BRANCHES]
    if data.branch not in valid_branch_names:
        raise HTTPException(status_code=400, detail=f"Invalid branch. Must be one of: {', '.join(valid_branch_names)}")

    membership.branch = data.branch
    db.commit()

    return {
        "status": "success",
        "message": f"Successfully enrolled into Kaizen branch: {data.branch}",
        "branch": data.branch
    }

# ==================== PRESIDENT STRATEGIC REPORTING DESK ====================
@router.post("/{club_id}/president-report", response_model=PresidentReportOut)
def submit_president_report(
    club_id: int,
    data: PresidentReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    is_domain_auth = getattr(current_user, "is_domain_authorized", False) or current_user.role in ["ADMIN", "CAMPUS_MANAGER"]
    my_m = db.query(ClubMembership).filter(
        ClubMembership.club_id == club_id,
        ClubMembership.user_id == current_user.id
    ).first()
    is_pres = my_m and my_m.post == "PRESIDENT"

    if not (is_pres or is_domain_auth):
        raise HTTPException(
            status_code=403,
            detail="Governance Rule: Only the Club President has authority to submit vision and leadership reports to the Club Advisor."
        )

    report = ClubPresidentReport(
        club_id=club_id,
        president_id=current_user.id,
        advisor_id=club.faculty_advisor_id,
        title=data.title,
        vision_statement=data.vision_statement,
        vp_operational_orders=data.vp_operational_orders,
        finance_budget_overview=data.finance_budget_overview,
        media_campaign_plan=data.media_campaign_plan,
        general_secretary_notes=data.general_secretary_notes,
        status="SUBMITTED"
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    audit = AuditLog(
        user_id=current_user.id,
        action="PRESIDENT_REPORT_SUBMITTED",
        target_type="CLUB_PRESIDENT_REPORT",
        target_id=str(report.id),
        details=f"President {current_user.name} submitted vision report '{report.title}' for {club.name} to Advisor"
    )
    db.add(audit)
    db.commit()

    return PresidentReportOut(
        id=report.id,
        club_id=report.club_id,
        club_name=club.name,
        president_id=report.president_id,
        president_name=current_user.name,
        advisor_id=report.advisor_id,
        advisor_name=club.faculty_advisor.name if club.faculty_advisor else None,
        title=report.title,
        vision_statement=report.vision_statement,
        vp_operational_orders=report.vp_operational_orders,
        finance_budget_overview=report.finance_budget_overview,
        media_campaign_plan=report.media_campaign_plan,
        general_secretary_notes=report.general_secretary_notes,
        status=report.status,
        advisor_feedback=report.advisor_feedback,
        submitted_at=report.submitted_at,
        reviewed_at=report.reviewed_at
    )

@router.get("/{club_id}/president-reports", response_model=List[PresidentReportOut])
def get_president_reports(
    club_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    reports = db.query(ClubPresidentReport).filter(ClubPresidentReport.club_id == club_id).order_by(ClubPresidentReport.submitted_at.desc()).all()
    out = []
    for r in reports:
        out.append(PresidentReportOut(
            id=r.id,
            club_id=r.club_id,
            club_name=club.name,
            president_id=r.president_id,
            president_name=r.president.name if r.president else None,
            advisor_id=r.advisor_id,
            advisor_name=r.advisor.name if r.advisor else None,
            title=r.title,
            vision_statement=r.vision_statement,
            vp_operational_orders=r.vp_operational_orders,
            finance_budget_overview=r.finance_budget_overview,
            media_campaign_plan=r.media_campaign_plan,
            general_secretary_notes=r.general_secretary_notes,
            status=r.status,
            advisor_feedback=r.advisor_feedback,
            submitted_at=r.submitted_at,
            reviewed_at=r.reviewed_at
        ))
    return out

@router.put("/{club_id}/president-reports/{report_id}/feedback")
def review_president_report(
    club_id: int,
    report_id: int,
    data: PresidentReportReview,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    is_domain_auth = getattr(current_user, "is_domain_authorized", False) or current_user.role in ["ADMIN", "CAMPUS_MANAGER"]
    is_advisor = current_user.id == club.faculty_advisor_id or current_user.role == "FACULTY_ADVISOR"

    if not (is_advisor or is_domain_auth):
        raise HTTPException(
            status_code=403,
            detail="Governance Policy: Only the assigned Club Advisor (or Domain Authority) can review and provide feedback on President Vision Reports."
        )

    report = db.query(ClubPresidentReport).filter(
        ClubPresidentReport.id == report_id,
        ClubPresidentReport.club_id == club_id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Vision report not found")

    report.status = data.status.upper()
    report.advisor_feedback = data.advisor_feedback
    report.reviewed_at = datetime.utcnow()
    report.advisor_id = current_user.id

    audit = AuditLog(
        user_id=current_user.id,
        action="PRESIDENT_REPORT_REVIEW",
        target_type="CLUB_PRESIDENT_REPORT",
        target_id=str(report.id),
        details=f"Advisor {current_user.name} reviewed report '{report.title}' with status {report.status}"
    )
    db.add(audit)
    db.commit()

    return {
        "status": "success",
        "message": f"Vision Report updated to {report.status}",
        "report_id": report.id,
        "new_status": report.status,
        "advisor_feedback": report.advisor_feedback
    }

