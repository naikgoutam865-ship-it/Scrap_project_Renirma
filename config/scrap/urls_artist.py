from django.urls import path

from . import views

# from config.accounts import views
from .views_artist import artist_scrap_list

urlpatterns = [
    path("artist/scraps/", artist_scrap_list, name="artist_scrap_list"),
    path("scrap-payment/<int:request_id>/", views.scrap_payment, name="scrap_payment"),
    path("convert/<int:request_id>/", views.convert_to_artwork, name="convert_to_artwork"),

]
