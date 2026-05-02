from django.http import HttpResponse
from .ai_utils import recommend_price
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings

from accounts.decorators import artist_required, dealer_required

from orders.models import ArtworkOrder
from .models import Review,Scrap, ScrapRequest, ScrapPayment, WalletTransaction, Wishlist
from artist.models import Artwork
from .recommendation import get_recommended_artworks


from decimal import Decimal
import requests



# ===============================
# SELLER — ADD SCRAP
# ===============================
@login_required
def add_scrap(request):

    selected_category = request.GET.get("category")

    # 🔥 NEW LINE (IMPORTANT)
    if not selected_category and request.method != "POST":
        return redirect("select_category")

    if request.method == "POST":

        category = request.POST.get("category")
        custom_category = request.POST.get("custom_category")

        # 🔥 MAIN FIX (ONLY THIS ADDED)
        if category == "other" and custom_category:
            category = custom_category.strip().title()

        Scrap.objects.create(
            seller=request.user,
            category=category,   # 👈 yahi change hua hai
            weight_kg=request.POST.get("weight_kg"),
            available_weight=request.POST.get("weight_kg"),
            price_per_kg=request.POST.get("price_per_kg"),
            location=request.POST.get("location"),
            image=request.FILES.get("image"),
            is_available=True
        )

        return redirect("my_scraps")

    return render(
        request,
        "scrap/add_scrap.html",
        {"selected_category": selected_category}
    )


# ===============================
# SELLER — MY SCRAPS
# ===============================
@login_required
def my_scraps(request):

    scraps = Scrap.objects.filter(seller=request.user)

    return render(
        request,
        "scrap/my_scraps.html",
        {"scraps": scraps}
    )


# ===============================
# MARKETPLACE
# ===============================
@login_required
def scrap_list(request):

    scraps = Scrap.objects.filter(
        is_available=True,
        available_weight__gt=0
    ).select_related("seller")

    return render(
        request,
        "scrap/scrap_list.html",
        {"scraps": scraps}
    )


# ===============================
# REQUEST SCRAP
# ===============================
@login_required
def request_scrap(request, scrap_id):

    scrap = get_object_or_404(Scrap, id=scrap_id)

    if scrap.seller == request.user:
        return redirect("scrap_list")

    # ✅ ensure available_weight initialized
    if scrap.available_weight == 0:
        scrap.available_weight = scrap.weight_kg
        scrap.save()

    if request.method == "POST":

        req_weight = float(request.POST.get("requested_weight"))

        # ❌ VALIDATION FIX (IMPORTANT)
        if req_weight > scrap.available_weight:
            messages.error(request, "Requested weight exceeds available scrap!")
            return render(request, "scrap/request_scrap.html", {"scrap": scrap})

        ScrapRequest.objects.create(
            scrap=scrap,
            requested_by=request.user,
            requested_weight=req_weight,
            status="pending"
        )

        messages.success(request, "Request sent successfully!")
        return redirect("my_requests")

    return render(
        request,
        "scrap/request_scrap.html",
        {"scrap": scrap}
    )


# ===============================
# SELLER — REQUESTS RECEIVED
# ===============================
@login_required
def my_scrap_requests(request):

    requests = ScrapRequest.objects.filter(
        scrap__seller=request.user
    ).select_related(
        "scrap",
        "requested_by"
    ).order_by("-requested_at")

    return render(
        request,
        "scrap/my_scrap_requests.html",
        {"requests": requests}
    )


# ===============================
# SELLER — APPROVE / REJECT
# ===============================
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages

