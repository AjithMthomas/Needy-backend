"""Auction rule tests — bid integrity + closing semantics."""

import pytest
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Member
from apps.auctions import services
from apps.auctions.models import AuctionItem
from apps.core.exceptions import BusinessRuleError

pytestmark = pytest.mark.django_db


def auth_for(member):
    return {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(member).access_token!s}"}


@pytest.fixture
def seller():
    return Member.objects.create_member("seller@test.dev", public_name="Seller")


@pytest.fixture
def bidder():
    return Member.objects.create_member("bidder@test.dev", public_name="Bidder")


@pytest.fixture
def live_auction(seller):
    return AuctionItem.objects.create(
        seller=seller,
        title="Test item",
        description="A thing",
        category="Gadgets",
        base_price=100,
        current_bid=100,
        buy_it_now_price=500,
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=5),
        status=AuctionItem.Status.ACTIVE,
    )


def test_bid_must_exceed_current(client, seller, bidder, live_auction):
    response = client.post(
        f"/api/v1/auctions/{live_auction.id}/bids",
        {"amount": 90},
        content_type="application/json",
        **auth_for(bidder),
    )
    assert response.status_code == 400


def test_bid_success_updates_state(client, seller, bidder, live_auction):
    response = client.post(
        f"/api/v1/auctions/{live_auction.id}/bids",
        {"amount": 150},
        content_type="application/json",
        **auth_for(bidder),
    )
    assert response.status_code == 201
    live_auction.refresh_from_db()
    assert float(live_auction.current_bid) == 150.0
    assert live_auction.total_bids == 1


def test_seller_cannot_bid(client, seller, live_auction):
    with pytest.raises(BusinessRuleError):
        services.place_bid(live_auction, seller, 200)


def test_buy_now_wins_instantly(client, seller, bidder, live_auction):
    response = client.post(
        f"/api/v1/auctions/{live_auction.id}/buy-now",
        content_type="application/json",
        **auth_for(bidder),
    )
    assert response.status_code == 200
    live_auction.refresh_from_db()
    assert str(live_auction.winner_id) == str(bidder.id)
    assert live_auction.status == AuctionItem.Status.COMPLETED

    # Second buyer is too late.
    late = Member.objects.create_member("late@test.dev", public_name="Late")
    response = client.post(
        f"/api/v1/auctions/{live_auction.id}/buy-now",
        content_type="application/json",
        **auth_for(late),
    )
    assert response.status_code == 400


def test_lazy_close_completes_ended_auction(client, seller, bidder, live_auction):
    live_auction.end_time = timezone.now() - timezone.timedelta(minutes=1)
    live_auction.save()

    response = client.get(f"/api/v1/auctions/{live_auction.id}", **auth_for(bidder))
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"  # no bids placed


def test_create_and_rent_furniture_item(client, seller, bidder):
    # 1. Create a rental listing for an ergonomic office chair & desk
    create_res = client.post(
        "/api/v1/auctions/create",
        {
            "title": "Ergonomic Office Chair & Work Desk",
            "description": "Solid wood desk and high-back mesh chair in Madiwala.",
            "category": "Home & Room",
            "listing_type": "rent",
            "rent_price": "499.00",
            "rent_period": "month",
            "deposit_amount": "1000.00",
            "area": "Madiwala 1st Stage",
        },
        content_type="application/json",
        **auth_for(seller),
    )
    assert create_res.status_code == 201
    item_id = create_res.json()["id"]
    assert create_res.json()["listing_type"] == "rent"
    assert float(create_res.json()["rent_price"]) == 499.0

    # 2. Filter by listing_type=rent
    list_res = client.get("/api/v1/auctions?listing_type=rent", **auth_for(bidder))
    assert list_res.status_code == 200
    assert any(item["id"] == item_id for item in list_res.json()["results"])

    # 3. Seller cannot rent own item
    self_rent = client.post(
        f"/api/v1/auctions/{item_id}/rent",
        {"duration_units": 2},
        content_type="application/json",
        **auth_for(seller),
    )
    assert self_rent.status_code == 400

    # 4. Renter successfully rents item
    rent_res = client.post(
        f"/api/v1/auctions/{item_id}/rent",
        {"duration_units": 3},
        content_type="application/json",
        **auth_for(bidder),
    )
    assert rent_res.status_code == 200
    assert rent_res.json()["is_rented"] is True

    # 5. Subsequent rental is rejected
    another = Member.objects.create_member("another@test.dev", public_name="Another")
    rent_again = client.post(
        f"/api/v1/auctions/{item_id}/rent",
        {"duration_units": 1},
        content_type="application/json",
        **auth_for(another),
    )
    assert rent_again.status_code == 400

