from __future__ import annotations

import pytest

from services.email import EmailMessage, EmailSender, EmailTemplate

# ---------------------------------------------------------------------------
# EmailMessage
# ---------------------------------------------------------------------------


def test_email_message_fields_and_immutability() -> None:
    """EmailMessage must expose its fields and reject mutation (frozen dataclass)."""
    msg = EmailMessage(to="a@tul.cz", subject="Hi", body="Hello")
    assert msg.to == "a@tul.cz"
    assert msg.subject == "Hi"
    assert msg.body == "Hello"
    with pytest.raises(AttributeError):
        msg.to = "other@tul.cz"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# EmailTemplate — OTP
# ---------------------------------------------------------------------------


def test_otp_template() -> None:
    """OTP template must address the recipient, embed the code, and reference OTP in subject."""
    msg = EmailTemplate.otp(to="user@tul.cz", otp_code="987654", portal_url="http://localhost:5173")
    assert msg.to == "user@tul.cz"
    assert "987654" in msg.body
    assert "one-time" in msg.subject.lower()
    assert msg.subject.startswith("TUL Student Projects:")
    # Body should include a link to the portal.
    assert "http://localhost:5173" in msg.body


# ---------------------------------------------------------------------------
# EmailTemplate — project invite
# ---------------------------------------------------------------------------


def test_project_invite_template() -> None:
    """Project invite must address the recipient, mention project/course, and have valid subject."""
    msg = EmailTemplate.project_invite(
        to="student@tul.cz",
        project_name="Awesome App",
        course_name="PSI",
        portal_url="http://localhost:5173",
    )
    assert msg.to == "student@tul.cz"
    assert "Awesome App" in msg.body
    assert "PSI" in msg.body
    assert "Awesome App" in msg.subject
    assert msg.subject.startswith("TUL Student Projects:")
    # Body should include a link to the portal.
    assert "http://localhost:5173" in msg.body


# ---------------------------------------------------------------------------
# EmailTemplate — course invite
# ---------------------------------------------------------------------------


def test_course_invite_template() -> None:
    """Course invite must address a lecturer, mention the course, and have a valid subject."""
    msg = EmailTemplate.course_invite(
        to="lecturer@tul.cz", course_name="PSI", portal_url="http://localhost:5173"
    )
    assert msg.to == "lecturer@tul.cz"
    assert "PSI" in msg.body
    assert "PSI" in msg.subject
    assert msg.subject.startswith("TUL Student Projects:")
    # The invite is specifically for a lecturer role.
    assert "lecturer" in msg.body.lower()
    # Body should include a link to the portal.
    assert "http://localhost:5173" in msg.body


# ---------------------------------------------------------------------------
# EmailTemplate — results unlocked
# ---------------------------------------------------------------------------


def test_results_unlocked_template() -> None:
    """Results unlocked must address the recipient, mention project name, and have valid subject."""
    msg = EmailTemplate.results_unlocked(
        to="student@tul.cz", project_name="My Project", portal_url="http://localhost:5173"
    )
    assert msg.to == "student@tul.cz"
    assert "My Project" in msg.body
    assert "My Project" in msg.subject
    assert msg.subject.startswith("TUL Student Projects:")
    # Body should include a link to the portal.
    assert "http://localhost:5173" in msg.body


def test_results_unlocked_template_peer_feedback_mentioned_when_enabled() -> None:
    """EmailTemplate.results_unlocked body must mention peer feedback when the flag is True."""
    msg_with = EmailTemplate.results_unlocked(
        to="student@tul.cz",
        project_name="My Project",
        portal_url="http://localhost:5173",
        peer_feedback_enabled=True,
    )
    msg_without = EmailTemplate.results_unlocked(
        to="student@tul.cz",
        project_name="My Project",
        portal_url="http://localhost:5173",
        peer_feedback_enabled=False,
    )
    assert "peer feedback" in msg_with.body.lower()
    assert "peer feedback" not in msg_without.body.lower()


# ---------------------------------------------------------------------------
# EmailSender — local environment
# ---------------------------------------------------------------------------


def test_email_sender_local_outputs_to_stderr_and_not_stdout(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Local EmailSender must write to stderr, include all fields, and not touch stdout."""
    msg = EmailMessage(to="dev@tul.cz", subject="Test Subject", body="Test Body Content")
    EmailSender(app_env="local").send(msg)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "dev@tul.cz" in captured.err
    assert "Test Subject" in captured.err
    assert "Test Body Content" in captured.err


# ---------------------------------------------------------------------------
# EmailSender — non-local environment
# ---------------------------------------------------------------------------


def test_email_sender_raises_in_non_local_env(capsys: pytest.CaptureFixture[str]) -> None:
    """Non-local EmailSender must raise NotImplementedError and produce no output."""
    msg = EmailMessage(to="user@tul.cz", subject="Test", body="Hello")
    with pytest.raises(NotImplementedError):
        EmailSender(app_env="production").send(msg)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_email_sender_raises_in_dev_env() -> None:
    """EmailSender must also raise NotImplementedError in the 'dev' environment."""
    msg = EmailMessage(to="user@tul.cz", subject="Test", body="Hello")
    with pytest.raises(NotImplementedError):
        EmailSender(app_env="dev").send(msg)
