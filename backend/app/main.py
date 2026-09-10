import os

from fastapi.responses import RedirectResponse
from fastapi import Depends, FastAPI, Request
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from app.ai.gemini_client import classify_email

from app.scheduler.email_scheduler import (
    start_scheduler,
    stop_scheduler,
)

from app.api.chat_routes import (
    router as chat_router,
)

from app.api.category_routes import (
    router as category_router,
)

from app.api.dashboard_routes import (
    router as dashboard_router,
)

from app.api.email_routes import (
    router as email_router,
)

from app.auth.credential_service import (
    load_google_credentials,
    save_google_credentials,
)

from app.auth.google_oauth import create_google_flow
from app.auth.google_user import get_google_user

from app.database.database import (
    Base,
    engine,
    get_db,
)

from app.models import (
    Email,
    EmailAccount,
    EmailClassification,
    User,
)

from app.services.email.classification_service import (
    classify_account_emails,
)

from app.services.email.email_sync_service import (
    sync_gmail_emails,
)


# ============================================================
# Application
# ============================================================

app = FastAPI(
    title="AI Mail Manager",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://ai-mail-manager-swart.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Session Middleware
# ============================================================

SESSION_SECRET = os.getenv(
    "SESSION_SECRET",
    "development-session-secret",
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="none",
    https_only=True,
)

# ============================================================
# Database
# ============================================================

Base.metadata.create_all(
    bind=engine
)


# ============================================================
# Routers
# ============================================================

app.include_router(
    email_router
)

app.include_router(
    dashboard_router
)

app.include_router(
    category_router
)

app.include_router(
    chat_router
)


# ============================================================
# Health
# ============================================================

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "AI Mail Manager",
    }


# ============================================================
# Database Test
# ============================================================

@app.get("/api/database/test")
def test_database():

    try:

        with engine.connect() as connection:

            result = connection.execute(
                text("SELECT 1")
            )

            value = result.scalar()

        return {
            "status": "ok",
            "database": "connected",
            "test_value": value,
        }

    except Exception as error:

        return {
            "status": "error",
            "database": "connection_failed",
            "error": str(error),
        }


# ============================================================
# Google OAuth - Login
# ============================================================

@app.get("/auth/google")
def google_login(
    request: Request,
):

    flow = create_google_flow()

    authorization_url, state = (
        flow.authorization_url(
            access_type="offline",
            prompt="consent",
        )
    )

    request.session["oauth_state"] = state

    if flow.code_verifier:
        request.session["code_verifier"] = (
            flow.code_verifier
        )

    return RedirectResponse(
        url=authorization_url
    )


# ============================================================
# Google OAuth - Callback
# ============================================================

