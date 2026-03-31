from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlmodel import Session

from db.session import get_session
from services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_TUL_DOMAIN = "tul.cz"


class OtpRequestBody(BaseModel):
    """Request body for the OTP request endpoint."""

    email: EmailStr


class OtpRequestResponse(BaseModel):
    """Response body for the OTP request endpoint."""

    message: str


@router.post(
    "/otp/request",
    response_model=OtpRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Request a one-time password",
    description=(
        "Sends a 6-digit OTP to the supplied ``@tul.cz`` address. "
        "Always returns HTTP 200 regardless of whether the address is "
        "registered to prevent user enumeration."
    ),
)
async def request_otp(
    body: OtpRequestBody,
    session: Session = Depends(get_session),
) -> OtpRequestResponse:
    """Handle a request for a one-time password.

    Validates that the email belongs to the ``@tul.cz`` domain (422 otherwise),
    then delegates to :func:`auth_service.request_otp` which generates the OTP,
    hashes it, persists it, and logs the plaintext value in lieu of SMTP.
    """
    domain = body.email.split("@", 1)[-1].lower()
    if domain != _TUL_DOMAIN:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Only @{_TUL_DOMAIN} email addresses are accepted.",
        )

    auth_service.request_otp(body.email, session)

    return OtpRequestResponse(message="If this email is registered, an OTP has been sent.")
