"""Authentication module."""

import hashlib
import os
from typing import Optional


def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Hash a password with salt."""
    if salt is None:
        salt = os.urandom(16).hex()
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    salt, stored = hashed.split(":", 1)
    computed = hash_password(password, salt)
    return computed.split(":")[1] == stored


class User:
    """User model."""

    def __init__(self, username: str, email: str):
        self.username = username
        self.email = email
        self._password_hash = None

    def set_password(self, password: str) -> None:
        self._password_hash = hash_password(password)

    def check_password(self, password: str) -> bool:
        return verify_password(password, self._password_hash)


class AdminUser(User):
    """Admin user with elevated privileges."""

    role = "admin"

    def __init__(self, username: str, email: str):
        super().__init__(username, email)
        self.permissions = ["read", "write", "delete"]
