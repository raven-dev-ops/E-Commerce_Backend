from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = "Remove expired email verification tokens for unverified users."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=1,
            help="Tokens older than this number of days will be removed.",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        expiration_days = options["days"]
        cutoff = timezone.now() - timedelta(days=expiration_days)
        qs = User.objects.filter(
            email_verified=False,
            verification_token__isnull=False,
            date_joined__lt=cutoff,
        )
        count = qs.update(verification_token=None)
        self.stdout.write(
            self.style.SUCCESS(f"Removed {count} expired verification tokens.")
        )
