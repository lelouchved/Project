from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

# Campus
class CampusOut(BaseModel):
    id: int
    name: str
    code: str
    class Config:
        from_attributes = True

# User
class UserOut(BaseModel):
    id: int
    username: Optional[str] = None
    name: str
    email: str
    phone: Optional[str] = None
    roll_no: Optional[str] = None
    role: str
    is_domain_authorized: bool = False
    avatar_url: Optional[str] = None
    campus_id: int
    campus_name: Optional[str] = None
    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str
    domain_passkey: Optional[str] = None

class OTPRequest(BaseModel):
    identifier: str  # email or phone or username

class RegisterWithOTP(BaseModel):
    email: str
    name: str
    phone: str
    student_id: str  # Roll Number / College ID
    username: str
    password: str
    otp: str
    domain_passkey: Optional[str] = None
    campus_id: Optional[int] = 1

class LoginWithOTP(BaseModel):
    identifier: str  # email, username or phone
    otp: str

class SocialLoginRequest(BaseModel):
    provider: str  # google, instagram, github
    email: Optional[str] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None

# Membership
class MembershipCreate(BaseModel):
    club_id: int
    post: Optional[str] = "MEMBER"

class MembershipOut(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_email: str
    roll_no: Optional[str] = None
    club_id: int
    club_name: str
    post: str
    status: str
    joined_at: datetime
    class Config:
        from_attributes = True

# Club
class ClubCreate(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    campus_id: int
    faculty_advisor_id: int
    capacity: Optional[int] = 60
    is_recruiting: Optional[bool] = True
    recruitment_deadline: Optional[datetime] = None
    meeting_rules: Optional[str] = "Every Saturday 10:00 AM - 1:00 PM"

class ClubOut(BaseModel):
    id: int
    name: str
    category: str
    logo_url: Optional[str] = None
    description: Optional[str] = None
    campus_id: int
    campus_name: Optional[str] = None
    faculty_advisor_id: int
    faculty_advisor_name: Optional[str] = None
    faculty_advisor_email: Optional[str] = None
    capacity: int
    member_count: int = 0
    is_recruiting: bool
    recruitment_deadline: Optional[datetime] = None
    meeting_rules: Optional[str] = None
    posts: Optional[dict] = None
    class Config:
        from_attributes = True

# Budget
class BudgetCreate(BaseModel):
    club_id: int
    title: str
    amount: float
    category: str
    purpose: str
    scale: str = "Medium"
    receipt_url: Optional[str] = None

class BudgetReview(BaseModel):
    status: str  # APPROVED, REJECTED
    admin_notes: Optional[str] = None

class BudgetOut(BaseModel):
    id: int
    club_id: int
    club_name: str
    requested_by_id: int
    requested_by_name: str
    title: str
    amount: float
    category: str
    purpose: str
    scale: str
    receipt_url: Optional[str] = None
    status: str
    approved_by_id: Optional[int] = None
    admin_notes: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# Event
class EventCreate(BaseModel):
    club_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    event_type: str = "CLUB_DAY"  # CLUB_DAY, RECRUITING, FLAGSHIP_EVENT, IMPORTANT_DATE
    visibility: str = "CAMPUS_STUDENTS"  # PUBLIC, CAMPUS_STUDENTS, CLUB_ONLY
    date: datetime
    venue: str = "Campus Auditorium / Lab"
    deliverable_info: Optional[str] = None
    is_important: bool = False

class EventOut(BaseModel):
    id: int
    club_id: Optional[int] = None
    club_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    event_type: str
    visibility: str
    date: datetime
    venue: str
    deliverable_info: Optional[str] = None
    status: str
    is_important: bool = False
    has_active_session: bool = False
    created_by_name: Optional[str] = None
    created_by_post: Optional[str] = None
    class Config:
        from_attributes = True

# Attendance & Dynamic TOTP QR
class AttendanceSessionStart(BaseModel):
    event_id: int
    duration_minutes: int = 45

class AttendanceCheckIn(BaseModel):
    session_id: int
    token: str  # 6-digit TOTP code generated from dynamic rotating QR

class AttendanceOverride(BaseModel):
    session_id: int
    student_id: int
    status: str = "MANUAL_OVERRIDE"
    reason: str

class AttendanceRecordOut(BaseModel):
    id: int
    session_id: int
    user_id: int
    user_name: str
    roll_no: Optional[str] = None
    checkin_time: datetime
    status: str
    override_reason: Optional[str] = None
    class Config:
        from_attributes = True

# Assignments & Submissions
class AssignmentCreate(BaseModel):
    club_id: int
    event_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    assignment_type: str = "ASSIGNMENT"
    due_date: datetime
    max_score: float = 30.0

class AssignmentOut(BaseModel):
    id: int
    club_id: int
    club_name: str
    event_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    assignment_type: str
    due_date: datetime
    max_score: float
    submission_count: int = 0
    my_submission: Optional[dict] = None
    class Config:
        from_attributes = True

class SubmissionCreate(BaseModel):
    assignment_id: int
    file_url: Optional[str] = None
    external_link: Optional[str] = None
    notes: Optional[str] = None

class EvaluationCreate(BaseModel):
    submission_id: int
    content_score: float = Field(..., ge=0, le=10)
    presentation_score: float = Field(..., ge=0, le=10)
    participation_score: float = Field(..., ge=0, le=10)
    comments: Optional[str] = None

class SubmissionOut(BaseModel):
    id: int
    assignment_id: int
    assignment_title: str
    student_id: int
    student_name: str
    roll_no: Optional[str] = None
    file_url: Optional[str] = None
    external_link: Optional[str] = None
    notes: Optional[str] = None
    status: str
    submitted_at: datetime
    evaluation: Optional[dict] = None
    class Config:
        from_attributes = True

# Certificate & Transcript
class CertificateOut(BaseModel):
    id: str
    certificate_number: str
    user_id: int
    student_name: str
    club_id: Optional[int] = None
    club_name: Optional[str] = None
    event_title: Optional[str] = None
    cert_type: str
    title: str
    issue_date: datetime
    verification_hash: str
    verification_url: str
    pdf_url: Optional[str] = None
    class Config:
        from_attributes = True

class ResetPasswordRequest(BaseModel):
    email: str
    new_password: Optional[str] = None

# Analytics & Hackathon Achievements
class HackathonAchievementCreate(BaseModel):
    club_id: int
    title: str
    rank_position: str
    level: Optional[str] = "National"
    team_name: str
    team_members: str
    points_awarded: Optional[int] = 100
    certificate_link: Optional[str] = None
    achievement_date: Optional[datetime] = None
    advisor_notes: Optional[str] = None

class HackathonAchievementOut(BaseModel):
    id: int
    club_id: int
    club_name: Optional[str] = None
    title: str
    rank_position: str
    level: str
    team_name: str
    team_members: str
    points_awarded: int
    certificate_link: Optional[str] = None
    achievement_date: datetime
    advisor_verified_by_name: Optional[str] = None
    advisor_notes: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class ClubAdvisorAuditUpdate(BaseModel):
    activity_execution_score: Optional[float] = None
    activity_feedback: Optional[str] = None
    budget_governance_score: Optional[float] = None
    budget_audit_notes: Optional[str] = None
    project_quality_score: Optional[float] = None
    project_audit_notes: Optional[str] = None

