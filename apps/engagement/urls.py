"""engagement URL routes (mounted under /api/v1/)."""

from django.urls import path

from apps.engagement import views

urlpatterns = [
    path("karma", views.KarmaView.as_view(), name="karma"),
    path("perks", views.PerkListView.as_view(), name="perks"),
    path("perks/<uuid:perk_id>/claim", views.PerkClaimView.as_view(), name="perk-claim"),
    path("challenges", views.ChallengeListView.as_view(), name="challenges"),
    path(
        "challenges/<uuid:challenge_id>/play",
        views.ChallengePlayView.as_view(),
        name="challenge-play",
    ),
    path("community/ideas", views.IdeaListView.as_view(), name="ideas"),
    path("community/ideas/create", views.IdeaCreateView.as_view(), name="idea-create"),
    path("community/ideas/<uuid:idea_id>/vote", views.IdeaVoteView.as_view(), name="idea-vote"),
    path("radar", views.RadarView.as_view(), name="radar"),
]
