from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_TUL_DOMAIN = "tul.cz"

# JWT session cookie lifetime — must match the token expiry in auth_service.
_COOKIE_MAX_AGE_SECONDS = 8 * 3600


class OtpRequestBody(BaseModel):
    """Request body for the OTP request endpoint."""

    email: EmailStr

    @field_validator("email")
    @classmethod
    def email_must_be_tul_domain(cls, v: str) -> str:
        """Reject any address whose domain is not @tul.cz."""
        # Normalize the entire email address to lowercase so that subsequent lookups
        # using case-sensitive comparisons behave consistently.
        v = v.strip().lower()
        domain = v.split("@", 1)[-1]
        if domain != _TUL_DOMAIN:
            raise ValueError(f"Only @{_TUL_DOMAIN} email addresses are accepted.")
        return v


class OtpRequestResponse(BaseModel):
    """Response body for the OTP request endpoint."""

    message: str


class OtpVerifyBody(BaseModel):
    """Request body for the OTP verify endpoint."""

    email: EmailStr
    otp: str

    @field_validator("email")
    @classmethod
    def email_must_be_tul_domain(cls, v: str) -> str:
        """Reject any address whose domain is not @tul.cz."""
        v = v.strip().lower()
        domain = v.split("@", 1)[-1]
        if domain != _TUL_DOMAIN:
            raise ValueError(f"Only @{_TUL_DOMAIN} email addresses are accepted.")
        return v


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
async def request_otp(
    body: OtpRequestBody,
    session: AsyncSession = Depends(get_session),
) -> OtpRequestResponse:
    """Handle a request for a one-time password.

    Domain validation is enforced at the Pydantic model level (422 for non-@tul.cz).
    Delegates to :func:`auth_service.request_otp` which generates the OTP, hashes it,
    persists it, and logs the plaintext value in lieu of SMTP.
    """
    await auth_service.request_otp(body.email, session)

    return OtpRequestResponse(message="If this email is registered, an OTP has been sent.")


@router.post(
    "/otp/verify",
    status_code=status.HTTP_200_OK,
    summary="Verify a one-time password",
    description=(
        "Validates the OTP, marks it as used, and sets an HttpOnly ``session`` cookie "
        "containing a signed JWT.  Returns HTTP 401 for an invalid or expired code, and "
        "HTTP 429 when the per-token failed-attempt limit is exceeded."
    ),
)
async def verify_otp(
    body: OtpVerifyBody,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Handle OTP verification and JWT issuance.

    On success, a signed JWT is stored in an HttpOnly cookie named ``session``.
    The cookie is also marked ``Secure`` and ``SameSite=Strict`` as required
    by the security policy documented in DESIGN.md.
    """
    try:
        jwt_token = await auth_service.verify_otp(body.email, body.otp, session)
    except auth_service.TooManyAttemptsError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts — request a new code",
        ) from None
    except auth_service.InvalidOtpError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired code",
        ) from None

    response.set_cookie(
        key="session",
        value=jwt_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=_COOKIE_MAX_AGE_SECONDS,
    )
    return {}
