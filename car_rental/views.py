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
import datetime

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

    # If user provided booking dates
    if start_date and start_time and end_date and end_time:
        start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
        end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")

        # Filter cars that are NOT booked in that time
        booked_car_ids = Booking.objects.filter(
            start_datetime__lt=end_datetime,
            end_datetime__gt=start_datetime
        ).values_list('car_id', flat=True)

        cars = cars.exclude(id__in=booked_car_ids)

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
                return redirect('browse_cars')
    else:
        form = BookingForm()

    return render(request, 'car_book.html', {'car': car, 'form': form})
