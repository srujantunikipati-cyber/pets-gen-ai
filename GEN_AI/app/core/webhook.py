"""Webhook signature validation utilities."""

import hashlib
import hmac
from typing import Optional


def verify_webhook_signature(
    *,
    payload: bytes,
    signature: str,
    secret: str,
    algorithm: str = "sha256",
) -> bool:
    """Verify HMAC signature for incoming webhook payloads.

    Args:
        payload: Raw webhook body bytes
        signature: Signature from the webhook provider (typically a hex digest)
        secret: Shared secret for signature generation
        algorithm: HMAC algorithm name (default: sha256)

    Returns:
        True if signature is valid, False otherwise

    Example:
        >>> body = b'{"job_id": "123", "status": "completed"}'
        >>> sig = "abc123..."
        >>> verify_webhook_signature(payload=body, signature=sig, secret="my-secret")
        True
    """
    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        getattr(hashlib, algorithm),
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def extract_signature_from_header(header_value: Optional[str], prefix: str = "sha256=") -> Optional[str]:
    """Extract signature hash from an HTTP header value.

    Args:
        header_value: Raw header string, e.g., "sha256=abc123..."
        prefix: Prefix to strip (default: "sha256=")

    Returns:
        Extracted signature or None if header is missing/malformed
    """
    if not header_value:
        return None
    if header_value.startswith(prefix):
        return header_value[len(prefix):]
    return header_value
