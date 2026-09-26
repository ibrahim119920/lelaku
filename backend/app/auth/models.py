"""Compatibility exports; auth ORM definitions live in the shared model registry."""

from backend.app.models import DriverProfile, User, UserSession, Vehicle

__all__ = ["DriverProfile", "User", "UserSession", "Vehicle"]
