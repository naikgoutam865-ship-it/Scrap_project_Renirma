from scrap.models import Wallet, WalletTransaction
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings

from artist.models import Artwork
from orders.models import ArtworkOrder
import razorpay


# ========================================
# BUY PRODUCT WITH RAZORPAY
# ========================================
@login_required
def buy_product(request, artwork_id):

    artwork = get_object_or_404(Artwork, id=artwork_id)

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    if request.method == "POST":

        # 🧮 Quantity user se lo
        quantity = int(request.POST.get("quantity", 1))

        # ❗ Safety check (available quantity se zyada na ho)
        if quantity > artwork.quantity:
            messages.error(request, "Requested quantity exceeds available stock.")
            return redirect("artwork_detail", artwork_id=artwork.id)

        # 💰 Total price calculate
        total_price = float(artwork.price) * quantity

        # Razorpay ke liye paisa convert
        amount_paise = int(total_price * 100)

        print("DEBUG TOTAL:", amount_paise)

        razorpay_order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": 1
        })

        # 🧾 Order save karo
        ArtworkOrder.objects.create(
            artwork=artwork,
            buyer=request.user,
            quantity=quantity,   # 👈 NEW
            status="Pending",
            razorpay_order_id=razorpay_order["id"],
            payment_status="pending",
            is_sold=False
        )

        return render(
            request,
            "orders/payment_checkout.html",
            {
                "artwork": artwork,
                "razorpay_order_id": razorpay_order["id"],
                "razorpay_key": settings.RAZORPAY_KEY_ID,
                "amount": total_price,
                "quantity": quantity
            }
        )

    return render(
        request,
        "orders/buy_artwork.html",
        {"artwork": artwork}
    )


# ========================================
# ARTWORK PAYMENT SUCCESS
# ========================================
@login_required
def payment_success(request):

    if request.method == "POST":

        payment_id = request.POST.get("razorpay_payment_id")
        order_id = request.POST.get("razorpay_order_id")
        signature = request.POST.get("razorpay_signature")

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        # 🔐 VERIFY PAYMENT
        try:
            client.utility.verify_payment_signature({
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature
            })
        except:
            messages.error(request, "Payment verification failed!")
            return redirect("artwork_marketplace")

        # GET ORDER
        order = ArtworkOrder.objects.filter(
            razorpay_order_id=order_id
        ).first()

        if not order:
            messages.error(request, "Order not found.")
            return redirect("artwork_marketplace")

        artwork = order.artwork

        # 🔎 CHECK IF ORDER ALREADY PAID
        if order.payment_status == "paid":
            messages.warning(request, "Payment already processed.")
            return redirect("order_history")

        # ===============================
        # REDUCE ARTWORK QUANTITY
        # ===============================
        if artwork.quantity >= order.quantity:
            artwork.quantity -= order.quantity
        else:
            artwork.quantity = 0

        # Hide artwork when stock finished
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
        # CREDIT ARTIST WALLET
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
        order.payment_id = payment_id
        order.payment_status = "paid"
        order.status = "Sold"
        order.commission_amount = float(commission)
        order.artist_amount = float(artist_amount)
        order.is_sold = True
        order.save()

        messages.success(request, "🎉 Payment successful!")
        return redirect("order_history")

    return redirect("artwork_marketplace")


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
