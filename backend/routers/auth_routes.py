import os
import shutil
import time
import random
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.database import get_db
from backend.models import User, Campus, AuditLog
from backend.schemas import (
    UserLogin, UserOut, CampusOut, OTPRequest, RegisterWithOTP, LoginWithOTP,
    SocialLoginRequest, ResetPasswordRequest, UserProfileUpdate
)
from backend.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication & OTP"])
users_router = APIRouter(prefix="/api/users", tags=["Users & Profiles"])

AVATARS_DIR = "./uploads/avatars"
os.makedirs(AVATARS_DIR, exist_ok=True)

def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "is_domain_authorized": bool(user.is_domain_authorized),
        "avatar_url": user.avatar_url,
        "campus_id": user.campus_id,
        "campus_name": user.campus.name if user.campus else None,
        "roll_no": user.roll_no
    }

# In-memory OTP store (identifier -> {otp, expires_at})
OTP_STORE = {}

DOMAIN_PASSKEY = "Yuzuru"

def generate_otp() -> str:
    return f"{random.randint(100000, 999999)}"

@router.post("/otp/request")
def request_otp(data: OTPRequest):
    identifier = data.identifier.strip().lower()
    if not identifier:
        raise HTTPException(status_code=400, detail="Identifier (email or phone) is required.")

    otp = generate_otp()
    OTP_STORE[identifier] = {
        "otp": otp,
        "expires_at": time.time() + 300 # 5 minutes
    }

    print(f"\n=======================================================", flush=True)
    print(f"📨 [MIRAI OTP DISPATCH SERVICE]", flush=True)
    print(f"Recipient Contact: {data.identifier}", flush=True)
    print(f"Verification Code: {otp}", flush=True)
    print(f"Validity: 5 minutes", flush=True)
    print(f"=======================================================\n", flush=True)

    return {
        "message": f"6-digit verification code sent to {data.identifier}",
        "identifier": data.identifier,
        "simulated_otp": otp,
        "expires_in": 300
    }

def verify_otp_internal(identifier: str, input_otp: str) -> bool:
    clean_id = identifier.strip().lower()
    # Support development master OTP 999999 or exact match
    if input_otp == "999999":
        return True
    record = OTP_STORE.get(clean_id)
    if not record:
        return False
    if time.time() > record["expires_at"]:
        OTP_STORE.pop(clean_id, None)
        return False
    if record["otp"] == input_otp.strip():
        OTP_STORE.pop(clean_id, None)
        return True
    return False

