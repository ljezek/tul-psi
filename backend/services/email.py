from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from email.message import EmailMessage as MIMEMessage
from typing import TYPE_CHECKING, Literal

import aiosmtplib

if TYPE_CHECKING:
    from settings import Settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EmailMessage:
    """An immutable representation of an outgoing email.

    All three fields are required; the body is plain-text only at this stage.
    """

    to: str
    subject: str
    body: str


# ---------------------------------------------------------------------------
# Template factory
# ---------------------------------------------------------------------------

# Prefix applied to every outgoing email subject for consistent branding.
_SUBJECT_PREFIX = "TUL Student Projects: "

# Sign-off line used at the end of every email body.
_SIGN_OFF = "Regards,\nTUL Student Projects Catalogue"


class EmailTemplate:
    """Factory that constructs :class:`EmailMessage` instances for common emails.

    Each class method corresponds to one notification type.  Keeping template
    logic here (rather than inline in callers) makes it easy to later migrate
    to Jinja2 or another templating engine without touching call-sites.

    All template methods require the caller to supply *portal_url* explicitly
    so that this module has no dependency on application settings.  The caller
    reads ``settings.frontend_url`` and passes it here.
    """

    @staticmethod
    def _greeting(recipient_name: str | None) -> str:
        """Return a greeting line with an optional display name."""
        # Collapse all whitespace so user-provided names cannot create multi-line greetings.
        greeting_name = " ".join(recipient_name.split()) if recipient_name else ""
        return f"Hello {greeting_name}," if greeting_name else "Hello,"

    @classmethod
    def otp(
        cls,
        to: str,
        otp_code: str,
        *,
        portal_url: str,
        recipient_name: str | None = None,
    ) -> EmailMessage:
        """Return a one-time-password email addressed to *to*.

        Args:
            to: Recipient e-mail address.
            otp_code: The plaintext 6-digit OTP that the user must enter.
            portal_url: Absolute URL of the frontend portal to embed in the body.
            recipient_name: Optional recipient display name used in the greeting.
        """
        greeting = cls._greeting(recipient_name)
        return EmailMessage(
            to=to,
            subject=f"{_SUBJECT_PREFIX}Your one-time login code",
            body=(
                f"{greeting}\n\n"
                f"Your one-time login code for the "
                f"TUL Student Projects Catalogue is: {otp_code}\n\n"
                f"This code is valid for 15 minutes and can only be used once.\n"
                f"If you did not request a login, you can safely ignore this email.\n\n"
                f"You can continue in the portal here: {portal_url}\n\n"
                f"{_SIGN_OFF}"
            ),
        )

    @classmethod
    def project_invite(
        cls,
        to: str,
        project_name: str,
        course_name: str,
        *,
        portal_url: str,
        recipient_name: str | None = None,
    ) -> EmailMessage:
        """Return a project-invitation email addressed to *to*.

        Args:
            to: Recipient e-mail address.
            project_name: Human-readable name of the project the user is invited to.
            course_name: Human-readable name of the course the project belongs to.
            portal_url: Absolute URL of the frontend portal to embed in the body.
            recipient_name: Optional recipient display name used in the greeting.
        """
        return EmailMessage(
            to=to,
            subject=f'{_SUBJECT_PREFIX}You have been invited to project "{project_name}"',
            body=(
                f"{cls._greeting(recipient_name)}\n\n"
                f'You have been invited to join the project "{project_name}" '
                f'in the course "{course_name}".\n\n'
                f"Please sign in to the TUL Student Projects Catalogue "
                f"to see details and next steps:\n"
                f"{portal_url}\n\n"
                f"{_SIGN_OFF}"
            ),
        )

    @classmethod
    def course_invite(
        cls,
        to: str,
        course_name: str,
        *,
        portal_url: str,
        recipient_name: str | None = None,
    ) -> EmailMessage:
        """Return a course-invitation email addressed to a lecturer.

        Args:
            to: Recipient e-mail address.
            course_name: Human-readable name of the course the lecturer is invited to.
            portal_url: Absolute URL of the frontend portal to embed in the body.
            recipient_name: Optional recipient display name used in the greeting.
        """
        return EmailMessage(
            to=to,
            subject=(
                f'{_SUBJECT_PREFIX}You have been invited as a lecturer to course "{course_name}"'
            ),
            body=(
                f"{cls._greeting(recipient_name)}\n\n"
                f'You have been invited as a lecturer to the course "{course_name}" '
                f"in the TUL Student Projects Catalogue.\n\n"
                f"After signing in, you can coordinate with fellow lecturers, "
                f"manage project topics, "
                f"and evaluate student project work.\n\n"
                f"Portal: {portal_url}\n\n"
                f"{_SIGN_OFF}"
            ),
        )

    @classmethod
    def user_invite(
        cls,
        to: str,
        role: str,
        *,
        portal_url: str,
        recipient_name: str | None = None,
    ) -> EmailMessage:
        """Return a user-invitation email addressed to a new user.

        Args:
            to: Recipient e-mail address.
            role: The role the user has been invited to assume.
            portal_url: Absolute URL of the frontend portal to embed in the body.
            recipient_name: Optional recipient display name used in the greeting.
        """
        return EmailMessage(
            to=to,
            subject=(f"{_SUBJECT_PREFIX}You have been invited as a {role}"),
            body=(
                f"{cls._greeting(recipient_name)}\n\n"
                f"You have been invited as a {role} to the TUL Student Projects Catalogue.\n\n"
                f"After signing in, you can complete your profile and "
                f"access course and project information.\n\n"
                f"Portal: {portal_url}\n\n"
                f"{_SIGN_OFF}"
            ),
        )

    @classmethod
    def results_unlocked(
        cls,
        to: str,
        project_name: str,
        *,
        portal_url: str,
        peer_feedback_enabled: bool = False,
        recipient_name: str | None = None,
    ) -> EmailMessage:
        """Return a results-unlocked notification email addressed to *to*.

        This email is sent when evaluation results for a project become visible
        to its members.

        Args:
            to: Recipient e-mail address.
            project_name: Human-readable name of the project whose results are now visible.
            portal_url: Absolute URL of the frontend portal to embed in the body.
            peer_feedback_enabled: When ``True``, the body mentions that peer feedback
                results are also available.
            recipient_name: Optional recipient display name used in the greeting.
        """
        peer_feedback_note = (
            " Peer feedback contributions for this project are also visible."
            if peer_feedback_enabled
            else ""
        )
        return EmailMessage(
            to=to,
            subject=f'{_SUBJECT_PREFIX}Results are now available for "{project_name}"',
            body=(
                f"{cls._greeting(recipient_name)}\n\n"
                f'The evaluation results for your project "{project_name}" '
                f"have been submitted and are now available in the "
                f"TUL Student Projects Catalogue.\n\n"
                f"Please sign in to review the feedback and final evaluation."
                f"{peer_feedback_note}\n\n"
                f"Portal: {portal_url}\n\n"
                f"{_SIGN_OFF}"
            ),
        )