@login_required
def update_request_status(request, request_id, status):

    req = get_object_or_404(ScrapRequest, id=request_id)

    if req.scrap.seller != request.user:
        return redirect("my_scrap_requests")

    req.status = status
    req.save()

    if status == "approved":

        scrap = req.scrap

        # ❌ already approved block
        if req.status == "approved":
            messages.warning(request, "Already approved!")
            return redirect("my_scrap_requests")

        # safety initialization
        if scrap.available_weight == 0:
            scrap.available_weight = scrap.weight_kg

        # ❌ weight exceed check (IMPORTANT)
        if req.requested_weight > scrap.available_weight:
            messages.error(request, "Not enough scrap available!")
            return redirect("my_scrap_requests")

        # ✅ reduce weight
        scrap.available_weight -= req.requested_weight

        if scrap.available_weight <= 0:
            scrap.available_weight = 0
            scrap.is_available = False

        scrap.save()

        # ✅ status update yaha kar
        req.status = "approved"
        req.save()

        # ===============================
        # 📧 EMAIL TO ARTIST ON APPROVAL
        # ===============================
        from django.core.mail import send_mail
        from django.conf import settings

        try:
            if req.requested_by.email:
                send_mail(
                    subject="Scrap Approved – Complete Payment ♻️",
                    message=f"""
Hello {req.requested_by.username},

Great news!

Your scrap request for "{req.scrap.category}" has been approved by the seller.

👉 Please login and complete payment to start your artwork creation.

– ReNirma Team
""",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[req.requested_by.email],
                    fail_silently=False,
                )
        except Exception as e:
            print("Approval Email Error:", e)

    elif status == "rejected":
        req.status = "rejected"
        req.save()

        messages.warning(request, "Scrap request rejected ❌")

        return redirect("my_scrap_requests")

    # 🚨 SAFETY RETURN (very important)
    return redirect("my_scrap_requests")




# ===============================
# MY REQUESTS
# ===============================
@login_required
def my_requests(request):

    requests = ScrapRequest.objects.filter(
        requested_by=request.user
    ).select_related(
        "scrap",
        "scrap__seller"
    ).order_by("-requested_at")

    return render(
        request,
        "scrap/my_requests.html",
        {"requests": requests}
    )


# =====================================================
# ARTIST — VIEW AVAILABLE SCRAPS
# =====================================================
@artist_required
@login_required
def artist_scrap_list(request):

    scraps = Scrap.objects.filter(is_available=True , available_weight__gt=0)

    return render(
        request,
        "artist/artist_scrap_list.html",
        {"scraps": scraps}
    )


# =====================================================
# ARTIST — APPROVED SCRAPS
# =====================================================
@artist_required
@login_required
def scrap_payment(request, request_id):

    approved_request = get_object_or_404(
        ScrapRequest,
        id=request_id,
        requested_by=request.user,
        status="approved"
    )

    if approved_request.is_paid:
        return redirect("convert_to_artwork", request_id=request_id)

    scrap = approved_request.scrap
    amount = Decimal(approved_request.requested_weight) * Decimal(scrap.price_per_kg)

    if request.method == "POST":

        # ✅ mark paid directly
        approved_request.is_paid = True
        approved_request.pickup_status = "pending"
        approved_request.save()

        # 💰 CREDIT SELLER WALLET
        seller = scrap.seller

        commission = amount * Decimal("0.05")
        seller_amount = amount - commission

        wallet, _ = Wallet.objects.get_or_create(user=seller)
        wallet.balance += seller_amount
        wallet.save()

        WalletTransaction.objects.create(
            user=seller,
            amount=seller_amount,
            transaction_type="credit",
            description=f"Scrap sold: {scrap.category}"
        )

        messages.success(request, "Payment successful!")
        return redirect("pickup_details", request_id=request_id)

    return render(
        request,
        "artist/scrap_payment.html",
        {
            "approved_request": approved_request,
            "amount": amount,
        }
    )

# ===============================
# MY ARTWORKS
# ===============================
@artist_required
@login_required
def my_artworks(request):

    artworks = Artwork.objects.filter(
        artist=request.user
    ).order_by("-created_at")

    return render(
        request,
        "scrap/my_artworks.html",
        {"artworks": artworks}
    )

# ===============================
# PUBLIC ARTWORK MARKETPLACE
# ===============================
from django.db.models import Avg, Count
from django.db.models import Avg, Count, Q
from math import radians, cos, sin, asin, sqrt
from artist.models import Artwork

# 🔥 ADD THIS FUNCTION (TOP ME EK BAAR)


