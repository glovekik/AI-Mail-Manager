import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv


load_dotenv()


TOKEN_ENCRYPTION_KEY = os.getenv(
    "TOKEN_ENCRYPTION_KEY"
)

if not TOKEN_ENCRYPTION_KEY:
    raise RuntimeError(
        "TOKEN_ENCRYPTION_KEY is not configured."
    )


fernet = Fernet(
    TOKEN_ENCRYPTION_KEY.encode()
)


def encrypt_token(token: str | None) -> str | None:
    if not token:
        return None

    return fernet.encrypt(
        token.encode()
    ).decode()


def decrypt_token(
    encrypted_token: str | None,
) -> str | None:

    if not encrypted_token:
        return None

    return fernet.decrypt(
        encrypted_token.encode()
    ).decode()