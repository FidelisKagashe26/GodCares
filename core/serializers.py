# core/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from .models import UserActivity, SystemSetting
from content.models import Profile


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer ya profile + user fields pamoja (for /api/user/profile/me/).
    """

    email = serializers.EmailField(source="user.email")
    first_name = serializers.CharField(
        source="user.first_name", required=False, allow_blank=True
    )
    last_name = serializers.CharField(
        source="user.last_name", required=False, allow_blank=True
    )
    username = serializers.CharField(source="user.username", read_only=True)
    date_joined = serializers.DateTimeField(source="user.date_joined", read_only=True)
    # Tunatumia last_login kama last_active ya sasa
    last_active = serializers.DateTimeField(
        source="user.last_login", read_only=True
    )

    class Meta:
        model = Profile
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "email_verified",
            "receive_notifications",
            "last_active",
            "date_joined",
            "created_at",
        ]
        read_only_fields = ["email_verified", "last_active", "created_at"]

    def update(self, instance, validated_data):
        # Update sehemu ya User
        user_data = validated_data.pop("user", {})
        user = instance.user

        for attr in ("email", "first_name", "last_name"):
            if attr in user_data:
                setattr(user, attr, user_data[attr])
        user.save()

        # Update sehemu ya Profile
        return super().update(instance, validated_data)


class UserActivitySerializer(serializers.ModelSerializer):
    """
    Activity log serializer.
    """

    user_username = serializers.CharField(source="user.username", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = UserActivity
        fields = "__all__"
        read_only_fields = ["created_at"]


class SystemSettingSerializer(serializers.ModelSerializer):
    """
    System settings serializer.
    """

    class Meta:
        model = SystemSetting
        fields = "__all__"
        read_only_fields = ["created_at"]


class DashboardStatsSerializer(serializers.Serializer):
    """
    Simple wrapper serializer kwa dashboard summary.
    """

    user_stats = serializers.DictField()
    global_stats = serializers.DictField()
    recent_missions = serializers.ListField()
    journey = serializers.DictField(allow_null=True)


class MissionProgressStatsSerializer(serializers.Serializer):
    """
    Stats za MissionProgressAPIView (monthly & yearly).
    """

    monthly = serializers.DictField()
    yearly = serializers.DictField()


class TrackActivityRequestSerializer(serializers.Serializer):
    """
    Payload ya track_activity endpoint.
    """

    activity_type = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.DictField(required=False)


class SimpleMessageSerializer(serializers.Serializer):
    """
    Response rahisi kwa endpoints kama track_activity.
    """

    status = serializers.CharField(required=False)
    error = serializers.CharField(required=False)


class SiteSearchResponseSerializer(serializers.Serializer):
    """
    Response ya site_search: tunaweka generic Dict kwa results
    ili kuepuka circular imports.
    """

    query = serializers.CharField()
    results = serializers.DictField()
    total_results = serializers.IntegerField()


class PasswordChangeSerializer(serializers.Serializer):
    """
    Password change serializer (tuta-tumia baadaye kwenye auth endpoints).
    """

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("New passwords don't match")

        validate_password(attrs["new_password"])
        return attrs


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    User registration serializer (kwa siku tutakapo-fungua registration).
    """

    password = serializers.CharField(
        write_only=True, validators=[validate_password]
    )
    confirm_password = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(
        required=False, allow_blank=True
    )
    accept_terms = serializers.BooleanField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "confirm_password",
            "phone_number",
            "accept_terms",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords don't match")

        if not attrs.get("accept_terms"):
            raise serializers.ValidationError(
                "You must accept the terms and conditions"
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        phone_number = validated_data.pop("phone_number", "")
        validated_data.pop("accept_terms", None)

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            is_active=False,  
        )

        Profile.objects.create(user=user, phone_number=phone_number)

        return user
