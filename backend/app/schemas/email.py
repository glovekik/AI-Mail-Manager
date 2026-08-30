from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EmailClassificationResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    category: str
    confidence: float
    recommended_action: str
    keywords: str | None = None
    reason: str | None = None
    risk_level: str | None = None


class EmailListItemResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    provider_message_id: str
    thread_id: str | None = None
    sender: str | None = None
    sender_name: str | None = None
    subject: str | None = None
    received_at: str | None = None
    snippet: str | None = None
    is_read: bool

    classification: (
        EmailClassificationResponse | None
    ) = None


class EmailListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    emails: list[EmailListItemResponse]