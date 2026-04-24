from django.db import models
from django.conf import settings
from artist.models import Artwork   # ✅ SINGLE SOURCE OF TRUTH


# ===============================
# SCRAP MODEL
# ===============================

class Scrap(models.Model):

    CATEGORY_CHOICES = (
        ('plastic', 'Plastic'),
        ('metal', 'Metal'),
        ('paper', 'Paper'),
        ('ewaste', 'E-Waste'),
        ('glass', 'Glass'),
    )

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    weight_kg = models.FloatField()
    price_per_kg = models.FloatField()
    location = models.CharField(max_length=200)

    image = models.ImageField(
        upload_to="scrap_images/",
        blank=True,
        null=True
    )

    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    available_weight = models.FloatField(default=0)

    def __str__(self):
        return f"{self.category} - {self.weight_kg} kg"


# ===============================
# SCRAP REQUEST MODEL
# ===============================

class ScrapRequest(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    scrap = models.ForeignKey(
        Scrap,
        on_delete=models.CASCADE,
        related_name="requests"
    )

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="my_requests"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    is_paid = models.BooleanField(default=False)

    requested_at = models.DateTimeField(auto_now_add=True)

    requested_weight = models.FloatField(default=0)

    pickup_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("scheduled", "Scheduled"),
            ("picked", "Picked Up"),
            ("completed", "Completed"),
        ],
        default="pending"
    )
    pickup_deadline = models.DateTimeField(null=True, blank=True)

    pickup_time = models.CharField(
        max_length=20,
        choices=[
            ("morning", "Morning"),
            ("afternoon", "Afternoon"),
            ("evening", "Evening")
        ],
        blank=True,
        null=True
    )
    pickup_date = models.DateField(blank=True, null=True)
    pickup_contact = models.CharField(max_length=15, blank=True, null=True)
    
    def __str__(self):
        return f"{self.requested_by} → {self.scrap} ({self.status})"


# ===============================
# SCRAP PAYMENT MODEL (ADMIN HOLD)
# ===============================

class ScrapPayment(models.Model):

    STATUS_CHOICES = (
        ("created", "Created"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    )

    scrap_request = models.ForeignKey(
        ScrapRequest,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    artist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    razorpay_order_id = models.CharField(max_length=200, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=200, blank=True, null=True)

    # ✅ NEW FIELD (for signature verification security)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="created"
    )

    is_released = models.BooleanField(default=False)  # Admin payout control

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Scrap Payment - {self.scrap_request.id}"

# ===============================
# WISHLIST SYSTEM
# ===============================

class Wishlist(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist_items"
    )

    artwork = models.ForeignKey(
        Artwork,
        on_delete=models.CASCADE,
        related_name="wishlisted_by"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "artwork")  # 🔥 prevent duplicate

    def __str__(self):
        return f"{self.user.username} ❤️ {self.artwork.title}"

class Review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    artist_name = models.CharField(max_length=120)
    scrap_type = models.CharField(max_length=120)
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.scrap_type} - {self.rating}⭐"

# NOTIFICATION SYSTEM

class ScrapAlert(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    category = models.CharField(max_length=50)
    min_weight = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_notified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} waiting for {self.category}"

# ===============================
# WALLET SYSTEM
# ===============================

class Wallet(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} Wallet"
    

# ===============================
# WITHDRAW REQUEST MODEL
# ===============================

class WithdrawRequest(models.Model):

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("rejected", "Rejected"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    payout_reference = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    paid_at = models.DateTimeField(
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount}"
    

# ===============================
# BANK DETAILS MODEL
# ===============================

class BankDetails(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    account_holder_name = models.CharField(max_length=200)

    bank_account_number = models.CharField(max_length=50)

    ifsc_code = models.CharField(max_length=20)

    upi_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} Bank Details"

# ===============================
# WALLET TRANSACTION LEDGER
# ===============================

class WalletTransaction(models.Model):

    TRANSACTION_TYPE = (
        ("credit", "Credit"),
        ("debit", "Debit"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPE
    )

    description = models.CharField(
        max_length=255
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} {self.transaction_type} ₹{self.amount}"