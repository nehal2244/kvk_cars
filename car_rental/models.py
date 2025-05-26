from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Car(models.Model):
    TRANSMISSION_CHOICES = [
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
    ]

    name = models.CharField(max_length=100)
    car_type = models.CharField(max_length=50)
    seating_capacity = models.PositiveIntegerField()
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES)
    
    # Pricing fields
    free_km_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)        # Price with free kms
    unlimited_km_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)   # Price for unlimited kms
    extra_km_charge = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)      # Extra km charge per km
    
    free_kms = models.PositiveIntegerField(default=0)   # Number of free kms allowed
    
    image_url = models.URLField()

    def __str__(self):
        return self.name


class Booking(models.Model):
    car = models.ForeignKey('Car', on_delete=models.CASCADE, related_name='bookings')
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    def __str__(self):
        return f"{self.car.name} from {self.start_datetime} to {self.end_datetime}"
