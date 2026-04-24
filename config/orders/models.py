from django.db import models
from django.conf import settings
from scrap.models import Artwork


class Order(models.Model):

    STATUS = (
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('FAILED', 'Failed'),  # ✅ Added for payment failure handling
    )

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="scrap_orders"
    )

    artwork = models.ForeignKey(
        Artwork,
        on_delete=models.CASCADE,
        related_name="market_orders"
    )

    quantity = models.PositiveIntegerField(default=1)
    total_price = models.FloatField()

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default='PENDING'
    )

    # 🔐 Razorpay Payment Tracking Fields (NEW - SAFE ADDITION)
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)

    ordered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.artwork.title} | {self.buyer.username}"


# ===============================
# ARTWORK ORDER MODEL
# ===============================

class ArtworkOrder(models.Model):

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("failed", "Failed"),
    )

    artwork = models.ForeignKey(
        Artwork,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="artwork_orders"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )
    quantity = models.PositiveIntegerField(default=1)
    
    payment_id = models.CharField(max_length=200, blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=200, blank=True, null=True)

    payment_status = models.CharField(
        max_length=20,
        default="pending"
    )

    commission_amount = models.FloatField(default=0)
    artist_amount = models.FloatField(default=0)

    is_settled = models.BooleanField(default=False)

    is_sold = models.BooleanField(default=False)

    ordered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.artwork.title} → {self.buyer.username}"