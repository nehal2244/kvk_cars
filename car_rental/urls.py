from django.contrib import admin
from django.urls import path, include
from car_rental import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.index, name='index'),
    path("browse_cars/", views.browse_cars, name='browse_cars'),
    path('car/<int:pk>/', views.car_detail, name='car_detail'),    # for view details
    path('car/<int:pk>/book/', views.car_book, name='car_book'),  
    path('pay-online/', views.pay_online, name='pay_online'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('about/' , views.about , name='about'),
    
]
