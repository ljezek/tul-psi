from __future__ import annotations

from io import StringIO
from unittest.mock import patch

import pytest

from services.email import EmailMessage, EmailSender, EmailTemplate

# ---------------------------------------------------------------------------
# EmailMessage
# ---------------------------------------------------------------------------


def test_email_message_fields() -> None:
    """EmailMessage must expose the three fields it was constructed with."""
    msg = EmailMessage(to="a@tul.cz", subject="Hi", body="Hello")
    assert msg.to == "a@tul.cz"
    assert msg.subject == "Hi"
    assert msg.body == "Hello"


def test_email_message_is_immutable() -> None:
    """EmailMessage must be frozen; attribute assignment must raise AttributeError."""
    msg = EmailMessage(to="a@tul.cz", subject="Hi", body="Hello")
    with pytest.raises(AttributeError):
        msg.to = "other@tul.cz"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# EmailTemplate — OTP
# ---------------------------------------------------------------------------


def test_otp_template_addressing() -> None:
    """EmailTemplate.otp must set the ``to`` field to the supplied recipient."""
    msg = EmailTemplate.otp(to="user@tul.cz", otp_code="123456")
    assert msg.to == "user@tul.cz"


def test_otp_template_contains_code() -> None:
    """EmailTemplate.otp body must contain the OTP code."""
    msg = EmailTemplate.otp(to="user@tul.cz", otp_code="987654")
    assert "987654" in msg.body


def test_otp_template_has_subject() -> None:
    """EmailTemplate.otp must produce a non-empty subject line."""
    msg = EmailTemplate.otp(to="user@tul.cz", otp_code="000000")
    assert msg.subject


# ---------------------------------------------------------------------------
# EmailTemplate — project invite
# ---------------------------------------------------------------------------


def test_project_invite_addressing() -> None:
    """EmailTemplate.project_invite must set the ``to`` field correctly."""
    msg = EmailTemplate.project_invite(
        to="student@tul.cz", project_name="My Project", course_name="PSI"
    )
    assert msg.to == "student@tul.cz"


def test_project_invite_contains_names() -> None:
    """EmailTemplate.project_invite body must mention both project and course names."""
    msg = EmailTemplate.project_invite(
        to="student@tul.cz", project_name="My Project", course_name="PSI"
    )
    assert "My Project" in msg.body
    assert "PSI" in msg.body


def test_project_invite_subject_contains_project_name() -> None:
    """EmailTemplate.project_invite subject must reference the project name."""
    msg = EmailTemplate.project_invite(
        to="student@tul.cz", project_name="Awesome App", course_name="PSI"
    )
    assert "Awesome App" in msg.subject


# ---------------------------------------------------------------------------
# EmailTemplate — course invite
# ---------------------------------------------------------------------------


def test_course_invite_addressing() -> None:
    """EmailTemplate.course_invite must set the ``to`` field correctly."""
    msg = EmailTemplate.course_invite(to="student@tul.cz", course_name="PSI")
    assert msg.to == "student@tul.cz"


def test_course_invite_contains_course_name() -> None:
    """EmailTemplate.course_invite body must mention the course name."""
    msg = EmailTemplate.course_invite(to="student@tul.cz", course_name="PSI")
    assert "PSI" in msg.body


def test_course_invite_subject_contains_course_name() -> None:
    """EmailTemplate.course_invite subject must reference the course name."""
    msg = EmailTemplate.course_invite(to="student@tul.cz", course_name="PSI")
    assert "PSI" in msg.subject


# ---------------------------------------------------------------------------
# EmailTemplate — results unlocked
# ---------------------------------------------------------------------------


def test_results_unlocked_addressing() -> None:
    """EmailTemplate.results_unlocked must set the ``to`` field correctly."""
    msg = EmailTemplate.results_unlocked(to="student@tul.cz", project_name="My Project")
    assert msg.to == "student@tul.cz"


def test_results_unlocked_contains_project_name() -> None:
    """EmailTemplate.results_unlocked body must mention the project name."""
    msg = EmailTemplate.results_unlocked(to="student@tul.cz", project_name="My Project")
    assert "My Project" in msg.body


def test_results_unlocked_subject_contains_project_name() -> None:
    """EmailTemplate.results_unlocked subject must reference the project name."""
    msg = EmailTemplate.results_unlocked(to="student@tul.cz", project_name="My Project")
    assert "My Project" in msg.subject


# ---------------------------------------------------------------------------
# EmailSender
# ---------------------------------------------------------------------------


def test_email_sender_writes_to_stderr() -> None:
    """EmailSender.send must write output to stderr, not stdout."""
    msg = EmailMessage(to="dev@tul.cz", subject="Test", body="Hello from test")
    buf = StringIO()
    with patch("sys.stderr", buf):
        EmailSender().send(msg)
    output = buf.getvalue()
    assert output  # Something was written.


def test_email_sender_output_contains_fields() -> None:
    """EmailSender.send output must include the recipient, subject, and body."""
    msg = EmailMessage(to="dev@tul.cz", subject="Test Subject", body="Test Body Content")
    buf = StringIO()
    with patch("sys.stderr", buf):
        EmailSender().send(msg)
    output = buf.getvalue()
    assert "dev@tul.cz" in output
    assert "Test Subject" in output
    assert "Test Body Content" in output


def test_email_sender_does_not_write_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    """EmailSender.send must write to stderr and nothing to stdout."""
    msg = EmailMessage(to="dev@tul.cz", subject="Test", body="Hello")
    EmailSender().send(msg)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err != ""
