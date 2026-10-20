import hashlib
import hmac
import time
import json
import base64
from typing import Optional
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User

import os

SECRET_KEY = os.environ.get("SECRET_KEY", "msot-club-governance-secret-key-2026")
ALLOW_ROLE_SWITCHER = os.environ.get("ALLOW_ROLE_SWITCHER", "true").lower() in ("true", "1")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def create_access_token(user_id: int, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": int(time.time()) + 86400 * 7 # 7 days
    }
    payload_str = json.dumps(payload)
    b64_payload = base64.urlsafe_b64encode(payload_str.encode("utf-8")).decode("utf-8")
    sig = hmac.new(SECRET_KEY.encode("utf-8"), b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{b64_payload}.{sig}"

def decode_access_token(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        b64_payload, sig = parts
        expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        payload_str = base64.urlsafe_b64decode(b64_payload.encode("utf-8")).decode("utf-8")
        payload = json.loads(payload_str)
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None

def get_current_user(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None), # Support easy role switcher in testing/UI
    db: Session = Depends(get_db)
) -> User:
    # 1. Quick switcher header (active in demo/dev mode for testing all roles in UI)
    if ALLOW_ROLE_SWITCHER and x_user_id and x_user_id.isdigit():
        user = db.query(User).filter(User.id == int(x_user_id)).first()
        if user:
            return user

    # 2. Bearer token
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        payload = decode_access_token(token)
        if payload:
            user = db.query(User).filter(User.id == payload.get("sub")).first()
            if user:
                return user

    # 3. Default fallback for anonymous / public access
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required"
    )

def get_optional_user(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    try:
        return get_current_user(authorization, x_user_id, db)
    except HTTPException:
        return None
