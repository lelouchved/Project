import csv
import io
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import (
    Club, ClubMembership, AttendanceSession, AttendanceRecord, Submission, Evaluation, User, Campus
)
from backend.auth import get_current_user

router = APIRouter(prefix="/api/reports", tags=["Dashboards & Academic Reports"])

@router.get("/campus-analytics")
def get_campus_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Campus Manager & Executive Dashboard:
    - Overall participation rate
    - Inactive clubs (<2 sessions or low activity)
    - Students with 0% participation (early warning intervention)
    - Top student contributors
    """
    # 1. Total clubs
    clubs = db.query(Club).all()
    campuses = db.query(Campus).all()
    students = db.query(User).filter(User.role == "STUDENT").all()
    total_students = len(students)

    club_analytics = []
    inactive_clubs = []

    for c in clubs:
        total_sessions = db.query(AttendanceSession).filter(AttendanceSession.club_id == c.id).count()
        total_members = db.query(ClubMembership).filter(ClubMembership.club_id == c.id, ClubMembership.status == "ACTIVE").count()
        total_submissions = db.query(Submission).join(ClubMembership, Submission.student_id == ClubMembership.user_id).filter(ClubMembership.club_id == c.id).count()
        
        # Check active status
        if total_sessions < 1:
            inactive_clubs.append({
                "id": c.id,
                "name": c.name,
                "campus": c.campus.name if c.campus else "N/A",
                "advisor": c.faculty_advisor.name if c.faculty_advisor else "None",
                "member_count": total_members,
                "reason": "Zero Club Day sessions planned or logged"
            })

        club_analytics.append({
            "id": c.id,
            "name": c.name,
            "category": c.category,
            "campus": c.campus.name if c.campus else "N/A",
            "member_count": total_members,
            "capacity": c.capacity,
            "total_sessions": total_sessions,
            "submissions": total_submissions
        })

    # 2. Students with 0 participation (Early Warning List)
    zero_participation_students = []
    for s in students:
        attended = db.query(AttendanceRecord).filter(AttendanceRecord.user_id == s.id).count()
        submissions = db.query(Submission).filter(Submission.student_id == s.id).count()
        if attended == 0 and submissions == 0:
            enrolled = db.query(ClubMembership).filter(ClubMembership.user_id == s.id).count()
            zero_participation_students.append({
                "id": s.id,
                "name": s.name,
                "email": s.email,
                "roll_no": s.roll_no,
                "campus": s.campus.name if s.campus else "N/A",
                "clubs_joined": enrolled
            })

    # 3. Top student contributors
    top_contributors = []
    for s in students:
        attended = db.query(AttendanceRecord).filter(AttendanceRecord.user_id == s.id).count()
        subs = db.query(Submission).filter(Submission.student_id == s.id).count()
        score_sum = sum([sub.evaluation.total_score for sub in s.submissions if sub.evaluation])
        points = (attended * 10) + (subs * 15) + int(score_sum)
        if points > 0:
            top_contributors.append({
                "id": s.id,
                "name": s.name,
                "roll_no": s.roll_no,
                "campus": s.campus.code if s.campus else "N/A",
                "attended": attended,
                "submissions": subs,
                "score_sum": score_sum,
                "total_points": points
            })
    top_contributors = sorted(top_contributors, key=lambda x: x["total_points"], reverse=True)[:10]

    return {
        "summary": {
            "total_campuses": len(campuses),
            "total_clubs": len(clubs),
            "total_students": total_students,
            "inactive_clubs_count": len(inactive_clubs),
            "zero_participation_count": len(zero_participation_students),
            "healthy_participation_rate": round(((total_students - len(zero_participation_students)) / max(total_students, 1)) * 100, 1)
        },
        "clubs": club_analytics,
        "inactive_clubs": inactive_clubs,
        "zero_participation_students": zero_participation_students[:20],
        "top_contributors": top_contributors
    }

@router.get("/export-monthly-csv")
def export_monthly_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generates an exportable CSV report for Campus Managers & Academic Leadership."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Headers
    writer.writerow([
        "Student ID", "Student Name", "Roll Number", "Campus",
        "Enrolled Clubs", "Attended Sessions", "Submissions Made", "Average Rubric Score (/30)"
    ])

    students = db.query(User).filter(User.role == "STUDENT").all()
    for s in students:
        clubs = ", ".join([m.club.name for m in s.memberships if m.status == "ACTIVE"])
        attended = db.query(AttendanceRecord).filter(AttendanceRecord.user_id == s.id).count()
        submissions = db.query(Submission).filter(Submission.student_id == s.id).all()
        scores = [sub.evaluation.total_score for sub in submissions if sub.evaluation]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

        writer.writerow([
            s.id, s.name, s.roll_no or "N/A", s.campus.name if s.campus else "N/A",
            clubs or "None", attended, len(submissions), avg_score
        ])

    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=msot_club_monthly_report.csv"}
    )
