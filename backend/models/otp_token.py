from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from sqlalchemy import Column
from sqlalchemy import DateTime as SADateTime
from sqlmodel import Field, SQLModel


class OtpToken(SQLModel, table=True):
    """One-time password token used for passwordless authentication.

    The raw OTP is never stored; only its hash is persisted in
    ``token_hash``.  ``attempts`` tracks failed verification tries so the
    API can enforce a per-token limit and return HTTP 429 before the token
    is brute-forced.  Once ``used`` is ``True`` the token cannot be
    verified again regardless of ``expires_at``.
    """

    __tablename__: ClassVar[str] = "otp_token"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    # Hash of the raw OTP — the raw value must never be stored.
    # Indexed because every OTP verification queries by token_hash.
    token_hash: str = Field(index=True, max_length=255)
    # Number of failed verification attempts; used to enforce retry limits.
    attempts: int = Field(default=0)
    expires_at: datetime = Field(
        sa_column=Column(SADateTime(timezone=True), nullable=False)
    )
    # Once True the token is consumed and cannot be used again.
    used: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(SADateTime(timezone=True), nullable=False),
    )
