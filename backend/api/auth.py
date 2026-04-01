from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from services import auth_service
from settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_TUL_DOMAIN = "tul.cz"

# JWT session cookie lifetime — derived from auth_service to avoid configuration drift.
_COOKIE_MAX_AGE_SECONDS = int(auth_service._JWT_TTL_HOURS * 3600)


def _validate_tul_email(v: str) -> str:
    """Normalise and validate that *v* is a @tul.cz e-mail address.

    Strips whitespace and lowercases the address so that subsequent
    case-sensitive DB lookups behave consistently.  Raises ``ValueError``
    (which Pydantic converts to a 422 response) for any other domain.
    """
    v = v.strip().lower()
    domain = v.split("@", 1)[-1]
    if domain != _TUL_DOMAIN:
        raise ValueError(f"Only @{_TUL_DOMAIN} email addresses are accepted.")
    return v


class OtpRequestBody(BaseModel):
    """Request body for the OTP request endpoint."""

    email: EmailStr

    @field_validator("email")
    @classmethod
    def email_must_be_tul_domain(cls, v: str) -> str:
        """Reject any address whose domain is not @tul.cz."""
        return _validate_tul_email(v)


class OtpRequestResponse(BaseModel):
    """Response body for the OTP request endpoint."""

    message: str


class OtpVerifyBody(BaseModel):
    """Request body for the OTP verify endpoint."""

    email: EmailStr
    # The OTP is kept as a string to preserve any leading zeros (e.g. "001234")
    # and to allow future expansion to non-numeric characters without a schema change.
    otp: str

    @field_validator("email")
    @classmethod
    def email_must_be_tul_domain(cls, v: str) -> str:
        """Reject any address whose domain is not @tul.cz."""
        return _validate_tul_email(v)


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
        "Validates the OTP for the user identified by ``email``, marks it as used, and sets "
        "an HttpOnly ``session`` cookie containing a signed JWT.  Returns HTTP 401 for an "
        "invalid or expired code, and HTTP 429 when the per-token failed-attempt limit is exceeded."
    ),
)
async def verify_otp(
    body: OtpVerifyBody,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Handle OTP verification and JWT issuance for the user identified by *body.email*.

    On success, a signed JWT is stored in an HttpOnly cookie named ``session``.
    The ``Secure`` flag is enabled in all non-local environments so that the
    cookie is only transmitted over HTTPS, as required by DESIGN.md.  It is
    intentionally disabled for the ``local`` environment to allow plain-HTTP
    development without additional TLS setup.
    """
    try:
        jwt_token = await auth_service.verify_otp(body.email, body.otp, session)
    except auth_service.TooManyAttemptsError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts — request a new OTP code",
        ) from None
    except auth_service.IncorrectOtpError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired code",
        ) from None

    settings = get_settings()
    # Secure cookies require HTTPS; disable only for the local development environment.
    secure_cookie = settings.app_env != "local"
    response.set_cookie(
        key="session",
        value=jwt_token,
        httponly=True,
        secure=secure_cookie,
        samesite="strict",
        max_age=_COOKIE_MAX_AGE_SECONDS,
    )
    return {}
