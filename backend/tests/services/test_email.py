from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.email import (
    EmailDeliveryError,
    EmailDeliveryNotImplementedError,
    EmailMessage,
    EmailSender,
    EmailTemplate,
)

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
    msg = EmailTemplate.otp(
        to="user@tul.cz",
        otp_code="987654",
        portal_url="http://localhost:5173",
        recipient_name="Jan Novak",
    )
    assert msg.to == "user@tul.cz"
    assert "987654" in msg.body
    assert "Hello Jan Novak," in msg.body
    assert "catalogue" in msg.body.lower()
    assert "one-time" in msg.subject.lower()
    assert msg.subject.startswith("TUL Student Projects:")
    # Body should include a link to the portal.
    assert "http://localhost:5173" in msg.body


def test_otp_template_uses_generic_greeting_when_name_missing() -> None:
    """OTP template must keep the generic greeting when recipient name is not provided."""
    msg = EmailTemplate.otp(to="user@tul.cz", otp_code="987654", portal_url="http://localhost:5173")
    assert "Hello," in msg.body


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
        recipient_name="Alice Student",
    )
    assert msg.to == "student@tul.cz"
    assert "Hello Alice Student," in msg.body
    assert "Awesome App" in msg.body
    assert "PSI" in msg.body
    assert "next steps" in msg.body.lower()
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
        to="lecturer@tul.cz",
        course_name="PSI",
        portal_url="http://localhost:5173",
        recipient_name="Petr Lecturer",
    )
    assert msg.to == "lecturer@tul.cz"
    assert "Hello Petr Lecturer," in msg.body
    assert "PSI" in msg.body
    assert "PSI" in msg.subject
    assert msg.subject.startswith("TUL Student Projects:")
    # The invite is specifically for a lecturer role.
    assert "lecturer" in msg.body.lower()
    assert "fellow lecturers" in msg.body.lower()
    # Body should include a link to the portal.
    assert "http://localhost:5173" in msg.body


# ---------------------------------------------------------------------------
# EmailTemplate — results unlocked
# ---------------------------------------------------------------------------


def test_results_unlocked_template() -> None:
    """Results unlocked must address the recipient, mention project name, and have valid subject."""
    msg = EmailTemplate.results_unlocked(
        to="student@tul.cz",
        project_name="My Project",
        portal_url="http://localhost:5173",
        recipient_name="Jan Student",
    )
    assert msg.to == "student@tul.cz"
    assert "Hello Jan Student," in msg.body
    assert "My Project" in msg.body
    assert "My Project" in msg.subject
    assert "review the feedback" in msg.body.lower()
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


def test_user_invite_template() -> None:
    """User invite must include role, recipient details, and portal URL."""
    msg = EmailTemplate.user_invite(
        to="admin.new@tul.cz",
        role="admin",
        portal_url="http://localhost:5173",
        recipient_name="Eva Admin",
    )
    assert msg.to == "admin.new@tul.cz"
    assert "Hello Eva Admin," in msg.body
    assert "admin" in msg.body.lower()
    assert "complete your profile" in msg.body.lower()
    assert "http://localhost:5173" in msg.body


# ---------------------------------------------------------------------------
# EmailSender — local environment (auto backend)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_email_sender_local_outputs_to_stderr_and_not_stdout(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Local EmailSender must write to stderr, include all fields, and not touch stdout."""
    msg = EmailMessage(to="dev@tul.cz", subject="Test Subject", body="Test Body Content")
    await EmailSender(app_env="local").send(msg)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "dev@tul.cz" in captured.err
    assert "Test Subject" in captured.err
    assert "Test Body Content" in captured.err