def artwork_marketplace(request):
    
    query = request.GET.get("q", "")
    sort = request.GET.get("sort", "")
    artist_filter = request.GET.get("artist", "")
    min_price = request.GET.get("min_price", "")
    max_price = request.GET.get("max_price", "")
    min_rating = request.GET.get("min_rating", "")

    artworks = Artwork.objects.filter(
        is_active=True,
        quantity__gt=0
    )

    # 🔎 Search
    if query:
        artworks = artworks.filter(title__icontains=query)

    # 🎨 Filter by Artist
    if artist_filter:
        artworks = artworks.filter(artist__username__icontains=artist_filter)

    # 💲 Price Range
    if min_price:
        artworks = artworks.filter(price__gte=min_price)

    if max_price:
        artworks = artworks.filter(price__lte=max_price)

    # ⭐ Rating
    if min_rating:
        try:
            artworks = artworks.filter(avg_rating__gte=min_rating)
        except:
            pass

    # 🔥 Sorting
    if sort == "low":
        artworks = artworks.order_by("price")
    elif sort == "high":
        artworks = artworks.order_by("-price")
    else:
        artworks = artworks.order_by("?")\
        

    # 🤖 Recommendation
    recommended = []
    if request.user.is_authenticated:
        try:
            recommended = get_recommended_artworks(request.user)
        except:
            recommended = []

    context = {
        "artworks": artworks,
        "query": query,
        "sort": sort,
        "artist_filter": artist_filter,
        "min_price": min_price,
        "max_price": max_price,
        "recommended": recommended,
    }

    return render(
        request,
        "artwork/artwork_marketplace.html",
        context
    )

def calculate_distance(lat1, lon1, lat2, lon2):

    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    r = 6371
    return c * r

def home(request):
    return render(request, "home.html")


# =====================================================
# SAFE BACKWARD COMPATIBILITY FIX
# =====================================================

@login_required
def artist_request_scrap(request, scrap_id):
    """
    Old URL compatibility function.
    Redirects safely to new unified request_scrap logic.
    """
    return request_scrap(request, scrap_id)


@login_required
def approved_scraps(request):

    approved_requests = ScrapRequest.objects.filter(
        requested_by=request.user,
        status="approved"
    ).select_related("scrap")

    print("CURRENT USER:", request.user)
    print("APPROVED DATA:", approved_requests)

    return render(
        request,
        "artist/approved_scraps.html",
        {
            "approved_requests": approved_requests
        }
    )

def is_scrap_converted(scrap):
    return Artwork.objects.filter(scrap=scrap).exists()


# ===============================
# ARTWORK DETAIL PAGE
# ===============================

@login_required
def artwork_detail(request, artwork_id):

    artwork = get_object_or_404(
        Artwork,
        id=artwork_id,
        is_active=True
    )

    return render(
        request,
        "artwork/artwork_detail.html",
        {
            "artwork": artwork,
        }
    )

# ===============================
# TOGGLE WISHLIST
# ===============================

@login_required
def toggle_wishlist(request, artwork_id):

    artwork = get_object_or_404(Artwork, id=artwork_id)

    wishlist_item = Wishlist.objects.filter(
        user=request.user,
        artwork=artwork
    )

    if wishlist_item.exists():
        wishlist_item.delete()
    else:
        Wishlist.objects.create(
            user=request.user,
            artwork=artwork
        )

    return redirect(request.META.get("HTTP_REFERER", "artwork_marketplace"))

# ===============================
# MY WISHLIST PAGE
# ===============================

@login_required
def my_wishlist(request):

    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related("artwork", "artwork__artist")

    return render(
        request,
        "artwork/my_wishlist.html",
        {
            "wishlist_items": wishlist_items
        }
    )

# ===============================
# ADMIN FINANCE DASHBOARD
# ===============================

from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404, redirect
from orders.models import ArtworkOrder
from .models import ScrapPayment


def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)


@superuser_required
def admin_finance_dashboard(request):

    # 📌 Pending paid orders
    pending_orders = ArtworkOrder.objects.filter(
        status="paid",
        is_settled=False
    ).select_related("artwork", "artwork__artist")

    # 💵 Total Revenue
    total_revenue = ArtworkOrder.objects.filter(
        status="paid"
    ).aggregate(total=Sum("artist_amount"))["total"] or 0

    # 🏦 Total Commission
    total_commission = ArtworkOrder.objects.filter(
        status="paid"
    ).aggregate(total=Sum("commission_amount"))["total"] or 0

    # 🎨 Total Artist Earnings
    total_artist_earnings = ArtworkOrder.objects.filter(
        status="paid"
    ).aggregate(total=Sum("artist_amount"))["total"] or 0

    # ⏳ Pending Settlements Count
    pending_settlements = pending_orders.count()

    # ♻ Scrap Payments Revenue
    scrap_revenue = ScrapPayment.objects.filter(
        status="paid"
    ).aggregate(total=Sum("amount"))["total"] or 0

    context = {
        "total_revenue": total_revenue,
        "total_commission": total_commission,
        "total_artist_earnings": total_artist_earnings,
        "pending_settlements": pending_settlements,
        "scrap_revenue": scrap_revenue,
        "pending_orders": pending_orders,
    }

    return render(
        request,
        "admin/admin_finance_dashboard.html",
        context
    )


