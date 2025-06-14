from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render, redirect
from car_rental.models import Car, Booking
from car_rental.forms import PaymentForm, BookingForm
from datetime import datetime, timedelta
from django.utils.timezone import make_aware, is_naive
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal
from django.http import JsonResponse
import uuid
from django.utils import timezone
from django.urls import reverse



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

    # Handle date/time filtering and exclude booked cars
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

                # Calculate dynamic prices
                rental_hours = (end_datetime - start_datetime).total_seconds() / 3600
                rental_hours_decimal = Decimal(str(rental_hours))

                for car in cars:
                    car.dynamic_price_100km = float(car.calculate_price(rental_hours_decimal, '100km'))
                    car.dynamic_price_200km = float(car.calculate_price(rental_hours_decimal, '200km'))
                    car.dynamic_price_300km = float(car.calculate_price(rental_hours_decimal, '300km'))
                    car.dynamic_price_unlimited = float(car.calculate_price(rental_hours_decimal, 'unlimited'))

        except ValueError:
            error = "Invalid date or time format."
        except Exception:
            # You might want to log this exception in real app
            pass

    # Apply text search and other filters
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

    # Calculate prices for template
    calculated_prices = {}
    if all([start_date, start_time, end_date, end_time]) and not error:
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
            # Handle payment processing here
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
            data = form.cleaned_data

            # Validate start/end datetime logic (optional)
            if data['end_datetime'] <= data['start_datetime']:
                form.add_error('end_datetime', 'End datetime must be after start datetime.')
            elif data['start_datetime'] < timezone.now():
                form.add_error('start_datetime', 'Start datetime cannot be in the past.')
            else:
                # Create the booking first to generate the token
                booking = Booking.objects.create(
                    car=car,
                    start_datetime=data['start_datetime'],
                    end_datetime=data['end_datetime'],
                    user_email=data['email']
                )

                # Generate approval link
                from django.urls import reverse
                approval_link = request.build_absolute_uri(
                    reverse('approve_booking', args=[str(booking.approval_token)])
                )

                # Compose email message
                message = (
                    f"New booking request for {car.name}\n\n"
                    f"Name: {data['full_name']}\n"
                    f"Email: {data['email']}\n"
                    f"Phone: {data['phone']}\n"
                    f"Start: {data['start_datetime']}\n"
                    f"End: {data['end_datetime']}\n\n"
                    f"To approve this booking, click the link below:\n{approval_link}"
                )

                send_mail(
                    subject=f"Booking Request for {car.name}",
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.MANAGER_EMAIL],
                    fail_silently=False,
                )
                return redirect('booking_pending')
    else:
        form = BookingForm()

    return render(request, 'car_book.html', {'car': car, 'form': form})



def booking_pending(request):
    return render(request, 'booking_pending.html')

def approve_booking(request, token):
    booking = get_object_or_404(Booking, approval_token=token)
    booking.is_approved = True
    booking.save()

    # Send confirmation email to customer
    success_link = request.build_absolute_uri(
        reverse('booking_success', args=[booking.id])
    )

    send_mail(
        subject="Your booking is approved!",
        message=(
            f"Dear customer,\n\n"
            f"Your booking for {booking.car.name} has been approved.\n"
            f"You can view confirmation details here:\n{success_link}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[booking.user_email],
        fail_silently=False,
    )

    return render(request, 'booking_approved.html', {'booking': booking})


def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if not booking.is_approved:
        return render(request, 'booking_pending.html', {'car': booking.car})

    return render(request, 'booking_success.html', {'booking': booking})


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

