from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.models import (
    Email,
    EmailAccount,
    EmailClassification,
)

from app.schemas.email import (
    EmailListResponse,
)

from app.auth.credential_service import (
    load_google_credentials,
)

from app.services.gmail.gmail_provider import (
    GmailProvider,
)


router = APIRouter(
    prefix="/api/emails",
    tags=["Emails"],
)


# ============================================================
# List emails
# ============================================================

@router.get(
    "",
    response_model=EmailListResponse,
)
def list_emails(
    email_account_id: int,
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    job_only: bool = Query(
        default=False,
    ),
    db: Session = Depends(get_db),
):

    offset = (
        page - 1
    ) * page_size

    query = (
        db.query(Email)
        .outerjoin(
            EmailClassification,
            EmailClassification.email_id
            == Email.id,
        )
        .filter(
            Email.email_account_id
            == email_account_id
        )
    )

    # --------------------------------------------------------
    # Job Applications filter
    # --------------------------------------------------------

    if job_only:

        query = query.filter(
            EmailClassification.is_job_related.is_(True)
        )

    query = query.order_by(
        Email.created_at.desc()
    )

    total = query.count()

    emails = (
        query
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return EmailListResponse(
        total=total,
        page=page,
        page_size=page_size,
        emails=emails,
    )


# ============================================================
# Get single email
# ============================================================

@router.get(
    "/{email_id}"
)
def get_email(
    email_id: int,
    db: Session = Depends(get_db),
):

    email = (
        db.query(Email)
        .filter(
            Email.id == email_id
        )
        .first()
    )

    if email is None:

        raise HTTPException(
            status_code=404,
            detail="Email not found",
        )

    classification = (
        email.classification
    )

    return {
        "id": email.id,
        "provider_message_id": (
            email.provider_message_id
        ),
        "thread_id": email.thread_id,
        "sender": email.sender,
        "sender_name": email.sender_name,
        "subject": email.subject,
        "received_at": email.received_at,
        "snippet": email.snippet,
        "body": email.body,
        "is_read": email.is_read,
        "classification": classification,
    }


# ============================================================
# Helper: get Gmail provider
# ============================================================

def get_gmail_provider(
    email: Email,
    db: Session,
):

    email_account = (
        db.query(EmailAccount)
        .filter(
            EmailAccount.id
            == email.email_account_id
        )
        .first()
    )

    if email_account is None:

        raise HTTPException(
            status_code=404,
            detail="Email account not found",
        )

    if email_account.provider != "gmail":

        raise HTTPException(
            status_code=400,
            detail="Email account is not a Google account",
        )

    try:

        credentials = (
            load_google_credentials(
                email_account
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=401,
            detail=(
                "Unable to load Google credentials: "
                f"{error}"
            ),
        )

    return GmailProvider(
        credentials
    )


# ============================================================
# Mark email as read
# ============================================================

@router.post(
    "/{email_id}/read"
)
def mark_email_read(
    email_id: int,
    db: Session = Depends(get_db),
):

    email = (
        db.query(Email)
        .filter(
            Email.id == email_id
        )
        .first()
    )

    if email is None:

        raise HTTPException(
            status_code=404,
            detail="Email not found",
        )

    try:

        gmail = get_gmail_provider(
            email,
            db,
        )

        gmail.mark_as_read(
            email.provider_message_id
        )

        email.is_read = True

        db.commit()

        return {
            "status": "success",
            "message": "Email marked as read",
            "email_id": email.id,
        }

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# Mark email as unread
# ============================================================

@router.post(
    "/{email_id}/unread"
)
def mark_email_unread(
    email_id: int,
    db: Session = Depends(get_db),
):

    email = (
        db.query(Email)
        .filter(
            Email.id == email_id
        )
        .first()
    )

    if email is None:

        raise HTTPException(
            status_code=404,
            detail="Email not found",
        )

    try:

        gmail = get_gmail_provider(
            email,
            db,
        )

        gmail.mark_as_unread(
            email.provider_message_id
        )

        email.is_read = False

        db.commit()

        return {
            "status": "success",
            "message": "Email marked as unread",
            "email_id": email.id,
        }

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# Archive email
# ============================================================

@router.post(
    "/{email_id}/archive"
)
def archive_email(
    email_id: int,
    db: Session = Depends(get_db),
):

    email = (
        db.query(Email)
        .filter(
            Email.id == email_id
        )
        .first()
    )

    if email is None:

        raise HTTPException(
            status_code=404,
            detail="Email not found",
        )

    try:

        gmail = get_gmail_provider(
            email,
            db,
        )

        gmail.archive_message(
            email.provider_message_id
        )

        db.commit()

        return {
            "status": "success",
            "message": "Email archived",
            "email_id": email.id,
        }

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# Delete email
# ============================================================

@router.post(
    "/{email_id}/delete"
)
def delete_email(
    email_id: int,
    db: Session = Depends(get_db),
):

    email = (
        db.query(Email)
        .filter(
            Email.id == email_id
        )
        .first()
    )

    if email is None:

        raise HTTPException(
            status_code=404,
            detail="Email not found",
        )

    try:

        gmail = get_gmail_provider(
            email,
            db,
        )

        gmail.trash_message(
            email.provider_message_id
        )

        db.commit()

        return {
            "status": "success",
            "message": "Email moved to trash",
            "email_id": email.id,
        }

    except HTTPException:

        raise

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )
