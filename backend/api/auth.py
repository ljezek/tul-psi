from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlmodel import Session

from db.session import get_session
from services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_TUL_DOMAIN = "tul.cz"


class OtpRequestBody(BaseModel):
    """Request body for the OTP request endpoint."""

    email: EmailStr

    @field_validator("email")
    @classmethod
    def email_must_be_tul_domain(cls, v: str) -> str:
        """Reject any address whose domain is not @tul.cz."""
        domain = v.split("@", 1)[-1].lower()
        if domain != _TUL_DOMAIN:
            raise ValueError(f"Only @{_TUL_DOMAIN} email addresses are accepted.")
        return v


class OtpRequestResponse(BaseModel):
    """Response body for the OTP request endpoint."""

    message: str


@router.post(
    "/otp/request",
    response_model=OtpRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Request a one-time password",
    description=(
        "Sends a 6-digit OTP to the supplied ``@tul.cz`` address. Always returns HTTP 200 "
        "regardless of whether the address is registered to prevent user enumeration."
    ),
)
def request_otp(
    body: OtpRequestBody,
    session: Session = Depends(get_session),
) -> OtpRequestResponse:
    """Handle a request for a one-time password.

    Domain validation is enforced at the Pydantic model level (422 for non-@tul.cz).
    Delegates to :func:`auth_service.request_otp` which generates the OTP, hashes it,
    persists it, and logs the plaintext value in lieu of SMTP.
    """
    auth_service.request_otp(body.email, session)

    return OtpRequestResponse(message="If this email is registered, an OTP has been sent.")
