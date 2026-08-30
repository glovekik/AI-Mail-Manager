from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class Email(Base):
    __tablename__ = "emails"

    __table_args__ = (
        UniqueConstraint(
            "email_account_id",
            "provider_message_id",
            name="uq_email_account_message",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    email_account_id: Mapped[int] = mapped_column(
        ForeignKey("email_accounts.id"),
        nullable=False,
    )

    provider_message_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    thread_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    sender: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    sender_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    subject: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    received_at: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    snippet: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    body: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    labels: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    email_account = relationship(
        "EmailAccount",
        back_populates="emails",
    )

    classification = relationship(
        "EmailClassification",
        back_populates="email",
        uselist=False,
        cascade="all, delete-orphan",
    )