@router.post("/register")
def register_with_otp(data: RegisterWithOTP, db: Session = Depends(get_db)):
    """
    Registers a new user with OTP verification and domain exception passkey.
    If passkey == 'Yuzuru', user gets supreme domain authority to reassign posts,
    members, attendance, and all club operations.
    Otherwise, user is registered as a regular Member / MSOT Student.
    """
    # 1. Verify OTP for either email or phone
    is_valid_otp = (
        verify_otp_internal(data.email, data.otp) or
        verify_otp_internal(data.phone, data.otp) or
        verify_otp_internal(data.username, data.otp)
    )
    if not is_valid_otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP verification code.")

    # 2. Check unique username
    clean_username = data.username.strip().lower()
    existing_user = db.query(User).filter(User.username == clean_username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username is already taken. Please choose another unique username.")

    # 3. Check unique email
    existing_email = db.query(User).filter(User.email == data.email.strip().lower()).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="An account with this email address already exists.")

    # 4. Check domain exception passkey "Yuzuru"
    is_authorized = False
    assigned_role = "STUDENT"
    authority_message = "Registered as MSOT Student / Member."

    if data.domain_passkey and data.domain_passkey.strip() == DOMAIN_PASSKEY:
        is_authorized = True
        assigned_role = "ADMIN"
        authority_message = "👑 Domain Exception Passkey 'Yuzuru' verified! Supreme Club Management Authority granted."

    # 5. Create user
    user = User(
        username=clean_username,
        name=data.name.strip(),
        email=data.email.strip().lower(),
        phone=data.phone.strip(),
        roll_no=data.student_id.strip(),
        password_hash=hash_password(data.password),
        role=assigned_role,
        is_domain_authorized=is_authorized,
        campus_id=data.campus_id or 1
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Log audit
    log = AuditLog(
        user_id=user.id,
        action="USER_REGISTERED",
        target_type="USER",
        target_id=str(user.id),
        details=f"User {user.name} registered as {assigned_role}. Domain passkey applied: {is_authorized}"
    )
    db.add(log)
    db.commit()

    token = create_access_token(user.id, user.role)
    return {
        "message": authority_message,
        "access_token": token,
        "token_type": "bearer",
        "user": serialize_user(user)
    }

@router.post("/login-otp")
def login_with_otp(data: LoginWithOTP, db: Session = Depends(get_db)):
    """Logs in using verified OTP via username, email or phone."""
    clean_id = data.identifier.strip().lower()
    user = db.query(User).filter(
        or_(
            User.email == clean_id,
            User.username == clean_id,
            User.phone == clean_id
        )
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="No registered account found with that identifier.")

    # Verify OTP
    if not (verify_otp_internal(clean_id, data.otp) or verify_otp_internal(user.email, data.otp)):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")

    token = create_access_token(user.id, user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": serialize_user(user)
    }

@router.post("/social-login")
def social_login(data: SocialLoginRequest, db: Session = Depends(get_db)):
    """Handles 1-click seamless OAuth login for Google, Instagram, and GitHub."""
    provider = data.provider.lower().strip()
    if provider not in ["google", "instagram", "github"]:
        raise HTTPException(status_code=400, detail="Unsupported social provider.")

    default_profiles = {
        "google": ("mirai_google_student", "Google Authenticated Scholar", "student.google@msot.org", "MSOT-GGL-2026"),
        "instagram": ("mirai_insta_creator", "Instagram Creative Student", "student.insta@msot.org", "MSOT-INS-2026"),
        "github": ("mirai_git_developer", "GitHub OpenSource Developer", "student.git@msot.org", "MSOT-GIT-2026"),
    }
    def_username, def_name, def_email, def_roll = default_profiles.get(
        provider, ("social_user", "Social Scholar", f"{provider}@msot.org", "MSOT-SOC-2026")
    )
    email = data.email.strip().lower() if data.email else def_email
    name = data.name.strip() if data.name else def_name
    username = (data.name.lower().replace(" ", "_") if data.name else def_username)

    user = db.query(User).filter(or_(User.email == email, User.username == username)).first()
    if not user:
        # Default campus is HIET (campus_id=1)
        hiet_campus = db.query(Campus).filter(Campus.code == "HIET").first()
        campus_id = hiet_campus.id if hiet_campus else 1
        user = User(
            username=username,
            name=name,
            email=email,
            phone="+91 98888 77777",
            roll_no=def_roll,
            password_hash=hash_password("social_default_secret"),
            role="STUDENT",
            is_domain_authorized=False,
            campus_id=campus_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(user.id, user.role)
    return {
        "message": f"Welcome! Authenticated via {provider.capitalize()}.",
        "access_token": token,
        "token_type": "bearer",
        "user": serialize_user(user)
    }

@router.post("/login")
def login(creds: UserLogin, db: Session = Depends(get_db)):
    clean_id = creds.email.strip().lower()
    user = db.query(User).filter(
        or_(
            User.email == clean_id,
            User.username == clean_id
        )
    ).first()
    if not user or not verify_password(creds.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid email/username or password")
    
    token = create_access_token(user.id, user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": serialize_user(user)
    }

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return serialize_user(current_user)

@router.post("/profile-photo")
@users_router.post("/profile-photo")
def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Allows every member, student, president, and advisor to set their profile photo."""
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ".png"
    if ext not in [".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"]:
        ext = ".png"
    safe_filename = f"avatar_{current_user.id}_{int(time.time())}{ext}"
    dest_path = os.path.join(AVATARS_DIR, safe_filename)
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    current_user.avatar_url = f"/uploads/avatars/{safe_filename}"
    db.commit()
    db.refresh(current_user)
    return {
        "status": "success",
        "message": "Profile photo updated successfully!",
        "avatar_url": current_user.avatar_url,
        "user": serialize_user(current_user)
    }

@router.put("/profile")
@users_router.put("/profile")
def update_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Allows any member to update their profile settings (name, phone, avatar_url)."""
    if data.name and data.name.strip():
        current_user.name = data.name.strip()
    if data.phone is not None:
        current_user.phone = data.phone.strip()
    if data.avatar_url is not None:
        current_user.avatar_url = data.avatar_url.strip()
    
    db.commit()
    db.refresh(current_user)
    return {
        "status": "success",
        "message": "Profile updated successfully!",
        "user": serialize_user(current_user)
    }

@router.get("/users")
def list_demo_users(db: Session = Depends(get_db)):
    """List users categorized by role for effortless demo role-switching."""
    users = db.query(User).all()
    results = []
    for u in users:
        posts = [f"{m.post} of {m.club.name}" for m in u.memberships if m.post != "MEMBER"]
        results.append({
            "id": u.id,
            "username": u.username,
            "name": u.name,
            "email": u.email,
            "phone": u.phone,
            "role": u.role,
            "is_domain_authorized": u.is_domain_authorized,
            "avatar_url": u.avatar_url,
            "campus_id": u.campus_id,
            "campus_code": u.campus.code if u.campus else "",
            "roll_no": u.roll_no,
            "leadership": posts
        })
    return results

@router.get("/campuses", response_model=List[CampusOut])
def list_campuses(db: Session = Depends(get_db)):
    return db.query(Campus).all()

@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Handles password reset recovery flow."""
    clean_email = data.email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()
    
    if data.new_password:
        if not user:
            raise HTTPException(status_code=404, detail="No user found with this email.")
        user.password_hash = hash_password(data.new_password)
        db.commit()
        return {
            "success": True,
            "message": "Password successfully updated! You can now sign in with your new credentials."
        }
    
    # Recovery dispatch notification
    if not user:
        return {
            "success": True,
            "message": f"If an account exists for {clean_email}, a password reset link has been dispatched to their inbox."
        }
    
    return {
        "success": True,
        "message": f"Password reset link dispatched to {clean_email}! Please check your inbox or spam folder.",
        "recovery_token": f"rst_{random.randint(10000000, 99999999)}"
    }

