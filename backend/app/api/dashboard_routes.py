from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models import Email, EmailClassification


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)


@router.get("")
def dashboard(
    email_account_id: int,
    db: Session = Depends(get_db),
):
    emails = (
        db.query(Email)
        .filter(
            Email.email_account_id
            == email_account_id
        )
        .all()
    )

    classifications = (
        db.query(EmailClassification)
        .join(
            Email,
            EmailClassification.email_id
            == Email.id,
        )
        .filter(
            Email.email_account_id
            == email_account_id
        )
        .all()
    )

    category_counts = Counter(
        classification.category
        for classification in classifications
    )

    action_counts = Counter(
        classification.recommended_action
        for classification in classifications
    )

    risk_counts = Counter(
        classification.risk_level
        for classification in classifications
    )

    unread_count = sum(
        1
        for email in emails
        if not email.is_read
    )

    return {
        "total_emails": len(emails),
        "unread_emails": unread_count,
        "classified_emails": len(
            classifications
        ),
        "categories": dict(
            category_counts
        ),
        "recommended_actions": dict(
            action_counts
        ),
        "risk_levels": dict(
            risk_counts
        ),
    }