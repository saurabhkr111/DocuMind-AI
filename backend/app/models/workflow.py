from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base


class Workflow(Base):

    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING",
        nullable=False
    )

    source_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    source_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    agent_logs = relationship(
        "AgentLog",
        back_populates="workflow",
        cascade="all, delete-orphan"
    )

    documents = relationship(
        "Document",
        back_populates="workflow",
        cascade="all, delete-orphan"
    )