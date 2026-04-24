
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import logout
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from django.core.cache import cache

def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        # 🔐 Track login attempts
        attempts_key = f"login_attempts_{username}"
        attempts = cache.get(attempts_key, 0)

        # 🚫 Block after 5 tries
        if attempts >= 5:
            messages.error(request, "Too many failed attempts. Try again after 10 minutes.")
            return redirect("login")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # reset attempts after success
            cache.delete(attempts_key)

            return redirect("home")

        else:
            attempts += 1
            cache.set(attempts_key, attempts, timeout=600)  # block 10 min

            messages.error(request, "Invalid username or password")
            return redirect("login")

    return render(request, "accounts/login.html")



from django.contrib.auth import get_user_model

User = get_user_model()

from .forms import RegisterForm
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives

def register_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        language = request.POST.get("language", "en")

        # 🔐 Password strength check
        try:
            validate_password(password)
        except ValidationError as e:
            messages.error(request, " ".join(e.messages))
            return redirect("register")

        role = request.POST.get("role")

        # ✅ Terms check
        if not request.POST.get("terms"):
            messages.error(request, "You must accept Terms & Conditions")
            return redirect("register")

        # ✅ Username validation
        if not username:
            return HttpResponse("Username missing")

        # ✅ Duplicate user check
        if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
            messages.error(request, "You are already registered. Please login.")
            return redirect("login")

        # ✅ Create user (inactive until email verified)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        user.role = role
        user.language = language
        user.is_active = False   # 🔥 EMAIL VERIFY REQUIRED
        user.save()

        # 🔐 EMAIL VERIFICATION LINK
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        verify_link = settings.SITE_URL + reverse(
            "verify_email",
            args=[uid, token]
        )


        subject = "Verify your ReNirma account"

        text_content = f"Hi {username}, Click this link to verify your account: {verify_link}"

        html_content = f"""
        <p>Hi {username},</p>

        <p>Please verify your account by clicking the button below:</p>

        <p>
        <a href="{verify_link}" style="
        background:#0d6efd;
        color:white;
        padding:10px 18px;
        text-decoration:none;
        border-radius:6px;
        font-weight:bold;">
        Verify Account
        </a>
        </p>

        <p>If button not working, copy this link:</p>
        <p>{verify_link}</p>
        """

        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.EMAIL_HOST_USER,
            [email]
        )

        msg.attach_alternative(html_content, "text/html")
        msg.send()

        messages.success(
            request,
            "Account created! Please check your email to verify before login."
        )

        return redirect("login")

    return render(request, "accounts/register.html")

from scrap.models import Scrap, ScrapRequest
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from orders.models import ArtworkOrder
from artist.models import Artwork
from django.db.models import Sum
from django.utils import translation

@login_required
def dashboard_view(request):

    translation.activate(request.user.language)
    
    user = request.user

    if user.is_superuser:
        return redirect("/admin/")

    # =========================
    # USER DASHBOARD
    # =========================
    if user.role == "user":

        total_scraps = Scrap.objects.filter(
            seller=user
        ).count()

        requests_received = ScrapRequest.objects.filter(
            scrap__seller=user
        ).count()

        orders_count = ScrapRequest.objects.filter(
            scrap__seller=request.user,
            status__in=["approved", "converted"]
        ).count()
        
        # ===== Progress Bar Safe Calculation =====
        max_value = max(total_scraps, requests_received, orders_count, 1)

        scrap_percent = (total_scraps / max_value) * 100
        request_percent = (requests_received / max_value) * 100
        order_percent = (orders_count / max_value) * 100


        # 🔥 NEW ANALYTICS
        from scrap.models import Wishlist

        wishlist_count = Wishlist.objects.filter(
            user=user
        ).count()

        total_orders = ArtworkOrder.objects.filter(
            buyer=user,
            status="paid"
        ).count()

        total_spent = ArtworkOrder.objects.filter(
            buyer=user,
            status="paid"
        ).aggregate(total=Sum("artist_amount"))["total"] or 0

        context = {
            "total_scraps": total_scraps,
            "requests_received": requests_received,
            "orders_count": orders_count,
            "wishlist_count": wishlist_count,
            "total_orders": total_orders,
            "total_spent": total_spent,

            "scrap_percent": scrap_percent,
            "request_percent": request_percent,
            "order_percent": order_percent,
        }

        return render(
            request,
            "dashboard/user_dashboard.html",
            context
        )

    # =========================
    # DEALER DASHBOARD
    # =========================
    
    if user.role == "dealer":

        available_scraps = Scrap.objects.filter(
            available_weight__gt=0
        ).count()

        requests_sent = ScrapRequest.objects.filter(
            requested_by=user
        ).count()

        approved_deals = ScrapRequest.objects.filter(
            requested_by=user,
            status="approved"
        ).count()

        total_purchase_value = ArtworkOrder.objects.filter(
            buyer=user,
            payment_status="paid"
        ).aggregate(
            total=Sum("artist_amount")
        )["total"] or 0

        recent_requests = ScrapRequest.objects.filter(
        requested_by=user
        ).order_by("-requested_at")[:5]

        context = {
            "available_scraps": available_scraps,
            "requests_sent": requests_sent,
            "approved_deals": approved_deals,
            "total_purchase_value": total_purchase_value,
            "recent_requests": recent_requests
        }

        return render(
            request,
            "dashboard/dealer_dashboard.html",
            context
        )

    # =========================
    # ARTIST DASHBOARD
    # =========================
    if user.role == "artist":

        
        artworks = Artwork.objects.filter(artist=user)

        total_artworks = artworks.count()

        # ✅ Sold artworks
        sold_artworks = ArtworkOrder.objects.filter(
            artwork__artist=user,
            payment_status="paid"
        ).count()

        # ✅ Pending artworks (active but not sold)
        pending_artworks = artworks.filter(is_active=True).count()

        # ✅ Total earnings

        total_earnings = ArtworkOrder.objects.filter(
            artwork__artist=request.user,
            payment_status="paid"
        ).aggregate(
            total=Sum("artist_amount")
        )["total"] or 0

        context = {
            "total_artworks": total_artworks,
            "sold_artworks": sold_artworks,
            "pending_artworks": pending_artworks,
            "total_earnings": total_earnings,
        }

        return render(
            request,
            "dashboard/artist_dashboard.html",
            context
        )


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
def artist_panel(request):
    return render(request, "dashboard/artist_panel.html")

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum, Count

from orders.models import ArtworkOrder
from scrap.models import Wishlist

from artist.models import Artwork


def terms_view(request):
    return render(request, "accounts/terms.html")


from django.utils.http import urlsafe_base64_decode

def verify_email(request, uidb64, token):

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Email verified! You can login now.")
        return redirect("login")

    messages.error(request, "Verification link invalid or expired")
    return redirect("register")
