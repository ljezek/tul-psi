from __future__ import annotations

import sys
from dataclasses import dataclass

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


class EmailTemplate:
    """Factory that constructs :class:`EmailMessage` instances for common emails.

    Each class method corresponds to one notification type.  Keeping template
    logic here (rather than inline in callers) makes it easy to later migrate
    to Jinja2 or another templating engine without touching call-sites.
    """

    @classmethod
    def otp(cls, to: str, otp_code: str) -> EmailMessage:
        """Return a one-time-password email addressed to *to*.

        Args:
            to: Recipient e-mail address.
            otp_code: The plaintext 6-digit OTP that the user must enter.
        """
        return EmailMessage(
            to=to,
            subject="Your one-time login code",
            body=(
                f"Hello,\n\n"
                f"Your one-time login code is: {otp_code}\n\n"
                f"The code is valid for 15 minutes and can only be used once.\n"
                f"If you did not request this code, you can safely ignore this email.\n\n"
                f"Regards,\nStudent Projects Catalogue"
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
        return EmailMessage(
            to=to,
            subject=f'You have been invited to project "{project_name}"',
            body=(
                f"Hello,\n\n"
                f'You have been invited to join the project "{project_name}" '
                f'in the course "{course_name}".\n\n'
                f"Please log in to the Student Projects Catalogue to accept or decline.\n\n"
                f"Regards,\nStudent Projects Catalogue"
            ),
        )

    @classmethod
    def course_invite(cls, to: str, course_name: str) -> EmailMessage:
        """Return a course-invitation email addressed to *to*.

        Args:
            to: Recipient e-mail address.
            course_name: Human-readable name of the course the user is invited to.
        """
        return EmailMessage(
            to=to,
            subject=f'You have been invited to course "{course_name}"',
            body=(
                f"Hello,\n\n"
                f'You have been invited to participate in the course "{course_name}" '
                f"in the Student Projects Catalogue.\n\n"
                f"Please log in to review the course details and confirm your participation.\n\n"
                f"Regards,\nStudent Projects Catalogue"
            ),
        )

    @classmethod
    def results_unlocked(cls, to: str, project_name: str) -> EmailMessage:
        """Return a results-unlocked notification email addressed to *to*.

        This email is sent when evaluation results for a project become visible
        to its members.

        Args:
            to: Recipient e-mail address.
            project_name: Human-readable name of the project whose results are now visible.
        """
        return EmailMessage(
            to=to,
            subject=f'Results are now available for "{project_name}"',
            body=(
                f"Hello,\n\n"
                f'The evaluation results for your project "{project_name}" '
                f"have been published and are now available in the Student Projects Catalogue.\n\n"
                f"Log in to view your results.\n\n"
                f"Regards,\nStudent Projects Catalogue"
            ),
        )


# ---------------------------------------------------------------------------
# Sender (fake / dev implementation)
# ---------------------------------------------------------------------------


class EmailSender:
    """Fake email sender that writes messages to *stderr* instead of SMTP.

    This implementation is intentionally simplified — it exists as a stand-in
    until a real SMTP (or transactional email) integration is added.  Callers
    should depend on this class through its :meth:`send` interface so that
    swapping in a real implementation later requires no changes to call-sites.

    .. warning::
        This class must **not** be used in production.  It prints the full
        email body, including any secrets (such as OTP codes), to stderr.
    """

    def send(self, message: EmailMessage) -> None:
        """Print *message* to *stderr* as a formatted block.

        The output format is intentionally human-readable so that developers
        can quickly inspect emails during local development.

        Args:
            message: The email to "send".
        """
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
