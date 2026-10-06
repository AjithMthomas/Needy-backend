"""posts serializers."""

from django.utils import timezone
from rest_framework import serializers

from apps.posts.models import Application, Task


class CreatorCardSerializer(serializers.Serializer):
    """The creator card the UI renders (denormalised onto each Task row)."""

    id = serializers.UUIDField()
    public_name = serializers.CharField()
    photo_url = serializers.CharField()
    verified = serializers.BooleanField()
    rating = serializers.FloatField()
    completed = serializers.IntegerField()


class TaskListSerializer(serializers.ModelSerializer):
    creator = serializers.SerializerMethodField()
    kind = serializers.CharField()
    type = serializers.CharField()
    exchange = serializers.CharField()
    gender_preference = serializers.CharField()
    risk = serializers.CharField()
    status = serializers.CharField()
    is_saved = serializers.SerializerMethodField()
    is_reposted = serializers.SerializerMethodField()
    has_applied = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "type",
            "kind",
            "payout_note",
            "title",
            "description",
            "category",
            "scheduled_at",
            "duration_minutes",
            "area",
            "distance_km",
            "exchange",
            "reward_amount",
            "capacity",
            "applicant_count",
            "gender_preference",
            "risk",
            "status",
            "created_at",
            "meeting_preference",
            "has_checkin",
            "creator",
            "is_saved",
            "is_reposted",
            "has_applied",
        ]

    def get_creator(self, obj) -> dict:
        return {
            "id": str(obj.creator_id),
            "public_name": obj.display_creator_name,
            "photo_url": obj.creator.photo_url,
            "verified": obj.creator.verified_badge,
            "rating": obj.creator.rating,
            "completed": obj.creator.completed_count,
        }

    def _member(self):
        return self.context["request"].user

    def get_is_saved(self, obj) -> bool:
        return obj.saved_by.filter(member=self._member()).exists()

    def get_is_reposted(self, obj) -> bool:
        return obj.reposted_by.filter(member=self._member()).exists()

    def get_has_applied(self, obj) -> bool:
        return obj.applications.filter(member=self._member()).exists()


class TaskDetailSerializer(TaskListSerializer):
    class Meta(TaskListSerializer.Meta):
        fields = [*TaskListSerializer.Meta.fields, "quarantined", "lat", "lng"]


class ApplicationSerializer(serializers.ModelSerializer):
    member = serializers.SerializerMethodField()
    status = serializers.CharField()

    class Meta:
        model = Application
        fields = [
            "id",
            "task",
            "member",
            "intro_message",
            "status",
            "created_at",
            "unread_for_creator",
            "unread_for_member",
        ]

    def get_member(self, obj) -> dict:
        from apps.accounts.serializers import MemberPublicSerializer

        return MemberPublicSerializer(obj.member).data


class TaskCreateSerializer(serializers.ModelSerializer):
    """Covers every create flow: wizard, SOS broadcast, gigs, rooms, teams."""

    kind = serializers.ChoiceField(choices=Task.PostKind.choices)
    type = serializers.ChoiceField(choices=Task.PostType.choices)
    exchange = serializers.ChoiceField(choices=Task.ExchangeMode.choices)
    gender_preference = serializers.ChoiceField(choices=Task.GenderPreference.choices)
    payout_note = serializers.CharField(required=False, allow_blank=True, default="")

    class Meta:
        model = Task
        fields = [
            "type",
            "kind",
            "title",
            "description",
            "category",
            "scheduled_at",
            "duration_minutes",
            "area",
            "exchange",
            "reward_amount",
            "capacity",
            "gender_preference",
            "meeting_preference",
            "has_checkin",
            "payout_note",
        ]

    def validate_title(self, value):
        from apps.core.moderation import screen

        verdict = screen(value, self.initial_data.get("description", ""))
        if not verdict.clean:
            raise serializers.ValidationError(verdict.reason)
        return value

    def validate(self, attrs):
        kind = attrs.get("kind")
        if kind == Task.PostKind.EMERGENCY:
            attrs["risk"] = Task.TaskRisk.HIGH
            attrs["has_checkin"] = True
            attrs["exchange"] = Task.ExchangeMode.FREE
            attrs["scheduled_at"] = attrs.get("scheduled_at") or timezone.now()
        if kind == Task.PostKind.TRIP:
            attrs["risk"] = Task.TaskRisk.MEDIUM
            attrs["has_checkin"] = True
        if kind == Task.PostKind.GIG:
            attrs["exchange"] = Task.ExchangeMode.PAID
        if kind == Task.PostKind.ROOM:
            attrs["exchange"] = Task.ExchangeMode.PAID
        # Risk heuristics mirroring the client's _riskFor():
        when = attrs.get("scheduled_at")
        if when and not attrs.get("risk"):
            hour = when.hour
            if hour >= 21 or hour <= 5:
                attrs["risk"] = Task.TaskRisk.HIGH
            elif attrs.get("duration_minutes", 0) > 180:
                attrs["risk"] = Task.TaskRisk.MEDIUM
            else:
                attrs["risk"] = Task.TaskRisk.LOW
        return attrs
