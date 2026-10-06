"""auctions views."""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auctions import services
from apps.auctions.models import AuctionItem
from apps.auctions.serializers import (
    AuctionCreateSerializer,
    AuctionItemSerializer,
    BidSerializer,
)
from apps.core.exceptions import BusinessRuleError


def _fresh(request, auction_id) -> AuctionItem:
    auction = get_object_or_404(
        AuctionItem.objects.select_related("seller"),
        id=auction_id,
    )
    return services.maybe_close(auction)


class AuctionListView(generics.ListAPIView):
    """GET /auctions — newest first; ?live=1 filters to active ones."""

    serializer_class = AuctionItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = AuctionItem.objects.select_related("seller")
        if self.request.query_params.get("live") == "1":
            qs = qs.filter(
                status__in=[AuctionItem.Status.ACTIVE, AuctionItem.Status.ENDING_SOON],
            )
            # Exclude auctions past their end time that no detail read has
            # lazily closed yet — otherwise users can tap a "live" auction
            # and get "This auction has just ended" on their first bid.
            qs = qs.exclude(end_time__lte=timezone.now())
        return qs


class AuctionDetailView(APIView):
    """GET /auctions/{id} — lazy-closes the auction on read."""

    permission_classes = [IsAuthenticated]

    def get(self, request, auction_id):
        auction = _fresh(request, auction_id)
        return Response(AuctionItemSerializer(auction).data)


class AuctionCreateView(APIView):
    """POST /auctions — host a new auction."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AuctionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        auction = serializer.save(
            seller=request.user,
            current_bid=serializer.validated_data["base_price"],
            status=AuctionItem.Status.ACTIVE,
        )
        return Response(AuctionItemSerializer(auction).data, status=status.HTTP_201_CREATED)


class BidView(APIView):
    """POST /auctions/{id}/bids {amount}."""

    permission_classes = [IsAuthenticated]

    def post(self, request, auction_id):
        auction = _fresh(request, auction_id)
        amount = (request.data or {}).get("amount")
        if amount is None:
            return Response(
                {"detail": "amount required", "code": "invalid"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            bid = services.place_bid(auction, request.user, float(amount))
        except (BusinessRuleError, ValueError) as exc:
            detail = str(getattr(exc, "detail", exc))
            return Response(
                {"detail": detail, "code": "bid_invalid"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(BidSerializer(bid).data, status=status.HTTP_201_CREATED)


class BuyNowView(APIView):
    """POST /auctions/{id}/buy-now — instant win."""

    permission_classes = [IsAuthenticated]

    def post(self, request, auction_id):
        auction = _fresh(request, auction_id)
        try:
            auction = services.buy_now(auction, request.user)
        except BusinessRuleError as exc:
            return Response(
                {"detail": str(exc.detail), "code": exc.default_code},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(AuctionItemSerializer(auction).data)
