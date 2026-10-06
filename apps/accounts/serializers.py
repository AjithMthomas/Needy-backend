"""Member serializers.

Two projections: ``MemberSelfSerializer`` (everything the owner sees)
and ``MemberPublicSerializer`` (what other members see — no email, no
safety contact, no DOB).
"""

from rest_framework import serializers

from apps.accounts.models import Member


class MemberPublicSerializer(serializers.ModelSerializer):
    badges = serializers.SerializerMethodField()
    is_established = serializers.BooleanField(read_only=True)
    reliability_percent = serializers.IntegerField(read_only=True)

    class Meta:
        model = Member
        fields = [
            "id",
            "public_name",
            "photo_url",
            "gender",
            "bio",
            "completed_count",
            "rating",
            "rating_count",
            "cancellations",
            "no_shows",
            "verified_badge",
            "is_established",
            "joined_at",
            "categories",
            "availability_hours",
            "karma",
            "is_guardian",
            "available_now",
            "badges",
            "reliability_percent",
        ]

    def get_badges(self, obj) -> list[str]:
        return obj.badge_codes


class MemberSelfSerializer(MemberPublicSerializer):
    class Meta(MemberPublicSerializer.Meta):
        fields = [
            *MemberPublicSerializer.Meta.fields,
            "email",
            "is_email_verified",
            "date_of_birth",
            "age_gate_passed",
            "safety_contact_name",
            "safety_contact_phone",
            "profile_completed",
        ]

    def validate_date_of_birth(self, value):
        if value is not None:
            from datetime import date

            today = date.today()
            age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
            if age < 18:
                raise serializers.ValidationError("Members must be 18 or older.")
        return value


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """PATCH /me — display-layer fields only; trust stats are server-owned."""

    class Meta:
        model = Member
        fields = [
            "public_name",
            "photo_url",
            "bio",
            "gender",
            "categories",
            "availability_hours",
            "safety_contact_name",
            "safety_contact_phone",
            "date_of_birth",
        ]

    def validate_date_of_birth(self, value):
        if value is not None:
            from datetime import date

            today = date.today()
            age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
            if age < 18:
                raise serializers.ValidationError("Members must be 18 or older.")
        return value


class SignupProfileSerializer(serializers.Serializer):
    """POST /me/complete-profile — the onboarding step after OTP verify."""

    name = serializers.CharField(min_length=2, max_length=60)
    gender = serializers.ChoiceField(choices=Member.Gender.choices)
    bio = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
    categories = serializers.ListField(
        child=serializers.CharField(max_length=40),
        required=False,
        default=list,
    )
    photo_url = serializers.URLField(required=False, allow_blank=True, default="")

    def save(self, member: Member) -> Member:
        data = self.validated_data
        member.public_name = data["name"]
        member.gender = data["gender"]
        member.bio = data.get("bio", "")
        member.categories = data.get("categories", [])
        member.photo_url = data.get("photo_url", "") or member.photo_url
        member.age_gate_passed = True
        member.is_email_verified = True
        member.save()
        return member