@superuser_required
def mark_order_settled(request, order_id):

    order = get_object_or_404(ArtworkOrder, id=order_id)

    if order.status == "paid":
        order.is_settled = True
        order.save()

    return redirect("admin_finance_dashboard")

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Review


def all_reviews(request):

    reviews = Review.objects.all().order_by("-created_at")

    return render(
        request,
        "reviews/all_reviews.html",
        {"reviews": reviews}
    )


@login_required
def add_review(request):

    if request.user.role == "artist":
        messages.error(request, "Artists cannot add reviews.")
        return redirect("all_reviews")

    if request.method == "POST":

        Review.objects.create(
            user=request.user,
            artist_name=request.POST.get("artist_name"),
            scrap_type=request.POST.get("scrap_type"),
            rating=int(request.POST.get("rating")),
            comment=request.POST.get("comment")
        )

        messages.success(request, "Review submitted successfully!")
        return redirect("all_reviews")

    return render(request, "reviews/add_review.html")

from .models import ScrapAlert
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def create_scrap_alert(request):

    if request.method == "POST":
        category = request.POST.get("category")
        weight = request.POST.get("weight")

        ScrapAlert.objects.create(
            user=request.user,
            category=category,
            min_weight=weight   # ✅ CORRECT FIELD NAME
        )

        messages.success(request, "We will notify you when scrap becomes available!")
        return redirect("scrap_list")

    return render(request, "scrap/create_alert.html")

from django.http import JsonResponse
from .ai_fixed_data import SCRAP_AI_DATA

from django.http import JsonResponse

def ai_price(request):

    category = request.GET.get("category", "").lower()
    weight = float(request.GET.get("weight", 1))

    location = request.GET.get("location", "").lower()

    data = get_scrap_price(category)
    # 🔥 CATEGORY BASED INSIGHT
    INSIGHTS = {
        "newspaper": "Widely recycled for paper products",
        "books": "Good demand for reuse and recycled pulp",
        "cardboard": "High use in packaging industry",
        "iron": "Strong industrial demand and reuse value",
        "aluminium": "Very high recycling value with low energy cost",
        "copper": "Extremely valuable metal with strong resale market",
        "bottle": "Plastic bottles used in eco-art and recycling",
        "container": "Reusable and moderate demand material",
        "polythene": "High demand in recycling industries",
        "mobile": "Contains valuable electronic components",
        "laptop": "High resale potential due to parts reuse",
        "electronics": "E-waste valuable for extraction & art",
        "glass": "Used in decorative and recycled products",
    }

    base_price = data["price"]
    
    # 🔥 LOCATION FACTOR
    metro_cities = ["delhi", "mumbai", "bangalore", "hyderabad", "pune"]

    location_factor = 1.0   # default pehle set kar

    if any(city in location for city in metro_cities):
        location_factor = 1.1
        demand_level = "Very High"

    elif "odisha" in location or "bihar" in location:
        location_factor = 0.95
        demand_level = "Moderate"

    # 🔥 WEIGHT LOGIC (SMART ADD)
    if weight > 50:
        weight_factor = 0.9   # bulk discount
    elif weight > 20:
        weight_factor = 0.95
    elif weight < 5:
        weight_factor = 1.1   # small quantity → higher rate
    else:
        weight_factor = 1.0

    final_price = round(base_price * weight_factor * location_factor, 2)

    price = final_price
    total = round(price * weight, 2)

    

    insight_msg = "Stable scrap market"

    for key in INSIGHTS:
        if key in category:
            insight_msg = INSIGHTS[key]
            break
    
    # 🔥 DYNAMIC INSIGHT ADDITION
    if weight > 50:
        insight_msg += " | Bulk quantity may reduce per kg price"

    if "delhi" in location or "mumbai" in location:
        insight_msg += " | Metro city demand is high"

    return JsonResponse({
        "price": price,
        "total": total,
        "min": data["min"],
        "max": data["max"],
        "demand": demand_level,
        "resale": data["resale"],
        "insight": insight_msg
    })