# ---------------------------------------------------------------------------
# Delivery errors
# ---------------------------------------------------------------------------


class EmailDeliveryError(Exception):
    """Raised when email delivery fails or is not configured."""


# Backwards-compatible alias used by existing tests and service code.
EmailDeliveryNotImplementedError = EmailDeliveryError


# ---------------------------------------------------------------------------
# Sender
# ---------------------------------------------------------------------------


class EmailSender:
    """Delivers email messages.

    The active backend is selected by *email_backend*:

    - ``"auto"``    — console (stderr) when *app_env* is ``"local"`` or ``"e2e"``,
      SMTP otherwise.  This is the production default.
    - ``"smtp"``    — always deliver via SMTP regardless of *app_env*.  Set
      ``EMAIL_BACKEND=smtp`` locally to test real delivery end-to-end.
    - ``"console"`` — always print to stderr.  Useful for silencing email in a
      live environment during debugging without touching SMTP credentials.

    Args:
        app_env: The application environment string (``"local"``, ``"dev"``,
            ``"production"``).
        email_backend: One of ``"auto"``, ``"smtp"``, or ``"console"``.
        smtp_host: SMTP relay hostname.  Required when backend resolves to SMTP.
        smtp_port: SMTP relay port (default 587 for STARTTLS).
        smtp_username: SMTP authentication username.  Required when backend
            resolves to SMTP.
        smtp_password: SMTP authentication password.  Required when backend
            resolves to SMTP.
        smtp_from_address: Sender address used in the ``From`` header.  Required
            when backend resolves to SMTP (e.g. ``tul-projects@jezci.net``).
    """

    def __init__(
        self,
        *,
        app_env: str,
        email_backend: Literal["auto", "smtp", "console"] = "auto",
        smtp_host: str | None = None,
        smtp_port: int = 587,
        smtp_username: str | None = None,
        smtp_password: str | None = None,
        smtp_from_address: str | None = None,
    ) -> None:
        self._app_env = app_env
        self._email_backend = email_backend
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._smtp_username = smtp_username
        self._smtp_password = smtp_password
        self._smtp_from_address = smtp_from_address

    @classmethod
    def from_settings(cls, settings: Settings) -> EmailSender:
        """Construct an :class:`EmailSender` from application settings."""
        return cls(
            app_env=settings.app_env,
            email_backend=settings.email_backend,
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_username=settings.smtp_username,
            smtp_password=settings.smtp_password,
            smtp_from_address=settings.smtp_from_address,
        )

    async def send(self, message: EmailMessage) -> None:
        """Deliver *message*.

        Routes the message to the console or SMTP depending on *email_backend*
        and *app_env* (see class docstring).

        Args:
            message: The email to deliver.

        Raises:
            EmailDeliveryError: When SMTP credentials are missing or delivery fails.
        """
        use_console = self._email_backend == "console" or (
            self._email_backend == "auto" and self._app_env in ("local", "e2e")
        )
        if use_console:
            print(  # noqa: T201
                f"\n{'=' * 60}\n"
                f"[FAKE EMAIL]\n"
                f"To:      {message.to}\n"
                f"Subject: {message.subject}\n"
                f"{'-' * 60}\n"
                f"{message.body}\n"
                f"{'=' * 60}\n",
                file=sys.stderr,
            )
            return

        if not all(
            [self._smtp_host, self._smtp_username, self._smtp_password, self._smtp_from_address]
        ):
            logger.error(
                "SMTP email not configured; message not sent.",
                extra={"to": message.to, "subject": message.subject},
            )
            raise EmailDeliveryError(
                "SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, and SMTP_FROM_ADDRESS must be set "
                "for email delivery."
            )

        # Build a MIME message so that the relay receives a well-formed RFC 5322 message.
        mime_message = MIMEMessage()
        mime_message["From"] = f"TUL Student Projects <{self._smtp_from_address}>"
        mime_message["To"] = message.to
        mime_message["Subject"] = message.subject
        mime_message.set_content(message.body)

        await aiosmtplib.send(
            mime_message,
            hostname=self._smtp_host,
            port=self._smtp_port,
            username=self._smtp_username,
            password=self._smtp_password,
            start_tls=True,
        )
        logger.info(
            "Email sent via SMTP.",
            extra={"to": message.to, "subject": message.subject},
        )
