from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
import os
import shutil

from backend.database import get_db
from backend.models import Club, ClubMembership, User, AuditLog
from backend.schemas import ClubCreate, ClubOut, MembershipOut
from backend.auth import get_current_user, get_optional_user

router = APIRouter(prefix="/api/clubs", tags=["Clubs Management"])

UPLOAD_DIR = "./uploads/logos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
        # Extract executive posts
        posts_map = {
            "president": None,
            "vice_president": None,
            "finance_president": None,
            "media_president": None
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
        "media_president": None
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

@router.put("/{club_id}/assign-post")
def assign_club_post(
    club_id: int,
    target_user_id: int,
    post: str, # PRESIDENT, VICE_PRESIDENT, FINANCE_PRESIDENT, MEDIA_PRESIDENT, MEMBER
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Domain Authorized Users (via passkey "Code Geass"), Faculty Advisor, Campus Manager, Admin, or President
    is_domain_auth = getattr(current_user, "is_domain_authorized", False) or current_user.role in ["ADMIN", "CAMPUS_MANAGER"]
    my_m = db.query(ClubMembership).filter(
        ClubMembership.club_id == club_id,
        ClubMembership.user_id == current_user.id
    ).first()
    is_pres = my_m and my_m.post == "PRESIDENT"
    is_advisor = current_user.id == club.faculty_advisor_id

    if not (is_domain_auth or is_pres or is_advisor):
        raise HTTPException(
            status_code=403,
            detail="Only Authorized Keyholders with Domain Authority or Club President/Advisor can modify club posts."
        )

    valid_posts = ["PRESIDENT", "VICE_PRESIDENT", "FINANCE_PRESIDENT", "MEDIA_PRESIDENT", "MEMBER"]
    post_upper = post.upper()
    if post_upper not in valid_posts:
        raise HTTPException(status_code=400, detail=f"Invalid post. Valid posts are: {', '.join(valid_posts)}")

    membership = db.query(ClubMembership).filter(
        ClubMembership.club_id == club_id,
        ClubMembership.user_id == target_user_id
    ).first()
    if not membership:
        if is_domain_auth:
            membership = ClubMembership(
                club_id=club_id,
                user_id=target_user_id,
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
        details=f"Authorized user {current_user.name} changed user {target_user_id} post from {old_post} to {post_upper} in club {club.name}"
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
            status=m.status,
            joined_at=m.joined_at
        ))
    return results
