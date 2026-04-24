from .models import Artwork, Wishlist
from django.db.models import Count, Avg
from orders.models import ArtworkOrder


def get_recommended_artworks(user):

    # ⭐ Case 1 — If user has wishlist
    wishlist_categories = Wishlist.objects.filter(
        user=user
    ).values_list("artwork__title", flat=True)

    if wishlist_categories:
        return Artwork.objects.filter(
            title__in=wishlist_categories,
            is_active=True
        )[:3]

    # ⭐ Case 2 — If user has purchases
    orders = ArtworkOrder.objects.filter(
        buyer=user,
        status="Sold"
    )

    if orders.exists():
        avg_price = orders.aggregate(avg=Avg("artwork__price"))["avg"]

        return Artwork.objects.filter(
            price__gte=avg_price * 0.7,
            price__lte=avg_price * 1.3,
            is_active=True
        )[:3]

    # ⭐ Case 3 — fallback → popular artworks
    return Artwork.objects.filter(
        is_active=True
    ).annotate(
        popularity=Count("wishlisted_by")
    ).order_by("-popularity")[:3]
