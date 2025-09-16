from django.urls import path
from django.contrib import admin

from . import views

urlpatterns = [
    # Basic site pages
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),

    # User and coupon dashboards
    path('dash/', views.dash, name='dash'),
    path('payment/', views.payment, name='payment'),

    # User authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),

    # Coupon management
    path('gen/', views.gen, name='gen'),
    path('download/', views.download, name='download'),
    path('delete-all-coupons/', views.delete_all_coupons, name='delete_all_coupons'),

    # Prize management
    path('manage-prizes/', views.manage_prizes, name='manage_prizes'),
    path('prize/', views.manage_prizes, name='manage_prizes'),  # optional alias
    path('delete-prize/<int:prize_id>/', views.delete_prize, name='delete_prize'),
    path('prize/', views.manage_prizes, name='prize'),
    path('admin-delete-coupons/<int:user_id>/', views.delete_all_coupons, name='admin_delete_coupons'),
    path('admin/', admin.site.urls),
    # Spin & Win and QR code
    path('spin/', views.spin_and_win, name='spin_and_win'),
    path('qr/', views.qr, name='qr'),
    path('update-prize/<int:prize_id>/', views.update_prize, name='update_prize'),


    # Other pages
    path('customer/', views.customer, name='customer'),

    # AJAX endpoints
    path('validate_coupon/', views.validate_coupon, name='validate_coupon'),
    path('redeem_coupon/', views.redeem_coupon, name='redeem_coupon'),
]
