"""Fernet encryption/decryption for GitHub access tokens."""

from cryptography.fernet import Fernet, InvalidToken
from app.config import get_settings

settings = get_settings()


def _get_fernet() -> Fernet:
    key = settings.FERNET_KEY
    if not key:
        raise ValueError("FERNET_KEY is not set. Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'")
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_token(token: str) -> str:
    """Encrypt a GitHub access token."""
    f = _get_fernet()
    return f.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a GitHub access token."""
    f = _get_fernet()
    try:
        return f.decrypt(encrypted_token.encode()).decode()
    except InvalidToken:
        raise ValueError("Failed to decrypt token — invalid or corrupted.")
