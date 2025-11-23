from django.urls import path
from mentorship.views import (
    MyReferralView, attach_referral_view, MyMenteesView, LeaderboardView, referral_redirect
)

app_name = "mentorship"

urlpatterns = [
    path("me/referral/", MyReferralView.as_view(), name="my_referral"),
    path("attach/", attach_referral_view, name="attach_referral"),
    path("me/mentees/", MyMenteesView.as_view(), name="my_mentees"),
    path("leaderboard/", LeaderboardView.as_view(), name="leaderboard"),
    path("r/<str:code>/", referral_redirect, name="ref_redirect"),  # short-link
]
