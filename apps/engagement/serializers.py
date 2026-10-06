from rest_framework import serializers

from apps.engagement.models import (
    BoardIdea,
    KarmaLedger,
    PartnerPerk,
    PlayChallenge,
)


class KarmaEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = KarmaLedger
        fields = ["id", "kind", "amount", "reason", "balance_after", "created_at"]


class PartnerPerkSerializer(serializers.ModelSerializer):
    claimed_by_me = serializers.SerializerMethodField()

    class Meta:
        model = PartnerPerk
        fields = [
            "id",
            "merchant",
            "title",
            "details",
            "icon",
            "cost_karma",
            "area",
            "valid_hours",
            "claimed_by_me",
        ]

    def get_claimed_by_me(self, obj) -> bool:
        member = self.context.get("member")
        return bool(member and obj.claims.filter(member=member).exists())


class PlayChallengeSerializer(serializers.ModelSerializer):
    played_today = serializers.SerializerMethodField()

    class Meta:
        model = PlayChallenge
        fields = ["id", "code", "title", "rules", "target", "reward_karma", "icon", "played_today"]

    def get_played_today(self, obj) -> bool:
        from apps.engagement.services import has_played_today

        member = self.context.get("member")
        return bool(member and has_played_today(member, obj))


class BoardIdeaSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    voted_by_me = serializers.SerializerMethodField()

    class Meta:
        model = BoardIdea
        fields = [
            "id",
            "author",
            "title",
            "details",
            "tag",
            "upvotes",
            "voted_by_me",
            "scheduled",
            "created_at",
        ]

    def get_author(self, obj) -> dict:
        return {
            "id": str(obj.author_id),
            "public_name": obj.author.public_name,
            "photo_url": obj.author.photo_url,
        }

    def get_voted_by_me(self, obj) -> bool:
        member = self.context.get("member")
        return bool(member and obj.votes.filter(member=member).exists())


class IdeaCreateSerializer(serializers.Serializer):
    title = serializers.CharField(min_length=4, max_length=140)
    details = serializers.CharField(max_length=800, required=False, allow_blank=True, default="")
    tag = serializers.CharField(max_length=40, default="Feature")


class RadarZoneSerializer(serializers.Serializer):
    zone = serializers.CharField()
    free = serializers.IntegerField()
    tasks = serializers.IntegerField()
    tea = serializers.IntegerField()
