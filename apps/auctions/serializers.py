from rest_framework import serializers

from apps.auctions.models import AuctionItem, Bid


class BidSerializer(serializers.ModelSerializer):
    bidder_name = serializers.CharField(source="bidder.public_name", read_only=True)
    bidder_photo = serializers.CharField(source="bidder.photo_url", read_only=True)

    class Meta:
        model = Bid
        fields = ["id", "bidder", "bidder_name", "bidder_photo", "amount", "created_at"]


class AuctionItemSerializer(serializers.ModelSerializer):
    seller = serializers.SerializerMethodField()
    bids = serializers.SerializerMethodField()
    status = serializers.CharField()
    platform_fee_amount = serializers.FloatField(read_only=True)
    total_winner_cost = serializers.FloatField(read_only=True)

    class Meta:
        model = AuctionItem
        fields = [
            "id",
            "title",
            "description",
            "category",
            "image_url",
            "video_url",
            "listing_type",
            "rent_price",
            "rent_period",
            "deposit_amount",
            "is_rented",
            "seller",
            "base_price",
            "current_bid",
            "buy_it_now_price",
            "service_fee_percent",
            "platform_fee_amount",
            "total_winner_cost",
            "start_time",
            "end_time",
            "total_bids",
            "status",
            "area",
            "distance_km",
            "bids",
            "created_at",
        ]

    def get_seller(self, obj) -> dict:
        return {
            "id": str(obj.seller_id),
            "public_name": obj.seller.public_name,
            "photo_url": obj.seller.photo_url,
            "verified": obj.seller.verified_badge,
            "rating": obj.seller.rating,
        }

    def get_bids(self, obj) -> list:
        top = obj.bid_history.select_related("bidder")[:10]
        return BidSerializer(top, many=True).data


class AuctionCreateSerializer(serializers.ModelSerializer):
    duration_hours = serializers.IntegerField(min_value=1, max_value=24 * 30, default=168)
    base_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)

    class Meta:
        model = AuctionItem
        fields = [
            "title",
            "description",
            "category",
            "image_url",
            "listing_type",
            "rent_price",
            "rent_period",
            "deposit_amount",
            "base_price",
            "buy_it_now_price",
            "duration_hours",
            "area",
        ]

    def validate(self, attrs):
        from django.utils import timezone

        listing_type = attrs.get("listing_type", AuctionItem.ListingType.AUCTION)
        if listing_type == AuctionItem.ListingType.RENT:
            if not attrs.get("rent_price") and not attrs.get("base_price"):
                raise serializers.ValidationError("Rent price is required for rentals.")
            if not attrs.get("base_price"):
                attrs["base_price"] = attrs.get("rent_price")
            if not attrs.get("rent_price"):
                attrs["rent_price"] = attrs.get("base_price")
        else:
            if not attrs.get("base_price"):
                raise serializers.ValidationError("Base price is required.")

        bin_price = attrs.get("buy_it_now_price")
        base = attrs.get("base_price")
        if bin_price is not None and base is not None and bin_price <= base:
            raise serializers.ValidationError("Buy-It-Now must be higher than the base price.")
        from apps.core.moderation import screen

        verdict = screen(attrs.get("title", ""), attrs.get("description", ""))
        if not verdict.clean:
            raise serializers.ValidationError(verdict.reason)
        attrs["start_time"] = timezone.now()
        duration = attrs.pop("duration_hours", 168)
        attrs["end_time"] = timezone.now() + timezone.timedelta(hours=duration)
        return attrs

