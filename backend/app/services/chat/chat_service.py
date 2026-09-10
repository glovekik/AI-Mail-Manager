import time

from app.ai.chat_prompts import (
    build_email_assistant_prompt,
)
from app.ai.chat_schemas import (
    EmailAssistantIntent,
)
from app.ai.gemini_client import (
    client,
    GEMINI_MODEL,
)


def understand_email_request(
    message: str,
) -> EmailAssistantIntent:

    prompt = build_email_assistant_prompt(
        message
    )

    last_error = None

    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": EmailAssistantIntent,
                },
            )

            if not response.text:
                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            return EmailAssistantIntent.model_validate_json(
                response.text
            )

        except Exception as error:

            last_error = error

            if attempt < 2:
                time.sleep(2)

    raise RuntimeError(
        f"Gemini request failed after 3 attempts: {last_error}"
    )