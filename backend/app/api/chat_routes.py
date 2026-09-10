from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)

from pydantic import BaseModel

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.services.chat.chat_service import (
    understand_email_request,
)

from app.services.email.email_search_service import (
    search_emails,
)


router = APIRouter(
    prefix="/api/chat",
    tags=["Email Assistant"],
)


# ============================================================
# Request schema
# ============================================================

class ChatRequest(BaseModel):

    message: str


# ============================================================
# Understand request
#
# Debug/testing endpoint.
#
# This only asks Gemini to understand the user's request.
# It does NOT search the database.
# ============================================================

@router.post("/understand")
def understand_request(
    message: str,
):

    if not message.strip():

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    try:

        intent = understand_email_request(
            message
        )

        return {
            "message": message,
            "intent": intent.model_dump(),
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Email Assistant failed: {error}"
            ),
        )


# ============================================================
# Email Assistant
#
# Example:
#
# POST /api/chat
#
# {
#     "message": "Show my job applications from Infosys"
# }
#
# The email account is obtained from the authenticated
# session instead of trusting the frontend.
# ============================================================

@router.post("")
def chat(
    request: ChatRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Validate message
    # --------------------------------------------------------

    if not request.message.strip():

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    # --------------------------------------------------------
    # Get authenticated email account
    # --------------------------------------------------------

    email_account_id = (
        http_request.session.get(
            "email_account_id"
        )
    )

    if not email_account_id:

        raise HTTPException(
            status_code=401,
            detail="Not authenticated.",
        )

    # --------------------------------------------------------
    # Understand request using Gemini
    # --------------------------------------------------------

    try:

        intent = understand_email_request(
            request.message
        )

        # ====================================================
        # SEARCH EMAILS
        # ====================================================

        if intent.intent == "search_emails":

            emails = search_emails(
                db=db,
                email_account_id=(
                    email_account_id
                ),
                search_query=(
                    intent.search_query
                ),
                job_only=(
                    intent.job_only
                ),
                date_from=(
                    intent.date_from
                ),
                date_to=(
                    intent.date_to
                ),
            )

            return {
                "message": request.message,

                "intent": (
                    intent.model_dump()
                ),

                "count": len(emails),

                "emails": [
                    {
                        "id": email.id,

                        "sender": (
                            email.sender
                        ),

                        "sender_name": (
                            email.sender_name
                        ),

                        "subject": (
                            email.subject
                        ),

                        "received_at": (
                            email.received_at
                        ),

                        "snippet": (
                            email.snippet
                        ),

                        "is_read": (
                            email.is_read
                        ),

                        "is_job_related": (
                            email.classification.is_job_related
                            if email.classification
                            else False
                        ),
                    }

                    for email in emails
                ],
            }

        # ====================================================
        # NOT IMPLEMENTED YET
        # ====================================================

        return {
            "message": request.message,

            "intent": (
                intent.model_dump()
            ),

            "count": 0,

            "emails": [],

            "message_response": (
                "I understand your request, "
                "but this operation is not "
                "implemented yet."
            ),
        }

    except HTTPException:

        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Email Assistant failed: {error}"
            ),
        )