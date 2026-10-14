from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
import os
import shutil

from backend.database import get_db
from backend.models import Club, ClubMembership, ClubBudget, User, AuditLog
from backend.schemas import BudgetCreate, BudgetReview, BudgetOut
from backend.auth import get_current_user

router = APIRouter(prefix="/api/budgets", tags=["Club Budget & Finance"])

UPLOAD_DIR = "./uploads/receipts"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("", response_model=List[BudgetOut])
def list_budgets(
    club_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(ClubBudget)
    if club_id:
        query = query.filter(ClubBudget.club_id == club_id)
    
    # Campus managers see all in their campus, or all if admin
    if current_user.role == "CAMPUS_MANAGER":
        query = query.join(Club).filter(Club.campus_id == current_user.campus_id)
    elif current_user.role == "STUDENT":
        # Students see budgets of their enrolled clubs
        my_club_ids = [m.club_id for m in current_user.memberships if m.status == "ACTIVE"]
        query = query.filter(ClubBudget.club_id.in_(my_club_ids))

    budgets = query.order_by(ClubBudget.created_at.desc()).all()
    results = []
    for b in budgets:
        results.append(BudgetOut(
            id=b.id,
            club_id=b.club_id,
            club_name=b.club.name,
            requested_by_id=b.requested_by_id,
            requested_by_name=b.requested_by.name,
            title=b.title,
            amount=b.amount,
            category=b.category,
            purpose=b.purpose,
            scale=b.scale,
            receipt_url=b.receipt_url,
            status=b.status,
            approved_by_id=b.approved_by_id,
            admin_notes=b.admin_notes,
            created_at=b.created_at
        ))
    return results

@router.post("", response_model=BudgetOut)
def submit_budget_proposal(
    budget_in: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    club = db.query(Club).filter(Club.id == budget_in.club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Only Finance President, President, VP or Faculty Advisor can request budgets
    membership = db.query(ClubMembership).filter(
        ClubMembership.club_id == budget_in.club_id,
        ClubMembership.user_id == current_user.id
    ).first()

    is_finance = membership and membership.post == "FINANCE_PRESIDENT"
    is_lead = membership and membership.post in ["PRESIDENT", "VICE_PRESIDENT"]
    is_advisor = current_user.id == club.faculty_advisor_id or current_user.role in ["ADMIN", "CAMPUS_MANAGER"]

    if not (is_finance or is_lead or is_advisor):
        raise HTTPException(
            status_code=403,
            detail="Only the Finance President or Club Executive Officers can submit budget requests."
        )

    budget = ClubBudget(
        club_id=budget_in.club_id,
        requested_by_id=current_user.id,
        title=budget_in.title,
        amount=budget_in.amount,
        category=budget_in.category,
        purpose=budget_in.purpose,
        scale=budget_in.scale,
        receipt_url=budget_in.receipt_url,
        status="PENDING"
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)

    # Log audit
    log = AuditLog(
        user_id=current_user.id,
        action="BUDGET_REQUEST_SUBMITTED",
        target_type="BUDGET",
        target_id=str(budget.id),
        details=f"Submitted budget request for ₹{budget.amount} ({budget.title}) for {club.name}"
    )
    db.add(log)
    db.commit()

    return BudgetOut(
        id=budget.id,
        club_id=budget.club_id,
        club_name=club.name,
        requested_by_id=budget.requested_by_id,
        requested_by_name=current_user.name,
        title=budget.title,
        amount=budget.amount,
        category=budget.category,
        purpose=budget.purpose,
        scale=budget.scale,
        receipt_url=budget.receipt_url,
        status=budget.status,
        approved_by_id=None,
        admin_notes=None,
        created_at=budget.created_at
    )

@router.post("/{budget_id}/receipt")
def upload_budget_receipt(
    budget_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    budget = db.query(ClubBudget).filter(ClubBudget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget item not found")

    file_ext = os.path.splitext(file.filename)[1]
    safe_name = f"receipt_{budget_id}_{int(datetime.utcnow().timestamp())}{file_ext}"
    dest_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    budget.receipt_url = f"/uploads/receipts/{safe_name}"
    db.commit()
    return {"message": "Receipt uploaded successfully", "receipt_url": budget.receipt_url}

@router.put("/{budget_id}/review", response_model=BudgetOut)
def review_budget(
    budget_id: int,
    review_in: BudgetReview,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Campus Manager / Admin reviews and approves or rejects budget proposals."""
    if current_user.role not in ["ADMIN", "CAMPUS_MANAGER"]:
        raise HTTPException(
            status_code=403,
            detail="Only MSOT Officials (Campus Manager or Admin) can approve or reject club budgets."
        )

    budget = db.query(ClubBudget).filter(ClubBudget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget request not found")

    if review_in.status not in ["APPROVED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="Status must be either APPROVED or REJECTED")

    budget.status = review_in.status
    budget.approved_by_id = current_user.id
    budget.admin_notes = review_in.admin_notes

    # Audit log
    log = AuditLog(
        user_id=current_user.id,
        action=f"BUDGET_{review_in.status}",
        target_type="BUDGET",
        target_id=str(budget.id),
        details=f"MSOT Official {current_user.name} marked budget ₹{budget.amount} as {review_in.status}. Notes: {review_in.admin_notes}"
    )
    db.add(log)
    db.commit()

    return BudgetOut(
        id=budget.id,
        club_id=budget.club_id,
        club_name=budget.club.name,
        requested_by_id=budget.requested_by_id,
        requested_by_name=budget.requested_by.name,
        title=budget.title,
        amount=budget.amount,
        category=budget.category,
        purpose=budget.purpose,
        scale=budget.scale,
        receipt_url=budget.receipt_url,
        status=budget.status,
        approved_by_id=budget.approved_by_id,
        admin_notes=budget.admin_notes,
        created_at=budget.created_at
    )
