from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from mentorship.models import Referral

User = get_user_model()

class Command(BaseCommand):
    help = "Create Referral for users who don't have one (inactive by default)."

    def handle(self, *args, **opts):
        created = 0
        for u in User.objects.filter(referral__isnull=True).iterator():
            code = Referral.generate_code()
            while Referral.objects.filter(code=code).exists():
                code = Referral.generate_code()
            Referral.objects.create(mentor=u, code=code, is_active=False)
            created += 1
        self.stdout.write(self.style.SUCCESS(f"Created {created} referral(s)."))
