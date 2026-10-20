import datetime
import uuid
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from backend.database import Base

class Campus(Base):
    __tablename__ = "campuses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False)  # HI-Tech, Ratnam, RGIB, JUJ
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    users = relationship("User", back_populates="campus")
    clubs = relationship("Club", back_populates="campus")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    roll_no = Column(String(50), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # ADMIN, CAMPUS_MANAGER, FACULTY_ADVISOR, TEACHER, STUDENT, GUEST
    user_category = Column(String(50), nullable=True, default=None)  # NON_MIRAI, TEACHER, FACULTY_ADVISOR, STUDENT_NON_MEMBER, STUDENT_MEMBER
    is_mirai_entity = Column(Boolean, nullable=True, default=None)
    teacher_type = Column(String(50), nullable=True)  # ADVISOR, NORMAL
    student_type = Column(String(50), nullable=True)  # CLUB_MEMBER, NON_CLUB_MEMBER
    is_domain_authorized = Column(Boolean, default=False)  # Granted via passkey "Code Geass"
    avatar_url = Column(String(255), nullable=True)
    campus_id = Column(Integer, ForeignKey("campuses.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    campus = relationship("Campus", back_populates="users")
    memberships = relationship("ClubMembership", back_populates="user")
    advised_clubs = relationship("Club", back_populates="faculty_advisor", foreign_keys="Club.faculty_advisor_id")
    submissions = relationship("Submission", back_populates="student")
    attendance_records = relationship("AttendanceRecord", back_populates="user", foreign_keys="AttendanceRecord.user_id")
    certificates = relationship("Certificate", back_populates="user")


class Club(Base):
    __tablename__ = "clubs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50), nullable=False)  # Technical, Cultural, Literary, Sports, Innovation
    logo_url = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    campus_id = Column(Integer, ForeignKey("campuses.id"), nullable=False)
    faculty_advisor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    capacity = Column(Integer, default=60)  # Configured 50-70
    is_recruiting = Column(Boolean, default=True)
    recruitment_deadline = Column(DateTime, nullable=True)
    meeting_rules = Column(String(255), default="Every Saturday 10:00 AM - 1:00 PM")
    is_approved = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    campus = relationship("Campus", back_populates="clubs")
    faculty_advisor = relationship("User", foreign_keys=[faculty_advisor_id], back_populates="advised_clubs")
    memberships = relationship("ClubMembership", back_populates="club", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="club", cascade="all, delete-orphan")
    budgets = relationship("ClubBudget", back_populates="club", cascade="all, delete-orphan")
    assignments = relationship("AssignmentProject", back_populates="club", cascade="all, delete-orphan")
    resources = relationship("ClubResource", back_populates="club", cascade="all, delete-orphan")
    hackathon_achievements = relationship("HackathonAchievement", back_populates="club", cascade="all, delete-orphan")
    advisor_audit = relationship("ClubAdvisorAudit", back_populates="club", uselist=False, cascade="all, delete-orphan")
    president_reports = relationship("ClubPresidentReport", back_populates="club", cascade="all, delete-orphan")


class ClubMembership(Base):
    __tablename__ = "club_memberships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    post = Column(String(50), default="MEMBER")  # PRESIDENT, VICE_PRESIDENT, FINANCE_PRESIDENT, MEDIA_PRESIDENT, GENERAL_SECRETARY, MEMBER
    branch = Column(String(100), nullable=True)  # For Kaizen: "CPP Club", "Dev Club", "Kaizen Intelligence", "Media Club"
    status = Column(String(50), default="ACTIVE")  # ACTIVE, PENDING
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="memberships")
    club = relationship("Club", back_populates="memberships")


class ClubBudget(Base):
    __tablename__ = "club_budgets"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(100), default="Equipment/Supplies")  # Event, Workshop, Equipment, Marketing
    purpose = Column(Text, nullable=False)
    scale = Column(String(50), default="Medium")  # Small, Medium, Flagship Event
    receipt_url = Column(String(255), nullable=True)
    status = Column(String(50), default="PENDING")  # PENDING, APPROVED, REJECTED
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    admin_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    club = relationship("Club", back_populates="budgets")
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=True)  # Nullable for college-wide
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(String(50), default="CLUB_DAY")  # CLUB_DAY, RECRUITING, FLAGSHIP_EVENT, IMPORTANT_DATE
    visibility = Column(String(50), default="CAMPUS_STUDENTS")  # PUBLIC, CAMPUS_STUDENTS, CLUB_ONLY
    date = Column(DateTime, nullable=False)
    venue = Column(String(150), default="Campus Auditorium / Lab")
    deliverable_info = Column(String(255), nullable=True)
    status = Column(String(50), default="SCHEDULED")  # SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
    is_important = Column(Boolean, default=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    club = relationship("Club", back_populates="events")
    created_by = relationship("User", foreign_keys=[created_by_id])
    attendance_session = relationship("AttendanceSession", back_populates="event", uselist=False, cascade="all, delete-orphan")
    assignments = relationship("AssignmentProject", back_populates="event", cascade="all, delete-orphan")


class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=True)
    totp_secret = Column(String(64), nullable=False)
    opens_at = Column(DateTime, default=datetime.datetime.utcnow)
    closes_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)

    event = relationship("Event", back_populates="attendance_session")
    records = relationship("AttendanceRecord", back_populates="session", cascade="all, delete-orphan")


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("attendance_sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    checkin_time = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(50), default="PRESENT")  # PRESENT, LATE, MANUAL_OVERRIDE
    override_reason = Column(String(255), nullable=True)
    override_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    session = relationship("AttendanceSession", back_populates="records")
    user = relationship("User", back_populates="attendance_records", foreign_keys=[user_id])
    override_by = relationship("User", foreign_keys=[override_by_id])


class AssignmentProject(Base):
    __tablename__ = "assignments_projects"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    assignment_type = Column(String(50), default="ASSIGNMENT")  # ASSIGNMENT, PROJECT, PRESENTATION
    due_date = Column(DateTime, nullable=False)
    max_score = Column(Float, default=30.0)  # 10 Content + 10 Presentation + 10 Participation
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    club = relationship("Club", back_populates="assignments")
    event = relationship("Event", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments_projects.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_url = Column(String(255), nullable=True)
    external_link = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(50), default="SUBMITTED")  # SUBMITTED, EVALUATED
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)

    assignment = relationship("AssignmentProject", back_populates="submissions")
    student = relationship("User", back_populates="submissions")
    evaluation = relationship("Evaluation", back_populates="submission", uselist=False, cascade="all, delete-orphan")


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    evaluated_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_score = Column(Float, default=0.0)      # 0-10
    presentation_score = Column(Float, default=0.0) # 0-10
    participation_score = Column(Float, default=0.0)# 0-10
    total_score = Column(Float, default=0.0)        # 0-30
    feedback_comments = Column(Text, nullable=True)
    evaluated_at = Column(DateTime, default=datetime.datetime.utcnow)

    submission = relationship("Submission", back_populates="evaluation")
    evaluated_by = relationship("User", foreign_keys=[evaluated_by_id])


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    certificate_number = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    cert_type = Column(String(50), default="ACHIEVEMENT")  # PARTICIPATION, ACHIEVEMENT, LEADERSHIP
    title = Column(String(200), nullable=False)
    issue_date = Column(DateTime, default=datetime.datetime.utcnow)
    verification_hash = Column(String(128), nullable=False)
    pdf_url = Column(String(255), nullable=True)

    user = relationship("User", back_populates="certificates")
    club = relationship("Club")
    event = relationship("Event")


