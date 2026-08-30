import requests


GOOGLE_USERINFO_URL = (
    "https://www.googleapis.com/oauth2/v2/userinfo"
)


def get_google_user(access_token: str) -> dict:
    response = requests.get(
        GOOGLE_USERINFO_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        timeout=10,
    )

    response.raise_for_status()

    return response.json()