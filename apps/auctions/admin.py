from django.contrib import admin

from apps.auctions.models import AuctionItem, Bid


@admin.register(AuctionItem)
class AuctionItemAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "seller",
        "current_bid",
        "buy_it_now_price",
        "total_bids",
        "status",
        "end_time",
    )
    list_filter = ("status", "category")
    search_fields = ("title", "seller__email")


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ("auction", "bidder", "amount", "created_at")
    search_fields = ("auction__title", "bidder__email")
