from django.contrib import admin 
from car_rental.models import Car, Booking

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'car_type',
        'seating_capacity',
        'transmission',
        'fuel_type',
        'free_km_price',
        'unlimited_km_price',
        'free_kms',
        'extra_km_charge',
    ]
    list_filter = ['car_type', 'transmission', 'fuel_type']
    search_fields = ['name']

    # 👇 Add the image fields to the admin form
    fields = [
        'name',
        'car_type',
        'seating_capacity',
        'transmission',
        'fuel_type',
        'free_km_price',
        'free_kms',
        'unlimited_km_price',
        'extra_km_charge',
        'price_100km',
        'price_200km',
        'price_300km',
        'image_file',   # Local upload
        'image_url',    # External image
    ]

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['car', 'start_datetime', 'end_datetime']
    list_filter = ['car']
    search_fields = ['car__name']
