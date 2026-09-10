from typing import Literal

from pydantic import BaseModel, Field


class EmailAssistantIntent(BaseModel):
    intent: Literal[
        "search_emails",
        "sync_emails",
        "summarize_emails",
        "unknown",
    ] = Field(
        description="The action the user wants the email assistant to perform."
    )

    search_query: str | None = Field(
        default=None,
        description="Company, sender, subject, or keyword to search for.",
    )

    job_only: bool = Field(
        default=False,
        description="True when the user asks specifically about job applications.",
    )

    date_from: str | None = Field(
        default=None,
        description="Start date in YYYY-MM-DD format.",
    )

    date_to: str | None = Field(
        default=None,
        description="End date in YYYY-MM-DD format.",
    )
