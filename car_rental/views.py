from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render, redirect
from car_rental.models import Car, Booking
from car_rental.forms import PaymentForm, BookingForm
from datetime import datetime
from django.utils.timezone import make_aware, is_naive
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal


def index(request):
    return render(request, 'index.html')


def browse_cars(request):
    cars = Car.objects.all()
    error = None

    search_query = request.GET.get('search', '')
    car_type = request.GET.get('car_type', '')
    transmission = request.GET.get('transmission', '')
    sort = request.GET.get('sort', '')

    start_date = request.GET.get('start_date')
    start_time = request.GET.get('start_time')
    end_date = request.GET.get('end_date')
    end_time = request.GET.get('end_time')

    if all([start_date, start_time, end_date, end_time]):
        try:
            start_datetime = make_aware(datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %I:%M %p"))
            end_datetime = make_aware(datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %I:%M %p"))

            if end_datetime <= start_datetime:
                error = "Drop-off must be after pickup."
            else:
                booked_car_ids = Booking.objects.filter(
                    start_datetime__lt=end_datetime,
                    end_datetime__gt=start_datetime
                ).values_list('car_id', flat=True)
                cars = cars.exclude(id__in=booked_car_ids)

        except ValueError:
            error = "Invalid date or time format."

    if all([start_date, start_time, end_date, end_time]) and not error:
        try:
            start_datetime = make_aware(datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %I:%M %p"))
            end_datetime = make_aware(datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %I:%M %p"))

            rental_hours = (end_datetime - start_datetime).total_seconds() / 3600
            rental_hours_decimal = Decimal(str(rental_hours))

            for car in cars:
                car.dynamic_price_100km = float(car.calculate_price(rental_hours_decimal, '100km'))
                car.dynamic_price_200km = float(car.calculate_price(rental_hours_decimal, '200km'))
                car.dynamic_price_300km = float(car.calculate_price(rental_hours_decimal, '300km'))
                car.dynamic_price_unlimited = float(car.calculate_price(rental_hours_decimal, 'unlimited'))
        except Exception:
            pass

    if search_query:
        cars = cars.filter(name__icontains=search_query)

    if car_type:
        cars = cars.filter(car_type=car_type)

    if transmission:
        cars = cars.filter(transmission__iexact=transmission)

    if sort == 'price_low':
        cars = cars.order_by('price_100km')
    elif sort == 'price_high':
        cars = cars.order_by('-price_100km')

    calculated_prices = {}
    if all([start_date, start_time, end_date, end_time]):
        try:
            start_datetime = make_aware(datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %I:%M %p"))
            end_datetime = make_aware(datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %I:%M %p"))
            rental_hours = (end_datetime - start_datetime).total_seconds() / 3600
            rental_hours_decimal = Decimal(str(rental_hours))

            for car in cars:
                calculated_prices[car.id] = {
                    '100km': round(float(car.calculate_price(rental_hours_decimal, '100km')), 2),
                    '200km': round(float(car.calculate_price(rental_hours_decimal, '200km')), 2),
                    '300km': round(float(car.calculate_price(rental_hours_decimal, '300km')), 2),
                    'unlimited': round(float(car.calculate_price(rental_hours_decimal, 'unlimited')), 2),
                }
        except Exception:
            pass

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
        'calculated_prices': calculated_prices,
    }

    return render(request, 'browse_cars.html', context)


def car_detail(request, pk):
    car = get_object_or_404(Car, pk=pk)
    return render(request, 'car_detail.html', {'car': car})


def pay_online(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
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
        booking = form.instance
        booking.car = car

        if form.is_valid():
            start = form.cleaned_data['start_datetime']
            end = form.cleaned_data['end_datetime']

            if is_naive(start):
                start = make_aware(start)
            if is_naive(end):
                end = make_aware(end)

            booking.start_datetime = start
            booking.end_datetime = end
            booking.save()

            return redirect('booking_success', booking_id=booking.id)
    else:
        form = BookingForm()

    return render(request, 'car_book.html', {'car': car, 'form': form})


def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if not booking.is_approved:
        return render(request, 'booking_pending.html', {'car': booking.car})

    return render(request, 'booking_success.html', {'booking': booking})


from django.http import JsonResponse

def get_dynamic_prices(request):
    start_date = request.GET.get('start_date')
    start_time = request.GET.get('start_time')
    end_date = request.GET.get('end_date')
    end_time = request.GET.get('end_time')

    if not all([start_date, start_time, end_date, end_time]):
        return JsonResponse({'error': 'Incomplete date/time data'}, status=400)

    try:
        start_datetime = make_aware(datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %I:%M %p"))
        end_datetime = make_aware(datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %I:%M %p"))
        rental_hours = (end_datetime - start_datetime).total_seconds() / 3600
        rental_hours_decimal = Decimal(str(rental_hours))
    except Exception:
        return JsonResponse({'error': 'Invalid date/time format'}, status=400)

    cars = Car.objects.all()

    prices = {}
    for car in cars:
        prices[car.id] = {
            '100km': round(float(car.calculate_price(rental_hours_decimal, '100km')), 2),
            '200km': round(float(car.calculate_price(rental_hours_decimal, '200km')), 2),
            '300km': round(float(car.calculate_price(rental_hours_decimal, '300km')), 2),
            'unlimited': round(float(car.calculate_price(rental_hours_decimal, 'unlimited')), 2),
        }
    return JsonResponse({'prices': prices})


def contactus(request):
    return render(request, "contactus.html")


def approve_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    booking.is_approved = True
    booking.save()

    send_mail(
        'Your Booking Has Been Approved',
        f"Dear Customer,\n\nYour booking for {booking.car.name} from {booking.start_datetime} to {booking.end_datetime} has been approved. Thank you!",
        settings.DEFAULT_FROM_EMAIL,
        [booking.user_email],
        fail_silently=True,
    )

    return render(request, 'booking_approved.html', {'booking': booking})
