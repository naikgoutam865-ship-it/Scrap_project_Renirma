from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from scrap.models import Scrap


@login_required
def artist_scrap_list(request):
    scraps = Scrap.objects.filter(is_available=True)

    return render(
        request,
        "artist/artist_scrap_list.html",
        {
            "scraps": scraps
        }
    )
