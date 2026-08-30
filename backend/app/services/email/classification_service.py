from sqlalchemy.orm import Session

from app.ai.gemini_client import classify_email
from app.models import (
    Email,
    EmailAccount,
    EmailClassification,
)


def classify_new_email(
    db: Session,
    email: Email,
):
    """
    Classify one newly synchronized email
    using Gemini and save the result.
    """

    result = classify_email(
        sender=email.sender or "",
        sender_name=email.sender_name or "",
        subject=email.subject or "",
        body=email.body or "",
    )

    classification = (
        db.query(EmailClassification)
        .filter(
            EmailClassification.email_id
            == email.id
        )
        .first()
    )

    keywords = ", ".join(
        result.keywords
    )

    if classification is None:

        classification = EmailClassification(
            email_id=email.id,
            category=result.category,
            is_job_related=result.is_job_related,
            confidence=result.confidence,
            recommended_action=(
                result.recommended_action
            ),
            keywords=keywords,
            reason=result.reason,
            risk_level=result.risk_level,
        )

        db.add(
            classification
        )

    else:

        classification.category = (
            result.category
        )

        classification.is_job_related = (
            result.is_job_related
        )

        classification.confidence = (
            result.confidence
        )

        classification.recommended_action = (
            result.recommended_action
        )

        classification.keywords = keywords

        classification.reason = (
            result.reason
        )

        classification.risk_level = (
            result.risk_level
        )

    db.commit()

    db.refresh(
        classification
    )

    return classification


def classify_account_emails(
    db: Session,
    email_account: EmailAccount,
):
    """
    Classify all emails belonging to an account.

    This remains available for the manual
    POST /api/ai/classify endpoint.
    """

    emails = (
        db.query(Email)
        .filter(
            Email.email_account_id
            == email_account.id
        )
        .order_by(
            Email.created_at.asc()
        )
        .all()
    )

    if not emails:
        return {
            "fetched": 0,
            "classified": 0,
            "inserted": 0,
            "updated": 0,
            "failed": 0,
            "errors": [],
        }

    inserted_count = 0
    updated_count = 0
    failed_count = 0
    classified_count = 0

    errors = []

    for email in emails:

        try:

            result = classify_email(
                sender=email.sender or "",
                sender_name=(
                    email.sender_name or ""
                ),
                subject=email.subject or "",
                body=email.body or "",
            )

            classification = (
                db.query(
                    EmailClassification
                )
                .filter(
                    EmailClassification.email_id
                    == email.id
                )
                .first()
            )

            keywords = ", ".join(
                result.keywords
            )

            if classification is None:

                classification = (
                    EmailClassification(
                        email_id=email.id,
                        category=result.category,
                        is_job_related=(
                            result.is_job_related
                        ),
                        confidence=result.confidence,
                        recommended_action=(
                            result.recommended_action
                        ),
                        keywords=keywords,
                        reason=result.reason,
                        risk_level=result.risk_level,
                    )
                )

                db.add(
                    classification
                )

                inserted_count += 1

            else:

                classification.category = (
                    result.category
                )

                classification.is_job_related = (
                    result.is_job_related
                )

                classification.confidence = (
                    result.confidence
                )

                classification.recommended_action = (
                    result.recommended_action
                )

                classification.keywords = (
                    keywords
                )

                classification.reason = (
                    result.reason
                )

                classification.risk_level = (
                    result.risk_level
                )

                updated_count += 1

            classified_count += 1

            # Commit after each email.
            # This prevents losing all successful
            # classifications if a later email fails.
            db.commit()

        except Exception as error:

            db.rollback()

            failed_count += 1

            errors.append(
                {
                    "email_id": email.id,
                    "error": str(error),
                }
            )

    return {
        "fetched": len(emails),
        "classified": classified_count,
        "inserted": inserted_count,
        "updated": updated_count,
        "failed": failed_count,
        "errors": errors,
    }
