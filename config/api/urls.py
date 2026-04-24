from django.urls import path
from .views import scrap_list

urlpatterns = [
    path('scraps/', scrap_list),
]
