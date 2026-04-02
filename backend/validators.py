from __future__ import annotations

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
