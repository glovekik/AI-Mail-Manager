from sqlalchemy.orm import Session

from app.models import Email, EmailAccount
from app.services.gmail.gmail_provider import GmailProvider
from app.services.email.classification_service import (
    classify_new_email,
)


def sync_gmail_emails(
    db: Session,
    email_account: EmailAccount,
    credentials,
    max_results: int = 10,
):
    """
    Synchronize Gmail messages into the database.

    New Gmail messages are inserted.
    Existing Gmail messages are updated.

    Newly inserted emails are automatically
    classified using Gemini.

    Duplicate messages are prevented using:
        email_account_id + provider_message_id
    """

    # ========================================================
    # Create Gmail provider
    # ========================================================

    provider = GmailProvider(
        credentials
    )

    # ========================================================
    # Fetch messages from Gmail
    # ========================================================

    gmail_emails = provider.get_messages(
        max_results=max_results
    )

    inserted_count = 0
    updated_count = 0
    failed_count = 0

    classified_count = 0
    classification_failed_count = 0

    errors = []
    classification_errors = []

    # Keep track of emails that are actually
    # inserted during THIS sync.
    new_emails = []

    # ========================================================
    # Process Gmail messages
    # ========================================================

    for gmail_email in gmail_emails:

        provider_message_id = (
            gmail_email.get("id")
        )

        try:

            # ------------------------------------------------
            # Validate Gmail message ID
            # ------------------------------------------------

            if not provider_message_id:

                raise ValueError(
                    "Gmail message does not contain an ID."
                )

            # ------------------------------------------------
            # Find existing email
            # ------------------------------------------------

            existing_email = (
                db.query(Email)
                .filter(
                    Email.email_account_id
                    == email_account.id,
                    Email.provider_message_id
                    == provider_message_id,
                )
                .first()
            )

            # =================================================
            # INSERT NEW EMAIL
            # =================================================

            if existing_email is None:

                email = Email(
                    email_account_id=(
                        email_account.id
                    ),
                    provider_message_id=(
                        provider_message_id
                    ),
                    thread_id=(
                        gmail_email.get(
                            "thread_id"
                        )
                    ),
                    sender=(
                        gmail_email.get(
                            "sender"
                        )
                    ),
                    sender_name=(
                        gmail_email.get(
                            "sender_name"
                        )
                    ),
                    subject=(
                        gmail_email.get(
                            "subject"
                        )
                    ),
                    received_at=(
                        gmail_email.get(
                            "received_at"
                        )
                    ),
                    snippet=(
                        gmail_email.get(
                            "snippet"
                        )
                    ),
                    body=(
                        gmail_email.get(
                            "body"
                        )
                    ),
                    labels=(
                        ",".join(
                            gmail_email.get(
                                "labels",
                                [],
                            )
                        )
                    ),
                    is_read=(
                        gmail_email.get(
                            "is_read",
                            True,
                        )
                    ),
                )

                db.add(email)

                # Generate the database ID.
                db.flush()

                # Remember this email so we can
                # classify ONLY newly inserted emails.
                new_emails.append(email)

                inserted_count += 1

            # =================================================
            # UPDATE EXISTING EMAIL
            # =================================================

            else:

                existing_email.thread_id = (
                    gmail_email.get(
                        "thread_id"
                    )
                )

                existing_email.sender = (
                    gmail_email.get(
                        "sender"
                    )
                )

                existing_email.sender_name = (
                    gmail_email.get(
                        "sender_name"
                    )
                )

                existing_email.subject = (
                    gmail_email.get(
                        "subject"
                    )
                )

                existing_email.received_at = (
                    gmail_email.get(
                        "received_at"
                    )
                )

                existing_email.snippet = (
                    gmail_email.get(
                        "snippet"
                    )
                )

                existing_email.body = (
                    gmail_email.get(
                        "body"
                    )
                )

                existing_email.labels = (
                    ",".join(
                        gmail_email.get(
                            "labels",
                            [],
                        )
                    )
                )

                existing_email.is_read = (
                    gmail_email.get(
                        "is_read",
                        True,
                    )
                )

                updated_count += 1

            # ------------------------------------------------
            # Commit email synchronization
            # ------------------------------------------------

            db.commit()

        except Exception as error:

            db.rollback()

            failed_count += 1

            errors.append(
                {
                    "provider_message_id": (
                        provider_message_id
                    ),
                    "error": str(error),
                }
            )

    # ========================================================
    # Classify newly inserted emails
    # ========================================================

    for email in new_emails:

        try:

            classify_new_email(
                db=db,
                email=email,
            )

            classified_count += 1

        except Exception as error:

            db.rollback()

            classification_failed_count += 1

            classification_errors.append(
                {
                    "email_id": email.id,
                    "error": str(error),
                }
            )

    # ========================================================
    # Return synchronization result
    # ========================================================

    return {
        "status": "success",

        "fetched": len(gmail_emails),

        "inserted": inserted_count,

        "updated": updated_count,

        "failed": failed_count,

        "classified": classified_count,

        "classification_failed": (
            classification_failed_count
        ),

        "errors": errors,

        "classification_errors": (
            classification_errors
        ),
    }