from __future__ import annotations

from unittest.mock import MagicMock, patch

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
# EmailSender — non-local, ACS not configured
# ---------------------------------------------------------------------------


def test_email_sender_raises_when_acs_not_configured_in_non_local_env() -> None:
    """Non-local EmailSender with no ACS config must raise EmailDeliveryError."""
    msg = EmailMessage(to="user@tul.cz", subject="Test", body="Hello")
    with pytest.raises(EmailDeliveryError):
        EmailSender(app_env="production").send(msg)


def test_email_sender_raises_when_acs_not_configured_in_dev_env() -> None:
    """EmailSender must raise EmailDeliveryError in the 'dev' environment without ACS config."""
    msg = EmailMessage(to="user@tul.cz", subject="Test", body="Hello")
    with pytest.raises(EmailDeliveryError):
        EmailSender(app_env="dev").send(msg)


def test_email_delivery_not_implemented_error_is_alias() -> None:
    """EmailDeliveryNotImplementedError must be the same class as EmailDeliveryError."""
    assert EmailDeliveryNotImplementedError is EmailDeliveryError


# ---------------------------------------------------------------------------
# EmailSender — non-local, ACS configured (happy path)
# ---------------------------------------------------------------------------


def test_email_sender_calls_acs_with_correct_payload() -> None:
    """EmailSender must call ACS begin_send with the correct message payload."""
    msg = EmailMessage(to="student@tul.cz", subject="Hello", body="Body text")

    mock_poller = MagicMock()
    mock_client = MagicMock()
    mock_client.begin_send.return_value = mock_poller

    with patch("services.email.EmailClient") as mock_email_client_cls:
        mock_email_client_cls.from_connection_string.return_value = mock_client
        EmailSender(
            app_env="dev",
            acs_connection_string="endpoint=https://example.communication.azure.com/;accesskey=abc123==",
            acs_from_address="DoNotReply@example.azurecomm.net",
        ).send(msg)

    mock_email_client_cls.from_connection_string.assert_called_once_with(
        "endpoint=https://example.communication.azure.com/;accesskey=abc123=="
    )
    call_payload = mock_client.begin_send.call_args[0][0]
    assert call_payload["senderAddress"] == "DoNotReply@example.azurecomm.net"
    assert call_payload["recipients"]["to"][0]["address"] == "student@tul.cz"
    assert call_payload["content"]["subject"] == "Hello"
    assert call_payload["content"]["plainText"] == "Body text"
    mock_poller.result.assert_called_once()


def test_email_sender_acs_exception_propagates() -> None:
    """Exceptions from the ACS SDK must propagate out of EmailSender.send."""
    msg = EmailMessage(to="student@tul.cz", subject="Hello", body="Body text")

    mock_client = MagicMock()
    mock_client.begin_send.side_effect = RuntimeError("ACS unavailable")

    with patch("services.email.EmailClient") as mock_email_client_cls:
        mock_email_client_cls.from_connection_string.return_value = mock_client
        with pytest.raises(RuntimeError, match="ACS unavailable"):
            EmailSender(
                app_env="dev",
                acs_connection_string="endpoint=https://example.communication.azure.com/;accesskey=abc123==",
                acs_from_address="DoNotReply@example.azurecomm.net",
            ).send(msg)


# ---------------------------------------------------------------------------
# EmailSender.from_settings factory
# ---------------------------------------------------------------------------


def test_from_settings_constructs_sender_from_settings_object() -> None:
    """from_settings must read app_env, acs_connection_string, and acs_from_address."""
    mock_settings = MagicMock()
    mock_settings.app_env = "dev"
    mock_settings.acs_connection_string = "endpoint=https://x.communication.azure.com/;accesskey=k"
    mock_settings.acs_from_address = "DoNotReply@x.azurecomm.net"

    sender = EmailSender.from_settings(mock_settings)

    assert sender._app_env == "dev"
    assert sender._acs_connection_string == mock_settings.acs_connection_string
    assert sender._acs_from_address == mock_settings.acs_from_address
