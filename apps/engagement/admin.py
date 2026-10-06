from django.contrib import admin

from apps.engagement.models import (
    BoardIdea,
    ChallengePlay,
    IdeaVote,
    KarmaLedger,
    PartnerPerk,
    PerkClaim,
    PlayChallenge,
    RadarPing,
)


@admin.register(KarmaLedger)
class KarmaLedgerAdmin(admin.ModelAdmin):
    list_display = ("member", "kind", "amount", "reason", "balance_after", "created_at")
    search_fields = ("member__email", "reason")
    list_filter = ("kind",)


@admin.register(PartnerPerk)
class PartnerPerkAdmin(admin.ModelAdmin):
    list_display = ("merchant", "title", "cost_karma", "area", "valid_hours", "is_active")
    list_filter = ("is_active",)


@admin.register(PlayChallenge)
class PlayChallengeAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "target", "reward_karma", "is_active")


@admin.register(BoardIdea)
class BoardIdeaAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "tag", "upvotes", "scheduled", "created_at")
    list_filter = ("scheduled", "tag")
    search_fields = ("title", "author__email")


admin.site.register(PerkClaim)
admin.site.register(ChallengePlay)
admin.site.register(IdeaVote)
admin.site.register(RadarPing)
