from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from models.user import User
from validators import derive_display_name, require_user_id, validate_tul_email

# ---------------------------------------------------------------------------
# validate_tul_email
# ---------------------------------------------------------------------------


def test_validate_tul_email_accepts_valid_tul_address() -> None:
    """A valid @tul.cz address must be returned normalised (lowercase, stripped)."""
    assert validate_tul_email("  Jan.Novak@TUL.cz ") == "jan.novak@tul.cz"


def test_validate_tul_email_rejects_non_tul_domain() -> None:
    """An address with a domain other than @tul.cz must raise ``ValueError``."""
    with pytest.raises(ValueError, match="@tul.cz"):
        validate_tul_email("student@gmail.com")


def test_validate_tul_email_rejects_subdomain() -> None:
    """A subdomain like @sub.tul.cz must not be accepted."""
    with pytest.raises(ValueError, match="@tul.cz"):
        validate_tul_email("user@sub.tul.cz")


def test_validate_tul_email_rejects_missing_at_sign() -> None:
    """A value without an @ sign must raise ``ValueError``."""
    with pytest.raises(ValueError, match="@"):
        validate_tul_email("not-an-email")


# ---------------------------------------------------------------------------
# require_user_id
# ---------------------------------------------------------------------------


def test_require_user_id_returns_id_when_present() -> None:
    """``require_user_id`` must return the user's id when it is not ``None``."""
    user = MagicMock(spec=User)
    user.id = 42
    assert require_user_id(user) == 42


def test_require_user_id_raises_when_id_is_none() -> None:
    """``require_user_id`` must raise ``ValueError`` when ``user.id`` is ``None``."""
    user = MagicMock(spec=User)
    user.id = None
    with pytest.raises(ValueError, match="no id"):
        require_user_id(user)


# ---------------------------------------------------------------------------
# derive_display_name
# ---------------------------------------------------------------------------


def test_derive_display_name_splits_on_dots() -> None:
    """Dots in the local part must be treated as word separators."""
    assert derive_display_name("jan.novak@tul.cz") == "Jan Novak"


def test_derive_display_name_splits_on_underscores() -> None:
    """Underscores in the local part must be treated as word separators."""
    assert derive_display_name("j_doe@tul.cz") == "J Doe"


def test_derive_display_name_handles_mixed_separators() -> None:
    """A mix of dots and underscores must all be treated as word separators."""
    assert derive_display_name("john_jacob.smith@tul.cz") == "John Jacob Smith"


def test_derive_display_name_single_word() -> None:
    """A local part with no separators must be capitalised as a single word."""
    assert derive_display_name("alice@tul.cz") == "Alice"
