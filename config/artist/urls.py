from django.urls import path
from . import views

urlpatterns = [

    path("upload-artwork/", views.upload_artwork, name="upload_artwork"),

    path("sold-artworks/", views.sold_artworks, name="sold_artworks"),

    path("sell-artwork/", views.sell_artwork, name="sell_artwork"),

    path("delete-artwork/<int:art_id>/", views.delete_artwork, name="delete_artwork"),

]