@login_required
def convert_to_artwork(request, request_id):

    approved_request = get_object_or_404(
        ScrapRequest,
        id=request_id,
        requested_by=request.user,
        status="approved"
    )

    if not approved_request.is_paid:
        messages.error(request, "Please complete payment first.")
        return redirect("scrap_payment", request_id=request_id)

    scrap = approved_request.scrap

    if request.method == "POST":

        title = request.POST.get("title")
        notes = request.POST.get("description", "")
        price = request.POST.get("price")
        image = request.FILES.get("artwork_image")
        quantity = int(request.POST.get("quantity", 1))

        if not price:
            messages.error(request, "Please enter artwork price.")
            return redirect("convert_to_artwork", request_id=request_id)

        # ✅ SAFE PRICE CONVERSION
        try:
            price = float(price)
        except:
            messages.error(request, "Invalid price entered.")
            return redirect("convert_to_artwork", request_id=request_id)

        # ✅ IMAGE CHECK
        if not image:
            messages.error(request, "Please upload artwork image.")
            return redirect("convert_to_artwork", request_id=request_id)

        # ✅ CREATE ARTWORK
        artwork = Artwork.objects.create(
                artist=request.user,
                scrap=scrap,   # 👈 IMPORTANT (link scrap)
                title=title,
                description=notes,
                price=price,
                image=image,
                quantity=quantity
            )

        # 👇 FORCE activate (database safe)
        artwork.is_active = True
        artwork.save()

        # # 🔥 ADD THIS BLOCK (REQUIRED FOR SOLD COUNT)
        # from scrap.models import ArtworkOrder
        # ArtworkOrder.objects.create(
        #     artwork=artwork,
        #     buyer=request.user,
        #     is_sold=True,
        #     status="paid"
        # )

        # ✅ REMOVE FROM APPROVED LIST
        approved_request.status = "converted"
        approved_request.save()

        messages.success(request, "Artwork created successfully!")
        return redirect("artwork_marketplace")

    return render(
        request,
        "artist/convert_to_artwork.html",
        {"approved_request": approved_request}
    )

@dealer_required
@login_required
def sanctioned_scraps(request):

    scraps = ScrapRequest.objects.filter(
        requested_by=request.user,
        status="approved",
        is_paid=False
    ).select_related("scrap","scrap__seller")

    return render(
        request,
        "dealer/sanctioned_scraps.html",
        {"scraps": scraps}
    )

@dealer_required
@login_required
def dealer_history(request):

    purchases = ScrapRequest.objects.filter(
        requested_by=request.user,
        is_paid=True
    ).select_related("scrap", "scrap__seller")

    return render(
        request,
        "dealer/dealer_history.html",
        {"purchases": purchases}
    )


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from scrap.models import ScrapRequest, Wallet


@login_required
def dealer_scrap_payment(request, request_id):

    approved_request = get_object_or_404(
        ScrapRequest,
        id=request_id,
        requested_by=request.user,
        status="approved"
    )

    # already paid
    if approved_request.is_paid:
        return redirect("dealer_history")

    scrap = approved_request.scrap
    amount = Decimal(approved_request.requested_weight) * Decimal(scrap.price_per_kg)

    if request.method == "POST":

        # 🔥 IMPORTANT FIX (ye add kiya)
        request_id_post = request.POST.get("request_id")

        if not request_id_post:
            messages.error(request, "Invalid request ID")
            return redirect("dealer_history")

        approved_request = get_object_or_404(
            ScrapRequest,
            id=request_id_post,
            requested_by=request.user,
            status="approved"
        )

        # prevent double payment
        if approved_request.is_paid:
            return redirect("dealer_history")

        approved_request.is_paid = True
        approved_request.save()

        # 💰 CREDIT SELLER
        seller = approved_request.scrap.seller

        commission = amount * Decimal("0.05")
        seller_amount = amount - commission

        wallet, _ = Wallet.objects.get_or_create(user=seller)
        wallet.balance += seller_amount
        wallet.save()

        messages.success(request, "Payment successful!")

        return redirect("dealer_history")

    return render(
        request,
        "dealer/dealer_scrap_payment.html",
        {
            "approved_request": approved_request,
            "amount": amount,
        }
    )

from decimal import Decimal
from scrap.models import Wallet, WalletTransaction

