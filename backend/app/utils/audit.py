"""Audit logging for sensitive operations."""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("codelens.audit")


def log_auth_event(event: str, user_id: Optional[str] = None, details: Optional[dict] = None) -> None:
    """Log authentication-related events."""
    logger.info(
        "AUTH_EVENT | event=%s | user_id=%s | details=%s | ts=%s",
        event,
        user_id or "anonymous",
        details or {},
        datetime.now(timezone.utc).isoformat(),
    )


def log_repo_access(user_id: str, repo_id: str, action: str) -> None:
    """Log repository access events."""
    logger.info(
        "REPO_ACCESS | user_id=%s | repo_id=%s | action=%s | ts=%s",
        user_id,
        repo_id,
        action,
        datetime.now(timezone.utc).isoformat(),
    )


def log_security_event(event: str, details: Optional[dict] = None) -> None:
    """Log security-related events (rate limits, injection attempts, etc.)."""
    logger.warning(
        "SECURITY_EVENT | event=%s | details=%s | ts=%s",
        event,
        details or {},
        datetime.now(timezone.utc).isoformat(),
    )
