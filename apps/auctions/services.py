"""auction services — bidding, buy-it-now, lazy closing.

Lazy close: auctions flip to ``completed`` whenever they are read after
their end time — no cron needed for correctness on the free tier. An
optional daily management command (later) sweeps stragglers.
"""

from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Member
from apps.auctions.models import AuctionItem, Bid
from apps.core.exceptions import BusinessRuleError


@transaction.atomic
def place_bid(auction: AuctionItem, bidder: Member, amount: float) -> Bid:
    """Race-safe: lock the auction row, re-validate, then write."""
    if auction.seller_id == bidder.id:
        raise BusinessRuleError("You can't bid on your own auction.")
    if auction.status == AuctionItem.Status.COMPLETED:
        raise BusinessRuleError("This auction has ended.")

    locked = AuctionItem.objects.select_for_update().get(pk=auction.pk)
    if locked.end_time <= timezone.now():
        _complete(locked)
        raise BusinessRuleError("This auction has just ended.")

    amount = Decimal(str(amount)).quantize(Decimal("0.01"))
    if amount <= locked.current_bid:
        raise BusinessRuleError(
            f"Bid must be higher than the current bid (₹{locked.current_bid:0.0f})."
        )

    bid = Bid.objects.create(auction=locked, bidder=bidder, amount=amount)
    locked.current_bid = amount
    locked.total_bids = locked.total_bids + 1
    locked.save(update_fields=["current_bid", "total_bids", "updated_at"])
    return bid


@transaction.atomic
def buy_now(auction: AuctionItem, buyer: Member) -> AuctionItem:
    """Instant win at the BIN price — first caller wins (row-locked)."""
    if auction.seller_id == buyer.id:
        raise BusinessRuleError("You can't buy your own auction.")
    if auction.status == AuctionItem.Status.COMPLETED:
        raise BusinessRuleError("This auction has ended.")

    locked = AuctionItem.objects.select_for_update().get(pk=auction.pk)
    if locked.buy_it_now_price is None:
        raise BusinessRuleError("No Buy-It-Now price on this auction.")
    if locked.end_time <= timezone.now():
        _complete(locked)
        raise BusinessRuleError("This auction has just ended.")
    if locked.winner_id is not None:
        raise BusinessRuleError("Someone already claimed Buy-It-Now.")

    locked.winner = buyer
    locked.current_bid = locked.buy_it_now_price
    locked.status = AuctionItem.Status.COMPLETED
    locked.save(update_fields=["winner", "current_bid", "status", "updated_at"])
    return locked


def maybe_close(auction: AuctionItem) -> AuctionItem:
    """Lazy close on read; cheap (single UPDATE) once closed."""
    if auction.status == AuctionItem.Status.COMPLETED:
        return auction
    if auction.end_time <= timezone.now():
        _complete(auction)
    elif auction.status == AuctionItem.Status.ACTIVE:
        remaining = auction.end_time - timezone.now()
        if remaining.total_seconds() <= 3600:
            auction.status = AuctionItem.Status.ENDING_SOON
            auction.save(update_fields=["status", "updated_at"])
    return auction


@transaction.atomic
def _complete(auction: AuctionItem) -> None:
    top = auction.bid_history.order_by("-amount", "-created_at").first()
    if top is not None:
        auction.winner = top.bidder
        auction.status = AuctionItem.Status.COMPLETED
    else:
        auction.status = AuctionItem.Status.CANCELLED
    auction.save(update_fields=["winner", "status", "updated_at"])
