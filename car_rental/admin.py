from django.contrib import admin
from car_rental.models import Car,Booking

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'car_type',
        'seating_capacity',
        'transmission',
        'free_km_price',
        'unlimited_km_price',
        'free_kms',
        'extra_km_charge',
    ]
    list_filter = ['car_type', 'transmission']
    search_fields = ['name']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['car', 'start_datetime', 'end_datetime']
    list_filter = ['car']
    search_fields = ['car__name']
