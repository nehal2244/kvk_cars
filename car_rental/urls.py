from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from car_rental import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('browse_cars/', views.browse_cars, name='browse_cars'),
    path('car/<int:pk>/', views.car_detail, name='car_detail'),
    path('pay-online/', views.pay_online, name='pay_online'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('about/', views.about, name='about'),

    # Booking URLs
    path('cars/book/<int:pk>/', views.car_book, name='car_book'),
    path('booking-success/<int:booking_id>/', views.booking_success, name='booking_success'),
    path('booking_pending/', views.booking_pending, name='booking_pending'),

    # Approval URL expects UUID token
    path('approve_booking/<uuid:token>/', views.approve_booking, name='approve_booking'),

    # API
    path('api/get_dynamic_prices/', views.get_dynamic_prices, name='get_dynamic_prices'),
    path('get_dynamic_prices/', views.get_dynamic_prices),  # optional alias


    path('contactus/', views.contactus, name='contactus'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
