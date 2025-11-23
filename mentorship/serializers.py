from django.contrib.auth import get_user_model
from rest_framework import serializers
from mentorship.models import Referral, Mentorship, RewardEvent

User = get_user_model()

class ReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = Referral
        fields = ["code", "is_active", "created_at"]

class MenteeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]

class MentorshipSerializer(serializers.ModelSerializer):
    mentor = serializers.PrimaryKeyRelatedField(read_only=True)
    mentee = MenteeSerializer(read_only=True)
    class Meta:
        model = Mentorship
        fields = ["mentor", "mentee", "date_joined"]

class AttachReferralInput(serializers.Serializer):
    referral_code = serializers.CharField(max_length=20)

class RewardEventSerializer(serializers.ModelSerializer):
    mentee = MenteeSerializer(read_only=True)
    class Meta:
        model = RewardEvent
        fields = ["event", "points", "created_at", "mentee"]
