"""Prune expired privacy-preserving login and invitation throttle state."""

from django.core.management.base import BaseCommand

from apps.accounts.services import purge_expired_throttle_state


class Command(BaseCommand):
    """Remove throttle fingerprints that have exceeded their short retention period."""

    help = "Delete expired login and invitation throttle fingerprints."

    def handle(self, *args: object, **options: object) -> None:
        deleted = purge_expired_throttle_state()
        self.stdout.write(f"Removed {deleted} expired throttle fingerprints.")