@app.get("/auth/google/callback")
def google_callback(
    request: Request,
    code: str,
    state: str,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Validate OAuth state
    # --------------------------------------------------------

    saved_state = request.session.get(
        "oauth_state"
    )

    code_verifier = request.session.get(
        "code_verifier"
    )

    if (
        not saved_state
        or state != saved_state
    ):

        return {
            "error": "Invalid OAuth state"
        }

    # --------------------------------------------------------
    # Create OAuth flow
    # --------------------------------------------------------

    flow = create_google_flow()

    flow.fetch_token(
        code=code,
        code_verifier=code_verifier,
        include_client_id=True,
    )

    credentials = flow.credentials

    # --------------------------------------------------------
    # Get Google account information
    # --------------------------------------------------------

    google_user = get_google_user(
        credentials.token
    )

    google_email = google_user.get(
        "email"
    )

    google_id = google_user.get(
        "id"
    )

    if (
        not google_email
        or not google_id
    ):

        return {
            "error": (
                "Could not retrieve "
                "Google account information"
            )
        }

    # --------------------------------------------------------
    # Find or create User
    # --------------------------------------------------------

    user = (
        db.query(User)
        .filter(
            User.email == google_email
        )
        .first()
    )

    if user is None:

        user = User(
            email=google_email
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    # --------------------------------------------------------
    # Find or create Gmail EmailAccount
    # --------------------------------------------------------

    email_account = (
        db.query(EmailAccount)
        .filter(
            EmailAccount.user_id == user.id,
            EmailAccount.provider == "gmail",
        )
        .first()
    )

    if email_account is None:

        email_account = EmailAccount(
            user_id=user.id,
            provider="gmail",
            provider_account_id=google_id,
        )

        db.add(email_account)
        db.commit()
        db.refresh(email_account)

    # --------------------------------------------------------
    # Save OAuth credentials
    # --------------------------------------------------------

    save_google_credentials(
        db=db,
        email_account=email_account,
        credentials=credentials,
    )

    # --------------------------------------------------------
    # Create application session
    # --------------------------------------------------------

    request.session["user_id"] = user.id

    request.session["email_account_id"] = (
        email_account.id
    )

    request.session["email"] = user.email

    # --------------------------------------------------------
    # Clear OAuth temporary session data
    # --------------------------------------------------------

    request.session.pop(
        "oauth_state",
        None,
    )

    request.session.pop(
        "code_verifier",
        None,
    )

    # --------------------------------------------------------
    # Redirect to frontend
    # --------------------------------------------------------

    frontend_url = os.getenv(
        "FRONTEND_URL",
        "http://localhost:5173",
    )

    return RedirectResponse(
        url=f"{frontend_url}?connected=true"
    )


# ============================================================
# Current Authenticated User
# ============================================================

@app.get("/auth/me")
def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
):

    user_id = request.session.get(
        "user_id"
    )

    if not user_id:

        return {
            "authenticated": False,
            "user": None,
            "email_account_id": None,
        }

    user = (
        db.query(User)
        .filter(
            User.id == user_id
        )
        .first()
    )

    if user is None:

        request.session.clear()

        return {
            "authenticated": False,
            "user": None,
            "email_account_id": None,
        }

    email_account = (
        db.query(EmailAccount)
        .filter(
            EmailAccount.user_id == user.id,
            EmailAccount.provider == "gmail",
        )
        .first()
    )

    if email_account is None:

        return {
            "authenticated": False,
            "user": None,
            "email_account_id": None,
        }

    return {
        "authenticated": True,
        "user": {
            "id": user.id,
            "email": user.email,
        },
        "email_account_id": email_account.id,
    }


# ============================================================
# Logout
# ============================================================

@app.post("/auth/logout")
def logout(
    request: Request,
):

    request.session.clear()

    return {
        "message": "Logged out successfully"
    }


# ============================================================
# Gmail Sync
# ============================================================

@app.post("/api/emails/sync")
def sync_emails(
    email_account_id: int,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Find email account
    # --------------------------------------------------------

    email_account = (
        db.query(EmailAccount)
        .filter(
            EmailAccount.id
            == email_account_id
        )
        .first()
    )

    if email_account is None:

        return {
            "error": (
                "Email account not found"
            )
        }

    # --------------------------------------------------------
    # Load encrypted credentials
    # --------------------------------------------------------

    try:

        credentials = (
            load_google_credentials(
                email_account
            )
        )

    except Exception as error:

        return {
            "error": (
                "Could not load "
                "Google credentials"
            ),
            "details": str(error),
        }

    # --------------------------------------------------------
    # Sync Gmail messages
    # --------------------------------------------------------

    try:

        result = sync_gmail_emails(
            db=db,
            email_account=email_account,
            credentials=credentials,
            max_results=10,
        )

        return result

    except Exception as error:

        return {
            "error": "Gmail synchronization failed",
            "details": str(error),
        }


# ============================================================
# Gemini - Test One Email
# ============================================================

@app.post("/api/ai/test-classification")
def test_classification(
    email_account_id: int,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Find email account
    # --------------------------------------------------------

    email_account = (
        db.query(EmailAccount)
        .filter(
            EmailAccount.id
            == email_account_id
        )
        .first()
    )

    if email_account is None:

        return {
            "error": (
                "Email account not found"
            )
        }

    # --------------------------------------------------------
    # Get one email
    # --------------------------------------------------------

    email = (
        db.query(Email)
        .filter(
            Email.email_account_id
            == email_account_id
        )
        .order_by(
            Email.created_at.asc()
        )
        .first()
    )

    if email is None:

        return {
            "error": "No emails found"
        }

    # --------------------------------------------------------
    # Classify with Gemini
    # --------------------------------------------------------

    try:

        result = classify_email(
            sender=email.sender or "",
            sender_name=email.sender_name or "",
            subject=email.subject or "",
            body=email.body or "",
        )

        return {
            "email_id": email.id,
            "classification": (
                result.model_dump()
            ),
        }

    except Exception as error:

        return {
            "error": (
                "Gemini classification failed"
            ),
            "details": str(error),
        }


# ============================================================
# Gemini - Classify All Emails
# ============================================================

@app.post("/api/ai/classify")
def classify_emails(
    email_account_id: int,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Find email account
    # --------------------------------------------------------

    email_account = (
        db.query(EmailAccount)
        .filter(
            EmailAccount.id
            == email_account_id
        )
        .first()
    )

    if email_account is None:

        return {
            "error": (
                "Email account not found"
            )
        }

    # --------------------------------------------------------
    # Classify account emails
    # --------------------------------------------------------

    try:

        result = classify_account_emails(
            db=db,
            email_account=email_account,
        )

        return result

    except Exception as error:

        return {
            "error": (
                "Email classification failed"
            ),
            "details": str(error),
        }


# ============================================================
# Root
# ============================================================

@app.get("/")
def root():

    return {
        "service": "AI Mail Manager",
        "status": "running",
        "docs": "/docs",
    }


# ============================================================
# Scheduler
# ============================================================

@app.on_event("startup")
def startup_event():

    start_scheduler()


@app.on_event("shutdown")
def shutdown_event():

    stop_scheduler()
