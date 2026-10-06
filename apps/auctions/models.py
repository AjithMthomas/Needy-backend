"""auctions models — auctions, bids, buy-it-now, 5% service fee.

Fee math lives in services; the model stores the percent so the rate is
frozen per auction at creation time (changing the platform fee later
never rewrites history).
"""

from __future__ import annotations

import uuid

from django.db import models

from apps.accounts.models import Member
from apps.core.models import UUIDModel


class AuctionItem(UUIDModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Live auction"
        ENDING_SOON = "endingSoon", "Ending soon"
        COMPLETED = "completed", "Auction ended"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="auctions")
    title = models.CharField(max_length=140)
    description = models.TextField()
    category = models.CharField(max_length=60, default="Gadgets")
    image_url = models.URLField(blank=True, default="")
    video_url = models.URLField(blank=True, default="")

    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    current_bid = models.DecimalField(max_digits=12, decimal_places=2)
    buy_it_now_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    service_fee_percent = models.DecimalField(max_digits=4, decimal_places=2, default=5.0)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField(db_index=True)
    total_bids = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    area = models.CharField(max_length=120, default="Madiwala Central")
    distance_km = models.FloatField(default=0.5)
    winner = models.ForeignKey(
        Member,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="auctions_won",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "-end_time"])]

    def __str__(self) -> str:
        return self.title

    @property
    def platform_fee_amount(self) -> float:
        return float(self.current_bid) * float(self.service_fee_percent) / 100.0

    @property
    def total_winner_cost(self) -> float:
        return float(self.current_bid) + self.platform_fee_amount


class Bid(UUIDModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auction = models.ForeignKey(AuctionItem, on_delete=models.CASCADE, related_name="bid_history")
    bidder = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="bids")
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["-amount", "-created_at"]
        # Under-bids are impossible by construction: services.place_bid()
        # locks the auction row (select_for_update) and re-validates before
        # inserting. (A DB constraint can't span the join to auction.current_bid.)
