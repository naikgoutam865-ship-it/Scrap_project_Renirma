from scrap.models import Wallet, WalletTransaction
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from artist.models import Artwork
from orders.models import ArtworkOrder


# ========================================
# BUY PRODUCT (NO PAYMENT GATEWAY)
# ========================================
@login_required
def buy_product(request, artwork_id):

    artwork = get_object_or_404(Artwork, id=artwork_id)

    if request.method == "POST":

        quantity = int(request.POST.get("quantity", 1))

        if quantity > artwork.quantity:
            messages.error(request, "Requested quantity exceeds available stock.")
            return redirect("artwork_detail", artwork_id=artwork.id)

        total_price = float(artwork.price) * quantity
        if total_price < 50:
            messages.error(request, "Minimum order amount is ₹50")
            return redirect("artwork_detail", artwork_id=artwork.id)

        order = ArtworkOrder.objects.create(
            artwork=artwork,
            buyer=request.user,
            quantity=quantity,
            status="Pending",
            payment_status="pending",
            is_sold=False
        )

        import stripe
        from django.conf import settings
        stripe.api_key = settings.STRIPE_SECRET_KEY

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'inr',
                    'product_data': {
                        'name': artwork.title,
                    },
                    'unit_amount': int(total_price * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url = f"http://127.0.0.1:8000/orders/payment-success/?order_id={order.id}",
            cancel_url='http://127.0.0.1:8000/orders/cancel/',
        )

        return redirect(session.url)

    return render(request, "orders/buy_artwork.html", {"artwork": artwork})


# ========================================
# FAKE PAYMENT SUCCESS (DUMMY)
# ========================================
@login_required
def payment_success(request):

    # ✅ Stripe se order_id GET me aata hai
    order_id = request.GET.get("order_id")

    if not order_id:
        return redirect("artwork_marketplace")

    order = get_object_or_404(ArtworkOrder, id=order_id)
    artwork = order.artwork

    # 🔎 Already paid check
    if order.payment_status == "paid":
        messages.warning(request, "Payment already processed.")
        return redirect("order_history")

    # ===============================
    # REDUCE STOCK
    # ===============================
    if artwork.quantity >= order.quantity:
        artwork.quantity -= order.quantity
    else:
        artwork.quantity = 0

    if artwork.quantity <= 0:
        artwork.is_active = False

    artwork.save()

    # ===============================
    # CALCULATE COMMISSION
    # ===============================
    total_price = Decimal(str(artwork.price)) * Decimal(str(order.quantity))

    commission = total_price * Decimal("0.05")
    artist_amount = total_price - commission

    # ===============================
    # CREDIT WALLET
    # ===============================
    wallet, _ = Wallet.objects.get_or_create(user=artwork.artist)

    wallet.balance += artist_amount
    wallet.save()

    WalletTransaction.objects.create(
        user=artwork.artist,
        amount=artist_amount,
        transaction_type="credit",
        description=f"Artwork sold: {artwork.title} (x{order.quantity})"
    )

    # ===============================
    # UPDATE ORDER
    # ===============================
    order.payment_status = "paid"
    order.status = "Sold"
    order.commission_amount = float(commission)
    order.artist_amount = float(artist_amount)
    order.is_sold = True
    order.save()

    messages.success(request, "🎉 Payment successful!")
    return redirect("order_history")

# ========================================
# ORDER HISTORY
# ========================================
@login_required
def order_history(request):

    orders = ArtworkOrder.objects.filter(
        buyer=request.user
    ).select_related("artwork").order_by("-ordered_at")

    return render(
        request,
        "orders/order_history.html",
        {"orders": orders}
    )