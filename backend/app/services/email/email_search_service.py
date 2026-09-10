from datetime import datetime

from sqlalchemy.orm import Session

from app.models import (
    Email,
    EmailClassification,
)


def search_emails(
    db: Session,
    email_account_id: int,
    search_query: str | None = None,
    job_only: bool = False,
    date_from: str | None = None,
    date_to: str | None = None,
):
    query = (
        db.query(Email)
        .outerjoin(
            EmailClassification,
            EmailClassification.email_id == Email.id,
        )
        .filter(
            Email.email_account_id == email_account_id
        )
    )

    # --------------------------------------------------------
    # Job applications
    # --------------------------------------------------------

    if job_only:
        query = query.filter(
            EmailClassification.is_job_related.is_(True)
        )

    # --------------------------------------------------------
    # Text search
    # --------------------------------------------------------

    if search_query:
        search = f"%{search_query.lower()}%"

        query = query.filter(
            (
                Email.sender.ilike(search)
                | Email.sender_name.ilike(search)
                | Email.subject.ilike(search)
                | Email.body.ilike(search)
            )
        )

    # --------------------------------------------------------
    # Date range
    # --------------------------------------------------------

    if date_from:
        start_date = datetime.fromisoformat(
            date_from
        )

        query = query.filter(
            Email.received_at >= start_date
        )

    if date_to:
        end_date = datetime.fromisoformat(
            date_to
        )

        query = query.filter(
            Email.received_at < end_date.replace(
                hour=23,
                minute=59,
                second=59,
            )
        )

    return (
        query
        .order_by(Email.received_at.desc())
        .limit(50)
        .all()
    )
