from typing import Literal

from pydantic import BaseModel, Field


class EmailClassificationResult(BaseModel):
    category: Literal[
        "Work",
        "Personal",
        "Finance",
        "Promotions",
        "Social",
        "Updates",
        "Spam",
        "Other",
    ] = Field(
        description="The primary category of the email."
    )

    is_job_related: bool = Field(
        description=(
            "True if the email is related to a job "
            "application, recruitment, interview, "
            "assessment, hiring process, offer, "
            "rejection, or communication from a "
            "company/recruiter regarding employment."
        ),
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Confidence score between 0 and 1."
        ),
    )

    recommended_action: Literal[
        "Read",
        "Reply",
        "Archive",
        "Delete",
        "Ignore",
        "Review",
    ] = Field(
        description=(
            "Recommended action for the user."
        ),
    )

    keywords: list[str] = Field(
        description=(
            "Important keywords describing "
            "the email."
        ),
    )

    reason: str = Field(
        description=(
            "Short explanation for the classification."
        ),
    )

    risk_level: Literal[
        "Low",
        "Medium",
        "High",
    ] = Field(
        description=(
            "Potential risk level of the email."
        ),
    )