@csrf_exempt
@login_required
def dealer_scrap_payment_success(request):

    request_id = request.POST.get("request_id")

    if not request_id:
        return HttpResponse("ERROR: request_id missing")

    scrap_request = get_object_or_404(
        ScrapRequest,
        id=request_id,
        requested_by=request.user
    )

    # ✅ already paid check
    if scrap_request.is_paid:
        return redirect("dealer_history")

    scrap = scrap_request.scrap

    amount = Decimal(scrap_request.requested_weight) * Decimal(scrap.price_per_kg)

    # ===============================
    # ✅ MARK PAID
    # ===============================
    scrap_request.is_paid = True
    scrap_request.save()

    # ===============================
    # 💰 WALLET CREDIT (IMPORTANT)
    # ===============================
    seller = scrap.seller

    commission = amount * Decimal("0.05")
    seller_amount = amount - commission

    wallet, _ = Wallet.objects.get_or_create(user=seller)

    wallet.balance += seller_amount
    wallet.save()

    # optional but BEST
    WalletTransaction.objects.create(
        user=seller,
        amount=seller_amount,
        transaction_type="credit",
        description=f"Scrap sold ({scrap.category})"
    )

    messages.success(request, "Payment successful!")

    return redirect("dealer_history")

from .models import Wallet

@login_required
def wallet_view(request):

    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    withdrawals = WithdrawRequest.objects.filter(
        user=request.user
    ).order_by("-created_at")

    # 🔥 ADD THIS
    transactions = WalletTransaction.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "wallet/wallet.html",
        {
            "wallet": wallet,
            "withdrawals": withdrawals,
            "transactions": transactions
        }
    )

from .models import WithdrawRequest
from django.contrib import messages
from decimal import Decimal

@login_required
def withdraw_request(request):

    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if request.method == "POST":

        amount = Decimal(request.POST.get("amount"))

        if amount > wallet.balance:
            messages.error(request, "Insufficient wallet balance")
            return redirect("wallet")

        WithdrawRequest.objects.create(
            user=request.user,
            amount=amount
        )

        wallet.balance -= amount
        wallet.save()

        WalletTransaction.objects.create(
            user=request.user,
            amount=amount,
            transaction_type="debit",
            description="Withdraw request"
        )

        messages.success(request, "Withdraw request submitted")

        return redirect("wallet")
    
from .models import BankDetails


@login_required
def bank_details(request):

    bank, _ = BankDetails.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        bank.account_holder_name = request.POST.get(
            "account_holder_name"
        )

        bank.bank_account_number = request.POST.get(
            "bank_account_number"
        )

        bank.ifsc_code = request.POST.get(
            "ifsc_code"
        )

        bank.upi_id = request.POST.get(
            "upi_id"
        )

        bank.save()

        messages.success(
            request,
            "Bank details saved successfully"
        )

        return redirect("wallet")

    return render(
        request,
        "wallet/bank_details.html",
        {
            "bank": bank
        }
    )

from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def admin_withdraw_requests(request):

    requests = WithdrawRequest.objects.select_related(
        "user"
    ).order_by("-created_at")

    return render(
        request,
        "admin/withdraw_requests.html",
        {
            "requests": requests
        }
    )

@staff_member_required
def approve_withdraw(request, request_id):

    withdraw = get_object_or_404(
        WithdrawRequest,
        id=request_id
    )

    withdraw.status = "paid"
    withdraw.save()

    messages.success(
        request,
        "Withdraw marked as paid"
    )

    return redirect("admin_withdraw_requests")

@staff_member_required
def reject_withdraw(request, request_id):

    withdraw = get_object_or_404(
        WithdrawRequest,
        id=request_id
    )

    withdraw.status = "rejected"
    withdraw.save()

    messages.warning(
        request,
        "Withdraw request rejected"
    )

    return redirect("admin_withdraw_requests")

from django.utils import timezone


@staff_member_required
def payout_withdraw(request, request_id):

    withdraw = get_object_or_404(
        WithdrawRequest,
        id=request_id
    )

    if request.method == "POST":

        reference = request.POST.get("reference")

        withdraw.status = "paid"
        withdraw.payout_reference = reference
        withdraw.paid_at = timezone.now()

        withdraw.save()

        messages.success(
            request,
            "Payout completed successfully"
        )

        return redirect("admin_withdraw_requests")

    return render(
        request,
        "admin/payout_form.html",
        {
            "withdraw": withdraw
        }
    )

@login_required
def mark_scrap_picked(request, request_id):

    req = get_object_or_404(ScrapRequest, id=request_id)

    if req.scrap.seller != request.user:
        return redirect("my_scrap_requests")

    req.pickup_status = "picked"
    req.save()

    messages.success(request, "Scrap marked as picked up")

    return redirect("my_scrap_requests")

