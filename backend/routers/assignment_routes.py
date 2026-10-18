import os
import shutil
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from backend.database import get_db, DELIVERABLES_DIR
from backend.models import (
    Club, ClubMembership, AssignmentProject, Submission, Evaluation, ClubResource, User, Certificate, AuditLog
)
from backend.schemas import (
    AssignmentCreate, AssignmentOut, SubmissionCreate, SubmissionOut, EvaluationCreate
)
from backend.auth import get_current_user, get_optional_user

router = APIRouter(prefix="/api/assignments", tags=["Assignments, Projects & Evaluation"])

UPLOAD_DIR = DELIVERABLES_DIR

@router.get("", response_model=List[AssignmentOut])
def list_assignments(
    club_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(AssignmentProject)
    if club_id:
        query = query.filter(AssignmentProject.club_id == club_id)
    else:
        # Filter to enrolled clubs if student
        if current_user.role == "STUDENT":
            my_club_ids = [m.club_id for m in current_user.memberships if m.status == "ACTIVE"]
            query = query.filter(AssignmentProject.club_id.in_(my_club_ids))

    assignments = query.order_by(AssignmentProject.due_date.asc()).all()
    results = []
    for a in assignments:
        sub_count = db.query(Submission).filter(Submission.assignment_id == a.id).count()
        # Find current user's submission if any
        my_sub = db.query(Submission).filter(
            Submission.assignment_id == a.id,
            Submission.student_id == current_user.id
        ).first()

        my_sub_dict = None
        if my_sub:
            eval_dict = None
            if my_sub.evaluation:
                eval_dict = {
                    "content_score": my_sub.evaluation.content_score,
                    "presentation_score": my_sub.evaluation.presentation_score,
                    "participation_score": my_sub.evaluation.participation_score,
                    "total_score": my_sub.evaluation.total_score,
                    "feedback": my_sub.evaluation.feedback_comments
                }
            my_sub_dict = {
                "id": my_sub.id,
                "file_url": my_sub.file_url,
                "external_link": my_sub.external_link,
                "submitted_at": my_sub.submitted_at,
                "status": my_sub.status,
                "evaluation": eval_dict
            }

        results.append(AssignmentOut(
            id=a.id,
            club_id=a.club_id,
            club_name=a.club.name,
            event_id=a.event_id,
            title=a.title,
            description=a.description,
            assignment_type=a.assignment_type,
            due_date=a.due_date,
            max_score=a.max_score,
            submission_count=sub_count,
            my_submission=my_sub_dict
        ))
    return results

@router.post("", response_model=AssignmentOut)
def create_assignment(
    assignment_in: AssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    club = db.query(Club).filter(Club.id == assignment_in.club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Only members with assigned posts (President, VP, Media, Finance) or Faculty Advisor can give assignments
    membership = db.query(ClubMembership).filter(
        ClubMembership.club_id == assignment_in.club_id,
        ClubMembership.user_id == current_user.id
    ).first()

    has_post = membership and membership.post in ["PRESIDENT", "VICE_PRESIDENT", "MEDIA_PRESIDENT", "FINANCE_PRESIDENT"]
    is_advisor = current_user.id == club.faculty_advisor_id or current_user.role in ["ADMIN", "CAMPUS_MANAGER"]

    if not (has_post or is_advisor):
        raise HTTPException(
            status_code=403,
            detail="Only club officers with an assigned post or Faculty Advisor can create assignments and projects."
        )

    assignment = AssignmentProject(
        club_id=assignment_in.club_id,
        event_id=assignment_in.event_id,
        title=assignment_in.title,
        description=assignment_in.description,
        assignment_type=assignment_in.assignment_type,
        due_date=assignment_in.due_date,
        max_score=assignment_in.max_score,
        created_by_id=current_user.id
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return AssignmentOut(
        id=assignment.id,
        club_id=assignment.club_id,
        club_name=club.name,
        event_id=assignment.event_id,
        title=assignment.title,
        description=assignment.description,
        assignment_type=assignment.assignment_type,
        due_date=assignment.due_date,
        max_score=assignment.max_score,
        submission_count=0,
        my_submission=None
    )

@router.post("/submit", response_model=SubmissionOut)
def submit_assignment(
    assignment_id: int = Form(...),
    external_link: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Student submits PPT, assignment document, or GitHub repo link."""
    assignment = db.query(AssignmentProject).filter(AssignmentProject.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Must be member of the club
    membership = db.query(ClubMembership).filter(
        ClubMembership.club_id == assignment.club_id,
        ClubMembership.user_id == current_user.id,
        ClubMembership.status == "ACTIVE"
    ).first()
    if not membership and current_user.role not in ["ADMIN"]:
        raise HTTPException(status_code=403, detail="You must be an active member of this club to submit work.")

    file_url = None
    if file and file.filename:
        file_ext = os.path.splitext(file.filename)[1]
        safe_name = f"sub_{assignment_id}_{current_user.id}_{int(datetime.utcnow().timestamp())}{file_ext}"
        dest_path = os.path.join(UPLOAD_DIR, safe_name)
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_url = f"/uploads/deliverables/{safe_name}"

    if not file_url and not external_link:
        raise HTTPException(status_code=400, detail="Please provide either an uploaded file (PPT/PDF) or an external project link.")

    # Check if existing submission
    sub = db.query(Submission).filter(
        Submission.assignment_id == assignment_id,
        Submission.student_id == current_user.id
    ).first()

    if not sub:
        sub = Submission(
            assignment_id=assignment_id,
            student_id=current_user.id,
            file_url=file_url,
            external_link=external_link,
            notes=notes,
            status="SUBMITTED",
            submitted_at=datetime.utcnow()
        )
        db.add(sub)
    else:
        if file_url:
            sub.file_url = file_url
        if external_link:
            sub.external_link = external_link
        sub.notes = notes
        sub.submitted_at = datetime.utcnow()
        sub.status = "SUBMITTED"

    db.commit()
    db.refresh(sub)

    return SubmissionOut(
        id=sub.id,
        assignment_id=assignment.id,
        assignment_title=assignment.title,
        student_id=current_user.id,
        student_name=current_user.name,
        roll_no=current_user.roll_no,
        file_url=sub.file_url,
        external_link=sub.external_link,
        notes=sub.notes,
        status=sub.status,
        submitted_at=sub.submitted_at,
        evaluation=None
    )

@router.get("/deadlines")
def get_deadlines_and_status(
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Returns upcoming deadlines (<= 48 hours alert) and project completion status.
    Strictly gated by role eligibility:
    - Guests: only public dates.
    - Students: enrolled club assignments and personal submission statuses.
    - Presidents: only submissions and member progress for their own club.
    - Domain Authority: ecosystem-wide overview.
    """
    now = datetime.utcnow()
    notifications = []

    if not current_user:
        clubs = db.query(Club).filter(Club.is_recruiting == True).all()
        for c in clubs:
            if c.recruitment_deadline and c.recruitment_deadline > now:
                diff = c.recruitment_deadline - now
                hours = int(diff.total_seconds() // 3600)
                if hours <= 48:
                    notifications.append({
                        "id": f"rec_{c.id}",
                        "type": "RECRUITMENT",
                        "urgency": "CRITICAL",
                        "title": f"Recruitment Closing: {c.name}",
                        "club_name": c.name,
                        "club_id": c.id,
                        "deadline": c.recruitment_deadline.isoformat(),
                        "hours_remaining": hours,
                        "message": f"⚠️ Enrolment for {c.name} closes in {hours} hours!"
                    })
        return {
            "eligible": False,
            "role": "GUEST",
            "notifications": notifications,
            "project_overview": {
                "total_projects": 0,
                "submitted_projects": 0,
                "pending_projects": 0,
                "all_submitted": False,
                "message": "Sign in to view your enrolled club assignments and submission status."
            }
        }

    is_domain_auth = getattr(current_user, "is_domain_authorized", False) or current_user.role in ["ADMIN", "CAMPUS_MANAGER"]

    my_memberships = db.query(ClubMembership).filter(
        ClubMembership.user_id == current_user.id,
        ClubMembership.status == "ACTIVE"
    ).all()
    my_club_ids = [m.club_id for m in my_memberships]
    pres_club_ids = [m.club_id for m in my_memberships if m.post in ["PRESIDENT", "VICE_PRESIDENT"]]

    query = db.query(AssignmentProject)
    if not is_domain_auth:
        if pres_club_ids:
            query = query.filter(AssignmentProject.club_id.in_(pres_club_ids))
        else:
            query = query.filter(AssignmentProject.club_id.in_(my_club_ids))

    assignments = query.order_by(AssignmentProject.due_date.asc()).all()
    total_projects = len(assignments)
    submitted_count = 0
    project_details = []

    for a in assignments:
        diff = a.due_date - now
        hours = int(diff.total_seconds() // 3600) if a.due_date > now else 0
        is_urgent = 0 <= hours <= 48

        my_sub = db.query(Submission).filter(
            Submission.assignment_id == a.id,
            Submission.student_id == current_user.id
        ).first()

        sub_status = "SUBMITTED" if my_sub else "PENDING"
        if my_sub:
            submitted_count += 1

        club_stats = None
        if a.club_id in pres_club_ids or is_domain_auth:
            total_members = db.query(ClubMembership).filter(ClubMembership.club_id == a.club_id, ClubMembership.status == "ACTIVE").count()
            total_subs = db.query(Submission).filter(Submission.assignment_id == a.id).count()
            club_stats = f"{total_subs}/{total_members} members submitted"

        project_details.append({
            "assignment_id": a.id,
            "title": a.title,
            "club_id": a.club_id,
            "club_name": a.club.name,
            "due_date": a.due_date.isoformat(),
            "hours_remaining": hours,
            "status": sub_status,
            "score": my_sub.evaluation.total_score if (my_sub and my_sub.evaluation) else None,
            "club_stats": club_stats
        })

        if is_urgent:
            msg = f"⚠️ Project Due in {hours}h: '{a.title}' ({a.club.name})!"
            if sub_status == "SUBMITTED":
                msg = f"✓ Project Delivered: You submitted '{a.title}' for {a.club.name}."
            notifications.append({
                "id": f"assign_{a.id}",
                "type": "PROJECT_DEADLINE",
                "urgency": "CRITICAL" if sub_status == "PENDING" else "INFO",
                "title": a.title,
                "club_name": a.club.name,
                "club_id": a.club_id,
                "due_date": a.due_date.isoformat(),
                "hours_remaining": hours,
                "user_submission_status": sub_status,
                "club_stats": club_stats,
                "message": msg
            })

    # Club recruitment notices
    for m in my_memberships:
        club = m.club
        if club and club.recruitment_deadline and club.recruitment_deadline > now:
            diff = club.recruitment_deadline - now
            hours = int(diff.total_seconds() // 3600)
            if hours <= 48:
                notifications.append({
                    "id": f"club_rec_{club.id}",
                    "type": "RECRUITMENT",
                    "urgency": "WARNING",
                    "title": f"Recruitment Window Closing: {club.name}",
                    "club_name": club.name,
                    "club_id": club.id,
                    "due_date": club.recruitment_deadline.isoformat(),
                    "hours_remaining": hours,
                    "message": f"📢 Enrolment for {club.name} closes in {hours} hours!"
                })

    return {
        "eligible": True,
        "role": current_user.role,
        "is_domain_authorized": is_domain_auth,
        "is_president_of": pres_club_ids,
        "notifications": notifications,
        "project_overview": {
            "total_projects": total_projects,
            "submitted_projects": submitted_count,
            "pending_projects": total_projects - submitted_count,
            "all_submitted": (submitted_count == total_projects and total_projects > 0),
            "projects": project_details
        }
    }

@router.get("/submissions/{assignment_id}", response_model=List[SubmissionOut])
def list_submissions(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    assignment = db.query(AssignmentProject).filter(AssignmentProject.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    is_domain_auth = getattr(current_user, "is_domain_authorized", False) or current_user.role in ["ADMIN", "CAMPUS_MANAGER"]
    
    my_m = db.query(ClubMembership).filter(
        ClubMembership.club_id == assignment.club_id,
        ClubMembership.user_id == current_user.id
    ).first()
    is_this_club_lead = (my_m and my_m.post in ["PRESIDENT", "VICE_PRESIDENT", "FINANCE_PRESIDENT", "MEDIA_PRESIDENT"]) or (current_user.id == assignment.club.faculty_advisor_id)

    if is_domain_auth or is_this_club_lead:
        submissions = db.query(Submission).filter(Submission.assignment_id == assignment_id).all()
    else:
        submissions = db.query(Submission).filter(
            Submission.assignment_id == assignment_id,
            Submission.student_id == current_user.id
        ).all()

    results = []
    for s in submissions:
        eval_dict = None
        if s.evaluation:
            eval_dict = {
                "id": s.evaluation.id,
                "content_score": s.evaluation.content_score,
                "presentation_score": s.evaluation.presentation_score,
                "participation_score": s.evaluation.participation_score,
                "total_score": s.evaluation.total_score,
                "feedback": s.evaluation.feedback_comments,
                "evaluated_by": s.evaluation.evaluated_by.name if s.evaluation.evaluated_by else None
            }
        results.append(SubmissionOut(
            id=s.id,
            assignment_id=s.assignment_id,
            assignment_title=s.assignment.title,
            student_id=s.student_id,
            student_name=s.student.name,
            roll_no=s.student.roll_no,
            file_url=s.file_url,
            external_link=s.external_link,
            notes=s.notes,
            status=s.status,
            submitted_at=s.submitted_at,
            evaluation=eval_dict
        ))
    return results

@router.post("/evaluate")
def evaluate_submission(
    eval_in: EvaluationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Coordinators or Faculty Advisors grade submission on standardized 3-part rubric:
    1. Content Score (0-10)
    2. Presentation Score (0-10)
    3. Participation Score (0-10)
    Total: 0-30 points
    """
    sub = db.query(Submission).filter(Submission.id == eval_in.submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    club = sub.assignment.club
    membership = db.query(ClubMembership).filter(
        ClubMembership.club_id == club.id,
        ClubMembership.user_id == current_user.id
    ).first()

    has_post = membership and membership.post in ["PRESIDENT", "VICE_PRESIDENT"]
    is_advisor = current_user.id == club.faculty_advisor_id or current_user.role in ["ADMIN", "CAMPUS_MANAGER"]

    if not (has_post or is_advisor):
        raise HTTPException(status_code=403, detail="Only Club Leadership or Faculty Advisor can evaluate submissions.")

    total = eval_in.content_score + eval_in.presentation_score + eval_in.participation_score

    evaluation = db.query(Evaluation).filter(Evaluation.submission_id == sub.id).first()
    if not evaluation:
        evaluation = Evaluation(
            submission_id=sub.id,
            evaluated_by_id=current_user.id,
            content_score=eval_in.content_score,
            presentation_score=eval_in.presentation_score,
            participation_score=eval_in.participation_score,
            total_score=total,
            feedback_comments=eval_in.comments,
            evaluated_at=datetime.utcnow()
        )
        db.add(evaluation)
    else:
        evaluation.content_score = eval_in.content_score
        evaluation.presentation_score = eval_in.presentation_score
        evaluation.participation_score = eval_in.participation_score
        evaluation.total_score = total
        evaluation.feedback_comments = eval_in.comments
        evaluation.evaluated_by_id = current_user.id
        evaluation.evaluated_at = datetime.utcnow()

    sub.status = "EVALUATED"

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="SUBMISSION_EVALUATION",
        target_type="EVALUATION",
        target_id=str(sub.id),
        details=f"Evaluated submission for {sub.student.name} with score {total}/30"
    )
    db.add(audit)
    db.commit()

    return {
        "message": f"Evaluation saved! Total score: {total}/30",
        "content_score": eval_in.content_score,
        "presentation_score": eval_in.presentation_score,
        "participation_score": eval_in.participation_score,
        "total_score": total,
        "comments": eval_in.comments
    }

@router.get("/resources/{club_id}")
def list_club_resources(
    club_id: int,
    db: Session = Depends(get_db)
):
    resources = db.query(ClubResource).filter(ClubResource.club_id == club_id).order_by(ClubResource.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "file_url": r.file_url,
            "link_url": r.link_url,
            "uploaded_by": r.uploaded_by.name,
            "created_at": r.created_at
        }
        for r in resources
    ]

@router.post("/resources")
def share_club_resource(
    club_id: int = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    link_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    membership = db.query(ClubMembership).filter(
        ClubMembership.club_id == club_id,
        ClubMembership.user_id == current_user.id
    ).first()
    has_post = membership and membership.post in ["PRESIDENT", "VICE_PRESIDENT", "MEDIA_PRESIDENT", "FINANCE_PRESIDENT"]
    is_advisor = current_user.id == club.faculty_advisor_id or current_user.role in ["ADMIN", "CAMPUS_MANAGER"]

    if not (has_post or is_advisor):
        raise HTTPException(status_code=403, detail="Only officers with an assigned post or Faculty Advisor can share files.")

    file_url = None
    if file and file.filename:
        file_ext = os.path.splitext(file.filename)[1]
        safe_name = f"res_{club_id}_{int(datetime.utcnow().timestamp())}{file_ext}"
        dest_path = os.path.join(UPLOAD_DIR, safe_name)
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_url = f"/uploads/deliverables/{safe_name}"

    res = ClubResource(
        club_id=club_id,
        uploaded_by_id=current_user.id,
        title=title,
        description=description,
        file_url=file_url,
        link_url=link_url
    )
    db.add(res)
    db.commit()
    db.refresh(res)

    return {"message": "Resource shared successfully", "id": res.id, "title": res.title}
