from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.add_scrap, name='add_scrap'),
    path('my/', views.my_scraps, name='my_scraps'),
    path('list/', views.scrap_list, name='scrap_list'),
    path('request/<int:scrap_id>/', views.request_scrap, name='request_scrap'),

    path(
        "request/<int:request_id>/<str:status>/",
        views.update_request_status,
        name="update_request_status"
    ),
    path("my-requests/", views.my_scrap_requests, name="my_scrap_requests"),
    path("my-sent-requests/", views.my_requests, name="my_requests"),

    path(
        "artist/scraps/",
        views.artist_scrap_list,
        name="artist_scrap_list"
    ),

    path(
        "artist/request/<int:scrap_id>/",
        views.artist_request_scrap,
        name="artist_request_scrap"
    ),

    path(
    "artist/approved-scraps/",
    views.approved_scraps,
    name="approved_scraps"
    ),

    path(
    "artist/convert/<int:request_id>/",
    views.convert_to_artwork,
    name="convert_to_artwork"
    ),

    path(
    "artist/approved-scraps/",
    views.artist_approved_scraps,
    name="artist_approved_scraps"
    ),

    path(
    "artist/my-artworks/",
    views.my_artworks,
    name="my_artworks"
    ),

    path(
    "artist/convert/<int:request_id>/",
    views.convert_to_artwork,
    name="convert_to_art"
    ),

    path(
    "artworks/",
    views.artwork_marketplace,
    name="artwork_marketplace"
    ),

    path("artist/scrap-payment/<int:request_id>/", views.scrap_payment, name="scrap_payment"),
    path("artist/scrap-payment-success/", views.scrap_payment_success, name="scrap_payment_success"),
    path("artwork/<int:artwork_id>/", views.artwork_detail, name="artwork_detail"),
    path("wishlist/<int:artwork_id>/", views.toggle_wishlist, name="toggle_wishlist"),
    path("my-wishlist/", views.my_wishlist, name="my_wishlist"),
    path("admin/finance/", views.admin_finance_dashboard, name="admin_finance_dashboard"),
    path("admin/settle/<int:order_id>/",
        views.mark_order_settled,
        name="mark_order_settled"),

    path("reviews/", views.all_reviews, name="all_reviews"),
    path("reviews/add/", views.add_review, name="add_review"),
    
    path("notify-me/", views.create_scrap_alert, name="create_scrap_alert"),
    path("ai-price/", views.ai_price, name="ai_price"),
    path(
        "sanctioned-scraps/",
        views.sanctioned_scraps,
        name="sanctioned_scraps"
    ),
    path(
        "dealer-history/",
        views.dealer_history,
        name="dealer_history"
    ),

    path(
        "dealer/payment/<int:request_id>/",
        views.dealer_scrap_payment,
        name="dealer_scrap_payment"
    ),

    path(
        "dealer/payment-success/",
        views.dealer_scrap_payment_success,
        name="dealer_scrap_payment_success"
    ),
    path(
        "wallet/",
        views.wallet_view,
        name="wallet"
    ),

    path(
        "withdraw/",
        views.withdraw_request,
        name="withdraw_request"
    ),

    path(
        "bank-details/",
        views.bank_details,
        name="bank_details"
    ),

    path(
        "admin/withdraw-requests/",
        views.admin_withdraw_requests,
        name="admin_withdraw_requests"
    ),

    path(
        "admin/withdraw-approve/<int:request_id>/",
        views.approve_withdraw,
        name="approve_withdraw"
    ),

    path(
        "admin/withdraw-reject/<int:request_id>/",
        views.reject_withdraw,
        name="reject_withdraw"
    ),

    path(
        "admin/payout/<int:request_id>/",
        views.payout_withdraw,
        name="payout_withdraw"
    ),

    path(
        "pickup-complete/<int:request_id>/",
        views.mark_scrap_picked,
        name="pickup_complete",
    ),
    path(
        "pickup-details/<int:request_id>/",
        views.add_pickup_details,
        name="pickup_details",
    ),

    path(
        "pickup-history/",
        views.pickup_history,
        name="pickup_history",
    ),

    path("select-category/",views.select_category, name="select_category"),

    path("wishlist/", views.wishlist_page, name="wishlist"),
    
    path("delete-scrap/<int:scrap_id>/", views.delete_scrap, name="delete_scrap"),

    path(
        "admin/bank-details/",
        views.admin_bank_details,
        name="admin_bank_details"
    ),

]