@login_required
def add_pickup_details(request, request_id):

    req = get_object_or_404(ScrapRequest, id=request_id)

    if req.requested_by != request.user:
        return redirect("scrap_list")

    if request.method == "POST":

        req.pickup_time = request.POST.get("pickup_time")
        req.pickup_date = request.POST.get("pickup_date")
        req.pickup_contact = request.POST.get("pickup_contact")

        req.save()

        messages.success(request, "Pickup details submitted successfully")

        return redirect("my_requests")

    return render(
        request,
        "scrap/add_pickup_details.html",
        {"req": req}
    )

@login_required
def pickup_history(request):

    pickups = ScrapRequest.objects.filter(
        scrap__seller=request.user
    ).order_by("-id")

    return render(
        request,
        "scrap/pickup_history.html",
        {"pickups": pickups}
    )

@login_required
def select_category(request):
    return render(request, "scrap/select_category.html")
# ......................................................................................................
def get_market_price(category):

    price_map = {
        "iron": 28,
        "aluminium": 120,
        "copper": 650,
        "plastic": 15,
        "bottle": 18,
        "polythene": 10,
        "newspaper": 20,
        "books": 18,
        "cardboard": 12,
    }

    return price_map.get(category.lower(), 20)

@login_required
def wishlist_page(request):

    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related("artwork", "artwork__artist")

    return render(
        request,
        "artist/wishlist.html",
        {"wishlist_items": wishlist_items}
    )

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

@login_required
def delete_scrap(request, scrap_id):

    scrap = get_object_or_404(Scrap, id=scrap_id)

    # 🔥 SECURITY: sirf owner delete kare
    if scrap.seller == request.user:
        scrap.delete()

    return redirect("my_scraps")

# .................................................................................
from .ai_fixed_data import SCRAP_AI_DATA

def get_scrap_price(category):

    category = category.lower()

    for key in SCRAP_AI_DATA:
        if key in category or category in key:
            return SCRAP_AI_DATA[key]
        
    return {
        "price": 25,
        "min": 15,
        "max": 50,
        "demand": "Average",
        "resale": "40%"
    }

from django.contrib.admin.views.decorators import staff_member_required
from .models import BankDetails

@staff_member_required
def admin_bank_details(request):

    query = request.GET.get("q", "")

    banks = BankDetails.objects.select_related("user")

    if query:
        banks = banks.filter(user__username__icontains=query)

    banks = banks.order_by("-created_at")

    return render(
        request,
        "admin/admin_bank_details.html",
        {
            "banks": banks,
            "query": query
        }
    )
@login_required
def scrap_payment_success(request):

    request_id = request.GET.get("request_id")

    if not request_id:
        return redirect("approved_scraps")

    scrap_request = get_object_or_404(
        ScrapRequest,
        id=request_id,
        requested_by=request.user
    )

    if scrap_request.is_paid:
        return redirect("convert_to_artwork", request_id=request_id)

    scrap = scrap_request.scrap

    amount = Decimal(scrap_request.requested_weight) * Decimal(scrap.price_per_kg)

    # ✅ MARK PAID
    scrap_request.is_paid = True
    scrap_request.save()

    # 💰 WALLET CREDIT
    seller = scrap.seller

    commission = amount * Decimal("0.05")
    seller_amount = amount - commission

    wallet, _ = Wallet.objects.get_or_create(user=seller)
    wallet.balance += seller_amount
    wallet.save()

    WalletTransaction.objects.create(
        user=seller,
        amount=seller_amount,
        transaction_type="credit",
        description=f"Artist paid for scrap ({scrap.category})"
    )

    messages.success(request, "Payment successful!")

    return redirect("pickup_details", request_id=request_id)

import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import ScrapRequest

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def create_checkout_session(request, request_id):

    scrap_request = get_object_or_404(ScrapRequest, id=request_id)

    amount = int(scrap_request.scrap.price_per_kg * scrap_request.requested_weight * 100)

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'inr',
                'product_data': {
                    'name': 'Scrap Payment',
                },
                'unit_amount': amount,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri(f"/scrap/payment-success/{request_id}/"),
        cancel_url=request.build_absolute_uri("/scrap/"),
    )

    return redirect(session.url)

@login_required
def stripe_payment_success(request, request_id):

    scrap_request = get_object_or_404(
        ScrapRequest,
        id=request_id,
        requested_by=request.user
    )

    # already paid check
    if not scrap_request.is_paid:
        scrap_request.is_paid = True
        scrap_request.save()

    return redirect("pickup_details", request_id=request_id)


from decimal import Decimal
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
import stripe

from scrap.models import ScrapRequest, Wallet, WalletTransaction

