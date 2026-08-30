import os

from dotenv import load_dotenv
from google import genai

from app.ai.prompts import (
    build_email_classification_prompt,
)
from app.ai.schemas import (
    EmailClassificationResult,
)


load_dotenv()


GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.7-flash",
)


if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not configured."
    )


client = genai.Client(
    api_key=GEMINI_API_KEY
)


def classify_email(
    sender: str,
    sender_name: str,
    subject: str,
    body: str,
) -> EmailClassificationResult:

    prompt = build_email_classification_prompt(
        sender=sender,
        sender_name=sender_name,
        subject=subject,
        body=body,
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": (
                EmailClassificationResult
            ),
        },
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return EmailClassificationResult.model_validate_json(
        response.text
    )