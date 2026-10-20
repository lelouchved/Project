from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    Event, Club, ClubMembership, User, AttendanceSession, AssignmentProject, Submission, AuditLog
)
from backend.schemas import EventCreate, EventOut
from backend.auth import get_current_user, get_optional_user

router = APIRouter(prefix="/api/events", tags=["Events & Calendar"])

class ClubImportantEventCreate(BaseModel):
    club_id: int
    title: str
    description: Optional[str] = None
    date: datetime
    venue: str = "Campus Auditorium / Lab"
    deliverable_info: Optional[str] = None

@router.get("", response_model=List[EventOut])
def list_events(
    event_type: Optional[str] = None, # CLUB_DAY, RECRUITING, FLAGSHIP_EVENT, IMPORTANT_DATE
    club_id: Optional[int] = None,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Enforces 3-tier audience visibility:
    1. Public / Anonymous: Only sees PUBLIC events & showcases.
    2. MSOT Student / Non-Club: Sees PUBLIC and CAMPUS_STUDENTS events.
    3. Club Members & Leadership: Sees all above + CLUB_ONLY events for clubs they belong to.
    """
    query = db.query(Event)

    if not current_user:
        query = query.filter(Event.visibility == "PUBLIC")
    else:
        if current_user.role in ["ADMIN", "CAMPUS_MANAGER"]:
            pass
        else:
            my_club_ids = [m.club_id for m in current_user.memberships if m.status == "ACTIVE"]
            if current_user.role == "FACULTY_ADVISOR":
                advised_club_ids = [c.id for c in current_user.advised_clubs]
                my_club_ids = list(set(my_club_ids + advised_club_ids))

            query = query.filter(
                (Event.visibility.in_(["PUBLIC", "CAMPUS_STUDENTS"])) |
                ((Event.visibility == "CLUB_ONLY") & (Event.club_id.in_(my_club_ids)))
            )

    if event_type:
        query = query.filter(Event.event_type == event_type)
    if club_id:
        query = query.filter(Event.club_id == club_id)

    events = query.order_by(Event.date.asc()).all()
    results = []
    for e in events:
        has_active = bool(e.attendance_session and e.attendance_session.is_active)
        creator_name = e.created_by.name if e.created_by else None
        results.append(EventOut(
            id=e.id,
            club_id=e.club_id,
            club_name=e.club.name if e.club else "MSOT Central",
            title=e.title,
            description=e.description,
            event_type=e.event_type,
            visibility=e.visibility,
            date=e.date,
            venue=e.venue,
            deliverable_info=e.deliverable_info,
            status=e.status,
            is_important=bool(e.is_important),
            has_active_session=has_active,
            created_by_name=creator_name
        ))
    return results

@router.get("/common-calendar")
def get_common_calendar(
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Common Public Calendar visible to everyone (Guests, Students, Visitors, Faculty).
    Shows upcoming public & campus-wide events, hackathons, and Saturday Club Days.
    Includes authority metadata indicating if the user has permission to schedule/edit.
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=24)

    # Check if user is a non-Mirai entity (visitor, guest, or categorized as NON_MIRAI)
    is_non_mirai = False
    if current_user:
        is_non_mirai = (
            getattr(current_user, "user_category", None) == "NON_MIRAI"
            or getattr(current_user, "is_mirai_entity", True) is False
        )
    else:
        is_non_mirai = True

    # Ensure baseline upcoming public events exist for external participants
    public_count = db.query(Event).filter(Event.visibility == "PUBLIC", Event.date >= now).count()
    if public_count < 2:
        ext_hack = Event(
            club_id=1,
            title="National DeepTech Hackathon 2026 (Open External Participation)",
            description="Inter-university hackathon where outside developers, innovators, and students build production AI & Web3 MVPs. External participation fully welcome.",
            event_type="FLAGSHIP_EVENT",
            visibility="PUBLIC",
            is_important=True,
            date=now + timedelta(days=14),
            venue="Mirai Innovation Arena & Virtual Discord",
            deliverable_info="Open GitHub repo and live demo link."
        )
        ext_summit = Event(
            club_id=2,
            title="Global AI Builders Keynote & Open Networking (External Guests Welcome)",
            description="Open guest keynote featuring top deep-tech founders and autonomous system researchers. Open for all university students and external attendees.",
            event_type="WORKSHOP",
            visibility="PUBLIC",
            is_important=False,
            date=now + timedelta(days=21),
            venue="HIET Main Auditorium & YouTube Live Broadcast",
            deliverable_info="RSVP and external attendee badge."
        )
        db.add(ext_hack)
        db.add(ext_summit)
        db.commit()

    if is_non_mirai:
        # Non-Mirai entity: ONLY upcoming public events where anyone from outside can participate!
        events = db.query(Event).filter(
            Event.visibility.in_(["PUBLIC", "PUBLIC_CAMPUS"]),
            Event.date >= now
        ).order_by(Event.date.asc()).all()
    else:
        events = db.query(Event).filter(
            ((Event.visibility.in_(["PUBLIC", "CAMPUS_STUDENTS"])) | 
            (Event.event_type.in_(["FLAGSHIP_EVENT", "CLUB_DAY", "RECRUITING", "IMPORTANT_DATE"]))),
            Event.date >= cutoff
        ).order_by(Event.date.asc()).all()

    is_domain_auth = False
    is_pres = False
    is_advisor = False
    authorized_clubs = []

    if current_user:
        is_domain_auth = getattr(current_user, "is_domain_authorized", False) or current_user.role in ["ADMIN", "CAMPUS_MANAGER"]
        pres_m = [m for m in current_user.memberships if m.post in ["PRESIDENT", "VICE_PRESIDENT"]]
        is_pres = len(pres_m) > 0
        adv_clubs = list(current_user.advised_clubs)
        is_advisor = len(adv_clubs) > 0 or current_user.role == "FACULTY_ADVISOR"

        if is_domain_auth:
            all_clubs = db.query(Club).all()
            authorized_clubs = [{"id": c.id, "name": c.name, "post": "Executive Leadership"} for c in all_clubs]
        else:
            seen_ids = set()
            for m in pres_m:
                if m.club and m.club_id not in seen_ids:
                    seen_ids.add(m.club_id)
                    authorized_clubs.append({"id": m.club_id, "name": m.club.name, "post": m.post})
            for c in adv_clubs:
                if c.id not in seen_ids:
                    seen_ids.add(c.id)
                    authorized_clubs.append({"id": c.id, "name": c.name, "post": "FACULTY_ADVISOR"})
    if is_non_mirai:
        can_update = False
        authorized_clubs = []
        is_domain_auth = False
        is_pres = False
        is_advisor = False
    else:
        can_update = is_domain_auth or is_pres or is_advisor

    results = []
    for e in events:
        has_active = bool(e.attendance_session and e.attendance_session.is_active)
        results.append({
            "id": e.id,
            "club_id": e.club_id,
            "club_name": e.club.name if e.club else "MSOT Central",
            "title": e.title,
            "description": e.description,
            "event_type": e.event_type,
            "visibility": e.visibility,
            "date": e.date.isoformat(),
            "time": e.date.strftime("%I:%M %p"),
            "venue": e.venue,
            "deliverable_info": e.deliverable_info,
            "status": e.status,
            "is_important": bool(e.is_important),
            "has_active_session": has_active,
            "created_by_name": e.created_by.name if e.created_by else None
        })

    return {
        "status": "success",
        "user_has_authority": can_update,
        "is_president": is_pres,
        "is_advisor": is_advisor,
        "is_domain_authorized": is_domain_auth,
        "authorized_clubs": authorized_clubs,
        "total_events": len(results),
        "events": results
    }

@router.get("/personal-calendar")
def get_personal_calendar(
    user_id: Optional[int] = Query(None, description="Specific user ID to view personal calendar for"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Personal Calendar: Specific to every particular user ID.
    Shows all important dates for this user:
    1. Important events pushed specifically to club members by President / Club Advisor.
    2. Assignment / Project Deadlines with personal submission status.
    3. Saturday Club Sessions for enrolled clubs.
    4. Club recruitment closures.
    5. Public college summits.
    """
    # Build users directory for instant preview of any particular member ID
    users_directory = [
        {
            "id": u.id,
            "name": u.name,
            "role": u.role,
            "roll_no": u.roll_no or "N/A",
            "enrolled_clubs": [m.club.name for m in u.memberships if m.club and m.status == "ACTIVE"]
        }
        for u in db.query(User).order_by(User.id.asc()).all()
    ]

    target_user = None
    if user_id is not None:
        target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        target_user = current_user

    if not target_user:
        public_events = db.query(Event).filter(
            Event.visibility == "PUBLIC"
        ).order_by(Event.date.asc()).all()

        items = []
        for e in public_events:
            items.append({
                "id": f"pub_event_{e.id}",
                "event_id": e.id,
                "title": e.title,
                "description": e.description,
                "date": e.date.isoformat(),
                "time": e.date.strftime("%I:%M %p"),
                "venue": e.venue,
                "category": "PUBLIC_EVENT",
                "club_id": e.club_id,
                "club_name": e.club.name if e.club else "MSOT Central",
                "is_important": bool(e.is_important),
                "pushed_by_authority": False,
                "badge": "Public Event",
                "badge_color": "blue",
                "deliverable_info": e.deliverable_info
            })
        return {
            "status": "success",
            "eligible": False,
            "role": "GUEST",
            "message": "Sign in or select a member ID to view personal calendar with enrolled club milestones and president-assigned events.",
            "total_items": len(items),
            "items": items,
            "users_directory": users_directory
        }

    is_domain_auth = getattr(target_user, "is_domain_authorized", False) or target_user.role in ["ADMIN", "CAMPUS_MANAGER"]

    my_memberships = db.query(ClubMembership).filter(
        ClubMembership.user_id == target_user.id,
        ClubMembership.status == "ACTIVE"
    ).all()
    my_club_ids = [m.club_id for m in my_memberships]
    pres_club_ids = [m.club_id for m in my_memberships if m.post in ["PRESIDENT", "VICE_PRESIDENT"]]

    advised_clubs = db.query(Club).filter(Club.faculty_advisor_id == target_user.id).all()
    adv_club_ids = [c.id for c in advised_clubs]

    all_relevant_club_ids = list(set(my_club_ids + adv_club_ids))

    items = []

    # 1. Events for relevant clubs (including President/Advisor pushed milestones)
    query_events = db.query(Event)
    if not is_domain_auth:
        query_events = query_events.filter(
            (Event.visibility == "PUBLIC") |
            ((Event.visibility.in_(["CLUB_ONLY", "CAMPUS_STUDENTS"])) & (Event.club_id.in_(all_relevant_club_ids)))
        )
    events = query_events.order_by(Event.date.asc()).all()

    for e in events:
        is_club_important = bool(e.is_important or e.event_type == "IMPORTANT_DATE")
        creator_name = e.created_by.name if e.created_by else "Club Leadership"
        creator_post = "President / Advisor"
        if e.created_by and e.club_id:
            m = db.query(ClubMembership).filter(ClubMembership.club_id == e.club_id, ClubMembership.user_id == e.created_by.id).first()
            if m and m.post:
                creator_post = m.post.replace('_', ' ').title()
            elif e.club and e.created_by.id == e.club.faculty_advisor_id:
                creator_post = "Club Faculty Advisor"

        badge = "Important Event" if is_club_important else ("Saturday Club Day" if e.event_type == "CLUB_DAY" else "Campus Event")
        badge_color = "amber" if is_club_important else ("blue" if e.event_type == "CLUB_DAY" else "purple")

        items.append({
            "id": f"event_{e.id}",
            "event_id": e.id,
            "title": e.title,
            "description": e.description,
            "date": e.date.isoformat(),
            "time": e.date.strftime("%I:%M %p"),
            "venue": e.venue,
            "category": "CLUB_IMPORTANT_EVENT" if is_club_important else "SESSION_EVENT",
            "club_id": e.club_id,
            "club_name": e.club.name if e.club else "MSOT Central",
            "is_important": is_club_important,
            "pushed_by_authority": is_club_important,
            "created_by_name": creator_name,
            "creator_post": creator_post,
            "badge": f"👑 {badge} (by {creator_post})" if is_club_important else badge,
            "badge_color": badge_color,
            "deliverable_info": e.deliverable_info
        })

    # 2. Assignment / Project Deadlines for Enrolled Clubs
    query_assign = db.query(AssignmentProject)
    if not is_domain_auth:
        query_assign = query_assign.filter(AssignmentProject.club_id.in_(all_relevant_club_ids))
    assignments = query_assign.order_by(AssignmentProject.due_date.asc()).all()

    now = datetime.utcnow()
    for a in assignments:
        my_sub = db.query(Submission).filter(
            Submission.assignment_id == a.id,
            Submission.student_id == target_user.id
        ).first()

        sub_status = "SUBMITTED" if my_sub else "PENDING"
        hours_left = int((a.due_date - now).total_seconds() // 3600) if a.due_date > now else 0
        is_urgent = (0 <= hours_left <= 48 and sub_status == "PENDING")

        score = my_sub.evaluation.total_score if (my_sub and my_sub.evaluation) else None

        items.append({
            "id": f"assign_{a.id}",
            "assignment_id": a.id,
            "title": f"Deliverable Deadline: {a.title}",
            "description": a.description,
            "date": a.due_date.isoformat(),
            "time": a.due_date.strftime("%I:%M %p"),
            "venue": "Digital Deliverable Submission Vault",
            "category": "ASSIGNMENT_DEADLINE",
            "club_id": a.club_id,
            "club_name": a.club.name if a.club else "Club",
            "is_important": is_urgent or sub_status == "PENDING",
            "pushed_by_authority": False,
            "submission_status": sub_status,
            "hours_remaining": hours_left,
            "is_urgent": is_urgent,
            "score": score,
            "max_score": a.max_score,
            "badge": "✓ Submitted" if sub_status == "SUBMITTED" else (f"⚠️ Due in {hours_left}h" if is_urgent else "Pending Submission"),
            "badge_color": "emerald" if sub_status == "SUBMITTED" else ("rose" if is_urgent else "amber"),
            "deliverable_info": f"Max Score: {a.max_score} pts"
        })

    # 3. Recruitment Deadlines
    for m in my_memberships:
        c = m.club
        if c and c.recruitment_deadline:
            items.append({
                "id": f"rec_{c.id}",
                "title": f"Recruitment Window Closing: {c.name}",
                "description": f"Enrolment closes for {c.name}.",
                "date": c.recruitment_deadline.isoformat(),
                "time": c.recruitment_deadline.strftime("%I:%M %p"),
                "venue": "Campus Enrolment Portal",
                "category": "RECRUITMENT",
                "club_id": c.id,
                "club_name": c.name,
                "is_important": False,
                "pushed_by_authority": False,
                "badge": "Enrolment Deadline",
                "badge_color": "amber",
                "deliverable_info": "Recruitment window"
            })

    # 4. Personal Reminders & Notes (Private to target_user only)
    personal_notes = db.query(Event).filter(
        Event.visibility == "PERSONAL",
        Event.created_by_id == target_user.id
    ).order_by(Event.date.asc()).all()

    for pn in personal_notes:
        items.append({
            "id": f"personal_note_{pn.id}",
            "event_id": pn.id,
            "title": pn.title,
            "description": pn.description,
            "date": pn.date.isoformat(),
            "time": pn.date.strftime("%I:%M %p"),
            "venue": pn.venue or "Personal Note",
            "category": "PERSONAL_NOTE",
            "club_id": None,
            "club_name": "Private Note",
            "is_important": False,
            "pushed_by_authority": False,
            "is_personal": True,
            "badge": "📝 Personal Note",
            "badge_color": "emerald",
            "deliverable_info": pn.deliverable_info
        })

    # Sort all personal calendar items chronologically
    items.sort(key=lambda x: x["date"])

    return {
        "status": "success",
        "eligible": True,
        "user_id": target_user.id,
        "user_name": target_user.name,
        "user_role": target_user.role,
        "roll_no": target_user.roll_no or "N/A",
        "is_president": len(pres_club_ids) > 0,
        "is_advisor": len(adv_club_ids) > 0 or target_user.role == "FACULTY_ADVISOR",
        "is_domain_authorized": is_domain_auth,
        "president_of_clubs": pres_club_ids,
        "advised_club_ids": adv_club_ids,
        "enrolled_club_ids": my_club_ids,
        "enrolled_club_names": [m.club.name for m in my_memberships if m.club],
        "total_items": len(items),
        "items": items,
        "users_directory": users_directory
    }

@router.post("/club-important-event")
def add_important_club_event(
    data: ClubImportantEventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Authority Gated: Only Club Presidents and Club Advisors can add important events
    to their club members' personal calendars.
    """
    club = db.query(Club).filter(Club.id == data.club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    is_domain_auth = getattr(current_user, "is_domain_authorized", False) or current_user.role in ["ADMIN", "CAMPUS_MANAGER"]
    
    membership = db.query(ClubMembership).filter(
        ClubMembership.club_id == data.club_id,
        ClubMembership.user_id == current_user.id
    ).first()

    is_pres = membership and membership.post in ["PRESIDENT", "VICE_PRESIDENT"]
    is_advisor = (
        current_user.id == club.faculty_advisor_id
        or current_user.role == "FACULTY_ADVISOR"
        or getattr(current_user, "teacher_type", None) == "CLUB_ADVISOR"
        or getattr(current_user, "user_category", None) == "CLUB_ADVISOR"
    )

    if not (is_domain_auth or is_pres or is_advisor):
        raise HTTPException(
            status_code=403,
            detail="Only Club Presidents and Club Advisors have authority to add important events to club members' personal calendars."
        )

    event = Event(
        club_id=data.club_id,
        title=data.title,
        description=data.description,
        event_type="IMPORTANT_DATE",
        visibility="CLUB_ONLY",
        is_important=True,
        date=data.date,
        venue=data.venue,
        deliverable_info=data.deliverable_info,
        status="SCHEDULED",
        created_by_id=current_user.id
    )
    db.add(event)
    
    # Audit trail
    audit = AuditLog(
        user_id=current_user.id,
        action="ADD_IMPORTANT_CLUB_EVENT",
        target_type="CLUB_MEMBER_CALENDAR",
        target_id=str(club.id),
        details=f"Pushed important event '{data.title}' on {data.date} to all {club.name} members' personal calendars."
    )
    db.add(audit)
    db.commit()
    db.refresh(event)

    creator_role = "President" if is_pres else ("Club Advisor" if is_advisor else "Domain Authority")

    return {
        "status": "success",
        "message": f"Successfully added important event to all {club.name} members' personal calendars!",
        "event_id": event.id,
        "title": event.title,
        "club_name": club.name,
        "date": event.date.isoformat(),
        "pushed_by": current_user.name,
        "creator_role": creator_role
    }

class PersonalNoteCreate(BaseModel):
    title: str
    description: Optional[str] = None
    date: datetime
    venue: Optional[str] = "Personal Note"
    deliverable_info: Optional[str] = None

@router.post("/personal-note")
def add_personal_note(
    data: PersonalNoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Personal Calendar Editing for Students & All Members:
    Allows student candidates and all users to edit their calendar for themselves only.
    Cannot publish or mark important events for others.
    """
    event = Event(
        club_id=None,
        title=data.title.strip(),
        description=data.description.strip() if data.description else None,
        event_type="PERSONAL_NOTE",
        visibility="PERSONAL",
        is_important=False,
        date=data.date,
        venue=data.venue or "Personal Note",
        deliverable_info=data.deliverable_info,
        status="SCHEDULED",
        created_by_id=current_user.id
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "status": "success",
        "message": "Personal reminder added to your private calendar!",
        "event_id": event.id,
        "title": event.title,
        "date": event.date.isoformat(),
        "is_personal": True
    }

@router.post("", response_model=EventOut)
def create_event(
    event_in: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Common Calendar & Club Events Creator:
    - If visibility is PERSONAL: Any authenticated member / student candidate can create
      private calendar notes for themselves (is_important forced to False).
    - If visibility is PUBLIC, CAMPUS_STUDENTS, or CLUB_ONLY: Strictly requires Club President,
      Club Faculty Advisor, Campus Manager, or Admin authority. Student candidates get 403 Forbidden.
    """
    is_domain_auth = getattr(current_user, "is_domain_authorized", False) or current_user.role in ["ADMIN", "CAMPUS_MANAGER"]

    # Student personal note flow
    if event_in.visibility == "PERSONAL":
        # Force is_important to False for personal student notes
        event = Event(
            club_id=event_in.club_id,
            title=event_in.title,
            description=event_in.description,
            event_type="PERSONAL_NOTE",
            visibility="PERSONAL",
            date=event_in.date,
            venue=event_in.venue or "Personal Note",
            deliverable_info=event_in.deliverable_info,
            status="SCHEDULED",
            is_important=False,
            created_by_id=current_user.id
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        return EventOut(
            id=event.id,
            club_id=event.club_id,
            club_name=event.club.name if event.club else "Personal Note",
            title=event.title,
            description=event.description,
            event_type=event.event_type,
            visibility=event.visibility,
            date=event.date,
            venue=event.venue,
            deliverable_info=event.deliverable_info,
            status=event.status,
            is_important=False,
            has_active_session=False,
            created_by_name=current_user.name
        )

    # If publishing public/campus/club events, students are strictly forbidden
    if event_in.is_important and not is_domain_auth:
        # Check if user is president or advisor
        if event_in.club_id:
            membership = db.query(ClubMembership).filter(
                ClubMembership.club_id == event_in.club_id,
                ClubMembership.user_id == current_user.id
            ).first()
            is_pres = membership and membership.post in ["PRESIDENT", "VICE_PRESIDENT"]
            club = db.query(Club).filter(Club.id == event_in.club_id).first()
            is_advisor = club and current_user.id == club.faculty_advisor_id
            if not (is_pres or is_advisor):
                raise HTTPException(
                    status_code=403,
                    detail="Student candidates cannot publish or mark important events. You can only edit your own personal calendar by adding personal notes."
                )

    if event_in.club_id:
        club = db.query(Club).filter(Club.id == event_in.club_id).first()
        if not club:
            raise HTTPException(status_code=404, detail="Club not found")

        membership = db.query(ClubMembership).filter(
            ClubMembership.club_id == event_in.club_id,
            ClubMembership.user_id == current_user.id
        ).first()

        is_lead = membership and membership.post in ["PRESIDENT", "VICE_PRESIDENT", "MEDIA_PRESIDENT", "FINANCE_PRESIDENT"]
        is_faculty = current_user.id == club.faculty_advisor_id

        if not (is_domain_auth or is_lead or is_faculty):
            raise HTTPException(
                status_code=403,
                detail="Student candidates cannot publish or change club events. Only Club Presidents, Club Advisors, and Campus Leadership have authority to add or update events on the Common Calendar."
            )
    else:
        # College-wide event
        if not is_domain_auth:
            raise HTTPException(
                status_code=403,
                detail="Only Campus Managers, Admins, or Domain Keyholders have authority to schedule college-wide events."
            )

    event = Event(
        club_id=event_in.club_id,
        title=event_in.title,
        description=event_in.description,
        event_type=event_in.event_type,
        visibility=event_in.visibility,
        date=event_in.date,
        venue=event_in.venue,
        deliverable_info=event_in.deliverable_info,
        status="SCHEDULED",
        is_important=bool(event_in.is_important),
        created_by_id=current_user.id
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return EventOut(
        id=event.id,
        club_id=event.club_id,
        club_name=event.club.name if event.club else "MSOT Central",
        title=event.title,
        description=event.description,
        event_type=event.event_type,
        visibility=event.visibility,
        date=event.date,
        venue=event.venue,
        deliverable_info=event.deliverable_info,
        status=event.status,
        is_important=bool(event.is_important),
        has_active_session=False,
        created_by_name=current_user.name
    )

@router.delete("/{event_id}")
def delete_event(
    event_id: int,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Delete an event from the calendar.
    Requires President, Advisor, Admin, or Creator.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required to delete events")

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    is_domain_auth = getattr(current_user, "is_domain_authorized", False) or current_user.role in ["ADMIN", "CAMPUS_MANAGER"]
    pres_clubs = [m.club_id for m in current_user.memberships if m.post in ["PRESIDENT", "VICE_PRESIDENT"]]
    adv_clubs = [c.id for c in current_user.advised_clubs]

    can_delete = is_domain_auth or (event.club_id in pres_clubs) or (event.club_id in adv_clubs) or (event.created_by_id == current_user.id)
    if not can_delete:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this event.")

    title = event.title
    db.delete(event)
    db.commit()

    return {"status": "success", "message": f"Event '{title}' deleted successfully"}

