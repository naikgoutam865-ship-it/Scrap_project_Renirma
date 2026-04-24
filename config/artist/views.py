from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ArtworkForm

from math import radians, cos, sin, asin, sqrt
def calculate_distance(lat1, lon1, lat2, lon2):

    # degrees → radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # difference
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    # haversine formula
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    # earth radius (km)
    r = 6371

    return c * r

@login_required
def upload_artwork(request):
    if request.method == "POST":
        form = ArtworkForm(request.POST, request.FILES)
        if form.is_valid():
            artwork = form.save(commit=False)
            artwork.artist = request.user
            artwork.save()
            return redirect("artwork_marketplace")
    else:
        form = ArtworkForm()

    return render(request, "artist/upload_artwork.html", {"form": form})

from orders.models import ArtworkOrder

@login_required
def sold_artworks(request):
    orders = ArtworkOrder.objects.select_related(
        "artwork",
        "buyer"
    ).filter(
        artwork__artist=request.user,
        is_sold=True
    ).order_by("-ordered_at")

    return render(
        request,
        "artist/sold_artworks.html",
        {"orders": orders}
    )

from django.db.models import Sum
from artist.models import Artwork
from orders.models import ArtworkOrder

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from artist.models import Artwork


@login_required
def sell_artwork(request):

    if request.method == "POST":

        title = request.POST.get("title")
        description = request.POST.get("description")
        price = request.POST.get("price")
        image = request.FILES.get("image")

        if not title or not price:
            messages.error(request, "Title and price required.")
            return redirect("sell_artwork")

        Artwork.objects.create(
            artist=request.user,
            title=title,
            description=description,
            price=float(price),
            image=image,
            is_active=True,
        )

        messages.success(request, "Artwork added to marketplace!")
        return redirect("artwork_marketplace")

    return render(request, "artist/sell_artwork.html")

from django.shortcuts import get_object_or_404

@login_required
def delete_artwork(request, art_id):

    art = get_object_or_404(Artwork, id=art_id)

    # 🔐 security
    if art.artist == request.user:
        art.delete()

    return redirect("artwork_marketplace")


