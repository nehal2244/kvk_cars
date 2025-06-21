from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
<<<<<<< HEAD
=======

>>>>>>> 01293db9c10c8e80aa92d2f98e81b9193520aa89
from django.utils.timezone import make_aware
import datetime
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import uuid


<<<<<<< HEAD
=======

>>>>>>> 01293db9c10c8e80aa92d2f98e81b9193520aa89
class Car(models.Model):
    TRANSMISSION_CHOICES = [
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
    ]

    FUEL_CHOICES = [
        ('petrol', 'Petrol'),
        ('ev', 'Electric Vehicle'),
        ('cng', 'CNG'),
<<<<<<< HEAD
        ('petrol_cng', 'Petrol/CNG'),
=======
>>>>>>> 01293db9c10c8e80aa92d2f98e81b9193520aa89
    ]

    name = models.CharField(max_length=100)
    car_type = models.CharField(max_length=50)
    seating_capacity = models.PositiveIntegerField()
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES)
    fuel_type = models.CharField(max_length=10, choices=FUEL_CHOICES, default='petrol')

    # Pricing fields
    free_km_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    free_kms = models.PositiveIntegerField(default=0)
    unlimited_km_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    extra_km_charge = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    extra_hour_charge = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.0,
        help_text="Charge per hour after 12 hours rental"
    )
<<<<<<< HEAD
    extra_hour_charge_unlimited = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.0,
        help_text="Extra hourly charge *after 12 hrs* for Unlimited KM plan"
    )

    extra_km_per_hour_150km = models.PositiveIntegerField(
        default=0,
        help_text="Free km/hour after 12 hours for 150km plan"
    )

    price_150km = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
=======
    # NEW: Prices for fixed km plans
    price_100km = models.DecimalField(max_digits=8, decimal_places=2, default=0.0, verbose_name="150 KM")
    price_200km = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    price_300km = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
>>>>>>> 01293db9c10c8e80aa92d2f98e81b9193520aa89

    image_file = models.ImageField(upload_to='car_images/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

    def image_preview(self):
        if self.image_file:
            return self.image_file.url
        elif self.image_url:
            return self.image_url
        return ''

    def calculate_price(self, rental_hours, km_package):
<<<<<<< HEAD
        if rental_hours <= 12:
            if km_package == '150km':
                return self.price_150km
            elif km_package == 'unlimited':
                return self.unlimited_km_price
            else:
                return self.price_150km

        extra_hours = rental_hours - 12

        if km_package == '150km':
            extra_kms = extra_hours * self.extra_km_per_hour_150km
            extra_km_cost = extra_kms * self.extra_km_charge
            extra_hour_cost = extra_hours * self.extra_hour_charge
            return self.price_150km + extra_km_cost + extra_hour_cost

        elif km_package == 'unlimited':
            return self.unlimited_km_price + (extra_hours * self.extra_hour_charge_unlimited)

        else:
            return self.price_150km + (extra_hours * self.extra_hour_charge)
=======
        km_price_map = {
            '100km': self.price_100km,
            '200km': self.price_200km,
            '300km': self.price_300km,
            'unlimited': self.unlimited_km_price,
        }
        base_price = km_price_map.get(km_package, self.price_100km)

        if rental_hours <= 12:
            return base_price
        else:
            extra_hours = rental_hours - 12
            extra_price = extra_hours * self.extra_hour_charge
            return base_price + extra_price
>>>>>>> 01293db9c10c8e80aa92d2f98e81b9193520aa89


class Booking(models.Model): 
    car = models.ForeignKey('Car', on_delete=models.CASCADE, related_name='bookings')
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    
    full_name = models.CharField(max_length=150, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)

    user_email = models.EmailField()
<<<<<<< HEAD
    kms_plan = models.CharField(max_length=20, default='150km', help_text="Chosen KM plan")

    is_approved = models.BooleanField(default=False)
    approval_token = models.UUIDField(default=uuid.uuid4, editable=False, null=True)

=======
    is_approved = models.BooleanField(default=False)
    approval_token = models.UUIDField(default=uuid.uuid4, editable=False, null=True)  # no unique=True yet

    # ✅ New fields retained
>>>>>>> 01293db9c10c8e80aa92d2f98e81b9193520aa89
    pickup_by_customer = models.BooleanField(default=True, help_text="Will the customer pick up the car?")
    dropoff_by_customer = models.BooleanField(default=True, help_text="Will the customer drop off the car?")

    def __str__(self):
        return f"{self.car.name} from {self.start_datetime} to {self.end_datetime}"

    def clean(self):
<<<<<<< HEAD
        if self.start_datetime is None or self.end_datetime is None:
            raise ValidationError(_('Start date and end date must be provided.'))

        if self.end_datetime <= self.start_datetime:
            raise ValidationError({'end_datetime': _('End date and time must be after start date and time.')})

        if self.start_datetime < timezone.now():
            raise ValidationError({'start_datetime': _('Booking cannot start in the past.')})

=======
        # Defensive check: ensure start_datetime and end_datetime are provided
        if self.start_datetime is None or self.end_datetime is None:
            raise ValidationError(_('Start date and end date must be provided.'))

        # 1. End date must be after start date
        if self.end_datetime <= self.start_datetime:
            raise ValidationError({'end_datetime': _('End date and time must be after start date and time.')})

        # 2. Start date must be in the future
        if self.start_datetime < timezone.now():
            raise ValidationError({'start_datetime': _('Booking cannot start in the past.')})

        # 3. Prevent overlapping bookings for the same car
>>>>>>> 01293db9c10c8e80aa92d2f98e81b9193520aa89
        overlapping = Booking.objects.filter(
            car=self.car,
            end_datetime__gt=self.start_datetime,
            start_datetime__lt=self.end_datetime
        )
        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)

        if overlapping.exists():
            raise ValidationError(_('This booking overlaps with an existing booking for this car.'))

    def save(self, *args, **kwargs):
<<<<<<< HEAD
        self.full_clean()
        super().save(*args, **kwargs)


class PendingBooking(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    kms_plan = models.CharField(max_length=50, default='150km')
    approval_token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
=======
        self.full_clean()  # Ensure validation runs before save
        super().save(*args, **kwargs)
>>>>>>> 01293db9c10c8e80aa92d2f98e81b9193520aa89
