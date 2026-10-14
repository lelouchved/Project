from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Event, Club, ClubMembership, User, AttendanceSession
from backend.schemas import EventCreate, EventOut
from backend.auth import get_current_user, get_optional_user

router = APIRouter(prefix="/api/events", tags=["Events & Calendar"])

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
    2. MSOT Student / Non-Club: Sees PUBLIC and CAMPUS_STUDENTS events (recruiting dates, flagship events, college dates).
    3. Club Members & Leadership: Sees all above + CLUB_ONLY events for clubs they belong to.
    """
    query = db.query(Event)

    if not current_user:
        # Tier 1: Public / Anonymous
        query = query.filter(Event.visibility == "PUBLIC")
    else:
        # Tier 2 & 3
        if current_user.role in ["ADMIN", "CAMPUS_MANAGER"]:
            # College Leadership sees all
            pass
        else:
            # Enrolled clubs for this student/advisor
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
            has_active_session=has_active
        ))
    return results

@router.post("", response_model=EventOut)
def create_event(
    event_in: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    All members that have an assigned post (President, VP, Media, Finance)
    or Faculty Advisor / Campus Manager can add upcoming events.
    """
    if event_in.club_id:
        club = db.query(Club).filter(Club.id == event_in.club_id).first()
        if not club:
            raise HTTPException(status_code=404, detail="Club not found")

        membership = db.query(ClubMembership).filter(
            ClubMembership.club_id == event_in.club_id,
            ClubMembership.user_id == current_user.id
        ).first()

        has_post = membership and membership.post in ["PRESIDENT", "VICE_PRESIDENT", "MEDIA_PRESIDENT", "FINANCE_PRESIDENT"]
        is_faculty = current_user.id == club.faculty_advisor_id or current_user.role in ["ADMIN", "CAMPUS_MANAGER"]

        if not (has_post or is_faculty):
            raise HTTPException(
                status_code=403,
                detail="Only members with an assigned post (President, VP, Media, Finance) or Faculty Advisor can schedule events."
            )
    else:
        # College-wide event
        if current_user.role not in ["ADMIN", "CAMPUS_MANAGER"]:
            raise HTTPException(status_code=403, detail="Only Campus Managers/Admins can schedule college-wide events.")

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
        has_active_session=False
    )
