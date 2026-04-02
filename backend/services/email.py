from __future__ import annotations

import sys
from dataclasses import dataclass

from settings import get_settings

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

    All templates read ``frontend_url`` from the application settings so that
    the portal link in each email body points to the correct environment.
    """

    @classmethod
    def otp(cls, to: str, otp_code: str) -> EmailMessage:
        """Return a one-time-password email addressed to *to*.

        Args:
            to: Recipient e-mail address.
            otp_code: The plaintext 6-digit OTP that the user must enter.
        """
        portal_url = get_settings().frontend_url
        return EmailMessage(
            to=to,
            subject=f"{_SUBJECT_PREFIX}Your one-time login code",
            body=(
                f"Hello,\n\n"
                f"Your one-time login code is: {otp_code}\n\n"
                f"The code is valid for 15 minutes and can only be used once.\n"
                f"If you did not request this code, you can safely ignore this email.\n\n"
                f"Visit the portal: {portal_url}\n\n"
                f"{_SIGN_OFF}"
            ),
        )

    @classmethod
    def project_invite(cls, to: str, project_name: str, course_name: str) -> EmailMessage:
        """Return a project-invitation email addressed to *to*.

        Args:
            to: Recipient e-mail address.
            project_name: Human-readable name of the project the user is invited to.
            course_name: Human-readable name of the course the project belongs to.
        """
        portal_url = get_settings().frontend_url
        return EmailMessage(
            to=to,
            subject=f'{_SUBJECT_PREFIX}You have been invited to project "{project_name}"',
            body=(
                f"Hello,\n\n"
                f'You have been invited to join the project "{project_name}" '
                f'in the course "{course_name}".\n\n'
                f"Please log in to the TUL Student Projects Catalogue to accept or decline.\n\n"
                f"Visit the portal: {portal_url}\n\n"
                f"{_SIGN_OFF}"
            ),
        )

    @classmethod
    def course_invite(
        cls,
        to: str,
        course_name: str,
        *,
        peer_feedback_enabled: bool = False,
    ) -> EmailMessage:
        """Return a course-invitation email addressed to a lecturer.

        Args:
            to: Recipient e-mail address.
            course_name: Human-readable name of the course the lecturer is invited to.
            peer_feedback_enabled: When ``True``, the body mentions that the course
                uses peer feedback assessment.
        """
        portal_url = get_settings().frontend_url
        peer_feedback_note = (
            "\nThis course uses peer feedback assessment. "
            "Students will be asked to review each other's contributions.\n"
            if peer_feedback_enabled
            else ""
        )
        return EmailMessage(
            to=to,
            subject=(
                f'{_SUBJECT_PREFIX}You have been invited as a lecturer to course "{course_name}"'
            ),
            body=(
                f"Hello,\n\n"
                f'You have been invited as a lecturer to the course "{course_name}" '
                f"in the TUL Student Projects Catalogue.\n\n"
                f"Please log in to manage the course details, add other lecturers, "
                f"create student projects and evaluate existing ones."
                f"{peer_feedback_note}\n\n"
                f"Visit the portal: {portal_url}\n\n"
                f"{_SIGN_OFF}"
            ),
        )

    @classmethod
    def results_unlocked(
        cls,
        to: str,
        project_name: str,
        *,
        peer_feedback_enabled: bool = False,
    ) -> EmailMessage:
        """Return a results-unlocked notification email addressed to *to*.

        This email is sent when evaluation results for a project become visible
        to its members.

        Args:
            to: Recipient e-mail address.
            project_name: Human-readable name of the project whose results are now visible.
            peer_feedback_enabled: When ``True``, the body mentions that peer feedback
                results are also available.
        """
        portal_url = get_settings().frontend_url
        peer_feedback_note = (
            " Peer feedback contributions for this project are also visible."
            if peer_feedback_enabled
            else ""
        )
        return EmailMessage(
            to=to,
            subject=f'{_SUBJECT_PREFIX}Results are now available for "{project_name}"',
            body=(
                f"Hello,\n\n"
                f'The evaluation results for your project "{project_name}" '
                f"have been published and are now available in the "
                f"TUL Student Projects Catalogue.\n\n"
                f"Log in to view your results.{peer_feedback_note}\n\n"
                f"Visit the portal: {portal_url}\n\n"
                f"{_SIGN_OFF}"
            ),
        )


# ---------------------------------------------------------------------------
# Sender (fake / dev implementation)
# ---------------------------------------------------------------------------


class EmailSender:
    """Fake email sender for local development that writes messages to *stderr*.

    In a ``local`` environment the full email is printed to stderr so that
    developers can inspect it without a running SMTP server.

    In any other environment (``dev``, ``production``, …) this class raises
    :exc:`NotImplementedError` on :meth:`send` because a real SMTP integration
    has not yet been implemented.  This prevents the fake sender from being
    accidentally used in non-local deployments.

    Args:
        app_env: The application environment string.  When ``None`` (default),
            it is read from :func:`~settings.get_settings`.  Pass an explicit
            value in tests to avoid depending on the live settings object.
    """

    def __init__(self, *, app_env: str | None = None) -> None:
        self._app_env = app_env if app_env is not None else get_settings().app_env

    def send(self, message: EmailMessage) -> None:
        """Deliver *message* according to the current environment.

        In a ``local`` environment the message is printed to *stderr* in a
        human-readable format.  In any other environment a
        :exc:`NotImplementedError` is raised because real SMTP delivery is
        not yet implemented.

        Args:
            message: The email to deliver.

        Raises:
            NotImplementedError: When the environment is not ``local``.
        """
        if self._app_env != "local":
            raise NotImplementedError(
                f"Real SMTP delivery is not yet implemented. "
                f"EmailSender cannot be used in the '{self._app_env}' environment."
            )
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