stripe.api_key = settings.STRIPE_SECRET_KEY


# ===============================
# ARTIST STRIPE PAYMENT
# ===============================
@login_required
def artist_stripe_pay(request, request_id):
    print("🔥 HIT artist_stripe_pay")
    
    approved_request = get_object_or_404(
        ScrapRequest,
        id=request_id,
        requested_by=request.user,
        status="approved"
    )

    scrap = approved_request.scrap

    amount = Decimal(approved_request.requested_weight) * Decimal(scrap.price_per_kg)

    # 🔥 FIX: minimum Stripe amount
    amount_paise = int(amount * 100)
    if amount_paise < 50:
        amount_paise = 50

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'inr',
                    'product_data': {
                        'name': scrap.category,
                    },
                    'unit_amount': amount_paise,
                },
                'quantity': 1,
            }],
            mode='payment',

            success_url=f"http://127.0.0.1:8000/scrap/artist/payment-success/?request_id={approved_request.id}",
            cancel_url="http://127.0.0.1:8000/scrap/artist/approved-scraps/",
        )

        return redirect(session.url)

    except Exception as e:
        print("Stripe Error:", e)
        messages.error(request, "Payment failed. Try again.")
        return redirect("approved_scraps")

@login_required
def artist_payment_success(request):

    request_id = request.GET.get("request_id")

    if not request_id:
        messages.error(request, "Invalid request")
        return redirect("approved_scraps")

    approved_request = get_object_or_404(
        ScrapRequest,
        id=request_id,
        requested_by=request.user,
        status="approved"
    )

    # 🔎 Already paid check
    if approved_request.is_paid:
        messages.warning(request, "Already paid")
        return redirect("approved_scraps")

    scrap = approved_request.scrap

    amount = Decimal(approved_request.requested_weight) * Decimal(scrap.price_per_kg)

    # ===============================
    # 💰 CREDIT SELLER WALLET
    # ===============================
    seller = scrap.seller

    commission = amount * Decimal("0.05")
    seller_amount = amount - commission

    wallet, _ = Wallet.objects.get_or_create(user=seller)
    wallet.balance += seller_amount
    wallet.save()

    WalletTransaction.objects.create(
        user=seller,
        amount=seller_amount,
        transaction_type="credit",
        description=f"Scrap sold: {scrap.category}"
    )

    # ===============================
    # UPDATE REQUEST
    # ===============================
    approved_request.is_paid = True
    approved_request.save()

    messages.success(request, "🎉 Payment successful!")

    return redirect("pickup_details", request_id=request_id)

@login_required
def dealer_payment_success(request):

    request_id = request.GET.get("request_id")

    if not request_id:
        return redirect("sanctioned_scraps")

    scrap_request = get_object_or_404(
        ScrapRequest,
        id=request_id,
        requested_by=request.user
    )

    if scrap_request.is_paid:
        return redirect("dealer_history")

    scrap = scrap_request.scrap

    amount = Decimal(scrap_request.requested_weight) * Decimal(scrap.price_per_kg)

    # ✅ mark paid
    scrap_request.is_paid = True
    scrap_request.save()

    # 💰 wallet update
    seller = scrap.seller

    commission = amount * Decimal("0.05")
    seller_amount = amount - commission

    wallet, _ = Wallet.objects.get_or_create(user=seller)
    wallet.balance += seller_amount
    wallet.save()

    WalletTransaction.objects.create(
        user=seller,
        amount=seller_amount,
        transaction_type="credit",
        description=f"Dealer paid for scrap ({scrap.category})"
    )

    messages.success(request, "Payment successful!")

    return redirect("dealer_history")


@login_required
def dealer_stripe_pay(request, request_id):

    approved_request = get_object_or_404(
        ScrapRequest,
        id=request_id,
        requested_by=request.user,
        status="approved"
    )

    scrap = approved_request.scrap

    amount = Decimal(approved_request.requested_weight) * Decimal(scrap.price_per_kg)

    amount_paise = int(amount * 100)
    if amount_paise < 50:
        amount_paise = 50

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'inr',
                'product_data': {
                    'name': scrap.category,
                },
                'unit_amount': amount_paise,
            },
            'quantity': 1,
        }],
        mode='payment',

        success_url=f"http://127.0.0.1:8000/scrap/dealer/payment-success/?request_id={approved_request.id}",
        cancel_url="http://127.0.0.1:8000/scrap/sanctioned-scraps/",
    )

    return redirect(session.url)