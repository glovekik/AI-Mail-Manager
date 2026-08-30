from datetime import datetime, timezone

from google.oauth2.credentials import Credentials
from sqlalchemy.orm import Session

from app.models import EmailAccount
from app.security.token_encryption import (
    decrypt_token,
    encrypt_token,
)


def save_google_credentials(
    db: Session,
    email_account: EmailAccount,
    credentials: Credentials,
):
    email_account.access_token = encrypt_token(
        credentials.token
    )

    if credentials.refresh_token:
        email_account.refresh_token = (
            encrypt_token(
                credentials.refresh_token
            )
        )

    if credentials.expiry:
        expiry = credentials.expiry

        if expiry.tzinfo is None:
            expiry = expiry.replace(
                tzinfo=timezone.utc
            )

        email_account.token_expiry = expiry

    db.add(email_account)
    db.commit()
    db.refresh(email_account)


def load_google_credentials(
    email_account: EmailAccount,
) -> Credentials:

    access_token = decrypt_token(
        email_account.access_token
    )

    refresh_token = decrypt_token(
        email_account.refresh_token
    )

    if not access_token and not refresh_token:
        raise RuntimeError(
            "No Google credentials found "
            "for this email account."
        )

    expiry = email_account.token_expiry

    return Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=None,
        client_secret=None,
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/gmail.modify",
        ],
    )