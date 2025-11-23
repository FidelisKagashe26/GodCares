from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from mentorship.services.activation import try_activate_for_user

User = get_user_model()

class Command(BaseCommand):
    help = "Auto-activate referrals for users that now meet the policy criteria."

    def handle(self, *args, **options):
        count = 0
        for u in User.objects.iterator():
            if try_activate_for_user(u, reason="batch"):
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Activated {count} referral(s)."))