# ---------------------------------------------------------------------------
# EmailSender — email_backend override
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_email_sender_smtp_backend_forces_real_delivery_in_local_env(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """EMAIL_BACKEND=smtp must bypass the console path even when app_env is 'local'."""
    msg = EmailMessage(to="dev@tul.cz", subject="Test", body="Body")
    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        await EmailSender(
            app_env="local",
            email_backend="smtp",
            smtp_host="mail.smtp2go.com",
            smtp_port=587,
            smtp_username="testuser",
            smtp_password="testpass",
            smtp_from_address="tul-projects@jezci.net",
        ).send(msg)
    mock_send.assert_awaited_once()
    # Nothing should have been printed to stderr.
    assert capsys.readouterr().err == ""


@pytest.mark.asyncio
async def test_email_sender_console_backend_forces_stderr_in_non_local_env(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """EMAIL_BACKEND=console must use the console path even when app_env is 'dev'."""
    msg = EmailMessage(to="dev@tul.cz", subject="Test", body="Body")
    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        await EmailSender(app_env="dev", email_backend="console").send(msg)
    mock_send.assert_not_awaited()
    assert "dev@tul.cz" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# EmailSender — non-local, SMTP not configured
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_email_sender_raises_when_smtp_not_configured_in_production() -> None:
    """Non-local EmailSender with no SMTP config must raise EmailDeliveryError."""
    msg = EmailMessage(to="user@tul.cz", subject="Test", body="Hello")
    with pytest.raises(EmailDeliveryError):
        await EmailSender(app_env="production").send(msg)


@pytest.mark.asyncio
async def test_email_sender_raises_when_smtp_not_configured_in_dev() -> None:
    """EmailSender must raise EmailDeliveryError in the 'dev' environment without SMTP config."""
    msg = EmailMessage(to="user@tul.cz", subject="Test", body="Hello")
    with pytest.raises(EmailDeliveryError):
        await EmailSender(app_env="dev").send(msg)


def test_email_delivery_not_implemented_error_is_alias() -> None:
    """EmailDeliveryNotImplementedError must be the same class as EmailDeliveryError."""
    assert EmailDeliveryNotImplementedError is EmailDeliveryError


# ---------------------------------------------------------------------------
# EmailSender — non-local, SMTP configured (happy path)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_email_sender_calls_aiosmtplib_with_correct_params() -> None:
    """EmailSender must call aiosmtplib.send with the correct connection params and message."""
    msg = EmailMessage(to="student@tul.cz", subject="Hello", body="Body text")

    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        await EmailSender(
            app_env="dev",
            smtp_host="mail.smtp2go.com",
            smtp_port=587,
            smtp_username="testuser",
            smtp_password="testpass",
            smtp_from_address="tul-projects@jezci.net",
        ).send(msg)

    mock_send.assert_awaited_once()
    _mime_msg, kwargs = mock_send.call_args[0][0], mock_send.call_args[1]
    assert kwargs["hostname"] == "mail.smtp2go.com"
    assert kwargs["port"] == 587
    assert kwargs["username"] == "testuser"
    assert kwargs["password"] == "testpass"
    assert kwargs["start_tls"] is True
    # Verify the MIME message headers.
    assert _mime_msg["To"] == "student@tul.cz"
    assert _mime_msg["Subject"] == "Hello"
    assert "tul-projects@jezci.net" in _mime_msg["From"]


@pytest.mark.asyncio
async def test_email_sender_smtp_exception_propagates() -> None:
    """Exceptions from aiosmtplib must propagate out of EmailSender.send."""
    import aiosmtplib

    msg = EmailMessage(to="student@tul.cz", subject="Hello", body="Body text")

    with patch("aiosmtplib.send", side_effect=aiosmtplib.SMTPException("relay unavailable")):
        with pytest.raises(aiosmtplib.SMTPException, match="relay unavailable"):
            await EmailSender(
                app_env="dev",
                smtp_host="mail.smtp2go.com",
                smtp_port=587,
                smtp_username="testuser",
                smtp_password="testpass",
                smtp_from_address="tul-projects@jezci.net",
            ).send(msg)


# ---------------------------------------------------------------------------
# EmailSender.from_settings factory
# ---------------------------------------------------------------------------


def test_from_settings_constructs_sender_from_settings_object() -> None:
    """from_settings must read app_env, email_backend, and all five SMTP fields from settings."""
    mock_settings = MagicMock()
    mock_settings.app_env = "dev"
    mock_settings.email_backend = "auto"
    mock_settings.smtp_host = "mail.smtp2go.com"
    mock_settings.smtp_port = 587
    mock_settings.smtp_username = "testuser"
    mock_settings.smtp_password = "testpass"
    mock_settings.smtp_from_address = "tul-projects@jezci.net"

    sender = EmailSender.from_settings(mock_settings)

    assert sender._app_env == "dev"
    assert sender._email_backend == mock_settings.email_backend
    assert sender._smtp_host == mock_settings.smtp_host
    assert sender._smtp_port == mock_settings.smtp_port
    assert sender._smtp_username == mock_settings.smtp_username
    assert sender._smtp_password == mock_settings.smtp_password
    assert sender._smtp_from_address == mock_settings.smtp_from_address
