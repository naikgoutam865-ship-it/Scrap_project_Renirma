from django.contrib import admin
from .models import Scrap, ScrapRequest


@admin.register(Scrap)
class ScrapAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "category",
        "seller",
        "weight_kg",
        "price_per_kg",
        "location",
        "is_available",
        "created_at",
    )
    list_filter = ("category", "is_available")
    search_fields = ("category", "seller__username")


@admin.register(ScrapRequest)
class ScrapRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "scrap",
        "requested_by",
        "status",
        "requested_at",
    )
    list_filter = ("status",)
    search_fields = (
        "requested_by__username",
        "scrap__seller__username",
    )

from orders.models import ArtworkOrder
from scrap.models import ScrapPayment

from django.contrib import admin

@admin.register(ArtworkOrder)
class ArtworkOrderAdmin(admin.ModelAdmin):
    list_display = (
        "artwork",
        "buyer",
        "status",
        "payment_status",
        "is_sold",
        "is_settled",
        "ordered_at",
    )

    list_filter = ("status", "payment_status", "is_settled")

    search_fields = ("artwork__title", "buyer__username")

admin.site.register(ScrapPayment)

from .models import Wishlist
admin.site.register(Wishlist)
