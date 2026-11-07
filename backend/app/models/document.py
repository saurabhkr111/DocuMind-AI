from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base


class Document(Base):

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("workflows.id"),
        nullable=False
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    document_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    approval_status: Mapped[str] = mapped_column(
    String(30),
    nullable=False,
    default="PENDING",
    server_default="PENDING"
    )
    reviewed_by: Mapped[str | None] = mapped_column(
    String(255),
    nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True),
    nullable=True
    )
    approval_reason: Mapped[str | None] = mapped_column(
    Text,
    nullable=True
    )




    workflow = relationship(
        "Workflow",
        back_populates="documents"
    )