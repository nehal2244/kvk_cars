from django import forms
from car_rental.models import Booking
from django.utils import timezone
from django.utils.timezone import make_aware
import datetime

class PaymentForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'placeholder': 'Your full name'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'placeholder': 'your.email@example.com'
    }))
    amount = forms.DecimalField(min_value=0.01, max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs={
        'placeholder': 'Amount in Rs'
    }))
    PAYMENT_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    payment_method = forms.ChoiceField(choices=PAYMENT_CHOICES)

class BookingForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20)
    start_datetime = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    end_datetime = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
