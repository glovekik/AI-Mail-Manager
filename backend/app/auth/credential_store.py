from google.oauth2.credentials import Credentials


_credentials = {}


def save_credentials(
    email_account_id: int,
    credentials: Credentials,
):
    _credentials[email_account_id] = credentials


def get_credentials(email_account_id: int):
    return _credentials.get(email_account_id)