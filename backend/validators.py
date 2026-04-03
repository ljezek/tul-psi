from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.user import User

_TUL_DOMAIN = "tul.cz"


def validate_tul_email(v: str) -> str:
    """Normalise and validate that *v* is a @tul.cz e-mail address.

    Strips whitespace and lowercases the address so that subsequent
    case-sensitive DB lookups behave consistently.  Raises ``ValueError``
    (which Pydantic converts to a 422 response) for any non-@tul.cz address
    or any value that does not contain an ``@`` sign.
    """
    v = v.strip().lower()
    if "@" not in v:
        raise ValueError("E-mail address must contain an @ symbol.")
    domain = v.split("@", 1)[-1]
    if domain != _TUL_DOMAIN:
        raise ValueError(f"Only @{_TUL_DOMAIN} email addresses are accepted.")
    return v


def require_user_id(user: User) -> int:
    """Return ``user.id``, raising ``ValueError`` if it is ``None``.

    ``User.id`` is typed as ``int | None`` because SQLModel allows unsaved instances,
    but any row returned from the database always has a non-None primary key.
    This helper surfaces the inconsistency early with a clear message rather than
    letting it propagate as a silent ``None``.
    """
    if user.id is None:
        raise ValueError(f"User returned from DB has no id: {user!r}")
    return user.id


def derive_display_name(email: str) -> str:
    """Derive a human-readable display name from the local part of *email*.

    Dots and underscores are treated as word separators and each word is
    title-cased (e.g. ``jan.novak@tul.cz`` → ``"Jan Novak"``).
    """
    prefix = email.split("@")[0]
    return " ".join(part.capitalize() for part in prefix.replace("_", ".").split("."))
