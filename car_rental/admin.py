from django.contrib import admin
from .models import Car

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
        'is_available',
    ]
    list_filter = ['car_type', 'transmission', 'is_available']
    search_fields = ['name']
