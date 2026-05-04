from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from azure.communication.email.aio import EmailClient

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

    In ``local`` environments the full email is printed to stderr (no SMTP or
    cloud service required).  In all other environments Azure Communication
    Services is used; the caller must supply ``acs_connection_string`` and
    ``acs_from_address`` (injected from ACA secrets via Bicep).

    Args:
        app_env: The application environment string (``"local"``, ``"dev"``,
            ``"production"``).
        acs_connection_string: ACS connection string.  Required in non-local
            environments.
        acs_from_address: Verified sender address from the ACS managed domain.
            Required in non-local environments.
    """

    def __init__(
        self,
        *,
        app_env: str,
        acs_connection_string: str | None = None,
        acs_from_address: str | None = None,
    ) -> None:
        self._app_env = app_env
        self._acs_connection_string = acs_connection_string
        self._acs_from_address = acs_from_address

    @classmethod
    def from_settings(cls, settings: Settings) -> EmailSender:
        """Construct an :class:`EmailSender` from application settings."""
        return cls(
            app_env=settings.app_env,
            acs_connection_string=settings.acs_connection_string,
            acs_from_address=settings.acs_from_address,
        )

    async def send(self, message: EmailMessage) -> None:
        """Deliver *message*.

        In ``local`` environments the message is printed to *stderr*.
        In all other environments the message is sent via Azure Communication
        Services Email.

        Args:
            message: The email to deliver.

        Raises:
            EmailDeliveryError: When ACS credentials are missing or delivery fails.
        """
        if self._app_env in ("local", "e2e"):
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

        if not self._acs_connection_string or not self._acs_from_address:
            logger.error(
                "ACS email not configured; message not sent.",
                extra={"to": message.to, "subject": message.subject},
            )
            raise EmailDeliveryError(
                "ACS_CONNECTION_STRING and ACS_FROM_ADDRESS must be set for email delivery."
            )

        client = EmailClient.from_connection_string(self._acs_connection_string)
        async with client:
            poller = await client.begin_send(
                {
                    "senderAddress": self._acs_from_address,
                    "recipients": {"to": [{"address": message.to}]},
                    "content": {"subject": message.subject, "plainText": message.body},
                }
            )
            await poller.result()
            logger.info(
                "Email sent via ACS.",
                extra={"to": message.to, "subject": message.subject},
            )
