# views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from car_rental.models import Car,Booking
from car_rental.forms import PaymentForm
from datetime import datetime
from car_rental.forms import BookingForm
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.timezone import make_aware
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect



# username = Admin
# password = Admin@123

def index(request):
    return render(request , 'index.html')

def browse_cars(request):
    cars = Car.objects.all()
    search_query = request.GET.get('search', '')
    car_type = request.GET.get('car_type', '')
    transmission = request.GET.get('transmission', '')
    sort = request.GET.get('sort', '')
    
    start_date = request.GET.get('start_date')
    start_time = request.GET.get('start_time')
    end_date = request.GET.get('end_date')
    end_time = request.GET.get('end_time')

    error = None

    if start_date and start_time and end_date and end_time:
        try:
            start_datetime = make_aware(datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %I:%M %p"))
            end_datetime = make_aware(datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %I:%M %p"))

            if end_datetime <= start_datetime:
                error = "Drop-off must be after pickup."
                cars = []  # show no cars

            else:
                # Filter out booked cars
                booked_car_ids = Booking.objects.filter(
                    start_datetime__lt=end_datetime,
                    end_datetime__gt=start_datetime
                ).values_list('car_id', flat=True)
                cars = cars.exclude(id__in=booked_car_ids)

        except ValueError:
            error = "Invalid date or time format."
            cars = []

    # Apply additional filters
    if search_query:
        cars = cars.filter(name__icontains=search_query)
    if car_type:
        cars = cars.filter(car_type=car_type)
    if transmission:
        cars = cars.filter(transmission__iexact=transmission)
    if sort == 'price_low':
        cars = cars.order_by('free_km_price')
    elif sort == 'price_high':
        cars = cars.order_by('-free_km_price')

    context = {
        'cars': cars,
        'search_query': search_query,
        'car_type': car_type,
        'transmission': transmission,
        'sort': sort,
        'start_date': start_date,
        'start_time': start_time,
        'end_date': end_date,
        'end_time': end_time,
        'error': error,
    }

    return render(request, 'browse_cars.html', context)

def car_detail(request, pk):
    car = get_object_or_404(Car, pk=pk)
    return render(request, 'car_detail.html', {'car': car})


def pay_online(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            # Here you would handle payment processing logic
            # For demo, just redirect to a success page
            return redirect('payment_success')
    else:
        form = PaymentForm()
    return render(request, 'pay_online.html', {'form': form})

def payment_success(request):
    return render(request, 'payment_success.html')

def about(request):
    return render(request, "about.html")

def car_book(request, pk):
    car = get_object_or_404(Car, pk=pk)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            start = form.cleaned_data['start_datetime']
            end = form.cleaned_data['end_datetime']

            overlapping = Booking.objects.filter(
                car=car,
                start_datetime__lt=end,
                end_datetime__gt=start
            ).exists()

            if overlapping:
                form.add_error(None, "This car is already booked for the selected time period.")
            else:
                booking = form.save(commit=False)
                booking.car = car
                booking.save()

                # Send email to admin
                subject = f"New Booking: {car.name}"
                message = (
                    f"Car '{car.name}' has been booked.\n"
                    f"Start: {start}\n"
                    f"End: {end}\n"
                    f"Booking ID: {booking.id}\n"
                )
                admin_email = settings.DEFAULT_FROM_EMAIL  # or your admin email
                # send_mail(subject, message, admin_email, [admin_email])

                # Redirect to a booking success page with booking ID
                return redirect('booking_success', booking_id=booking.id)
    else:
        form = BookingForm()

    return render(request, 'car_book.html', {'car': car, 'form': form})

def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'booking_success.html', {'booking': booking})
