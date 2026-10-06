"""auctions URL routes (mounted under /api/v1/)."""

from django.urls import path

from apps.auctions import views

urlpatterns = [
    path("auctions", views.AuctionListView.as_view(), name="auctions"),
    path("auctions/create", views.AuctionCreateView.as_view(), name="auction-create"),
    path("auctions/<uuid:auction_id>", views.AuctionDetailView.as_view(), name="auction-detail"),
    path("auctions/<uuid:auction_id>/bids", views.BidView.as_view(), name="auction-bid"),
    path("auctions/<uuid:auction_id>/buy-now", views.BuyNowView.as_view(), name="auction-buy-now"),
]
