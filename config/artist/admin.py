from django.contrib import admin
from .models import Artwork


@admin.register(Artwork)
class ArtworkAdmin(admin.ModelAdmin):
    list_display = (
        "id",           # 🔥 ID show karega
        "title",
        "artist",
        "price",
        "is_active",
        "created_at",
    )

    list_filter = ("is_active", "artist")
    search_fields = ("title", "artist__username")
