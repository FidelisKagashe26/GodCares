from django.contrib import admin
from django.utils import timezone
from django.db.models import Count, Sum
from mentorship.models import Referral, Mentorship, RewardEvent


@admin.action(description="Activate selected referrals")
def activate_referrals(modeladmin, request, queryset):
    updated = queryset.update(
        is_active=True,
        activation_method="manual",
        activated_at=timezone.now(),
    )
    modeladmin.message_user(request, f"{updated} referral(s) activated.")


@admin.action(description="Deactivate selected referrals")
def deactivate_referrals(modeladmin, request, queryset):
    updated = queryset.update(
        is_active=False,
        activation_method=None,
        activated_at=None,
    )
    modeladmin.message_user(request, f"{updated} referral(s) deactivated.")


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = (
        "mentor",
        "code",
        "is_active",
        "activation_method",
        "activated_at",
        "created_at",
        "mentees_count",
        "total_points",
    )
    search_fields = ("code", "mentor__username", "mentor__email")
    list_filter = ("is_active", "activation_method", "created_at")
    readonly_fields = ("code", "created_at", "activated_at")
    actions = [activate_referrals, deactivate_referrals]
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # annotate ili kuepuka N+1 kwenye hesabu
        return qs.annotate(
            _mentees_count=Count("mentor__my_mentees", distinct=True),
            _total_points=Sum("mentor__reward_events__points"),
        )

    @admin.display(ordering="_mentees_count", description="Mentees")
    def mentees_count(self, obj):
        return obj._mentees_count or 0

    @admin.display(ordering="_total_points", description="Total Points")
    def total_points(self, obj):
        return obj._total_points or 0


# --- Admin action: Award Baptism points kwa batch ---
@admin.action(description="Award Baptism points to selected mentees")
def award_baptism(modeladmin, request, queryset):
    count = 0
    for ms in queryset.select_related("mentor", "mentee"):
        obj, created = RewardEvent.objects.get_or_create(
            mentor=ms.mentor,
            mentee=ms.mentee,
            event="baptism",
            defaults={"points": 50},
        )
        if created:
            count += 1
    modeladmin.message_user(request, f"Awarded baptism points to {count} mentee(s).")


@admin.register(Mentorship)
class MentorshipAdmin(admin.ModelAdmin):
    list_display = ("mentor", "mentee", "date_joined")
    search_fields = ("mentor__username", "mentor__email", "mentee__username", "mentee__email")
    list_filter = ("date_joined",)
    date_hierarchy = "date_joined"
    actions = [award_baptism]


@admin.register(RewardEvent)
class RewardEventAdmin(admin.ModelAdmin):
    list_display = ("mentor", "mentee", "event", "points", "created_at")
    list_filter = ("event", "created_at")
    search_fields = ("mentor__username", "mentor__email", "mentee__username", "mentee__email")
    date_hierarchy = "created_at"
