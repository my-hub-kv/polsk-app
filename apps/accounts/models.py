"""Credential, invitation, and login-protection models."""

from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractUser, UserManager
from django.core.validators import validate_email
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower


class PolskUserManager(UserManager):
    """Create users with canonical username and optional email values."""

    @staticmethod
    def normalize_username_value(username: str) -> str:
        return username.strip().casefold()

    @staticmethod
    def normalize_email_value(email: str | None) -> str | None:
        if not email:
            return None
        return email.strip().casefold()

    @classmethod
    def normalize_email(cls, email: str | None) -> str | None:
        """Preserve a missing email as NULL for the conditional uniqueness rule."""
        return cls.normalize_email_value(email)

    def _create_user(
        self,
        username: str,
        email: str | None,
        password: str | None,
        **extra_fields: object,
    ) -> "User":
        return super()._create_user(
            self.normalize_username_value(username),
            self.normalize_email_value(email),
            password,
            **extra_fields,
        )


class User(AbstractUser):
    """Login account, deliberately distinct from a participant profile."""

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField(blank=True, null=True, validators=[validate_email])

    objects = PolskUserManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("username"), name="accounts_user_username_ci_unique"
            ),
            models.UniqueConstraint(
                Lower("email"),
                condition=Q(email__isnull=False),
                name="accounts_user_email_ci_unique_when_present",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.username = PolskUserManager.normalize_username_value(self.username)
        self.email = PolskUserManager.normalize_email_value(self.email)


class LoginThrottle(models.Model):
    """Short-lived, irreversible state for a login rate-limit key."""

    key_digest = models.CharField(max_length=64, unique=True)
    window_started_at = models.DateTimeField()
    failures = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)


class Invitation(models.Model):
    """Single-use credential setup or reset link stored only as a digest."""

    class Purpose(models.TextChoices):
        CREATE_ACCOUNT = "create_account", "Create account"
        RESET_CREDENTIALS = "reset_credentials", "Reset credentials"

    participation = models.ForeignKey(
        "people.EventParticipation",
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    token_digest = models.CharField(max_length=64, unique=True)
    purpose = models.CharField(max_length=32, choices=Purpose.choices)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["expires_at", "used_at", "revoked_at"])]


class InvitationThrottle(models.Model):
    """Short-lived, irreversible state for invitation redemption attempts."""

    key_digest = models.CharField(max_length=64, unique=True)
    window_started_at = models.DateTimeField()
    failures = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