class ClubResource(Base):
    __tablename__ = "club_resources"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    file_url = Column(String(255), nullable=True)
    link_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    club = relationship("Club", back_populates="resources")
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id])


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)  # ATTENDANCE_OVERRIDE, BUDGET_APPROVAL, SCORE_UPDATE
    target_type = Column(String(50), nullable=False)
    target_id = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class HackathonAchievement(Base):
    __tablename__ = "hackathon_achievements"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    title = Column(String(200), nullable=False)
    rank_position = Column(String(100), nullable=False) # e.g. "1st Place (Winner)", "2nd Place (Runner Up)", "3rd Place", "Top 5 Finalist"
    level = Column(String(50), default="National")      # National, State, Inter-Campus, Global
    team_name = Column(String(150), nullable=False)
    team_members = Column(Text, nullable=False)
    points_awarded = Column(Integer, default=100)
    certificate_link = Column(String(255), nullable=True)
    achievement_date = Column(DateTime, default=datetime.datetime.utcnow)
    advisor_verified_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    advisor_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    club = relationship("Club", back_populates="hackathon_achievements")
    advisor_verified_by = relationship("User", foreign_keys=[advisor_verified_by_id])


class ClubAdvisorAudit(Base):
    __tablename__ = "club_advisor_audits"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), unique=True, nullable=False)
    advisor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_execution_score = Column(Float, default=85.0) # 0 to 100
    activity_feedback = Column(Text, nullable=True)
    budget_governance_score = Column(Float, default=90.0)  # 0 to 100
    budget_audit_notes = Column(Text, nullable=True)
    project_quality_score = Column(Float, default=88.0)    # 0 to 100
    project_audit_notes = Column(Text, nullable=True)
    last_reviewed_at = Column(DateTime, default=datetime.datetime.utcnow)

    club = relationship("Club", back_populates="advisor_audit")
    advisor = relationship("User", foreign_keys=[advisor_id])


class ClubPresidentReport(Base):
    __tablename__ = "club_president_reports"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    president_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    advisor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(200), nullable=False)
    vision_statement = Column(Text, nullable=False)
    vp_operational_orders = Column(Text, nullable=True)
    finance_budget_overview = Column(Text, nullable=True)
    media_campaign_plan = Column(Text, nullable=True)
    general_secretary_notes = Column(Text, nullable=True)
    status = Column(String(50), default="SUBMITTED")  # SUBMITTED, APPROVED, NEEDS_REVISION
    advisor_feedback = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    club = relationship("Club", back_populates="president_reports")
    president = relationship("User", foreign_keys=[president_id])
    advisor = relationship("User", foreign_keys=[advisor_id])


