"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from scrap.views import artwork_marketplace
from django.contrib import admin
from django.urls import path, include
from scrap.views import home   # ✅ real home view (home.html)

urlpatterns = [

    # 🏠 HOME PAGE
    path("", home, name="home"),

    # ADMIN
    path("admin/", admin.site.urls),

    # APPS
    path("api/", include("api.urls")),
    path("accounts/", include("accounts.urls")),
    path("scrap/", include("scrap.urls")),
    path("artist/", include("scrap.urls_artist")),
    path("orders/", include("orders.urls")),
    path("artwork-marketplace/", artwork_marketplace, name="artwork_marketplace"),
    path("artist/", include("artist.urls")),
    path("assistant/", include("chatbot.urls")),

]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler403 = "config.views.custom_403"
handler404 = "config.views.custom_404"
handler500 = "config.views.custom_500"

from django.contrib.auth import views as auth_views

path(
    "password-reset/",
    auth_views.PasswordResetView.as_view(
        template_name="accounts/password_reset.html",
        email_template_name="accounts/password_reset_email.html",
        success_url="/accounts/password-reset/done/",
        extra_email_context={"domain":"c1f8-2409-4062-4e16-c8b3-2da6-e686-4bc0-858c.ngrok-free.app"}
    ),
    name="password_reset",
),
